import unittest
import pytest
import asyncio
import uuid
import os
import sys
from unittest.mock import MagicMock, AsyncMock, patch


from apps.backend.src.ai.agents.specialized.data_analysis_agent import DataAnalysisAgent
from apps.backend.src.hsp.types import HSPTaskRequestPayload, HSPMessageEnvelope
from apps.backend.src.shared.types.common_types import ToolDispatcherResponse

class TestDataAnalysisAgent(unittest.TestCase):

    def setUp(self):
        self.agent_id = f"did:hsp:test_data_analysis_agent_{uuid.uuid4().hex[:6]}"

        # We need to mock the services that the agent's base class initializes
        self.mock_services = {
            "hsp_connector": AsyncMock(),
            "tool_dispatcher": AsyncMock()
        }

        # Patch the service initialization and getter
        patcher_initialize = patch('apps.backend.src.core_services.initialize_services', return_value=None)
        patcher_get = patch('apps.backend.src.core_services.get_services', return_value=self.mock_services)

        self.addCleanup(patcher_initialize.stop)
        self.addCleanup(patcher_get.stop)

        self.mock_initialize = patcher_initialize.start()
        self.mock_get_services = patcher_get.start()

        self.agent = DataAnalysisAgent(agent_id=self.agent_id)
        self.agent.hsp_connector = self.mock_services["hsp_connector"]
        self.agent.tool_dispatcher = self.mock_services["tool_dispatcher"]

    @pytest.mark.timeout(10)
    def test_initialization(self):
        """Test that the agent initializes correctly and advertises its capabilities."""
        self.assertEqual(self.agent.agent_id, self.agent_id)
        self.assertIsNotNone(self.agent.hsp_connector)

        # Check that capabilities were defined
        self.assertTrue(len(self.agent.capabilities) > 0)
        # 验证能力名称与实现匹配
        self.assertEqual(self.agent.capabilities[0]['name'], 'statistical_analysis')

    @pytest.mark.timeout(10)
    def test_handle_task_request_success(self):
        """Test the agent's handling of a successful task request."""


        # 2. Create a mock HSP task payload
        request_id = "test_req_001"
        task_payload = HSPTaskRequestPayload(
            request_id=request_id,
            capability_id_filter=self.agent.capabilities[0]['capability_id'],
            parameters={"data": [1, 2, 3, 4, 5]},  # 修改参数以匹配实际实现
            callback_address="hsp/results/test_requester/req_001"
        )
        envelope = HSPMessageEnvelope(message_id="msg1", sender_ai_id="test_sender", recipient_ai_id=self.agent_id, timestamp_sent="", message_type="", protocol_version="")

        # 3. Run the handle_task_request method
        asyncio.run(self.agent.handle_task_request(task_payload, "test_sender", envelope))

        # 4. Assert that the HSP connector sent the correct result
        self.agent.hsp_connector.send_task_result.assert_called_once()
        sent_payload = self.agent.hsp_connector.send_task_result.call_args[0][0]
        sent_topic = self.agent.hsp_connector.send_task_result.call_args[0][1]

        self.assertEqual(sent_topic, "hsp/results/test_requester/req_001")
        self.assertEqual(sent_payload['request_id'], request_id)
        self.assertEqual(sent_payload['status'], "success")
        # 验证返回值包含正确的统计分析结果
        self.assertIn('mean', sent_payload['payload'])
        self.assertEqual(sent_payload['payload']['mean'], 3.0)

    @pytest.mark.timeout(10)
    def test_handle_task_request_tool_failure(self):
        """Test the agent's handling of a task where the tool fails."""


        # 2. Create a mock HSP task payload with invalid data that will cause sum() to fail
        request_id = "test_req_002"
        task_payload = HSPTaskRequestPayload(
            request_id=request_id,
            capability_id_filter=self.agent.capabilities[0]['capability_id'],
            parameters={"data": ["invalid", "data"]},  # 传递无法处理的数据，包含非数字元素的数组
            callback_address="hsp/results/test_requester/req_002"
        )
        envelope = HSPMessageEnvelope(message_id="msg2", sender_ai_id="test_sender", recipient_ai_id=self.agent_id, timestamp_sent="", message_type="", protocol_version="")

        # 3. Run the handler
        asyncio.run(self.agent.handle_task_request(task_payload, "test_sender", envelope))

        # 4. Assert HSP connector sent a failure result
        self.agent.hsp_connector.send_task_result.assert_called_once()
        sent_payload = self.agent.hsp_connector.send_task_result.call_args[0][0]
        sent_topic = self.agent.hsp_connector.send_task_result.call_args[0][1]

        self.assertEqual(sent_topic, "hsp/results/test_requester/req_002")
        self.assertEqual(sent_payload['request_id'], request_id)
        self.assertEqual(sent_payload['status'], "failure")
        self.assertIsNotNone(sent_payload.get('error_details'))