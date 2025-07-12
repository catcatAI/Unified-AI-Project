# src/fragmenta/tech_block.py
"""
Defines the Abstract Base Class for Tech Blocks, fundamental processing units
within the Fragmenta Multi-Bus System architecture.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Type # Using Type for type hints in schemas
import logging

# It's good practice for library-like modules to configure a null handler
# to avoid "No handler found" warnings if the main application doesn't configure logging.
# However, for internal modules, direct logger usage is fine.
logger = logging.getLogger(__name__)

class TechBlock(ABC):
    """
    Abstract Base Class for a Tech Block.
    Tech Blocks are granular, specialized processing units.
    """

    def __init__(self, block_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initializes the TechBlock.

        Args:
            block_id (str): A unique identifier for this instance of the block.
            config (Optional[Dict[str, Any]]): Configuration parameters for the block.
        """
        self._block_id = block_id
        self._config = config or {}
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}.{self._block_id}")
        self._logger.info(f"TechBlock '{self.get_name()}' (ID: {self._block_id}, Version: {self.get_version()}) initialized.")

    @property
    def block_id(self) -> str:
        return self._block_id

    @property
    def config(self) -> Dict[str, Any]:
        return self._config # Returns a reference; consider deepcopy if immutability is desired

    @abstractmethod
    def get_name(self) -> str:
        """Returns the human-readable name of the Tech Block."""
        pass

    @abstractmethod
    def get_version(self) -> str:
        """Returns the version of the Tech Block."""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Returns a brief description of what the Tech Block does."""
        pass

    @abstractmethod
    def get_input_schema(self) -> Dict[str, Any]:
        """
        Returns a JSON schema-like dictionary describing the expected inputs.
        Example:
        {
            "type": "object",
            "properties": {
                "text_content": {"type": "string", "description": "Text to process"},
                "threshold": {"type": "number", "default": 0.5}
            },
            "required": ["text_content"]
        }
        """
        pass

    @abstractmethod
    def get_output_schema(self) -> Dict[str, Any]:
        """
        Returns a JSON schema-like dictionary describing the output structure.
        Example:
        {
            "type": "object",
            "properties": {
                "processed_text": {"type": "string"},
                "confidence": {"type": "number"}
            },
            "required": ["processed_text"]
        }
        """
        pass

    @abstractmethod
    async def process(self, inputs: Dict[str, Any], complex_task_id: str, step_id: str) -> Dict[str, Any]:
        """
        The core execution method of the Tech Block.
        This method must be implemented by concrete subclasses.
        It should validate inputs against its schema (conceptually).

        Args:
            inputs (Dict[str, Any]): The input data for the block, expected to conform to get_input_schema().
            complex_task_id (str): The ID of the parent complex task in Fragmenta, for context/logging.
            step_id (str): The ID of the current processing step in Fragmenta, for context/logging.

        Returns:
            Dict[str, Any]: The output data, conforming to get_output_schema().

        Raises:
            NotImplementedError: If not implemented by a subclass.
            Exception: Can raise exceptions on processing errors.
        """
        pass

    # Optional common utility methods could be added here later,
    # e.g., for input validation against the schema, though that might be
    # better handled by a framework or a dedicated validation step in the bus.
    def _log_processing_start(self, inputs: Dict[str, Any], complex_task_id: str, step_id: str):
        """Helper to log the start of processing."""
        # Truncate inputs for logging if they are too large
        loggable_inputs = {k: (str(v)[:100] + '...' if isinstance(v, str) and len(v) > 100 else v)
                           for k, v in inputs.items()}
        self._logger.info(f"Starting processing for task '{complex_task_id}', step '{step_id}'. Inputs (preview): {loggable_inputs}")

    def _log_processing_end(self, outputs: Dict[str, Any], complex_task_id: str, step_id: str):
        """Helper to log the end of processing."""
        loggable_outputs = {k: (str(v)[:100] + '...' if isinstance(v, str) and len(v) > 100 else v)
                            for k, v in outputs.items()}
        self._logger.info(f"Finished processing for task '{complex_task_id}', step '{step_id}'. Outputs (preview): {loggable_outputs}")

```python
# Example of how a Type Hint for schema could be more specific if desired,
# though Dict[str, Any] is flexible for JSON schema.
# JsonSchemaProperty = TypedDict('JsonSchemaProperty', {'type': str, 'description': Optional[str], 'default': Any, ...}, total=False)
# JsonSchema = TypedDict('JsonSchema', {'type': str, 'properties': Dict[str, JsonSchemaProperty], 'required': Optional[List[str]]})


# --- Example Concrete TechBlock Implementations ---

class EchoTechBlock(TechBlock):
    """
    A simple Tech Block that echoes its inputs back as outputs.
    """
    def get_name(self) -> str:
        return "EchoTechBlock"

    def get_version(self) -> str:
        return "0.1.0"

    def get_description(self) -> str:
        return "Echoes the input data back as output. Useful for testing."

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "data": {"type": "object", "description": "Any data to be echoed.", "additionalProperties": True}
            },
            "required": ["data"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "echoed_data": {"type": "object", "description": "The input data, echoed back.", "additionalProperties": True}
            },
            "required": ["echoed_data"]
        }

    async def process(self, inputs: Dict[str, Any], complex_task_id: str, step_id: str) -> Dict[str, Any]:
        self._log_processing_start(inputs, complex_task_id, step_id)

        if "data" not in inputs:
            self._logger.error("Input 'data' field missing.")
            # Consider raising an error or returning an error structure
            # For now, return empty if required input is missing, though schema validation should catch this.
            return {"error": "Missing 'data' in input"}

        output_data = {"echoed_data": inputs["data"]}

        self._log_processing_end(output_data, complex_task_id, step_id)
        return output_data


class ConcatenateStringsTechBlock(TechBlock):
    """
    A Tech Block that concatenates a list of strings with a given separator.
    """
    def get_name(self) -> str:
        return "ConcatenateStringsTechBlock"

    def get_version(self) -> str:
        return "0.1.0"

    def get_description(self) -> str:
        return "Concatenates a list of input strings using a specified separator."

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "strings_to_join": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of strings to be concatenated."
                },
                "separator": {
                    "type": "string",
                    "description": "The separator to use between strings.",
                    "default": " " # Default separator is a space
                }
            },
            "required": ["strings_to_join"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "concatenated_string": {
                    "type": "string",
                    "description": "The resulting concatenated string."
                }
            },
            "required": ["concatenated_string"]
        }

    async def process(self, inputs: Dict[str, Any], complex_task_id: str, step_id: str) -> Dict[str, Any]:
        self._log_processing_start(inputs, complex_task_id, step_id)

        strings_to_join = inputs.get("strings_to_join")
        separator = inputs.get("separator", self.get_input_schema()["properties"]["separator"]["default"]) # Get default from schema

        if not isinstance(strings_to_join, list) or not all(isinstance(s, str) for s in strings_to_join):
            self._logger.error("'strings_to_join' must be a list of strings.")
            return {"error": "'strings_to_join' must be a list of strings."}

        if not isinstance(separator, str):
            self._logger.warning(f"Separator is not a string (type: {type(separator)}), using default ' '.")
            separator = " "

        result_string = separator.join(strings_to_join)
        output_data = {"concatenated_string": result_string}

        self._log_processing_end(output_data, complex_task_id, step_id)
        return output_data
```
