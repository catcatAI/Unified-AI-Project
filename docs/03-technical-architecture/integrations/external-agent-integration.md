# External Agent Integration Architecture

## I. Philosophy: A Hybrid AI Ecosystem

The `Unified-AI-Project` is designed as a hybrid AI ecosystem. This means it does not rely solely on its internal, built-in AI capabilities (like the systems powering the game character, Angela). Instead, a core part of its architecture is dedicated to **integrating with and orchestrating external, third-party AI agents and tools** (such as Rovo Dev Agent, Gemini, etc.).

This approach allows the platform to:

-   **Leverage Best-in-Class Tools**: Instead of reinventing the wheel, the project can incorporate the specialized capabilities of various external AI services.
-   **Maintain Modularity**: The core internal AI systems can remain focused on their primary tasks (e.g., game character simulation), while specialized tasks (like Atlassian integration) are delegated to external agents.
-   **Create a Flexible, Extensible Platform**: New tools and agents can be integrated into the system over time by creating new connectors and bridges, without requiring a fundamental redesign of the core architecture.

## II. Integration Mechanism

The integration of external agents is achieved through a set of dedicated software components within the `apps/backend/src/integrations` directory.

### Key Components:

1.  **Connectors (`..._connector.py`)**: These modules are responsible for the low-level communication with the external agent's API. They handle aspects like authentication, request formatting, and response parsing.
    -   *Example*: `enhanced_rovo_dev_connector.py` manages the connection to the Rovo Dev Agent.

2.  **Bridges (`..._bridge.py`)**: These modules act as a higher-level abstraction layer. They translate the external agent's data model and API into a format that is understood by the `Unified-AI-Project`'s internal systems. They expose a set of standardized methods that the core AI can use, regardless of the specific external agent being called.
    -   *Example*: `atlassian_bridge.py` provides a clean interface for the rest of the system to interact with Atlassian services, using the Rovo Dev Agent as the underlying engine.

3.  **Agent Implementations (`..._agent.py`)**: These are client-side representations or controllers for the external agents. They are responsible for managing the lifecycle and state of the integration.
    -   *Example*: `rovo_dev_agent.py` contains the logic for starting, stopping, and managing tasks related to the Rovo Dev Agent integration.

## III. Workflow Example: Creating a Jira Issue

1.  An internal module (e.g., `ProjectCoordinator`) determines that a Jira issue needs to be created.
2.  It calls a high-level method on the `AtlassianBridge` (e.g., `create_jira_issue(summary, description)`).
3.  The `AtlassianBridge` translates this request into a format that the `RovoDevConnector` understands.
4.  The `RovoDevConnector` sends the formatted request to the external Rovo Dev Agent API.
5.  The external Rovo Dev Agent performs the action (creating the Jira issue).
6.  The response flows back through the `Connector` and `Bridge`, and is returned to the original calling module.

This layered architecture ensures that the internal systems of the `Unified-AI-Project` are decoupled from the specific implementation details of the external tools they use, creating a robust and maintainable hybrid AI platform.
