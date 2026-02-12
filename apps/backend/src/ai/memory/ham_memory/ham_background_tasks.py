import logging
import asyncio
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

class HAMBackgroundTasks:
    def __init__(self, core_memory_store: Any, core_storage: Any, query_engine: Any, fernet: Any, next_memory_id: Any):
        self.core_memory_store = core_memory_store
        self.core_storage = core_storage
        self.query_engine = query_engine
        self.fernet = fernet
        self.next_memory_id = next_memory_id

    async def _delete_old_experiences(self):
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
            await asyncio.sleep(3600)  # Run once every hour
            logger.info("Running background task: Cleaning old experiences...")
            
            try:
                memories_to_delete = []
                now = datetime.now()
                
                # Configuration thresholds
                HIGH_IMPORTANCE_THRESHOLD = 0.7
                MEDIUM_IMPORTANCE_THRESHOLD = 0.3
                LOW_IMPORTANCE_AGE_DAYS = 30
                MEDIUM_IMPORTANCE_AGE_DAYS = 90
                MIN_MEMORIES_TO_KEEP = 100  # Always keep at least this many memories
                
                # Analyze each memory
                for mem_id, data_package in list(self.core_memory_store.items()):
                    try:
                        # Get memory metadata
                        relevance = data_package.get("relevance", 0.5)
                        metadata = data_package.get("metadata", {})
                        protected = metadata.get("protected", False)
                        
                        # Skip protected memories
                        if protected:
                            continue
                        
                        # Skip high importance memories
                        if relevance >= HIGH_IMPORTANCE_THRESHOLD:
                            continue
                        
                        # Get memory age
                        timestamp_str = data_package.get("timestamp", "")
                        if not timestamp_str:
                            continue
                        
                        try:
                            timestamp = datetime.fromisoformat(timestamp_str)
                            age_days = (now - timestamp).days
                        except ValueError:
                            continue
                        
                        # Apply deletion rules
                        should_delete = False
                        
                        if relevance < MEDIUM_IMPORTANCE_THRESHOLD:
                            # Low importance - delete if older than threshold
                            if age_days > LOW_IMPORTANCE_AGE_DAYS:
                                should_delete = True
                        elif relevance < HIGH_IMPORTANCE_THRESHOLD:
                            # Medium importance - delete if much older
                            if age_days > MEDIUM_IMPORTANCE_AGE_DAYS:
                                should_delete = True
                        
                        if should_delete:
                            memories_to_delete.append(mem_id)
                            
                    except Exception as e:
                        logger.error(f"Error analyzing memory {mem_id} for deletion: {e}")
                        continue
                
                # Ensure we keep minimum number of memories
                total_memories = len(self.core_memory_store)
                memories_to_keep = total_memories - MIN_MEMORIES_TO_KEEP
                
                if memories_to_keep > 0 and len(memories_to_delete) > memories_to_keep:
                    # Sort by relevance (delete lowest relevance first)
                    memories_with_relevance = []
                    for mem_id in memories_to_delete:
                        if mem_id in self.core_memory_store:
                            relevance = self.core_memory_store[mem_id].get("relevance", 0.5)
                            memories_with_relevance.append((mem_id, relevance))
                    
                    memories_with_relevance.sort(key=lambda x: x[1])
                    memories_to_delete = [m[0] for m in memories_with_relevance[:memories_to_keep]]
                
                # Delete selected memories
                if memories_to_delete:
                    logger.info(f"Deleting {len(memories_to_delete)} old memories...")
                    for mem_id in memories_to_delete:
                        try:
                            del self.core_memory_store[mem_id]
                            logger.debug(f"Deleted memory: {mem_id}")
                        except KeyError:
                            pass  # Memory already deleted
                    
                    # Save updated core memory to file
                    if hasattr(self.core_storage, '_save_core_memory_to_file'):
                        await self.core_storage._save_core_memory_to_file(
                            self.core_memory_store,
                            self.next_memory_id,
                            self.fernet
                        )
                    
                    logger.info(f"Successfully deleted {len(memories_to_delete)} old memories")
                else:
                    logger.info("No memories qualified for deletion")
                    
            except Exception as e:
                logger.error(f"Error during memory cleanup: {e}")
                
            logger.info("Background task: Old experiences cleanup complete.")
