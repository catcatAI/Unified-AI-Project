from typing import Any
from pydantic import BaseModel, Field
from apps.backend.src.tools.base_tool import BaseTool
from apps.backend.src.services.search_service import search_manager

class SearchToolSchema(BaseModel):
    query: str = Field(..., description="The search query.")
    num_results: int = Field(5, description="Number of results to return.")

class SearchTool(BaseTool):
    @property
    def name(self) -> str:
        return "search"

    @property
    def description(self) -> str:
        return "Performs a web search to retrieve information."

    @property
    def args_schema(self) -> type[BaseModel]:
        return SearchToolSchema

    async def execute(self, **kwargs: Any) -> Any:
        return await search_manager.search(**kwargs)
