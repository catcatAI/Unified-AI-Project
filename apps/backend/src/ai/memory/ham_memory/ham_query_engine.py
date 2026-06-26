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
    def __init__(
        self,
        core_memory_store: Dict[str, HAMDataPackageInternal],
        chroma_collection: Any,
        vector_store_manager: HAMVectorStoreManager,
        data_processor: HAMDataProcessor,
    ):
        self.core_memory_store = core_memory_store
        self.chroma_collection = chroma_collection
        self.vector_store_manager = vector_store_manager
        self.data_processor = data_processor

    def _normalize_date(self, date_input: Union[str, datetime]) -> datetime:
        """Normalize date."""
        if isinstance(date_input, str):
            try:
                # Attempt to parse with timezone info
                dt = datetime.fromisoformat(date_input)
                if dt.tzinfo is None:
                    # Assume UTC if no timezone info provided
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                logger.warning(f"Date parse failed for {date_input}, trying fallback format", exc_info=True)
                # Fallback for simpler date strings, assume UTC
                return datetime.strptime(date_input, "%Y-%m-%dT%H:%M:%S.%f").replace(
                    tzinfo=timezone.utc
                )
        elif isinstance(date_input, datetime):
            if date_input.tzinfo is None:
                return date_input.replace(tzinfo=timezone.utc)
            return date_input
        raise ValueError("Invalid date input type")

    def _check_basic_filters(
        self, data_package: Dict[str, Any], data_type_filter: Optional[str],
        min_importance: float, date_range: Optional[Tuple[datetime, datetime]]
    ) -> bool:
        """Check basic filters."""
        if data_type_filter and data_type_filter not in data_package["data_type"]:
            return False
        if data_package.get("relevance", 0.0) < min_importance:
            return False
        if date_range:
            memory_timestamp = self._normalize_date(data_package["timestamp"])
            start_date, end_date = date_range
            if not (start_date <= memory_timestamp <= end_date):
                return False
        return True

    def _search_keywords_in_memory(
        self, data_package: Dict[str, Any], keywords: List[str]
    ) -> tuple:
        """Search keywords in memory."""
        decompressed_data_str = ""
        try:
            decrypted_data = self.data_processor._decrypt(data_package["encrypted_package"])
            decompressed_data_bytes = self.data_processor._decompress(decrypted_data)
            decompressed_data_str = decompressed_data_bytes.decode("utf-8")
            gist_content = self._extract_gist(data_package, decompressed_data_str)
            keyword_match = any(keyword.lower() in gist_content.lower() for keyword in keywords)
            return decompressed_data_str, keyword_match
        except Exception:
            logger.warning("Keyword search decryption failed, trying base64 fallback", exc_info=True)
            try:
                import base64
                decoded_payload = base64.b64decode(data_package["encrypted_package"])
                decrypted_data = self.data_processor._decrypt(decoded_payload)
                decompressed_data_bytes = self.data_processor._decompress(decrypted_data)
                decompressed_data_str = decompressed_data_bytes.decode("utf-8")
                gist_content = self._extract_gist(data_package, decompressed_data_str)
                keyword_match = any(keyword.lower() in gist_content.lower() for keyword in keywords)
                return decompressed_data_str, keyword_match
            except Exception as e:
                logger.error(f"Error processing memory for keyword search: {e} (Fallback also failed)", exc_info=True)
                return "", False

    def _extract_gist(self, data_package: Dict[str, Any], decompressed_data_str: str) -> str:
        """Extract gist."""
        if "dialogue_text" in data_package["data_type"]:
            abstracted_gist = json.loads(decompressed_data_str)
            return abstracted_gist.get("gist", "")
        return decompressed_data_str

    async def query_core_memory(
        self,
        keywords: Optional[List[str]] = None,
        data_type_filter: Optional[str] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        min_importance: float = 0.0,
        limit: int = 10,
    ) -> List[HAMRecallResult]:
        """
        Queries the core memory based on various criteria.
        """
        results: List[HAMRecallResult] = []

        for mem_id, data_package in self.core_memory_store.items():
            match = self._check_basic_filters(data_package, data_type_filter, min_importance, date_range)

            decompressed_data_str = ""

            if keywords and match:
                decompressed_data_str, keyword_match = self._search_keywords_in_memory(data_package, keywords)
                if not keyword_match:
                    match = False

            if match and decompressed_data_str:
                results.append(
                    HAMRecallResult(
                        memory_id=mem_id,
                        content=(
                            self.data_processor._rehydrate_text_gist(
                                json.loads(decompressed_data_str)
                            )
                            if "dialogue_text" in data_package["data_type"]
                            else decompressed_data_str
                        ),
                        score=data_package.get("relevance", 0.0),
                        timestamp=self._normalize_date(data_package["timestamp"]),
                        metadata=data_package["metadata"],
                    )
                )

            if len(results) >= limit:
                break

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
            logger.warning("Vector store not initialized. Cannot perform semantic search.", exc_info=True)
            # Fallback to keyword-based search in core memory
            return await self._fallback_keyword_search(query, limit)

        try:
            logger.info(f"Performing semantic search for query: '{query}'")

            # Embed the query using the vector store
            query_embedding = await self.vector_store_manager.embed_text(query)

            if query_embedding is None:
                logger.error("Failed to embed query for semantic search", exc_info=True)
                return await self._fallback_keyword_search(query, limit)

            # Query the vector store for similar memories
            results = await self.vector_store_manager.query_similar(
                query_embedding=query_embedding, n_results=limit
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
                        decrypted_data = self.data_processor._decrypt(
                            data_package["encrypted_package"]
                        )
                        decompressed_data_bytes = self.data_processor._decompress(decrypted_data)
                        decompressed_data_str = decompressed_data_bytes.decode("utf-8")

                        # Parse the data based on type
                        if "dialogue_text" in data_package["data_type"]:
                            abstracted = json.loads(decompressed_data_str)
                            content = self.data_processor._rehydrate_text_gist(abstracted)
                        else:
                            content = decompressed_data_str

                        memories.append(
                            HAMMemory(
                                memory_id=memory_id,
                                content=content,
                                metadata=data_package.get("metadata", {}),
                                relevance=result.get("distance", 0.0),  # Distance-based relevance
                            )
                        )

                    except Exception as e:  # broad exception acceptable: semantic search should skip unprocessable memories
                        # Fallback for double-base64
                        try:
                            import base64
                            decoded_payload = base64.b64decode(data_package["encrypted_package"])
                            decrypted_data = self.data_processor._decrypt(decoded_payload)
                            decompressed_data_bytes = self.data_processor._decompress(decrypted_data)
                            decompressed_data_str = decompressed_data_bytes.decode("utf-8")

                            # Parse the data based on type
                            if "dialogue_text" in data_package["data_type"]:
                                abstracted = json.loads(decompressed_data_str)
                                content = self.data_processor._rehydrate_text_gist(abstracted)
                            else:
                                content = decompressed_data_str

                            memories.append(
                                HAMMemory(
                                    memory_id=memory_id,
                                    content=content,
                                    metadata=data_package.get("metadata", {}),
                                    relevance=result.get("distance", 0.0),
                                )
                            )
                        except Exception as e2:  # broad exception acceptable: semantic search should skip unprocessable memories
                            logger.error(f"Error processing memory {memory_id}: {e} (Fallback failed: {e2})", exc_info=True)
                            continue

            logger.info(f"Semantic search returned {len(memories)} results")
            return memories[:limit]

        except Exception as e:  # broad exception acceptable: semantic search should fallback gracefully
            logger.error(f"Error during semantic search: {e}", exc_info=True)
            return await self._fallback_keyword_search(query, limit)

    async def _fallback_keyword_search(self, query: str, limit: int = 10) -> List[HAMMemory]:
        logger.info(f"Performing fallback keyword search for query: '{query}'")
        query_words = set(re.findall(r"\b[a-zA-Z\u4e00-\u9fff]{2,}\b", query.lower()))
        if not query_words:
            return []

        results = []
        for mem_id, data_package in self.core_memory_store.items():
            mem = self._process_memory_for_keyword(mem_id, data_package, query_words)
            if mem is not None:
                results.append(mem)

        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results[:limit]

    def _process_memory_for_keyword(
        self, mem_id: str, data_package: dict, query_words: set
    ) -> Optional[HAMMemory]:
        encrypted = data_package["encrypted_package"]
        for attempt in (self._try_decrypt, self._try_b64_fallback):
            result = attempt(mem_id, data_package, encrypted, query_words)
            if result is not None:
                return result
        return None

    @staticmethod
    def _compute_match(abstracted: Optional[dict], decompressed_str: str, data_type: str, query_words: set) -> Optional[tuple]:
        if "dialogue_text" in data_type and abstracted is not None:
            content = abstracted.get("gist", "") + " " + " ".join(abstracted.get("keywords", []))
        else:
            content = decompressed_str
        content_lower = content.lower()
        match_count = sum(1 for word in query_words if word in content_lower)
        if match_count == 0:
            return None
        relevance = min(1.0, match_count / max(1, len(query_words)))
        return content, relevance

    def _try_decrypt(self, mem_id: str, data_package: dict, encrypted: Any, query_words: set) -> Optional[HAMMemory]:
        try:
            decrypted_data = self.data_processor._decrypt(encrypted)
            decompressed_bytes = self.data_processor._decompress(decrypted_data)
            decompressed_str = decompressed_bytes.decode("utf-8")
            abstracted = json.loads(decompressed_str) if "dialogue_text" in data_package["data_type"] else None
            result = self._compute_match(abstracted, decompressed_str, data_package["data_type"], query_words)
            if result is None:
                return None
            content, relevance = result
            stored_relevance = data_package.get("relevance", 0.5)
            final_score = (relevance * 0.7) + (stored_relevance * 0.3)
            return HAMMemory(
                memory_id=mem_id,
                content=self.data_processor._rehydrate_text_gist(abstracted) if abstracted is not None else decompressed_str[:200],
                metadata=data_package.get("metadata", {}),
                relevance=final_score,
            )
        except Exception:
            return None

    def _try_b64_fallback(self, mem_id: str, data_package: dict, encrypted: Any, query_words: set) -> Optional[HAMMemory]:
        try:
            import base64
            decoded_payload = base64.b64decode(encrypted)
            return self._try_decrypt(mem_id, data_package, decoded_payload, query_words)
        except Exception as e:
            logger.error(f"Error processing memory {mem_id} in keyword search: {e} (Fallback failed)", exc_info=True)
            return None
