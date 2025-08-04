# Trust Manager

## Overview

The `TrustManager` (`src/core_ai/trust_manager/trust_manager_module.py`) is a critical component within the Unified-AI-Project responsible for **assessing and managing the trustworthiness of other AI entities** (agents, services) interacting within the HSP network. In a multi-agent ecosystem, the ability to evaluate the reliability and credibility of information sources and service providers is paramount for robust decision-making and preventing the propagation of misinformation or unreliable data.

This module provides a quantitative measure of trust, allowing the AI to prioritize interactions with more reliable partners and to filter out potentially harmful or low-quality information.

## Key Responsibilities and Features

1.  **Trust Score Management**: 
    *   Maintains a registry of trust scores for known AI entities. Scores range from `0.0` (completely untrusted) to `1.0` (fully trusted).
    *   Assigns a `DEFAULT_TRUST_SCORE` (0.5) to newly encountered or unknown AI entities, representing a neutral starting point.

2.  **Capability-Specific Trust**: 
    *   Supports granular trust scores, allowing the system to track an AI's trustworthiness for specific capabilities (e.g., an AI might be highly trusted for "data analysis" but less so for "creative writing").
    *   If a capability-specific score exists, it is used; otherwise, it falls back to a general trust score for that AI.

3.  **Dynamic Trust Score Updates (`update_trust_score`)**: 
    *   Allows for the adjustment of an AI's trust score based on its performance, reliability, or other observed behaviors.
    *   Updates can be applied as an `adjustment` (relative change) or by setting a `new_absolute_score`.
    *   Ensures that trust scores remain within the defined `MIN_TRUST_SCORE` and `MAX_TRUST_SCORE` bounds.

4.  **Trust Score Retrieval (`get_trust_score`)**: 
    *   Provides a method to retrieve the current trust score for a given AI entity, optionally for a specific capability.

5.  **Default Trust Score Initialization (`set_default_trust_score`)**: 
    *   A utility method to initialize an AI's trust score to the default if it's not already known.

## How it Works

The `TrustManager` stores trust scores in an internal dictionary, mapping AI IDs to their respective score data (which can be general or capability-specific). When an AI needs to evaluate the trustworthiness of another AI (e.g., before accepting a fact from it or delegating a task), it queries the `TrustManager`. The `TrustManager` returns the most relevant trust score, considering specific capabilities if requested.

Trust scores are dynamically updated based on interactions. For instance, if an AI consistently provides accurate information or successfully completes tasks, its trust score can be increased. Conversely, failures or unreliable behavior can lead to a decrease in trust.

## Integration with Other Modules

-   **`ServiceDiscoveryModule`**: Uses the `TrustManager` to filter and prioritize capabilities advertised by other AI agents, ensuring that only trustworthy agents are considered for task delegation.
-   **`LearningManager`**: Critically relies on the `TrustManager` to assess the credibility of incoming facts from the HSP network, preventing the AI from learning from unreliable sources (part of the LIS concept).
-   **`ProjectCoordinator`**: May use trust scores when selecting agents for subtasks, preferring more trusted agents for critical operations.
-   **`HSPConnector`**: While not directly using trust scores for communication, the `HSPConnector` facilitates the exchange of information that can then be evaluated by the `TrustManager`.

## Code Location

`src/core_ai/trust_manager/trust_manager_module.py`
