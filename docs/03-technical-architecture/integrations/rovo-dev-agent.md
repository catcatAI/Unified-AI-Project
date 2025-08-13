# RovoDevAgent: Intelligent Development Assistant

## Overview

This document provides an overview of the `RovoDevAgent` module (`src/integrations/rovo_dev_agent.py`). This module implements an intelligent development assistant agent that integrates deeply with the Atlassian ecosystem, including Jira, Confluence, and Bitbucket.

## Purpose

The `RovoDevAgent` is designed to automate and assist with a variety of software development tasks. By leveraging the Atlassian suite of tools, it can perform actions such as code analysis, documentation generation, issue tracking, and project management, acting as a force multiplier for development teams.

## Key Responsibilities and Features

*   **Capability-Based Design**: The agent defines a set of specific capabilities that it can perform, such as `code_analysis`, `documentation_generation`, and `issue_tracking`. These capabilities are advertised on the Heterogeneous Service Protocol (HSP) network, allowing other AI agents and services to discover and utilize them.
*   **Asynchronous Task Processing**: Utilizes an `asyncio.Queue` to manage and process incoming tasks asynchronously. This allows the agent to handle multiple requests concurrently without blocking.
*   **Deep Atlassian Integration**: Leverages the `AtlassianBridge` to provide a rich set of interactions with Jira, Confluence, and Bitbucket. This includes creating and updating issues, generating reports, publishing documentation, and more.
*   **Resilience and Recovery**:
    *   **State Persistence**: The agent can save and restore its state, including active tasks and performance metrics, to and from pickle files. This allows it to recover from crashes and resume its work.
    *   **Automatic Task Retries**: Automatically retries failed tasks based on a configurable retry policy, which helps to overcome transient errors.
    *   **Degraded Mode**: Can automatically enter a "degraded mode" if it detects a high error rate or a loss of connectivity. In this mode, it disables non-critical capabilities to ensure that core functionalities remain available.
*   **Health Monitoring**: Includes a background task that continuously monitors the health of the agent and its dependencies, such as the `RovoDevConnector`.
*   **HSP Integration**: 
    *   Connects to the HSP network using the `EnhancedRovoDevConnector`.
    *   Advertises its capabilities on the HSP network, making them discoverable by other agents.
    *   Receives tasks from other agents and services via HSP.

## How it Works

The `RovoDevAgent` is initialized with a configuration dictionary and an optional `AgentManager`. When the agent is started, it connects to the HSP network and begins listening for tasks on its asynchronous queue. Each task is an `HSPTask` object that specifies a capability and a set of parameters. The agent dispatches the task to the appropriate handler method (e.g., `_handle_code_analysis`), which then uses the `AtlassianBridge` to perform the requested action. The agent tracks the state of each task, and its resilience mechanisms allow it to handle failures gracefully, either by retrying the task or by entering a degraded mode of operation.

## Integration with Other Modules

*   **`EnhancedRovoDevConnector`**: The primary connector used for all HSP communication.
*   **`AtlassianBridge`**: The bridge layer that provides a unified interface to all Atlassian services.
*   **`AgentManager`**: Can be used to manage the lifecycle of the `RovoDevAgent` itself, including launching and shutting it down.
*   **`HSPTask`**: The standardized data structure for tasks that are received from the HSP network.

## Code Location

`src/integrations/rovo_dev_agent.py`