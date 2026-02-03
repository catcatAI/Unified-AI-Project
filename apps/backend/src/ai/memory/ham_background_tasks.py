import asyncio
import logging
import psutil
from typing import Any, Dict

logger = logging.getLogger(__name__)

class HAMBackgroundTasks:
    def __init__(self, core_memory_store: Dict[str, Any], core_storage: Any, query_engine: Any, fernet: Any, next_memory_id: int):
        self.core_memory_store = core_memory_store
        self.core_storage = core_storage
        self.query_engine = query_engine
        self.fernet = fernet
        self.next_memory_id = next_memory_id

    async def _delete_old_experiences(self):
        """
        Deletes old experiences that are no longer relevant.
        """
        while True:
            # Ensure we don't check too frequently
            deletion_interval = max(60, 3600 - len(self.core_memory_store) * 10)
            await asyncio.sleep(deletion_interval)

            # Perform deletion check in a separate thread to avoid blocking
            try:
                await asyncio.to_thread(self._perform_deletion_check)
            except Exception as e:
                logger.error(f"Error during memory cleanup: {e}")
                # Continue with next iteration even if current check failed
                continue

    def _perform_deletion_check(self, memory_threshold: float = 0.1):
        """
        Checks for and deletes old / unprotected memories when memory usage is high.
        """
        try:
            # Check if memory usage is high
            memory_info = psutil.virtual_memory()
            if memory_info.available < memory_info.total * memory_threshold:
                # Identify memories to delete (unprotected, oldest / lowest relevance first)
                memories_to_consider = sorted(
                    [
                        (mem_id, data_pkg)
                        for mem_id, data_pkg in self.core_memory_store.items()
                        if not data_pkg.get("protected", False)
                    ],
                    key=lambda item: (item[1].get("relevance", 0.5), self.query_engine._normalize_date(item[1]["timestamp"]))
                )

                # Delete memories until memory usage is acceptable
                deleted_count = 0
                max_deletions_per_check = max(10, len(self.core_memory_store) // 10)  # Limit deletions per check

                for memory_id, _ in memories_to_consider:
                    # Safety check: don't delete too many memories at once
                    if deleted_count >= max_deletions_per_check:
                        logger.info(f"Memory deletion limit reached: {deleted_count} memories deleted")
                        break

                    current_memory = psutil.virtual_memory()
                    if current_memory.available < current_memory.total * memory_threshold:
                        if memory_id in self.core_memory_store:  # Ensure it still exists:
                            # Additional safety check: ensure we're not deleting protected memories
                            if not self.core_memory_store[memory_id].get("protected", False):
                                del self.core_memory_store[memory_id]
                                deleted_count += 1
                                logger.debug(f"Deleted memory: {memory_id}")
                            else:
                                logger.warning(f"Attempted to delete protected memory: {memory_id}")
                    else:
                        break

                if deleted_count > 0:
                    # Save the updated memory store to file
                    self.core_storage._save_core_memory_to_file(self.core_memory_store, self.next_memory_id, self.fernet)
                    logger.info(f"Memory cleanup completed: {deleted_count} memories deleted")
        except Exception as e:
            logger.error(f"Error during deletion check: {e}")
