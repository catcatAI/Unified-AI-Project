from typing import Dict, Any, Optional, List
from ...common.tech_block_interface import TechBlock
from ...common.data_models import TechBlockInput, TechBlockOutput, TechBlockManifest
from src.core_ai.memory.ham_memory_manager import HAMMemoryManager
from src.shared.types.common_types import DialogueMemoryEntryMetadata, HAMRecallResult

class HAMStoreBlock(TechBlock):
    """
    A TechBlock that stores an experience in HAMMemoryManager.
    """
    def __init__(self, block_id: str, version: str, config: Optional[Dict[str, Any]] = None, ham_manager: Optional[HAMMemoryManager] = None):
        super().__init__(block_id, version, config)
        self.ham_manager = ham_manager
        if not self.ham_manager:
            raise ValueError("HAMStoreBlock requires an initialized HAMMemoryManager instance.")

    @classmethod
    def get_class_manifest(cls) -> TechBlockManifest:
        return TechBlockManifest(
            id="ham.store.v1",
            name="HAM Store Block",
            version="1.0.0",
            description="Stores an experience in the Hierarchical Associative Memory (HAM).",
            input_schema={
                "type": "object",
                "properties": {
                    "raw_data": {"type": "string", "description": "The raw data to store.", "min_length": 1},
                    "data_type": {"type": "string", "description": "The type of data (e.g., dialogue_text, fact).", "min_length": 1},
                    "metadata": {"type": "object", "description": "Optional metadata for the experience.", "default": {}}
                },
                "required": ["raw_data", "data_type"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "string", "description": "The memory ID of the stored experience.", "min_length": 1}
                },
                "required": ["result"]
            },
            tags=["memory", "ham", "storage"]
        )

    async def execute(self, input_data: TechBlockInput, context: Optional[Dict[str, Any]] = None) -> TechBlockOutput:
        raw_data = input_data.get("data", {}).get("raw_data")
        data_type = input_data.get("data", {}).get("data_type")
        metadata = input_data.get("data", {}).get("metadata", {})

        if not raw_data or not data_type:
            return TechBlockOutput(result=None, status="error", error_message="raw_data and data_type are required for HAMStoreBlock.")

        try:
            memory_id = await self.ham_manager.store_experience(raw_data, data_type, metadata=metadata)
            if memory_id:
                return TechBlockOutput(result=memory_id, status="success", error_message=None)
            else:
                return TechBlockOutput(result=None, status="error", error_message="Failed to store experience in HAM.")
        except Exception as e:
            return TechBlockOutput(result=None, status="error", error_message=f"Error storing in HAM: {e}")

class HAMRecallBlock(TechBlock):
    """
    A TechBlock that recalls an experience from HAMMemoryManager.
    """
    def __init__(self, block_id: str, version: str, config: Optional[Dict[str, Any]] = None, ham_manager: Optional[HAMMemoryManager] = None):
        super().__init__(block_id, version, config)
        self.ham_manager = ham_manager
        if not self.ham_manager:
            raise ValueError("HAMRecallBlock requires an initialized HAMMemoryManager instance.")

    @classmethod
    def get_class_manifest(cls) -> TechBlockManifest:
        return TechBlockManifest(
            id="ham.recall.v1",
            name="HAM Recall Block",
            version="1.0.0",
            description="Recalls an experience from the Hierarchical Associative Memory (HAM) by ID.",
            input_schema={
                "type": "object",
                "properties": {
                    "memory_id": {"type": "string", "description": "The memory ID to recall.", "min_length": 1}
                },
                "required": ["memory_id"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "object", "description": "The recalled HAMRecallResult object."}
                },
                "required": ["result"]
            },
            tags=["memory", "ham", "recall"]
        )

    async def execute(self, input_data: TechBlockInput, context: Optional[Dict[str, Any]] = None) -> TechBlockOutput:
        memory_id = input_data.get("data", {}).get("memory_id")

        if not memory_id:
            return TechBlockOutput(result=None, status="error", error_message="memory_id is required for HAMRecallBlock.")

        try:
            recalled_item = await self.ham_manager.recall_gist(memory_id)
            if recalled_item:
                return TechBlockOutput(result=recalled_item, status="success", error_message=None)
            else:
                return TechBlockOutput(result=None, status="error", error_message=f"Memory ID '{memory_id}' not found or recall failed.")
        except Exception as e:
            return TechBlockOutput(result=None, status="error", error_message=f"Error recalling from HAM: {e}")
