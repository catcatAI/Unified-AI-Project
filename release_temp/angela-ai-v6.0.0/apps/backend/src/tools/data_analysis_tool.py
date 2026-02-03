from typing import Any, List, Dict
from pydantic import BaseModel, Field
from apps.backend.src.tools.base_tool import BaseTool
from apps.backend.src.services.data_analysis_service import data_analysis_manager

class DataAnalysisToolSchema(BaseModel):
    data: List[Dict[str, Any]] = Field(..., description="List of data points (dictionaries).")
    analysis_type: str = Field("summary", description="Type of analysis: 'summary', 'correlation', 'trend'.")
    parameters: Dict[str, Any] = Field({}, description="Additional parameters for analysis.")

class DataAnalysisTool(BaseTool):
    @property
    def name(self) -> str:
        return "data_analysis"

    @property
    def description(self) -> str:
        return "Analyzes structured data."

    @property
    def args_schema(self) -> type[BaseModel]:
        return DataAnalysisToolSchema

    async def execute(self, **kwargs: Any) -> Any:
        return await data_analysis_manager.analyze_data(**kwargs)
