import os
from typing import Any

os.environ["TRANSFORMERS_NO_TF_IMPORT"] = (
    "1"  # Explicitly prevent transformers from importing TensorFlow
)

import asyncio
import logging

from scipy.spatial.distance import cosine
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class VectorStore:
    """Placeholder for a vector database interface, e.g., based on ChromaDB.
    This component would handle storing and querying vector embeddings of memories.
    """

    def __init__(
        self,
        collection_name: str = "default_collection",
        model_name: str = "all-MiniLM-L6-v2",
        persistence_dir: str = "data/vector_store",
    ):
        logger.info(
            f"VectorStore initialized with collection: {collection_name} and embedding model: {model_name}",
        )
        self.embedding_model = SentenceTransformer(model_name)
        self.embedding_function = lambda texts: self.embedding_model.encode(
            texts,
            convert_to_numpy=True,
        )
        self.memories = []  # Stores tuples of (embedding, document, metadata, id)
        self.collection_name = collection_name  # Store collection_name as an attribute
        
        logger.warning(f"VectorStore initialized in LOCAL JSON PERSISTENCE MODE. Collection: {collection_name}")
        logger.warning("Data will be saved to 'data/vector_store/' but this is not a production-grade vector DB.")
        
        # Load existing memories if available
        self.persistence_dir = persistence_dir
        self.persistence_path = os.path.join(
            self.persistence_dir, f"{self.collection_name}.json"
        )
        self._load_from_disk()
        logger.info("Custom in-memory VectorStore initialized with persistence.")

    def _save_to_disk(self):
        """Saves the current memories to disk."""
        try:
            os.makedirs(self.persistence_dir, exist_ok=True)
            data_to_save = []
            for mem in self.memories:
                # Convert numpy array to list for JSON serialization
                mem_copy = mem.copy()
                if hasattr(mem_copy["embedding"], "tolist"):
                    mem_copy["embedding"] = mem_copy["embedding"].tolist()
                data_to_save.append(mem_copy)
            
            import json
            with open(self.persistence_path, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(self.memories)} memories to {self.persistence_path}")
        except Exception as e:
            logger.error(f"Failed to save vector store to disk: {e}")

    def _load_from_disk(self):
        """Loads memories from disk."""
        import json
        import numpy as np
        
        if not os.path.exists(self.persistence_path):
            return

        try:
            with open(self.persistence_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self.memories = []
            for mem in data:
                # Convert list back to numpy array
                mem["embedding"] = np.array(mem["embedding"])
                self.memories.append(mem)
            logger.info(f"Loaded {len(self.memories)} memories from {self.persistence_path}")
        except Exception as e:
            logger.error(f"Failed to load vector store from disk: {e}")

    async def add_memories(
        self,
        contents: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> list[str]:
        """Adds new memories (text content) to the vector store.
        Generates embeddings for the content and stores them in ChromaDB.

        Args:
            contents (List[str]): A list of text contents to store.
            metadatas (Optional[List[Dict[str, Any]]]): Optional list of metadata dictionaries for each content.
            ids (Optional[List[str]]): Optional list of unique IDs for each content. If None, ChromaDB generates them.

        Returns:
            List[str]: A list of IDs of the added memories.

        """
        logger.info(
            f"VectorStore: Adding {len(contents)} memories to collection '{self.collection_name}'...",
        )

        if ids is None:
            ids = [f"mem_{len(self.memories) + i}" for i in range(len(contents))]

        if metadatas is None:
            metadatas = [{}] * len(contents)

        embeddings = self.embedding_function(contents)

        for i, content in enumerate(contents):
            self.memories.append(
                {
                    "id": ids[i],
                    "document": content,
                    "metadata": metadatas[i],
                    "embedding": embeddings[i],
                },
            )
        logger.info(f"Added {len(contents)} memories to custom in-memory VectorStore.")
        self._save_to_disk()
        return ids

    async def query_memories(
        self,
        query_text: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Queries the vector store for memories similar to the given query text.

        Args:
            query_text (str): The text query to search for.
            top_k (int): The maximum number of similar memories to retrieve.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each containing 'id', 'document', 'metadata', and 'distance'.

        """
        logger.info(
            f"VectorStore: Querying for top {top_k} similar memories for query: '{query_text}'...",
        )

        if not self.memories:
            logger.info("No memories in store to query.")
            return []

        query_embedding = self.embedding_function([query_text])[0]

        similarities = []
        for memory in self.memories:
            # Cosine distance is 1 - cosine similarity. We want higher similarity, so lower distance.
            # Or, more directly, cosine similarity = 1 - cosine_distance
            similarity = 1 - cosine(query_embedding, memory["embedding"])
            similarities.append((similarity, memory))

        similarities.sort(
            key=lambda x: x[0],
            reverse=True,
        )  # Sort by similarity, descending

        formatted_results = []
        for sim, memory in similarities[:top_k]:
            formatted_results.append(
                {
                    "id": memory["id"],
                    "document": memory["document"],
                    "metadata": memory["metadata"],
                    "distance": 1
                    - sim,  # Return distance for consistency with ChromaDB output
                },
            )

        logger.info(
            f"Retrieved {len(formatted_results)} memories from custom in-memory VectorStore.",
        )
        return formatted_results


if __name__ == "__main__":

    async def main():
        # Set PYTHONPATH to include the project root for module resolution
        import os
        import sys

        sys.path.insert(
            0,
            os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."),
            ),
        )

        # Initialize VectorStore with a specific collection name
        vector_store = VectorStore(collection_name="test_agent_memories")

        # Sample memories to add
        sample_contents = [
            "The user asked to rebuild the project from the blueprint.",
            "The agent fixed the perceive method signatures in several agents.",
            "HSP extensibility and bridge components were implemented.",
            "The project is about building an AGI system.",
            "The user wants to thoroughly complete and perfect the project.",
        ]
        sample_metadatas = [
            {"type": "task", "source": "user_request"},
            {"type": "code_fix", "source": "agent_action"},
            {"type": "implementation", "source": "agent_action"},
            {"type": "project_info", "source": "blueprint"},
            {"type": "task", "source": "user_request"},
        ]

        # Add memories
        added_ids = await vector_store.add_memories(sample_contents, sample_metadatas)
        print(f"\nAdded memories with IDs: {added_ids}")

        # Query memories
        query_text = "What has the agent done recently regarding project completion?"
        query_results = await vector_store.query_memories(query_text, top_k=3)

        print("\n--- Query Results ---")
        for res in query_results:
            print(
                f"ID: {res['id']}, Distance: {res['distance']:.4f}, Document: {res['document']}, Metadata: {res['metadata']}",
            )

        query_text_2 = "Tell me about the AGI system."
        query_results_2 = await vector_store.query_memories(query_text_2, top_k=2)

        print("\n--- Query Results for AGI ---")
        for res in query_results_2:
            print(
                f"ID: {res['id']}, Distance: {res['distance']:.4f}, Document: {res['document']}, Metadata: {res['metadata']}",
            )

    asyncio.run(main())
