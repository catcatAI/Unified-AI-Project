import asyncio
from .base_agent import BaseAgent
from ..tools.web_search_tool import WebSearchTool

class WebSearchAgent(BaseAgent):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.web_search_tool = WebSearchTool()

    def get_capabilities(self):
        return {
            "search_web": {
                "description": "Searches the web for a given query.",
                "parameters": {
                    "query": "The search query."
                }
            }
        }

    async def handle_task_request(self, task_payload, sender_ai_id, envelope):
        capability_name = task_payload.get("capability_id_filter", "")
        parameters = task_payload.get("parameters", {})
        
        if "search_web" in capability_name:
            query = parameters.get("query")
            if query:
                result = await self.web_search_tool.search(query)
                return {
                    "status": "success",
                    "payload": result
                }
            else:
                return {
                    "status": "failure",
                    "error_details": {
                        "error_code": "MISSING_PARAMETER",
                        "error_message": "Missing query parameter."
                    }
                }
        else:
            return {
                "status": "failure",
                "error_details": {
                    "error_code": "UNKNOWN_CAPABILITY",
                    "error_message": f"Unknown capability: {capability_name}"
                }
            }

if __name__ == "__main__":
    agent = WebSearchAgent(agent_id="web_search_agent_1")
    asyncio.run(agent.start())
