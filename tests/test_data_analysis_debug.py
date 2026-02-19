"""
測試模組 - test_data_analysis_debug

自動生成的測試模組,用於驗證系統功能。
"""

import sys
import os
import uuid
import pytest
import logging
logger = logging.getLogger(__name__)

# Add the src directory to the path
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src")
)

from unittest.mock import AsyncMock

# 修复导入路径
from ai.agents.specialized.data_analysis_agent import DataAnalysisAgent
from core.hsp.types import HSPTaskRequestPayload, HSPMessageEnvelope


class TestDataAnalysisAgent:
    """DataAnalysisAgent 測試類"""

    def setup_method(self):
        """测试前设置"""
        self.test_data = {}
        self.test_config = {}

    def teardown_method(self):
        """测试后清理"""
        self.test_data.clear()
        self.test_config.clear()

    @pytest.mark.asyncio
    async def test_data_analysis_agent(self):
        """测试 DataAnalysisAgent 的基本功能"""
        # 创建一个DataAnalysisAgent实例
        agent_id = f"did:hsp:test_data_analysis_agent_{uuid.uuid4().hex[:6]}"
        agent = DataAnalysisAgent(agent_id=agent_id)

        # 模拟hsp_connector
        agent.hsp_connector = AsyncMock()

        # 测试正常情况
        print("测试正常情况...")
        request_id = "test_req_001"
        task_payload = HSPTaskRequestPayload(
            request_id=request_id,
            capability_id_filter=agent.capabilities[0]["capability_id"],
            parameters={"data": [1, 2, 3, 4, 5]},
            callback_address="hsp/results/test_requester/req_001",
        )
        envelope = HSPMessageEnvelope(
            message_id="msg1",
            sender_ai_id="test_sender",
            recipient_ai_id=agent_id,
            timestamp_sent="",
            message_type="",
            protocol_version="",
        )

        await agent.handle_task_request(task_payload, "test_sender", envelope)

        # 检查调用
        print("正常情况调用结果:")
        print(f"send_task_result called: {agent.hsp_connector.send_task_result.called}")
        if agent.hsp_connector.send_task_result.called:
            sent_payload = agent.hsp_connector.send_task_result.call_args[0][0]
            print(f"Status: {sent_payload['status']}")
            print(f"Payload: {sent_payload['payload']}")

        # 重置mock
        agent.hsp_connector.reset_mock()

        # 测试异常情况
        print("\n测试异常情况...")
        task_payload = HSPTaskRequestPayload(
            request_id=request_id,
            capability_id_filter=agent.capabilities[0]["capability_id"],
            parameters={"data": ["a", "b", "c"]},  # 传递无法求和的数据
            callback_address="hsp/results/test_requester/req_002",
        )
        envelope = HSPMessageEnvelope(
            message_id="msg2",
            sender_ai_id="test_sender",
            recipient_ai_id=agent_id,
            timestamp_sent="",
            message_type="",
            protocol_version="",
        )

        await agent.handle_task_request(task_payload, "test_sender", envelope)

        # 检查调用
        print("异常情况调用结果:")
        print(f"send_task_result called: {agent.hsp_connector.send_task_result.called}")
        if agent.hsp_connector.send_task_result.called:
            sent_payload = agent.hsp_connector.send_task_result.call_args[0][0]
            print(f"Status: {sent_payload['status']}")
            print(f"Payload: {sent_payload.get('payload', 'N/A')}")
            print(f"Error details: {sent_payload.get('error_details', 'N/A')}")
