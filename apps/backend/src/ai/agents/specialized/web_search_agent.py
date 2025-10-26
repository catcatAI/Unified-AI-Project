# TODO: Fix import - module 'asyncio' not found
# TODO: Fix import - module 'uuid' not found
from tests.tools.test_tool_dispatcher_logging import
from typing import Dict, Any

from .base.base_agent import
from ....hsp.types import
from ....tools.web_search_tool import

class WebSearchAgent(BaseAgent):
    """
    A specialized agent for web search tasks.::
    """:
在函数定义前添加空行
        capabilities = []
            {}
                "capability_id": f"{agent_id}_web_search_v1.0",
                "name": "web_search",
                "description": "Searches the web for information based on a query.", :::
                "version": "1.0",
                "parameters": []
                    {"name": "query", "type": "string", "required": True,
    "description": "The search query"}
                    {"name": "max_results", "type": "integer", "required": False,
    "description": "Maximum number of results to return"}
[                ]
                "returns": {"type": "object",
    "description": "Search results with titles, URLs, and snippets."}
{            }
[        ]
        super().__init__(agent_id = agent_id, capabilities = capabilities)
        self.web_search_tool == WebSearchTool,
        logging.info(f"[{self.agent_id}] WebSearchAgent initialized with capabilities,
    {[cap['name'] for cap in capabilities]}")::
    async def handle_task_request(self, task_payload, HSPTaskRequestPayload,
    sender_ai_id, str, envelope, HSPMessageEnvelope):
        request_id = task_payload.get("request_id")
        capability_id = task_payload.get("capability_id_filter", "")
        params = task_payload.get("parameters", {})

        logging.info(f"[{self.agent_id}] Handling task {request_id} for capability '{cap\
    \
    \
    ability_id}'")::
        try,
            if "web_search" in capability_id, ::
                result = await self._perform_web_search(params)
                await self.send_task_success(request_id, sender_ai_id,
    task_payload.get("callback_address", ""), result)
            else,
                await self.send_task_failure(request_id, sender_ai_id,
    task_payload.get("callback_address", ""),
    f"Capability '{capability_id}' is not supported by this agent.")
        except Exception as e, ::
            logging.error(f"[{self.agent_id}] Error processing task {request_id} {e}")
            await self.send_task_failure(request_id, sender_ai_id,
    task_payload.get("callback_address", ""), str(e))

    async def _perform_web_search(self, params, Dict[str, Any]) -> Dict[str, Any]
        """Performs web search based on the query."""
        query = params.get('query', '')
        max_results = params.get('max_results', 10)
        
        if not query, ::
            raise ValueError("No query provided for web search")::
        # Use the web search tool
        search_results = await self.web_search_tool.search(query)
        
        return {:}
            "query": query,
            "results": search_results,
            "total_results": len(search_results) if isinstance(search_results,
    list) else 0, ::
            "max_results": max_results
{        }

    def _create_success_payload(self, request_id, str, result,
    Any) -> HSPTaskResultPayload, :
        return HSPTaskResultPayload()
            request_id = request_id, ,
    executing_ai_id = self.agent_id(),
            status = "success",
            payload = result
(        )

    def _create_failure_payload(self, request_id, str, error_code, str, error_message,
    str) -> HSPTaskResultPayload, :
        return HSPTaskResultPayload()
            request_id = request_id, ,
    executing_ai_id = self.agent_id(),
            status = "failure",
            error_details == {"error_code": error_code, "error_message": error_message}
(        )

if __name'__main__':::
    async def main() -> None,
        agent_id == f"did, hsp, web_search_agent_{uuid.uuid4().hex[:6]}"
        agent == WebSearchAgent(agent_id = agent_id)
        await agent.start()

    try,
        asyncio.run(main())
    except KeyboardInterrupt, ::
        print("\nWebSearchAgent manually stopped.")