import unittest
import unittest.mock # Explicit import
import time
import threading # Added for spec in MagicMock
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List, Any

from src.core_ai.service_discovery.service_discovery_module import ServiceDiscoveryModule, StoredCapabilityInfo
from src.core_ai.trust_manager.trust_manager_module import TrustManager
from src.hsp.types import HSPCapabilityAdvertisementPayload, HSPMessageEnvelope

class MockTrustManager(TrustManager):
    def __init__(self, initial_trust_scores: Optional[Dict[str, float]] = None):
        super().__init__(initial_trust_scores)
        self.scores_to_return = initial_trust_scores if initial_trust_scores else {}

    def get_trust_score(self, ai_id: str) -> float:
        return self.scores_to_return.get(ai_id, self.DEFAULT_TRUST_SCORE)

    def set_mock_score(self, ai_id: str, score: float):
        self.scores_to_return[ai_id] = score

class TestHSPServiceDiscoveryModule(unittest.TestCase):

    def setUp(self):
        self.mock_trust_manager = MockTrustManager()
        # Using a long pruning interval so it doesn't interfere with non-pruning tests
        self.sdm = ServiceDiscoveryModule(
            trust_manager=self.mock_trust_manager,
            staleness_threshold_seconds=1,
            pruning_interval_seconds=3600
        )
        # Stop the timer started in __init__ for this test class,
        # as these tests don't focus on active pruning.
        if hasattr(self.sdm, 'stop_pruning_timer'):
            self.sdm.stop_pruning_timer()


        self.cap_adv1_payload: HSPCapabilityAdvertisementPayload = {
            "capability_id": "translator_v1", "ai_id": "did:hsp:ai_translator_1", "name": "Fast Translator",
            "description": "Translates text fast.", "version": "1.0", "availability_status": "online",
            "tags": ["translation", "nlp", "text"]
        }
        self.cap_adv1_envelope: HSPMessageEnvelope = {
            "hsp_envelope_version": "0.1", "message_id": "msg1", "sender_ai_id": "did:hsp:ai_translator_1",
            "recipient_ai_id": "hsp/capabilities/advertisements", "timestamp_sent": datetime.now(timezone.utc).isoformat(),
            "message_type": "HSP::CapabilityAdvertisement_v0.1", "protocol_version": "0.1.1",
            "communication_pattern": "publish", "payload": self.cap_adv1_payload
        }

        self.cap_adv2_payload: HSPCapabilityAdvertisementPayload = {
            "capability_id": "image_analyzer_v2", "ai_id": "did:hsp:ai_vision_1", "name": "Image Analyzer",
            "description": "Analyzes images.", "version": "2.0", "availability_status": "online",
            "tags": ["vision", "cv", "images"]
        }
        self.cap_adv2_envelope: HSPMessageEnvelope = {
            "hsp_envelope_version": "0.1", "message_id": "msg2", "sender_ai_id": "did:hsp:ai_vision_1",
            "recipient_ai_id": "hsp/capabilities/advertisements", "timestamp_sent": datetime.now(timezone.utc).isoformat(),
            "message_type": "HSP::CapabilityAdvertisement_v0.1", "protocol_version": "0.1.1",
            "communication_pattern": "publish", "payload": self.cap_adv2_payload
        }

        self.cap_adv3_payload_offline: HSPCapabilityAdvertisementPayload = {
            "capability_id": "offline_tool_v1", "ai_id": "did:hsp:ai_translator_1", "name": "Offline Text Utility",
            "description": "A tool that is offline.", "version": "1.0", "availability_status": "offline",
            "tags": ["utility", "text"]
        }
        self.cap_adv3_envelope: HSPMessageEnvelope = {
            "hsp_envelope_version": "0.1", "message_id": "msg3", "sender_ai_id": "did:hsp:ai_translator_1",
            "recipient_ai_id": "hsp/capabilities/advertisements", "timestamp_sent": datetime.now(timezone.utc).isoformat(),
            "message_type": "HSP::CapabilityAdvertisement_v0.1", "protocol_version": "0.1.1",
            "communication_pattern": "publish", "payload": self.cap_adv3_payload_offline
        }

    def tearDown(self):
        # Ensure the timer is stopped after each test if it was started by a test
        if hasattr(self.sdm, 'stop_pruning_timer'):
            self.sdm.stop_pruning_timer()


    def test_initialization(self):
        # Re-initialize sdm for this specific test to check initial state before setUp's stop_pruning_timer
        sdm_init_test = ServiceDiscoveryModule(
            trust_manager=self.mock_trust_manager,
            staleness_threshold_seconds=1,
            pruning_interval_seconds=600
        )
        self.assertIsNotNone(sdm_init_test)
        self.assertEqual(sdm_init_test.staleness_threshold_seconds, 1)
        self.assertEqual(len(sdm_init_test._capabilities_store), 0)
        self.assertIsNotNone(sdm_init_test._pruning_timer, "Timer should be initialized by default")
        self.assertTrue(sdm_init_test._pruning_timer.is_alive(), "Timer should be running by default")
        self.assertFalse(sdm_init_test._stop_pruning_event.is_set(), "Stop event should be clear initially")
        sdm_init_test.stop_pruning_timer() # Clean up this instance's timer


    def test_process_capability_advertisement_valid(self):
        self.sdm.process_capability_advertisement(self.cap_adv1_payload, self.cap_adv1_envelope['sender_ai_id'], self.cap_adv1_envelope)
        self.assertIn("translator_v1", self.sdm._capabilities_store)
        stored_item = self.sdm._capabilities_store["translator_v1"]
        self.assertEqual(stored_item['payload']['name'], "Fast Translator")

    def test_process_capability_advertisement_sender_mismatch(self):
        mismatch_payload = self.cap_adv1_payload.copy()
        mismatch_payload["ai_id"] = "did:hsp:payload_specific_ai"
        mismatch_envelope = self.cap_adv1_envelope.copy()
        mismatch_envelope["sender_ai_id"] = "did:hsp:envelope_sender_actual"
        mismatch_envelope["payload"] = mismatch_payload
        self.mock_trust_manager.set_mock_score("did:hsp:envelope_sender_actual", 0.9)
        with self.assertLogs(logger='src.core_ai.service_discovery.service_discovery_module', level='WARNING') as cm:
            self.sdm.process_capability_advertisement(mismatch_payload, mismatch_envelope['sender_ai_id'], mismatch_envelope)
        self.assertTrue(any("mismatched 'ai_id'" in message for message in cm.output))
        stored_item = self.sdm._capabilities_store.get(mismatch_payload["capability_id"])
        self.assertEqual(stored_item['sender_ai_id'], "did:hsp:envelope_sender_actual")

    def test_process_capability_advertisement_update(self):
        self.sdm.process_capability_advertisement(self.cap_adv1_payload, self.cap_adv1_envelope['sender_ai_id'], self.cap_adv1_envelope)
        original_timestamp = self.sdm._capabilities_store["translator_v1"]['last_seen_timestamp']

        # To ensure the timestamp is different for the update:
        time.sleep(0.01) # Small delay

        updated_payload = self.cap_adv1_payload.copy()
        updated_payload["version"] = "1.1"
        updated_envelope = self.cap_adv1_envelope.copy()
        updated_envelope["payload"] = updated_payload
        updated_envelope["message_id"] = "msg1_updated"
        updated_envelope["timestamp_sent"] = datetime.now(timezone.utc).isoformat()

        self.sdm.process_capability_advertisement(updated_payload, updated_envelope['sender_ai_id'], updated_envelope)
        stored_item = self.sdm._capabilities_store["translator_v1"]
        self.assertEqual(stored_item['payload']['version'], "1.1")
        self.assertTrue(stored_item['last_seen_timestamp'] > original_timestamp)


    def test_process_capability_advertisement_invalid_payload(self):
        invalid_payload = self.cap_adv1_payload.copy()
        del invalid_payload["name"]
        with self.assertLogs(logger='src.core_ai.service_discovery.service_discovery_module', level='WARNING') as cm:
            self.sdm.process_capability_advertisement(invalid_payload, self.cap_adv1_envelope['sender_ai_id'], self.cap_adv1_envelope)
        self.assertEqual(len(self.sdm._capabilities_store), 0)
        self.assertTrue(any("missing essential fields" in message for message in cm.output))
        self.assertTrue(any("name" in message and "missing essential fields" in message for message in cm.output))

    def test_process_empty_or_none_payload(self):
        with self.assertLogs(logger='src.core_ai.service_discovery.service_discovery_module', level='WARNING') as cm:
            self.sdm.process_capability_advertisement(None, "sender_for_none", self.cap_adv1_envelope)
        self.assertTrue(any("Received empty capability_payload" in message for message in cm.output))
        self.assertEqual(len(self.sdm._capabilities_store), 0)

        empty_payload: HSPCapabilityAdvertisementPayload = {}
        envelope_for_empty = self.cap_adv1_envelope.copy()
        envelope_for_empty["payload"] = empty_payload
        with self.assertLogs(logger='src.core_ai.service_discovery.service_discovery_module', level='WARNING') as cm_empty:
            self.sdm.process_capability_advertisement(empty_payload, "sender_for_empty", envelope_for_empty)
        self.assertTrue(any("Received empty capability_payload" in message for message in cm_empty.output),
                        f"Log 'Received empty capability_payload' not found in {cm_empty.output} for empty dict payload.")
        self.assertEqual(len(self.sdm._capabilities_store), 0)

    def test_get_capability_by_id(self):
        self.sdm.process_capability_advertisement(self.cap_adv1_payload, self.cap_adv1_envelope['sender_ai_id'], self.cap_adv1_envelope)
        retrieved_cap = self.sdm.get_capability_by_id("translator_v1")
        self.assertIsNotNone(retrieved_cap)

    def test_find_capabilities_no_filters(self):
        self.sdm.process_capability_advertisement(self.cap_adv1_payload, self.cap_adv1_envelope['sender_ai_id'], self.cap_adv1_envelope)
        self.sdm.process_capability_advertisement(self.cap_adv2_payload, self.cap_adv2_envelope['sender_ai_id'], self.cap_adv2_envelope)
        results = self.sdm.find_capabilities(exclude_unavailable=False)
        self.assertEqual(len(results), 2)


    def test_find_capabilities_by_name(self):
        self.sdm.process_capability_advertisement(self.cap_adv1_payload, self.cap_adv1_envelope['sender_ai_id'], self.cap_adv1_envelope)
        results = self.sdm.find_capabilities(capability_name_filter="Fast Translator")
        self.assertEqual(len(results), 1)

    def test_find_capabilities_by_id(self):
        self.sdm.process_capability_advertisement(self.cap_adv1_payload, self.cap_adv1_envelope['sender_ai_id'], self.cap_adv1_envelope)
        results = self.sdm.find_capabilities(capability_id_filter="translator_v1")
        self.assertEqual(len(results), 1)

    def test_find_capabilities_by_tags(self):
        self.sdm.process_capability_advertisement(self.cap_adv1_payload, self.cap_adv1_envelope['sender_ai_id'], self.cap_adv1_envelope)
        self.sdm.process_capability_advertisement(self.cap_adv2_payload, self.cap_adv2_envelope['sender_ai_id'], self.cap_adv2_envelope)
        results_nlp = self.sdm.find_capabilities(tags_filter=["nlp"])
        self.assertEqual(len(results_nlp), 1)

    def test_find_capabilities_with_trust_filter_and_sort(self):
        self.mock_trust_manager.set_mock_score("did:hsp:ai_translator_1", 0.8)
        self.mock_trust_manager.set_mock_score("did:hsp:ai_vision_1", 0.3)
        self.sdm.process_capability_advertisement(self.cap_adv1_payload, self.cap_adv1_envelope['sender_ai_id'], self.cap_adv1_envelope)
        self.sdm.process_capability_advertisement(self.cap_adv2_payload, self.cap_adv2_envelope['sender_ai_id'], self.cap_adv2_envelope)
        results_min_trust = self.sdm.find_capabilities(min_trust_score=0.5)
        self.assertEqual(len(results_min_trust), 1)
        self.mock_trust_manager.set_mock_score("did:hsp:ai_vision_1", 0.9)
        results_sorted = self.sdm.find_capabilities(exclude_unavailable=False)
        self.assertEqual(results_sorted[0]['capability_id'], "image_analyzer_v2")

    def test_staleness(self):
        self.sdm.process_capability_advertisement(self.cap_adv1_payload, self.cap_adv1_envelope['sender_ai_id'], self.cap_adv1_envelope)
        with self.sdm._store_lock:
            if "translator_v1" in self.sdm._capabilities_store:
                current_entry = self.sdm._capabilities_store["translator_v1"]
                stale_time = datetime.now(timezone.utc) - timedelta(seconds=self.sdm.staleness_threshold_seconds + 5)
                self.sdm._capabilities_store["translator_v1"] = StoredCapabilityInfo(
                    payload=current_entry['payload'], sender_ai_id=current_entry['sender_ai_id'],
                    last_seen_timestamp=stale_time, message_id=current_entry['message_id']
                )
        self.assertIsNone(self.sdm.get_capability_by_id("translator_v1"))

    def test_availability_filtering(self):
        self.sdm.process_capability_advertisement(self.cap_adv1_payload, self.cap_adv1_envelope['sender_ai_id'], self.cap_adv1_envelope)
        self.sdm.process_capability_advertisement(self.cap_adv3_payload_offline, self.cap_adv3_envelope['sender_ai_id'], self.cap_adv3_envelope)
        online_caps = self.sdm.find_capabilities(capability_name_filter="Fast Translator")
        self.assertEqual(len(online_caps), 1)
        all_caps_utility = self.sdm.find_capabilities(capability_name_filter="Offline Text Utility", exclude_unavailable=False)
        self.assertEqual(len(all_caps_utility), 1)

    def test_get_all_capabilities(self):
        self.sdm.process_capability_advertisement(self.cap_adv1_payload, self.cap_adv1_envelope['sender_ai_id'], self.cap_adv1_envelope)
        self.sdm.process_capability_advertisement(self.cap_adv2_payload, self.cap_adv2_envelope['sender_ai_id'], self.cap_adv2_envelope)
        self.sdm.process_capability_advertisement(self.cap_adv3_payload_offline, self.cap_adv3_envelope['sender_ai_id'], self.cap_adv3_envelope)
        all_caps = self.sdm.get_all_capabilities()
        self.assertEqual(len(all_caps), 3)
        online_only = self.sdm.get_all_capabilities(exclude_unavailable=True)
        self.assertEqual(len(online_only), 2)


class TestActivePruning(unittest.TestCase):
    def setUp(self):
        self.mock_trust_manager = MockTrustManager()
        self.sdm = ServiceDiscoveryModule(
            trust_manager=self.mock_trust_manager,
            staleness_threshold_seconds=1,
            pruning_interval_seconds=0.05
        )
        self.cap_fresh_payload: HSPCapabilityAdvertisementPayload = {
            "capability_id": "fresh_cap", "ai_id": "did:hsp:ai_fresh", "name": "Fresh Capability",
            "description": "This should remain.", "version": "1.0", "availability_status": "online", "tags": []
        }
        self.cap_fresh_envelope: HSPMessageEnvelope = {
            "hsp_envelope_version": "0.1", "message_id": "msg_fresh", "sender_ai_id": "did:hsp:ai_fresh",
            "recipient_ai_id": "hsp/cap_adv", "timestamp_sent": "", "message_type": "HSP::CapAdv",
            "protocol_version": "0.1.1", "communication_pattern": "publish", "payload": self.cap_fresh_payload
        }

        self.cap_stale_payload: HSPCapabilityAdvertisementPayload = {
            "capability_id": "stale_cap", "ai_id": "did:hsp:ai_stale", "name": "Stale Capability",
            "description": "This should be pruned.", "version": "1.0", "availability_status": "online", "tags": []
        }
        self.cap_stale_envelope: HSPMessageEnvelope = {
            "hsp_envelope_version": "0.1", "message_id": "msg_stale", "sender_ai_id": "did:hsp:ai_stale",
            "recipient_ai_id": "hsp/cap_adv", "timestamp_sent": "", "message_type": "HSP::CapAdv",
            "protocol_version": "0.1.1", "communication_pattern": "publish", "payload": self.cap_stale_payload
        }

    def tearDown(self):
        if hasattr(self.sdm, 'stop_pruning_timer'):
            self.sdm.stop_pruning_timer()


    @unittest.mock.patch('threading.Timer', autospec=True)
    def test_active_pruning_removes_stale_capabilities(self, MockTimerClass):
        # Stop the timer started in setUp to control calls for this test
        self.sdm.stop_pruning_timer()
        MockTimerClass.reset_mock() # Reset count from setUp's __init__ call

        # Explicitly start the timer; this should be the first call to MockTimerClass constructor for this test
        self.sdm._stop_pruning_event.clear()
        self.sdm._start_pruning_timer()
        self.assertEqual(MockTimerClass.call_count, 1, "Timer should be constructed once by explicit _start_pruning_timer.")

        stale_timestamp = datetime.now(timezone.utc) - timedelta(seconds=self.sdm.staleness_threshold_seconds + 5)
        self.sdm.process_capability_advertisement(self.cap_stale_payload, self.cap_stale_envelope['sender_ai_id'], self.cap_stale_envelope)
        with self.sdm._store_lock:
             if "stale_cap" in self.sdm._capabilities_store: # Check before modifying
                self.sdm._capabilities_store["stale_cap"]["last_seen_timestamp"] = stale_timestamp

        fresh_timestamp = datetime.now(timezone.utc) - timedelta(seconds=0.5)
        self.sdm.process_capability_advertisement(self.cap_fresh_payload, self.cap_fresh_envelope['sender_ai_id'], self.cap_fresh_envelope)
        with self.sdm._store_lock:
            if "fresh_cap" in self.sdm._capabilities_store: # Check before modifying
                self.sdm._capabilities_store["fresh_cap"]["last_seen_timestamp"] = fresh_timestamp

        self.assertIn("stale_cap", self.sdm._capabilities_store)
        self.assertIn("fresh_cap", self.sdm._capabilities_store)

        self.sdm._run_pruning_cycle()

        self.assertNotIn("stale_cap", self.sdm._capabilities_store)
        self.assertIn("fresh_cap", self.sdm._capabilities_store)
        # After _run_pruning_cycle, _start_pruning_timer is called again if not stopped
        self.assertEqual(MockTimerClass.call_count, 2, "Timer should be constructed twice (explicit start + one reschedule).")


    @unittest.mock.patch('threading.Timer', autospec=True)
    def test_stop_pruning_timer(self, MockTimerClass):
        # Scenario 1: Timer is alive
        controlled_mock_instance_alive = unittest.mock.MagicMock()
        controlled_mock_instance_alive.is_alive = unittest.mock.MagicMock(return_value=True)
        controlled_mock_instance_alive.cancel = unittest.mock.MagicMock()
        self.sdm._pruning_timer = controlled_mock_instance_alive

        self.sdm.stop_pruning_timer()
        self.assertTrue(self.sdm._stop_pruning_event.is_set())
        controlled_mock_instance_alive.cancel.assert_called_once()
        self.assertIsNone(self.sdm._pruning_timer)

        # Scenario 2: Timer is not alive
        self.sdm._stop_pruning_event.clear()
        controlled_mock_instance_not_alive = unittest.mock.MagicMock()
        controlled_mock_instance_not_alive.is_alive = unittest.mock.MagicMock(return_value=False)
        controlled_mock_instance_not_alive.cancel = unittest.mock.MagicMock()
        self.sdm._pruning_timer = controlled_mock_instance_not_alive

        self.sdm.stop_pruning_timer()
        controlled_mock_instance_not_alive.cancel.assert_not_called()
        self.assertTrue(self.sdm._stop_pruning_event.is_set())
        self.assertIsNone(self.sdm._pruning_timer)

        initial_call_count = MockTimerClass.call_count
        self.sdm._run_pruning_cycle() # stop_event is set
        self.assertEqual(MockTimerClass.call_count, initial_call_count)


if __name__ == '__main__':
    unittest.main()
