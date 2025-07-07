# tests/services/test_ai_virtual_input_service.py
import unittest
from typing import Tuple, Optional, List, Dict, Any

# Assuming 'src' is a top-level package in the test execution context
from src.services.ai_virtual_input_service import AIVirtualInputService
from src.shared.types.common_types import (
    VirtualMouseCommand,
    VirtualKeyboardCommand,
    VirtualMouseEventType,
    VirtualKeyboardActionType,
    VirtualInputPermissionLevel
)

class TestAIVirtualInputService(unittest.TestCase):

    def setUp(self):
        """Set up for each test method."""
        self.avis = AIVirtualInputService(initial_mode="simulation_only")

    def tearDown(self):
        """Clean up after each test method."""
        self.avis.clear_action_log()

    def test_initialization_defaults(self):
        self.assertEqual(self.avis.mode, "simulation_only")
        self.assertEqual(self.avis.virtual_cursor_position, (0.5, 0.5))
        self.assertIsNone(self.avis.virtual_focused_element_id)
        self.assertEqual(len(self.avis.get_action_log()), 0)

    def test_process_mouse_command_move_relative_to_window(self):
        command: VirtualMouseCommand = { # type: ignore
            "action_type": "move_relative_to_window",
            "relative_x": 0.25,
            "relative_y": 0.75
        }
        response = self.avis.process_mouse_command(command)

        self.assertEqual(self.avis.virtual_cursor_position, (0.25, 0.75))
        self.assertEqual(response["status"], "simulated")
        self.assertEqual(response["action"], "move_relative_to_window")
        self.assertEqual(response["new_cursor_position"], (0.25, 0.75))

        log = self.avis.get_action_log()
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]["command_type"], "mouse")
        self.assertEqual(log[0]["command_details"], command)
        self.assertEqual(log[0]["outcome"], response)

    def test_process_mouse_command_move_clamps_coordinates(self):
        command: VirtualMouseCommand = { # type: ignore
            "action_type": "move_relative_to_window",
            "relative_x": 1.5, # Out of bounds
            "relative_y": -0.5 # Out of bounds
        }
        self.avis.process_mouse_command(command)
        self.assertEqual(self.avis.virtual_cursor_position, (1.0, 0.0)) # Should be clamped

    def test_process_mouse_command_click_simulation(self):
        command: VirtualMouseCommand = { # type: ignore
            "action_type": "click",
            "target_element_id": "button1",
            "click_type": "left",
            "relative_x": 0.1,
            "relative_y": 0.2
        }
        response = self.avis.process_mouse_command(command)

        self.assertEqual(self.avis.virtual_focused_element_id, "button1")
        self.assertEqual(response["status"], "simulated")
        self.assertEqual(response["action"], "click")
        self.assertEqual(response["details"]["target_element_id"], "button1")
        self.assertEqual(response["details"]["click_type"], "left")
        self.assertEqual(response["details"]["position"], (0.1, 0.2))

        log = self.avis.get_action_log()
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]["command_details"], command)

    def test_process_mouse_command_unimplemented_action_logs(self):
        command: VirtualMouseCommand = {"action_type": "scroll"} # type: ignore
        response = self.avis.process_mouse_command(command)
        self.assertEqual(response["status"], "simulated_not_implemented")
        self.assertEqual(response["action"], "scroll")
        self.assertEqual(len(self.avis.get_action_log()), 1)

    def test_process_keyboard_command_type_string(self):
        command: VirtualKeyboardCommand = { # type: ignore
            "action_type": "type_string",
            "text_to_type": "hello world",
            "target_element_id": "input_field_1"
        }
        response = self.avis.process_keyboard_command(command)

        self.assertEqual(self.avis.virtual_focused_element_id, "input_field_1")
        self.assertEqual(response["status"], "simulated")
        self.assertEqual(response["action"], "type_string")
        self.assertEqual(response["details"]["text_typed"], "hello world")
        self.assertEqual(response["details"]["target_element_id"], "input_field_1")

        log = self.avis.get_action_log()
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]["command_details"], command)

    def test_process_keyboard_command_type_string_no_target(self):
        self.avis.virtual_focused_element_id = "initial_focus"
        command: VirtualKeyboardCommand = { # type: ignore
            "action_type": "type_string",
            "text_to_type": "test"
            # No target_element_id, should use existing focus
        }
        response = self.avis.process_keyboard_command(command)

        self.assertEqual(self.avis.virtual_focused_element_id, "initial_focus") # Focus should not change
        self.assertEqual(response["details"]["target_element_id"], "initial_focus")


    def test_process_keyboard_command_unimplemented_action_logs(self):
        command: VirtualKeyboardCommand = {"action_type": "press_keys", "keys": ["ctrl", "c"]} # type: ignore
        response = self.avis.process_keyboard_command(command)
        self.assertEqual(response["status"], "simulated_not_implemented")
        self.assertEqual(response["action"], "press_keys")
        self.assertEqual(len(self.avis.get_action_log()), 1)

    def test_get_action_log_and_clear(self):
        self.assertEqual(len(self.avis.get_action_log()), 0)
        mouse_cmd: VirtualMouseCommand = {"action_type": "hover"} # type: ignore
        self.avis.process_mouse_command(mouse_cmd)
        self.assertEqual(len(self.avis.get_action_log()), 1)

        log_copy = self.avis.get_action_log()
        self.assertTrue(isinstance(log_copy, list))

        self.avis.clear_action_log()
        self.assertEqual(len(self.avis.get_action_log()), 0)
        # Ensure the copy was not affected
        self.assertEqual(len(log_copy), 1)


    def test_get_virtual_state(self):
        self.avis.virtual_cursor_position = (0.1, 0.2)
        self.avis.virtual_focused_element_id = "elem123"
        key_cmd: VirtualKeyboardCommand = {"action_type": "type_string", "text_to_type":"hi"} # type: ignore
        self.avis.process_keyboard_command(key_cmd) # This will add to action_log

        state = self.avis.get_virtual_state()
        self.assertEqual(state["mode"], "simulation_only")
        self.assertEqual(state["virtual_cursor_position"], (0.1, 0.2))
        self.assertEqual(state["virtual_focused_element_id"], "elem123") # type_string doesn't change focus if no target_element_id
        self.assertEqual(state["action_log_count"], 1)

if __name__ == '__main__':
    unittest.main()
