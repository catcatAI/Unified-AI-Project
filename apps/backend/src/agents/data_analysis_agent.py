import asyncio
import asyncio
import json
import sys
import os

from src.agents.base_agent import BaseAgent
from src.hsp.types import HSPCapabilityAdvertisementPayload, HSPTaskResultPayload
from src.shared.types.common_types import ToolDispatcherResponse

class DataAnalysisAgent(BaseAgent):
    def __init__(self, agent_id: str):
        super().__init__(
            agent_id=agent_id,
            agent_name="Data Analysis Agent",
            capabilities=[
                HSPCapabilityAdvertisementPayload(
                    capability_id="data_analysis_v1",
                    ai_id=agent_id,
                    name="CSV Data Analyzer",
                    description="Analyzes CSV data and provides insights.",
                    version="1.0",
                    availability_status="online",
                    supported_tools=["analyze_csv"]
                )
            ]
        )

    async def handle_task_request(self, task_payload, sender_ai_id, envelope):
        request_id = task_payload['request_id']
        parameters = task_payload['parameters']
        csv_content = parameters.get("csv_content")
        query = parameters.get("query")
        callback_address = task_payload['callback_address']

        if not csv_content or not query:
            error_message = "Missing 'csv_content' or 'query' in task parameters."
            await self.send_task_failure(request_id, sender_ai_id, callback_address, error_message)
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
                error_message = "Dummy analysis failed: Unsupported query or invalid CSV."
            else:
                error_message = "Dummy analysis failed: Unsupported query or invalid CSV."

        if status == "success":
            await self.send_task_success(request_id, sender_ai_id, callback_address, payload)
        else:
            await self.send_task_failure(request_id, sender_ai_id, callback_address, error_message)