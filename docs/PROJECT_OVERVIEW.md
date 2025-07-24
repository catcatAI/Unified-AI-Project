# Unified AI Project: Architecture Overview

The Unified AI Project is a sophisticated, multi-agent system designed for complex task execution. It features a modular and scalable architecture that allows for dynamic collaboration between a central coordinator and specialized agents.

## High-Level Architecture

The project follows a distributed, service-oriented architecture where a central "meta-agent" named Angela orchestrates the execution of complex tasks by delegating them to a network of specialized sub-agents. The key architectural principles are:

- **Modularity**: The system is composed of independent components with well-defined responsibilities, such as dialogue management, project coordination, agent management, and communication.
- **Scalability**: New capabilities can be added by creating new agents and tools without modifying the core system. The use of a message broker (MQTT) for communication allows the system to scale to a large number of agents.
- **Dynamic Collaboration**: The system can dynamically launch and shut down agents based on the requirements of the task at hand. This allows for efficient use of resources.
- **Service-Oriented**: Agents expose their functionalities as services on a network, which can be discovered and consumed by other components.

The following diagram illustrates the high-level architecture of the project:

```mermaid
graph TD
    subgraph User Interfaces
        A[FastAPI Web Server]
        B[Command-Line Interface]
    end

    subgraph Core System
        C[Dialogue Manager]
        D[Project Coordinator]
        E[Agent Manager]
        F[Service Discovery]
        G[HAM Memory]
        H[Learning Manager]
    end

    subgraph Communication
        I[HSP Connector (MQTT)]
    end

    subgraph Agents
        J[Data Analysis Agent]
        K[Creative Writing Agent]
        L[...]
    end

    A --> C
    B --> C
    C --> D
    D -- Manages --> E
    D -- Uses --> F
    D -- Communicates via --> I
    I -- Communicates with --> J
    I -- Communicates with --> K
    I -- Communicates with --> L
    E -- Launches/Terminates --> J
    E -- Launches/Terminates --> K
    E -- Launches/Terminates --> L
    F -- Discovers --> J
    F -- Discovers --> K
    F -- Discovers --> L
    D -- Uses --> G
    D -- Uses --> H
```

## Core Components

This section provides a detailed description of each major component of the Unified AI Project.

### Entry Points

The system provides two primary entry points for user interaction:

-   **`src/services/main_api_server.py`**: A FastAPI application that exposes a RESTful API for interacting with the AI. It handles chat, session management, and HSP-related requests. It uses a `lifespan` event handler to initialize and shut down the core services.
-   **`src/interfaces/cli/main.py`**: A command-line interface that allows users to interact with the AI from the terminal. It supports sending queries and publishing facts to the HSP network.

### Core Services (`src/core_services.py`)

This module is the heart of the application's backend. It uses a singleton pattern to initialize and provide access to all major components. The `initialize_services` function is called by the entry points to set up the application's environment.

### Dialogue and Project Management

-   **`src/core_ai/dialogue/dialogue_manager.py`**: The `DialogueManager` is the first point of contact for user queries. It identifies complex project requests and delegates them to the `ProjectCoordinator`. For simpler queries, it can provide a direct response.
-   **`src/core_ai/dialogue/project_coordinator.py`**: The `ProjectCoordinator` implements the "four-draw" model for complex task execution. It decomposes a project query into a dependency graph of subtasks, orchestrates the execution of these tasks by delegating them to the appropriate agents, and integrates the results into a final response.

### Agent Collaboration Framework

-   **`src/core_ai/agent_manager.py`**: The `AgentManager` is responsible for managing the lifecycle of the sub-agents. It can discover available agent scripts, launch them in separate processes when needed, and terminate them when they are no longer required.
-   **`src/core_ai/service_discovery/service_discovery_module.py`**: This module keeps track of the capabilities advertised by all agents on the HSP network. The `ProjectCoordinator` uses it to find the right agent for a given task. It also handles stale capabilities and filters them based on trust scores.
-   **`src/agents/`**: This directory contains the implementations of the specialized sub-agents. Each agent inherits from `BaseAgent`, defines its capabilities, and implements a `handle_task_request` method to process tasks.

### Communication

-   **`src/hsp/connector.py`**: The `HSPConnector` is a gmqtt-based client that handles all communication over the Heterogeneous Service Protocol (HSP) network. It provides methods for publishing facts, sending task requests, and receiving results.
-   **HSP (Heterogeneous Service Protocol)**: A custom protocol built on top of MQTT that defines the message formats and communication patterns for interaction between the coordinator and the agents.

### Learning and Memory

-   **`src/core_ai/memory/ham_memory_manager.py`**: The `HAMMemoryManager` provides a Hierarchical Abstractive Memory for storing and retrieving experiences, facts, and dialogue context.
-   **`src/core_ai/learning/learning_manager.py`**: The `LearningManager` is responsible for learning from completed projects to improve future performance. It can analyze successful and failed project executions to refine its strategies.

## Key Workflows

This section illustrates the key workflows of the Unified AI Project.

### The "Four-Draw" Model for Complex Project Execution

The "four-draw" model is the core workflow for handling complex user requests. It consists of four main phases:

1.  **Instruction Understanding and Expansion**: The `ProjectCoordinator` receives a user query and uses an LLM to expand it into a detailed project plan.
2.  **Task Decomposition and Publishing**: The `ProjectCoordinator` decomposes the project plan into a DAG of subtasks and publishes them to the HSP network.
3.  **Distributed Execution and Result Return**: Specialized agents on the network execute the subtasks and return the results.
4.  **Result Integration and Feedback**: The `ProjectCoordinator` integrates the results from the agents into a final response and presents it to the user.

The following diagram illustrates this workflow:

```mermaid
graph TD
    A[User Query] --> B{1. Instruction Understanding};
    B --> C{2. Task Decomposition};
    C --> D[Subtask 1];
    C --> E[Subtask 2];
    C --> F[...];
    D --> G{3. Distributed Execution};
    E --> G;
    F --> G;
    G --> H{4. Result Integration};
    H --> I[Final Response];
```

### Agent Discovery and Task Dispatching

When the `ProjectCoordinator` needs to execute a subtask, it follows this workflow to find and dispatch it to an agent:

1.  **Find Capability**: The `ProjectCoordinator` queries the `ServiceDiscoveryModule` to find an agent with the required capability.
2.  **Launch Agent (if necessary)**: If no running agent has the required capability, the `ProjectCoordinator` asks the `AgentManager` to launch a suitable agent.
3.  **Send Task Request**: The `ProjectCoordinator` sends a task request to the agent via the `HSPConnector`.
4.  **Wait for Result**: The `ProjectCoordinator` waits for the agent to complete the task and return the result.

The following diagram illustrates this workflow:

```mermaid
sequenceDiagram
    participant PC as ProjectCoordinator
    participant SDM as ServiceDiscoveryModule
    participant AM as AgentManager
    participant Agent
    participant HSP

    PC->>SDM: Find capability
    SDM-->>PC: Agent found
    alt Agent not running
        PC->>AM: Launch agent
        AM-->>PC: Agent launched
    end
    PC->>HSP: Send task request
    HSP->>Agent: Task request
    Agent-->>HSP: Task result
    HSP-->>PC: Task result
```

### HSP Communication Flow

All communication between the `ProjectCoordinator` and the agents is done via the HSP protocol over MQTT. Here's a typical communication flow:

1.  **Agent Advertisement**: When an agent starts, it advertises its capabilities by publishing an `HSPCapabilityAdvertisementPayload` message to the HSP network.
2.  **Task Request**: The `ProjectCoordinator` sends a task to an agent by publishing an `HSPTaskRequestPayload` message.
3.  **Task Result**: The agent completes the task and returns the result by publishing an `HSPTaskResultPayload` message.

This asynchronous, message-based communication allows for a flexible and scalable system.

## Configuration and Setup

This section explains how to set up and configure the Unified AI Project.

### Dependencies and Installation

The project's dependencies are defined in `pyproject.toml` and are categorized into `core`, `ai`, `web`, `testing`, etc. This allows for flexible installation based on the desired features.

The recommended way to install the project is to use the command-line installer:

```bash
python installer_cli.py
```

This script guides the user through the installation process, including selecting an installation type (e.g., `minimal`, `standard`, `full`) and generating the `.env` file.

### Environment Variables

The project uses a `.env` file for configuration. A template for this file is provided in `.env.example`. The key environment variables are:

-   `MIKO_HAM_KEY`: The encryption key for the HAM memory manager.
-   `GEMINI_API_KEY`: The API key for Google Gemini.
-   `OPENAI_API_KEY`: The API key for OpenAI.
-   `PYTHON_EXECUTABLE`: The path to the Python executable.

### Running the Application

The application can be run in several ways:

-   **API Server**: `uvicorn src.services.main_api_server:app --reload --host 0.0.0.0 --port 8000`
-   **CLI**: `python src/interfaces/cli/main.py query "Your query"`
-   **Agents**: `python src/agents/data_analysis_agent.py`
