import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Import the shared instance from the llm_service package
from apps.backend.src.services.llm_service import llm_manager
from apps.backend.src.services.llm_service.base_provider import LLMResponse

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/llm",
    tags=["LLM Service"],
)


class GenerationRequest(BaseModel):
    """Defines the request body for the /generate endpoint."""

    model: str = Field(
        ...,
        description="The name of the model to use for generation, e.g., 'gpt-4' or 'distilgpt2'.",
    )
    prompt: str = Field(..., description="The text prompt to send to the model.")
    kwargs: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional provider-specific arguments, e.g., temperature, max_tokens.",
    )


def _handle_llm_exception(model_name: str, e: Exception):
    logger.error(
        f"An unexpected error occurred during generation for model '{model_name}': {e}",
        exc_info=True,
    )
    raise HTTPException(
        status_code=500,
        detail=f"An error occurred during generation: {e!s}",
    )

@router.post("/generate", response_model=LLMResponse)
async def generate_completion(request: GenerationRequest):
    """Generates a text completion using the configured Multi-LLM service.
    The request is routed to the appropriate provider based on the model name.
    """
    logger.info(
        f"Received API request to generate completion for model '{request.model}'.",
    )
    try:
        return await llm_manager.generate(
            model=request.model,
            prompt=request.prompt,
            **request.kwargs,
        )
    except ValueError as e:
        # Handles cases like model not configured or provider not loaded
        logger.warning(f"Generation failed for model '{request.model}': {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        _handle_llm_exception(request.model, e)
