import datetime
from typing import Any
import ray

from .vector_store import VectorStore


@ray.remote
class HAMMemoryManagerActor:
    """Hierarchical Associative Memory (HAM) Manager.
    Manages AI's memory storage and retrieval in a hierarchical and semantic way, as a Ray Actor.
    """

    def __init__(self):
        """Initializes the HAMMemoryManagerActor."""
        self.vector_store = VectorStore()  # Initialize the custom VectorStore
        print("HAMMemoryManagerActor initialized with custom VectorStore.")

    async def store_experience(self, experience: dict[str, Any]) -> str:
        """Stores a new experience in the memory using the VectorStore.

        Args:
            experience (Dict[str, Any]): The experience to store.
                                         Expected to contain at least 'content'.

        Returns:
            str: The ID of the stored experience.

        """
        content = experience.get("content", "")
        if not content:
            raise ValueError("Experience must contain 'content' to be stored.")

        # Prepare metadata and ID for VectorStore
        metadata = {k: v for k, v in experience.items() if k not in ["content", "id"]}
        memory_id = experience.get(
            "id",
        )  # Allow pre-defined ID or let VectorStore generate

        # Add timestamp if not present
        if "timestamp" not in metadata:
            metadata["timestamp"] = datetime.datetime.now().isoformat()

        # VectorStore.add_memories expects lists
        ids = await self.vector_store.add_memories(
            contents=[content],
            metadatas=[metadata],
            ids=[memory_id] if memory_id else None,
        )
        print(f"Stored experience with ID: {ids[0]}")
        return ids[0]

    async def retrieve_relevant_memories(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Retrieves memories relevant to the given query using the VectorStore.

        Args:
            query (str): The text query to search for.
            limit (int): The maximum number of memories to retrieve.

        Returns:
            List[Dict[str, Any]]: A list of relevant memories.

        """
        print(f"Retrieving memories for query: '{query}' using VectorStore.")
        results = await self.vector_store.query_memories(query_text=query, top_k=limit)

        # Format results to match expected output if necessary, or return directly
        # VectorStore.query_memories already returns a list of dicts with 'id', 'document', 'metadata', 'distance'
        return results

    def get_memory_by_id(self, memory_id: str) -> dict[str, Any] | None:
        """Retrieves a memory by its ID from the VectorStore."""
        # In a simple in-memory VectorStore, we can iterate.
        # A more optimized VectorStore would have a direct lookup.
        for mem_entry in self.vector_store.memories:
            if mem_entry.get("id") == memory_id:
                # Return a formatted memory similar to query results
                return {
                    "id": mem_entry["id"],
                    "document": mem_entry["document"],
                    "metadata": mem_entry["metadata"],
                    "embedding": mem_entry[
                        "embedding"
                    ],  # Include embedding for completeness
                }
        return None

    def get_all_memories(self) -> list[dict[str, Any]]:
        """Returns all stored memories from the VectorStore."""
        # Return a list of formatted memories
        return [
            {
                "id": mem_entry["id"],
                "document": mem_entry["document"],
                "metadata": mem_entry["metadata"],
                "embedding": mem_entry["embedding"],
            }
            for mem_entry in self.vector_store.memories
        ]