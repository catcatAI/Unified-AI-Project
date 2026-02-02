# AgentManager: Lifecycle Management for Specialized Sub-Agents

## Overview

This document provides an overview of the `AgentManager` module (`src/core_ai/agent_manager.py`). Its primary function is to manage the lifecycle of specialized sub-agents, which includes discovering, launching, and terminating them as separate, independent processes.

## Purpose

The `AgentManager` is a key component for enabling a modular and scalable architecture. It allows the main AI system to delegate specific, complex, or long-running tasks to specialized agents that can run in parallel. This prevents blocking of the main AI loop and promotes a separation of concerns, where each agent can be an expert in a specific domain (e.g., data analysis, creative writing, web search).

## Key Responsibilities and Features

*   **Agent Discovery (`_discover_agent_scripts`)**: Automatically discovers available agent scripts within a designated directory (e.g., `src/agents`). This allows for the easy addition of new agents without requiring manual registration.
*   **Lifecycle Management**:
    *   **`launch_agent`**: Launches a specified agent in a new, non-blocking subprocess using `subprocess.Popen`. It ensures that the same agent is not launched multiple times if it is already running.
    *   **`shutdown_agent`**: Terminates a running agent process. It first attempts a graceful shutdown (using `SIGTERM`) and then forcefully terminates the process (using `SIGKILL`) if it does not respond within a timeout period.
    *   **`shutdown_all_agents`**: Provides a method to shut down all currently active agents that are managed by the `AgentManager`.
*   **Health Checking (`check_agent_health`)**: Includes a basic mechanism to check if an agent process is still running. (A more robust health check, such as inter-process communication, is noted as a potential future improvement).
*   **Readiness Probing (`wait_for_agent_ready`)**: Contains a placeholder method to wait for a newly launched agent to become "ready." This is achieved by monitoring for the agent's capability advertisement on the HSP network via the `ServiceDiscoveryModule`.

## How it Works

The `AgentManager` first discovers all available agent scripts and stores their paths in a map. When a request to launch an agent is received, it uses Python's `subprocess` module to execute the corresponding agent script in a new, independent process. It maintains a dictionary of these active agent processes, which allows it to track and manage them. To shut down an agent, it uses the stored process object to send the appropriate termination signals.

## Integration with Other Modules

*   **`subprocess`, `sys`, `os`, `logging`, `threading`**: Utilizes standard Python libraries for process management, system interaction, logging, and ensuring thread safety during agent launch.
*   **`core_services`**: Can be used to get access to other core services, particularly the `ServiceDiscoveryModule`, which is essential for the readiness probing mechanism.
*   **`DialogueManager`**: A primary consumer of the `AgentManager`. The `DialogueManager` would use this service to delegate complex tasks to specialized agents, allowing it to continue interacting with the user while the agent works in the background.

## Code Location

`src/core_ai/agent_manager.py`