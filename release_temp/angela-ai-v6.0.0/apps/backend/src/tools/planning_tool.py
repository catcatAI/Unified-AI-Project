from typing import Any, List
from pydantic import BaseModel, Field
from apps.backend.src.tools.base_tool import BaseTool
from apps.backend.src.services.planning_service import planning_manager

class PlanningToolSchema(BaseModel):
    goal: str = Field(..., description="The goal to achieve.")
    constraints: List[str] = Field([], description="List of constraints.")
    context: str = Field("", description="Additional context.")

class PlanningTool(BaseTool):
    @property
    def name(self) -> str:
        return "planning"

    @property
    def description(self) -> str:
        return "Generates plans to achieve goals."

    @property
    def args_schema(self) -> type[BaseModel]:
        return PlanningToolSchema

    async def execute(self, **kwargs: Any) -> Any:
        return await planning_manager.generate_plan(**kwargs)
