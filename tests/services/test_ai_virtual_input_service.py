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
    VirtualInputPermissionLevel,
    AIPermissionSet,
    ExecutionResult,
    VirtualInputElementDescription # Make sure this is imported
)
from unittest.mock import MagicMock, patch

# Mock AISimulationControlService for testing AIVirtualInputService in isolation
# We can patch it where AIVisualInputService tries to import it, or pass a mock.
# For now, let's design tests to allow injecting a mock.

class TestAIVirtualInputService(unittest.TestCase):

    def setUp(self):
        """Set up for each test method."""
        # Mock AISimulationControlService
        self.mock_sim_control_service = MagicMock()
        self.mock_sim_control_service.get_current_ai_permissions.return_value = {
            "can_execute_code": True, "can_read_sim_hw_status": True
        }
        self.mock_sim_control_service.get_sim_hardware_status.return_value = {
            "profile_name": "TestHWProfile", "cpu_cores": 4
        }
        self.mock_sim_control_service.execute_ai_code.return_value = { # type: ignore
            "request_id": "test-req-123",
            "execution_success": True,
            "script_exit_code": 0,
            "stdout": "Mock code execution success",
            "stderr": "",
            "status_message": "Execution completed."
        }

        # Mock ResourceAwarenessService
        self.mock_resource_service = MagicMock()

        # Mock SandboxExecutor
        self.mock_sandbox_executor = MagicMock()

        self.avis = AIVirtualInputService(
            initial_mode="simulation_only",
            resource_awareness_service=self.mock_resource_service,
            sandbox_executor=self.mock_sandbox_executor # Pass SandboxExecutor
        )
        # Replace the internally created AISimulationControlService with our mock for fine-grained testing
        # This allows us to assert calls on mock_sim_control_service without needing to
        # also mock what AISimulationControlService passes to SandboxExecutor.
        self.avis.ai_simulation_control_service = self.mock_sim_control_service


        # Define standard UI elements that will be used in multiple tests
        self.code_editor_el: VirtualInputElementDescription = {"element_id": "code_editor", "element_type": "text_area", "value": ""} # type: ignore
        self.run_button_el: VirtualInputElementDescription = {"element_id": "run_code_button", "element_type": "button"} # type: ignore
        self.output_display_el: VirtualInputElementDescription = {"element_id": "code_output_display", "element_type": "text_area", "value": "", "read_write": False} # type: ignore
        self.perm_display_el: VirtualInputElementDescription = {"element_id": "ai_permissions_display", "element_type": "text_area", "value": "", "read_write": False} # type: ignore
        self.hw_display_el: VirtualInputElementDescription = {"element_id": "sim_hw_status_display", "element_type": "text_area", "value": "", "read_write": False} # type: ignore

        self.full_test_ui: List[VirtualInputElementDescription] = [
            self.code_editor_el, self.run_button_el, self.output_display_el,
            self.perm_display_el, self.hw_display_el
        ]


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
        # Verify focus update through get_virtual_state as well
        self.assertEqual(self.avis.get_virtual_state()["virtual_focused_element_id"], "button1")

        log = self.avis.get_action_log()
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]["command_details"], command)

    def test_process_mouse_command_unimplemented_action_logs(self):
        command: VirtualMouseCommand = {"action_type": "drag_start"} # type: ignore Changed from "scroll"
        response = self.avis.process_mouse_command(command)
        self.assertEqual(response["status"], "simulated_not_implemented")
        self.assertEqual(response["action"], "drag_start") # Ensure action reflects the command
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

        # Additionally, test UI state update
        mock_ui_structure: List[VirtualInputElementDescription] = [
            {"element_id": "input_field_1", "element_type": "text_field", "value": ""} # type: ignore
        ]
        self.avis.load_virtual_ui(mock_ui_structure)

        # Retest with UI loaded
        self.avis.clear_action_log() # Clear log from load_virtual_ui if any (though it doesn't log)
        self.avis.virtual_focused_element_id = None # Reset focus

        response_with_ui = self.avis.process_keyboard_command(command)
        self.assertEqual(self.avis.virtual_focused_element_id, "input_field_1")
        self.assertTrue(response_with_ui["details"]["value_updated"])
        self.assertEqual(response_with_ui["details"]["updated_element_id"], "input_field_1")

        updated_ui = self.avis.get_current_virtual_ui()
        # print("Updated UI for typing:", updated_ui) # Debug
        typed_element = self.avis._find_element_by_id("input_field_1", updated_ui)
        self.assertIsNotNone(typed_element)
        self.assertEqual(typed_element.get("value"), "hello world")


    def test_process_keyboard_command_type_string_no_target(self):
        # Setup: Load a UI with a focusable element and focus it
        mock_ui_structure: List[VirtualInputElementDescription] = [
            {"element_id": "initial_focus", "element_type": "text_field", "value": "initial"} # type: ignore
        ]
        self.avis.load_virtual_ui(mock_ui_structure)
        self.avis.virtual_focused_element_id = "initial_focus"

        command: VirtualKeyboardCommand = { # type: ignore
            "action_type": "type_string",
            "text_to_type": "test"
            # No target_element_id, should use existing focus
        }
        response = self.avis.process_keyboard_command(command)

        self.assertEqual(self.avis.virtual_focused_element_id, "initial_focus") # Focus should not change
        self.assertEqual(response["details"]["target_element_id"], "initial_focus")

    # Removed test_process_keyboard_command_unimplemented_action_logs
    # as all defined VirtualKeyboardActionTypes now have specific handlers
    # that return "simulated" rather than "simulated_not_implemented".
    # The `else` branch in process_keyboard_command would only be hit by an
    # undefined action_type string, which is not a valid test of defined types.

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

    def test_load_and_get_virtual_ui(self):
        self.assertEqual(len(self.avis.get_current_virtual_ui()), 0, "Initial virtual UI should be empty.")

        mock_ui_element: VirtualInputElementDescription = { # type: ignore
            "element_id": "window1",
            "element_type": "window",
            "children": [
                {"element_id": "button1", "element_type": "button", "label_text": "OK"} # type: ignore
            ]
        }
        mock_ui_structure = [mock_ui_element]

        self.avis.load_virtual_ui(mock_ui_structure)

        retrieved_ui = self.avis.get_current_virtual_ui()
        self.assertEqual(len(retrieved_ui), 1)
        self.assertEqual(retrieved_ui[0]["element_id"], "window1")
        self.assertIsNot(retrieved_ui, self.avis.virtual_ui_elements, "get_current_virtual_ui should return a deep copy.")
        self.assertEqual(retrieved_ui[0].get("children", [])[0]["label_text"], "OK")

        # Test that modifying retrieved UI doesn't affect internal state
        if retrieved_ui and retrieved_ui[0].get("children"):
            retrieved_ui[0]["children"][0]["label_text"] = "Cancel" # type: ignore

        original_internal_label = self.avis.virtual_ui_elements[0].get("children", [])[0].get("label_text")
        self.assertEqual(original_internal_label, "OK", "Modifying copy from get_current_virtual_ui should not alter internal state.")

    def test_find_element_by_id(self):
        child_button: VirtualInputElementDescription = {"element_id": "btn_child", "element_type": "button"} # type: ignore
        parent_panel: VirtualInputElementDescription = {"element_id": "panel_parent", "element_type": "panel", "children": [child_button]} # type: ignore
        top_window: VirtualInputElementDescription = {"element_id": "win_top", "element_type": "window", "children": [parent_panel]} # type: ignore

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

    def test_process_mouse_command_hover(self):
        command: VirtualMouseCommand = { # type: ignore
            "action_type": "hover",
            "target_element_id": "hover_target_elem",
            "relative_x": 0.5,
            "relative_y": 0.5
        }
        response = self.avis.process_mouse_command(command)
        self.assertEqual(response["status"], "simulated")
        self.assertEqual(response["action"], "hover")
        self.assertEqual(response["details"]["target_element_id"], "hover_target_elem")
        self.assertEqual(response["details"]["position"], (0.5, 0.5))
        log = self.avis.get_action_log()
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]["command_details"], command)

    def test_process_mouse_command_scroll(self):
        command: VirtualMouseCommand = { # type: ignore
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

    def test_process_keyboard_command_press_keys_with_target(self):
        command: VirtualKeyboardCommand = { # type: ignore
            "action_type": "press_keys",
            "keys": ["control", "shift", "escape"],
            "target_element_id": "press_keys_target"
        }
        response = self.avis.process_keyboard_command(command)
        self.assertEqual(self.avis.virtual_focused_element_id, "press_keys_target")
        self.assertEqual(response["status"], "simulated")
        self.assertEqual(response["action"], "press_keys")
        self.assertEqual(response["details"]["keys_pressed"], ["control", "shift", "escape"])
        self.assertEqual(response["details"]["target_element_id"], "press_keys_target")
        log = self.avis.get_action_log()
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]["command_details"], command)

    def test_process_keyboard_command_special_key_with_target(self):
        command: VirtualKeyboardCommand = { # type: ignore
            "action_type": "special_key",
            "keys": ["enter"], # As per current implementation, special key name is in keys[0]
            "target_element_id": "special_key_target"
        }
        response = self.avis.process_keyboard_command(command)
        self.assertEqual(self.avis.virtual_focused_element_id, "special_key_target")
        self.assertEqual(response["status"], "simulated")
        self.assertEqual(response["action"], "special_key")
        self.assertEqual(response["details"]["key_name"], "enter")
        self.assertEqual(response["details"]["target_element_id"], "special_key_target")
        log = self.avis.get_action_log()
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]["command_details"], command)

if __name__ == '__main__':
    unittest.main()


    # --- New Tests for AISimulationControlService Integration ---

    def test_initialization_with_sim_control_service(self):
        # Test that AVIS initializes AISimulationControlService and fetches initial status
        self.avis.ai_simulation_control_service.get_current_ai_permissions.assert_called_once()
        self.avis.ai_simulation_control_service.get_sim_hardware_status.assert_called_once()

        self.assertEqual(self.avis.current_ai_permissions["can_execute_code"], True)
        self.assertEqual(self.avis.current_sim_hardware_status["profile_name"], "TestHWProfile")

    def test_refresh_simulation_status(self):
        # Reset call counts for this specific test
        self.avis.ai_simulation_control_service.get_current_ai_permissions.reset_mock()
        self.avis.ai_simulation_control_service.get_sim_hardware_status.reset_mock()

        # Load UI that includes display elements
        self.avis.load_virtual_ui(self.full_test_ui)

        # Change the mock return values for the next call
        self.mock_sim_control_service.get_current_ai_permissions.return_value = {
            "can_execute_code": False, "can_read_sim_hw_status": False
        }
        self.mock_sim_control_service.get_sim_hardware_status.return_value = {
            "profile_name": "RefreshedProfile", "cpu_cores": 8
        }

        self.avis.refresh_simulation_status()

        self.avis.ai_simulation_control_service.get_current_ai_permissions.assert_called_once()
        self.avis.ai_simulation_control_service.get_sim_hardware_status.assert_called_once()

        self.assertFalse(self.avis.current_ai_permissions["can_execute_code"])
        self.assertEqual(self.avis.current_sim_hardware_status["profile_name"], "RefreshedProfile")

        # Check if UI display elements were updated
        perm_display = self.avis._find_element_by_id("ai_permissions_display")
        self.assertIn("CodeExec=False", perm_display.get("value", "")) # type: ignore
        hw_display = self.avis._find_element_by_id("sim_hw_status_display")
        self.assertIn("Profile=RefreshedProfile", hw_display.get("value", "")) # type: ignore
        self.assertIn("CPU=8 cores", hw_display.get("value", "")) # type: ignore


    def test_process_mouse_command_click_run_code_button(self):
        self.avis.load_virtual_ui(self.full_test_ui)

        # Set some code in the code editor element
        code_editor = self.avis._find_element_by_id("code_editor")
        test_code = "print('Hello AVIS from test')"
        code_editor["value"] = test_code # type: ignore

        click_command: VirtualMouseCommand = { # type: ignore
            "action_type": "click",
            "target_element_id": "run_code_button"
        }
        response = self.avis.process_mouse_command(click_command)

        self.assertEqual(response["status"], "simulated")
        self.assertEqual(response["details"].get("triggered_action"), "code_execution")

        # Verify that AISimulationControlService.execute_ai_code was called correctly
        self.avis.ai_simulation_control_service.execute_ai_code.assert_called_once_with(
            test_code,
            self.avis.current_ai_permissions # Should pass its current permissions
        )

        # Verify that the output display was updated
        output_display = self.avis._find_element_by_id("code_output_display")
        self.assertIn("Mock code execution success", output_display.get("value", "")) # type: ignore
        self.assertIn("test-req-123", output_display.get("value", "")) # type: ignore

    def test_process_mouse_command_click_run_code_button_no_editor(self):
        # UI without a code editor
        ui_no_editor = [self.run_button_el, self.output_display_el]
        self.avis.load_virtual_ui(ui_no_editor)

        click_command: VirtualMouseCommand = { # type: ignore
            "action_type": "click",
            "target_element_id": "run_code_button"
        }
        response = self.avis.process_mouse_command(click_command)
        self.assertEqual(response["details"].get("triggered_action"), "code_execution_failed_no_editor")
        self.avis.ai_simulation_control_service.execute_ai_code.assert_not_called()


    def test_process_code_execution_command_direct_call(self):
        self.avis.load_virtual_ui(self.full_test_ui) # Ensure output element exists
        test_code = "print('Direct call test')"

        self.avis.process_code_execution_command(test_code)

        self.avis.ai_simulation_control_service.execute_ai_code.assert_called_once_with(
            test_code,
            self.avis.current_ai_permissions
        )
        output_display = self.avis._find_element_by_id("code_output_display")
        self.assertIn("Mock code execution success", output_display.get("value", "")) # type: ignore

    def test_process_code_execution_command_no_sim_control_service(self):
        self.avis.load_virtual_ui(self.full_test_ui)
        self.avis.ai_simulation_control_service = None # Simulate service not available

        test_code = "print('This will fail')"
        self.avis.process_code_execution_command(test_code)

        output_display = self.avis._find_element_by_id("code_output_display")
        self.assertEqual(output_display.get("value", ""), "Error: AISimulationControlService not available.") # type: ignore

    def test_info_displays_populated_on_init_via_refresh(self):
        # This test relies on _update_info_display_elements being called after status fetch in __init__
        # (which happens if refresh_simulation_status is called or its parts are)
        # We need to ensure AIVS calls _update_info_display_elements after its own init.
        # The current AIVS __init__ calls parts of refresh_simulation_status internally.
        # Let's re-initialize AVIS with a UI already loaded to test this path.

        # For this test, we need to ensure _update_info_display_elements is called by __init__
        # The current structure of AIVS __init__ gets permissions/status,
        # then _update_info_display_elements is called by refresh_simulation_status.
        # AIVS.__init__ does not explicitly call refresh_simulation_status.
        # It *does* call the underlying service methods to get the status.
        # Let's ensure the _update_info_display_elements is called during/after load_virtual_ui or refresh.

        # Test setup: Create a new AVIS instance, then load UI, then refresh.
        avis_for_init_test = AIVirtualInputService(
            resource_awareness_service=self.mock_resource_service,
            sandbox_executor=self.mock_sandbox_executor # Use sandbox_executor
        )
        avis_for_init_test.ai_simulation_control_service = self.mock_sim_control_service # Inject mock

        avis_for_init_test.load_virtual_ui(self.full_test_ui) # Load UI
        avis_for_init_test.refresh_simulation_status() # Explicitly refresh to trigger UI update

        perm_display = avis_for_init_test._find_element_by_id("ai_permissions_display")
        self.assertIn("CodeExec=True", perm_display.get("value", "")) # type: ignore
        hw_display = avis_for_init_test._find_element_by_id("sim_hw_status_display")
        self.assertIn("Profile=TestHWProfile", hw_display.get("value", "")) # type: ignore
        self.assertIn("CPU=4 cores", hw_display.get("value", "")) # type: ignore

    # --- Tests for Virtual File System Operations ---

    def test_virtual_file_system_initialization(self):
        """Test that the virtual file system is empty upon AVIS initialization."""
        self.assertEqual(self.avis.virtual_file_system, {})

    def test_load_virtual_files(self):
        """Test loading files into the virtual file system."""
        # Test loading into an empty FS
        files_to_load1 = {
            "src/main.py": "print('hello')",
            "data/config.txt": "key=value"
        }
        self.avis.load_virtual_files(files_to_load1)
        self.assertEqual(self.avis.virtual_file_system, files_to_load1)
        # Ensure it's a copy
        self.assertIsNot(self.avis.virtual_file_system, files_to_load1)

        # Test that loading new files replaces the old FS
        files_to_load2 = {
            "docs/readme.md": "# Project Readme"
        }
        self.avis.load_virtual_files(files_to_load2)
        self.assertEqual(self.avis.virtual_file_system, files_to_load2)
        self.assertNotEqual(self.avis.virtual_file_system, files_to_load1)

        # Test loading empty dictionary
        self.avis.load_virtual_files({})
        self.assertEqual(self.avis.virtual_file_system, {})

    def test_clear_virtual_files(self):
        """Test clearing the virtual file system."""
        files_to_load = {
            "src/main.py": "print('hello')"
        }
        self.avis.load_virtual_files(files_to_load)
        self.assertNotEqual(self.avis.virtual_file_system, {}) # Ensure it's not empty

        self.avis.clear_virtual_files()
        self.assertEqual(self.avis.virtual_file_system, {})

    def test_process_file_op_read_file_exists(self):
        """Test reading an existing file from the virtual file system."""
        file_path = "src/readable.py"
        file_content = "print('I am readable')"
        self.avis.load_virtual_files({file_path: file_content})

        command: Dict[str, Any] = { # Using Dict for easier construction than exact AVISFileOperationCommand
            "action_type": "file_operation",
            "operation": "read_file",
            "path": file_path
        }
        response = self.avis.process_file_operation_command(command) # type: ignore

        self.assertEqual(response["status"], "success")
        self.assertEqual(response.get("content"), file_content)
        self.assertIn(f"Successfully read virtual file: {file_path}", response.get("message", ""))

        # Check logs
        log = self.avis.get_action_log()
        self.assertEqual(len(log), 1) # Assuming log is cleared by tearDown or setUp
        self.assertEqual(log[0]["command_type"], "file_operation")
        self.assertEqual(log[0]["command_details"], command)
        self.assertEqual(log[0]["outcome"]["status"], "success")


    def test_process_file_op_read_file_not_exists(self):
        """Test reading a non-existent file from the virtual file system."""
        self.avis.load_virtual_files({"some/other_file.txt": "content"}) # Ensure FS is not empty but target is missing

        command: Dict[str, Any] = {
            "action_type": "file_operation",
            "operation": "read_file",
            "path": "src/non_existent.py"
        }
        response = self.avis.process_file_operation_command(command) # type: ignore

        self.assertEqual(response["status"], "error_file_not_found")
        self.assertIsNone(response.get("content"))
        self.assertIn(f"Virtual file not found: {command['path']}", response.get("message", ""))

    def test_process_file_op_write_file_new(self):
        """Test writing a new file to the virtual file system."""
        file_path = "gen/new_file.txt"
        file_content = "This is a newly written file."
        command: Dict[str, Any] = {
            "action_type": "file_operation",
            "operation": "write_file",
            "path": file_path,
            "content": file_content
        }
        response = self.avis.process_file_operation_command(command) # type: ignore

        self.assertEqual(response["status"], "success")
        self.assertIn(f"Successfully wrote to virtual file: {file_path}", response.get("message", ""))
        self.assertEqual(self.avis.virtual_file_system.get(file_path), file_content)

        log = self.avis.get_action_log()
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]["outcome"]["status"], "success")

    def test_process_file_op_write_file_overwrite(self):
        """Test overwriting an existing file in the virtual file system."""
        file_path = "config/settings.ini"
        initial_content = "old_setting=true"
        new_content = "new_setting=false\nanother_setting=123"
        self.avis.load_virtual_files({file_path: initial_content})

        command: Dict[str, Any] = {
            "action_type": "file_operation",
            "operation": "write_file",
            "path": file_path,
            "content": new_content
        }
        response = self.avis.process_file_operation_command(command) # type: ignore

        self.assertEqual(response["status"], "success")
        self.assertEqual(self.avis.virtual_file_system.get(file_path), new_content)

    def test_process_file_op_write_file_empty_content(self):
        """Test writing empty content to a file."""
        file_path = "empty_file.md"
        command: Dict[str, Any] = {
            "action_type": "file_operation",
            "operation": "write_file",
            "path": file_path,
            "content": "" # Empty string
        }
        response = self.avis.process_file_operation_command(command) # type: ignore
        self.assertEqual(response["status"], "success")
        self.assertEqual(self.avis.virtual_file_system.get(file_path), "")

        # Test writing with content=None (should also result in empty string as per current implementation)
        command_none_content: Dict[str, Any] = {
            "action_type": "file_operation",
            "operation": "write_file",
            "path": "none_content_file.txt",
            "content": None
        }
        self.avis.clear_action_log() # Clear log from previous operation in this test
        response_none = self.avis.process_file_operation_command(command_none_content) # type: ignore
        self.assertEqual(response_none["status"], "success")
        self.assertEqual(self.avis.virtual_file_system.get("none_content_file.txt"), "")

    def test_process_file_op_list_directory(self):
        """Test listing directory contents from the virtual file system."""
        files_structure = {
            "dir1/fileA.txt": "contentA",
            "dir1/subdirB/fileB.txt": "contentB",
            "dir1/another_file.log": "log data",
            "fileC.txt": "contentC",
            "empty_dir/": "" # Representing an empty directory conceptually by its path ending in /
                             # The actual AVIS list_directory logic might not need this if it infers dirs from paths.
        }
        self.avis.load_virtual_files(files_structure)

        # Test listing root (conceptual "/") - AVIS code treats "" or "/" as root for listing
        # The current AVIS list_directory logic might not support a true "root" listing well without a common prefix.
        # Let's test based on its current behavior: listing items that don't have a '/' before their first segment.
        # Or, more accurately, how it segments paths.
        # The code iterates all keys. If path_prefix is "", it lists all top-level items.

        # Test listing root (empty path implies root for the current AVIS logic)
        cmd_root: Dict[str, Any] = {"action_type": "file_operation", "operation": "list_directory", "path": ""}
        res_root = self.avis.process_file_operation_command(cmd_root) # type: ignore
        self.assertEqual(res_root["status"], "success", "Listing root should succeed")
        # Expected: items in the "root" of the flat virtual_file_system keys.
        # The AVIS list_directory logic creates a pseudo-hierarchy.
        # For path="", it should list "dir1/" and "fileC.txt", "empty_dir/"
        expected_root_listing = sorted(["dir1/", "fileC.txt", "empty_dir/"])
        self.assertEqual(sorted(res_root.get("directory_listing", [])), expected_root_listing)


        # Test listing "dir1/"
        cmd_dir1: Dict[str, Any] = {"action_type": "file_operation", "operation": "list_directory", "path": "dir1/"}
        res_dir1 = self.avis.process_file_operation_command(cmd_dir1) # type: ignore
        self.assertEqual(res_dir1["status"], "success")
        expected_dir1_listing = sorted(["fileA.txt", "subdirB/", "another_file.log"])
        self.assertEqual(sorted(res_dir1.get("directory_listing", [])), expected_dir1_listing)

        # Test listing "dir1/subdirB/"
        cmd_subdirB: Dict[str, Any] = {"action_type": "file_operation", "operation": "list_directory", "path": "dir1/subdirB/"}
        res_subdirB = self.avis.process_file_operation_command(cmd_subdirB) # type: ignore
        self.assertEqual(res_subdirB["status"], "success")
        self.assertEqual(sorted(res_subdirB.get("directory_listing", [])), ["fileB.txt"])

        # Test listing an "empty_dir/" (which is empty of files but exists as a prefix)
        # The current logic might show it as empty or might depend on how it's defined.
        # If "empty_dir/" key exists, it implies it's a known path.
        # If we query "empty_dir/", it should list things *under* it. Since nothing is, it should be empty.
        cmd_empty_dir: Dict[str, Any] = {"action_type": "file_operation", "operation": "list_directory", "path": "empty_dir/"}
        res_empty_dir = self.avis.process_file_operation_command(cmd_empty_dir) # type: ignore
        self.assertEqual(res_empty_dir["status"], "success")
        self.assertEqual(res_empty_dir.get("directory_listing", []), [])

        # Test listing a non-existent directory
        cmd_non_existent: Dict[str, Any] = {"action_type": "file_operation", "operation": "list_directory", "path": "non_existent_dir/"}
        res_non_existent = self.avis.process_file_operation_command(cmd_non_existent) # type: ignore
        self.assertEqual(res_non_existent["status"], "error_file_not_found") # Or some path_not_found error

        # Test listing a path that is a file
        cmd_list_file: Dict[str, Any] = {"action_type": "file_operation", "operation": "list_directory", "path": "fileC.txt"}
        res_list_file = self.avis.process_file_operation_command(cmd_list_file) # type: ignore
        self.assertEqual(res_list_file["status"], "error_other") # As per AVIS code: path is a file
        self.assertIn("is a file, not a directory", res_list_file.get("message", ""))

        # Test listing a path that is a prefix but not explicitly ending with / in command
        cmd_dir1_no_slash: Dict[str, Any] = {"action_type": "file_operation", "operation": "list_directory", "path": "dir1"}
        res_dir1_no_slash = self.avis.process_file_operation_command(cmd_dir1_no_slash) # type: ignore
        self.assertEqual(res_dir1_no_slash["status"], "success")
        self.assertEqual(sorted(res_dir1_no_slash.get("directory_listing", [])), expected_dir1_listing)
