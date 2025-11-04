import logging
from typing import Dict, Any, Callable, Awaitable, Union
import asyncio # Added missing import

logger = logging.getLogger(__name__)

class ToolDispatcher:
    """
    Dispatches tool calls to registered tools.
    """
    def __init__(self):
        self.tools: Dict[str, Callable[..., Awaitable[Any]]] = {}

    def register_tool(self, name: str, tool_func: Callable[..., Awaitable[Any]]):
        """Registers an asynchronous tool function."""
        if not asyncio.iscoroutinefunction(tool_func):
            logger.warning(f"Tool '{name}' is not an async function. It will be called synchronously.")
        self.tools[name] = tool_func
        logger.info(f"Tool '{name}' registered.")

    async def dispatch_tool(self, name: str, **kwargs) -> Any:
        """
        Dispatches a call to the specified tool.
        """
        tool_func = self.tools.get(name)
        if not tool_func:
            raise ValueError(f"Tool '{name}' not found.")

        logger.info(f"Dispatching tool '{name}' with kwargs: {kwargs}")
        try:
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**kwargs)
            else:
                result = tool_func(**kwargs)
            logger.info(f"Tool '{name}' executed successfully. Result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error executing tool '{name}': {e}", exc_info=True)
            raise

# Example usage (for testing purposes)
async def example_async_tool(param1: str, param2: int) -> str:
    await asyncio.sleep(0.1) # Simulate async operation
    return f"Async tool executed with {param1} and {param2}"

def example_sync_tool(param: str) -> str:
    return f"Sync tool executed with {param}"

if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)

    async def main():
        dispatcher = ToolDispatcher()
        dispatcher.register_tool("async_tool", example_async_tool)
        dispatcher.register_tool("sync_tool", example_sync_tool)

        try:
            async_result = await dispatcher.dispatch_tool("async_tool", param1="hello", param2=123)
            print(f"Main received: {async_result}")

            sync_result = await dispatcher.dispatch_tool("sync_tool", param="world")
            print(f"Main received: {sync_result}")

            # Test non-existent tool
            await dispatcher.dispatch_tool("non_existent_tool")
        except ValueError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    asyncio.run(main())