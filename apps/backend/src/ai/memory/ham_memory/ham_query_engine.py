import json
import logging
import re
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
            
            # Initialize variables
            decompressed_data_str: str = ""
            gist_content: str = ""
            
            # Filter by keywords (simple check in gist for now)
            if keywords and match:
                try:
                    decrypted_data = self.data_processor._decrypt(data_package["encrypted_package"])
                    decompressed_data_bytes = self.data_processor._decompress(decrypted_data)
                    decompressed_data_str = decompressed_data_bytes.decode('utf-8')
                    
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

            if match and decompressed_data_str:
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
        
        Args:
            query: The search query string
            limit: Maximum number of results to return
            
        Returns:
            List of semantically relevant memories with relevance scores
        """
        if not self.vector_store_manager.vector_store:
            logger.warning("Vector store not initialized. Cannot perform semantic search.")
            # Fallback to keyword-based search in core memory
            return await self._fallback_keyword_search(query, limit)
        
        try:
            logger.info(f"Performing semantic search for query: '{query}'")
            
            # Embed the query using the vector store
            query_embedding = await self.vector_store_manager.embed_text(query)
            
            if query_embedding is None:
                logger.error("Failed to embed query for semantic search")
                return await self._fallback_keyword_search(query, limit)
            
            # Query the vector store for similar memories
            results = await self.vector_store_manager.query_similar(
                query_embedding=query_embedding,
                n_results=limit
            )
            
            if not results:
                logger.info("No semantic matches found, falling back to keyword search")
                return await self._fallback_keyword_search(query, limit)
            
            # Convert vector store results to HAMMemory format
            memories = []
            for result in results:
                memory_id = result.get("id")
                
                # Retrieve full memory from core storage if available
                if memory_id and memory_id in self.core_memory_store:
                    data_package = self.core_memory_store[memory_id]
                    
                    try:
                        decrypted_data = self.data_processor._decrypt(data_package["encrypted_package"])
                        decompressed_data_bytes = self.data_processor._decompress(decrypted_data)
                        decompressed_data_str = decompressed_data_bytes.decode('utf-8')
                        
                        # Parse the data based on type
                        if "dialogue_text" in data_package["data_type"]:
                            abstracted = json.loads(decompressed_data_str)
                            content = self.data_processor._rehydrate_text_gist(abstracted)
                        else:
                            content = decompressed_data_str
                        
                        memories.append(HAMMemory(
                            memory_id=memory_id,
                            content=content,
                            metadata=data_package.get("metadata", {}),
                            relevance=result.get("distance", 0.0)  # Distance-based relevance
                        ))
                        
                    except Exception as e:
                        logger.error(f"Error processing memory {memory_id}: {e}")
                        continue
            
            logger.info(f"Semantic search returned {len(memories)} results")
            return memories[:limit]
            
        except Exception as e:
            logger.error(f"Error during semantic search: {e}")
            return await self._fallback_keyword_search(query, limit)

    async def _fallback_keyword_search(self, query: str, limit: int = 10) -> List[HAMMemory]:
        """
        Fallback keyword-based search when vector store is unavailable.
        
        Args:
            query: The search query string
            limit: Maximum number of results to return
            
        Returns:
            List of keyword-matching memories with relevance scores
        """
        logger.info(f"Performing fallback keyword search for query: '{query}'")
        
        # Extract keywords from query
        query_words = set(re.findall(r'\b[a-zA-Z\u4e00-\u9fff]{2,}\b', query.lower()))
        
        if not query_words:
            return []
        
        results = []
        
        for mem_id, data_package in self.core_memory_store.items():
            try:
                decrypted_data = self.data_processor._decrypt(data_package["encrypted_package"])
                decompressed_data_bytes = self.data_processor._decompress(decrypted_data)
                decompressed_data_str = decompressed_data_bytes.decode('utf-8')
                
                # Get content
                if "dialogue_text" in data_package["data_type"]:
                    abstracted = json.loads(decompressed_data_str)
                    content = abstracted.get("gist", "") + " " + " ".join(abstracted.get("keywords", []))
                else:
                    content = decompressed_data_str
                
                # Calculate keyword match score
                content_lower = content.lower()
                match_count = sum(1 for word in query_words if word in content_lower)
                
                if match_count > 0:
                    # Calculate relevance based on match ratio
                    relevance = min(1.0, match_count / max(1, len(query_words)))
                    
                    # Apply stored relevance
                    stored_relevance = data_package.get("relevance", 0.5)
                    final_score = (relevance * 0.7) + (stored_relevance * 0.3)
                    
                    results.append(HAMMemory(
                        memory_id=mem_id,
                        content=self.data_processor._rehydrate_text_gist(abstracted) if "dialogue_text" in data_package["data_type"] else decompressed_data_str[:200],
                        metadata=data_package.get("metadata", {}),
                        relevance=final_score
                    ))
                    
            except Exception as e:
                logger.error(f"Error processing memory {mem_id} in keyword search: {e}")
                continue
        
        # Sort by relevance and return top results
        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results[:limit]
