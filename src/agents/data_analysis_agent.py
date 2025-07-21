import asyncio
import uuid
from typing import Dict, Any, List

from src.agents.base_agent import BaseAgent
from src.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope
from src.tools.tool_dispatcher import ToolDispatcher

class DataAnalysisAgent(BaseAgent):
    """
    A specialized agent for analyzing data, particularly CSV files.
    """
    def __init__(self, agent_id: str):
        # Define the capabilities of this agent
        capabilities = [
            {
                "capability_id": f"{agent_id}_analyze_csv_data_v1.0",
                "name": "CSV Data Analyzer",
                "description": "Analyzes provided CSV data based on a query (e.g., 'summarize', 'columns').",
                "version": "1.0",
                "parameters": [
                    {"name": "csv_content", "type": "string", "required": True, "description": "The full content of the CSV as a string."},
                    {"name": "query", "type": "string", "required": True, "description": "The analysis query (e.g., 'summarize')."}
                ],
                "returns": {"type": "object", "description": "An object containing the analysis result or an error."}
            }
        ]
        super().__init__(agent_id=agent_id, capabilities=capabilities)

        # This agent needs a tool dispatcher to use the CsvTool
        self.tool_dispatcher = ToolDispatcher()

    async def handle_task_request(self, task_payload: HSPTaskRequestPayload, sender_ai_id: str, envelope: HSPMessageEnvelope):
        """
        Handles incoming data analysis tasks.
        """
        request_id = task_payload.get("request_id")
        params = task_payload.get("parameters", {})
        print(f"[{self.agent_id}] Handling task {request_id} with params: {params}")

        # Dispatch the task to the CsvTool via the ToolDispatcher
        tool_response = self.tool_dispatcher.dispatch(
            query=params.get("query", ""), # The query for the tool
            explicit_tool_name="analyze_csv",
            csv_content=params.get("csv_content"),
            query=params.get("query")
        )

        if tool_response:
            result_payload = HSPTaskResultPayload(
                request_id=request_id,
                status="success" if tool_response["status"] == "success" else "failure",
                payload=tool_response["payload"],
                error_details={"error_message": tool_response["error_message"]} if tool_response["error_message"] else None
            )
        else:
            result_payload = HSPTaskResultPayload(
                request_id=request_id,
                status="failure",
                error_details={"error_code": "DISPATCH_ERROR", "error_message": "Tool dispatcher failed to handle the request."}
            )

        if self.hsp_connector and task_payload.get("callback_address"):
            callback_topic = task_payload["callback_address"]
            self.hsp_connector.send_task_result(result_payload, callback_topic)
            print(f"[{self.agent_id}] Sent task result for {request_id} to {callback_topic}")

if __name__ == '__main__':
    async def main():
        agent_id = f"did:hsp:data_analysis_agent_{uuid.uuid4().hex[:6]}"
        agent = DataAnalysisAgent(agent_id=agent_id)
        await agent.start()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDataAnalysisAgent manually stopped.")
