import asyncio
import logging
from typing import Any
from datetime import datetime
import ray

# Assuming DialogueManager and other services are available in the backend
from apps.backend.src.game.angela import DialogueManager
from apps.backend.src.game.economy_manager import EconomyManager

logger = logging.getLogger(__name__)


from apps.backend.src.game.personality import PersonalityEngine, PersonalityTraits

@ray.remote
class DesktopPetActor:
    """Represents the core logic for the Desktop Pet MVP feature, running as a Ray Actor.
    This class manages the pet's state, interactions, and integration with AI services.
    """

    def __init__(self, name: str, orchestrator: Any = None, economy_manager: EconomyManager | None = None):
        self.name = name
        self.orchestrator = orchestrator # This will be an ActorHandle
        self.economy_manager = economy_manager # This will be an ActorHandle
        self.personality = PersonalityEngine(traits=PersonalityTraits(curiosity=0.7, extroversion=0.6))
        self.favorability = 50  # Initial favorability score (0-100)
        self.status = "idle"  # e.g., "idle", "interacting", "sleeping" (Legacy status)
        self.position = {"x": 0, "y": 0}  # Placeholder for screen position
        self.current_user = "default_user" # Placeholder for multi-user support
        self.proactive_message_queue = []  # Phase 2.2: Queue for autonomous messages
        self.last_proactive_check = None
        logger.info(f"DesktopPetActor '{self.name}' initialized with Personality, Orchestrator, and Economy.")

    async def check_and_queue_proactive_messages(self):
        """Check if personality triggers warrant a proactive message. (Phase 2.2)"""
        should_trigger, trigger_type = self.personality.should_trigger_proactive_message()
        
        if should_trigger and self.orchestrator:
            # Avoid spamming - only one message per trigger type
            existing_types = [msg.get("trigger_type") for msg in self.proactive_message_queue]
            if trigger_type in existing_types:
                return
            
            context = self.personality.get_proactive_message_context(trigger_type)
            
            # Phase 2.2 Advanced: Query HAM Memory for recent context
            memory_context = ""
            try:
                # Orchestrator is an ActorHandle, so call remote method
                # Assuming ham_memory is a property of the CognitiveOrchestratorActor
                if self.orchestrator and hasattr(self.orchestrator, 'ham_memory_manager'): # Check for ham_memory_manager attribute on the ActorHandle
                    # Retrieve recent interactions by calling remote method on HamMemoryManagerActor
                    ham_memory_actor_handle = await self.orchestrator.ham_memory_manager.remote() # Get the HamMemoryManagerActor handle from OrchestratorActor
                    recent_memories = await ham_memory_actor_handle.retrieve_relevant_memories.remote(
                        query="recent conversation topics",
                        limit=3
                    )
                    if recent_memories:
                        topics = [mem.get("content", "")[:100] for mem in recent_memories]
                        memory_context = f" Recent topics: {', '.join(topics)}."
                        logger.debug(f"Retrieved {len(recent_memories)} memories for proactive context")
            except Exception as e:
                logger.warning(f"Failed to retrieve memory context: {e}")
            
            # Generate message using orchestrator with enhanced context
            try:
                enhanced_prompt = f"[Proactive Message - {context.get('tone', 'neutral')}] {context.get('prompt_hint', 'Say something.')}{memory_context}"
                # Orchestrator is an ActorHandle, so call remote method
                result = await self.orchestrator.process_user_input.remote(enhanced_prompt)
                
                message = {
                    "trigger_type": trigger_type,
                    "tone": context.get("tone"),
                    "text": result.get("response", "..."),
                    "timestamp": datetime.now().isoformat(),
                    "has_context": bool(memory_context)
                }
                
                self.proactive_message_queue.append(message)
                logger.info(f"Proactive message queued: {trigger_type} (context: {bool(memory_context)})")
            except Exception as e:
                logger.error(f"Failed to generate proactive message: {e}")

    def get_proactive_messages(self, clear_queue: bool = True) -> list:
        """Retrieve and optionally clear the proactive message queue."""
        messages = self.proactive_message_queue.copy()
        if clear_queue:
            self.proactive_message_queue.clear()
        return messages

    async def handle_user_input(
        self,
        input_type: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Handles various types of user input directed at the desktop pet."""
        logger.debug(
            f"Pet '{self.name}' received input: {input_type} with payload {payload}",
        )
        response = {"status": "processed", "pet_response": ""}

        if input_type == "click":
            response["pet_response"] = await self._handle_click(payload)
        elif input_type == "message":
            res = await self._handle_message(payload)
            response["pet_response"] = res["response"]
            response["metadata"] = res.get("metadata", {})
        elif input_type == "drag":
            response["pet_response"] = await self._handle_drag(payload)
        elif input_type == "gift":
            response["pet_response"] = await self._handle_gift(payload)
        else:
            response["status"] = "unsupported_input"
            response["pet_response"] = "I don't understand that interaction."

        return response

    async def _handle_click(self, payload: dict[str, Any]) -> str:
        """Internal handler for click events."""
        self.increase_favorability(1, quality_score=0.8) # Clicks are positive
        return f"You clicked me! My favorability is now {self.favorability}."

    async def _handle_message(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Internal handler for message input. Uses core MSCU Orchestrator."""
        user_message = payload.get("text", "")
        if not user_message:
            return {"response": "Did you say something?"}

        # Use Unified Cognitive Orchestrator Actor
        if self.orchestrator:
            result = await self.orchestrator.process_user_input.remote(user_message)
            response_text = result.get("response", "...")
            metadata = result.get("metadata", {})
            
            # Dynamic Favorability based on Quality Score
            quality_score = metadata.get("quality_score", 0.7)
            gain = int(5 * quality_score) # Scale base gain by quality
            await self.increase_favorability.remote(gain, quality_score=quality_score) # Call remote increase_favorability
            
            return {"response": response_text, "metadata": metadata}
        else:
            # Fallback to simple response if orchestrator missing
            return {"response": "I'm thinking, but my brain feels disconnected."}

    async def _handle_drag(self, payload: dict[str, Any]) -> str:
        """Internal handler for drag events (e.g., moving the pet)."""
        new_x = payload.get("x", self.position["x"])
        new_y = payload.get("y", self.position["y"])
        self.position = {"x": new_x, "y": new_y}
        await self.decrease_favorability.remote(1)  # Being moved might be slightly annoying
        return f"Whee! You moved me to ({new_x}, {new_y}). My favorability is now {self.favorability}."

    async def _handle_gift(self, payload: dict[str, Any]) -> str:
        """Internal handler for gift events. Now uses the item system."""
        if not self.economy_manager:
            return "Economy system not active."
        
        item_id = payload.get("item_id")
        user_id = payload.get("user_id", self.current_user)

        if not item_id:
            return "Please specify an item to gift."

        # EconomyManager is an ActorHandle
        item_definition = await self.economy_manager.get_item_definition.remote(item_id)
        if not item_definition:
            return f"Item '{item_id}' not found in the economy."
        
        # Assume buying the item to give as a gift
        if await self.economy_manager.buy_item.remote(user_id, item_id, quantity=1):
            # Favorability gain based on item value or category
            favorability_gain = int(item_definition["base_price"] * 1.5) # Example: 1.5x price
            if item_definition["category"] == "food":
                self.personality.needs.hunger = max(0.0, self.personality.needs.hunger - 0.5) # Food reduces hunger
                favorability_gain += 5
            elif item_definition["category"] == "toy":
                self.personality.needs.attention = max(0.0, self.personality.needs.attention - 0.5) # Toy provides attention
                favorability_gain += 10
            
            await self.increase_favorability.remote(favorability_gain, quality_score=1.0) 
            self.status = "happy"
            return f"Oh, a {item_definition['name']}! Thank you so much! I feel much closer to you now. (Favorability: {self.favorability})"
        else:
            return f"You don't have enough coins to buy {item_definition['name']} for a gift, or something went wrong."

    async def increase_favorability(self, amount: int, quality_score: float = 1.0):
        """Increases the pet's favorability and rewards the user with coins (Meta-Formula)."""
        old_fav = self.favorability
        self.favorability = min(100, self.favorability + amount)
        fav_delta = self.favorability - old_fav
        
        logger.debug(f"Favorability increased to {self.favorability}")
        
        # Update Personality/Emotion (Phase 2: Spark of Life)
        self.personality.update_emotion(interaction_quality=quality_score, favorability=self.favorability)
        self.status = self.personality.mood.value # Keep legacy status in sync for now
        
        # Earn Logic: Meta-Formula implementation (Phase 2: Spark of Life)
        if self.economy_manager and fav_delta > 0:
            # Reward = Delta * Multiplier * Quality
            # Multiplier is based on current favorability level (Loyalty bonus)
            loyalty_multiplier = 0.5 + (self.favorability / 100.0) 
            reward = round(fav_delta * loyalty_multiplier * quality_score, 2)
            await self.economy_manager.reward_user.remote(self.current_user, reward) # Call remote reward_user
            logger.info(f"Rewarded user {self.current_user} with {reward} coins (Quality: {quality_score})")

    async def decrease_favorability(self, amount: int):
        """Decreases the pet's favorability."""
        self.favorability = max(0, self.favorability - amount)
        logger.debug(f"Favorability decreased to {self.favorability}")

    async def check_for_proactive_interaction(self) -> str:
        """Simulates the pet initiating an interaction based on its internal state or external factors."""
        if self.favorability < 30 and self.status == "idle":
            self.status = "interacting"
            return "I'm feeling a bit lonely. Could you talk to me?"
        if self.favorability > 80 and self.status == "idle":
            self.status = "interacting"
            return "You're the best! What are you up to?"

        self.status = "idle"
        return ""  # No proactive interaction

    async def update_state(self):
        """Periodically updates the pet's internal state.
        This could include checking for proactive interactions, hunger, etc.
        """
        # For now, just check for proactive interactions
        proactive_message = await self.check_for_proactive_interaction()
        if proactive_message:
            logger.info(f"Pet '{self.name}' initiated: {proactive_message}")
            # In a real scenario, this would be sent to the frontend for display
        await asyncio.sleep(1)  # Simulate some work