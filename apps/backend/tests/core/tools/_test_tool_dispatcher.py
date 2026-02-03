


import pytest
import asyncio
from core.tools.tool_dispatcher import ToolDispatcher

# Define a simple synchronous tool for testing
def sync_test_tool(arg1: str, arg2: int) -> str:
    return f"Sync tool received: {arg1} and {arg2}"

# Define a simple asynchronous tool for testing
async def async_test_tool(arg: str) -> str:
    await asyncio.sleep(0.01) # Simulate async operation
    return f"Async tool received: {arg}"

@pytest.fixture
def tool_dispatcher():
    """Fixture to provide a fresh ToolDispatcher instance for each test."""
    return ToolDispatcher()

@pytest.mark.asyncio
async def test_register_and_dispatch_sync_tool(tool_dispatcher: ToolDispatcher):
    """Test registration and dispatch of a synchronous tool."""
    tool_dispatcher.register_tool("sync_tool", sync_test_tool)
    result = await tool_dispatcher.dispatch_tool("sync_tool", arg1="test", arg2=123)
    assert result == {"tool_name": "sync_tool", "result": "Sync tool received: test and 123"}

@pytest.mark.asyncio
async def test_register_and_dispatch_async_tool(tool_dispatcher: ToolDispatcher):
    """Test registration and dispatch of an asynchronous tool."""
    tool_dispatcher.register_tool("async_tool", async_test_tool)
    result = await tool_dispatcher.dispatch_tool("async_tool", arg="async_data")
    assert result == {"tool_name": "async_tool", "result": "Async tool received: async_data"}

@pytest.mark.asyncio
async def test_dispatch_unregistered_tool(tool_dispatcher: ToolDispatcher):
    """Test dispatching a tool that is not registered."""
    with pytest.raises(ValueError, match="Tool 'non_existent_tool' is not registered."):
        await tool_dispatcher.dispatch_tool("non_existent_tool")

@pytest.mark.asyncio
async def test_list_tools(tool_dispatcher: ToolDispatcher):
    """Test listing registered tools."""
    tool_dispatcher.register_tool("tool_a", sync_test_tool)
    tool_dispatcher.register_tool("tool_b", async_test_tool)
    listed_tools = tool_dispatcher.list_tools()
    assert "registered_tools" in listed_tools
    assert set(listed_tools["registered_tools"]) == {"tool_a", "tool_b"}

# Test for the hello_tool from main.py (assuming it's registered globally or can be mocked)
# For a true unit test, we'd mock the global registration.
# For integration, we'd run the main app.
# For now, let's simulate its registration.
@pytest.mark.asyncio
async def test_hello_tool_functionality(tool_dispatcher: ToolDispatcher):
    """Test the functionality of a simulated 'hello' tool."""
    def hello_tool(name: str = "World") -> str:
        return f"Hello, {name} from a dispatched tool!"
    
    tool_dispatcher.register_tool("hello", hello_tool)
    result = await tool_dispatcher.dispatch_tool("hello", name="Gemini")
    assert result == {"tool_name": "hello", "result": "Hello, Gemini from a dispatched tool!"}
    
    result_default = await tool_dispatcher.dispatch_tool("hello")
    assert result_default == {"tool_name": "hello", "result": "Hello, World from a dispatched tool!"}