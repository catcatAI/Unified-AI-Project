import unittest
import pytest
import asyncio
import uuid
import os
import sys
from unittest.mock import MagicMock, AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from apps.backend.src.agents.creative_writing_agent import CreativeWritingAgent
from apps.backend.src.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope
from apps.backend.src.services.multi_llm_service import MultiLLMService, ChatMessage, LLMResponse

class TestCreativeWritingAgent:

    @pytest.fixture(autouse=True)
    def setup_agent(self):
        self.agent_id = f"did:hsp:test_creative_writing_agent_{uuid.uuid4().hex[:6]}"

        # Mock the services that the agent's base class initializes
        self.mock_llm_interface = MagicMock(spec=MultiLLMService)
        self.mock_llm_interface.chat_completion = AsyncMock()
        
        self.mock_hsp_connector = MagicMock()
        self.mock_hsp_connector.send_task_result = AsyncMock()
        self.mock_hsp_connector.register_on_task_request_callback = MagicMock()
        self.mock_hsp_connector.advertise_capability = AsyncMock()
        
        self.mock_services = {
            "hsp_connector": self.mock_hsp_connector,
            "llm_interface": self.mock_llm_interface
        }

        with patch('src.agents.base_agent.initialize_services', return_value=None) as mock_initialize, \
             patch('src.agents.base_agent.get_services', return_value=self.mock_services) as mock_get_services:
            self.mock_initialize = mock_initialize
            self.mock_get_services = mock_get_services

            self.agent = CreativeWritingAgent(agent_id=self.agent_id)
            self.agent.hsp_connector = self.mock_services["hsp_connector"]
            self.agent.llm_interface = self.mock_services["llm_interface"]
            yield

    @pytest.mark.timeout(10)
    def test_initialization(self):
        """Test that the agent initializes correctly."""
        assert self.agent.agent_id == self.agent_id
        assert self.agent.llm_interface is not None
        assert len(self.agent.capabilities) == 2
        assert self.agent.capabilities[0]['name'] == 'generate_marketing_copy'

    @pytest.mark.asyncio
    async def test_handle_marketing_copy_request(self):
        """Test handling a 'generate_marketing_copy' task."""
        # 1. Configure mock LLM to return a predefined response
        expected_copy = "Buy our new amazing product! It's the best!"
        mock_llm_response = MagicMock(spec=LLMResponse)
        mock_llm_response.content = expected_copy
        self.mock_llm_interface.chat_completion.return_value = mock_llm_response

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
        await self.agent.handle_task_request(task_payload, "test_sender", envelope)

        # 4. Assert LLM was called with the correct prompt
        self.mock_llm_interface.chat_completion.assert_called_once()
        call_args = self.mock_llm_interface.chat_completion.call_args
        # Check the messages argument, which should be a list of ChatMessage objects
        messages_arg = call_args.args[0]
        assert isinstance(messages_arg, list)
        assert len(messages_arg) > 0
        assert isinstance(messages_arg[0], ChatMessage)
        assert "Generate marketing copy" in messages_arg[0].content
        assert "A new amazing product" in messages_arg[0].content

        # 5. Assert HSP connector sent the correct success result
        self.agent.hsp_connector.send_task_result.assert_called_once()
        sent_payload = self.agent.hsp_connector.send_task_result.call_args[0][0]

        assert sent_payload['status'] == "success"
        assert sent_payload['payload'] == expected_copy

    @pytest.mark.asyncio
    async def test_handle_polish_text_request(self):
        """Test handling a 'polish_text' task."""
        # 1. Configure mock LLM
        expected_polished_text = "This is a polished sentence."
        mock_llm_response = MagicMock(spec=LLMResponse)
        mock_llm_response.content = expected_polished_text
        self.mock_llm_interface.chat_completion.return_value = mock_llm_response

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
        await self.agent.handle_task_request(task_payload, "test_sender", envelope)

        # 4. Assert LLM was called correctly
        self.mock_llm_interface.chat_completion.assert_called_once()
        call_args = self.mock_llm_interface.chat_completion.call_args
        messages_arg = call_args.args[0]
        assert isinstance(messages_arg, list)
        assert len(messages_arg) > 0
        assert isinstance(messages_arg[0], ChatMessage)
        assert "Please proofread and polish the following text for grammar, style, and clarity. Return only the improved text:" in messages_arg[0].content
        assert "this is a polished sentence" in messages_arg[0].content

        # 5. Assert HSP connector sent the correct success result
        self.agent.hsp_connector.send_task_result.assert_called_once()
        sent_payload = self.agent.hsp_connector.send_task_result.call_args[0][0]

        assert sent_payload['status'] == "success"
        assert sent_payload['payload'] == expected_polished_text

    @pytest.mark.asyncio
    async def test_unsupported_capability(self):
        """Test that the agent correctly handles a request for a capability it doesn't support."""
        request_id = "creative_req_003"
        task_payload = HSPTaskRequestPayload(
            request_id=request_id,
            capability_id_filter="translate_to_klingon",
            parameters={},
            callback_address="hsp/results/test_requester/req_003"
        )
        envelope = HSPMessageEnvelope(message_id="msg_creative_3", sender_ai_id="test_sender", recipient_ai_id=self.agent_id, timestamp_sent="", message_type="", protocol_version="")

        await self.agent.handle_task_request(task_payload, "test_sender", envelope)

        self.agent.hsp_connector.send_task_result.assert_called_once()
        sent_payload = self.agent.hsp_connector.send_task_result.call_args[0][0]

        assert sent_payload['status'] == "failure"
        assert sent_payload['error_details'] is not None
        assert sent_payload['error_details']['error_code'] == "CAPABILITY_NOT_SUPPORTED"


