from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

# Assuming src is in PYTHONPATH for these imports
from hsp.types import HSPCapabilityAdvertisementPayload, HSPMessageEnvelope
# HSPConnector needed if this module subscribes directly, or it gets data from a higher level orchestrator
# from hsp.connector import HSPConnector


class ServiceDiscoveryModule:
    """
    Manages the discovery and registry of capabilities advertised by other AIs on the HSP network.
    """
    def __init__(self):
        # Stores capabilities by their unique capability_id
        # The value could be the full HSPCapabilityAdvertisementPayload
        self.known_capabilities: Dict[str, HSPCapabilityAdvertisementPayload] = {}
        self.last_seen: Dict[str, datetime] = {} # Tracks when a capability was last advertised/refreshed
        print("ServiceDiscoveryModule initialized.")

    def process_capability_advertisement(
        self,
        payload: HSPCapabilityAdvertisementPayload,
        source_ai_id: str, # The AI ID that advertised this capability
        hsp_envelope: HSPMessageEnvelope # Full envelope for context if needed
    ) -> None:
        """
        Processes an incoming capability advertisement.
        Stores or updates the capability in the local registry.
        """
        capability_id = payload.get("capability_id")
        if not capability_id:
            print("ServiceDiscoveryModule: Received capability advertisement without a capability_id. Skipping.")
            return

        # Ensure required fields are present for a valid advertisement (basic check)
        if not all(key in payload for key in ["ai_id", "name", "description", "version", "availability_status"]):
            print(f"ServiceDiscoveryModule: Received capability advertisement '{capability_id}' with missing required fields. Skipping.")
            return

        print(f"ServiceDiscoveryModule: Processing capability advertisement '{capability_id}' from AI '{source_ai_id}'.")

        # Store or update the capability
        # We might want to check versioning or if it's from the same source_ai_id as payload['ai_id']
        if payload.get("ai_id") != source_ai_id:
            print(f"ServiceDiscoveryModule: Warning - Capability '{capability_id}' ai_id '{payload.get('ai_id')}' "
                  f"differs from HSP sender_ai_id '{source_ai_id}'. Using payload's ai_id for storage key if matches capability_id structure.")

        # Use capability_id as the primary key
        self.known_capabilities[capability_id] = payload
        self.last_seen[capability_id] = datetime.now(timezone.utc)

        print(f"ServiceDiscoveryModule: Capability '{capability_id}' (Name: '{payload.get('name')}') from AI '{payload.get('ai_id')}' "
              f"added/updated. Total known capabilities: {len(self.known_capabilities)}")

    def find_capabilities(
        self,
        capability_name_filter: Optional[str] = None,
        capability_id_filter: Optional[str] = None,
        ai_id_filter: Optional[str] = None,
        tags_filter: Optional[List[str]] = None,
        min_availability: Optional[List[str]] = None # e.g., ["online", "degraded"]
    ) -> List[HSPCapabilityAdvertisementPayload]:
        """
        Finds capabilities based on various filter criteria.

        Args:
            capability_name_filter (str, optional): Filter by capability name (exact match, case-insensitive).
            capability_id_filter (str, optional): Filter by exact capability ID.
            ai_id_filter (str, optional): Filter by the AI ID offering the capability.
            tags_filter (List[str], optional): Filter by capabilities that have ALL specified tags.
            min_availability (List[str], optional): Filter by minimum availability status (e.g. if "online" is passed, only online capabilities are returned)
                                                    More sophisticated logic could handle ordered availability. For now, exact match in list.

        Returns:
            List[HSPCapabilityAdvertisementPayload]: A list of matching capability advertisements.
        """
        if min_availability is None:
            min_availability = ["online"] # Default to only finding 'online' capabilities

        results: List[HSPCapabilityAdvertisementPayload] = []
        for cap_id, cap_payload in self.known_capabilities.items():
            match = True # Assume it matches until a filter disqualifies it

            if capability_id_filter and cap_id != capability_id_filter:
                match = False

            if match and capability_name_filter and cap_payload.get("name", "").lower() != capability_name_filter.lower():
                match = False

            if match and ai_id_filter and cap_payload.get("ai_id") != ai_id_filter:
                match = False

            if match and tags_filter:
                cap_tags = cap_payload.get("tags", [])
                if not all(tag.lower() in [t.lower() for t in cap_tags] for tag in tags_filter):
                    match = False

            if match and min_availability:
                current_status = cap_payload.get("availability_status", "offline")
                if current_status not in min_availability: # Check if current status is in the list of acceptable statuses
                    match = False

            if match:
                results.append(cap_payload)

        print(f"ServiceDiscoveryModule: Found {len(results)} capabilities matching filters.")
        return results

    def get_capability_by_id(self, capability_id: str) -> Optional[HSPCapabilityAdvertisementPayload]:
        """
        Retrieves a specific capability by its ID.
        """
        return self.known_capabilities.get(capability_id)

    def remove_capability(self, capability_id: str) -> bool:
        """
        Removes a capability from the registry (e.g., if it becomes stale or explicitly unregistered).
        """
        if capability_id in self.known_capabilities:
            del self.known_capabilities[capability_id]
            if capability_id in self.last_seen:
                del self.last_seen[capability_id]
            print(f"ServiceDiscoveryModule: Capability '{capability_id}' removed.")
            return True
        print(f"ServiceDiscoveryModule: Capability '{capability_id}' not found for removal.")
        return False

    def get_all_capabilities(self) -> List[HSPCapabilityAdvertisementPayload]:
        """Returns all known capabilities."""
        return list(self.known_capabilities.values())

    # TODO: Add logic for staleness/expiration of capabilities based on self.last_seen

if __name__ == '__main__':
    print("--- ServiceDiscoveryModule Standalone Test ---")
    discovery_module = ServiceDiscoveryModule()

    # Mock HSP Envelope and Payload for testing process_capability_advertisement
    mock_sender_ai_id = "did:hsp:ai_advertiser_001"
    mock_capability_payload_1 = HSPCapabilityAdvertisementPayload(
        capability_id="translator_en_fr_v1.0",
        ai_id=mock_sender_ai_id, # Should match sender or be consistent
        name="English to French Translator",
        description="Translates text from English to French using advanced NMT.",
        version="1.0",
        input_schema_uri="hsp://schemas/text_input_v1",
        output_schema_uri="hsp://schemas/text_output_v1",
        availability_status="online",
        tags=["nlp", "translation", "french"]
    )
    mock_envelope_1 = HSPMessageEnvelope( # type: ignore # Some fields are optional
        message_id=str(uuid.uuid4()),
        sender_ai_id=mock_sender_ai_id,
        recipient_ai_id="hsp/capabilities/advertisements/all", # Example topic
        timestamp_sent=datetime.now(timezone.utc).isoformat(),
        message_type="HSP::CapabilityAdvertisement_v0.1",
        protocol_version="0.1",
        communication_pattern="publish",
        payload=mock_capability_payload_1
    )

    discovery_module.process_capability_advertisement(mock_capability_payload_1, mock_sender_ai_id, mock_envelope_1)

    mock_capability_payload_2 = HSPCapabilityAdvertisementPayload(
        capability_id="image_classifier_resnet_v0.9",
        ai_id="did:hsp:ai_image_processor_002",
        name="Image Classifier (ResNet)",
        description="Classifies images using a ResNet50 model.",
        version="0.9",
        input_schema_uri="hsp://schemas/image_input_v1", # Expects image URL or base64
        output_schema_uri="hsp://schemas/classification_output_v1", # Returns top N classes
        availability_status="online",
        tags=["cv", "image_classification", "resnet"]
    )
    discovery_module.process_capability_advertisement(mock_capability_payload_2, "did:hsp:ai_image_processor_002", None) # type: ignore

    print("\nFinding 'translator':")
    results = discovery_module.find_capabilities(capability_name_filter="English to French Translator")
    assert len(results) == 1
    assert results[0]["capability_id"] == "translator_en_fr_v1.0"
    for res in results: print(f"  - {res.get('name')} by {res.get('ai_id')}")

    print("\nFinding capabilities with tag 'cv':")
    results_cv = discovery_module.find_capabilities(tags_filter=["cv"])
    assert len(results_cv) == 1
    assert results_cv[0]["capability_id"] == "image_classifier_resnet_v0.9"
    for res in results_cv: print(f"  - {res.get('name')} (Tags: {res.get('tags')})")

    print("\nFinding capabilities with tag 'nlp' AND 'french':")
    results_nlp_french = discovery_module.find_capabilities(tags_filter=["nlp", "french"])
    assert len(results_nlp_french) == 1
    assert results_nlp_french[0]["capability_id"] == "translator_en_fr_v1.0"
    for res in results_nlp_french: print(f"  - {res.get('name')}")

    print("\nFinding non-existent capability:")
    results_none = discovery_module.find_capabilities(capability_name_filter="NonExistent")
    assert len(results_none) == 0
    print("  - No results, as expected.")

    print("\nGetting by ID:")
    cap_by_id = discovery_module.get_capability_by_id("translator_en_fr_v1.0")
    assert cap_by_id is not None
    assert cap_by_id.get("name") == "English to French Translator"
    print(f"  Got: {cap_by_id.get('name')}")

    print("\nAll capabilities:")
    all_caps = discovery_module.get_all_capabilities()
    assert len(all_caps) == 2
    for cap in all_caps: print(f"  - {cap.get('name')} (ID: {cap.get('capability_id')})")

    print("\nServiceDiscoveryModule standalone test finished.")
```
