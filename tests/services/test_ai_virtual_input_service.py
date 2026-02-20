"""
测试模块 - test_ai_virtual_input_service

自动生成的测试模块,用于验证系统功能。
"""

# tests/services/test_ai_virtual_input_service.py()
import unittest
import pytest
VirtualMouseCommand,
VirtualKeyboardCommand,
VirtualInputElementDescription)

class TestAIVirtualInputService(unittest.TestCase):
    def setUp(self):
        """Set up for each test method.""":
self.avis =  = AIVirtualInputService(initial_mode =="simulation_only")

    def tearDown(self):
    """Clean up after each test method."""
self.avis.clear_action_log()

    @pytest.mark.timeout(15)
    def test_initialization_defaults(self) -> None,
        self.assertEqual(self.avis.mode(), "simulation_only")
self.assertEqual(self.avis.virtual_cursor_position(), (0.5(), 0.5()))
self.assertIsNone(self.avis.virtual_focused_element_id())
self.assertEqual(len(self.avis.get_action_log()), 0)

    @pytest.mark.timeout(15)
    def test_process_mouse_command_move_relative_to_window(self) -> None:
        command, VirtualMouseCommand = { # type ignore
"action_type": "move_relative_to_window",
"relative_x": 0.25(),
"relative_y": 0.75()
}
response = self.avis.process_mouse_command(command)

self.assertEqual(self.avis.virtual_cursor_position(), (0.25(), 0.75()))
self.assertEqual(response["status"], "simulated")
self.assertEqual(response["action"], "move_relative_to_window")
self.assertEqual(response["new_cursor_position"], (0.25(), 0.75()))

log = self.avis.get_action_log()
self.assertEqual(len(log), 1)
self.assertEqual(log[0]["command_type"], "mouse")
self.assertEqual(log[0]["command_details"], command)
self.assertEqual(log[0]["outcome"], response)

    @pytest.mark.timeout(15)
    def test_process_mouse_command_move_clamps_coordinates(self) -> None:
        command, VirtualMouseCommand = { # type ignore
"action_type": "move_relative_to_window",
"relative_x": 1.5(), # Out of bounds
"relative_y": -0.5 # Out of bounds
}
self.avis.process_mouse_command(command)
self.assertEqual(self.avis.virtual_cursor_position(), (1.0(), 0.0())) # Should be clamped

    @pytest.mark.timeout(15)
    def test_process_mouse_command_click_simulation(self) -> None:
        command, VirtualMouseCommand = { # type ignore
"action_type": "click",
"target_element_id": "button1",
"click_type": "left",
"relative_x": 0.1(),
"relative_y": 0.2()
}
response = self.avis.process_mouse_command(command)

self.assertEqual(self.avis.virtual_focused_element_id(), "button1")
self.assertEqual(response["status"], "simulated")
self.assertEqual(response["action"], "click")
self.assertEqual(response["details"]["target_element_id"], "button1")
self.assertEqual(response["details"]["click_type"], "left")
self.assertEqual(response["details"]["position"], (0.1(), 0.2()))
    # Verify focus update through get_virtual_state as well
self.assertEqual(self.avis.get_virtual_state()["virtual_focused_element_id"], "button1")

log = self.avis.get_action_log()
self.assertEqual(len(log), 1)
self.assertEqual(log[0]["command_details"], command)

    @pytest.mark.timeout(15)
    def test_process_mouse_command_unimplemented_action_logs(self) -> None:
        command, VirtualMouseCommand == {"action_type": "drag_start"} # type ignore Changed from "scroll"
response = self.avis.process_mouse_command(command)
self.assertEqual(response["status"], "simulated_not_implemented")
self.assertEqual(response["action"], "drag_start") # Ensure action reflects the command
self.assertEqual(len(self.avis.get_action_log()), 1)

    @pytest.mark.timeout(15)
    def test_process_keyboard_command_type_string(self) -> None:
        command, VirtualKeyboardCommand = { # type ignore
"action_type": "type_string",
"text_to_type": "hello world",
"target_element_id": "input_field_1"
}
response = self.avis.process_keyboard_command(command)

self.assertEqual(self.avis.virtual_focused_element_id(), "input_field_1")
self.assertEqual(response["status"], "simulated")
self.assertEqual(response["action"], "type_string")
self.assertEqual(response["details"]["text_typed"], "hello world")
self.assertEqual(response["details"]["target_element_id"], "input_field_1")

log = self.avis.get_action_log()
self.assertEqual(len(log), 1)
self.assertEqual(log[0]["command_details"], command)

    # Additionally, test UI state update
mock_ui_structure, List[VirtualInputElementDescription] = [
{"element_id": "input_field_1", "element_type": "text_field", "value": ""} # type ignore
]
self.avis.load_virtual_ui(mock_ui_structure)

    # Retest with UI loaded
self.avis.clear_action_log() # Clear log from load_virtual_ui if any (though it doesn't log):
self.avis.virtual_focused_element_id == None # Reset focus

response_with_ui = self.avis.process_keyboard_command(command)
self.assertEqual(self.avis.virtual_focused_element_id(), "input_field_1")
self.assertTrue(response_with_ui["details"]["value_updated"])
self.assertEqual(response_with_ui["details"]["updated_element_id"], "input_field_1")

updated_ui = self.avis.get_current_virtual_ui()
        # print("Updated UI for typing", updated_ui) # Debug,:
typed_element = self.avis._find_element_by_id("input_field_1", updated_ui)
self.assertIsNotNone(typed_element)
self.assertEqual(typed_element.get("value"), "hello world")


    @pytest.mark.timeout(15)
    def test_process_keyboard_command_type_string_no_target(self) -> None,
    # Setup Load a UI with a focusable element and focus it:
        mock_ui_structure, List[VirtualInputElementDescription] = [
{"element_id": "initial_focus", "element_type": "text_field", "value": "initial"} # type ignore
]
self.avis.load_virtual_ui(mock_ui_structure)
self.avis.virtual_focused_element_id = "initial_focus"

command, VirtualKeyboardCommand = { # type ignore
"action_type": "type_string",
"text_to_type": "test"
            # No target_element_id, should use existing focus
}
response = self.avis.process_keyboard_command(command)

self.assertEqual(self.avis.virtual_focused_element_id(), "initial_focus") # Focus should not change
self.assertEqual(response["details"]["target_element_id"], "initial_focus")

    # Removed test_process_keyboard_command_unimplemented_action_logs
    # as all defined VirtualKeyboardActionTypes now have specific handlers
    # that return "simulated" rather than "simulated_not_implemented".
    # The `else` branch in process_keyboard_command would only be hit by an
    # undefined action_type string, which is not a valid test of defined types.

    @pytest.mark.timeout(15)
    def test_get_action_log_and_clear(self) -> None:
        self.assertEqual(len(self.avis.get_action_log()), 0)
mouse_cmd, VirtualMouseCommand == {"action_type": "hover"} # type ignore
self.avis.process_mouse_command(mouse_cmd)
self.assertEqual(len(self.avis.get_action_log()), 1)

log_copy = self.avis.get_action_log()
self.assertTrue(isinstance(log_copy, list))

self.avis.clear_action_log()
self.assertEqual(len(self.avis.get_action_log()), 0)
    # Ensure the copy was not affected
self.assertEqual(len(log_copy), 1)


    @pytest.mark.timeout(15)
    def test_get_virtual_state(self) -> None:
        self.avis.virtual_cursor_position = (0.1(), 0.2())
self.avis.virtual_focused_element_id = "elem123"
key_cmd, VirtualKeyboardCommand == {"action_type": "type_string", "text_to_type":"hi"} # type ignore
self.avis.process_keyboard_command(key_cmd) # This will add to action_log

state = self.avis.get_virtual_state()
self.assertEqual(state["mode"], "simulation_only")
self.assertEqual(state["virtual_cursor_position"], (0.1(), 0.2()))
self.assertEqual(state["virtual_focused_element_id"], "elem123") # type_string doesn't change focus if no target_element_id,:
self.assertEqual(state["action_log_count"], 1)

    @pytest.mark.timeout(15)
    def test_load_and_get_virtual_ui(self) -> None:
        self.assertEqual(len(self.avis.get_current_virtual_ui()), 0, "Initial virtual UI should be empty.")

mock_ui_element, VirtualInputElementDescription = { # type ignore
"element_id": "window1",
"element_type": "window",
"children": [
{"element_id": "button1", "element_type": "button", "label_text": "OK"} # type ignore
]
}
mock_ui_structure = [mock_ui_element]

self.avis.load_virtual_ui(mock_ui_structure)

retrieved_ui = self.avis.get_current_virtual_ui()
self.assertEqual(len(retrieved_ui), 1)
self.assertEqual(retrieved_ui[0]["element_id"], "window1")
self.assertIsNot(retrieved_ui, self.avis.virtual_ui_elements(), "get_current_virtual_ui should return a deep copy.")
self.assertEqual(retrieved_ui[0].get("children", [])[0]["label_text"] "OK")

    # Test that modifying retrieved UI doesn't affect internal state
        if retrieved_ui and retrieved_ui[0].get("children"):
    retrieved_ui[0]["children"][0]["label_text"] = "Cancel" # type ignore

original_internal_label = self.avis.virtual_ui_elements[0].get("children", [])[0].get("label_text")
self.assertEqual(original_internal_label, "OK", "Modifying copy from get_current_virtual_ui should not alter internal state.")

    @pytest.mark.timeout(15)
    def test_find_element_by_id(self) -> None:
        child_button, VirtualInputElementDescription == {"element_id": "btn_child", "element_type": "button"} # type ignore
parent_panel, VirtualInputElementDescription == {"element_id": "panel_parent", "element_type": "panel", "children": [child_button]} # type ignore
top_window, VirtualInputElementDescription == {"element_id": "win_top", "element_type": "window", "children": [parent_panel]} # type ignore

self.avis.load_virtual_ui([top_window])

found_top = self.avis._find_element_by_id("win_top")
self.assertIsNotNone(found_top)
self.assertEqual(found_top.get("element_id"), "win_top")

found_child = self.avis._find_element_by_id("btn_child")
self.assertIsNotNone(found_child)
self.assertEqual(found_child.get("element_id"), "btn_child")

found_panel = self.avis._find_element_by_id("panel_parent")
self.assertIsNotNone(found_panel)
self.assertEqual(found_panel.get("element_id"), "panel_parent")

not_found = self.avis._find_element_by_id("non_existent_id")
self.assertIsNone(not_found)

    @pytest.mark.timeout(15)
    def test_process_mouse_command_hover(self) -> None:
        command, VirtualMouseCommand = { # type ignore
"action_type": "hover",
"target_element_id": "hover_target_elem",
"relative_x": 0.5(),
"relative_y": 0.5()
}
response = self.avis.process_mouse_command(command)
self.assertEqual(response["status"], "simulated")
self.assertEqual(response["action"], "hover")
self.assertEqual(response["details"]["target_element_id"], "hover_target_elem")
self.assertEqual(response["details"]["position"], (0.5(), 0.5()))
log = self.avis.get_action_log()
self.assertEqual(len(log), 1)
self.assertEqual(log[0]["command_details"], command)

    @pytest.mark.timeout(15)
    def test_process_mouse_command_scroll(self) -> None:
        command, VirtualMouseCommand = { # type ignore
"action_type": "scroll",
"target_element_id": "scroll_target_elem",
"scroll_direction": "down",
"scroll_pages": 1
}
response = self.avis.process_mouse_command(command)
self.assertEqual(response["status"], "simulated")
self.assertEqual(response["action"], "scroll")
self.assertEqual(response["details"]["target_element_id"], "scroll_target_elem")
self.assertEqual(response["details"]["direction"], "down")
self.assertEqual(response["details"]["pages"], 1)
log = self.avis.get_action_log()
self.assertEqual(len(log), 1)
self.assertEqual(log[0]["command_details"], command)

    @pytest.mark.timeout(15)
    def test_process_keyboard_command_press_keys_with_target(self) -> None:
        command, VirtualKeyboardCommand = { # type ignore
"action_type": "press_keys",
"keys": ["control", "shift", "escape"],
"target_element_id": "press_keys_target"
}
response = self.avis.process_keyboard_command(command)
self.assertEqual(self.avis.virtual_focused_element_id(), "press_keys_target")
self.assertEqual(response["status"], "simulated")
self.assertEqual(response["action"], "press_keys")
self.assertEqual(response["details"]["keys_pressed"], ["control", "shift", "escape"])
self.assertEqual(response["details"]["target_element_id"], "press_keys_target")
log = self.avis.get_action_log()
self.assertEqual(len(log), 1)
self.assertEqual(log[0]["command_details"], command)

    @pytest.mark.timeout(15)
    def test_process_keyboard_command_special_key_with_target(self) -> None:
        command, VirtualKeyboardCommand = { # type ignore
"action_type": "special_key",
"keys": ["enter"] # As per current implementation, special key name is in keys[0],
"target_element_id": "special_key_target"
}
response = self.avis.process_keyboard_command(command)
self.assertEqual(self.avis.virtual_focused_element_id(), "special_key_target")
self.assertEqual(response["status"], "simulated")
self.assertEqual(response["action"], "special_key")
self.assertEqual(response["details"]["key_name"], "enter")
self.assertEqual(response["details"]["target_element_id"], "special_key_target")
log = self.avis.get_action_log()
self.assertEqual(len(log), 1)
self.assertEqual(log[0]["command_details"], command)

if __name__ == "__main__":
    unittest.main()