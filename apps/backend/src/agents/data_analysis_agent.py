import asyncio
import uuid
from typing import Dict, Any, List

from apps.backend.src.agents.base_agent import BaseAgent
from apps.backend.src.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope

class DataAnalysisAgent(BaseAgent):
    """
    A specialized agent for performing data analysis on CSV data.
    """
    def __init__(self, agent_id: str):
        capabilities = [
            {
                "capability_id": "data_analysis_v1",
                "name": "Data Analysis",
                "description": "Performs data analysis tasks.",
                "version": "1.0",
                "parameters": [
                    {"name": "data", "type": "array", "required": True}
                ],
                "returns": {"type": "number", "description": "The sum of the data array."}
            }
        ]
        super().__init__(agent_id=agent_id, capabilities=capabilities)

    async def handle_task_request(self, task_payload: HSPTaskRequestPayload, sender_ai_id: str, envelope: HSPMessageEnvelope):
        # 使用 .get() 方法安全地访问 TypedDict 中的字段
        request_id = task_payload.get('request_id', '')
        parameters = task_payload.get('parameters', {})
        data = parameters.get("data", [])
        callback_address = task_payload.get('callback_address', '')

        # 计算数据数组的和，这与测试期望的结果一致
        try:
            # 确保数据是数字数组，否则抛出异常
            if not all(isinstance(x, (int, float)) for x in data):
                raise TypeError("All elements in data array must be numbers")
            result_data = sum(data)
            payload = result_data
            status = "success"
            error_message = ""
        except Exception as e:
            payload = None
            status = "failure"
            error_message = f"Failed to process data: {str(e)}"

        if status == "success":
            # 确保 callback_address 是字符串类型，避免传递 None
            safe_callback_address = callback_address if callback_address is not None else ''
            await self.send_task_success(request_id, sender_ai_id, safe_callback_address, payload)
        else:
            # 确保 callback_address 是字符串类型，避免传递 None
            safe_callback_address = callback_address if callback_address is not None else ''
            await self.send_task_failure(request_id, sender_ai_id, safe_callback_address, error_message)

if __name__ == '__main__':
    async def main():
        agent_id = f"did:hsp:data_analysis_agent_{uuid.uuid4().hex[:6]}"
        agent = DataAnalysisAgent(agent_id=agent_id)
        await agent.start()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDataAnalysisAgent manually stopped.")