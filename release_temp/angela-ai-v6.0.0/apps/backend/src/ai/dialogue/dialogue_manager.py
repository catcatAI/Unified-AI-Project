import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

from apps.backend.src.core.llm.hybrid_brain import HybridBrain

class DialogueManager:
    """
    Manages dialogue interactions for the AI character.
    Orchestrates NLU, context management, and response generation.
    """

    def __init__(self):
        logger.info("DialogueManager initialized.")
        self.brain = HybridBrain()

    async def get_response(self, player_message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a response to the player's message.
        
        Args:
            player_message (str): The user's input text.
            context (Dict[str, Any]): Contextual information (mood, favorability, etc.).
            
        Returns:
            Dict[str, Any]: The response dictionary, usually containing 'response' text.
        """
        logger.info(f"Processing message: {player_message} with context: {context}")
        
        # Prepare context for Brain
        brain_context = {
            "user_input": player_message,
            "drafts": [], # Brain will generate drafts internally if needed, or we can skip M1 for chat
            "governance_lock": False, # Chat is usually safe, but VDAF should check it
            **context
        }
        
        # We can use a simplified flow for chat:
        # 1. VDAF Check (Optional here, usually done by Orchestrator)
        # 2. Generate Response
        
        # For now, we'll ask the brain to generate a response directly using the provider
        # But HybridBrain doesn't expose a direct "chat" method yet.
        # We'll use the provider directly via the brain, or add a method to brain.
        # Let's use the provider directly for now to keep it simple, or better:
        # Add a 'chat' method to HybridBrain?
        # No, let's use the existing synthesize_and_verify but with a chat-specific prompt.
        
        try:
            response_text = await self.brain.chat(player_message, context)
        except Exception as e:
            logger.error(f"Dialogue Generation Failed: {e}")
            response_text = "..."

        return {"response": response_text}
