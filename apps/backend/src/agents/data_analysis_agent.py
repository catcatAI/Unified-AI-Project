import asyncio
import uuid
from typing import Dict, Any, List

from src.agents.base_agent import BaseAgent
from src.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope

class DataAnalysisAgent(BaseAgent):
    """
    A specialized agent for performing data analysis on CSV data.
    """
    def __init__(self, agent_id: str):
        capabilities = [
            {
                "capability_id": f"{agent_id}_analyze_data_v1.0",
                "name": "CSV Data Analyzer",
                "description": "Performs data analysis on provided CSV content based on a query.",
                "version": "1.0",
                "parameters": [
                    {"name": "csv_content", "type": "string", "required": True},
                    {"name": "query", "type": "string", "required": True}
                ],
                "returns": {"type": "object", "description": "Analysis results based on the query."}
            }
        ]
        super().__init__(agent_id=agent_id, capabilities=capabilities)

    async def handle_task_request(self, task_payload: HSPTaskRequestPayload, sender_ai_id: str, envelope: HSPMessageEnvelope):
        # 使用 .get() 方法安全地访问 TypedDict 中的字段
        request_id = task_payload.get('request_id', '')
        parameters = task_payload.get('parameters', {})
        csv_content = parameters.get("csv_content")
        query = parameters.get("query")
        callback_address = task_payload.get('callback_address', '')
        error_message = ""  # 初始化 error_message 变量

        if not csv_content or not query:
            error_message = "Missing 'csv_content' or 'query' in task parameters."
            # 确保 callback_address 是字符串类型，避免传递 None
            safe_callback_address = callback_address if callback_address is not None else ''
            await self.send_task_failure(request_id, sender_ai_id, safe_callback_address, error_message)
            return

        # In a real scenario, this would call a tool dispatcher or internal logic
        # For this dummy agent, we'll just simulate a response
        # Simulate failure for invalid CSV (e.g., inconsistent columns)
        is_csv_valid = True
        lines = csv_content.strip().splitlines()
        if lines:
            header_len = len(lines[0].split(','))
            for line in lines[1:]:
                if len(line.split(',')) != header_len:
                    is_csv_valid = False
                    break

        if "summarize" in query.lower() and csv_content and is_csv_valid:
            payload = f"Dummy analysis: Summarized {len(lines)} lines of CSV data."
            status = "success"
        else:
            payload = None
            status = "failure"
            if not csv_content:
                error_message = "Dummy analysis failed: Missing CSV content."
            elif not is_csv_valid:
                # 修复错误消息，使其与测试期望一致
                error_message = "Dummy analysis failed: Invalid CSV format (inconsistent columns)."
            else:
                error_message = "Dummy analysis failed: Unsupported query or invalid CSV."

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