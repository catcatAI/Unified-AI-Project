from typing import Dict, Any
from .base_agent import BaseAgent


class DataAnalysisAgent(BaseAgent):
    def __init__(self, agent_id: str):
        capabilities = [
            {
                "capability_id": "data_analysis_v1",
                "name": "CSV Data Analyzer",
                "description": "Analyze CSV content and provide summaries",
            }
        ]
        super().__init__(agent_id, capabilities, agent_name="DataAnalysisAgent")

    async def start(self) -> bool:
        return True

    async def stop(self) -> bool:
        return True

    async def handle_task_request(self, payload: Dict[str, Any], sender_ai_id: str, envelope: Dict[str, Any]) -> None:
        request_id = payload.get("request_id", "")
        csv_content = payload.get("parameters", {}).get("csv_content", "")
        
        try:
            lines = csv_content.strip().split('\n')
            if len(lines) < 2:
                raise ValueError("CSV must have at least a header and one data row")
            
            # Check if CSV has consistent number of columns
            header_columns = len(lines[0].split(','))
            for i, line in enumerate(lines[1:], 1):
                if len(line.split(',')) != header_columns:
                    raise ValueError(f"Row {i} has {len(line.split(','))} columns, expected {header_columns}")
            
            # Expect data lines to be counted as lines - 1 (excluding header)
            data_lines = len(lines) - 1
            
            result_payload: Dict[str, Any] = {
                "request_id": request_id,
                "status": "success",
                "payload": f"Dummy analysis: Summarized {data_lines} lines of CSV data.",
            }
        except Exception as e:
            result_payload: Dict[str, Any] = {
                "request_id": request_id,
                "status": "failure",
                "payload": f"CSV analysis failed: {str(e)}",
            }
        
        callback_address = payload.get("callback_address")
        if self.hsp_connector and callback_address:
            await self.hsp_connector.send_task_result(result_payload, callback_address, request_id)