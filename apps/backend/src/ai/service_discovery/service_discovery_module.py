import logging
import asyncio
import threading
from datetime import datetime, timezone
from typing import Dict, Optional, List, Tuple, Any

from core.hsp.payloads import (
    HSPCapabilityAdvertisementPayload,
    HSPMessageEnvelope
)
from ai.trust.trust_manager_module import TrustManager

logger = logging.getLogger(__name__)

class ServiceDiscoveryModule:
    """
    Manages discovery and registry of capabilities advertised by other AIs
    on the HSP network, integrating with a TrustManager.
    """
    DEFAULT_STALENESS_THRESHOLD_SECONDS = 600  # 10 minutes

    def __init__(self, trust_manager: TrustManager, staleness_threshold_seconds: Optional[int] = None) -> None:
        """
        Initializes the ServiceDiscoveryModule for HSP capabilities.
        """
        self.trust_manager = trust_manager
        # Stores capability_id -> (HSPCapabilityAdvertisementPayload, last_seen_datetime_utc)
        self.known_capabilities: Dict[str, Tuple[HSPCapabilityAdvertisementPayload, datetime]] = {}
        self.lock = threading.RLock()
        self.staleness_threshold_seconds = staleness_threshold_seconds or self.DEFAULT_STALENESS_THRESHOLD_SECONDS
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        logger.info(f"HSP ServiceDiscoveryModule initialized. Staleness threshold: {self.staleness_threshold_seconds} seconds.")

    def start_cleanup_task(self, cleanup_interval_seconds: int = 60):
        """Starts the periodic cleanup task in a background thread."""
        if self._cleanup_thread is None:
            self._stop_event.clear()
            self._cleanup_thread = threading.Thread(
                target=self._periodic_cleanup,
                args=(cleanup_interval_seconds,),
                daemon=True
            )
            self._cleanup_thread.start()
            logger.info(f"ServiceDiscoveryModule cleanup task started with interval {cleanup_interval_seconds}s.")

    def stop_cleanup_task(self):
        """Stops the periodic cleanup task."""
        if self._cleanup_thread is not None:
            self._stop_event.set()
            self._cleanup_thread.join(timeout=5)
            self._cleanup_thread = None
            logger.info("ServiceDiscoveryModule cleanup task stopped.")

    def _periodic_cleanup(self, cleanup_interval_seconds: int):
        """The target function for the cleanup thread."""
        while not self._stop_event.is_set():
            self.remove_stale_capabilities()
            self._stop_event.wait(cleanup_interval_seconds)

    def remove_stale_capabilities(self):
        """Removes capabilities that have exceeded the staleness threshold."""
        with self.lock:
            current_time = datetime.now(timezone.utc)
            stale_keys = []
            for key, (_, last_seen) in self.known_capabilities.items():
                if (current_time - last_seen).total_seconds() > self.staleness_threshold_seconds:
                    stale_keys.append(key)
            
            for key in stale_keys:
                del self.known_capabilities[key]
                logger.info(f"Removed stale capability: {key}")

    def process_capability_advertisement(self, payload: HSPCapabilityAdvertisementPayload, 
                                       sender_ai_id: str, envelope: HSPMessageEnvelope) -> None:
        """
        Processes an incoming HSPCapabilityAdvertisementPayload.
        """
        capability_id = payload.get('capability_id')
        advertiser_ai_id = payload.get('ai_id')

        if not capability_id:
            logger.error(f"Received capability advertisement with no capability_id. Payload: {payload}")
            return

        if not advertiser_ai_id:
            logger.error(f"Received capability advertisement (ID: {capability_id}) with no 'ai_id'. Payload: {payload}")
            return

        with self.lock:
            current_time = datetime.now(timezone.utc)
            self.known_capabilities[capability_id] = (payload, current_time)
            logger.info(f"Processed capability advertisement for ID: {capability_id} from AI: {advertiser_ai_id}")

    async def find_capabilities(self, capability_id_filter: Optional[str] = None,
                               capability_name_filter: Optional[str] = None,
                               tags_filter: Optional[List[str]] = None,
                               min_trust_score: Optional[float] = None,
                               sort_by_trust: bool = False) -> List[HSPCapabilityAdvertisementPayload]:
        """
        Finds registered capabilities based on specified filters, excluding stale entries.
        """
        return self._find_capabilities_sync(
            capability_id_filter=capability_id_filter,
            capability_name_filter=capability_name_filter,
            tags_filter=tags_filter,
            min_trust_score=min_trust_score,
            sort_by_trust=sort_by_trust
        )

    def _find_capabilities_sync(self, capability_id_filter: Optional[str] = None,
                               capability_name_filter: Optional[str] = None,
                               tags_filter: Optional[List[str]] = None,
                               min_trust_score: Optional[float] = None,
                               sort_by_trust: bool = False) -> List[HSPCapabilityAdvertisementPayload]:
        """
        Synchronous version of find_capabilities.
        """
        pre_results: List[Tuple[HSPCapabilityAdvertisementPayload, float]] = []
        current_time = datetime.now(timezone.utc)

        with self.lock:
            capabilities_to_iterate = list(self.known_capabilities.items())

            for capability_id, (payload, last_seen) in capabilities_to_iterate:
                # Staleness check
                if (current_time - last_seen).total_seconds() > self.staleness_threshold_seconds:
                    continue

                # Apply filters
                if capability_id_filter and capability_id != capability_id_filter:
                    continue

                if capability_name_filter and payload.get('name') != capability_name_filter:
                    continue

                if tags_filter:
                    capability_tags = payload.get('tags', [])
                    if not all(tag in capability_tags for tag in tags_filter):
                        continue

                advertiser_ai_id = payload.get('ai_id')
                if not advertiser_ai_id:
                    continue

                trust_score = self.trust_manager.get_trust_score(advertiser_ai_id)
                if min_trust_score is not None and trust_score < min_trust_score:
                    continue

                pre_results.append((payload, trust_score))

        if sort_by_trust:
            pre_results.sort(key=lambda item: item[1], reverse=True)

        return [payload for payload, _ in pre_results]

    def get_capability_by_id(self, capability_id: str) -> Optional[HSPCapabilityAdvertisementPayload]:
        """Retrieves a specific capability by its ID if not stale."""
        with self.lock:
            capability_entry = self.known_capabilities.get(capability_id)
            if capability_entry:
                payload, last_seen = capability_entry
                if (datetime.now(timezone.utc) - last_seen).total_seconds() > self.staleness_threshold_seconds:
                    return None
                return payload
            return None

    def get_all_capabilities(self) -> List[HSPCapabilityAdvertisementPayload]:
        """Returns a list of all known, non-stale capabilities."""
        return self._find_capabilities_sync()

    async def get_all_capabilities_async(self) -> List[HSPCapabilityAdvertisementPayload]:
        """Async version of get_all_capabilities."""
        return self.get_all_capabilities()

    def is_capability_available(self, capability_id: str) -> bool:
        """Checks if a capability is available."""
        return self.get_capability_by_id(capability_id) is not None