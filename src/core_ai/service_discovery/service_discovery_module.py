# src/core_ai/service_discovery/service_discovery_module.py

import json
import time
import threading
from typing import Dict, Any, Optional, Callable, List, Tuple
from enum import Enum
import uuid
import random # For jitter

# Assuming common_types.py is in a reachable path like 'shared.types'
# from shared.types.common_types import ServiceStatus, ServiceAdvertisement, ServiceQuery, ServiceInstanceHealth
# For now, using placeholder definitions if not found, to allow isolated development.
try:
    from src.shared.types.common_types import ServiceStatus, ServiceAdvertisement, ServiceQuery, ServiceInstanceHealth, ServiceType
except ImportError:
    from typing import TypedDict # Import TypedDict here for the fallback definitions
    print("ServiceDiscoveryModule: common_types not found, using placeholders.")
    class ServiceStatus(Enum):
        UNKNOWN = 0
        STARTING = 1
        HEALTHY = 2
        UNHEALTHY = 3
        STOPPING = 4
        STOPPED = 5
        DEGRADED = 6

    class ServiceType(Enum):
        UNKNOWN = "unknown"
        CORE_AI_COMPONENT = "core_ai_component"
        EXTERNAL_API = "external_api"
        DATA_STORE = "data_store"
        INTERNAL_TOOL = "internal_tool"
        # Add more as needed

    class ServiceAdvertisement(TypedDict): # Changed to TypedDict for consistency
        service_id: str
        service_name: str
        service_type: ServiceType # Using enum
        service_version: str
        endpoint_url: Optional[str] # e.g., http://localhost:8000/api
        metadata: Dict[str, Any] # Custom metadata (capabilities, load, etc.)
        status: ServiceStatus # Current status
        last_seen_timestamp: float # Unix timestamp
        ttl: int # Time-to-live in seconds for this advertisement

    class ServiceQuery(TypedDict, total=False): # Changed to TypedDict for consistency
        service_type: Optional[ServiceType] # Using enum
        service_name: Optional[str]
        min_version: Optional[str]
        required_capabilities: Optional[List[str]] # e.g., ["text_to_speech", "sentiment_analysis"]
        status_filter: Optional[List[ServiceStatus]] # e.g., [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]

    class ServiceInstanceHealth(TypedDict): # Changed to TypedDict for consistency
        service_id: str
        instance_id: str # If multiple instances of a service exist
        status: ServiceStatus
        last_heartbeat: float
        metrics: Optional[Dict[str, Any]] # e.g., CPU load, memory usage, qps


class ServiceDiscoveryModule:
    """
    Manages service registration, discovery, and basic health checking (via TTL).
    This is a conceptual, in-memory implementation. A real-world scenario might use
    Consul, etcd, Zookeeper, or a cloud provider's service discovery mechanism.
    """

    def __init__(self, ai_id: str, operational_config: Optional[Dict[str, Any]] = None):
        self.ai_id = ai_id
        self.config = operational_config or {}
        self.registry: Dict[str, ServiceAdvertisement] = {} # service_id -> ServiceAdvertisement
        self.lock = threading.RLock() # Reentrant lock for registry access

        # Configuration for health checks and cleanup
        self.default_ttl = self.config.get("service_discovery_default_ttl_seconds", 300) # 5 minutes
        self.cleanup_interval = self.config.get("service_discovery_cleanup_interval_seconds", 60) # 1 minute
        self.health_check_jitter_max = self.config.get("service_discovery_health_check_jitter_max_seconds", 5)

        self._stop_event = threading.Event()
        self._cleanup_thread = threading.Thread(target=self._periodic_cleanup, daemon=True)
        self._cleanup_thread.start()
        print(f"ServiceDiscoveryModule initialized for AI ID '{self.ai_id}'. Cleanup interval: {self.cleanup_interval}s, Default TTL: {self.default_ttl}s.")


    def register_service(self,
                         service_name: str,
                         service_type: ServiceType,
                         service_version: str,
                         endpoint_url: Optional[str] = None,
                         metadata: Optional[Dict[str, Any]] = None,
                         initial_status: ServiceStatus = ServiceStatus.STARTING,
                         ttl_seconds: Optional[int] = None,
                         service_id_override: Optional[str] = None
                        ) -> str:
        """
        Registers a new service or updates an existing one.
        A unique service_id is generated if not provided.
        """
        with self.lock:
            service_id = service_id_override if service_id_override else f"{service_name}_{uuid.uuid4().hex[:8]}"

            if service_id in self.registry:
                print(f"ServiceDiscovery: Updating existing service '{service_id}' ({service_name}).")
            else:
                print(f"ServiceDiscovery: Registering new service '{service_id}' ({service_name}).")

            advertisement = ServiceAdvertisement(
                service_id=service_id,
                service_name=service_name,
                service_type=service_type,
                service_version=service_version,
                endpoint_url=endpoint_url,
                metadata=metadata or {},
                status=initial_status,
                last_seen_timestamp=time.time(),
                ttl=ttl_seconds if ttl_seconds is not None else self.default_ttl
            )
            self.registry[service_id] = advertisement
            print(f"  Service '{service_id}' registered/updated. Type: {service_type.value}, Status: {initial_status.name}, Endpoint: {endpoint_url}, TTL: {advertisement['ttl']}s")
            return service_id

    def deregister_service(self, service_id: str) -> bool:
        """Removes a service from the registry."""
        with self.lock:
            if service_id in self.registry:
                del self.registry[service_id]
                print(f"ServiceDiscovery: Service '{service_id}' deregistered.")
                return True
            print(f"ServiceDiscovery: Service '{service_id}' not found for deregistration.")
            return False

    def update_service_status(self, service_id: str, new_status: ServiceStatus, metadata_update: Optional[Dict[str, Any]] = None) -> bool:
        """Updates the status and optionally metadata of a registered service, refreshing its TTL."""
        with self.lock:
            if service_id in self.registry:
                advertisement = self.registry[service_id]
                advertisement['status'] = new_status
                advertisement['last_seen_timestamp'] = time.time() # Refresh timestamp (heartbeat)
                if metadata_update:
                    advertisement['metadata'].update(metadata_update)

                # No need to re-assign self.registry[service_id] = advertisement if TypedDict is mutable
                print(f"ServiceDiscovery: Updated status for service '{service_id}' to {new_status.name}. Metadata updated: {bool(metadata_update)}.")
                return True
            print(f"ServiceDiscovery: Service '{service_id}' not found for status update.")
            return False

    def heartbeat_service(self, service_id: str) -> bool:
        """Refreshes the last_seen_timestamp for a service, keeping it alive."""
        return self.update_service_status(service_id, self.registry[service_id]['status'] if service_id in self.registry else ServiceStatus.UNKNOWN)


    def discover_services(self, query: ServiceQuery) -> List[ServiceAdvertisement]:
        """
        Finds services based on a query.
        Considers service status (e.g., only HEALTHY or DEGRADED) and TTL.
        """
        with self.lock:
            current_time = time.time()
            results: List[ServiceAdvertisement] = []

            for ad in list(self.registry.values()): # Iterate over a copy in case of modification during cleanup
                if current_time > (ad['last_seen_timestamp'] + ad['ttl']):
                    continue

                match = True
                if query.get('service_type') and ad['service_type'] != query['service_type']:
                    match = False
                if query.get('service_name') and ad['service_name'] != query['service_name']:
                    match = False

                if query.get('min_version') and ad['service_version'] < query['min_version']:
                    match = False

                if query.get('required_capabilities'):
                    service_caps = ad['metadata'].get("capabilities", [])
                    if not all(cap in service_caps for cap in query['required_capabilities']):
                        match = False

                if query.get('status_filter') and ad['status'] not in query['status_filter']:
                    match = False

                if match:
                    results.append(ad)

            print(f"ServiceDiscovery: Discovery query found {len(results)} matching service(s).")
            return results

    def get_service_details(self, service_id: str) -> Optional[ServiceAdvertisement]:
        """Retrieves the details of a specific service if it's alive."""
        with self.lock:
            ad = self.registry.get(service_id)
            if ad:
                current_time = time.time()
                if current_time <= (ad['last_seen_timestamp'] + ad['ttl']):
                    return ad
                else:
                    print(f"ServiceDiscovery: Service '{service_id}' found but TTL expired. Considered unavailable.")
            return None

    def _remove_expired_services(self):
        """Internal method to remove services whose TTL has expired."""
        with self.lock:
            current_time = time.time()
            expired_ids = [
                sid for sid, ad in self.registry.items()
                if current_time > (ad['last_seen_timestamp'] + ad['ttl'])
            ]
            for sid in expired_ids:
                print(f"ServiceDiscovery: TTL expired for service '{self.registry[sid]['service_name']}' (ID: {sid}). Removing from registry.")
                del self.registry[sid]
            if expired_ids:
                 print(f"ServiceDiscovery: Removed {len(expired_ids)} expired service(s).")


    def _periodic_cleanup(self):
        """Runs periodically to remove expired services."""
        print("ServiceDiscovery: Periodic cleanup thread started.")
        while not self._stop_event.is_set():
            try:
                jitter = random.uniform(0, self.health_check_jitter_max)
                actual_interval = self.cleanup_interval + jitter

                wait_chunk = 1.0
                waited_time = 0.0
                while waited_time < actual_interval and not self._stop_event.is_set():
                    remaining_wait = min(wait_chunk, actual_interval - waited_time)
                    self._stop_event.wait(timeout=remaining_wait)
                    waited_time += remaining_wait

                if self._stop_event.is_set():
                    break
                self._remove_expired_services()

            except Exception as e:
                print(f"ServiceDiscovery: Error in periodic cleanup thread: {e}")
                self._stop_event.wait(timeout=self.cleanup_interval * 2)

        print("ServiceDiscovery: Periodic cleanup thread stopped.")

    def stop(self):
        """Stops the periodic cleanup thread."""
        print("ServiceDiscovery: Stopping periodic cleanup thread...")
        self._stop_event.set()
        if self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=self.cleanup_interval + 5)
        if self._cleanup_thread.is_alive():
            print("ServiceDiscovery: Cleanup thread did not terminate cleanly.")


if __name__ == "__main__":
    print("--- ServiceDiscoveryModule Example ---")
    # Need to import TypedDict for this example if not globally available
    from typing import TypedDict

    discovery_module = ServiceDiscoveryModule(ai_id="test_ai_host_for_sdm")

    tts_service_id = discovery_module.register_service(
        service_name="TextToSpeechService",
        service_type=ServiceType.CORE_AI_COMPONENT,
        service_version="1.2.0",
        endpoint_url="http://localhost:8080/tts",
        metadata={"language_support": ["en-US", "es-ES"], "voice_quality": "high"},
        initial_status=ServiceStatus.HEALTHY,
        ttl_seconds=60
    )
    print(f"Registered TTS Service ID: {tts_service_id}")

    ner_service_id = discovery_module.register_service(
        service_name="NamedEntityRecognition",
        service_type=ServiceType.CORE_AI_COMPONENT,
        service_version="0.9.5",
        endpoint_url="grpc://ner-service:50051",
        metadata={"model_type": "transformer_large", "entity_types": ["PER", "ORG", "LOC", "DATE"]},
        initial_status=ServiceStatus.HEALTHY,
        ttl_seconds=120
    )
    print(f"Registered NER Service ID: {ner_service_id}")

    db_service_id = discovery_module.register_service(
        service_name="KnowledgeGraphDB",
        service_type=ServiceType.DATA_STORE,
        service_version="2.0.1",
        initial_status=ServiceStatus.STARTING,
        metadata={"storage_type": "graph"}
    )

    print("\n--- Discovering AI Modules ---")
    ai_module_query = ServiceQuery(service_type=ServiceType.CORE_AI_COMPONENT, status_filter=[ServiceStatus.HEALTHY])
    healthy_ai_modules = discovery_module.discover_services(ai_module_query)
    for ad in healthy_ai_modules:
        print(f"  Found Healthy AI Module: {ad['service_name']} (ID: {ad['service_id']}) at {ad['endpoint_url']}")
        print(f"    Metadata: {ad['metadata']}")

    print("\n--- Discovering specific service by name ---")
    tts_query = ServiceQuery(service_name="TextToSpeechService")
    tts_services = discovery_module.discover_services(tts_query)
    if tts_services:
        print(f"  TTS Service Details: {tts_services[0]}")
    else:
        print("  TTS Service not found (or not healthy if status filter was applied).")

    print(f"\n--- Updating status for {db_service_id} to HEALTHY ---")
    discovery_module.update_service_status(db_service_id, ServiceStatus.HEALTHY, {"message": "Database fully initialized."})
    db_details = discovery_module.get_service_details(db_service_id)
    if db_details:
        print(f"  DB Service now: Status={db_details['status'].name}, Meta={db_details['metadata']}")

    print(f"\n--- Simulating time passing (e.g., {tts_services[0]['ttl'] + 10 if tts_services else 70} seconds) for TTS service '{tts_service_id}' to expire ---")

    print("Manually triggering cleanup for demo purposes...")
    if tts_services:
        with discovery_module.lock:
            if tts_service_id in discovery_module.registry:
                 discovery_module.registry[tts_service_id]['last_seen_timestamp'] = time.time() - (discovery_module.registry[tts_service_id]['ttl'] + 10)
        discovery_module._remove_expired_services()

    print("\n--- Discovering TTS service again (should be expired if TTL was short and cleanup ran) ---")
    tts_services_after_expiry = discovery_module.discover_services(tts_query)
    if tts_services_after_expiry:
        print(f"  TTS Service still found (unexpected for short TTL test): {tts_services_after_expiry[0]['service_name']}")
    else:
        print("  TTS Service not found (as expected after TTL expiry and cleanup).")

    discovery_module.stop()
    print("\n--- ServiceDiscoveryModule Example Finished ---")
# ``` # This was the offending line, now removed.
