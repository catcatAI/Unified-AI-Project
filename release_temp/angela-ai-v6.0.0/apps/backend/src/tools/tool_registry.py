import importlib
import inspect
import logging
import pkgutil

from apps.backend.src.tools.base_tool import BaseTool

# Configure logger for this module
logger = logging.getLogger(__name__)

# Module-level registry to store tool instances
_tool_registry: dict[str, BaseTool] = {}


def load_tools(force_reload: bool = False):
    """Discovers and loads all tool classes from the 'tools' directory into the registry.

    This function iterates through all modules in the `apps.backend.src.tools` package,
    finds subclasses of `BaseTool`, instantiates them, and adds them to a central registry.

    Args:
        force_reload (bool): If True, clears the existing registry and reloads all tools.
                             Defaults to False.

    """
    global _tool_registry
    if _tool_registry and not force_reload:
        logger.debug("Tool registry already populated. Skipping load.")
        return

    if force_reload:
        _tool_registry = {}
        logger.info("Forcing tool registry reload.")

    # Dynamically import the tools package
    try:
        import apps.backend.src.tools as tools_package
    except ImportError as e:
        logger.error(
            f"Could not import the tools package. Ensure it's a valid package. Error: {e}",
        )
        return

    logger.info(f"Loading tools from package: {tools_package.__name__}")
    for _, module_name, _ in pkgutil.walk_packages(
        path=tools_package.__path__,
        prefix=tools_package.__name__ + ".",
    ):
        try:
            module = importlib.import_module(module_name)
            for name, obj in inspect.getmembers(module):
                # Check if it's a class, a subclass of BaseTool, and not BaseTool itself
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, BaseTool)
                    and obj is not BaseTool
                ):
                    logger.debug(f"Found tool class: {obj.__name__}")
                    tool_instance = obj()

                    if tool_instance.name in _tool_registry:
                        logger.warning(
                            f"Duplicate tool name '{tool_instance.name}' found. Overwriting.",
                        )

                    _tool_registry[tool_instance.name] = tool_instance
                    logger.info(
                        f"Successfully loaded and registered tool: '{tool_instance.name}'",
                    )

        except Exception as e:
            logger.error(
                f"Failed to load tools from module {module_name}: {e}",
                exc_info=True,
            )


def get_tool(name: str) -> BaseTool | None:
    """Retrieves a tool instance from the registry by its name."""
    if not _tool_registry:
        load_tools()
    return _tool_registry.get(name)


def get_all_tools() -> dict[str, BaseTool]:
    """Returns a dictionary of all registered tool instances."""
    if not _tool_registry:
        load_tools()
    return _tool_registry.copy()


def get_all_schemas() -> list[dict]:
    """Returns the JSON schemas of all registered tools."""
    if not _tool_registry:
        load_tools()
    return [tool.get_schema() for tool in _tool_registry.values()]


# Initial load when the module is first imported.
# This ensures tools are ready as soon as the registry is accessed.
load_tools()
