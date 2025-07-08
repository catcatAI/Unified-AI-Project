# SimpleCodingAgent

## Overview

The `SimpleCodingAgent` is a basic, scripted agent designed to interact with the `AIVirtualInputService` (AVIS). Its primary purpose is to serve as a test harness and a clear example for demonstrating and validating the AI code execution capabilities integrated into AVIS (via the `AISimulationControlService`).

It does **not** contain any advanced AI, planning, or learning capabilities. Instead, it follows a predefined sequence of actions to:
1.  Write a simple Python script for a calculation into a virtual code editor within AVIS.
2.  Trigger the execution of this script.
3.  Read the output of the script from AVIS.
4.  Read displayed AI permissions and simulated hardware status information from AVIS.
5.  Write another Python script to report these observed statuses.
6.  Trigger the execution of the reporting script.
7.  Read the final output.

## Purpose & Use Cases

*   **Validation of AVIS/ASCS:** Confirms that the AVIS and `AISimulationControlService` correctly handle UI interaction for code input, execution requests, permission checks (implicitly, as ASCS handles it), and display of results.
*   **Example Implementation:** Provides developers with a straightforward example of how an agent can programmatically control AVIS to achieve a goal involving code execution.
*   **Debugging Aid:** The agent's verbose print statements help trace the interaction flow with AVIS, which can be useful when debugging AVIS itself or more complex agents.
*   **Basic Integration Test:** Acts as an end-to-end test for the AVIS code execution loop from the perspective of a client agent.

## How it Works

The agent operates based on a hardcoded task plan and predefined IDs for expected virtual UI elements in AVIS:
*   `code_editor_id`: For typing code.
*   `run_button_id`: For triggering execution.
*   `output_display_id`: For reading `stdout`/`stderr` of executed code.
*   `ai_permissions_display_id`: For reading current AI permissions.
*   `sim_hw_status_display_id`: For reading simulated hardware status.

It uses helper methods to encapsulate AVIS commands (typing, clicking, reading element values).

## Running the Agent

The `SimpleCodingAgent` can be run using the driver script located at `examples/run_simple_coding_agent.py`.

To run it:
1.  Ensure you are in the root directory of the project.
2.  Execute the script:
    ```bash
    python examples/run_simple_coding_agent.py
    ```

The script will:
*   Set up the necessary environment, including `ResourceAwarenessService` and `AIVirtualInputService` (with a mock bash runner for code execution).
*   Load a predefined virtual UI into AVIS that contains the elements the agent expects.
*   Instantiate and run the `SimpleCodingAgent`.
*   Print detailed logs of the agent's actions and its interactions with AVIS.

This agent is not intended for production use but is a valuable tool for development and testing of the AVIS ecosystem.
