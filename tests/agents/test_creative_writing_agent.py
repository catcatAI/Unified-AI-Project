import unittest
import asyncio
import uuid
import os
import sys
from unittest.mock import MagicMock, AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.agents.creative_writing_agent import CreativeWritingAgent
from src.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope
from src.services.llm_interface import LLMInterface

class TestCreativeWritingAgent(unittest.TestCase):

    def setUp(self):
        self.agent_id = f"did:hsp:test_creative_writing_agent_{uuid.uuid4().hex[:6]}"

        # Mock the services that the agent's base class initializes
        self.mock_llm_interface = MagicMock(spec=LLMInterface)
        self.mock_services = {
            "hsp_connector": MagicMock(),
            "llm_interface": self.mock_llm_interface
        }

        patcher_initialize = patch('src.agents.base_agent.initialize_services', return_value=None)
        patcher_get = patch('src.agents.base_agent.get_services', return_value=self.mock_services)

        self.addCleanup(patcher_initialize.stop)
        self.addCleanup(patcher_get.stop)

        self.mock_initialize = patcher_initialize.start()
        self.mock_get_services = patcher_get.start()

        self.agent = CreativeWritingAgent(agent_id=self.agent_id)
        self.agent.hsp_connector = self.mock_services["hsp_connector"]
        self.agent.llm_interface = self.mock_services["llm_interface"]

    def test_initialization(self):
        """Test that the agent initializes correctly."""
        self.assertEqual(self.agent.agent_id, self.agent_id)
        self.assertIsNotNone(self.agent.llm_interface)
        self.assertEqual(len(self.agent.capabilities), 2)
        self.assertEqual(self.agent.capabilities[0]['name'], 'generate_marketing_copy')

    def test_handle_marketing_copy_request(self):
        """Test handling a 'generate_marketing_copy' task."""
        # 1. Configure mock LLM to return a predefined response
        expected_copy = "Buy our new amazing product! It's the best!"
        self.mock_llm_interface.generate_response.return_value = expected_copy

        # 2. Create mock HSP task payload
        request_id = "creative_req_001"
        task_payload = HSPTaskRequestPayload(
            request_id=request_id,
            capability_id_filter="generate_marketing_copy",
            parameters={
                "product_description": "A new amazing product.",
                "target_audience": "Everyone",
                "style": "enthusiastic"
            },
            callback_address="hsp/results/test_requester/req_001"
        )
        envelope = HSPMessageEnvelope(message_id="msg_creative_1", sender_ai_id="test_sender", recipient_ai_id=self.agent_id, timestamp_sent="", message_type="", protocol_version="")

        # 3. Run the handler
        asyncio.run(self.agent.handle_task_request(task_payload, "test_sender", envelope))

        # 4. Assert LLM was called with the correct prompt
        self.mock_llm_interface.generate_response.assert_called_once()
        call_args = self.mock_llm_interface.generate_response.call_args
        self.assertIn("Generate marketing copy", call_args.args[0])
        self.assertIn("A new amazing product", call_args.args[0])

        # 5. Assert HSP connector sent the correct success result
        self.agent.hsp_connector.send_task_result.assert_called_once()
        sent_payload = self.agent.hsp_connector.send_task_result.call_args[0][0]

        self.assertEqual(sent_payload['status'], "success")
        self.assertEqual(sent_payload['payload'], expected_copy)

    def test_handle_polish_text_request(self):
        """Test handling a 'polish_text' task."""
        # 1. Configure mock LLM
        expected_polished_text = "This is a polished sentence."
        self.mock_llm_interface.generate_response.return_value = expected_polished_text

        # 2. Create mock HSP task payload
        request_id = "creative_req_002"
        task_payload = HSPTaskRequestPayload(
            request_id=request_id,
            capability_id_filter="polish_text",
            parameters={"text_to_polish": "this is a polished sentence"},
            callback_address="hsp/results/test_requester/req_002"
        )
        envelope = HSPMessageEnvelope(message_id="msg_creative_2", sender_ai_id="test_sender", recipient_ai_id=self.agent_id, timestamp_sent="", message_type="", protocol_version="")

        # 3. Run the handler
        asyncio.run(self.agent.handle_task_request(task_payload, "test_sender", envelope))

        # 4. Assert LLM was called correctly
        self.mock_llm_interface.generate_response.assert_called_once_with(
            "Please proofread and polish the following text for grammar, style, and clarity. Return only the improved text:\n\n---\nthis is a polished sentence\n---"
        )

        # 5. Assert HSP connector sent the correct success result
        self.agent.hsp_connector.send_task_result.assert_called_once()
        sent_payload = self.agent.hsp_connector.send_task_result.call_args[0][0]

        self.assertEqual(sent_payload['status'], "success")
        self.assertEqual(sent_payload['payload'], expected_polished_text)

    def test_unsupported_capability(self):
        """Test that the agent correctly handles a request for a capability it doesn't support."""
        request_id = "creative_req_003"
        task_payload = HSPTaskRequestPayload(
            request_id=request_id,
            capability_id_filter="translate_to_klingon",
            parameters={},
            callback_address="hsp/results/test_requester/req_003"
        )
        envelope = HSPMessageEnvelope(message_id="msg_creative_3", sender_ai_id="test_sender", recipient_ai_id=self.agent_id, timestamp_sent="", message_type="", protocol_version="")

        asyncio.run(self.agent.handle_task_request(task_payload, "test_sender", envelope))

        self.agent.hsp_connector.send_task_result.assert_called_once()
        sent_payload = self.agent.hsp_connector.send_task_result.call_args[0][0]

        self.assertEqual(sent_payload['status'], "failure")
        self.assertIsNotNone(sent_payload['error_details'])
        self.assertEqual(sent_payload['error_details']['error_code'], "CAPABILITY_NOT_SUPPORTED")

if __name__ == '__main__':
    unittest.main()
