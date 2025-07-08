# src/core_ai/service_discovery/service_discovery_module.py

import logging
import threading
from datetime import datetime, timezone
from typing import Dict, Optional, List, Tuple

from src.hsp.types import HSPCapabilityAdvertisementPayload, HSPMessageEnvelope
# Assuming TrustManager is correctly importable. If it's in the same directory, this might need adjustment
# based on how __init__.py in trust_manager_module's folder is set up.
# For now, direct import path as per typical project structure.
from src.core_ai.trust_manager.trust_manager_module import TrustManager

logger = logging.getLogger(__name__)

class ServiceDiscoveryModule:
    """
    Manages discovery and registry of capabilities advertised by other AIs
    on the HSP network, integrating with a TrustManager.
    This module is intended to handle HSPCapabilityAdvertisementPayload objects.
    """

    def __init__(self, trust_manager: TrustManager):
        """
        Initializes the ServiceDiscoveryModule for HSP capabilities.

        Args:
            trust_manager (TrustManager): An instance of the TrustManager to use for
                                          assessing the trustworthiness of capability advertisers.
        """
        self.trust_manager: TrustManager = trust_manager
        # Stores capability_id -> (HSPCapabilityAdvertisementPayload, last_seen_datetime_utc)
        self.known_capabilities: Dict[str, Tuple[HSPCapabilityAdvertisementPayload, datetime]] = {}
        self.lock = threading.RLock() # For thread-safe access to known_capabilities

        logger.info("HSP ServiceDiscoveryModule initialized.")

    def process_capability_advertisement(
        self,
        payload: HSPCapabilityAdvertisementPayload,
        sender_ai_id: str,  # The direct sender from the HSP envelope
        envelope: HSPMessageEnvelope # Full envelope for context if needed
    ) -> None:
        """
        Processes an incoming HSPCapabilityAdvertisementPayload.
        Stores or updates the capability in the registry with a 'last_seen' timestamp.

        Args:
            payload (HSPCapabilityAdvertisementPayload): The capability advertisement data.
            sender_ai_id (str): The AI ID of the direct sender of this message.
                                (May or may not be the same as payload.get('ai_id')).
            envelope (HSPMessageEnvelope): The full message envelope.
        """
        capability_id = payload.get('capability_id')
        advertiser_ai_id = payload.get('ai_id') # The AI actually offering the capability

        if not capability_id:
            logger.error("Received capability advertisement with no capability_id. Discarding. Payload: %s", payload)
            return

        if not advertiser_ai_id:
            logger.error("Received capability advertisement (ID: %s) with no 'ai_id' (advertiser AI ID) in payload. Discarding. Payload: %s", capability_id, payload)
            return

        # Optional: Could use sender_ai_id for additional trust checks or logging if different from advertiser_ai_id
        # For now, the primary identifier for trust is the advertiser_ai_id from the payload.

        with self.lock:
            current_time = datetime.now(timezone.utc)
            self.known_capabilities[capability_id] = (payload, current_time)
            logger.info(
                "Processed capability advertisement for ID: %s from AI: %s (Sender: %s). Last seen updated to: %s.",
                capability_id, advertiser_ai_id, sender_ai_id, current_time.isoformat()
            )

    def find_capabilities(
        self,
        capability_id_filter: Optional[str] = None,
        capability_name_filter: Optional[str] = None,
        tags_filter: Optional[List[str]] = None,
        min_trust_score: Optional[float] = None,
        sort_by_trust: bool = False
    ) -> List[HSPCapabilityAdvertisementPayload]:
        """
        Finds registered and non-stale (in future) capabilities based on specified filters.

        Args:
            capability_id_filter: Filter by exact capability ID.
            capability_name_filter: Filter by exact capability name.
            tags_filter: Filter by capabilities that include ALL specified tags.
            min_trust_score: Filter by capabilities from AIs with at least this trust score.
            sort_by_trust: If True, sort results by trust score in descending order.

        Returns:
            A list of HSPCapabilityAdvertisementPayload objects matching the criteria.
        """
        # Tuples of (payload, trust_score) for potential sorting
        pre_results: List[Tuple[HSPCapabilityAdvertisementPayload, float]] = []

        # TODO: In a future step, integrate staleness_threshold_seconds from __init__
        # current_time_for_staleness_check = datetime.now(timezone.utc)

        with self.lock:
            # Iterate over a copy of values in case of concurrent modification (though less likely here)
            capabilities_to_check = list(self.known_capabilities.values())

            for payload, last_seen in capabilities_to_check:
                # --- STALENESS CHECK (to be implemented based on original TODO) ---
                # if (current_time_for_staleness_check - last_seen).total_seconds() > self.staleness_threshold_seconds:
                #     logger.debug("Skipping stale capability ID: %s", payload.get('capability_id'))
                #     continue
                # For now, all capabilities are considered non-stale.

                # Apply capability_id_filter
                if capability_id_filter and payload.get('capability_id') != capability_id_filter:
                    continue

                # Apply capability_name_filter
                if capability_name_filter and payload.get('name') != capability_name_filter:
                    continue

                # Apply tags_filter (must match ALL tags in filter)
                if tags_filter:
                    capability_tags = payload.get('tags', [])
                    if not capability_tags or not all(tag in capability_tags for tag in tags_filter):
                        continue

                advertiser_ai_id = payload.get('ai_id')
                if not advertiser_ai_id: # Should not happen if process_capability_advertisement validates
                    logger.warning("Found capability with no advertiser_ai_id during find: %s. Skipping.", payload.get('capability_id'))
                    continue

                trust_score = self.trust_manager.get_trust_score(advertiser_ai_id)

                # Apply min_trust_score filter
                if min_trust_score is not None and trust_score < min_trust_score:
                    continue

                pre_results.append((payload, trust_score))

        # Sort if requested
        if sort_by_trust:
            pre_results.sort(key=lambda item: item[1], reverse=True) # Sort by trust_score descending

        # Extract just the payloads for the final list
        final_results = [payload for payload, _ in pre_results]

        logger.info("Found %d capabilities matching criteria. ID_filter: %s, Name_filter: %s, Tags_filter: %s, Min_trust: %s",
                    len(final_results), capability_id_filter, capability_name_filter, tags_filter, min_trust_score)
        return final_results

    def get_capability_by_id(self, capability_id: str) -> Optional[HSPCapabilityAdvertisementPayload]:
        """
        Retrieves a specific capability by its ID.
        (Does not yet check for staleness - this will be added later).

        Args:
            capability_id (str): The unique ID of the capability to retrieve.

        Returns:
            Optional[HSPCapabilityAdvertisementPayload]: The capability payload if found
                                                         (and not stale in the future),
                                                         otherwise None.
        """
        with self.lock:
            capability_entry = self.known_capabilities.get(capability_id)
            if capability_entry:
                payload, last_seen = capability_entry
                # TODO: Add staleness check here in the future, similar to find_capabilities
                # For now, if it exists, return it.
                logger.debug("Capability ID '%s' found. Last seen: %s", capability_id, last_seen.isoformat())
                return payload
            else:
                logger.debug("Capability ID '%s' not found in known capabilities.", capability_id)
                return None

if __name__ == '__main__':
    # Basic test/example of instantiation (requires a mock TrustManager)
    class MockTrustManager(TrustManager):
        def __init__(self):
            super().__init__() # Call parent __init__ if it has one and it's needed
            logger.info("MockTrustManager initialized for SDM example.")
        def get_trust_score(self, ai_id: str) -> float:
            return 0.5 # Default mock score
        def update_trust_score(self, ai_id: str, new_absolute_score: Optional[float] = None, change_reason: Optional[str] = None, interaction_quality: Optional[float] = None):
            pass

    mock_tm = MockTrustManager()
    sdm_instance = ServiceDiscoveryModule(trust_manager=mock_tm)
    logger.info(f"ServiceDiscoveryModule instance created: {sdm_instance}")
    logger.info(f"Known capabilities initially: {sdm_instance.known_capabilities}")

    # Example of how process_capability_advertisement might be called (method not yet implemented)
    sample_cap_payload = HSPCapabilityAdvertisementPayload(
        capability_id="test_cap_001",
        ai_id="did:hsp:test_advertiser_ai",
        name="Test Capability",
        description="A capability for testing.",
        version="1.0",
        availability_status="online",
        # other fields as required by HSPCapabilityAdvertisementPayload
    )
    # sdm_instance.process_capability_advertisement(sample_cap_payload, "did:hsp:test_advertiser_ai", {}) # type: ignore
    # logger.info(f"Known capabilities after hypothetical advertisement: {sdm_instance.known_capabilities}")

    # Example of find_capabilities (method not yet implemented)
    # found_caps = sdm_instance.find_capabilities(capability_name_filter="Test Capability")
    # logger.info(f"Found capabilities: {found_caps}")
