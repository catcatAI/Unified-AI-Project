import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PetManager:
    """Manages the state, behavior, and interactions of the desktop pet.
    Designed to allow for dynamic personalities and behaviors that can be updated by the core AI.
    """

    def __init__(self, pet_id: str, config: Dict[str, Any]):
        """Initializes the PetManager for a specific pet."""
        self.pet_id = pet_id
        self.config = config
        self.state = {
            "happiness": 100,
            "hunger": 0,
            "energy": 100
        }
        self.personality = self.config.get("initial_personality", {"curiosity": 0.7, "playfulness": 0.8})
        self.behavior_rules = self.config.get("initial_behaviors", {"on_interaction": "show_happiness"})
        logger.info(f"PetManager for pet '{self.pet_id}' initialized with personality: {self.personality}")

    def handle_interaction(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handles user interaction and updates the pet's state based on behavior rules."""
        interaction_type = interaction_data.get("type")
        logger.debug(f"Handling interaction: '{interaction_type}' for pet '{self.pet_id}'")

        # TODO: Implement more complex logic based on personality and state.
        if self.behavior_rules.get("on_interaction") == "show_happiness":
            self.state["happiness"] = min(100, self.state["happiness"] + 10)
            logger.info(f"Pet '{self.pet_id}' happiness increased to {self.state['happiness']}")

        return {"status": "success", "new_state": self.state}

    def get_current_state(self) -> Dict[str, Any]:
        """Returns the current state of the pet."""
        return self.state

    def update_behavior(self, new_behaviors: Dict[str, Any]):
        """Allows the core AI to dynamically update the pet's behavior rules."""
        logger.info(f"Updating behavior for pet '{self.pet_id}' from {self.behavior_rules} to {new_behaviors}")
        self.behavior_rules.update(new_behaviors)
        # TODO: Add validation for new behaviors.
        logger.info(f"Behavior for pet '{self.pet_id}' updated successfully.")
