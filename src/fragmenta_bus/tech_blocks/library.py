from typing import Dict, Type, Optional, List
from ..common.tech_block_interface import TechBlock
from ..common.data_models import TechBlockManifest

class TechBlockRegistrationError(Exception):
    pass

class TechBlockNotFoundError(Exception):
    pass

class TechBlockLibrary:
    """
    Manages the registration and retrieval of TechBlock classes.
    It stores TechBlock classes, not instances.
    The key for the registry is the TechBlock manifest ID.
    """
    _registry: Dict[str, Type[TechBlock]]

    def __init__(self):
        self._registry = {}

    @staticmethod
    def get_manifest_id_from_class(block_class: Type[TechBlock]) -> str:
        """
        Helper static method to retrieve the manifest ID from a TechBlock class.
        This assumes TechBlock classes have a way to expose their manifest's ID,
        ideally via a class method like `get_class_manifest()`.
        """
        if not hasattr(block_class, 'get_class_manifest'):
            raise TechBlockRegistrationError(
                f"TechBlock class {block_class.__name__} must have a 'get_class_manifest' class method."
            )
        manifest = block_class.get_class_manifest()
        block_id = manifest.get("id")
        if not block_id:
            raise TechBlockRegistrationError(
                f"TechBlock class {block_class.__name__} manifest is missing an 'id'."
            )
        return block_id

    def register_block(self, block_class: Type[TechBlock]) -> None:
        """
        Registers a TechBlock class with the library.
        The manifest ID is used as the key.

        Args:
            block_class (Type[TechBlock]): The TechBlock class to register.

        Raises:
            TechBlockRegistrationError: If the class is not a valid TechBlock,
                                        if its manifest ID cannot be retrieved,
                                        or if a block with the same ID is already registered.
        """
        if not issubclass(block_class, TechBlock):
            raise TechBlockRegistrationError(
                f"Class {block_class.__name__} is not a subclass of TechBlock."
            )

        try:
            block_id = self.get_manifest_id_from_class(block_class)
        except TechBlockRegistrationError as e:
            raise e
        except Exception as e:
            raise TechBlockRegistrationError(
                f"Unexpected error getting manifest ID for {block_class.__name__}: {e}"
            )

        if block_id in self._registry:
            raise TechBlockRegistrationError(
                f"TechBlock with ID '{block_id}' (from class {block_class.__name__}) is already registered."
            )

        self._registry[block_id] = block_class

    def get_block_class(self, block_id: str) -> Type[TechBlock]:
        """
        Retrieves a registered TechBlock class by its manifest ID.

        Args:
            block_id (str): The manifest ID of the TechBlock class to retrieve.

        Returns:
            Type[TechBlock]: The registered TechBlock class.

        Raises:
            TechBlockNotFoundError: If no TechBlock with the given ID is found.
        """
        block_class = self._registry.get(block_id)
        if not block_class:
            raise TechBlockNotFoundError(f"TechBlock with ID '{block_id}' not found in library.")
        return block_class

    def list_available_blocks(self) -> List[TechBlockManifest]:
        """
        Lists the manifests of all available Tech Blocks.
        """
        available_manifests = []
        for block_class in self._registry.values():
            try:
                manifest = block_class.get_class_manifest()
                available_manifests.append(manifest)
            except Exception:
                available_manifests.append(TechBlockManifest(id=f"error_retrieving_manifest_for_{block_class.__name__}", name="Error", version="N/A", description="Could not retrieve manifest", input_schema={}, output_schema={}))
        return available_manifests

    def clear(self) -> None:
        """Clears all registered blocks. Useful for testing."""
        self._registry.clear()
