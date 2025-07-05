import uvicorn # For running the app
from fastapi import FastAPI
from datetime import datetime
import uuid # For generating session IDs

# Assuming src is in PYTHONPATH or this script is run from project root
# Adjust paths as necessary if running from within services directory directly for testing
from core_ai.dialogue.dialogue_manager import DialogueManager
from services.api_models import UserInput, AIOutput, SessionStartRequest, SessionStartResponse


app = FastAPI(
    title="Unified AI Project API",
    description="API endpoints for interacting with the Unified AI.",
    version="0.1.0"
)

# Instantiate DialogueManager globally for now.
# For production, consider lifespan events or dependency injection for managing such resources.
# Ensure DialogueManager and its dependencies (like PersonalityManager loading profiles)
# can handle being initialized at the module level.
try:
    dialogue_manager = DialogueManager()
    print("MainAPIServer: DialogueManager instantiated successfully.")
except Exception as e:
    print(f"MainAPIServer: CRITICAL ERROR - Failed to instantiate DialogueManager: {e}")
    # Potentially exit or define a fallback dialogue_manager that returns errors
    dialogue_manager = None


@app.post("/api/v1/chat", response_model=AIOutput, tags=["Chat"])
async def chat_endpoint(user_input: UserInput):
    """
    Receives user input and returns the AI's response.
    """
    print(f"API: Received chat input: UserID='{user_input.user_id}', SessionID='{user_input.session_id}', Text='{user_input.text}'")
    if dialogue_manager is None:
        return AIOutput(
            response_text="Error: DialogueManager not available.",
            user_id=user_input.user_id,
            session_id=user_input.session_id,
            timestamp=datetime.now().isoformat()
        )

    # Pass user_id and session_id to DialogueManager
    ai_response_text = await dialogue_manager.get_simple_response( # Added await
        user_input.text,
        session_id=user_input.session_id,
        user_id=user_input.user_id
    )

    return AIOutput(
        response_text=ai_response_text,
        user_id=user_input.user_id,
        session_id=user_input.session_id,
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/v1/session/start", response_model=SessionStartResponse, tags=["Session"])
async def start_session_endpoint(session_start_request: SessionStartRequest):
    """
    Starts a new session and returns an initial greeting and session ID.
    """
    print(f"API: Received session start request: UserID='{session_start_request.user_id}'")
    if dialogue_manager is None:
        # Even if DM is None, we can still provide a session ID and a generic error greeting
        session_id = uuid.uuid4().hex
        return SessionStartResponse(
            greeting="Error: AI Service not available.",
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )

    greeting = dialogue_manager.start_session(user_id=session_start_request.user_id)
    session_id = uuid.uuid4().hex # Generate a new session ID

    return SessionStartResponse(
        greeting=greeting,
        session_id=session_id,
        timestamp=datetime.now().isoformat()
    )

# Placeholder for other API routes - to be added in next steps

if __name__ == "__main__":
    print("Attempting to run MainAPIServer with Uvicorn...")
    if dialogue_manager is None:
        print("ERROR: DialogueManager could not be initialized. API server will not function correctly.")
        # Optionally, prevent server from starting or make it clear it's in a degraded state.

    # Note: host and port can be configured via environment variables or a config file in a real app
    uvicorn.run(app, host="0.0.0.0", port=8000)
    # To run this directly: python src/services/main_api_server.py
    # (Ensure PYTHONPATH includes project root or Unified-AI-Project directory)

    # If you want to run with auto-reload for development:
    # uvicorn src.services.main_api_server:app --reload --host 0.0.0.0 --port 8000
    # (Run from project root: Unified-AI-Project/)
