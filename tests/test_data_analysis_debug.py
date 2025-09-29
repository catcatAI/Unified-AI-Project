import uuid
import pytest
from unittest.mock import AsyncMock

# 修复导入路径
from apps.backend.src.core_ai.agents.specialized.data_analysis_agent import DataAnalysisAgent
from apps.backend.src.core.hsp.types import HSPTaskRequestPayload, HSPMessageEnvelope

# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
@pytest.mark.asyncio
async def test_data_analysis_agent() -> None:
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
        capability_id_filter=agent.capabilities[0]['capability_id'],
        parameters={"data": [1, 2, 3, 4, 5]},
        callback_address="hsp/results/test_requester/req_001"
    )
    envelope = HSPMessageEnvelope(
        message_id="msg1", 
        sender_ai_id="test_sender", 
        recipient_ai_id=agent_id, 
        timestamp_sent="", 
        message_type="", 
        protocol_version=""
    )
    
    _ = await agent.handle_task_request(task_payload, "test_sender", envelope)
    
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
        capability_id_filter=agent.capabilities[0]['capability_id'],
        parameters={"data": ["a", "b", "c"]},  # 传递无法求和的数据
        callback_address="hsp/results/test_requester/req_002"
    )
    envelope = HSPMessageEnvelope(
        message_id="msg2", 
        sender_ai_id="test_sender", 
        recipient_ai_id=agent_id, 
        timestamp_sent="", 
        message_type="", 
        protocol_version=""
    )
    
    _ = await agent.handle_task_request(task_payload, "test_sender", envelope)
    
    # 检查调用
    print("异常情况调用结果:")
    print(f"send_task_result called: {agent.hsp_connector.send_task_result.called}")
    if agent.hsp_connector.send_task_result.called:
        sent_payload = agent.hsp_connector.send_task_result.call_args[0][0]
        print(f"Status: {sent_payload['status']}")
        print(f"Payload: {sent_payload.get('payload', 'N/A')}")
        print(f"Error details: {sent_payload.get('error_details', 'N/A')}")