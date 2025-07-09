import threading
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List, Any, TypedDict

from src.hsp.types import HSPCapabilityAdvertisementPayload, HSPMessageEnvelope
from src.core_ai.trust_manager.trust_manager_module import TrustManager # Assuming path

logger = logging.getLogger(__name__)

class StoredCapabilityInfo(TypedDict):
    payload: HSPCapabilityAdvertisementPayload
    sender_ai_id: str
    last_seen_timestamp: datetime
    message_id: str # From the HSP envelope

class ServiceDiscoveryModule:
    """
    Manages the discovery of capabilities advertised by other AIs over HSP.
    Integrates with TrustManager to filter and sort capabilities by trust.
    Handles staleness of capability advertisements.
    This module is intended to replace the previous generic service discovery.
    """

    def __init__(self,
                 trust_manager: TrustManager,
                 staleness_threshold_seconds: int = 3600 * 24,
                 pruning_interval_seconds: int = 60 * 10): # Default 10 minutes
        """
        Initializes the HSP ServiceDiscoveryModule.

        Args:
            trust_manager: An instance of the TrustManager.
            staleness_threshold_seconds: How long an advertisement is considered valid
                                         without being re-advertised (default: 24 hours).
            pruning_interval_seconds: How often to run the pruning mechanism for stale capabilities.
        """
        self.trust_manager: TrustManager = trust_manager
        self.staleness_threshold_seconds: int = staleness_threshold_seconds
        self._capabilities_store: Dict[str, StoredCapabilityInfo] = {}
        self._store_lock: threading.Lock = threading.Lock()
        self._pruning_interval_seconds: int = pruning_interval_seconds
        self._pruning_timer: Optional[threading.Timer] = None
        self._stop_pruning_event: threading.Event = threading.Event()

        self._start_pruning_timer()
        logger.info(f"HSP ServiceDiscoveryModule initialized. Staleness threshold: {self.staleness_threshold_seconds}s, Pruning interval: {self._pruning_interval_seconds}s.")

    def _start_pruning_timer(self) -> None:
        """Starts the recurring timer for pruning stale capabilities."""
        if not self._stop_pruning_event.is_set():
            self._pruning_timer = threading.Timer(self._pruning_interval_seconds, self._run_pruning_cycle)
            self._pruning_timer.daemon = True  # Allow program to exit even if timer is active
            self._pruning_timer.start()
            logger.info(f"Pruning timer started. Next check in {self._pruning_interval_seconds} seconds.")

    def _run_pruning_cycle(self) -> None:
        """Internal method called by the timer to execute pruning and reschedule."""
        logger.debug("Pruning cycle triggered.")
        self._prune_stale_capabilities()
        # Reschedule the timer for the next run, unless stop event is set
        if not self._stop_pruning_event.is_set():
            self._start_pruning_timer()
        else:
            logger.info("Pruning timer stop event detected. Not rescheduling.")

    def stop_pruning_timer(self) -> None:
        """Stops the active pruning timer."""
        logger.info("Attempting to stop pruning timer...")
        self._stop_pruning_event.set() # Signal the timer loop to stop
        if self._pruning_timer and self._pruning_timer.is_alive():
            self._pruning_timer.cancel() # Cancel the current wait
            logger.info("Pruning timer cancelled.")
        self._pruning_timer = None


    def process_capability_advertisement(
        self,
        capability_payload: HSPCapabilityAdvertisementPayload,
        sender_ai_id: str,
        full_envelope: HSPMessageEnvelope
    ) -> None:
        """
        Processes an incoming capability advertisement from the HSPConnector.
        Stores or updates the capability in the internal store.
        This method is expected to be called by the HSPConnector's callback.
        """
        if not capability_payload:
            logger.warning("Received empty capability_payload. Ignoring.")
            return

        capability_id = capability_payload.get('capability_id')
        advertised_ai_id = capability_payload.get('ai_id') # The AI ID stated *in the payload*
        name = capability_payload.get('name')
        description = capability_payload.get('description')
        version = capability_payload.get('version')
        availability_status = capability_payload.get('availability_status')

        if not all([capability_id, advertised_ai_id, name, description, version, availability_status]):
            logger.warning(f"Received capability advertisement from {sender_ai_id} with missing essential fields (capability_id, ai_id, name, description, version, or availability_status). Payload: {capability_payload}. Ignoring.")
            return

        if advertised_ai_id != sender_ai_id:
            logger.warning(f"Capability advertisement {capability_id} from sender '{sender_ai_id}' has mismatched 'ai_id' ('{advertised_ai_id}') in payload. Using sender_ai_id from envelope as the source of truth.")
            # We will use sender_ai_id from the envelope for trust purposes.

        current_time = datetime.now(timezone.utc)
        message_id = full_envelope.get('message_id', 'unknown_message_id')

        stored_info = StoredCapabilityInfo(
            payload=capability_payload,
            sender_ai_id=sender_ai_id, # Use sender_ai_id from envelope
            last_seen_timestamp=current_time,
            message_id=message_id
        )

        with self._store_lock:
            self._capabilities_store[capability_id] = stored_info

        logger.info(f"Processed capability advertisement: '{name}' (ID: {capability_id}, Version: {version}) from AI '{sender_ai_id}'. Availability: {availability_status}.")

    def _is_stale(self, stored_capability: StoredCapabilityInfo, current_time: datetime) -> bool:
        """Checks if a stored capability is stale."""
        if not stored_capability or not stored_capability.get('last_seen_timestamp'):
            return True # Treat as stale if malformed
        age = current_time - stored_capability['last_seen_timestamp']
        return age.total_seconds() > self.staleness_threshold_seconds

    def find_capabilities(
        self,
        capability_name_filter: Optional[str] = None,
        capability_id_filter: Optional[str] = None,
        tags_filter: Optional[List[str]] = None,
        min_trust_score: Optional[float] = None,
        sort_by_trust: bool = True,
        exclude_unavailable: bool = True
    ) -> List[HSPCapabilityAdvertisementPayload]:
        """
        Finds capabilities based on various filters and sorts them.

        Args:
            capability_name_filter: Filter by capability name (case-insensitive exact match).
            capability_id_filter: Filter by exact capability ID.
            tags_filter: List of tags; capability must have ALL specified tags.
            min_trust_score: Minimum trust score of the advertising AI.
            sort_by_trust: If True, sort results by trust score (descending).
            exclude_unavailable: If True (default), only include capabilities with 'online' status.

        Returns:
            A list of HSPCapabilityAdvertisementPayload objects that match the criteria.
        """
        with self._store_lock:
            # Create a snapshot of items to avoid issues if store is modified during iteration (though lock helps)
            # However, self.trust_manager.get_trust_score is an external call, so better to release lock for that.
            # Let's copy relevant data first.

            # Create a list of (StoredCapabilityInfo, advertiser_ai_id) to process outside the main lock for trust calls
            candidate_infos: List[StoredCapabilityInfo] = list(self._capabilities_store.values())

        # Now process candidate_infos outside the main store lock

        current_time = datetime.now(timezone.utc)
        results_with_scores: List[Tuple[HSPCapabilityAdvertisementPayload, float]] = []

        for stored_info in candidate_infos:
            if self._is_stale(stored_info, current_time):
                logger.debug(f"Capability ID {stored_info['payload'].get('capability_id')} is stale. Skipping.")
                continue

            payload = stored_info['payload']

            if exclude_unavailable and payload.get('availability_status') != 'online':
                logger.debug(f"Capability ID {payload.get('capability_id')} is not 'online' ({payload.get('availability_status')}). Skipping due to exclude_unavailable=True.")
                continue

            if capability_id_filter and payload.get('capability_id') != capability_id_filter:
                continue

            if capability_name_filter and (payload.get('name') is None or payload.get('name', '').lower() != capability_name_filter.lower()):
                continue

            if tags_filter:
                payload_tags = payload.get('tags', [])
                if not all(tag.lower() in (pt.lower() for pt in payload_tags) for tag in tags_filter):
                    continue

            advertiser_ai_id = stored_info['sender_ai_id']
            trust_score = self.trust_manager.get_trust_score(advertiser_ai_id)

            if min_trust_score is not None and trust_score < min_trust_score:
                continue

            results_with_scores.append((payload, trust_score))

        if sort_by_trust:
            results_with_scores.sort(key=lambda item: item[1], reverse=True)

        final_results = [item[0] for item in results_with_scores]
        logger.debug(f"find_capabilities query returned {len(final_results)} results.")
        return final_results

    def get_capability_by_id(self, capability_id: str, exclude_unavailable: bool = False) -> Optional[HSPCapabilityAdvertisementPayload]:
        """
        Retrieves a specific capability by its unique ID.

        Args:
            capability_id: The unique ID of the capability.
            exclude_unavailable: If True, returns None if the capability status is not 'online'. Default False.


        Returns:
            The HSPCapabilityAdvertisementPayload if found and not stale (and matches availability criteria),
            otherwise None.
        """
        with self._store_lock:
            stored_info = self._capabilities_store.get(capability_id)

        if not stored_info:
            logger.debug(f"Capability ID '{capability_id}' not found in store.")
            return None

        current_time = datetime.now(timezone.utc)
        if self._is_stale(stored_info, current_time):
            logger.info(f"Capability ID '{capability_id}' found but is stale. Not returning.")
            # Optionally remove from store here or have a separate pruning mechanism
            # with self._store_lock:
            #     if capability_id in self._capabilities_store and self._is_stale(self._capabilities_store[capability_id], current_time):
            #         del self._capabilities_store[capability_id]
            #         logger.info(f"Removed stale capability ID '{capability_id}' from store.")
            return None

        payload = stored_info['payload']
        if exclude_unavailable and payload.get('availability_status') != 'online':
            logger.debug(f"Capability ID {payload.get('capability_id')} is not 'online' ({payload.get('availability_status')}). Not returning due to exclude_unavailable=True.")
            return None

        logger.debug(f"Capability ID '{capability_id}' found and is valid.")
        return payload

    def get_all_capabilities(self, exclude_stale: bool = True, exclude_unavailable: bool = False) -> List[HSPCapabilityAdvertisementPayload]:
        """
        Returns all known capabilities, optionally filtering out stale or unavailable ones.
        This method is useful for inspection or for UIs that list all services.
        Note: Does not apply trust sorting by default here, but could be an option.
        """
        with self._store_lock:
            all_stored_infos: List[StoredCapabilityInfo] = list(self._capabilities_store.values())

        current_time = datetime.now(timezone.utc)
        results: List[HSPCapabilityAdvertisementPayload] = []

        for stored_info in all_stored_infos:
            if exclude_stale and self._is_stale(stored_info, current_time):
                continue

            payload = stored_info['payload']
            if exclude_unavailable and payload.get('availability_status') != 'online':
                continue

            results.append(payload)

        logger.debug(f"get_all_capabilities returned {len(results)} capabilities.")
        return results

    def _prune_stale_capabilities(self) -> None:
        """
        (Optional internal method for future use if background pruning is desired)
        Removes stale capabilities from the store.
        This method is now called periodically by the pruning timer.
        """
        with self._store_lock:
            current_time = datetime.now(timezone.utc)
            # Ensure items() is called on a copy if modification during iteration is a concern,
            # though lock should prevent concurrent modification issues from other threads.
            # For simplicity here, direct iteration with a lock is common.
            stale_ids = [
                cap_id for cap_id, stored_info in list(self._capabilities_store.items()) # Iterate over a copy
                if self._is_stale(stored_info, current_time)
            ]
            if stale_ids:
                logger.info(f"Found {len(stale_ids)} stale capabilities to prune.")
                for cap_id in stale_ids:
                    try:
                        del self._capabilities_store[cap_id]
                        logger.debug(f"Successfully pruned stale capability ID: {cap_id}")
                    except KeyError:
                        logger.warning(f"Attempted to prune capability ID {cap_id} but it was already removed (possibly by a concurrent operation, though unlikely with current locking).")
                logger.info(f"Finished pruning. Total {len(stale_ids)} stale capabilities removed.")
            else:
                logger.debug("No stale capabilities found to prune.")

# Example usage (for testing or direct instantiation if needed)
if __name__ == '__main__':
    # This example requires a TrustManager instance.
    # Mocking TrustManager for simple test.
    class MockTrustManager(TrustManager):
        def get_trust_score(self, ai_id: str) -> float:
            if ai_id == "did:hsp:trusted_ai":
                return 0.9
            elif ai_id == "did:hsp:untrusted_ai":
                return 0.1
            return 0.5 # Default

    mock_trust_manager = MockTrustManager()
    sdm = ServiceDiscoveryModule(trust_manager=mock_trust_manager, staleness_threshold_seconds=60) # Short staleness for test

    # Example Capability Advertisements
    cap_adv1_payload: HSPCapabilityAdvertisementPayload = {
        "capability_id": "translator_v1", "ai_id": "did:hsp:trusted_ai", "name": "Fast Translator",
        "description": "Translates text fast.", "version": "1.0", "availability_status": "online",
        "tags": ["translation", "nlp"]
    }
    cap_adv1_envelope: HSPMessageEnvelope = {
        "hsp_envelope_version": "0.1", "message_id": "msg1", "sender_ai_id": "did:hsp:trusted_ai",
        "recipient_ai_id": "hsp/capabilities/advertisements", "timestamp_sent": datetime.now(timezone.utc).isoformat(),
        "message_type": "HSP::CapabilityAdvertisement_v0.1", "protocol_version": "0.1.1",
        "communication_pattern": "publish", "payload": cap_adv1_payload
    } # type: ignore

    cap_adv2_payload: HSPCapabilityAdvertisementPayload = {
        "capability_id": "image_analyzer_v2", "ai_id": "did:hsp:untrusted_ai", "name": "Image Analyzer",
        "description": "Analyzes images.", "version": "2.0", "availability_status": "online",
        "tags": ["vision", "cv"]
    }
    cap_adv2_envelope: HSPMessageEnvelope = {
        "hsp_envelope_version": "0.1", "message_id": "msg2", "sender_ai_id": "did:hsp:untrusted_ai",
        "recipient_ai_id": "hsp/capabilities/advertisements", "timestamp_sent": datetime.now(timezone.utc).isoformat(),
        "message_type": "HSP::CapabilityAdvertisement_v0.1", "protocol_version": "0.1.1",
        "communication_pattern": "publish", "payload": cap_adv2_payload
    } # type: ignore

    cap_adv3_payload: HSPCapabilityAdvertisementPayload = {
        "capability_id": "offline_tool_v1", "ai_id": "did:hsp:trusted_ai", "name": "Offline Tool",
        "description": "A tool that is offline.", "version": "1.0", "availability_status": "offline",
        "tags": ["utility"]
    }
    cap_adv3_envelope: HSPMessageEnvelope = {
        "hsp_envelope_version": "0.1", "message_id": "msg3", "sender_ai_id": "did:hsp:trusted_ai",
        "recipient_ai_id": "hsp/capabilities/advertisements", "timestamp_sent": datetime.now(timezone.utc).isoformat(),
        "message_type": "HSP::CapabilityAdvertisement_v0.1", "protocol_version": "0.1.1",
        "communication_pattern": "publish", "payload": cap_adv3_payload
    } # type: ignore


    logger.info("--- Testing HSP ServiceDiscoveryModule ---")
    logging.basicConfig(level=logging.INFO) # Show info logs for this test

    sdm.process_capability_advertisement(cap_adv1_payload, cap_adv1_envelope['sender_ai_id'], cap_adv1_envelope)
    sdm.process_capability_advertisement(cap_adv2_payload, cap_adv2_envelope['sender_ai_id'], cap_adv2_envelope)
    sdm.process_capability_advertisement(cap_adv3_payload, cap_adv3_envelope['sender_ai_id'], cap_adv3_envelope)

    logger.info("\n--- Find all online capabilities (sorted by trust):")
    all_online_caps = sdm.find_capabilities(sort_by_trust=True, exclude_unavailable=True)
    for cap in all_online_caps: logger.info(f"  Found: {cap.get('name')} from {cap.get('ai_id')}")
    assert len(all_online_caps) == 2
    assert all_online_caps[0]['capability_id'] == 'translator_v1' # Trusted AI first

    logger.info("\n--- Find 'Fast Translator':")
    translator_caps = sdm.find_capabilities(capability_name_filter="Fast Translator")
    for cap in translator_caps: logger.info(f"  Found: {cap.get('name')}")
    assert len(translator_caps) == 1

    logger.info("\n--- Find capabilities with tag 'vision':")
    vision_caps = sdm.find_capabilities(tags_filter=["vision"])
    for cap in vision_caps: logger.info(f"  Found: {cap.get('name')}")
    assert len(vision_caps) == 1
    assert vision_caps[0]['capability_id'] == 'image_analyzer_v2'

    logger.info("\n--- Find capabilities with min_trust_score 0.6 (sorted):")
    trusted_caps_only = sdm.find_capabilities(min_trust_score=0.6, sort_by_trust=True)
    for cap in trusted_caps_only: logger.info(f"  Found: {cap.get('name')} from {cap.get('ai_id')}")
    assert len(trusted_caps_only) == 1 # Only translator_v1 from trusted_ai (offline_tool is also from trusted_ai but find_capabilities excludes unavailable by default)

    logger.info("\n--- Get offline_tool_v1 by ID (exclude_unavailable=False):")
    offline_tool = sdm.get_capability_by_id("offline_tool_v1", exclude_unavailable=False)
    assert offline_tool is not None
    assert offline_tool['availability_status'] == 'offline' # type: ignore
    logger.info(f"  Found: {offline_tool.get('name')} with status {offline_tool.get('availability_status')}") # type: ignore

    logger.info("\n--- Get offline_tool_v1 by ID (exclude_unavailable=True, default):")
    offline_tool_excluded = sdm.get_capability_by_id("offline_tool_v1", exclude_unavailable=True)
    assert offline_tool_excluded is None
    logger.info(f"  Result when excluding unavailable: {offline_tool_excluded}")

    logger.info("\n--- Testing staleness (waiting for >60s for translator_v1 to be stale):")
    # This part of test is hard to automate reliably in short time without actual time.sleep
    # For a real unit test, time would be mocked.
    # Manually, one would wait here. We'll assume it's stale for a conceptual check.
    # To simulate staleness for 'translator_v1' for the test:
    with sdm._store_lock: # Simulate time passing for one entry
        if "translator_v1" in sdm._capabilities_store:
            sdm._capabilities_store["translator_v1"]["last_seen_timestamp"] -= timedelta(seconds=sdm.staleness_threshold_seconds + 5)
            logger.info(f"Artificially aged 'translator_v1'. Original last_seen: {sdm._capabilities_store['translator_v1']['last_seen_timestamp']}")

    stale_translator = sdm.get_capability_by_id("translator_v1")
    if stale_translator is None:
        logger.info("  'translator_v1' is now considered stale and was not returned by get_capability_by_id, as expected.")
    else:
        logger.warning("  'translator_v1' was unexpectedly returned, staleness check might need review.")
    assert stale_translator is None

    all_caps_after_stale = sdm.find_capabilities(sort_by_trust=False, exclude_unavailable=False) # find all, don't sort by trust
    logger.info(f"\n--- All capabilities after some aging (excluding stale by default in find_capabilities):")
    active_caps = sdm.find_capabilities(exclude_unavailable=False) # Default exclude_stale=True
    for cap in active_caps: logger.info(f"  Active: {cap.get('name')}")
    assert len(active_caps) == 2 # image_analyzer_v2, offline_tool_v1 should remain
    assert not any(c['capability_id'] == 'translator_v1' for c in active_caps)

    logger.info("\n--- Test Complete: HSP ServiceDiscoveryModule ---")
