# src/services/ai_virtual_input_service.py
"""
AI Virtual Input Service (AVIS)

This service provides a simulated environment for the AI to interact with
graphical user interfaces (GUIs) by sending virtual mouse and keyboard commands.
It logs these actions and maintains a simplified virtual state.

Future extensions may allow this service (under strict permissions) to
control actual system input devices.
"""

from typing import List, Optional, Dict, Any, Tuple

from src.shared.types.common_types import (
    VirtualInputPermissionLevel,
    VirtualMouseCommand,
    VirtualKeyboardCommand,
    VirtualMouseEventType,
    VirtualKeyboardActionType,
    VirtualInputElementDescription, # Added this import
    AIPermissionSet, # New type for AI permissions
    ExecutionResult # For process_code_execution_command
)

# Import ResourceAwarenessService for type hinting, will be optional
from src.services.resource_awareness_service import ResourceAwarenessService
# Import AISimulationControlService for instantiation
from src.services.ai_simulation_control_service import AISimulationControlService


# Further imports will be added as the class is implemented.
# For example, datetime for logging timestamps.
from datetime import datetime, timezone
import copy # For deepcopy

class AIVirtualInputService:
    """
    Manages virtual mouse and keyboard interactions for the AI.
    Operates primarily in a simulation mode, with future potential for actual control
    under strict permissions.
    """
    def __init__(self,
                 initial_mode: VirtualInputPermissionLevel = "simulation_only",
                 resource_awareness_service: Optional[ResourceAwarenessService] = None,
                 bash_runner: Optional[Any] = None): # For AISimulationControlService
        """
        Initializes the AI Virtual Input Service.

        Args:
            initial_mode (VirtualInputPermissionLevel): The starting operational mode.
            resource_awareness_service (Optional[ResourceAwarenessService]):
                An instance of ResourceAwarenessService.
            bash_runner (Optional[Any]): A callable (like Jules's run_in_bash_session)
                for executing shell commands, passed to AISimulationControlService.
        """
        self.mode: VirtualInputPermissionLevel = initial_mode

        # Initialize AISimulationControlService first, as it provides permissions and hw status
        self.ai_simulation_control_service = AISimulationControlService(
            resource_awareness_service=resource_awareness_service,
            bash_runner=bash_runner
        )

        # Virtual cursor position
        self.virtual_cursor_position: Tuple[float, float] = (0.5, 0.5)
        self.virtual_focused_element_id: Optional[str] = None
        self.action_log: List[Dict[str, Any]] = []
        self.virtual_ui_elements: List[VirtualInputElementDescription] = []

        # Populate AVIS state from AISimulationControlService
        self.current_ai_permissions: AIPermissionSet = self.ai_simulation_control_service.get_current_ai_permissions()
        self.current_sim_hardware_status: Dict[str, Any] = self.ai_simulation_control_service.get_sim_hardware_status()

        # Keep a reference if needed, though AISimulationControlService holds its own
        self.resource_awareness_service: Optional[ResourceAwarenessService] = resource_awareness_service


        print(f"AIVirtualInputService initialized in '{self.mode}' mode.")
        print(f"  AISimulationControlService integration active.")
        print(f"  Initial virtual cursor: {self.virtual_cursor_position}")
        print(f"  Current AI Permissions: {self.current_ai_permissions}")
        print(f"  Current Sim Hardware Status: {self.current_sim_hardware_status}")

    def refresh_simulation_status(self) -> None:
        """
        Refreshes AI permissions and simulated hardware status from AISimulationControlService.
        Also updates the relevant display elements in the virtual UI if they exist.
        """
        if not self.ai_simulation_control_service:
            print("AVIS: AISimulationControlService not available to refresh status.")
            return

        self.current_ai_permissions = self.ai_simulation_control_service.get_current_ai_permissions()
        self.current_sim_hardware_status = self.ai_simulation_control_service.get_sim_hardware_status()

        print(f"AVIS: Simulation status refreshed.")
        print(f"  Updated AI Permissions: {self.current_ai_permissions}")
        print(f"  Updated Sim Hardware Status: {self.current_sim_hardware_status}")

        # Update UI elements (implementation in a later step)
        self._update_info_display_elements()


    def _update_info_display_elements(self) -> None:
        """
        Updates the 'value' of predefined virtual UI elements that display
        AI permissions and simulated hardware status.
        (Element IDs: 'ai_permissions_display', 'sim_hw_status_display')
        """
        perm_display_el = self._find_element_by_id("ai_permissions_display")
        if perm_display_el:
            # Simple string representation for now
            perm_display_el["value"] = f"Permissions: CodeExec={self.current_ai_permissions.get('can_execute_code')}, ReadHW={self.current_ai_permissions.get('can_read_sim_hw_status')}"
            print(f"AVIS: Updated 'ai_permissions_display' element.")

        hw_display_el = self._find_element_by_id("sim_hw_status_display")
        if hw_display_el:
            # Simple string representation
            hw_display_el["value"] = f"HW Status: Profile={self.current_sim_hardware_status.get('profile_name', 'N/A')}, CPU={self.current_sim_hardware_status.get('cpu_cores')} cores"
            print(f"AVIS: Updated 'sim_hw_status_display' element.")


    def load_virtual_ui(self, elements: List[VirtualInputElementDescription]) -> None:
        """
        Loads or replaces the current virtual UI with a new set of elements.
        Args:
            elements: A list of VirtualInputElementDescription representing the new UI state.
        """
        self.virtual_ui_elements = copy.deepcopy(elements) # Store a copy
        print(f"AVIS: Virtual UI loaded with {len(self.virtual_ui_elements)} top-level elements.")

    def get_current_virtual_ui(self) -> List[VirtualInputElementDescription]:
        """
        Returns a deep copy of the current virtual UI element structure.
        This serves as the AI's way to "see" the simulated screen/window.
        """
        return copy.deepcopy(self.virtual_ui_elements)

    def _find_element_by_id(self, element_id: str, search_list: Optional[List[VirtualInputElementDescription]] = None) -> Optional[VirtualInputElementDescription]:
        """
        Recursively searches for an element by its ID within a list of elements
        (and their children).

        Args:
            element_id (str): The ID of the element to find.
            search_list (Optional[List[VirtualInputElementDescription]]): The list of elements
                to search within. If None, searches self.virtual_ui_elements.

        Returns:
            Optional[VirtualInputElementDescription]: The found element, or None.
        """
        if search_list is None:
            search_list = self.virtual_ui_elements

        for element in search_list:
            if element.get("element_id") == element_id:
                return element
            children = element.get("children")
            if children: # If it's a list and not None
                found_in_children = self._find_element_by_id(element_id, children)
                if found_in_children:
                    return found_in_children
        return None

    def _log_action(self, command_type: str, command_details: Dict[str, Any], outcome: Dict[str, Any]) -> None:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "command_type": command_type,
            "command_details": command_details,
            "outcome": outcome,
            "mode": self.mode
        }
        self.action_log.append(log_entry)

    def process_mouse_command(self, command: VirtualMouseCommand) -> Dict[str, Any]:
        """Processes a virtual mouse command in simulation mode."""
        action_type = command.get("action_type")
        # Make a copy of the command to log, as it might be modified or sensitive
        loggable_command_details = dict(command)
        outcome: Dict[str, Any] = {"status": "simulated_not_implemented", "action": action_type}

        if self.mode != "simulation_only":
            # In the future, actual control logic would be gated here by permissions.
            # For now, all non-simulation modes are treated as "not implemented for real action".
            outcome = {"status": "error", "message": f"Mode '{self.mode}' not fully supported for actual mouse actions yet. Simulating."}
            # Fall through to simulation for now.

        print(f"AVIS: Processing mouse command: {action_type}")

        if action_type == "move_relative_to_window":
            # For 'move_relative_to_window', relative_x and relative_y are new absolute ratios.
            new_x = command.get("relative_x", self.virtual_cursor_position[0])
            new_y = command.get("relative_y", self.virtual_cursor_position[1])

            # Clamp values to be within [0.0, 1.0]
            self.virtual_cursor_position = (
                max(0.0, min(1.0, new_x if isinstance(new_x, (int, float)) else self.virtual_cursor_position[0])),
                max(0.0, min(1.0, new_y if isinstance(new_y, (int, float)) else self.virtual_cursor_position[1]))
            )
            outcome = {
                "status": "simulated",
                "action": "move_relative_to_window",
                "new_cursor_position": self.virtual_cursor_position
            }
            print(f"  AVIS Sim: Cursor moved to {self.virtual_cursor_position}")

        elif action_type == "click":
            target_element = command.get("target_element_id")
            click_type = command.get("click_type", "left")
            pos_x = command.get("relative_x", self.virtual_cursor_position[0]) # Click at current virtual cursor if not specified
            pos_y = command.get("relative_y", self.virtual_cursor_position[1])

            # If target_element_id is provided, ideally we'd use its center or the relative_x/y within it.
            # For now, simulation just logs.
            click_details = {
                "click_type": click_type,
                "target_element_id": target_element,
                "position": (pos_x, pos_y)
            }
            outcome = {"status": "simulated", "action": "click", "details": click_details}
            print(f"  AVIS Sim: Click logged: {click_details}")

            if target_element == "run_code_button":
                print(f"  AVIS Sim: 'run_code_button' clicked. Attempting to execute code.")
                code_editor_element = self._find_element_by_id("code_editor")
                if code_editor_element and "value" in code_editor_element:
                    code_to_execute = str(code_editor_element.get("value", "")) # Ensure it's a string
                    self.process_code_execution_command(code_to_execute)
                    outcome["details"]["triggered_action"] = "code_execution" # type: ignore
                    outcome["details"]["code_editor_found"] = True # type: ignore
                    outcome["details"]["code_length"] = len(code_to_execute) # type: ignore
                else:
                    print("  AVIS Sim: 'code_editor' element not found or has no value. Cannot execute code.")
                    outcome["details"]["triggered_action"] = "code_execution_failed_no_editor" # type: ignore
                    outcome["details"]["code_editor_found"] = False # type: ignore
                # Focus does not change just by clicking the run button usually

            elif target_element: # Handle focus for other clickable elements
                self.virtual_focused_element_id = target_element
                print(f"  AVIS Sim: Focused element set to '{target_element}' due to click.")
            # If no target_element, focus remains unchanged.


        elif action_type == "hover":
            target_element = command.get("target_element_id")
            pos_x = command.get("relative_x")
            pos_y = command.get("relative_y")
            # In a real simulation with element bounds, virtual_cursor_position might update
            # to the element's center or the relative x/y within it.
            # For now, just log the intent.
            hover_details = {
                "target_element_id": target_element,
                "position": (pos_x, pos_y) if pos_x is not None and pos_y is not None else self.virtual_cursor_position
            }
            outcome = {"status": "simulated", "action": "hover", "details": hover_details}
            print(f"  AVIS Sim: Hover logged: {hover_details}")

        elif action_type == "scroll":
            target_element = command.get("target_element_id") # Optional, could be window scroll
            direction = command.get("scroll_direction")
            amount_ratio = command.get("scroll_amount_ratio")
            pages = command.get("scroll_pages")

            scroll_details = {
                "target_element_id": target_element,
                "direction": direction,
                "amount_ratio": amount_ratio,
                "pages": pages
            }
            outcome = {"status": "simulated", "action": "scroll", "details": scroll_details}
            print(f"  AVIS Sim: Scroll logged: {scroll_details}")

        # For other mouse actions, just log as simulated_not_implemented for now
        else:
            print(f"  AVIS Sim: Action '{action_type}' logged as simulated_not_implemented.")
            # Outcome already defaults to this

        self._log_action("mouse", loggable_command_details, outcome)
        return outcome

    def process_keyboard_command(self, command: VirtualKeyboardCommand) -> Dict[str, Any]:
        """Processes a virtual keyboard command in simulation mode."""
        action_type = command.get("action_type")
        loggable_command_details = dict(command)
        outcome: Dict[str, Any] = {"status": "simulated_not_implemented", "action": action_type}

        if self.mode != "simulation_only":
            outcome = {"status": "error", "message": f"Mode '{self.mode}' not fully supported for actual keyboard actions yet. Simulating."}
            # Fall through to simulation

        print(f"AVIS: Processing keyboard command: {action_type}")

        if action_type == "type_string":
            text_to_type = command.get("text_to_type", "")
            target_element = command.get("target_element_id")

            if target_element:
                self.virtual_focused_element_id = target_element
                print(f"  AVIS Sim: Focused element set to '{target_element}' for typing.")

            # In simulation, we just log that text would be typed, presumably into focused element.
            type_details = {
                "text_typed": text_to_type,
                "target_element_id": self.virtual_focused_element_id,
                "value_updated": False
            }

            element_to_type_in = None
            if self.virtual_focused_element_id: # Prefer typing into already focused element if no new target
                element_to_type_in = self._find_element_by_id(self.virtual_focused_element_id)

            if target_element: # If a specific target is given, override focus for this action
                self.virtual_focused_element_id = target_element
                element_to_type_in = self._find_element_by_id(target_element)
                print(f"  AVIS Sim: Focused element set to '{target_element}' for typing.")

            if element_to_type_in:
                # Check if element can receive text, e.g. "text_field", "textarea"
                # For now, we'll assume if it has a 'value' attribute, it can be typed into.
                if "value" in element_to_type_in: # Check if element has 'value' attribute
                    # Decide on append vs overwrite logic if needed in future. For now, overwrite.
                    element_to_type_in["value"] = text_to_type
                    type_details["value_updated"] = True
                    type_details["updated_element_id"] = element_to_type_in.get("element_id")
                    print(f"  AVIS Sim: Element '{element_to_type_in.get('element_id')}' value updated to '{text_to_type}'.")
                else:
                    print(f"  AVIS Sim: Element '{element_to_type_in.get('element_id')}' not a text input type (no 'value' attribute). Typing simulated by log only.")
            else:
                print(f"  AVIS Sim: No target element found or focused for typing. Typing simulated by log only.")

            outcome = {"status": "simulated", "action": "type_string", "details": type_details}
            print(f"  AVIS Sim: Typing action processed. Text: '{text_to_type}', Target: '{self.virtual_focused_element_id or 'none'}', Value Updated: {type_details['value_updated']}.")

        elif action_type == "press_keys":
            keys_pressed = command.get("keys", [])
            target_element = command.get("target_element_id")

            if target_element:
                self.virtual_focused_element_id = target_element
                print(f"  AVIS Sim: Focused element set to '{target_element}' for key press.")

            press_details = {
                "keys_pressed": keys_pressed,
                "target_element_id": self.virtual_focused_element_id
            }
            outcome = {"status": "simulated", "action": "press_keys", "details": press_details}
            print(f"  AVIS Sim: Key press logged: {keys_pressed} on focused '{self.virtual_focused_element_id or 'unknown'}'.")

        elif action_type == "special_key":
            special_keys = command.get("keys", []) # Expecting a list, e.g., ["enter"]
            key_name = special_keys[0] if special_keys else "unknown_special_key"
            target_element = command.get("target_element_id")

            if target_element:
                self.virtual_focused_element_id = target_element
                print(f"  AVIS Sim: Focused element set to '{target_element}' for special key press.")

            special_key_details = {
                "key_name": key_name,
                "target_element_id": self.virtual_focused_element_id
            }
            outcome = {"status": "simulated", "action": "special_key", "details": special_key_details}
            print(f"  AVIS Sim: Special key '{key_name}' press logged on focused '{self.virtual_focused_element_id or 'unknown'}'.")

        # For other keyboard actions, just log as simulated_not_implemented for now
        else:
            print(f"  AVIS Sim: Action '{action_type}' logged as simulated_not_implemented.")

        self._log_action("keyboard", loggable_command_details, outcome)
        return outcome

    def get_action_log(self) -> List[Dict[str, Any]]:
        """Returns the log of all actions processed by the service."""
        return list(self.action_log) # Return a copy

    def clear_action_log(self) -> None:
        """Clears the action log."""
        self.action_log = []
        print("AVIS: Action log cleared.")

    def get_virtual_state(self) -> Dict[str, Any]:
        """Returns the current simulated virtual state."""
        return {
            "mode": self.mode,
            "virtual_cursor_position": self.virtual_cursor_position,
            "virtual_focused_element_id": self.virtual_focused_element_id,
            "action_log_count": len(self.action_log),
            "current_ai_permissions": self.current_ai_permissions,
            "current_sim_hardware_status": self.current_sim_hardware_status
        }

    def process_code_execution_command(self, code_string: str, output_element_id: str = "code_output_display") -> None:
        """
        Processes a command to execute AI-provided code.
        Uses AISimulationControlService to perform the execution and updates a
        designated virtual UI element with the result.

        Args:
            code_string (str): The Python code string to execute.
            output_element_id (str): The element_id of the virtual UI text_area
                                     where execution results should be displayed.
                                     Defaults to "code_output_display".
        """
        if not self.ai_simulation_control_service:
            print("AVIS: Cannot process code execution. AISimulationControlService is not available.")
            # Optionally update output element with this error
            output_el = self._find_element_by_id(output_element_id)
            if output_el:
                output_el["value"] = "Error: AISimulationControlService not available."
            return

        print(f"AVIS: Received code execution command for {len(code_string)} chars of code.")

        # Execute the code via the control service
        # Permissions are checked by the AISimulationControlService using its current set.
        execution_result: ExecutionResult = self.ai_simulation_control_service.execute_ai_code(
            code_string,
            self.current_ai_permissions # Pass the current permissions from AVIS state
        )

        result_str = (
            f"--- Execution Result (Request ID: {execution_result['request_id']}) ---\n"
            f"Status: {execution_result['status_message']}\n"
            f"Success: {execution_result['execution_success']}\n"
            f"Exit Code: {execution_result['script_exit_code'] if execution_result['script_exit_code'] is not None else 'N/A'}\n"
            f"STDOUT:\n{execution_result['stdout']}\n"
            f"STDERR:\n{execution_result['stderr']}\n"
            f"-------------------------------------------------"
        )

        # Update the designated output element in the virtual UI
        output_element = self._find_element_by_id(output_element_id)
        if output_element:
            if "value" in output_element:
                output_element["value"] = result_str
                print(f"AVIS: Updated element '{output_element_id}' with execution result.")
            else:
                print(f"AVIS: Warning - Output element '{output_element_id}' has no 'value' attribute to update.")
        else:
            print(f"AVIS: Warning - Output element '{output_element_id}' not found in virtual UI.")

        # Log this action
        self._log_action(
            command_type="code_execution",
            command_details={"code_length": len(code_string), "output_element_id": output_element_id},
            outcome={
                "request_id": execution_result["request_id"],
                "execution_success": execution_result["execution_success"],
                "status_message": execution_result["status_message"]
            }
        )

        # Potentially refresh hardware status if code execution might affect it
        # For now, this is manual or tied to a general refresh.
        # self.refresh_simulation_status() # Consider if this should be automatic.

print("AIVirtualInputService module loaded.")
