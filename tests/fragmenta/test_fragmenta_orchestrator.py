import unittest
from unittest.mock import MagicMock, patch, ANY
import uuid
from datetime import datetime, timezone

from src.fragmenta.fragmenta_orchestrator import FragmentaOrchestrator, PendingHSPSubTaskInfo, ComplexTaskState
from src.core_ai.memory.ham_memory_manager import HAMMemoryManager
from src.services.llm_interface import LLMInterface
from src.tools.tool_dispatcher import ToolDispatcher
from src.core_ai.service_discovery.service_discovery_module import ServiceDiscoveryModule
from src.hsp.connector import HSPConnector
from src.core_ai.trust_manager.trust_manager_module import TrustManager # For mock SDM
from src.hsp.types import HSPCapabilityAdvertisementPayload, HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope

class TestFragmentaOrchestratorHSPIntegration(unittest.TestCase):

    def setUp(self):
        self.mock_ham_manager = MagicMock(spec=HAMMemoryManager)
        self.mock_llm_interface = MagicMock(spec=LLMInterface)
        self.mock_tool_dispatcher = MagicMock(spec=ToolDispatcher)
        self.mock_service_discovery = MagicMock(spec=ServiceDiscoveryModule)
        self.mock_hsp_connector = MagicMock(spec=HSPConnector)
        # Mock the ai_id attribute for hsp_connector if it's accessed directly
        self.mock_hsp_connector.ai_id = "did:hsp:fragmenta_test_host_ai"


        self.fragmenta = FragmentaOrchestrator(
            ham_manager=self.mock_ham_manager,
            llm_interface=self.mock_llm_interface,
            tool_dispatcher=self.mock_tool_dispatcher,
            service_discovery=self.mock_service_discovery,
            hsp_connector=self.mock_hsp_connector,
            config={"default_chunking_threshold": 50}
        )

        # Sample successful capability advertisement
        self.sample_hsp_capability: HSPCapabilityAdvertisementPayload = {
            "capability_id": "hsp_summary_tool_v1",
            "ai_id": "did:hsp:peer_summarizer_ai",
            "name": "HSPSummarizer",
            "description": "Summarizes text via HSP",
            "version": "1.0",
            "availability_status": "online",
            "tags": ["summary", "nlp"]
        }

        self.task_desc_hsp_explicit = {
            "goal": "summarize text using a specific HSP capability",
            "dispatch_to_hsp_capability_id": "hsp_summary_tool_v1",
            "hsp_task_parameters": {"text": "This is some long text to be summarized by an HSP peer."}
        }
        self.input_data_hsp = "Some input data that might be relevant context or ignored if params are full."


    def test_init_with_hsp_dependencies(self):
        self.assertIsNotNone(self.fragmenta.service_discovery)
        self.assertIsNotNone(self.fragmenta.hsp_connector)
        self.assertIsInstance(self.fragmenta._pending_hsp_sub_tasks, dict)
        self.assertIsInstance(self.fragmenta._complex_task_context, dict)

    def test_determine_processing_strategy_finds_hsp_capability(self):
        self.mock_service_discovery.get_capability_by_id.return_value = self.sample_hsp_capability

        strategy = self.fragmenta._determine_processing_strategy(
            self.task_desc_hsp_explicit,
            {"type": "text", "size": len(self.input_data_hsp)},
            "test_task_id_1"
        )

        self.assertEqual(strategy["name"], "dispatch_to_hsp_capability")
        self.assertEqual(strategy["hsp_capability_info"], self.sample_hsp_capability)
        self.assertEqual(strategy["hsp_task_parameters"], self.task_desc_hsp_explicit["hsp_task_parameters"])
        self.mock_service_discovery.get_capability_by_id.assert_called_once_with("hsp_summary_tool_v1", exclude_unavailable=True)

    def test_determine_processing_strategy_hsp_cap_not_found(self):
        self.mock_service_discovery.get_capability_by_id.return_value = None

        strategy = self.fragmenta._determine_processing_strategy(
            self.task_desc_hsp_explicit,
            {"type": "text", "size": len(self.input_data_hsp)},
            "test_task_id_2"
        )
        print(f"DEBUG: Strategy name in test_determine_processing_strategy_hsp_cap_not_found: {strategy.get('name')}") # DEBUG line
        # Should fall back to a local strategy. Given input_data_hsp length (76) > config threshold (50),
        # it should choose 'chunk_and_summarize_text_locally'.
        self.assertNotEqual(strategy["name"], "dispatch_to_hsp_capability")
        self.assertEqual(strategy["name"], "chunk_and_summarize_text_locally")


    def test_dispatch_hsp_sub_task_success(self):
        mock_correlation_id = f"corr_{uuid.uuid4().hex}"
        self.mock_hsp_connector.send_task_request.return_value = mock_correlation_id
        self.mock_hsp_connector.is_connected = True # Assume connected

        complex_task_id = "complex_task_001"
        params = {"text": "summarize this"}

        returned_corr_id = self.fragmenta._dispatch_hsp_sub_task(complex_task_id, self.sample_hsp_capability, params)

        self.assertEqual(returned_corr_id, mock_correlation_id)
        self.assertIn(mock_correlation_id, self.fragmenta._pending_hsp_sub_tasks)
        pending_info = self.fragmenta._pending_hsp_sub_tasks[mock_correlation_id]
        self.assertEqual(pending_info["original_complex_task_id"], complex_task_id)
        self.assertEqual(pending_info["dispatched_capability_id"], self.sample_hsp_capability["capability_id"])
        self.assertEqual(pending_info["request_payload_parameters"], params)

        self.mock_hsp_connector.send_task_request.assert_called_once()
        call_args = self.mock_hsp_connector.send_task_request.call_args[1] # Get kwargs
        self.assertEqual(call_args['payload']['requester_ai_id'], self.mock_hsp_connector.ai_id)
        self.assertEqual(call_args['payload']['target_ai_id'], self.sample_hsp_capability['ai_id'])
        self.assertEqual(call_args['payload']['capability_id_filter'], self.sample_hsp_capability['capability_id'])
        self.assertEqual(call_args['payload']['parameters'], params)


    def test_dispatch_hsp_sub_task_connector_not_available_or_connected(self):
        self.fragmenta.hsp_connector = None
        corr_id_no_conn = self.fragmenta._dispatch_hsp_sub_task("task1", self.sample_hsp_capability, {})
        self.assertIsNone(corr_id_no_conn)

        self.fragmenta.hsp_connector = self.mock_hsp_connector # Restore
        self.mock_hsp_connector.is_connected = False
        corr_id_not_connected = self.fragmenta._dispatch_hsp_sub_task("task2", self.sample_hsp_capability, {})
        self.assertIsNone(corr_id_not_connected)
        self.mock_hsp_connector.is_connected = True # Reset for other tests


    def test_handle_hsp_sub_task_result_success(self):
        complex_task_id = "complex_task_002"
        correlation_id = "corr_for_task_002"

        self.fragmenta._pending_hsp_sub_tasks[correlation_id] = PendingHSPSubTaskInfo(
            original_complex_task_id=complex_task_id,
            dispatched_capability_id="hsp_summary_tool_v1",
            request_payload_parameters={"text": "test"},
            dispatch_timestamp=datetime.now(timezone.utc).isoformat()
        )
        self.fragmenta._complex_task_context[complex_task_id] = ComplexTaskState(
            task_description={}, input_data=None, strategy_plan={}, current_step_index=0,
            intermediate_results=[], pending_hsp_correlation_ids=[correlation_id], status="awaiting_hsp_result"
        )

        mock_result_data = {"summary": "This is the HSP summary."}
        hsp_result_payload: HSPTaskResultPayload = {
            "result_id": "res_xyz", "request_id": "req_should_match_in_envelope_corr_id_origin",
            "executing_ai_id": "did:hsp:peer_summarizer_ai", "status": "success",
            "payload": mock_result_data
        }
        hsp_envelope: HSPMessageEnvelope = {
            "hsp_envelope_version": "0.1", "message_id": "res_msg_1", "correlation_id": correlation_id,
            "sender_ai_id": "did:hsp:peer_summarizer_ai", "recipient_ai_id": self.fragmenta.hsp_connector.ai_id, # type: ignore
            "timestamp_sent": datetime.now(timezone.utc).isoformat(),
            "message_type": "HSP::TaskResult_v0.1", "protocol_version": "0.1.1",
            "communication_pattern": "response", "payload": hsp_result_payload
        } # type: ignore

        self.fragmenta._handle_hsp_sub_task_result(hsp_result_payload, "did:hsp:peer_summarizer_ai", hsp_envelope)

        self.assertNotIn(correlation_id, self.fragmenta._pending_hsp_sub_tasks)
        task_ctx = self.fragmenta._complex_task_context[complex_task_id]
        self.assertIn(mock_result_data, task_ctx["intermediate_results"])
        self.assertEqual(task_ctx["status"], "hsp_result_received")
        self.assertEqual(len(task_ctx["pending_hsp_correlation_ids"]), 0)

    def test_handle_hsp_sub_task_result_failure(self):
        complex_task_id = "complex_task_003"
        correlation_id = "corr_for_task_003"
        self.fragmenta._pending_hsp_sub_tasks[correlation_id] = PendingHSPSubTaskInfo(
             original_complex_task_id=complex_task_id, dispatched_capability_id="cap1",
             request_payload_parameters={}, dispatch_timestamp=""
        )
        self.fragmenta._complex_task_context[complex_task_id] = ComplexTaskState(
            task_description={}, input_data=None, strategy_plan={}, current_step_index=0,
            intermediate_results=[], pending_hsp_correlation_ids=[correlation_id], status="awaiting_hsp_result"
        )

        error_details = {"error_code": "PEER_ERROR", "error_message": "Peer failed to process."}
        hsp_result_payload: HSPTaskResultPayload = {
            "result_id": "res_fail", "request_id": "req_fail", "executing_ai_id": "did:hsp:peer_ai",
            "status": "failure", "error_details": error_details # type: ignore
        }
        hsp_envelope: HSPMessageEnvelope = { # type: ignore
            "correlation_id": correlation_id, "sender_ai_id": "did:hsp:peer_ai",
            # Fill other required fields
             "hsp_envelope_version": "0.1", "message_id": "res_msg_f",
            "recipient_ai_id": self.fragmenta.hsp_connector.ai_id, # type: ignore
            "timestamp_sent": datetime.now(timezone.utc).isoformat(),
            "message_type": "HSP::TaskResult_v0.1", "protocol_version": "0.1.1",
            "communication_pattern": "response", "payload": hsp_result_payload
        }

        self.fragmenta._handle_hsp_sub_task_result(hsp_result_payload, "did:hsp:peer_ai", hsp_envelope)

        task_ctx = self.fragmenta._complex_task_context[complex_task_id]
        # Check if error information is stored or logged (actual storage in intermediate_results is one way)
        self.assertTrue(any(isinstance(res, str) and "HSP Task Error" in res for res in task_ctx["intermediate_results"]))
        self.assertEqual(task_ctx["status"], "hsp_result_received") # Still received, but content indicates error


    def test_process_complex_task_hsp_flow(self):
        # This is a more end-to-end style test for the HSP flow within process_complex_task
        # complex_task_id = "complex_e2e_task_001" # Remove this line for initial call
        self.mock_service_discovery.get_capability_by_id.return_value = self.sample_hsp_capability

        mock_correlation_id = f"corr_e2e_{uuid.uuid4().hex}"
        self.mock_hsp_connector.send_task_request.return_value = mock_correlation_id
        self.mock_hsp_connector.is_connected = True

        # Initial call to process_complex_task, should dispatch to HSP
        initial_response = self.fragmenta.process_complex_task(
            self.task_desc_hsp_explicit, self.input_data_hsp # Remove complex_task_id here
        )

        # Capture the generated complex_task_id
        complex_task_id = initial_response.get("complex_task_id")
        self.assertIsNotNone(complex_task_id, "complex_task_id was not returned in initial response")

        self.assertEqual(initial_response["status"], "pending_hsp")
        # self.assertEqual(initial_response["complex_task_id"], complex_task_id) # Already captured and checked
        self.assertEqual(initial_response.get("correlation_id"), mock_correlation_id) # Use .get for safety if key might be missing
        self.assertIn(mock_correlation_id, self.fragmenta._complex_task_context[complex_task_id]["pending_hsp_correlation_ids"])
        self.assertEqual(self.fragmenta._complex_task_context[complex_task_id]["status"], "awaiting_hsp_result")

        # Simulate HSP result callback
        mock_result_data = {"summary": "HSP summary for E2E test"}
        hsp_result_payload: HSPTaskResultPayload = {
            "result_id": "res_e2e", "request_id": "req_e2e",
            "executing_ai_id": self.sample_hsp_capability['ai_id'], "status": "success",
            "payload": mock_result_data
        }
        hsp_envelope: HSPMessageEnvelope = { # type: ignore
            "correlation_id": mock_correlation_id, "sender_ai_id": self.sample_hsp_capability['ai_id'],
            "hsp_envelope_version": "0.1", "message_id": "res_msg_e2e",
            "recipient_ai_id": self.fragmenta.hsp_connector.ai_id, # type: ignore
            "timestamp_sent": datetime.now(timezone.utc).isoformat(),
            "message_type": "HSP::TaskResult_v0.1", "protocol_version": "0.1.1",
            "communication_pattern": "response", "payload": hsp_result_payload
        }

        self.fragmenta._handle_hsp_sub_task_result(hsp_result_payload, self.sample_hsp_capability['ai_id'], hsp_envelope)

        # Verify context updated by callback
        task_ctx_after_callback = self.fragmenta._complex_task_context[complex_task_id]
        self.assertEqual(task_ctx_after_callback["status"], "hsp_result_received")
        self.assertIn(mock_result_data, task_ctx_after_callback["intermediate_results"])

        # Re-call process_complex_task to finalize based on received HSP result
        # For this simple case, it should go to merge and complete
        final_response = self.fragmenta.process_complex_task(
            task_description=None, input_data=None, complex_task_id=complex_task_id # type: ignore
        )

        self.assertEqual(final_response["status"], "completed")
        self.assertEqual(final_response["result"], mock_result_data) # Assuming merge simply returns the single HSP result
        # self.assertNotIn(complex_task_id, self.fragmenta._complex_task_context) # If context is cleaned up on completion

    def test_process_complex_task_local_fallback_if_hsp_services_missing(self):
        # Test that it falls back to local processing if SDM or HSP Connector are None
        self.fragmenta.service_discovery = None
        self.fragmenta.hsp_connector = None

        # Task description still hints at HSP
        strategy = self.fragmenta._determine_processing_strategy(
            self.task_desc_hsp_explicit,
            {"type": "text", "size": len(self.input_data_hsp)},
            "task_no_hsp_services"
        )
        # Should not be HSP strategy if services are None
        self.assertNotEqual(strategy.get("name"), "dispatch_to_hsp_capability")
        self.assertTrue(strategy.get("name") == "error_hsp_unavailable" or strategy.get("name") == "direct_local_llm_process")

        # Restore for other tests
        self.fragmenta.service_discovery = self.mock_service_discovery
        self.fragmenta.hsp_connector = self.mock_hsp_connector

if __name__ == '__main__':
    unittest.main()
