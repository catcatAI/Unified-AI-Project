import asyncio
from apps.backend.src.agents.base_agent import BaseAgent
from apps.backend.src.tools.web_search_tool import WebSearchTool

class WebSearchAgent(BaseAgent):
    def __init__(self, **kwargs):
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

    async def handle_task_request(self, capability_name, parameters):
        if capability_name == "search_web":
            query = parameters.get("query")
            if query:
                return await self.web_search_tool.search(query)
            else:
                return {"error": "Missing query parameter."}
        else:
            return {"error": f"Unknown capability: {capability_name}"}

if __name__ == "__main__":
    agent = WebSearchAgent(agent_id="web_search_agent_1")
    asyncio.run(agent.run())
