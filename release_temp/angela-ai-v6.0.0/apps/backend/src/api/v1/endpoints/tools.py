import logging
from typing import Annotated, Any

from fastapi import APIRouter, Body, HTTPException

from apps.backend.src.tools import tool_registry

# Configure logger
logger = logging.getLogger(__name__)

# Create a new router for tool-related endpoints
router = APIRouter(
    prefix="/tools",
    tags=["Tools"],
)


@router.get("/", response_model=list[dict[str, Any]])
async def list_available_tools():
    """Retrieves a list of all available tools and their schemas.
    This is the discovery endpoint for agents or UIs to learn what tools can be used.
    """
    logger.info("Request received to list all available tools.")
    schemas = tool_registry.get_all_schemas()
    logger.info(f"Found {len(schemas)} tools. Returning their schemas.")
    return schemas


@router.post("/{tool_name}/execute")
async def execute_tool(tool_name: str, body: Annotated[dict[str, Any], Body(...)]):
    """Executes a specified tool with the given arguments.

    - **tool_name**: The name of the tool to execute (e.g., 'calculator').
    - **body**: A JSON object containing the arguments for the tool, matching its args_schema.
    """
    logger.info(f"Request received to execute tool: '{tool_name}' with args: {body}")

    tool = tool_registry.get_tool(tool_name)
    if not tool:
        logger.warning(f"Execution failed: Tool '{tool_name}' not found.")
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found.")

    try:
        # The tool's own execute method is responsible for validating args and running the logic
        result = await tool.execute(**body)
        logger.info(f"Tool '{tool_name}' executed successfully.")
        return {"tool_name": tool_name, "status": "success", "result": result}
    except Exception as e:
        # This catches unexpected errors during tool execution.
        # Pydantic validation errors inside the tool are also caught here.
        logger.error(
            f"An error occurred while executing tool '{tool_name}': {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=400,  # 400 for bad request (e.g., invalid arguments)
            detail=f"An error occurred while executing tool '{tool_name}': {e!s}",
        )
