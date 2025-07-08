# tests/agents/test_simple_coding_agent.py
import unittest
from unittest.mock import MagicMock, call

# Adjust path to import from src
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
sys.path.insert(0, project_root)

from src.agents.simple_coding_agent import SimpleCodingAgent
# from src.services.ai_virtual_input_service import AIVirtualInputService # For type hinting if needed
from src.shared.types.common_types import VirtualInputElementDescription, VirtualKeyboardCommand, VirtualMouseCommand

from typing import Any, List, Optional # Added Any, List, Optional for type hints

# Use Any for AIVirtualInputService type hint to match the agent's current type hint
AIVirtualInputServiceType = Any

class TestSimpleCodingAgent(unittest.TestCase):

    def setUp(self):
        self.mock_avis_service = MagicMock() # spec=AIVirtualInputService later if full typing
        self.agent = SimpleCodingAgent(avis_service=self.mock_avis_service)

        # Define expected UI element IDs
        self.code_editor_id = "code_editor"
        self.run_button_id = "run_code_button"
        self.output_display_id = "code_output_display"
        self.perm_display_id = "ai_permissions_display"
        self.hw_display_id = "sim_hw_status_display"

        # Default mock return values for AVIS methods
        self.mock_avis_service.get_current_virtual_ui.return_value = [] # Default to empty UI
        self.mock_avis_service.process_keyboard_command.return_value = {"status": "simulated", "details": {}}
        self.mock_avis_service.process_mouse_command.return_value = {"status": "simulated", "details": {}}

    def _setup_mock_ui_for_element_value(self, element_id: str, value: str):
        """Helper to set up mock AVIS UI for _get_avis_ui_element_value tests."""
        mock_ui: List[VirtualInputElementDescription] = [
            {"element_id": element_id, "element_type": "text_area", "value": value} # type: ignore
        ]
        self.mock_avis_service.get_current_virtual_ui.return_value = mock_ui

    def test_initialization(self):
        self.assertEqual(self.agent.avis, self.mock_avis_service)
        self.assertEqual(self.agent.task_step, 0)
        self.assertIsNotNone(self.agent.calculation_code)

    def test_get_avis_ui_element_value_found(self):
        test_id = "test_el_1"
        test_value = "Hello Value"
        self._setup_mock_ui_for_element_value(test_id, test_value)

        value = self.agent._get_avis_ui_element_value(test_id)
        self.assertEqual(value, test_value)
        self.mock_avis_service.get_current_virtual_ui.assert_called_once()

    def test_get_avis_ui_element_value_not_found(self):
        self.mock_avis_service.get_current_virtual_ui.return_value = [
            {"element_id": "other_el", "element_type": "text_area", "value": "other"} # type: ignore
        ]
        value = self.agent._get_avis_ui_element_value("non_existent_el")
        self.assertIsNone(value)

    def test_get_avis_ui_element_value_no_value_attr(self):
        self.mock_avis_service.get_current_virtual_ui.return_value = [
             {"element_id": "el_no_value", "element_type": "button"} # type: ignore
        ]
        value = self.agent._get_avis_ui_element_value("el_no_value")
        self.assertIsNone(value) # Or check logs if agent logs this

    def test_type_in_avis(self):
        test_id = "editor1"
        test_text = "print('hello')"
        self.agent._type_in_avis(test_id, test_text)

        expected_command: VirtualKeyboardCommand = { # type: ignore
            "action_type": "type_string",
            "text_to_type": test_text,
            "target_element_id": test_id
        }
        self.mock_avis_service.process_keyboard_command.assert_called_once_with(expected_command)

    def test_click_avis_element(self):
        test_id = "button_run"
        self.agent._click_avis_element(test_id)

        expected_command: VirtualMouseCommand = { # type: ignore
            "action_type": "click",
            "target_element_id": test_id,
            "click_type": "left"
        }
        self.mock_avis_service.process_mouse_command.assert_called_once_with(expected_command)

    def test_perform_calculation_step(self):
        # Setup mock UI for output reading
        self._setup_mock_ui_for_element_value(self.output_display_id, "Calculation Result: 16")

        self.agent._perform_calculation_step()

        # Check typing command
        type_call_args = self.mock_avis_service.process_keyboard_command.call_args
        self.assertIsNotNone(type_call_args)
        typed_command = type_call_args[0][0]
        self.assertEqual(typed_command["target_element_id"], self.code_editor_id)
        self.assertEqual(typed_command["text_to_type"], self.agent.calculation_code)

        # Check click command
        click_call_args = self.mock_avis_service.process_mouse_command.call_args
        self.assertIsNotNone(click_call_args)
        clicked_command = click_call_args[0][0]
        self.assertEqual(clicked_command["target_element_id"], self.run_button_id)

        # Check that output was read (get_current_virtual_ui called by _get_avis_ui_element_value)
        # It's called once by _get_avis_ui_element_value within _perform_calculation_step
        self.mock_avis_service.get_current_virtual_ui.assert_called()


    def test_perform_status_reporting_step(self):
        perm_text = "Permissions: CodeExec=True"
        hw_text = "HW Status: CPU=Mock"

        # Setup mock UI for reading perm and hw displays, and then for output
        def get_ui_side_effect(*args, **kwargs):
            # First two calls are for reading perm_display and hw_display
            # Third call is for reading output_display_id
            if self.mock_avis_service.get_current_virtual_ui.call_count <= 1:
                 return [{"element_id": self.perm_display_id, "element_type": "text_area", "value": perm_text}] # type: ignore
            elif self.mock_avis_service.get_current_virtual_ui.call_count <= 2:
                 return [{"element_id": self.hw_display_id, "element_type": "text_area", "value": hw_text}] # type: ignore
            else: # For reading the output_display_id
                 return [{"element_id": self.output_display_id, "element_type": "text_area", "value": "Status Reported"}] # type: ignore

        self.mock_avis_service.get_current_virtual_ui.side_effect = get_ui_side_effect

        self.agent._perform_status_reporting_step()

        # Check typing command for reporting code
        # The last call to process_keyboard_command should be the reporting code
        type_call_args_list = self.mock_avis_service.process_keyboard_command.call_args_list
        self.assertTrue(len(type_call_args_list) > 0) # Ensure it was called
        last_type_call_args = type_call_args_list[-1]
        typed_command = last_type_call_args[0][0]

        self.assertEqual(typed_command["target_element_id"], self.code_editor_id)
        self.assertIn(perm_text.replace("'", "\\'"), typed_command["text_to_type"])
        self.assertIn(hw_text.replace("'", "\\'"), typed_command["text_to_type"])

        # Check click command for run button
        # The last call to process_mouse_command
        click_call_args_list = self.mock_avis_service.process_mouse_command.call_args_list
        self.assertTrue(len(click_call_args_list) > 0)
        last_click_call_args = click_call_args_list[-1]
        clicked_command = last_click_call_args[0][0]
        self.assertEqual(clicked_command["target_element_id"], self.run_button_id)

        # Verify get_current_virtual_ui was called multiple times
        # (once for perm, once for hw, once for output)
        self.assertEqual(self.mock_avis_service.get_current_virtual_ui.call_count, 3)


    def test_run_task_full_sequence(self):
        # More complex side effect for get_current_virtual_ui
        # 1. Calc output
        # 2. Perm display read
        # 3. HW display read
        # 4. Status report output
        calc_output_val = "Calculation Result: 16"
        perm_text_val = "Perms: OK"
        hw_text_val = "HW: OK"
        report_output_val = "Status Reported!"

        ui_states = [
            [{"element_id": self.output_display_id, "element_type": "text_area", "value": calc_output_val}], # After calc
            [{"element_id": self.perm_display_id, "element_type": "text_area", "value": perm_text_val}],   # For perm read
            [{"element_id": self.hw_display_id, "element_type": "text_area", "value": hw_text_val}],     # For hw read
            [{"element_id": self.output_display_id, "element_type": "text_area", "value": report_output_val}] # After report
        ]
        self.mock_avis_service.get_current_virtual_ui.side_effect = ui_states

        self.agent.run_task()

        self.assertEqual(self.agent.task_step, 2) # Should complete both steps

        # Check calls to AVIS keyboard
        expected_type_calls = [
            call(unittest.mock.ANY), # Calculation code
            call(unittest.mock.ANY)  # Reporting code
        ]
        self.mock_avis_service.process_keyboard_command.assert_has_calls(expected_type_calls, any_order=False)
        typed_calc_cmd = self.mock_avis_service.process_keyboard_command.call_args_list[0][0][0]
        self.assertEqual(typed_calc_cmd["text_to_type"], self.agent.calculation_code)

        typed_report_cmd = self.mock_avis_service.process_keyboard_command.call_args_list[1][0][0]
        self.assertIn(perm_text_val.replace("'", "\\'"), typed_report_cmd["text_to_type"])
        self.assertIn(hw_text_val.replace("'", "\\'"), typed_report_cmd["text_to_type"])


        # Check calls to AVIS mouse (run button clicks)
        expected_mouse_calls = [
            call(unittest.mock.ANY), # Click for calculation
            call(unittest.mock.ANY)  # Click for reporting
        ]
        self.mock_avis_service.process_mouse_command.assert_has_calls(expected_mouse_calls, any_order=False)
        clicked_cmd1 = self.mock_avis_service.process_mouse_command.call_args_list[0][0][0]
        self.assertEqual(clicked_cmd1["target_element_id"], self.run_button_id)
        clicked_cmd2 = self.mock_avis_service.process_mouse_command.call_args_list[1][0][0]
        self.assertEqual(clicked_cmd2["target_element_id"], self.run_button_id)

        # Check get_current_virtual_ui calls
        self.assertEqual(self.mock_avis_service.get_current_virtual_ui.call_count, 4)


if __name__ == "__main__":
    unittest.main()
