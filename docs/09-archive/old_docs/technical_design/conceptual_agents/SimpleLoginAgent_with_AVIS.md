# Conceptual Agent: SimpleLoginAgent using AVIS

## 1. Introduction

This document outlines the design and logic for a conceptual AI agent,
`SimpleLoginAgent`, whose task is to simulate logging into a website using the
AI Virtual Input System (AVIS). This exercise helps illustrate how an AI might
use the AVIS to perform GUI-based tasks and highlights the types of interactions
and information flow involved.

This agent operates purely in a simulated environment, interacting with a mocked
GUI state.

## 2. Task Definition: Log into a Conceptual Website

The `SimpleLoginAgent` is tasked with the following:

- **Goal:** Successfully simulate typing a username and password into respective
  fields on a conceptual login page and then clicking a login button.
- **Inputs to the Agent:**
  - `username_to_enter: str` (e.g., "test_user")
  - `password_to_enter: str` (e.g., "password123")
  - An instance of the `AIVirtualInputService`.
  - A description of the current (mocked) UI elements.
- **Key Steps for the Agent:**
  1.  Perceive/Identify the username input field, password input field, and the
      login button from the UI description.
  2.  Simulate typing the username into the username field.
  3.  Simulate typing the password into the password field.
  4.  Simulate clicking the login button.
  5.  (Optional/Conceptual) Perceive a status message to verify login success or
      failure.
- **Success Criteria (Simulation):**
  - The agent generates the correct sequence of AVIS commands.
  - AVIS logs these commands as successfully simulated.

## 3. Mocked GUI State Representation

The agent will receive a description of the UI elements on the conceptual login
page. This structure is based on the `VirtualInputElementDescription` TypedDict.

```json
[
  {
    "element_id": "window_login_page",
    "element_type": "window",
    "label_text": "Login Page - MyWebApp",
    "is_visible": true,
    "is_enabled": true,
    "bounds_relative": [0.0, 0.0, 1.0, 1.0],
    "children": [
      {
        "element_id": "label_username",
        "element_type": "label",
        "label_text": "Username:",
        "is_visible": true,
        "is_enabled": true,
        "bounds_relative": [0.1, 0.2, 0.2, 0.05],
        "attributes": {}
      },
      {
        "element_id": "field_username",
        "element_type": "text_field",
        "label_text": null,
        "value": "",
        "is_visible": true,
        "is_enabled": true,
        "is_focused": false,
        "bounds_relative": [0.35, 0.2, 0.5, 0.05],
        "attributes": { "placeholder": "Enter your username" }
      },
      {
        "element_id": "label_password",
        "element_type": "label",
        "label_text": "Password:",
        "is_visible": true,
        "is_enabled": true,
        "bounds_relative": [0.1, 0.3, 0.2, 0.05],
        "attributes": {}
      },
      {
        "element_id": "field_password",
        "element_type": "text_field",
        "label_text": null,
        "value": "",
        "is_visible": true,
        "is_enabled": true,
        "is_focused": false,
        "bounds_relative": [0.35, 0.3, 0.5, 0.05],
        "attributes": {
          "is_password": true,
          "placeholder": "Enter your password"
        }
      },
      {
        "element_id": "button_login",
        "element_type": "button",
        "label_text": "Login",
        "is_visible": true,
        "is_enabled": true,
        "is_focused": false,
        "bounds_relative": [0.4, 0.45, 0.2, 0.07],
        "attributes": {}
      },
      {
        "element_id": "area_status_message",
        "element_type": "label",
        "label_text": "",
        "is_visible": true,
        "is_enabled": true,
        "bounds_relative": [0.1, 0.55, 0.8, 0.05],
        "attributes": { "role": "status" }
      }
    ]
  }
]
```

## 4. Agent Logic Flow and AVIS Interaction

The `ConceptualLoginAgent` would execute the following logic:

**Agent State Variables (Conceptual):**

- `task_status: str` (e.g., "locating_elements", "typing_username", etc.)
- `target_element_ids: Dict[str, Optional[str]]` (to store found element IDs)

**Method: `agent_perform_login(username, password, avis, current_ui_elements)`**

1.  **Initialization:**
    - Set `task_status` to `"locating_elements"`.
    - Log: "Agent: Starting login task."

2.  **Locate UI Elements:**
    - The agent parses `current_ui_elements` (the mocked GUI state) to find the
      IDs of essential elements. This uses a conceptual `find_element_id` helper
      function.
      - `username_field_id = find_element_id(current_ui_elements, type="text_field", purpose="username")`
        (Expected: "field_username")
      - `password_field_id = find_element_id(current_ui_elements, type="text_field", purpose="password")`
        (Expected: "field_password")
      - `login_button_id = find_element_id(current_ui_elements, type="button", label="Login")`
        (Expected: "button_login")
      - `status_message_id = find_element_id(current_ui_elements, type="label", purpose="status_message")`
        (Expected: "area_status_message")
    - If any critical element (username field, password field, login button) is
      not found, log an error, set `task_status` to `"completed_failure"`, and
      return a failure status.
    - Store found IDs in `self.target_element_ids`.
    - Log: "Agent: Elements identified: User='...', Pass='...', LoginBtn='...'"

3.  **Type Username:**
    - Set `task_status` to `"typing_username"`.
    - Log: "Agent: Typing username into '{username_field_id}'."
    - Create `VirtualKeyboardCommand`:
      ```json
      {
        "action_type": "type_string",
        "text_to_type": "test_user", // from input username
        "target_element_id": "field_username" // from located ID
      }
      ```
    - Send to AVIS:
      `avis_response = avis.process_keyboard_command(username_command)`
    - Log AVIS response. If `avis_response["status"]` is not "simulated", handle
      error and abort.

4.  **Type Password:**
    - Set `task_status` to `"typing_password"`.
    - Log: "Agent: Typing password into '{password_field_id}'."
    - Create `VirtualKeyboardCommand`:
      ```json
      {
        "action_type": "type_string",
        "text_to_type": "password123", // from input password
        "target_element_id": "field_password" // from located ID
      }
      ```
    - Send to AVIS:
      `avis_response = avis.process_keyboard_command(password_command)`
    - Log AVIS response. If `avis_response["status"]` is not "simulated", handle
      error and abort.

5.  **Click Login Button:**
    - Set `task_status` to `"clicking_login"`.
    - Log: "Agent: Clicking login button '{login_button_id}'."
    - Create `VirtualMouseCommand`:
      ```json
      {
        "action_type": "click",
        "target_element_id": "button_login", // from located ID
        "click_type": "left"
      }
      ```
    - Send to AVIS:
      `avis_response = avis.process_mouse_command(login_click_command)`
    - Log AVIS response. If `avis_response["status"]` is not "simulated", handle
      error and abort.

6.  **Verify Outcome (Conceptual):**
    - Set `task_status` to `"verifying"`.
    - Log: "Agent: Login submitted. Conceptually verifying outcome..."
    - **Note:** This step is highly dependent on AVIS's simulation capabilities.
      For v0.1 of AVIS, the service doesn't maintain a full dynamic virtual UI
      model that changes based on actions.
    - A more advanced AVIS simulation might:
      - Receive the click on "button_login".
      - Internally update its mocked UI state, e.g., changing the `label_text`
        of the "area_status_message" element to "Login successful!" or "Invalid
        credentials."
    - The agent would then conceptually call a method like
      `updated_ui_elements = avis.get_current_virtual_ui_state_elements()` (a
      new method for AVIS).
    - The agent would parse `updated_ui_elements` to find the
      "area_status_message" and check its text.
    - For this initial conceptual agent, we assume this verification step is
      simplified or results in an assumed success if all prior simulated actions
      were accepted by AVIS.

7.  **Completion:**
    - Log: "Agent: Login task simulation sequence completed."
    - Set `task_status` to `"completed_success"` (assuming simulation success).
    - Return "success_simulation_complete".

**Helper: `find_element_id(ui_elements, type, purpose_or_label)` (Conceptual)**

- This function would recursively search the `ui_elements` list (and their
  `children`).
- It would match elements based on `element_type` and either a known
  `label_text` or a heuristic/custom attribute indicating the element's
  `purpose` (e.g., a `data-testid` or `automation_id` if these were part of
  `VirtualInputElementDescription.attributes`).
- For this conceptual document, we assume it can reliably find the IDs:
  "field_username", "field_password", "button_login", "area_status_message".

## 5. Discussion and Challenges

- **Element Identification:** The reliability of `find_element_id` is paramount.
  In real scenarios, this is very hard. Labels can change, UI structures can be
  dynamic. The mocked UI bypasses this.
- **State Synchronization:** The agent needs to know the current state of the
  UI. The proposed `get_screen_elements()` AVIS action (or a similar state
  query) is essential. How AVIS updates its virtual state after actions is also
  key for multi-step tasks.
- **Error Handling:** The agent needs robust error handling if AVIS reports an
  action couldn't be simulated, or if expected elements are not found.
- **Timing and Waits:** Real UIs have delays, animations, and loading times. A
  more advanced AVIS and agent would need to handle waits or checks for elements
  to become available/interactive. This is out of scope for the initial
  simulation.
- **Complexity of Real UIs:** The mocked UI is very simple. Real applications
  have far more elements, complex nesting, and dynamic content, making
  perception and reliable element identification much harder.

This conceptual agent demonstrates how the AVIS, even in simulation mode with a
mocked UI, can be used to model AI interaction with GUIs. It provides a basis
for designing tools or agent modules that leverage AVIS.
