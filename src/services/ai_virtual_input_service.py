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
    VirtualKeyboardActionType
    # VirtualInputElementDescription will be used by the AI agent, not directly by service input for now
)

# Further imports will be added as the class is implemented.
# For example, datetime for logging timestamps.
from datetime import datetime, timezone

class AIVirtualInputService:
    """
    Manages virtual mouse and keyboard interactions for the AI.
    Operates primarily in a simulation mode, with future potential for actual control
    under strict permissions.
    """
    def __init__(self, initial_mode: VirtualInputPermissionLevel = "simulation_only"):
        """
        Initializes the AI Virtual Input Service.

        Args:
            initial_mode (VirtualInputPermissionLevel): The starting operational mode.
                Defaults to "simulation_only".
        """
        self.mode: VirtualInputPermissionLevel = initial_mode

        # Virtual cursor position (x_ratio, y_ratio) relative to a 1.0x1.0 abstract window/screen.
        # (0.0, 0.0) is top-left, (1.0, 1.0) is bottom-right.
        self.virtual_cursor_position: Tuple[float, float] = (0.5, 0.5) # Start at center

        self.virtual_focused_element_id: Optional[str] = None
        self.action_log: List[Dict[str, Any]] = [] # Stores a log of commands processed

        print(f"AIVirtualInputService initialized in '{self.mode}' mode.")
        print(f"  Initial virtual cursor: {self.virtual_cursor_position}")

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
                "position": (pos_x, pos_y) # This might be element-relative or window-relative based on command version
            }
            outcome = {"status": "simulated", "action": "click", "details": click_details}
            print(f"  AVIS Sim: Click logged: {click_details}")
            if target_element: # Assume click might change focus
                self.virtual_focused_element_id = target_element
                print(f"  AVIS Sim: Focused element set to '{target_element}' due to click.")


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
                "target_element_id": self.virtual_focused_element_id
            }
            outcome = {"status": "simulated", "action": "type_string", "details": type_details}
            print(f"  AVIS Sim: Typing logged: '{text_to_type}' into focused '{self.virtual_focused_element_id or 'unknown'}'.")

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
            "action_log_count": len(self.action_log)
        }

print("AIVirtualInputService module loaded.")
