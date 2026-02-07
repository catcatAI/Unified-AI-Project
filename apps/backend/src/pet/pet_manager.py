import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class PetManager:
    """Manages the state, behavior, and interactions of the desktop pet.
    Designed to allow for dynamic personalities and behaviors that can be updated by the core AI.
    """

    def __init__(self, pet_id: str, config: Dict[str, Any], biological_integrator: Any = None, broadcast_callback: Optional[callable] = None) -> None:
        """Initializes the PetManager for a specific pet."""
        self.pet_id = pet_id
        self.config = config
        self.biological_integrator = biological_integrator
        self.broadcast_callback = broadcast_callback
        self.economy_manager = None  # To be set via setter or during init
        self.state: Dict[str, Any] = {
            "happiness": 100,
            "hunger": 0,
            "energy": 100,
            "position": {"x": 0, "y": 0},
            "scale": 1.0,
            "current_animation": "idle",
            "current_expression": "neutral"
        }
        self.personality: Dict[str, Any] = self.config.get("initial_personality", {"curiosity": 0.7, "playfulness": 0.8})
        self.behavior_rules: Dict[str, Any] = self.config.get("initial_behaviors", {"on_interaction": "show_happiness"})
        
        # Action queue for AI-initiated actions / AI 主動行為隊列
        self.action_queue: List[Dict[str, Any]] = []
        self.max_queue_size = 10
        
        # Survival Settings (Phase 13)
        self.decay_rates = {
            "hunger": 2.0,   # Increase per cycle
            "energy": 1.5,   # Decrease per cycle
            "happiness": 1.0 # Decrease per cycle
        }
        self.survival_threshold = 30.0 # Trigger behavior below this
        
        logger.info(f"PetManager for pet '{self.pet_id}' initialized.")

    def sync_with_biological_state(self):
        """Syncs pet state with internal biological simulation (hormones, arousal)."""
        if not self.biological_integrator:
            return

        bio_state = self.biological_integrator.get_biological_state()
        
        # Map arousal to happiness/energy
        arousal = bio_state.get("arousal", 50.0)
        mood = bio_state.get("mood", 0.5) # Pleasure dimension
        
        # Update happiness based on pleasure/mood
        self.state["happiness"] = int(mood * 100)
        
        # Map dominant emotion to expression
        emotion_map = {
            "joy": "happy",
            "trust": "happy",
            "fear": "scared",
            "surprise": "surprised",
            "sadness": "sad",
            "disgust": "annoyed",
            "anger": "angry",
            "calm": "neutral",
            "love": "happy"
        }
        dominant_emotion = bio_state.get("dominant_emotion", "unknown")
        self.state["current_expression"] = emotion_map.get(dominant_emotion, "neutral")
        
        # Map stress to animation if high
        stress = bio_state.get("stress_level", 0.0)
        if stress > 15.0: # Arbitrary threshold
            self.state["current_animation"] = "anxious"
        elif arousal < 20.0:
            self.state["current_animation"] = "sleepy"

        logger.debug(f"Pet '{self.pet_id}' synced with biological state. Happiness: {self.state['happiness']}")
        self._notify_state_change("sync_bio")

    async def _notify_state_change(self, reason: str):
        """Notifies external clients about pet state changes (e.g., via WebSocket)."""
        if self.broadcast_callback:
            try:
                # If broadcast_callback is coro, await it
                import asyncio
                payload = {
                    "pet_id": self.pet_id,
                    "reason": reason,
                    "state": self.state,
                    "timestamp": datetime.now().isoformat()
                }
                if asyncio.iscoroutinefunction(self.broadcast_callback):
                    await self.broadcast_callback("pet_state_update", payload)
                else:
                    self.broadcast_callback("pet_state_update", payload)
            except Exception as e:
                logger.error(f"Failed to broadcast pet state change: {e}")

    async def handle_interaction(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handles user interaction and updates the pet's state based on behavior rules."""
        interaction_type = interaction_data.get("type")
        logger.debug(f"Handling interaction: '{interaction_type}' for pet '{self.pet_id}'")
        
        # Update state based on interaction / 根據交互更新狀態
        if interaction_type == "pet":
            self.state["happiness"] = min(100, self.state["happiness"] + 10)
            self.state["current_expression"] = "happy"
            self.state["current_animation"] = "respond_to_pet"
        elif interaction_type == "feed":
            self.state["hunger"] = max(0, self.state["hunger"] - 20)
            self.state["happiness"] = min(100, self.state["happiness"] + 5)
            self.state["current_expression"] = "joy"
            self.state["current_animation"] = "eat"
        elif interaction_type == "play":
            self.state["energy"] = max(0, self.state["energy"] - 15)
            self.state["happiness"] = min(100, self.state["happiness"] + 15)
            self.state["current_animation"] = "dance"
        elif interaction_type == "rest":
            self.state["energy"] = min(100, self.state["energy"] + 20)
            self.state["current_expression"] = "relaxed"
            self.state["current_animation"] = "sleep"

        logger.info(f"Pet '{self.pet_id}' handled interaction '{interaction_type}'. Current state: {self.state}")
        # Notify immediately on interaction
        await self._notify_state_change(f"interaction_{interaction_type}")
        return {"status": "success", "new_state": self.state}

    def get_current_state(self) -> Dict[str, Any]:
        """Returns the current state of the pet."""
        return self.state

    def update_position(self, x: float, y: float, scale: float = None):
        """Update pet's desktop position and scale / 更新寵物在桌面上的位置和縮放"""
        self.state["position"] = {"x": x, "y": y}
        if scale is not None:
            self.state["scale"] = scale
        logger.debug(f"Pet '{self.pet_id}' position updated to ({x}, {y}), scale: {self.state['scale']}")

    def add_action(self, action_type: str, data: Dict[str, Any] = None):
        """Add an action for the desktop pet to perform / 為桌面端添加待執行動作"""
        action = {
            "action_id": str(uuid.uuid4()),
            "type": action_type,
            "data": data or {},
            "timestamp": datetime.now().isoformat()
        }
        self.action_queue.append(action)
        if len(self.action_queue) > self.max_queue_size:
            self.action_queue.pop(0)
        logger.info(f"Added action '{action_type}' to queue for pet '{self.pet_id}'")

    async def apply_resource_decay(self, delta_time_factor: float = 1.0):
        """Simulates the passage of time on pet needs (Hunger, Energy, Happiness)."""
        self.state["hunger"] = min(100, self.state["hunger"] + self.decay_rates["hunger"] * delta_time_factor)
        self.state["energy"] = max(0, self.state["energy"] - self.decay_rates["energy"] * delta_time_factor)
        self.state["happiness"] = max(0, self.state["happiness"] - self.decay_rates["happiness"] * delta_time_factor)
        
        logger.debug(f"Applied decay to pet '{self.pet_id}'. Current: H:{self.state['hunger']}, E:{self.state['energy']}, Hap:{self.state['happiness']}")
        
        # Check if pet needs to take action
        await self.check_survival_needs()
        await self._notify_state_change("decay")

    async def check_survival_needs(self):
        """Proactively checks survival bars and triggers economic activity if needed."""
        if not self.economy_manager:
            logger.error(f"DEBUG: Pet '{self.pet_id}' has NO linked economy_manager!")
            return
        
        logger.info(f"DEBUG: Pet '{self.pet_id}' checking survival needs. Hunger: {self.state['hunger']}, Energy: {self.state['energy']}, Threshold: {self.survival_threshold}")

        # 1. Hunger Check (Priority)
        if self.state["hunger"] > (100 - self.survival_threshold):
            logger.info(f"Pet '{self.pet_id}' is hungry ({self.state['hunger']}). Attempting purchase.")
            result = self.economy_manager.purchase_item(self.pet_id, "premium_bio_pellets")
            if result["success"]:
                self.state["hunger"] = max(0, self.state["hunger"] - result["effects"].get("hunger", 0))
                self.state["happiness"] = min(100, self.state["happiness"] + result["effects"].get("happiness", 0))
                self.add_action("eat_autonomous", {"item": "premium_bio_pellets"})
                await self._notify_state_change("autonomous_purchase_food")

        # 2. Energy Check
        if self.state["energy"] < self.survival_threshold:
            logger.info(f"Pet '{self.pet_id}' is tired ({self.state['energy']}). Attempting purchase.")
            result = self.economy_manager.purchase_item(self.pet_id, "digital_energy_drink")
            if result["success"]:
                self.state["energy"] = min(100, self.state["energy"] + result["effects"].get("energy", 0))
                self.add_action("drink_autonomous", {"item": "digital_energy_drink"})
                await self._notify_state_change("autonomous_purchase_energy")

    def set_economy_manager(self, eco_manager):
        """Link the economy manager for autonomous spending."""
        self.economy_manager = eco_manager
        logger.info(f"PetManager linked to EconomyManager.")

    def get_pending_actions(self) -> List[Dict[str, Any]]:
        """Get and clear pending actions / 獲取並清除待執行動作"""
        actions = self.action_queue.copy()
        self.action_queue.clear()
        return actions

    def update_behavior(self, new_behaviors: Dict[str, Any]):
        """Allows the core AI to dynamically update the pet's behavior rules."""
        logger.info(f"Updating behavior for pet '{self.pet_id}' from {self.behavior_rules} to {new_behaviors}")
        self.behavior_rules.update(new_behaviors)
        logger.info(f"Behavior for pet '{self.pet_id}' updated successfully.")
