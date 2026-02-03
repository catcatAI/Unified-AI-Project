from typing import Any
from pydantic import BaseModel, Field
from apps.backend.src.tools.base_tool import BaseTool
from apps.backend.src.services.image_service import image_manager

class ImageGenerationToolSchema(BaseModel):
    prompt: str = Field(..., description="Description of the image to generate.")
    style: str = Field("photorealistic", description="Style of the image.")
    size: str = Field("512x512", description="Size of the image.")

class ImageGenerationTool(BaseTool):
    @property
    def name(self) -> str:
        return "image_generation"

    @property
    def description(self) -> str:
        return "Generates images based on text prompts."

    @property
    def args_schema(self) -> type[BaseModel]:
        return ImageGenerationToolSchema

    async def execute(self, **kwargs: Any) -> Any:
        return await image_manager.generate_image(**kwargs)
