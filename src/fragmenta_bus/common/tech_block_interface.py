import abc
from typing import Dict, Any, Optional, List, Type

# Assuming TechBlockInput, TechBlockOutput, TechBlockManifest are defined in data_models.py
from .data_models import TechBlockInput, TechBlockOutput, TechBlockManifest

class TechBlock(abc.ABC):
    """
    Abstract Base Class for all Tech Blocks.
    Defines the essential interface for execution and metadata retrieval.
    """

    def __init__(self, block_id: str, version: str, config: Optional[Dict[str, Any]] = None):
        """
        Constructor for a TechBlock instance.
        Concrete implementations might take specific configuration at instantiation.

        Args:
            block_id (str): The unique ID of this block instance (might differ from manifest ID if configured).
            version (str): The version of this block instance.
            config (Optional[Dict[str, Any]]): Initial configuration for the block instance.
                                                 This is static config for the instance,
                                                 distinct from runtime config in TechBlockInput.
        """
        self._block_id = block_id
        self._version = version
        self._instance_config = config or {}

    @property
    def id(self) -> str:
        return self._block_id

    @property
    def version(self) -> str:
        return self._version

    @classmethod
    @abc.abstractmethod
    def get_class_manifest(cls) -> TechBlockManifest:
        """
        Returns the TechBlockManifest for this specific TechBlock class.
        This should be implemented by all concrete TechBlock subclasses.
        """
        pass

    @abc.abstractmethod
    async def execute(self, input_data: TechBlockInput, context: Optional[Dict[str, Any]] = None) -> TechBlockOutput:
        """
        Executes the core logic of the Tech Block.
        This method must be implemented by all concrete Tech Block classes.
        It should be designed to be potentially asynchronous if I/O operations are involved.

        Args:
            input_data (TechBlockInput): The standardized input payload.
                                         The 'data' field within should conform to this block's input_schema.
            context (Optional[Dict[str, Any]]): Optional execution context that might be provided by the
                                                calling Bus (e.g., user_id, session_id, access to shared services).

        Returns:
            TechBlockOutput: The standardized output payload, including the result and execution status.
        """
        pass

    def get_manifest(self) -> TechBlockManifest:
        return self.__class__.get_class_manifest()
