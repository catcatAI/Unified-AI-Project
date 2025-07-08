# src/agents/simple_coding_agent.py
"""
A simple, scripted agent that uses AIVirtualInputService to perform
a predefined task involving code execution.

Purpose:
- Validate and demonstrate AVIS code execution capabilities.
- Serve as a basic example of an agent interacting with AVIS.
- Help identify potential improvements or gaps in AVIS.
"""

from typing import Optional, List, Dict, Any
import time # For potential delays if needed

# Assuming AIVirtualInputService is correctly pathed for import
# from src.services.ai_virtual_input_service import AIVirtualInputService
# For now, to avoid circular dependencies or complex pathing issues during this step,
# we'll use a forward reference or Any for the type hint of AIVirtualInputService for now.
# Proper import when structure allows:
# from src.services.ai_virtual_input_service import AIVirtualInputService
AIVirtualInputServiceType = Any # Placeholder for AIVirtualInputService type

# Import necessary types for commands and UI elements
from src.shared.types.common_types import (
    VirtualKeyboardCommand,
    VirtualMouseCommand,
    VirtualInputElementDescription
)


class SimpleCodingAgent:
    """
    A simple agent that interacts with AIVirtualInputService to perform a
    hardcoded task:
    1. Write and execute code to perform a calculation.
    2. Read displayed permissions and hardware status.
    3. Write and execute code to report these statuses.
    """

    def __init__(self, avis_service: AIVirtualInputServiceType):
        """
        Initializes the SimpleCodingAgent.

        Args:
            avis_service: An instance of AIVirtualInputService.
        """
        if avis_service is None:
            raise ValueError("AIVirtualInputService instance is required.")
        self.avis: AIVirtualInputServiceType = avis_service

        self.task_step: int = 0 # 0: initial, 1: calc done, 2: status report done

        # Predefined element IDs the agent expects in the AVIS virtual UI
        self.code_editor_id: str = "code_editor"
        self.run_button_id: str = "run_code_button"
        self.output_display_id: str = "code_output_display"
        self.perm_display_id: str = "ai_permissions_display"
        self.hw_display_id: str = "sim_hw_status_display"

        self.calculation_code: str = "result = (5 + 3) * 2\nprint(f'Calculation Result: {result}')"

        print("SimpleCodingAgent initialized.")
        print(f"  AVIS Service Type: {type(self.avis)}")

    def _get_full_avis_ui(self) -> List[VirtualInputElementDescription]:
        """Gets the current virtual UI structure from AVIS."""
        print("Agent: Getting full AVIS UI...")
        return self.avis.get_current_virtual_ui()

    def _find_element_in_ui(self, element_id: str, ui_elements: List[VirtualInputElementDescription]) -> Optional[VirtualInputElementDescription]:
        """
        Finds an element by its ID in a given list of UI elements.
        This is a simplified client-side find; AVIS also has _find_element_by_id.
        """
        for element in ui_elements:
            if element.get("element_id") == element_id:
                return element
            # Basic recursive search if elements can be nested (not deeply handled here)
            if "children" in element and element["children"]:
                found_in_child = self._find_element_in_ui(element_id, element["children"]) # type: ignore
                if found_in_child:
                    return found_in_child
        return None

    def _get_avis_ui_element_value(self, element_id: str) -> Optional[str]:
        """Retrieves the 'value' of a specified UI element from AVIS."""
        print(f"Agent: Getting value of element '{element_id}'...")
        ui_elements = self._get_full_avis_ui()
        element = self._find_element_in_ui(element_id, ui_elements)
        if element and "value" in element:
            return str(element["value"])
        print(f"Agent: Element '{element_id}' not found or has no 'value'.")
        return None

    def _type_in_avis(self, element_id: str, text_to_type: str) -> None:
        """Sends a type_string command to AVIS for the specified element."""
        print(f"Agent: Typing into element '{element_id}': '{text_to_type[:50]}...'")
        command: VirtualKeyboardCommand = { # type: ignore
            "action_type": "type_string",
            "text_to_type": text_to_type,
            "target_element_id": element_id
        }
        response = self.avis.process_keyboard_command(command)
        print(f"Agent: AVIS response to typing: {response.get('status')}, details: {response.get('details')}")

    def _click_avis_element(self, element_id: str) -> None:
        """Sends a click command to AVIS for the specified element."""
        print(f"Agent: Clicking element '{element_id}'...")
        command: VirtualMouseCommand = { # type: ignore
            "action_type": "click",
            "target_element_id": element_id,
            "click_type": "left" # Default to left click
        }
        response = self.avis.process_mouse_command(command)
        print(f"Agent: AVIS response to click: {response.get('status')}, details: {response.get('details')}")

    def _perform_calculation_step(self) -> bool:
        """
        Types the calculation code into the AVIS code editor, clicks run,
        and optionally prints the output.
        Returns True if actions were attempted, False otherwise.
        """
        print("\nAgent: --- Performing Calculation Step ---")
        if not self.avis:
            print("Agent: AVIS service not available. Cannot perform calculation.")
            return False

        # Type the calculation code
        self._type_in_avis(self.code_editor_id, self.calculation_code)

        # Click the run button
        self._click_avis_element(self.run_button_id)

        # Allow some conceptual time for AVIS to process and update UI
        # In a real scenario with async operations, more robust waiting/polling needed.
        # For our synchronous AVIS simulation, this is mostly for logical separation.
        time.sleep(0.1)

        # Get and print the output
        output = self._get_avis_ui_element_value(self.output_display_id)
        if output:
            print(f"Agent: Calculation output from AVIS:\n{output}")
        else:
            print("Agent: Could not retrieve calculation output from AVIS.")

        print("Agent: --- Calculation Step Attempted ---")
        return True

    def _perform_status_reporting_step(self) -> bool:
        """
        Reads permission and hardware status from AVIS displays,
        then types and executes code to print these statuses.
        Returns True if actions were attempted, False otherwise.
        """
        print("\nAgent: --- Performing Status Reporting Step ---")
        if not self.avis:
            print("Agent: AVIS service not available. Cannot perform status reporting.")
            return False

        # Read displayed permissions and hardware status
        # AVIS needs to have updated these displays after initialization or a refresh.
        # The agent assumes these displays contain the information directly as strings.
        perm_text = self._get_avis_ui_element_value(self.perm_display_id) or "Permissions display not found or empty."
        hw_text = self._get_avis_ui_element_value(self.hw_display_id) or "Hardware status display not found or empty."

        print(f"Agent: Read from perm_display_id: '{perm_text}'")
        print(f"Agent: Read from hw_display_id: '{hw_text}'")

        # Escape quotes for embedding in Python string literal
        # A more robust solution would use json.dumps or similar for complex strings.
        escaped_perm_text = perm_text.replace("'", "\\'").replace("\n", "\\n")
        escaped_hw_text = hw_text.replace("'", "\\'").replace("\n", "\\n")

        reporting_code = (
            f"print('--- AI Status Report ---')\n"
            f"observed_permissions = '{escaped_perm_text}'\n"
            f"observed_hw_status = '{escaped_hw_text}'\n"
            f"print(f'Observed Permissions: {{observed_permissions}}')\n"
            f"print(f'Observed Hardware Status: {{observed_hw_status}}')"
        )

        # Type the reporting code
        self._type_in_avis(self.code_editor_id, reporting_code)

        # Click the run button
        self._click_avis_element(self.run_button_id)

        time.sleep(0.1) # Conceptual delay

        # Get and print the output
        output = self._get_avis_ui_element_value(self.output_display_id)
        if output:
            print(f"Agent: Status reporting output from AVIS:\n{output}")
        else:
            print("Agent: Could not retrieve status reporting output from AVIS.")

        print("Agent: --- Status Reporting Step Attempted ---")
        return True

    def run_task(self) -> None:
        """
        Runs the predefined task sequence:
        1. Perform calculation.
        2. Perform status reporting.
        """
        print("\nAgent: === Starting Task: Simple Calculator & Status Reporter ===")
        self.task_step = 0

        # Step 1: Perform Calculation
        print("\nAgent: Moving to Step 1: Calculation")
        if self._perform_calculation_step():
            self.task_step = 1
            print("Agent: Calculation step processing complete.")
        else:
            print("Agent: Calculation step failed to execute.")
            print("Agent: === Task Aborted ===")
            return

        # Brief pause for clarity in logs / conceptual separation
        time.sleep(0.2)

        # Step 2: Perform Status Reporting
        print("\nAgent: Moving to Step 2: Status Reporting")
        if self._perform_status_reporting_step():
            self.task_step = 2
            print("Agent: Status reporting step processing complete.")
        else:
            print("Agent: Status reporting step failed to execute.")

        print("\nAgent: === Task Finished ===")


if __name__ == '__main__':
    # This section is for basic testing or direct execution of the agent
    # and will be more fully developed in the "Create Basic Test/Driver Script" step.
    print("SimpleCodingAgent script executed directly (for testing).")

    # Example of how it might be set up (actual setup will be in the driver script)
    class MockAIVIS:
        def get_current_virtual_ui(self):
            print("MockAIVIS: get_current_virtual_ui called")
            return []
        def process_keyboard_command(self, cmd):
            print(f"MockAIVIS: process_keyboard_command called with: {cmd}")
            return {"status": "simulated", "details": {}}
        def process_mouse_command(self, cmd):
            print(f"MockAIVIS: process_mouse_command called with: {cmd}")
            return {"status": "simulated", "details": {}}
        # Add other methods that SimpleCodingAgent might call on AVIS

    mock_avis_instance = MockAIVIS()
    try:
        agent = SimpleCodingAgent(avis_service=mock_avis_instance) # type: ignore
        print("SimpleCodingAgent instance created with MockAIVIS.")
        # agent.run_task() # This will be implemented later
    except ValueError as e:
        print(f"Error creating agent: {e}")
