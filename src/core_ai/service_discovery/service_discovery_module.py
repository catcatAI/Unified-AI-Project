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
        # print(f"DEBUG SDM: _start_pruning_timer called. Stop event is set: {self._stop_pruning_event.is_set()}") # DEBUG REMOVED
        if not self._stop_pruning_event.is_set():
            self._pruning_timer = threading.Timer(self._pruning_interval_seconds, self._run_pruning_cycle)
            self._pruning_timer.daemon = True  # Allow program to exit even if timer is active
            self._pruning_timer.start()
            logger.info(f"Pruning timer started. Next check in {self._pruning_interval_seconds} seconds.")
        # else: # DEBUG REMOVED
            # print(f"DEBUG SDM: _start_pruning_timer NOT starting new timer because stop event is set.") # DEBUG REMOVED


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
        if not capability_payload: # Catches None and also {} because empty dict is falsy
            logger.warning("Received empty capability_payload. Ignoring.")
            return

        capability_id = capability_payload.get('capability_id')
        advertised_ai_id = capability_payload.get('ai_id')
        name = capability_payload.get('name')
        description = capability_payload.get('description')
        version = capability_payload.get('version')
        availability_status = capability_payload.get('availability_status')

        if not all([capability_id, advertised_ai_id, name, description, version, availability_status]):
            logger.warning(f"Received capability advertisement from {sender_ai_id} with missing essential fields (capability_id, ai_id, name, description, version, or availability_status). Payload: {capability_payload}. Ignoring.")
            return

        if advertised_ai_id != sender_ai_id:
            logger.warning(f"Capability advertisement {capability_id} from sender '{sender_ai_id}' has mismatched 'ai_id' ('{advertised_ai_id}') in payload. Using sender_ai_id from envelope as the source of truth.")

        current_time = datetime.now(timezone.utc)
        message_id = full_envelope.get('message_id', 'unknown_message_id')

        stored_info = StoredCapabilityInfo(
            payload=capability_payload,
            sender_ai_id=sender_ai_id,
            last_seen_timestamp=current_time,
            message_id=message_id
        )

        with self._store_lock:
            self._capabilities_store[capability_id] = stored_info

        logger.info(f"Processed capability advertisement: '{name}' (ID: {capability_id}, Version: {version}) from AI '{sender_ai_id}'. Availability: {availability_status}.")

    def _is_stale(self, stored_capability: StoredCapabilityInfo, current_time: datetime) -> bool:
        """Checks if a stored capability is stale."""
        if not stored_capability or not stored_capability.get('last_seen_timestamp'):
            return True
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
        """
        with self._store_lock:
            candidate_infos: List[StoredCapabilityInfo] = list(self._capabilities_store.values())

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
        """
        with self._store_lock:
            stored_info = self._capabilities_store.get(capability_id)

        if not stored_info:
            logger.debug(f"Capability ID '{capability_id}' not found in store.")
            return None

        current_time = datetime.now(timezone.utc)
        if self._is_stale(stored_info, current_time):
            logger.info(f"Capability ID '{capability_id}' found but is stale. Not returning.")
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
        Removes stale capabilities from the store.
        This method is now called periodically by the pruning timer.
        """
        with self._store_lock:
            current_time = datetime.now(timezone.utc)
            stale_ids = [
                cap_id for cap_id, stored_info in list(self._capabilities_store.items())
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

if __name__ == '__main__':
    class MockTrustManager(TrustManager):
        def get_trust_score(self, ai_id: str) -> float:
            if ai_id == "did:hsp:trusted_ai": return 0.9
            elif ai_id == "did:hsp:untrusted_ai": return 0.1
            return 0.5

    mock_trust_manager = MockTrustManager()
    sdm = ServiceDiscoveryModule(trust_manager=mock_trust_manager, staleness_threshold_seconds=60, pruning_interval_seconds=30)

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

    logging.basicConfig(level=logging.INFO)
    logger.info("--- Testing HSP ServiceDiscoveryModule with Pruning ---")
    sdm.process_capability_advertisement(cap_adv1_payload, cap_adv1_envelope['sender_ai_id'], cap_adv1_envelope)
    logger.info(f"Initial capabilities: {len(sdm.get_all_capabilities(exclude_stale=False))}")

    try:
        logger.info("Waiting for pruning cycles (e.g., >60s for staleness, pruning every 30s)...")
        # time.sleep(70) # Example: wait for it to become stale and pruned
        # logger.info(f"Capabilities after waiting: {len(sdm.get_all_capabilities(exclude_stale=False))}")
        # Add assertions here based on expected pruning
        # This manual test part needs actual waiting or more sophisticated timer control in tests.
        print("Example __main__ finished. Timer thread will exit if daemon=True.")
    finally:
        sdm.stop_pruning_timer() # Important to stop the timer
        logger.info("Pruning timer stopped by __main__.")
