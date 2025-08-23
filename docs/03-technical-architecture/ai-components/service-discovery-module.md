# ServiceDiscoveryModule: Dynamic Service Discovery and Trust-Aware Capability Management

## Overview

This document provides an overview of the `ServiceDiscoveryModule` (`src/core_ai/service_discovery/service_discovery_module.py`). This module is responsible for managing the discovery and registry of capabilities advertised by other AIs on the Heterogeneous Service Protocol (HSP) network, with integrated trust assessment via a `TrustManager`.

## Purpose

The primary purpose of the `ServiceDiscoveryModule` is to enable dynamic, flexible, and trustworthy communication and collaboration between different AI agents within the HSP network. It allows AI agents to efficiently discover what services and capabilities other AIs offer, and critically, to assess the trustworthiness of those advertising agents. This facilitates intelligent task delegation, resource sharing, and the formation of collaborative AI ecosystems.

## Key Responsibilities and Features

*   **Capability Registry**: Maintains an internal, thread-safe registry of `HSPCapabilityAdvertisementPayload` objects received from other AIs. Each entry is associated with a `last_seen` timestamp to track its recency.
*   **Staleness Management**: Implements a mechanism to periodically remove stale capability advertisements from the registry based on a configurable `staleness_threshold_seconds`. This ensures that the registry remains current and only contains active and relevant capabilities, preventing attempts to connect to offline or outdated services.
*   **Capability Processing (`process_capability_advertisement`)**:
    *   Receives and processes incoming `HSPCapabilityAdvertisementPayload` messages from the HSP network.
    *   Stores new capabilities or updates existing ones in the registry, refreshing their `last_seen` timestamp.
    *   Performs basic validation (e.g., checking for `capability_id` and `ai_id` presence) and logs the processing of advertisements.
*   **Capability Discovery (`find_capabilities`)**:
    *   Provides a flexible querying interface to search the registry for capabilities based on various filters, including `capability_id`, `name`, `tags` (requiring all specified tags to be present), and `min_trust_score`.
    *   **Note:** This is an asynchronous method (`async def`) and should be `await`ed when called.
    *   Automatically excludes stale entries from search results.
    *   Can sort the results by the trust score of the advertising AI, allowing for prioritization of more trustworthy services.
*   **Trust Integration**: Integrates directly with a `TrustManager` instance. This allows the module to query the trustworthiness of AI agents advertising capabilities, and to use this trust score as a filtering or sorting criterion during capability discovery.
*   **Thread-Safe Operations**: Utilizes a `threading.RLock` to ensure that concurrent access to the `known_capabilities` registry is thread-safe, preventing data corruption in multi-threaded environments.
*   **Background Cleanup Task**: Can initiate a daemon thread (`_periodic_cleanup`) that periodically runs the `remove_stale_capabilities` method, automating the maintenance of the registry.

## How it Works

The `ServiceDiscoveryModule` operates by continuously listening for `HSPCapabilityAdvertisementPayload` messages broadcasted on the HSP network. When such a message is received, it updates its internal `known_capabilities` registry, recording the details of the advertised capability and the time it was last seen. Other AI components or services can then query this module using `find_capabilities` to discover available services, optionally filtering by criteria such as trust score or specific features. A dedicated background thread ensures that outdated or unresponsive capabilities are automatically pruned from the registry, maintaining its accuracy and relevance.

## Integration with Other Modules

*   **`TrustManager`**: A crucial dependency that provides the trust assessment capabilities, allowing the `ServiceDiscoveryModule` to filter and prioritize capabilities based on the trustworthiness of the advertising AI agents.
*   **HSP Type Definitions**: Relies on `HSPCapabilityAdvertisementPayload` and `HSPMessageEnvelope` (from `src.hsp.types`) for the structured representation of HSP messages.
*   **AI Agents/Services**: Any AI agent or service that wishes to advertise its capabilities to the network or discover capabilities offered by others would interact with this `ServiceDiscoveryModule`.

## Code Location

`src/core_ai/service_discovery/service_discovery_module.py`