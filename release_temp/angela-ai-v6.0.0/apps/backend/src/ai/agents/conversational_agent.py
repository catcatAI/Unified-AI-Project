import logging
from typing import Any

from ...services.llm_service import llm_manager  # Import the shared singleton instance
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ConversationalAgent(BaseAgent):
    """An agent designed specifically to handle conversational interactions.
    It uses the central LLM service to generate human-like responses,
    and leverages the memory system to maintain conversation context.
    """

    async def perceive(
        self,
        task: dict[str, Any],
        retrieved_memories: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Processes the user's input and constructs a conversation history from retrieved memories."""
        user_input = task.get("user_input", "")
        logger.debug(f"ConversationalAgent perceived user input: '{user_input}'")

        # Build a simplified conversation history from past experiences
        history = []
        for mem in retrieved_memories:
            # Accessing nested data based on the structure we defined for storage in BaseAgent
            past_task = mem.get("full_context", {}).get("task", {})
            past_result = mem.get("full_context", {}).get("action_result", {})

            past_input = past_task.get("user_input")
            past_response = past_result.get("response_text")

            if past_input:
                history.append(f"User: {past_input}")
            if past_response:
                history.append(f"AI: {past_response}")

        conversation_history = "\n".join(history)
        logger.debug(f"Constructed conversation history:\n{conversation_history}")

        return {"user_input": user_input, "conversation_history": conversation_history}

    async def decide(
        self,
        perceived_info: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Decides on the action to take. For this agent, the decision is always to
        generate a text response, now including conversation history in the prompt.
        """
        user_input = perceived_info.get("user_input", "")
        history = perceived_info.get("conversation_history", "")

        # Construct a more context-aware prompt
        if history:
            prompt = f"Conversation History:\n{history}\n\nNew User Input: {user_input}"
        else:
            prompt = user_input

        # For the benchmark, use the model specified in the task, otherwise default.
        model_to_use = "distilgpt2"
        if context and "task" in context and "model" in context["task"]:
            model_to_use = context["task"]["model"]

        decision = {
            "action": "generate_response",
            "model": model_to_use,
            "prompt": prompt,
        }
        logger.debug(
            f"ConversationalAgent decided to '{decision['action']}' with model '{decision['model']}'.",
        )
        return decision

    async def act(
        self,
        decision: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Executes the decision by calling the LLM service."""
        if decision.get("action") == "generate_response":
            model = decision.get("model")
            prompt = decision.get("prompt")
            logger.info(f"Calling LLM service with model '{model}'.")

            try:
                # Use the singleton llm_manager to generate a response
                response = await llm_manager.generate(model=model, prompt=prompt)
                return {"response_text": response.text}
            except Exception as e:
                error_message = (
                    f"An error occurred while contacting the LLM service: {e}"
                )
                logger.error(error_message, exc_info=True)
                # Return a user-friendly error message
                return {
                    "response_text": "I'm sorry, I encountered an error and couldn't generate a response.",
                }

        logger.warning(f"Unknown action decided: {decision.get('action')}")
        return {"response_text": "I'm not sure how to proceed with that decision."}

    async def feedback(
        self,
        original_task: dict[str, Any],
        action_result: Any,
        context: dict[str, Any] | None = None,
    ) -> None:
        """The feedback phase for this agent. This is where the agent could perform
        self-reflection or scoring before the experience is stored by the BaseAgent.
        """
        logger.debug(
            f"ConversationalAgent feedback phase completed for task '{original_task.get('user_input')}'. The conversation turn will now be stored in memory.",
        )
