import logging
import os
import asyncio
import json
import hashlib
import base64
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Tuple

# Required imports
from cryptography.fernet import Fernet

# Internal imports using absolute paths
from ai.memory.ham_memory.ham_types import HAMDataPackageInternal, HAMRecallResult
from ai.memory.ham_memory.ham_core_storage import HAMCoreStorage
from ai.memory.ham_memory.ham_data_processor import HAMDataProcessor
from ai.memory.ham_memory.ham_vector_store_manager import HAMVectorStoreManager
from ai.memory.ham_memory.ham_importance_scorer import ImportanceScorer
from ai.memory.ham_memory.ham_query_engine import HAMQueryEngine
from ai.memory.ham_memory.ham_background_tasks import HAMBackgroundTasks

logger = logging.getLogger(__name__)

class HAMMemoryManager:
    """
    Manages the AI's Hierarchical Associative Memory system.
    """
    BASE_SAVE_DELAY_SECONDS = 0.1
    CONSOLIDATION_THRESHOLD_TOKENS = 5000

    def __init__(
        self,
        resource_awareness_service: Optional[Any] = None,
        personality_manager: Optional[Any] = None,
        storage_dir: Optional[str] = None,
        core_storage_filename: str = "core_memory.json",
        chroma_client: Optional[Any] = None,
    ):
        if storage_dir:
            self.storage_dir = storage_dir
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root: str = os.path.abspath(os.path.join(current_dir, "../../../../../"))
            self.storage_dir = os.path.join(project_root, "data", "processed_data")
        
        os.makedirs(self.storage_dir, exist_ok=True)
        self.personality_manager = personality_manager
        self.pending_tokens = 0

        key_path = os.path.join(self.storage_dir, ".soul.key")
        key_str = os.environ.get("MIKO_HAM_KEY")
        
        if not key_str and os.path.exists(key_path):
            with open(key_path, "rb") as f:
                key_str = f.read().decode()
                logger.info("🔑 [Memory] Soul Key loaded from persistent storage.")

        self.fernet: Optional[Any] = None
        if key_str:
            try:
                self.fernet = Fernet(key_str.encode())
            except Exception: self.fernet = None
        
        if self.fernet is None:
            # Generate and PERSIST a new key
            new_key = Fernet.generate_key()
            self.fernet = Fernet(new_key)
            with open(key_path, "wb") as f:
                f.write(new_key)
            logger.warning("✨ [Memory] New Soul Key generated and persisted. Do not delete .soul.key!")

        self.core_storage = HAMCoreStorage(self.storage_dir, core_storage_filename, resource_awareness_service)
        self.data_processor = HAMDataProcessor(fernet=self.fernet)
        self.vector_store_manager = HAMVectorStoreManager(self.storage_dir, chroma_client)
        self.importance_scorer = ImportanceScorer()

        self.core_memory_store: Dict[str, HAMDataPackageInternal] = {}
        self.next_memory_id: int = 0
        self.core_memory_store, self.next_memory_id = self.core_storage._load_core_memory_from_file(
            self.core_memory_store, self.next_memory_id, self.fernet
        )

        self.query_engine = HAMQueryEngine(self.core_memory_store, self.vector_store_manager.chroma_collection, self.vector_store_manager, self.data_processor)
        self.background_tasks = HAMBackgroundTasks(self.core_memory_store, self.core_storage, self.query_engine, self.fernet, self.next_memory_id)

        logger.info(f"HAMMemoryManager initialized.")

    async def initialize(self):
        """Async initialization for Memory systems."""
        logger.info("[Memory] Hierarchical Associative Memory online.")
        return True

    def _generate_memory_id(self) -> str:
        mem_id = f"mem_{self.next_memory_id:06d}"
        self.next_memory_id += 1
        return mem_id

    async def store_experience(self, raw_data: Any, data_type: str, metadata: Optional[Dict[str, Any]] = None, is_strategic: bool = False) -> Optional[str]:
        current_metadata = dict(metadata) if metadata else {}
        memory_id = self._generate_memory_id()
        
        if is_strategic:
            current_metadata["value_tier"] = "Strategic"
            current_metadata["protected"] = True
            current_metadata["importance_score"] = 0.95
        
        data_to_process: bytes = str(raw_data).encode("utf-8")
        if "dialogue_text" in data_type:
            try:
                abstracted = self.data_processor._abstract_text(str(raw_data))
                data_to_process = json.dumps(abstracted).encode("utf-8")
            except Exception: pass

        if current_metadata.get("importance_score") is None:
            current_metadata["importance_score"] = await self.importance_scorer.calculate(str(raw_data), current_metadata)

        await self.vector_store_manager.add_semantic_vector(memory_id=memory_id, content=str(raw_data), metadata=current_metadata)

        # Encode bytes to Base64 for JSON serialization
        encrypted_bytes = self.data_processor._encrypt(self.data_processor._compress(data_to_process))
        encoded_payload = base64.b64encode(encrypted_bytes).decode("utf-8")

        data_package: HAMDataPackageInternal = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data_type": data_type,
            "encrypted_package": encoded_payload,
            "metadata": current_metadata,
            "relevance": 0.5,
            "protected": current_metadata.get("protected", False),
        }
        self.core_memory_store[memory_id] = data_package
        
        # Token density trigger
        self.pending_tokens += len(str(raw_data))
        if self.pending_tokens >= self.CONSOLIDATION_THRESHOLD_TOKENS:
            asyncio.create_task(self.consolidate_memories())
            self.pending_tokens = 0

        return memory_id if await asyncio.to_thread(self.core_storage._save_core_memory_to_file, self.core_memory_store, self.next_memory_id, self.fernet) else None

    async def consolidate_memories(self, limit: int = 50):
        recent = await self.query_core_memory(data_type_filter="ai_dialogue_text", limit=limit)
        if len(recent) < 5: return None
        combined = "\n".join([f"{m.metadata.get('speaker', 'Unknown')}: {m.content}" for m in recent])
        abstract = self.data_processor._abstract_text(combined)
        return await self.store_experience(json.dumps(abstract), "long_term_gist", {"source": "consolidation"}, is_strategic=True)

    async def query_core_memory(self, keywords: Optional[List[str]] = None, data_type_filter: Optional[str] = None, limit: int = 10) -> List[HAMRecallResult]:
        if self.query_engine: return await self.query_engine.query_core_memory(keywords, data_type_filter, limit)
        return []

    async def store_template(self, template) -> bool:
        try:
            content = json.dumps(template.to_dict(), ensure_ascii=False)
            return await self.store_experience(content, "response_template", {"is_template": True}) is not None
        except Exception: return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("HAM Ready.")
