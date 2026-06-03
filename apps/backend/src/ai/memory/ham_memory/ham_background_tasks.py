import logging
import asyncio
from datetime import datetime
from typing import Any, List

logger = logging.getLogger(__name__)
from core.system.config.magic_numbers import loop_sleep


class HAMBackgroundTasks:
    def __init__(
        self,
        core_memory_store: Any,
        core_storage: Any,
        query_engine: Any,
        fernet: Any,
        next_memory_id: Any,
    ):
        self.core_memory_store = core_memory_store
        self.core_storage = core_storage
        self.query_engine = query_engine
        self.fernet = fernet
        self.next_memory_id = next_memory_id

    async def _delete_old_experiences(self) -> None:
        """
        Periodically deletes old experiences from memory based on:
        1. Age (memories older than threshold)
        2. Importance (low relevance scores)
        3. Access frequency (rarely accessed memories)

        Cleanup strategy:
        - Keep high importance memories (relevance >= 0.7) regardless of age
        - Keep protected memories regardless of age
        - Delete low importance memories (relevance < 0.3) older than 30 days
        - Delete medium importance memories (0.3 <= relevance < 0.7) older than 90 days
        - Always keep at least minimum number of recent memories
        """
        while True:
            await asyncio.sleep(loop_sleep("ham_hourly", 3600.0))  # Run once every hour
            logger.info("Running background task: Cleaning old experiences...")

            try:
                memories_to_delete = self._identify_memories_to_delete()
                memories_to_delete = self._trim_to_minimum(memories_to_delete)
                await self._execute_deletion(memories_to_delete)
            except Exception as e:  # broad exception acceptable: cleanup should not crash background task
                logger.error(f"Error during memory cleanup: {e}", exc_info=True)

            logger.info("Background task: Old experiences cleanup complete.")

    def _identify_memories_to_delete(self) -> List[str]:
        HIGH_IMPORTANCE_THRESHOLD = 0.7
        MEDIUM_IMPORTANCE_THRESHOLD = 0.3
        LOW_IMPORTANCE_AGE_DAYS = 30
        MEDIUM_IMPORTANCE_AGE_DAYS = 90
        memories_to_delete = []
        now = datetime.now()

        for mem_id, data_package in list(self.core_memory_store.items()):
            try:
                relevance = data_package.get("relevance", 0.5)
                metadata = data_package.get("metadata", {})
                protected = metadata.get("protected", False)

                if protected:
                    continue
                if relevance >= HIGH_IMPORTANCE_THRESHOLD:
                    continue

                timestamp_str = data_package.get("timestamp", "")
                if not timestamp_str:
                    continue

                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    age_days = (now - timestamp).days
                except ValueError:
                    logger.warning("Failed to parse timestamp '%s', skipping memory", timestamp_str, exc_info=True)
                    continue

                should_delete = False
                if relevance < MEDIUM_IMPORTANCE_THRESHOLD:
                    if age_days > LOW_IMPORTANCE_AGE_DAYS:
                        should_delete = True
                elif relevance < HIGH_IMPORTANCE_THRESHOLD:
                    if age_days > MEDIUM_IMPORTANCE_AGE_DAYS:
                        should_delete = True

                if should_delete:
                    memories_to_delete.append(mem_id)

            except Exception as e:
                logger.error(f"Error analyzing memory {mem_id} for deletion: {e}", exc_info=True)
                continue
        return memories_to_delete

    def _trim_to_minimum(self, memories_to_delete: List[str]) -> List[str]:
        MIN_MEMORIES_TO_KEEP = 100
        total_memories = len(self.core_memory_store)
        memories_to_keep = total_memories - MIN_MEMORIES_TO_KEEP

        if memories_to_keep > 0 and len(memories_to_delete) > memories_to_keep:
            memories_with_relevance = []
            for mem_id in memories_to_delete:
                if mem_id in self.core_memory_store:
                    relevance = self.core_memory_store[mem_id].get("relevance", 0.5)
                    memories_with_relevance.append((mem_id, relevance))
            memories_with_relevance.sort(key=lambda x: x[1])
            memories_to_delete = [m[0] for m in memories_with_relevance[:memories_to_keep]]
        return memories_to_delete

    async def _execute_deletion(self, memories_to_delete: List[str]) -> None:
        if memories_to_delete:
            logger.info(f"Deleting {len(memories_to_delete)} old memories...")
            for mem_id in memories_to_delete:
                try:
                    del self.core_memory_store[mem_id]
                    logger.debug(f"Deleted memory: {mem_id}")
                except KeyError:
                    logger.warning("Memory ID not found in store", exc_info=True)
            if hasattr(self.core_storage, "_save_core_memory_to_file"):
                await self.core_storage._save_core_memory_to_file(
                    self.core_memory_store, self.next_memory_id, self.fernet
                )
            logger.info(f"Successfully deleted {len(memories_to_delete)} old memories")
        else:
            logger.info("No memories qualified for deletion")
