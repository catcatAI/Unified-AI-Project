import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class PetManager:
    """Manages the state, behavior, and interactions of the desktop pet.
    Designed to allow for dynamic personalities and behaviors that can be updated by the core AI.
    """

    def __init__(self, pet_id: str, config: Dict[str, Any]) -> None:
        """Initializes the PetManager for a specific pet."""
        self.pet_id = pet_id
        self.config = config
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
        
        logger.info(f"PetManager for pet '{self.pet_id}' initialized with personality: {self.personality}")

    def handle_interaction(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
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
