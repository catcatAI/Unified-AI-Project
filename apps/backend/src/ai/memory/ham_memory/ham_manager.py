import logging
import os
import asyncio
import json
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Tuple

# Required imports
from cryptography.fernet import Fernet

# Internal imports
from .ham_types import HAMDataPackageInternal, HAMMemory, HAMRecallResult, HAMMemoryError
from .ham_core_storage import HAMCoreStorage
from .ham_data_processor import HAMDataProcessor
from .ham_vector_store_manager import HAMVectorStoreManager
from .ham_importance_scorer import ImportanceScorer
from .ham_query_engine import HAMQueryEngine
from .ham_background_tasks import HAMBackgroundTasks

logger = logging.getLogger(__name__)


class HAMMemoryManager:
    """
    Manages the AI's Hierarchical Associative Memory system.
    """

    BASE_SAVE_DELAY_SECONDS = 0.1
    CONSOLIDATION_THRESHOLD_TOKENS = 5000 # 2030 Standard for rest trigger

    def __init__(
        self,
        resource_awareness_service: Optional[Any] = None,
        personality_manager: Optional[Any] = None,
        storage_dir: Optional[str] = None,
        core_storage_filename: str = "core_memory.json",
        chroma_client: Optional[Any] = None,
    ):
        # ... existing init code ...
        self.pending_tokens = 0 # Track data density for Sleep Cycle
        # Determine base path for data storage
        if storage_dir:
            self.storage_dir = storage_dir
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Corrected path logic to reach project root
            project_root: str = os.path.abspath(os.path.join(current_dir, "../../../../../"))
            self.storage_dir = os.path.join(project_root, "data", "processed_data")
        
        os.makedirs(self.storage_dir, exist_ok=True)
        self.personality_manager = personality_manager

        # Initialize Fernet for encryption
        key_str = os.environ.get("MIKO_HAM_KEY")
        self.fernet: Optional[Any] = None
        self.fernet_key: Optional[bytes] = None

        if key_str:
            self.fernet_key = key_str.encode()
            try:
                self.fernet = Fernet(self.fernet_key)
            except Exception as e:
                logger.critical(f"Failed to initialize Fernet: {e}")
                self.fernet = None
        else:
            logger.warning("MIKO_HAM_KEY not set. Generating a temporary key for this session.")
            try:
                self.fernet_key = Fernet.generate_key()
                self.fernet = Fernet(self.fernet_key)
            except Exception as e:
                logger.error(f"Failed to generate temporary key: {e}")
                self.fernet = None

        self.core_storage = HAMCoreStorage(
            self.storage_dir, core_storage_filename, resource_awareness_service
        )
        self.data_processor = HAMDataProcessor(fernet=self.fernet)
        self.vector_store_manager = HAMVectorStoreManager(self.storage_dir, chroma_client)
        self.importance_scorer = ImportanceScorer()

        self.core_memory_store: Dict[str, HAMDataPackageInternal] = {}
        self.next_memory_id: int = 0
        self.core_memory_store, self.next_memory_id = self.core_storage._load_core_memory_from_file(
            self.core_memory_store, self.next_memory_id, self.fernet
        )

        self.query_engine = HAMQueryEngine(
            self.core_memory_store,
            self.vector_store_manager.chroma_collection,
            self.vector_store_manager,
            self.data_processor,
        )
        self.background_tasks = HAMBackgroundTasks(
            self.core_memory_store,
            self.core_storage,
            self.query_engine,
            self.fernet,
            self.next_memory_id,
        )

        logger.info(f"HAMMemoryManager initialized. Storage: {self.storage_dir}")

        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self.background_tasks._delete_old_experiences())
        except RuntimeError:
            pass

    def _generate_memory_id(self) -> str:
        mem_id = f"mem_{self.next_memory_id:06d}"
        self.next_memory_id += 1
        return mem_id

    def close(self):
        self.vector_store_manager.close()

    async def store_experience(
        self, raw_data: Any, data_type: str, metadata: Optional[Dict[str, Any]] = None, is_strategic: bool = False
    ) -> Optional[str]:
        current_metadata = dict(metadata) if metadata else {}
        memory_id = self._generate_memory_id()
        
        # GSI-4 M5: Value-Driven Weighting
        if is_strategic:
            current_metadata["value_tier"] = "Strategic"
            current_metadata["protected"] = True
            current_metadata["importance_score"] = 0.95
            logger.info(f"💎 [M5] Strategic memory captured: {memory_id}")
        else:
            current_metadata["value_tier"] = "Standard"

        # ... rest of processing ...

        data_to_process: bytes
        if "dialogue_text" in data_type:
            abstracted_gist = self.data_processor._abstract_text(str(raw_data))
            data_to_process = json.dumps(abstracted_gist).encode("utf-8")
        else:
            data_to_process = str(raw_data).encode("utf-8")

        sha256_checksum = hashlib.sha256(data_to_process).hexdigest()
        current_metadata["sha256_checksum"] = sha256_checksum

        if current_metadata.get("importance_score") is None:
            current_metadata["importance_score"] = await self.importance_scorer.calculate(
                str(raw_data), current_metadata
            )

        await self.vector_store_manager.add_semantic_vector(
            memory_id=memory_id,
            content=str(raw_data),
            metadata=current_metadata,
        )

        try:
            compressed_data = self.data_processor._compress(data_to_process)
            encrypted_data = self.data_processor._encrypt(compressed_data)
        except Exception as e:
            raise Exception(f"Failed to store experience: {e}") from e

        data_package: HAMDataPackageInternal = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data_type": data_type,
            "encrypted_package": encrypted_data,
            "metadata": current_metadata,
            "relevance": 0.5,
            "protected": current_metadata.get("protected", False),
        }
        self.core_memory_store[memory_id] = data_package

        save_successful = await asyncio.to_thread(
            self.core_storage._save_core_memory_to_file,
            self.core_memory_store,
            self.next_memory_id,
            self.fernet,
        )
        return memory_id if save_successful else None

    async def store_emotional_memory(
        self, content: str, emotion: str, intensity: float, context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        emotional_metadata = {
            "type": "emotional",
            "emotion": emotion,
            "emotional_intensity": float(intensity),
            "importance_score": float(intensity * 0.8),
        }
        if context:
            for k, v in context.items():
                emotional_metadata[f"context_{k}"] = str(v)
        return await self.store_experience(content, "emotional_memory", emotional_metadata)

    def recall_gist(self, memory_id: str) -> Optional[HAMRecallResult]:
        data_package = self.core_memory_store.get(memory_id)
        if not data_package: return None

        try:
            decrypted_data = self.data_processor._decrypt(data_package["encrypted_package"])
            decompressed_data_bytes = self.data_processor._decompress(decrypted_data)
            decompressed_data_str = decompressed_data_bytes.decode("utf-8")
        except Exception: return None

        rehydrated_content = decompressed_data_str
        if "dialogue_text" in data_package["data_type"]:
            try:
                rehydrated_content = self.data_processor._rehydrate_text_gist(json.loads(decompressed_data_str))
            except Exception: pass

        return HAMRecallResult(
            memory_id=memory_id,
            content=rehydrated_content,
            score=0.0,
            timestamp=datetime.now(timezone.utc),
            metadata=data_package.get("metadata", {}),
        )

    async def consolidate_memories(self, limit: int = 50):
        """
        Consolidation Cycle (Sleep). 
        Turns multiple fragmented dialogue logs into summarized semantic gists.
        """
        recent_memories = await self.query_core_memory(data_type_filter="ai_dialogue_text", limit=limit)
        if len(recent_memories) < 10:
            return "Insufficient data for consolidation."

        logger.info(f"🌙 [HAM] Starting Sleep Cycle: Consolidating {len(recent_memories)} records.")
        
        # 1. Gather all texts
        combined_text = "\n".join([f"{m.metadata.get('speaker', 'Unknown')}: {m.content}" for m in recent_memories])
        
        # 2. Abstract (Using our processor)
        abstract = self.data_processor._abstract_text(combined_text)
        
        # 3. Store as a 'Long-term Gist'
        summary_id = await self.store_experience(
            raw_data=json.dumps(abstract), 
            data_type="long_term_gist", 
            metadata={"source": "consolidation_cycle", "count": len(recent_memories)}
        )
        
        # 4. Optional: Mark old ones as 'archived' or reduce their retrieval weight
        logger.info(f"✨ [HAM] Consolidation complete. New Gist ID: {summary_id}")
        return summary_id

    async def query_core_memory(
        self, keywords: Optional[List[str]] = None, data_type_filter: Optional[str] = None, limit: int = 10
    ) -> List[HAMRecallResult]:
        if self.query_engine:
            return await self.query_engine.query_core_memory(keywords, data_type_filter, limit)
        return []

    async def store_template(self, template) -> bool:
        try:
            content = json.dumps(template.to_dict(), ensure_ascii=False)
            metadata = {"data_type": "response_template", "template_id": template.id, "is_template": True}
            return await self.store_experience(content, "response_template", metadata) is not None
        except Exception: return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("HAMMemoryManager Module direct run.")
    metadata = {"data_type": "response_template", "template_id": template.id, "is_template": True}
            return await self.store_experience(content, "response_template", metadata) is not None
        except Exception: return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("HAMMemoryManager Module direct run.")
