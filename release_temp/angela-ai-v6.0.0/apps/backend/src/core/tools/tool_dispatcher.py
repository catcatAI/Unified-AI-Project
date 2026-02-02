import inspect


class ToolDispatcher:
    def __init__(self):
        self.registered_tools = {}

    def register_tool(self, tool_name, tool_func):
        """Registers a tool with the dispatcher."""
        self.registered_tools[tool_name] = tool_func

    async def dispatch_tool(self, tool_name: str, *args, **kwargs):
        """Dispatches a registered tool by its name.
        Supports both synchronous and asynchronous tool functions.
        """
        if tool_name not in self.registered_tools:
            raise ValueError(f"Tool '{tool_name}' is not registered.")

        tool_func = self.registered_tools[tool_name]

        if inspect.iscoroutinefunction(tool_func):
            result = await tool_func(*args, **kwargs)
        else:
            result = tool_func(*args, **kwargs)

        return {"tool_name": tool_name, "result": result}

    def list_tools(self):
        """Lists all registered tool names."""
        return {"registered_tools": list(self.registered_tools.keys())}
