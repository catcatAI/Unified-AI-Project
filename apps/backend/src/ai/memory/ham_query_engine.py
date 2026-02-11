import logging
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union, Tuple

from .ham_types import HAMMemory, HAMRecallResult, HAMDataPackageInternal, HAMMemoryError
from .vector_store import VectorMemoryStore

logger = logging.getLogger(__name__)

class HAMQueryEngine:
    def __init__(self, core_memory_store: Dict[str, HAMDataPackageInternal], chroma_collection: Optional[Any], vector_store: Optional[VectorMemoryStore], data_processor: Any):
        self.core_memory_store = core_memory_store
        self.chroma_collection = chroma_collection
        self.vector_store = vector_store
        self.data_processor = data_processor

    def _normalize_date(self, date_input: Any) -> datetime:
        """
        Normalizes various date inputs into a timezone - aware datetime object (UTC).
        """
        if isinstance(date_input, datetime):
            if date_input.tzinfo is None:
                return date_input.replace(tzinfo=timezone.utc())
            return date_input.astimezone(timezone.utc())
        elif isinstance(date_input, (int, float)): # Unix timestamp: 
            return datetime.fromtimestamp(date_input, tz=timezone.utc())
        elif isinstance(date_input, str):
            try:
                # Try parsing as ISO format first
                dt = datetime.fromisoformat(date_input)
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=timezone.utc())
                return dt.astimezone(timezone.utc())
            except ValueError:
                # Fallback for other common formats if necessary, or raise error
                raise ValueError(f"Could not parse date string: {date_input}. Expected ISO format.")
        else:
            raise TypeError(f"Unsupported date input type: {type(date_input)}")

    def _deserialize_memory(self, memory_id: str, data_package: HAMDataPackageInternal) -> HAMMemory:
        """反序列化內部數據包為 HAMMemory 物件。"""
        timestamp = data_package.get("timestamp", "")
        data_type = data_package.get("data_type", "")
        metadata = data_package.get("metadata", {})
        encrypted_package = data_package["encrypted_package"]

        try:
            decrypted_data = self.data_processor._decrypt(encrypted_package)
            decompressed_data_bytes = self.data_processor._decompress(decrypted_data)
            content = decompressed_data_bytes.decode('utf-8') # Assuming content is text for now
            # Verify checksum (similar to recall_gist)
            stored_checksum = metadata.get('sha256_checksum')
            if stored_checksum:
                current_checksum = hashlib.sha256(decompressed_data_bytes).hexdigest()
                if current_checksum != stored_checksum:
                    logger.critical(f"Checksum mismatch during deserialization for memory ID {memory_id}! Data may be corrupted.")
            # Convert timestamp to datetime object
            timestamp_obj: datetime
            if isinstance(timestamp, str):
                timestamp_obj = self._normalize_date(timestamp)
            else:
                timestamp_obj = timestamp

            return HAMMemory(
                id=memory_id,
                content=content,
                timestamp=timestamp_obj,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error deserializing memory {memory_id}: {e}")
            raise HAMMemoryError(f"Failed to deserialize memory {memory_id}: {e}")

    async def retrieve_relevant_memories(self, query: str, limit: int = 10) -> List[HAMMemory]:
        """
        Retrieves memories relevant to a given query using semantic search, and
        merges with a keyword - based search for a comprehensive recall.
        """
        logger.debug(f"HAM: Retrieving relevant memories for query: '{query}'")
        semantic_results_ids = set()
        semantic_memories: List[HAMMemory] = []
        fallback_semantic = False

        # 1. Perform Semantic Search
        if query and self.chroma_collection is not None:
            try:
                # Fetch more results from Chroma to allow for filtering and merging
                chroma_results = self.chroma_collection.query(
                    query_texts=[query],
                    n_results=limit * 2,  # Fetch more results from Chroma to allow for filtering
                    include=['metadatas', 'documents']
                )
                # Extract memory_ids from Chroma results
                if chroma_results and chroma_results['ids']:
                    for i, mem_id in enumerate(chroma_results['ids'][0]):
                        if mem_id in self.core_memory_store:
                            data_package = self.core_memory_store[mem_id]
                            try:
                                # Use the new _deserialize_memory method
                                semantic_memories.append(self._deserialize_memory(mem_id, data_package))
                                semantic_results_ids.add(mem_id)
                            except HAMMemoryError as e:
                                logger.warning(f"Skipping deserialization of memory {mem_id} from vector store due to error: {e}")

                logger.debug(f"Retrieved {len(semantic_memories)} semantic memories for query: '{query}'")
            except Exception as e:
                logger.error(f"Error during semantic search for query '{query}': {e}")
                # Fallback if semantic search fails, proceed with only keyword search
                fallback_semantic = True
        else:
            logger.info(f"Vector / Chroma store disabled or no query, skipping semantic search for query: '{query}'")
            fallback_semantic = True

        # 2. Perform Keyword Search (and potential metadata filters)
        keyword_memories: List[HAMMemory] = []
        for mem_id, data_package in self.core_memory_store.items():
            if mem_id in semantic_results_ids:
                continue # Skip memories already found by semantic search

            # Very basic keyword matching for now (e.g., in content or metadata if rehydrated / accessible)
            item_metadata = data_package.get("metadata")
            # A more advanced implementation would rehydrate content for keyword search
            if any(kw.lower() in str(item_metadata).lower() for kw in query.lower().split() if len(kw) > 2):
                try:
                    keyword_memories.append(self._deserialize_memory(mem_id, data_package))
                except HAMMemoryError as e:
                    logger.warning(f"Skipping deserialization of memory {mem_id} from keyword search due to error: {e}")

        logger.debug(f"Retrieved {len(keyword_memories)} keyword - based memories.")

        # 3. Combine and Sort Results
        combined_results = semantic_memories + keyword_memories

        # Sort by relevance (semantic score from Chroma is implicitly higher for semantic memories)
        # but we need a unified scoring or a simple time - based sort for combination)
        # For simplicity, let's sort by timestamp (newest first) for combined results
        # A more complex system would assign a combined relevance score
        combined_results.sort(key=lambda x: x.timestamp, reverse=True)

        # Apply the final limit
        final_results: List[HAMMemory] = combined_results[:limit]

        logger.info(f"Retrieved {len(final_results)} combined relevant memories for query: '{query}'")
        return final_results

    def query_by_date_range(self, start_date: datetime, end_date: datetime) -> List[HAMRecallResult]:
        """
        Query memories by date range.

        Args:
            start_date (datetime): Start date for the query.
            end_date (datetime): End date for the query.

        Returns:
            List[HAMRecallResult]: List of memories within the specified date range.
        """
        try:
            results: List[HAMRecallResult] = []
            for memory_id, data_package in self.core_memory_store.items():
                try:
                    memory_timestamp = self._normalize_date(data_package["timestamp"])
                    if start_date <= memory_timestamp <= end_date:
                        # Assuming recall_gist is still in HAMMemoryManager and can be called
                        # Or, if recall_gist is also moved, it would be self.query_engine.recall_gist
                        # For now, let's assume HAMMemoryManager will call this query engine
                        # and then recall gist itself.
                        # This needs careful handling of inter-module calls.
                        # For now, we'll just deserialize and return basic HAMMemory objects
                        # The full recall_gist logic will remain in HAMMemoryManager for now
                        # and will call this query engine.
                        results.append(self._deserialize_memory(memory_id, data_package))
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse timestamp for memory {memory_id} or date_range {start_date} - {end_date}: {e}. Skipping this memory for date filter.")
                    continue
            return results
        except Exception as e:
            logger.error(f"Failed to query date range: {e}")
            raise Exception(f"Failed to query date range: {e}")

    def query_core_memory(
                        self,
                        keywords: Optional[List[str]] = None,
                        date_range: Optional[Tuple[datetime, datetime]] = None,
                        data_type_filter: Optional[str] = None,
                        metadata_filters: Optional[Dict[str, Any]] = None,
                        user_id_for_facts: Optional[str] = None,
                        limit: int = 5,
                        sort_by_confidence: bool = False,
                        return_multiple_candidates: bool = False,
                        semantic_query: Optional[str] = None
                        ) -> List[HAMRecallResult]:
        """
        Enhanced query function.
        Filters by data_type, metadata_filters (exact matches), user_id (for facts),
    and date_range.
        Optional keyword search on metadata string.
        Does NOT search encrypted content for keywords in this version.
        """
        logger.debug(f"HAM: Querying core memory (type: {data_type_filter}, meta_filters: {metadata_filters}, keywords: {keywords}, semantic_query: {semantic_query})")

        candidate_mem_ids: List[str] = []
        fallback_semantic = False

        if semantic_query:
            if self.chroma_collection is None:
                logger.warning("ChromaDB collection not initialized. Cannot perform semantic search.")
                # Fallback to iterating all memories if semantic search is not available
                candidate_mem_ids = sorted(list(self.core_memory_store.keys()),
    reverse = True)
                fallback_semantic = True
            else:
                try:
                    # Generate embedding for the semantic query using the collection's embedding function
                    chroma_results = self.chroma_collection.query(
                        query_texts=[semantic_query],
                        n_results=limit * 2,  # Fetch more results from Chroma to allow for filtering
                        include=['metadatas', 'documents']
                    )
                    # Extract memory_ids from Chroma results
                    if chroma_results and chroma_results['ids']:
                        candidate_mem_ids.extend(chroma_results['ids'][0])
                    logger.debug(f"HAM: ChromaDB returned {len(candidate_mem_ids)} candidates for semantic query.")
                except Exception as e:
                    logger.error(f"Error querying ChromaDB: {e}")
                    # Fallback to iterating all memories if ChromaDB query fails
                    candidate_mem_ids = sorted(list(self.core_memory_store.keys()),
    reverse = True)
                    fallback_semantic = True
        else:
            # If no semantic query, iterate through all memories
            candidate_mem_ids = [mem_id for mem_id in self.core_memory_store.keys() if mem_id is not None]
            candidate_mem_ids = sorted(candidate_mem_ids, reverse = True)

        # Candidate selection: Iterate through selected memory IDs
        candidate_items_with_id: List[HAMRecallResult] = []

        for mem_id in candidate_mem_ids:
            item = self.core_memory_store.get(mem_id)
            if not item: # Skip if memory not found in core store (e.g., filtered by Chroma but not in JSON): 
                continue

            item_metadata = item.get("metadata", {})
            match = True

            if data_type_filter:
                # Allow partial match for data_type_filter (e.g., "learned_fact_", matches all learned facts)
                if not item.get("data_type", "").startswith(data_type_filter):
                    match = False

            if match and date_range:
                try:
                    item_dt = self._normalize_date(item["timestamp"])
                    start_dt_normalized = self._normalize_date(date_range[0])
                    end_dt_normalized = self._normalize_date(date_range[1])

                    if not (start_dt_normalized <= item_dt <= end_dt_normalized):
                        match = False
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error parsing date for memory {mem_id} or date_range {date_range}: {e}. Skipping this memory for date filter.")
                    match = False # Treat as non - match if date parsing fails

            if match and metadata_filters:
                for key, value in metadata_filters.items():
                    # Support nested keys like "original_source_info.type" if needed, but simple for now,
                    if item_metadata.get(key) != value:
                        match = False
                        break

            if match and user_id_for_facts and data_type_filter and \
    data_type_filter.startswith("learned_fact"):
                if item_metadata.get("user_id") != user_id_for_facts:
                    match = False

            if match and keywords:
                metadata_str = str(item_metadata).lower()
                if not all(keyword.lower() in metadata_str for keyword in keywords):
                    match = False

            if match:
                # Assuming recall_gist is still in HAMMemoryManager and can be called
                # Or, if recall_gist is also moved, it would be self.query_engine.recall_gist
                # For now, we'll just deserialize and return basic HAMMemory objects
                # The full recall_gist logic will remain in HAMMemoryManager for now
                # and will call this query engine.
                recalled_item = self._deserialize_memory(mem_id, item)
                if recalled_item: # recall_gist now returns Optional[HAMRecallResult]:
                    # recalled_item already includes metadata if successful
                    candidate_items_with_id.append(recalled_item)

        # Apply fallback semantic ranking when needed
        if semantic_query and fallback_semantic and candidate_items_with_id:
            def _fallback_score(rec: HAMRecallResult) -> int:
                text = str(rec.content).lower()
                gist_tokens = {tok.strip('.,!?') for tok in text.split() if len(tok.strip('., !?')) > 2}
                return len(query_tokens.intersection(gist_tokens))
            query_tokens = {tok.strip('.,!?') for tok in semantic_query.lower().split() if len(tok.strip('., !?')) > 2}
            # Sort by score desc, then by timestamp (newest first)
            candidate_items_with_id.sort(
                key=lambda x: (_fallback_score(x), x.timestamp),
                reverse=True
            )

        # Sort by confidence if requested (primarily for facts)
        if sort_by_confidence and data_type_filter and \
    data_type_filter.startswith("learned_fact"):
            candidate_items_with_id.sort(key=lambda x: x.metadata.get("confidence", 0.0), reverse=True)

        # Apply limit
        results: List[HAMRecallResult] = candidate_items_with_id[:limit]

        if return_multiple_candidates:
            return results

        logger.debug(f"HAM: Query returned {len(results)} results (limit was {limit}).")
        return results
