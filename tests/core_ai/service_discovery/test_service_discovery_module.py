import unittest
from unittest.mock import MagicMock
from datetime import datetime, timezone
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src')))

from core_ai.service_discovery.service_discovery_module import ServiceDiscoveryModule, StoredCapabilityInfo
from core_ai.trust_manager.trust_manager_module import TrustManager
from hsp.types import HSPCapabilityAdvertisementPayload, HSPMessageEnvelope

class TestServiceDiscoveryModule(unittest.TestCase):

    def setUp(self):
        self.mock_trust_manager = MagicMock(spec=TrustManager)
        self.discovery_module_with_trust = ServiceDiscoveryModule(trust_manager=self.mock_trust_manager)
        self.discovery_module_no_trust = ServiceDiscoveryModule(trust_manager=None)

    def _create_sample_capability_payload(self, cap_id: str, ai_id: str, name: str, tags: list = None) -> HSPCapabilityAdvertisementPayload:
        return HSPCapabilityAdvertisementPayload(
            capability_id=cap_id,
            ai_id=ai_id,
            name=name,
            description=f"Description for {name}",
            version="1.0",
            availability_status="online",
            tags=tags or []
        )

    def _create_sample_envelope(self, sender_ai_id: str) -> HSPMessageEnvelope:
        return HSPMessageEnvelope(
            message_id="test_msg_id",
            sender_ai_id=sender_ai_id,
            recipient_ai_id="test_recipient",
            timestamp_sent=datetime.now(timezone.utc).isoformat(),
            message_type="HSP::CapabilityAdvertisement_v0.1",
            protocol_version="0.1",
            communication_pattern="publish",
            payload={} # Actual payload set by caller
        )

    def test_process_capability_advertisement_with_trust_manager(self):
        cap_payload = self._create_sample_capability_payload("cap1", "ai1", "Translator")
        sender_ai_id = "ai1"
        envelope = self._create_sample_envelope(sender_ai_id)

        self.mock_trust_manager.get_trust_score.return_value = 0.75

        self.discovery_module_with_trust.process_capability_advertisement(cap_payload, sender_ai_id, envelope)

        self.assertIn("cap1", self.discovery_module_with_trust.known_capabilities)
        stored_cap = self.discovery_module_with_trust.known_capabilities["cap1"]

        self.assertEqual(stored_cap.get("name"), "Translator")
        self.assertEqual(stored_cap.get("_trust_score"), 0.75)
        self.mock_trust_manager.get_trust_score.assert_called_once_with("ai1")
        self.assertIn("cap1", self.discovery_module_with_trust.last_seen)

    def test_process_capability_advertisement_no_trust_manager(self):
        cap_payload = self._create_sample_capability_payload("cap2", "ai2", "Summarizer")
        sender_ai_id = "ai2"
        envelope = self._create_sample_envelope(sender_ai_id)

        self.discovery_module_no_trust.process_capability_advertisement(cap_payload, sender_ai_id, envelope)

        self.assertIn("cap2", self.discovery_module_no_trust.known_capabilities)
        stored_cap = self.discovery_module_no_trust.known_capabilities["cap2"]

        self.assertEqual(stored_cap.get("name"), "Summarizer")
        self.assertEqual(stored_cap.get("_trust_score"), TrustManager.DEFAULT_TRUST_SCORE) # Should use default
        self.assertIn("cap2", self.discovery_module_no_trust.last_seen)

    def test_process_capability_advertisement_missing_id(self):
        cap_payload_no_id = self._create_sample_capability_payload("cap3", "ai3", "Test")
        del cap_payload_no_id["capability_id"] # Remove essential field
        sender_ai_id = "ai3"
        envelope = self._create_sample_envelope(sender_ai_id)

        with patch('builtins.print') as mock_print:
            self.discovery_module_no_trust.process_capability_advertisement(cap_payload_no_id, sender_ai_id, envelope) # type: ignore
            self.assertNotIn("cap3", self.discovery_module_no_trust.known_capabilities)
            mock_print.assert_any_call("ServiceDiscoveryModule: Received capability advertisement without a capability_id. Skipping.")

    def test_find_capabilities_by_name_and_id(self):
        cap1 = self._create_sample_capability_payload("id1", "ai1", "ServiceA")
        cap2 = self._create_sample_capability_payload("id2", "ai2", "ServiceB")
        self.discovery_module_no_trust.process_capability_advertisement(cap1, "ai1", self._create_sample_envelope("ai1"))
        self.discovery_module_no_trust.process_capability_advertisement(cap2, "ai2", self._create_sample_envelope("ai2"))

        results_name: List[StoredCapabilityInfo] = self.discovery_module_no_trust.find_capabilities(capability_name_filter="ServiceA")
        self.assertEqual(len(results_name), 1)
        self.assertEqual(results_name[0].get("capability_id"), "id1")

        results_id: List[StoredCapabilityInfo] = self.discovery_module_no_trust.find_capabilities(capability_id_filter="id2")
        self.assertEqual(len(results_id), 1)
        self.assertEqual(results_id[0].get("name"), "ServiceB")

    def test_find_capabilities_with_trust_filter_and_sort(self):
        cap1 = self._create_sample_capability_payload("id1", "ai_high_trust", "ServiceHigh")
        cap2 = self._create_sample_capability_payload("id2", "ai_low_trust", "ServiceLow")
        cap3 = self._create_sample_capability_payload("id3", "ai_mid_trust", "ServiceMid")

        self.mock_trust_manager.get_trust_score.side_effect = lambda ai_id: {"ai_high_trust": 0.9, "ai_low_trust": 0.3, "ai_mid_trust": 0.6}.get(ai_id, 0.5)

        self.discovery_module_with_trust.process_capability_advertisement(cap1, "ai_high_trust", self._create_sample_envelope("ai_high_trust"))
        self.discovery_module_with_trust.process_capability_advertisement(cap2, "ai_low_trust", self._create_sample_envelope("ai_low_trust"))
        self.discovery_module_with_trust.process_capability_advertisement(cap3, "ai_mid_trust", self._create_sample_envelope("ai_mid_trust"))

        # Test filtering
        results_min_trust: List[StoredCapabilityInfo] = self.discovery_module_with_trust.find_capabilities(min_trust_score=0.5)
        self.assertEqual(len(results_min_trust), 2) # Should include high (0.9) and mid (0.6)
        self.assertNotIn("id2", [c.get("capability_id") for c in results_min_trust])

        # Test sorting
        results_sorted: List[StoredCapabilityInfo] = self.discovery_module_with_trust.find_capabilities(sort_by_trust=True)
        self.assertEqual(len(results_sorted), 3)
        self.assertEqual(results_sorted[0].get("capability_id"), "id1") # Highest trust
        self.assertEqual(results_sorted[1].get("capability_id"), "id3") # Mid trust
        self.assertEqual(results_sorted[2].get("capability_id"), "id2") # Low trust

        # Test filtering and sorting
        results_filtered_sorted: List[StoredCapabilityInfo] = self.discovery_module_with_trust.find_capabilities(min_trust_score=0.5, sort_by_trust=True)
        self.assertEqual(len(results_filtered_sorted), 2)
        self.assertEqual(results_filtered_sorted[0].get("capability_id"), "id1") # High
        self.assertEqual(results_filtered_sorted[1].get("capability_id"), "id3") # Mid

    def test_get_capability_by_id(self):
        cap1 = self._create_sample_capability_payload("id1", "ai1", "ServiceA")
        self.discovery_module_no_trust.process_capability_advertisement(cap1, "ai1", self._create_sample_envelope("ai1"))

        found_cap: Optional[StoredCapabilityInfo] = self.discovery_module_no_trust.get_capability_by_id("id1")
        self.assertIsNotNone(found_cap)
        self.assertEqual(found_cap.get("name"), "ServiceA") # type: ignore

        not_found_cap = self.discovery_module_no_trust.get_capability_by_id("nonexistent")
        self.assertIsNone(not_found_cap)

    def test_remove_capability(self):
        cap1 = self._create_sample_capability_payload("id1", "ai1", "ServiceA")
        self.discovery_module_no_trust.process_capability_advertisement(cap1, "ai1", self._create_sample_envelope("ai1"))
        self.assertIn("id1", self.discovery_module_no_trust.known_capabilities)

        removed = self.discovery_module_no_trust.remove_capability("id1")
        self.assertTrue(removed)
        self.assertNotIn("id1", self.discovery_module_no_trust.known_capabilities)
        self.assertNotIn("id1", self.discovery_module_no_trust.last_seen)

        removed_again = self.discovery_module_no_trust.remove_capability("id1")
        self.assertFalse(removed_again)

    def test_get_all_capabilities(self):
        cap1 = self._create_sample_capability_payload("id1", "ai1", "ServiceA")
        cap2 = self._create_sample_capability_payload("id2", "ai2", "ServiceB")
        self.discovery_module_no_trust.process_capability_advertisement(cap1, "ai1", self._create_sample_envelope("ai1"))
        self.discovery_module_no_trust.process_capability_advertisement(cap2, "ai2", self._create_sample_envelope("ai2"))

        all_caps: List[StoredCapabilityInfo] = self.discovery_module_no_trust.get_all_capabilities()
        self.assertEqual(len(all_caps), 2)
        cap_ids_present = {c.get("capability_id") for c in all_caps}
        self.assertIn("id1", cap_ids_present)
        self.assertIn("id2", cap_ids_present)

if __name__ == '__main__':
    unittest.main(verbosity=2)
