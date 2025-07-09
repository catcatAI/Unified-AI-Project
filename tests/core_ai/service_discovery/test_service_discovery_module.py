import unittest
import time # For time.sleep in staleness test
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List, Any

# Modules to test
from src.core_ai.service_discovery.service_discovery_module import ServiceDiscoveryModule, StoredCapabilityInfo
from src.core_ai.trust_manager.trust_manager_module import TrustManager
from src.hsp.types import HSPCapabilityAdvertisementPayload, HSPMessageEnvelope

# Mock TrustManager for testing
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
        # Short staleness for easier testing
        self.sdm = ServiceDiscoveryModule(trust_manager=self.mock_trust_manager, staleness_threshold_seconds=1)

        # Sample Payloads & Envelopes
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
        } # type: ignore

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
        } # type: ignore

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
        } # type: ignore

    def test_initialization(self):
        self.assertIsNotNone(self.sdm)
        self.assertEqual(self.sdm.staleness_threshold_seconds, 1)
        self.assertEqual(len(self.sdm._capabilities_store), 0)

    def test_process_capability_advertisement_valid(self):
        self.sdm.process_capability_advertisement(self.cap_adv1_payload, self.cap_adv1_envelope['sender_ai_id'], self.cap_adv1_envelope)
        self.assertIn("translator_v1", self.sdm._capabilities_store)
        stored_item = self.sdm._capabilities_store["translator_v1"]
        self.assertEqual(stored_item['payload']['name'], "Fast Translator")
        self.assertEqual(stored_item['sender_ai_id'], "did:hsp:ai_translator_1")
        self.assertEqual(stored_item['message_id'], "msg1")
        self.assertAlmostEqual(stored_item['last_seen_timestamp'].timestamp(), datetime.now(timezone.utc).timestamp(), delta=1)

    def test_process_capability_advertisement_sender_mismatch(self):
        # Test scenario where payload.ai_id and envelope.sender_ai_id differ
        mismatch_payload = self.cap_adv1_payload.copy()
        mismatch_payload["ai_id"] = "did:hsp:payload_specific_ai" # Different from envelope sender

        mismatch_envelope = self.cap_adv1_envelope.copy()
        mismatch_envelope["sender_ai_id"] = "did:hsp:envelope_sender_actual"
        mismatch_envelope["payload"] = mismatch_payload # type: ignore
        mismatch_envelope["message_id"] = "msg_mismatch"

        self.mock_trust_manager.set_mock_score("did:hsp:envelope_sender_actual", 0.9)
        self.mock_trust_manager.set_mock_score("did:hsp:payload_specific_ai", 0.1) # Lower trust for payload AI ID

        with self.assertLogs(logger='src.core_ai.service_discovery.service_discovery_module', level='WARNING') as cm:
            self.sdm.process_capability_advertisement(mismatch_payload, mismatch_envelope['sender_ai_id'], mismatch_envelope)
        self.assertTrue(any("mismatched 'ai_id'" in message for message in cm.output))

        stored_item = self.sdm._capabilities_store.get(mismatch_payload["capability_id"])
        self.assertIsNotNone(stored_item)
        self.assertEqual(stored_item['sender_ai_id'], "did:hsp:envelope_sender_actual") # sender_ai_id for trust should be from envelope

        # Verify that trust score is based on the envelope sender
        found_caps = self.sdm.find_capabilities(capability_id_filter=mismatch_payload["capability_id"], min_trust_score=0.8)
        self.assertEqual(len(found_caps), 1, "Capability should be found based on envelope sender's high trust score")

    def test_process_capability_advertisement_update(self):
        self.sdm.process_capability_advertisement(self.cap_adv1_payload, self.cap_adv1_envelope['sender_ai_id'], self.cap_adv1_envelope)
        original_timestamp = self.sdm._capabilities_store["translator_v1"]['last_seen_timestamp']

        # time.sleep(0.1) # Ensure timestamp changes - replaced with direct manipulation for reliability
        updated_payload = self.cap_adv1_payload.copy()
        updated_payload["version"] = "1.1"
        updated_envelope = self.cap_adv1_envelope.copy()
        updated_envelope["payload"] = updated_payload
        updated_envelope["message_id"] = "msg1_updated"
        updated_envelope["timestamp_sent"] = datetime.now(timezone.utc).isoformat()

        self.sdm.process_capability_advertisement(updated_payload, updated_envelope['sender_ai_id'], updated_envelope)

        self.assertIn("translator_v1", self.sdm._capabilities_store)
        stored_item = self.sdm._capabilities_store["translator_v1"]
        self.assertEqual(stored_item['payload']['version'], "1.1")
        self.assertNotEqual(stored_item['last_seen_timestamp'], original_timestamp)
        self.assertTrue(stored_item['last_seen_timestamp'] > original_timestamp)
        self.assertEqual(stored_item['message_id'], "msg1_updated")

    def test_process_capability_advertisement_invalid_payload(self):
        invalid_payload = self.cap_adv1_payload.copy()
        del invalid_payload["name"] # Missing a required field

        self.sdm.process_capability_advertisement(invalid_payload, self.cap_adv1_envelope['sender_ai_id'], self.cap_adv1_envelope) # type: ignore
        self.assertEqual(len(self.sdm._capabilities_store), 0) # Should not store invalid payload
        self.assertTrue(any("missing essential fields" in message for message in cm.output), "Log message for missing fields not found.")
        # Check if 'name' (the deleted field) is mentioned in the log to confirm the specific failure reason
        self.assertTrue(any("name" in message for message in cm.output), "Log should specify 'name' was missing.")


    def test_process_empty_or_none_payload(self):
        with self.assertLogs(logger='src.core_ai.service_discovery.service_discovery_module', level='WARNING') as cm:
            self.sdm.process_capability_advertisement(None, "sender_for_none", self.cap_adv1_envelope) # type: ignore
        self.assertTrue(any("Received empty capability_payload" in message for message in cm.output))
        self.assertEqual(len(self.sdm._capabilities_store), 0)

        empty_payload: HSPCapabilityAdvertisementPayload = {} # type: ignore
        envelope_for_empty = self.cap_adv1_envelope.copy()
        envelope_for_empty["payload"] = empty_payload

        with self.assertLogs(logger='src.core_ai.service_discovery.service_discovery_module', level='WARNING') as cm_empty:
            self.sdm.process_capability_advertisement(empty_payload, "sender_for_empty", envelope_for_empty)
        self.assertTrue(any("missing essential fields" in message for message in cm_empty.output))
        self.assertEqual(len(self.sdm._capabilities_store), 0)


    def test_get_capability_by_id(self):
        self.sdm.process_capability_advertisement(self.cap_adv1_payload, self.cap_adv1_envelope['sender_ai_id'], self.cap_adv1_envelope)
        retrieved_cap = self.sdm.get_capability_by_id("translator_v1")
        self.assertIsNotNone(retrieved_cap)
        self.assertEqual(retrieved_cap['name'], "Fast Translator") # type: ignore

        non_existent_cap = self.sdm.get_capability_by_id("non_existent_id")
        self.assertIsNone(non_existent_cap)

    def test_find_capabilities_no_filters(self):
        self.sdm.process_capability_advertisement(self.cap_adv1_payload, self.cap_adv1_envelope['sender_ai_id'], self.cap_adv1_envelope)
        self.sdm.process_capability_advertisement(self.cap_adv2_payload, self.cap_adv2_envelope['sender_ai_id'], self.cap_adv2_envelope)
        results = self.sdm.find_capabilities(exclude_unavailable=False) # include offline for this count
        self.assertEqual(len(results), 2)

    def test_find_capabilities_by_name(self):
        self.sdm.process_capability_advertisement(self.cap_adv1_payload, self.cap_adv1_envelope['sender_ai_id'], self.cap_adv1_envelope)
        results = self.sdm.find_capabilities(capability_name_filter="Fast Translator")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['capability_id'], "translator_v1")

        results_case_insensitive = self.sdm.find_capabilities(capability_name_filter="fast translator")
        self.assertEqual(len(results_case_insensitive), 1)
        self.assertEqual(results_case_insensitive[0]['capability_id'], "translator_v1")

        results_no_match = self.sdm.find_capabilities(capability_name_filter="NonExistent Name")
        self.assertEqual(len(results_no_match), 0)

    def test_find_capabilities_by_id(self):
        self.sdm.process_capability_advertisement(self.cap_adv1_payload, self.cap_adv1_envelope['sender_ai_id'], self.cap_adv1_envelope)
        results = self.sdm.find_capabilities(capability_id_filter="translator_v1")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "Fast Translator")

    def test_find_capabilities_by_tags(self):
        self.sdm.process_capability_advertisement(self.cap_adv1_payload, self.cap_adv1_envelope['sender_ai_id'], self.cap_adv1_envelope) # tags: translation, nlp, text
        self.sdm.process_capability_advertisement(self.cap_adv2_payload, self.cap_adv2_envelope['sender_ai_id'], self.cap_adv2_envelope) # tags: vision, cv, images

        results_nlp = self.sdm.find_capabilities(tags_filter=["nlp"])
        self.assertEqual(len(results_nlp), 1)
        self.assertEqual(results_nlp[0]['capability_id'], "translator_v1")

        results_text_vision = self.sdm.find_capabilities(tags_filter=["text", "vision"]) # No capability has both
        self.assertEqual(len(results_text_vision), 0)

        results_multi_tag_match = self.sdm.find_capabilities(tags_filter=["translation", "text"])
        self.assertEqual(len(results_multi_tag_match), 1)
        self.assertEqual(results_multi_tag_match[0]['capability_id'], "translator_v1")

        results_case_insensitive_tags = self.sdm.find_capabilities(tags_filter=["TRANSLATION"])
        self.assertEqual(len(results_case_insensitive_tags), 1)


    def test_find_capabilities_with_trust_filter_and_sort(self):
        self.mock_trust_manager.set_mock_score("did:hsp:ai_translator_1", 0.8) # translator_v1
        self.mock_trust_manager.set_mock_score("did:hsp:ai_vision_1", 0.3)    # image_analyzer_v2

        self.sdm.process_capability_advertisement(self.cap_adv1_payload, self.cap_adv1_envelope['sender_ai_id'], self.cap_adv1_envelope)
        self.sdm.process_capability_advertisement(self.cap_adv2_payload, self.cap_adv2_envelope['sender_ai_id'], self.cap_adv2_envelope)

        # Test filtering by min_trust_score
        results_min_trust = self.sdm.find_capabilities(min_trust_score=0.5)
        self.assertEqual(len(results_min_trust), 1)
        self.assertEqual(results_min_trust[0]['capability_id'], "translator_v1")

        # Test sorting by trust (default)
        self.mock_trust_manager.set_mock_score("did:hsp:ai_vision_1", 0.9) # Make vision AI more trusted
        results_sorted = self.sdm.find_capabilities(exclude_unavailable=False) # Get all, including offline if any
        self.assertEqual(len(results_sorted), 2)
        self.assertEqual(results_sorted[0]['capability_id'], "image_analyzer_v2") # Vision AI (0.9)
        self.assertEqual(results_sorted[1]['capability_id'], "translator_v1") # Translator AI (0.8)

        # Test no sort
        results_no_sort = self.sdm.find_capabilities(sort_by_trust=False, exclude_unavailable=False)
        self.assertEqual(len(results_no_sort), 2)
        # Order might be insertion order or dict order, less predictable without sort

    def test_staleness(self):
        self.sdm.process_capability_advertisement(self.cap_adv1_payload, self.cap_adv1_envelope['sender_ai_id'], self.cap_adv1_envelope)

        # Initially, it should be found
        self.assertIsNotNone(self.sdm.get_capability_by_id("translator_v1"))
        found_caps = self.sdm.find_capabilities(capability_id_filter="translator_v1")
        self.assertEqual(len(found_caps), 1)

        # Artificially make it stale by directly manipulating its timestamp for test purposes
        # This is a white-box testing approach.
        with self.sdm._store_lock:
            if "translator_v1" in self.sdm._capabilities_store:
                current_entry = self.sdm._capabilities_store["translator_v1"]
                stale_time = datetime.now(timezone.utc) - timedelta(seconds=self.sdm.staleness_threshold_seconds + 5)
                # Create a new StoredCapabilityInfo with the old timestamp
                # Correctly creating a new dict for the StoredCapabilityInfo type
                self.sdm._capabilities_store["translator_v1"] = StoredCapabilityInfo(
                    payload=current_entry['payload'],
                    sender_ai_id=current_entry['sender_ai_id'],
                    last_seen_timestamp=stale_time, # This makes it stale
                    message_id=current_entry['message_id']
                )
            else:
                self.fail("Test setup error: translator_v1 not in store for staleness test.")

        # Now it should be considered stale
        self.assertIsNone(self.sdm.get_capability_by_id("translator_v1"), "Stale entry was not filtered by get_capability_by_id")

        found_caps_after_stale = self.sdm.find_capabilities(capability_id_filter="translator_v1")
        self.assertEqual(len(found_caps_after_stale), 0, "Stale entry was not filtered by find_capabilities")

        # Test re-advertising makes it not stale
        fresh_envelope = self.cap_adv1_envelope.copy()
        fresh_envelope["timestamp_sent"] = datetime.now(timezone.utc).isoformat()
        self.sdm.process_capability_advertisement(self.cap_adv1_payload, fresh_envelope['sender_ai_id'], fresh_envelope)
        self.assertIsNotNone(self.sdm.get_capability_by_id("translator_v1"))


    def test_availability_filtering(self):
        self.sdm.process_capability_advertisement(self.cap_adv1_payload, self.cap_adv1_envelope['sender_ai_id'], self.cap_adv1_envelope) # online
        self.sdm.process_capability_advertisement(self.cap_adv3_payload_offline, self.cap_adv3_envelope['sender_ai_id'], self.cap_adv3_envelope) # offline

        # Default: exclude_unavailable=True
        online_caps = self.sdm.find_capabilities(capability_name_filter="Fast Translator")
        self.assertEqual(len(online_caps), 1)
        self.assertEqual(online_caps[0]['capability_id'], 'translator_v1')

        offline_caps_excluded = self.sdm.find_capabilities(capability_name_filter="Offline Text Utility")
        self.assertEqual(len(offline_caps_excluded), 0)

        # exclude_unavailable=False
        all_caps_utility = self.sdm.find_capabilities(capability_name_filter="Offline Text Utility", exclude_unavailable=False)
        self.assertEqual(len(all_caps_utility), 1)
        self.assertEqual(all_caps_utility[0]['capability_id'], 'offline_tool_v1')

        # get_capability_by_id
        self.assertIsNotNone(self.sdm.get_capability_by_id("offline_tool_v1", exclude_unavailable=False))
        self.assertIsNone(self.sdm.get_capability_by_id("offline_tool_v1", exclude_unavailable=True))
        self.assertIsNotNone(self.sdm.get_capability_by_id("translator_v1", exclude_unavailable=True)) # translator_v1 is online

    def test_get_all_capabilities(self):
        self.sdm.process_capability_advertisement(self.cap_adv1_payload, self.cap_adv1_envelope['sender_ai_id'], self.cap_adv1_envelope)
        self.sdm.process_capability_advertisement(self.cap_adv2_payload, self.cap_adv2_envelope['sender_ai_id'], self.cap_adv2_envelope)
        self.sdm.process_capability_advertisement(self.cap_adv3_payload_offline, self.cap_adv3_envelope['sender_ai_id'], self.cap_adv3_envelope)

        # Default: exclude_stale=True, exclude_unavailable=False
        all_caps = self.sdm.get_all_capabilities()
        self.assertEqual(len(all_caps), 3)

        # Exclude unavailable
        online_only = self.sdm.get_all_capabilities(exclude_unavailable=True)
        self.assertEqual(len(online_only), 2)
        self.assertTrue(all(c.get('availability_status') == 'online' for c in online_only))

        # Simulate staleness for one
        with self.sdm._store_lock:
            if "translator_v1" in self.sdm._capabilities_store:
                 self.sdm._capabilities_store["translator_v1"]["last_seen_timestamp"] -= timedelta(seconds=self.sdm.staleness_threshold_seconds + 5)

        not_stale_caps = self.sdm.get_all_capabilities(exclude_stale=True, exclude_unavailable=False)
        self.assertEqual(len(not_stale_caps), 2) # cap1 is now stale
        self.assertFalse(any(c.get('capability_id') == 'translator_v1' for c in not_stale_caps))

    def tearDown(self):
        # Ensure the timer is stopped after each test if it was started
        if hasattr(self.sdm, '_pruning_timer') and self.sdm._pruning_timer is not None:
            self.sdm.stop_pruning_timer()

class TestActivePruning(unittest.TestCase):
    def setUp(self):
        self.mock_trust_manager = MockTrustManager()
        # Use very short staleness and pruning intervals for testing
        self.sdm = ServiceDiscoveryModule(
            trust_manager=self.mock_trust_manager,
            staleness_threshold_seconds=1, # Stale after 1 second
            pruning_interval_seconds=0.1  # Prune very frequently
        )
        # Payloads
        self.cap_fresh_payload: HSPCapabilityAdvertisementPayload = {
            "capability_id": "fresh_cap", "ai_id": "did:hsp:ai_fresh", "name": "Fresh Capability",
            "description": "This should remain.", "version": "1.0", "availability_status": "online", "tags": []
        }
        self.cap_fresh_envelope: HSPMessageEnvelope = {
            "hsp_envelope_version": "0.1", "message_id": "msg_fresh", "sender_ai_id": "did:hsp:ai_fresh",
            "recipient_ai_id": "hsp/cap_adv", "timestamp_sent": "", "message_type": "HSP::CapAdv",
            "protocol_version": "0.1.1", "communication_pattern": "publish", "payload": self.cap_fresh_payload
        } # type: ignore

        self.cap_stale_payload: HSPCapabilityAdvertisementPayload = {
            "capability_id": "stale_cap", "ai_id": "did:hsp:ai_stale", "name": "Stale Capability",
            "description": "This should be pruned.", "version": "1.0", "availability_status": "online", "tags": []
        }
        self.cap_stale_envelope: HSPMessageEnvelope = {
            "hsp_envelope_version": "0.1", "message_id": "msg_stale", "sender_ai_id": "did:hsp:ai_stale",
            "recipient_ai_id": "hsp/cap_adv", "timestamp_sent": "", "message_type": "HSP::CapAdv",
            "protocol_version": "0.1.1", "communication_pattern": "publish", "payload": self.cap_stale_payload
        } # type: ignore


    @unittest.mock.patch('threading.Timer')
    def test_active_pruning_removes_stale_capabilities(self, MockTimer):
        # Mock the timer to control its execution
        # The timer callback is sdm._run_pruning_cycle
        # We want to simulate it being called.

        # Store a capability that will become stale
        stale_timestamp = datetime.now(timezone.utc) - timedelta(seconds=self.sdm.staleness_threshold_seconds + 5)
        self.cap_stale_envelope["timestamp_sent"] = stale_timestamp.isoformat() # Not directly used by process_cap but good practice
        self.sdm.process_capability_advertisement(self.cap_stale_payload, self.cap_stale_envelope['sender_ai_id'], self.cap_stale_envelope)
        # Manually set its last_seen_timestamp to be in the past for process_capability_advertisement behavior
        with self.sdm._store_lock:
             self.sdm._capabilities_store["stale_cap"]["last_seen_timestamp"] = stale_timestamp


        # Store a fresh capability
        fresh_timestamp = datetime.now(timezone.utc) - timedelta(seconds=0.5) # Well within staleness threshold
        self.cap_fresh_envelope["timestamp_sent"] = fresh_timestamp.isoformat()
        self.sdm.process_capability_advertisement(self.cap_fresh_payload, self.cap_fresh_envelope['sender_ai_id'], self.cap_fresh_envelope)
        with self.sdm._store_lock: # Ensure its timestamp is recent
            self.sdm._capabilities_store["fresh_cap"]["last_seen_timestamp"] = fresh_timestamp


        self.assertIn("stale_cap", self.sdm._capabilities_store)
        self.assertIn("fresh_cap", self.sdm._capabilities_store)

        # Simulate the timer firing and calling _run_pruning_cycle
        # The actual timer is mocked, so we call the method it would call.
        self.sdm._run_pruning_cycle() # This will call _prune_stale_capabilities

        self.assertNotIn("stale_cap", self.sdm._capabilities_store, "Stale capability was not pruned.")
        self.assertIn("fresh_cap", self.sdm._capabilities_store, "Fresh capability was incorrectly pruned.")

        # Check if the timer was "restarted" by _run_pruning_cycle (i.e., Timer was called again)
        # _start_pruning_timer is called at the end of _run_pruning_cycle
        # So, MockTimer should have been called multiple times: once in __init__, once by _run_pruning_cycle
        self.assertTrue(MockTimer.call_count >= 2)


    @unittest.mock.patch('threading.Timer')
    def test_stop_pruning_timer(self, MockTimer):
        # SDM is initialized in setUp, so timer is already mocked and 'started' (constructor called)
        initial_timer_call_count = MockTimer.call_count

        self.sdm.stop_pruning_timer()

        # Check that the stop event is set
        self.assertTrue(self.sdm._stop_pruning_event.is_set())

        # Check that the timer instance's cancel method was called if it existed
        # The actual timer object is stored in self.sdm._pruning_timer
        # MockTimer().cancel is what we need to check.
        # The timer instance is created by MockTimer(interval, callback).
        # We need to get the instance that was created.
        if MockTimer.return_value.is_alive.return_value: # If mock timer was "alive"
             MockTimer.return_value.cancel.assert_called_once()

        # Simulate _run_pruning_cycle being called after stop_event is set
        # It should not reschedule the timer
        self.sdm._run_pruning_cycle()

        # The number of times Timer was constructed should not increase beyond what it was
        # after the initial start and the one call from _run_pruning_cycle before stop.
        # If _run_pruning_cycle was called, it might try to start one more if not for stop_event.
        # Let's be more precise: after stop, _run_pruning_cycle should not call _start_pruning_timer
        # which means MockTimer() constructor should not be called again by it.

        # Reset call count for the next part of the check or verify based on specific calls.
        # Count how many times MockTimer was instantiated AFTER stop_pruning_timer was called.
        # This is tricky because the first timer is started in __init__.
        # Let's verify that _start_pruning_timer within _run_pruning_cycle doesn't start a new one.

        # After stop_pruning_timer, _start_pruning_timer (called by _run_pruning_cycle)
        # should see the stop_event and not create a new Timer.
        # So, the number of MockTimer instantiations should be fixed after stop.

        # Let's refine:
        # 1. Timer is called in __init__ via _start_pruning_timer.
        # 2. We call sdm.stop_pruning_timer().
        # 3. We manually call sdm._run_pruning_cycle().
        # 4. Inside this _run_pruning_cycle, _start_pruning_timer is called.
        # 5. This _start_pruning_timer should NOT instantiate a new MockTimer because _stop_pruning_event is set.

        # So, if __init__ called Timer once. Then MockTimer.call_count is 1.
        # If _run_pruning_cycle is called directly by test, it will call _start_pruning_timer.
        # If stop_event is set, this _start_pruning_timer does not create a new Timer.
        # So the call_count should remain what it was just before the last _run_pruning_cycle if stop_event is set.

        # Let's re-initialize a fresh sdm for this specific test for clarity on call counts
        sdm_for_stop_test = ServiceDiscoveryModule(
            trust_manager=self.mock_trust_manager,
            pruning_interval_seconds=0.1
        )
        # At this point, MockTimer has been called once (in __init__)
        self.assertEqual(MockTimer.call_count, initial_timer_call_count + 1)

        sdm_for_stop_test.stop_pruning_timer()
        # Manually trigger the cycle that would have happened if timer fired
        sdm_for_stop_test._run_pruning_cycle()

        # No new timer should have been created by the above _run_pruning_cycle call
        self.assertEqual(MockTimer.call_count, initial_timer_call_count + 1,
                         "Timer should not be rescheduled after stop_pruning_timer and a manual cycle run.")


if __name__ == '__main__':
    unittest.main()
