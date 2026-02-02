from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class BaseTool(ABC):
    """The abstract base class for all tools that can be used by agents in the Unified AI Project."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The unique name of the tool (e.g., 'calculator', 'web_search')."""

    @property
    @abstractmethod
    def description(self) -> str:
        """A detailed description of what the tool does, for an AI agent to understand its purpose."""

    @property
    @abstractmethod
    def args_schema(self) -> type[BaseModel]:
        """The Pydantic model that defines the arguments for the tool."""

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """Executes the tool with the given arguments.

        Args:
            **kwargs: The arguments for the tool, which will be validated against the args_schema.

        Returns:
            Any: The result of the tool's execution. Can be a string, a dictionary, or any other serializable type.

        """

    def get_schema(self) -> dict[str, Any]:
        """Returns a JSON schema representation of the tool, which is useful for function-calling LLMs."""
        if self.args_schema is None or self.args_schema is type(None):
            # Handle tools with no arguments
            parameters = {"type": "object", "properties": {}, "required": []}
        else:
            parameters = self.args_schema.model_json_schema()

        return {
            "name": self.name,
            "description": self.description,
            "parameters": parameters,
        }


class EmptyToolSchema(BaseModel):
    """An empty schema for tools that do not require any arguments."""
