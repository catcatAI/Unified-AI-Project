import logging
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)

# In-memory store for session-to-agent mapping.
# In a production system, this would be a more persistent store like Redis.
chat_sessions: dict[str, str] = {}


class ChatRequest(BaseModel):
    """Defines the request body for the /chat endpoint."""

    user_input: str = Field(..., description="The user's message.")
    session_id: str | None = Field(
        None,
        description="A unique ID to maintain conversation context. If not provided, a new session is created.",
    )


class ChatResponse(BaseModel):
    """Defines the response body for the /chat endpoint."""

    response_text: str
    session_id: str


@router.post("/", response_model=ChatResponse)
async def handle_chat(request: ChatRequest):
    """Handles a user's chat message by routing it to a dedicated ConversationalAgent for the session."""
    # Local import to break circular dependency with main.py
    from apps.backend.main import agent_manager

    session_id = request.session_id or str(uuid.uuid4())
    logger.info(
        f"Received chat request for session '{session_id}': '{request.user_input}'",
    )

    agent_id = chat_sessions.get(session_id)
    agent = agent_manager.get_agent(agent_id) if agent_id else None

    if not agent:
        logger.info(
            f"No existing agent for session '{session_id}'. Launching a new ConversationalAgent.",
        )
        try:
            # Launch a new agent for the new session
            agent = await agent_manager.launch_agent(
                "ConversationalAgent",
                name=f"ConvAgent-{session_id[:8]}",
            )
            chat_sessions[session_id] = agent.agent_id
        except Exception as e:
            logger.error(f"Could not launch ConversationalAgent: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error launching agent: {e}")

    # After attempting to launch, if agent is still None, it means launch_agent failed
    # and did not raise a specific exception that was caught.
    if not agent:
        raise HTTPException(
            status_code=500,
            detail="Failed to launch a conversational agent. Is it registered?",
        )

    logger.info(f"Routing chat for session '{session_id}' to agent '{agent.agent_id}'.")

    try:
        task = {"user_input": request.user_input}
        # Directly call handle_task to get a response for this HTTP request
        result = await agent.handle_task(task)
    except Exception as e:
        logger.error(
            f"An error occurred during agent task handling: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {e}",
        )
    else: # Only process result if no exception occurred during handle_task
        if result.get("status") == "completed":
            response_text = result.get("result", {}).get(
                "response_text",
                "I'm sorry, I couldn't generate a proper response.",
            )
            return ChatResponse(response_text=response_text, session_id=session_id)
        error_detail = result.get(
            "error",
            "An unknown error occurred in the agent.",
        )
        raise HTTPException(status_code=500, detail=error_detail)
