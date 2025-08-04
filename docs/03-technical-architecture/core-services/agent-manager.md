# Agent Manager

## Overview

The `AgentManager` (`src/core_ai/agent_manager.py`) is a critical component within the Unified-AI-Project responsible for **managing the lifecycle of specialized sub-agents**. It provides the capabilities to dynamically launch, monitor, and terminate sub-agent processes, enabling the system to efficiently utilize resources and scale its functionalities based on task demands.

This module is fundamental to the project's multi-agent architecture, allowing the central AI (Angela) to orchestrate complex tasks by delegating them to specialized, independent AI processes.

## Key Responsibilities and Features

1.  **Agent Discovery (`_discover_agent_scripts`)**:
    *   Scans the `src/agents` directory to identify available Python scripts that implement specialized sub-agents.
    *   Maintains a map of agent names to their corresponding script paths, making them discoverable by other parts of the system.

2.  **Agent Launching (`launch_agent`)**:
    *   Initiates a new sub-agent process, running the agent's script using a specified Python executable.
    *   Manages a registry of `active_agents`, storing references to their process objects.
    *   Prevents launching an agent if it's already running, ensuring resource efficiency.

3.  **Agent Shutdown (`shutdown_agent`)**:
    *   Gracefully terminates a running sub-agent process.
    *   Attempts a graceful termination (SIGTERM) and, if necessary, forces termination (SIGKILL) after a timeout.

4.  **Bulk Shutdown (`shutdown_all_agents`)**:
    *   Provides a convenient method to shut down all sub-agent processes currently managed by the `AgentManager`.

5.  **Basic Agent Health Check (`check_agent_health`)**:
    *   Performs a rudimentary check to see if an agent's process is still alive.
    *   (Note: This is a placeholder for more sophisticated health checks that would involve inter-process communication with the agent itself.)

6.  **Waiting for Agent Readiness (`wait_for_agent_ready`)**:
    *   A utility method that polls the `ServiceDiscoveryModule` to check if a newly launched agent has successfully advertised its capabilities, indicating it's ready to receive tasks.

## How it Works

The `AgentManager` is initialized with the path to the Python executable. It then discovers all available agent scripts. When a request to launch an agent comes in (e.g., from the `ProjectCoordinator`), it creates a new subprocess for that agent. It keeps track of active agents by their process IDs. For shutdown, it sends termination signals to the processes and waits for them to exit.

## Integration with Other Modules

-   **`ProjectCoordinator`**: The primary consumer of the `AgentManager`. The `ProjectCoordinator` uses it to dynamically launch specialized agents required to execute subtasks within a complex project.
-   **`ServiceDiscoveryModule`**: The `AgentManager` relies on the `ServiceDiscoveryModule` to confirm when a newly launched agent has successfully advertised its capabilities and is ready for task delegation.
-   **`BaseAgent`**: All sub-agents inherit from `BaseAgent`, which handles the common logic for agent startup, shutdown, and HSP communication, working in conjunction with the `AgentManager`.

## Code Location

`src/core_ai/agent_manager.py`
