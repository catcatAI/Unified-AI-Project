import asyncio
import uuid
import logging
from typing import Dict, Any, List

from apps.backend.src.ai.agents.base.base_agent import BaseAgent
from apps.backend.src.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope
from apps.backend.src.tools.web_search_tool import WebSearchTool

class WebSearchAgent(BaseAgent):
    """
    A specialized agent for web search tasks.
    """
    def __init__(self, agent_id: str):
        capabilities = [
            {
                "capability_id": f"{agent_id}_web_search_v1.0",
                "name": "web_search",
                "description": "Searches the web for information based on a query.",
                "version": "1.0",
                "parameters": [
                    {"name": "query", "type": "string", "required": True, "description": "The search query"},
                    {"name": "max_results", "type": "integer", "required": False, "description": "Maximum number of results to return"}
                ],
                "returns": {"type": "object", "description": "Search results with titles, URLs, and snippets."}
            }
        ]
        super().__init__(agent_id=agent_id, capabilities=capabilities)
        self.web_search_tool = WebSearchTool()
        logging.info(f"[{self.agent_id}] WebSearchAgent initialized with capabilities: {[cap['name'] for cap in capabilities]}")

    async def handle_task_request(self, task_payload: HSPTaskRequestPayload, sender_ai_id: str, envelope: HSPMessageEnvelope):
        request_id = task_payload.get("request_id")
        capability_id = task_payload.get("capability_id_filter", "")
        params = task_payload.get("parameters", {})

        logging.info(f"[{self.agent_id}] Handling task {request_id} for capability '{capability_id}'")

        try:
            if "web_search" in capability_id:
                result = await self._perform_web_search(params)
                result_payload = self._create_success_payload(request_id, result)
            else:
                result_payload = self._create_failure_payload(request_id, "CAPABILITY_NOT_SUPPORTED", f"Capability '{capability_id}' is not supported by this agent.")
        except Exception as e:
            logging.error(f"[{self.agent_id}] Error processing task {request_id}: {e}")
            result_payload = self._create_failure_payload(request_id, "EXECUTION_ERROR", str(e))

        if self.hsp_connector and task_payload.get("callback_address"):
            callback_topic = task_payload["callback_address"]
            await self.hsp_connector.send_task_result(result_payload, callback_topic)
            logging.info(f"[{self.agent_id}] Sent task result for {request_id} to {callback_topic}")

    async def _perform_web_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Performs web search based on the query."""
        query = params.get('query', '')
        max_results = params.get('max_results', 10)
        
        if not query:
            raise ValueError("No query provided for web search")
        
        # Use the web search tool
        search_results = await self.web_search_tool.search(query)
        
        return {
            "query": query,
            "results": search_results,
            "total_results": len(search_results) if isinstance(search_results, list) else 0,
            "max_results": max_results
        }

    def _create_success_payload(self, request_id: str, result: Any) -> HSPTaskResultPayload:
        return HSPTaskResultPayload(
            request_id=request_id,
            status="success",
            payload=result
        )

    def _create_failure_payload(self, request_id: str, error_code: str, error_message: str) -> HSPTaskResultPayload:
        return HSPTaskResultPayload(
            request_id=request_id,
            status="failure",
            error_details={"error_code": error_code, "error_message": error_message}
        )

if __name__ == '__main__':
    async def main():
        agent_id = f"did:hsp:web_search_agent_{uuid.uuid4().hex[:6]}"
        agent = WebSearchAgent(agent_id=agent_id)
        await agent.start()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nWebSearchAgent manually stopped.")
