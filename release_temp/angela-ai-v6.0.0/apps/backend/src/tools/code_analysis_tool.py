from typing import Any
from pydantic import BaseModel, Field
from apps.backend.src.tools.base_tool import BaseTool
from apps.backend.src.services.code_analysis_service import code_analysis_manager

class CodeAnalysisToolSchema(BaseModel):
    code: str = Field(..., description="The code snippet to analyze.")
    request_type: str = Field("explain", description="Type of analysis: 'explain', 'debug', 'optimize'.")
    language: str = Field("python", description="Programming language of the code.")

class CodeAnalysisTool(BaseTool):
    @property
    def name(self) -> str:
        return "code_analysis"

    @property
    def description(self) -> str:
        return "Analyzes code for explanation, debugging, or optimization."

    @property
    def args_schema(self) -> type[BaseModel]:
        return CodeAnalysisToolSchema

    async def execute(self, **kwargs: Any) -> Any:
        return await code_analysis_manager.analyze_code(**kwargs)
