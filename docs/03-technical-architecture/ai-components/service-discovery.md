# Service Discovery Module

## Overview

The `ServiceDiscoveryModule` (`src/core_ai/service_discovery/service_discovery_module.py`) is a fundamental component of the Unified-AI-Project's Heterogeneous Service Protocol (HSP) ecosystem. Its primary role is to enable AI instances to **dynamically discover and register the capabilities** offered by other AI agents on the HSP network. This module is crucial for facilitating flexible and scalable multi-agent collaboration.

It acts as a central registry for advertised capabilities, ensuring that the `ProjectCoordinator` and other modules can efficiently find the right AI agent for a given task, while also maintaining the integrity and freshness of the capability information.

## Key Responsibilities and Features

1.  **Capability Registry (`known_capabilities`)**:
    *   Maintains an in-memory registry of all known capabilities advertised by various AI agents on the HSP network.
    *   Each entry includes the `HSPCapabilityAdvertisementPayload` (detailing the capability) and a `last_seen` timestamp.

2.  **Staleness Detection and Cleanup (`remove_stale_capabilities`)**:
    *   Automatically identifies and removes capabilities that have not been re-advertised within a configurable `staleness_threshold_seconds`.
    *   A background thread (`_periodic_cleanup`) ensures that the registry remains up-to-date and free of outdated information.

3.  **Processing Advertisements (`process_capability_advertisement`)**:
    *   Receives and processes incoming `HSPCapabilityAdvertisementPayload` messages from the HSP network.
    *   Updates existing capability entries or adds new ones, along with their `last_seen` timestamp.

4.  **Intelligent Capability Search (`find_capabilities`)**:
    *   Provides a robust querying mechanism to find capabilities based on various filters:
        *   Exact `capability_id` or `capability_name`.
        *   Inclusion of specific `tags`.
        *   Minimum `trust_score` of the advertising AI (integrates with `TrustManager`).
    *   Automatically excludes stale capabilities from search results.

5.  **Trust Integration**: 
    *   Leverages the `TrustManager` to assess the credibility of AI agents advertising capabilities. This ensures that the system prioritizes capabilities from trustworthy sources.

## How it Works

When an AI agent starts or updates its capabilities, it publishes an `HSPCapabilityAdvertisementPayload` message to the HSP network. The `ServiceDiscoveryModule` listens for these messages and updates its `known_capabilities` registry. Periodically, a background task prunes any capabilities that haven't been seen recently, ensuring the registry remains current.

Other modules, such as the `ProjectCoordinator`, can then query the `ServiceDiscoveryModule` to find agents that offer specific functionalities. The search results are filtered by various criteria, including the trust score of the advertising agent, providing a reliable list of available capabilities.

## Integration with Other Modules

-   **`HSPConnector`**: Provides the underlying communication mechanism for receiving capability advertisements.
-   **`TrustManager`**: Supplies trust scores that are used to filter and prioritize capabilities from different AI agents.
-   **`ProjectCoordinator`**: The primary consumer of this module, using it to find suitable agents for subtask delegation.
-   **`AgentManager`**: May interact with the `ServiceDiscoveryModule` to verify that newly launched agents successfully advertise their capabilities.

## Code Location

`src/core_ai/service_discovery/service_discovery_module.py`
