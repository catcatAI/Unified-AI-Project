import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Tuple

from .ham_types import HAMDataPackageInternal, HAMMemory, HAMRecallResult
from .ham_vector_store_manager import HAMVectorStoreManager
from .ham_data_processor import HAMDataProcessor

logger = logging.getLogger(__name__)

class HAMQueryEngine:
    def __init__(self, core_memory_store: Dict[str, HAMDataPackageInternal], chroma_collection: Any, vector_store_manager: HAMVectorStoreManager, data_processor: HAMDataProcessor):
        self.core_memory_store = core_memory_store
        self.chroma_collection = chroma_collection
        self.vector_store_manager = vector_store_manager
        self.data_processor = data_processor

    def _normalize_date(self, date_input: Union[str, datetime]) -> datetime:
        if isinstance(date_input, str):
            try:
                # Attempt to parse with timezone info
                dt = datetime.fromisoformat(date_input)
                if dt.tzinfo is None:
                    # Assume UTC if no timezone info provided
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                # Fallback for simpler date strings, assume UTC
                return datetime.strptime(date_input, "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc)
        elif isinstance(date_input, datetime):
            if date_input.tzinfo is None:
                return date_input.replace(tzinfo=timezone.utc)
            return date_input
        raise ValueError("Invalid date input type")

    async def query_core_memory(self,
                                keywords: Optional[List[str]] = None,
                                data_type_filter: Optional[str] = None,
                                date_range: Optional[Tuple[datetime, datetime]] = None,
                                min_importance: float = 0.0,
                                limit: int = 10) -> List[HAMRecallResult]:
        """
        Queries the core memory based on various criteria.
        """
        results: List[HAMRecallResult] = []
        
        # Simple filtering for now, can be enhanced with more sophisticated search
        for mem_id, data_package in self.core_memory_store.items():
            match = True

            # Filter by data type
            if data_type_filter and data_type_filter not in data_package["data_type"]:
                match = False

            # Filter by importance
            if data_package.get("relevance", 0.0) < min_importance:
                match = False

            # Filter by date range
            if date_range:
                memory_timestamp = self._normalize_date(data_package["timestamp"])
                start_date, end_date = date_range
                if not (start_date <= memory_timestamp <= end_date):
                    match = False
            
            # Filter by keywords (simple check in gist for now)
            if keywords and match:
                try:
                    decrypted_data = self.data_processor._decrypt(data_package["encrypted_package"])
                    decompressed_data_bytes = self.data_processor._decompress(decrypted_data)
                    decompressed_data_str = decompressed_data_bytes.decode('utf-8')
                    
                    gist_content = ""
                    if "dialogue_text" in data_package["data_type"]:
                        abstracted_gist = json.loads(decompressed_data_str)
                        gist_content = abstracted_gist.get("gist", "")
                    else:
                        gist_content = decompressed_data_str # For other types, use raw decompressed string

                    keyword_match = False
                    for keyword in keywords:
                        if keyword.lower() in gist_content.lower():
                            keyword_match = True
                            break
                    if not keyword_match:
                        match = False
                except Exception as e:
                    logger.error(f"Error processing memory {mem_id} for keyword search: {e}")
                    match = False # Exclude if there's an error processing

            if match:
                results.append(HAMRecallResult(
                    memory_id=mem_id,
                    content=self.data_processor._rehydrate_text_gist(json.loads(decompressed_data_str)) if "dialogue_text" in data_package["data_type"] else decompressed_data_str,
                    score=data_package.get("relevance", 0.0),
                    timestamp=self._normalize_date(data_package["timestamp"]),
                    metadata=data_package["metadata"]
                ))
            
            if len(results) >= limit:
                break

        # Sort by relevance (descending)
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    async def retrieve_relevant_memories(self, query: str, limit: int = 10) -> List[HAMMemory]:
        """
        Retrieves memories semantically relevant to the query using the vector store.
        """
        if self.vector_store_manager.vector_store:
            # Assuming vector_store.query_memories returns a list of HAMMemory
            # with content, metadata, and a relevance score.
            # The query itself might need to be embedded first.
            # For now, this is a placeholder for actual semantic search.
            logger.info(f"Performing semantic search for query: '{query}'")
            # Mocking a result for now
            mock_results = []
            for i in range(min(limit, 3)): # Return up to 3 mock results
                mock_results.append(HAMMemory(
                    memory_id=f"semantic_mem_{i}",
                    content=f"This is a semantically relevant memory to '{query}' (mock data {i})",
                    metadata={"source": "semantic_search", "query": query},
                    relevance=0.9 - (i * 0.1)
                ))
            return mock_results
        else:
            logger.warning("Vector store not initialized. Cannot perform semantic search.")
            return []
