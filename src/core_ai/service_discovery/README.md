# HSP Service Discovery Module

## Overview

The `ServiceDiscoveryModule`, located at `src/core_ai/service_discovery/service_discovery_module.py`, is responsible for discovering and managing capabilities advertised by other AI entities (peers) on the Heterogeneous Synchronization Protocol (HSP) network.

This module replaces a previous generic service registry and is specifically designed to work within the HSP ecosystem.

## Key Features

*   **HSP Capability Processing:**
    *   Receives `HSPCapabilityAdvertisementPayload` messages (typically via the `HSPConnector`).
    *   Stores and manages these advertisements.
*   **Integration with TrustManager:**
    *   Uses an instance of the `TrustManager` to retrieve trust scores for AIs advertising capabilities.
    *   Allows filtering and sorting of discovered capabilities based on these trust scores.
*   **Staleness Handling:**
    *   Advertisements are considered stale and are filtered out if not re-advertised within a configurable threshold (`staleness_threshold_seconds`).
*   **Flexible Querying:**
    *   Provides methods to find capabilities based on:
        *   Capability ID (`capability_id_filter`)
        *   Capability Name (`capability_name_filter`, case-insensitive exact match)
        *   Tags (`tags_filter`, case-insensitive, requires all specified tags to be present)
        *   Minimum trust score of the advertising AI (`min_trust_score`)
        *   Availability status (`exclude_unavailable` flag, defaults to true to only show 'online' capabilities).
*   **Sorting:**
    *   Can sort query results by the trust score of the advertising AI (descending by default).
*   **Thread Safety:** Internal storage access is protected by a `threading.Lock` to ensure safe operations when advertisements are processed from different threads (e.g., MQTT callbacks).

## How it Works

1.  **Initialization:**
    *   The `ServiceDiscoveryModule` is initialized with an instance of `TrustManager` and a `staleness_threshold_seconds` value.
2.  **Processing Advertisements (`process_capability_advertisement`):**
    *   This method is typically registered as a callback with the `HSPConnector`.
    *   When an `HSPCapabilityAdvertisementPayload` is received, this method validates it, records the `sender_ai_id` (from the HSP envelope), the current time as `last_seen_timestamp`, and stores the capability information.
    *   If a capability with the same `capability_id` is re-advertised, its entry (including `last_seen_timestamp` and potentially updated payload) is refreshed.
3.  **Storing Capabilities:**
    *   Capabilities are stored internally in a dictionary, keyed by `capability_id`. Each entry includes the payload, the sender's AI ID, the last seen timestamp, and the original message ID from the HSP envelope.
4.  **Querying (`find_capabilities`, `get_capability_by_id`, `get_all_capabilities`):**
    *   When a query is made:
        *   Stale entries are filtered out based on their `last_seen_timestamp` and the `staleness_threshold_seconds`.
        *   Filters for name, ID, tags, and availability are applied.
        *   If `min_trust_score` is provided, the `TrustManager` is consulted for each potential capability's advertiser, and those below the threshold are filtered out.
        *   Results can be sorted by trust score.

## Integration

*   **`core_services.py`:** This central service initializer is responsible for:
    *   Instantiating the `TrustManager`.
    *   Instantiating the `ServiceDiscoveryModule`, providing it with the `TrustManager` instance.
    *   Instantiating the `HSPConnector`.
    *   Registering the `ServiceDiscoveryModule`'s `process_capability_advertisement` method as a callback with the `HSPConnector` so it can receive incoming advertisements.
*   **`DialogueManager` (or other capability consumers):**
    *   Can query the `ServiceDiscoveryModule` instance (obtained via `get_services()`) to find available HSP capabilities from other AIs before dispatching tasks via HSP.

## Configuration

*   **`staleness_threshold_seconds`:** Passed during instantiation. Defines how long a capability advertisement remains valid if not refreshed. Defaults to 24 hours (3600 * 24 seconds).

This module is crucial for enabling dynamic and trust-aware discovery of services in the HSP network, facilitating more intelligent and robust inter-AI collaboration.
