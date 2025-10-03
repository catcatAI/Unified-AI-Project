# src/core_ai/service_discovery/service_discovery_module.py

import logging
import threading
from datetime import datetime, timezone
from typing import Dict, Optional, List, Tuple

# 修复导入路径 - 使用正确的模块路径
from apps.backend.src.hsp.types import HSPCapabilityAdvertisementPayload, HSPMessageEnvelope
# Assuming TrustManager is correctly importable. If it's in the same directory, this might need adjustment
# based on how __init__.py in trust_manager_module's folder is set up.
# For now, direct import path as per typical project structure.
from trust_manager.trust_manager_module import TrustManager

logger: Any = logging.getLogger(__name__)

class ServiceDiscoveryModule:
    """
    Manages discovery and registry of capabilities advertised by other AIs:
    on the HSP network, integrating with a TrustManager.:
    This module is intended to handle HSPCapabilityAdvertisementPayload objects.
    """
    DEFAULT_STALENESS_THRESHOLD_SECONDS: int = 600 # 10 minutes

    def __init__(self, trust_manager: TrustManager, staleness_threshold_seconds: Optional[int] = None) -> None:
    """
        Initializes the ServiceDiscoveryModule for HSP capabilities.:

    Args:
    _ = trust_manager (TrustManager) An instance of the TrustManager to use for
                                          assessing the trustworthiness of capability advertisers.:
    _ = staleness_threshold_seconds (Optional[int]) The duration in seconds after which
                                                         a capability advertisement is considered stale.
                                                         Defaults to DEFAULT_STALENESS_THRESHOLD_SECONDS.
    """
    self.trust_manager: TrustManager = trust_manager
    # Stores capability_id -> (HSPCapabilityAdvertisementPayload, last_seen_datetime_utc)
    self.known_capabilities: Dict[str, Tuple[HSPCapabilityAdvertisementPayload, datetime]] =
    self.lock = threading.RLock # For thread-safe access to known_capabilities

        if staleness_threshold_seconds is None:


    self.staleness_threshold_seconds = self.DEFAULT_STALENESS_THRESHOLD_SECONDS
        else:

            self.staleness_threshold_seconds = staleness_threshold_seconds

    self._cleanup_thread = None
    self._stop_event = threading.Event

    logger.info(
            "HSP ServiceDiscoveryModule initialized. Staleness threshold: %d seconds.",
            self.staleness_threshold_seconds
    )

    def start_cleanup_task(self, cleanup_interval_seconds: int = 60)
    """Starts the periodic cleanup task in a background thread."""
        if self._cleanup_thread is None:

    self._stop_event.clear
            self._cleanup_thread = threading.Thread(
                target=self._periodic_cleanup,
                args=(cleanup_interval_seconds,),
                daemon=True
            )
            self._cleanup_thread.start
            logger.info(f"ServiceDiscoveryModule cleanup task started with interval {cleanup_interval_seconds}s.")

    def stop_cleanup_task(self)
    """Stops the periodic cleanup task."""
        if self._cleanup_thread is not None:

    self._stop_event.set
            self._cleanup_thread.join(timeout=5) # Add a timeout to prevent indefinite blocking
            self._cleanup_thread = None
            logger.info("ServiceDiscoveryModule cleanup task stopped.")

    def _periodic_cleanup(self, cleanup_interval_seconds: int)
        """The target function for the cleanup thread.""":
    while not self._stop_event.is_set:

    self.remove_stale_capabilities
            # Use wait instead of sleep to allow earlier exit on stop event
            self._stop_event.wait(cleanup_interval_seconds)

    def remove_stale_capabilities(self)
    """Removes capabilities that have exceeded the staleness threshold."""
    with self.lock:
    current_time = datetime.now(timezone.utc)
            stale_keys = [
                key for key, (_, last_seen) in self.known_capabilities.items:
    if (current_time - last_seen).total_seconds > self.staleness_threshold_seconds
            ]
            for key in stale_keys:

    del self.known_capabilities[key]
                logger.info(f"Removed stale capability: {key}")

    def process_capability_advertisement(
    self,
    payload: HSPCapabilityAdvertisementPayload,
    sender_ai_id: str,  # The direct sender from the HSP envelope
        envelope: HSPMessageEnvelope # Full envelope for context if needed
    ) -> None:
    """
    Processes an incoming HSPCapabilityAdvertisementPayload.
    Stores or updates the capability in the registry with a 'last_seen' timestamp.:

    Args:
    _ = payload (HSPCapabilityAdvertisementPayload) The capability advertisement data.
            _ = sender_ai_id (str) The AI ID of the direct sender of this message.
                                (May or may not be the same as payload.get('ai_id')).
            _ = envelope (HSPMessageEnvelope) The full message envelope.
    """
    logger.debug("Entering process_capability_advertisement. Payload: %s, Sender: %s, Envelope: %s", payload, sender_ai_id, envelope)

    capability_id = payload.get('capability_id')
    advertiser_ai_id = payload.get('ai_id') # The AI actually offering the capability

        if not capability_id:


    logger.error("Received capability advertisement with no capability_id. Discarding. Payload: %s", payload)
            return

        if not advertiser_ai_id
    logger.error("Received capability advertisement (ID: %s) with no 'ai_id' (advertiser AI ID) in payload. Discarding. Payload: %s", capability_id, payload)
            return

    logger.debug("Processing capability advertisement: ID=%s, AI=%s, Sender=%s", capability_id, advertiser_ai_id, sender_ai_id)

        # Optional Could use sender_ai_id for additional trust checks or logging if different from advertiser_ai_id
        # For now, the primary identifier for trust is the advertiser_ai_id from the payload.

    with self.lock:
    current_time = datetime.now(timezone.utc)
            self.known_capabilities[capability_id] = (payload, current_time)
            logger.info(
                "Processed capability advertisement for ID: %s from AI: %s (Sender: %s). Last seen updated to: %s.",
                _ = capability_id, advertiser_ai_id, sender_ai_id, current_time.isoformat
            )
            logger.debug("Stored capability: %s, Last seen: %s", capability_id, current_time.isoformat)
            # Log the current state of known_capabilities for debugging
    logger.debug("Current known_capabilities state after update: %s",
                        {cap_id: cap_data[0].get('name') for cap_id, cap_data in self.known_capabilities.items}):

    async def find_capabilities(
    self,
    capability_id_filter: Optional[str] = None,
    capability_name_filter: Optional[str] = None,
    tags_filter: Optional[List[str]] = None,
    min_trust_score: Optional[float] = None,
    sort_by_trust: bool = False
    ) -> List[HSPCapabilityAdvertisementPayload]:
    """
    Finds registered capabilities based on specified filters, excluding stale entries.
        A capability is considered stale if its 'last_seen' timestamp is older than:
    the configured 'staleness_threshold_seconds'.

    Args:
    capability_id_filter: Filter by exact capability ID.
            capability_name_filter: Filter by exact capability name.
            tags_filter: Filter by capabilities that include ALL specified tags.
            min_trust_score: Filter by capabilities from AIs with at least this trust score.:
    sort_by_trust: If True, sort results by trust score in descending order.

    Returns:
            A list of HSPCapabilityAdvertisementPayload objects matching the criteria.
    """
        # Tuples of (payload, trust_score) for potential sorting
    pre_results: List[Tuple[HSPCapabilityAdvertisementPayload, float]] =

    current_time = datetime.now(timezone.utc)

    logger.debug("Finding capabilities with filters: ID=%s, Name=%s, Tags=%s, MinTrust=%s, SortByTrust=%s",
                     capability_id_filter, capability_name_filter, tags_filter, min_trust_score, sort_by_trust)
    logger.debug("Current known_capabilities before filtering: %s", self.known_capabilities)

    with self.lock:
            # Iterate over a copy of values in case of concurrent modification (though less likely here)
            # No, iterate items to get capability_id for logging if needed.
            # capabilities_to_check = list(self.known_capabilities.values)
            # Iterate items to get capability_id for logging if needed.
    capabilities_to_iterate = list(self.known_capabilities.items)


            for capability_id, (payload, last_seen) in capabilities_to_iterate:



    logger.debug("Checking capability: %s, Last seen: %s", capability_id, last_seen.isoformat)
                # --- Staleness Check ---
                age_seconds = (current_time - last_seen).total_seconds
                logger.debug("Capability %s age: %.2fs, threshold: %ds", capability_id, age_seconds, self.staleness_threshold_seconds)
                if age_seconds > self.staleness_threshold_seconds:

    logger.debug("Skipping stale capability ID: %s (age: %.2fs > threshold: %ds)", capability_id, age_seconds, self.staleness_threshold_seconds)
                    continue

                # Apply capability_id_filter
                if capability_id_filter and capability_id != capability_id_filter:

    logger.debug("Skipping capability %s: ID filter mismatch (expected %s)", capability_id, capability_id_filter)
                    continue

                # Apply capability_name_filter with exact matching for test compatibility
    if capability_name_filter:

    payload_name = payload.get('name', '')
                    # Exact match only for test compatibility
    if payload_name != capability_name_filter:

    logger.debug("Skipping capability %s: Name filter mismatch (expected %s, got %s)", capability_id, capability_name_filter, payload_name)
                        continue

                # Apply tags_filter (must match ALL tags in filter)
                if tags_filter:

    capability_tags = payload.get('tags', )
                    if not capability_tags or not all(tag in capability_tags for tag in tags_filter)

    logger.debug("Skipping capability %s: Tags filter mismatch (expected all of %s, got %s)", capability_id, tags_filter, capability_tags)
                        continue

                advertiser_ai_id = payload.get('ai_id')
                if not advertiser_ai_id:

    logger.warning("Found capability with no advertiser_ai_id during find: %s. Skipping.", payload.get('capability_id'))
                    continue

                trust_score = self.trust_manager.get_trust_score(advertiser_ai_id)
                logger.debug("Capability %s trust score: %.2f (min_trust_score: %s)", capability_id, trust_score, min_trust_score)

                # Apply min_trust_score filter
                if min_trust_score is not None and trust_score < min_trust_score:

    logger.debug("Skipping capability %s: Trust score %.2f below min_trust_score %.2f", capability_id, trust_score, min_trust_score)
                    continue

                pre_results.append((payload, trust_score))

        # Sort if requested
    if sort_by_trust:

    pre_results.sort(key=lambda item: item[1], reverse=True) # Sort by trust_score descending

        # Extract just the payloads for the final list
    final_results = [payload for payload, _ in pre_results]:

    logger.info("Found %d capabilities matching criteria. ID_filter: %s, Name_filter: %s, Tags_filter: %s, Min_trust: %s",
                    len(final_results), capability_id_filter, capability_name_filter, tags_filter, min_trust_score)
    return final_results

    def _find_capabilities_sync(
    self,
    capability_id_filter: Optional[str] = None,
    capability_name_filter: Optional[str] = None,
    tags_filter: Optional[List[str]] = None,
    min_trust_score: Optional[float] = None,
    sort_by_trust: bool = False
    ) -> List[HSPCapabilityAdvertisementPayload]:
    """
    Synchronous version of find_capabilities.
    Finds registered capabilities based on specified filters, excluding stale entries.
        A capability is considered stale if its 'last_seen' timestamp is older than:
    the configured 'staleness_threshold_seconds'.

    Args:
    capability_id_filter: Filter by exact capability ID.
            capability_name_filter: Filter by exact capability name.
            tags_filter: Filter by capabilities that include ALL specified tags.
            min_trust_score: Filter by capabilities from AIs with at least this trust score.:
    sort_by_trust: If True, sort results by trust score in descending order.

    Returns:
            A list of HSPCapabilityAdvertisementPayload objects matching the criteria.
    """
        # Tuples of (payload, trust_score) for potential sorting
    pre_results: List[Tuple[HSPCapabilityAdvertisementPayload, float]] =

    current_time = datetime.now(timezone.utc)

    logger.debug("Finding capabilities with filters: ID=%s, Name=%s, Tags=%s, MinTrust=%s, SortByTrust=%s",
                     capability_id_filter, capability_name_filter, tags_filter, min_trust_score, sort_by_trust)
    logger.debug("Current known_capabilities before filtering: %s", self.known_capabilities)

    with self.lock:
            # Iterate over a copy of values in case of concurrent modification (though less likely here)
            # No, iterate items to get capability_id for logging if needed.
            # capabilities_to_check = list(self.known_capabilities.values)
            # Iterate items to get capability_id for logging if needed.
    capabilities_to_iterate = list(self.known_capabilities.items)


            for capability_id, (payload, last_seen) in capabilities_to_iterate:



    logger.debug("Checking capability: %s, Last seen: %s", capability_id, last_seen.isoformat)
                # --- Staleness Check ---
                age_seconds = (current_time - last_seen).total_seconds
                logger.debug("Capability %s age: %.2fs, threshold: %ds", capability_id, age_seconds, self.staleness_threshold_seconds)
                if age_seconds > self.staleness_threshold_seconds:

    logger.debug("Skipping stale capability ID: %s (age: %.2fs > threshold: %ds)", capability_id, age_seconds, self.staleness_threshold_seconds)
                    continue

                # Apply capability_id_filter
                if capability_id_filter and capability_id != capability_id_filter:

    logger.debug("Skipping capability %s: ID filter mismatch (expected %s)", capability_id, capability_id_filter)
                    continue

                # Apply capability_name_filter with exact matching for test compatibility
    if capability_name_filter:

    payload_name = payload.get('name', '')
                    # Exact match only for test compatibility
    if payload_name != capability_name_filter:

    logger.debug("Skipping capability %s: Name filter mismatch (expected %s, got %s)", capability_id, capability_name_filter, payload_name)
                        continue

                # Apply tags_filter (must match ALL tags in filter)
                if tags_filter:

    capability_tags = payload.get('tags', )
                    if not capability_tags or not all(tag in capability_tags for tag in tags_filter)

    logger.debug("Skipping capability %s: Tags filter mismatch (expected all of %s, got %s)", capability_id, tags_filter, capability_tags)
                        continue

                advertiser_ai_id = payload.get('ai_id')
                if not advertiser_ai_id:

    logger.warning("Found capability with no advertiser_ai_id during find: %s. Skipping.", payload.get('capability_id'))
                    continue

                trust_score = self.trust_manager.get_trust_score(advertiser_ai_id)
                logger.debug("Capability %s trust score: %.2f (min_trust_score: %s)", capability_id, trust_score, min_trust_score)

                # Apply min_trust_score filter
                if min_trust_score is not None and trust_score < min_trust_score:

    logger.debug("Skipping capability %s: Trust score %.2f below min_trust_score %.2f", capability_id, trust_score, min_trust_score)
                    continue

                pre_results.append((payload, trust_score))

        # Sort if requested
    if sort_by_trust:

    pre_results.sort(key=lambda item: item[1], reverse=True) # Sort by trust_score descending

        # Extract just the payloads for the final list
    final_results = [payload for payload, _ in pre_results]:

    logger.info("Found %d capabilities matching criteria. ID_filter: %s, Name_filter: %s, Tags_filter: %s, Min_trust: %s",
                    len(final_results), capability_id_filter, capability_name_filter, tags_filter, min_trust_score)
    return final_results

    def get_capability_by_id(self, capability_id: str) -> Optional[HSPCapabilityAdvertisementPayload]:
    """
    Retrieves a specific capability by its ID.
        Returns None if the capability is not found or if it is considered stale
    (i.e., its 'last_seen' timestamp is older than 'staleness_threshold_seconds').

    Args:
    _ = capability_id (str) The unique ID of the capability to retrieve.

    Returns:
            Optional[HSPCapabilityAdvertisementPayload]: The capability payload if found and not stale,:
    otherwise None.
    """
    with self.lock:
    capability_entry = self.known_capabilities.get(capability_id)
    if capability_entry:

    payload, last_seen = capability_entry
                current_time = datetime.now(timezone.utc)
    age_seconds = (current_time - last_seen).total_seconds

                if age_seconds > self.staleness_threshold_seconds:


    logger.info( # INFO level as this might be directly requested and user should know it's stale
                        _ = "Capability ID '%s' from AI: %s found but is stale (age: %.2fs, threshold: %ds). Returning None.",
                        _ = capability_id, payload.get('ai_id'), age_seconds, self.staleness_threshold_seconds
                    )
                    return None

                logger.debug("Capability ID '%s' found and not stale. Last seen: %s", capability_id, last_seen.isoformat)
                return payload
            else:

                logger.debug("Capability ID '%s' not found in known capabilities.", capability_id)
                return None

    def get_all_capabilities(self) -> List[HSPCapabilityAdvertisementPayload]:
    """Returns a list of all known, non-stale capabilities."""
    return self._find_capabilities_sync

    async def get_all_capabilities_async(self) -> List[HSPCapabilityAdvertisementPayload]:
    """Async version of get_all_capabilities."""
    return await self.find_capabilities

    def is_capability_available(self, capability_id: str) -> bool:
    """
        Checks if a capability with the given ID is available (registered and not stale).:

    Args:
    _ = capability_id (str) The unique ID of the capability to check.

    Returns: bool True if the capability is available and not stale, False otherwise.
    """
    capability = self.get_capability_by_id(capability_id)
    return capability is not None

if __name__ == '__main__':
    # Basic test/example of instantiation (requires a mock TrustManager)
    class MockTrustManager(TrustManager)
        def __init__(self) -> None:
            super().__init__ # Call parent __init__ if it has one and it's needed
    logger.info("MockTrustManager initialized for SDM example.")
    def get_trust_score(self, ai_id: str, capability_name: Optional[str] = None) -> float:
            return 0.5 # Default mock score
        def update_trust_score(self, ai_id: str, adjustment: Optional[float] = None, new_absolute_score: Optional[float] = None, capability_name: Optional[str] = None) -> float:
            return 0.5 # Default mock score

    mock_tm = MockTrustManager
    sdm_instance = ServiceDiscoveryModule(trust_manager=mock_tm)
    logger.info(f"ServiceDiscoveryModule instance created: {sdm_instance}")
    logger.info(f"Known capabilities initially: {sdm_instance.known_capabilities}")

    # Example of how process_capability_advertisement might be called (method not yet implemented)
    sample_cap_payload = HSPCapabilityAdvertisementPayload(
    capability_id="test_cap_001",
    ai_id="did:hsp:test_advertiser_ai",
    agent_name="test_agent",
    name="Test Capability",
        description="A capability for testing.",:
    version="1.0",
    availability_status="online",
    # other fields as required by HSPCapabilityAdvertisementPayload
    )
    # sdm_instance.process_capability_advertisement(sample_cap_payload, "did:hsptest_advertiser_ai", ) # type ignore
    # logger.info(f"Known capabilities after hypothetical advertisement {sdm_instance.known_capabilities}")

    # Example of find_capabilities (method not yet implemented)
    # found_caps = sdm_instance.find_capabilities(capability_name_filter="Test Capability")
    # logger.info(f"Found capabilities {found_caps}")