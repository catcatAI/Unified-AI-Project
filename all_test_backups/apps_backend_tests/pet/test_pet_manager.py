import unittest
from apps.backend.src.pet.pet_manager import PetManager

class TestPetManager(unittest.TestCase):
    def setUp(self):
        self.pet_id = "test_pet"
        self.config = {
            "initial_personality": {"curiosity": 0.7, "playfulness": 0.8},
            "initial_behaviors": {"on_interaction": "show_happiness"}
        }
        self.manager = PetManager(self.pet_id, self.config)

    def test_initialization(self) -> None:
        self.assertEqual(self.manager.pet_id, "test_pet")
        self.assertEqual(self.manager.state["happiness"], 100)
        self.assertEqual(self.manager.state["hunger"], 0)
        self.assertEqual(self.manager.state["energy"], 100)
        self.assertEqual(self.manager.personality["curiosity"], 0.7)

    def test_get_current_state(self) -> None:
        state = self.manager.get_current_state()
        self.assertEqual(state["happiness"], 100)
        self.assertEqual(state["hunger"], 0)
        self.assertEqual(state["energy"], 100)

    def test_update_state_over_time(self) -> None:
        initial_happiness = self.manager.state["happiness"]
        initial_hunger = self.manager.state["hunger"]
        initial_energy = self.manager.state["energy"]

        self.manager._update_state_over_time(1.0)

        self.assertEqual(self.manager.state["hunger"], min(100, initial_hunger + 5))
        self.assertEqual(self.manager.state["energy"], max(0, initial_energy - 10))
        self.assertEqual(self.manager.state["happiness"], max(0, initial_happiness - 2))

    def test_handle_interaction_pet(self) -> None:
        initial_happiness = self.manager.state["happiness"]
        interaction_data = {"type": "pet"}
        result = self.manager.handle_interaction(interaction_data)
        self.assertEqual(result["status"], "success")
        self.assertEqual(self.manager.state["happiness"], min(100, initial_happiness + 15 - 2)) # +15 from pet, -2 from time decay

    def test_handle_interaction_feed(self) -> None:
        self.manager.state["hunger"] = 50
        initial_happiness = self.manager.state["happiness"]
        interaction_data = {"type": "feed"}
        result = self.manager.handle_interaction(interaction_data)
        self.assertEqual(result["status"], "success")
        self.assertEqual(self.manager.state["hunger"], 20) # 50 - 30
        self.assertEqual(self.manager.state["happiness"], min(100, initial_happiness + 5 - 2)) # +5 from feed, -2 from time decay

    def test_handle_interaction_play(self) -> None:
        self.manager.state["energy"] = 50
        initial_happiness = self.manager.state["happiness"]
        interaction_data = {"type": "play"}
        result = self.manager.handle_interaction(interaction_data)
        self.assertEqual(result["status"], "success")
        self.assertEqual(self.manager.state["energy"], 29) # 50 - 20 - 1 (from time decay)
        self.assertEqual(self.manager.state["happiness"], min(100, initial_happiness + 20 - 2)) # +20 from play, -2 from time decay

    def test_handle_interaction_rest(self) -> None:
        self.manager.state["energy"] = 50
        interaction_data = {"type": "rest"}
        result = self.manager.handle_interaction(interaction_data)
        self.assertEqual(result["status"], "success")
        self.assertEqual(self.manager.state["energy"], 89) # 50 + 40 - 1 (from time decay)

    def test_handle_interaction_unknown(self) -> None:
        interaction_data = {"type": "unknown_interaction"}
        result = self.manager.handle_interaction(interaction_data)
        self.assertEqual(result["status"], "success")
        # State should still decay due to time passage
        self.assertEqual(self.manager.state["happiness"], 100) # No happiness decay from time_passed=0.1 

    def test_update_behavior_valid(self) -> None:
        new_behaviors = {"on_new_command": "wag_tail", "on_sleep": "snore"}
        self.manager.update_behavior(new_behaviors)
        self.assertEqual(self.manager.behavior_rules["on_new_command"], "wag_tail")
        self.assertEqual(self.manager.behavior_rules["on_sleep"], "snore")

    def test_update_behavior_invalid_type(self) -> None:
        original_behaviors = self.manager.behavior_rules.copy()
        new_behaviors = {"on_invalid": 123} # Invalid value type
        self.manager.update_behavior(new_behaviors)
        self.assertEqual(self.manager.behavior_rules, original_behaviors) # Should not update

    def test_update_behavior_invalid_key(self) -> None:
        original_behaviors = self.manager.behavior_rules.copy()
        new_behaviors = {123: "wag_tail"} # Invalid key type
        self.manager.update_behavior(new_behaviors)
        self.assertEqual(self.manager.behavior_rules, original_behaviors) # Should not update

if __name__ == '__main__':
    unittest.main()
