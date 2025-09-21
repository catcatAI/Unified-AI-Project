import chromadb
# 修正導入方式 - 直接從chromadb導入Collection
from chromadb import Collection
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class VectorStore:
    """A wrapper for a ChromaDB vector store."""

    def __init__(self, path: str = ".chromadb/", collection_name: str = "main_collection"):
        """
        Initializes the VectorStore.

        Args:
            path (str): The path to the ChromaDB database directory.
            collection_name (str): The name of the collection to use.
        """
        try:
            # Use HttpClient to work with HTTP-only mode
            self.client = chromadb.HttpClient(
                host="localhost",
                port=8000
            )
            self.collection: Collection = self.client.get_or_create_collection(name=collection_name)
            logger.info(f"VectorStore initialized with collection '{collection_name}' using HttpClient.")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client with HttpClient: {e}")
            try:
                # Fallback to EphemeralClient if HttpClient fails
                self.client = chromadb.EphemeralClient()
                self.collection: Collection = self.client.get_or_create_collection(name=collection_name)
                logger.info(f"VectorStore initialized with collection '{collection_name}' using EphemeralClient.")
            except Exception as e2:
                logger.error(f"Failed to initialize ChromaDB client with EphemeralClient: {e2}")
                raise

    def add_documents(self, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]], documents: Optional[List[str]] = None):
        """
        Adds documents to the vector store.

        Args:
            ids (List[str]): A list of unique IDs for the documents.
            embeddings (List[List[float]]): A list of embeddings for the documents.
            metadatas (List[Dict[str, Any]]): A list of metadata dictionaries for the documents.
            documents (Optional[List[str]]): A list of the actual document content.
        """
        try:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
            logger.info(f"Added {len(ids)} documents to the collection.")
        except Exception as e:
            logger.error(f"Failed to add documents to collection: {e}")
            raise

    def query(self, query_embeddings: List[List[float]], n_results: int = 5, where: Optional[Dict[str, Any]] = None) -> Dict[str, List[Any]]:
        """
        Queries the vector store.

        Args:
            query_embeddings (List[List[float]]): A list of query embeddings.
            n_results (int): The number of results to return.
            where (Optional[Dict[str, Any]]): A dictionary of metadata to filter by.

        Returns:
            Dict[str, List[Any]]: A dictionary of query results.
        """
        try:
            results = self.collection.query(
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where
            )
            logger.info(f"Query returned {len(results.get('ids', []))} results.")
            return results
        except Exception as e:
            logger.error(f"Failed to query collection: {e}")
            raise

    def delete_documents(self, ids: List[str]):
        """
        Deletes documents from the vector store.

        Args:
            ids (List[str]): A list of document IDs to delete.
        """
        try:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents from the collection.")
        except Exception as e:
            logger.error(f"Failed to delete documents from collection: {e}")
            raise

    def update_document(self, id: str, embedding: Optional[List[float]] = None, metadata: Optional[Dict[str, Any]] = None, document: Optional[str] = None):
        """
        Updates a document in the vector store.

        Args:
            id (str): The ID of the document to update.
            embedding (Optional[List[float]]): The new embedding for the document.
            metadata (Optional[Dict[str, Any]]): The new metadata for the document.
            document (Optional[str]): The new content of the document.
        """
        try:
            update_data = {}
            if embedding is not None:
                update_data['embeddings'] = [embedding]
            if metadata is not None:
                update_data['metadatas'] = [metadata]
            if document is not None:
                update_data['documents'] = [document]

            if not update_data:
                logger.warning("Update called with no data to update.")
                return

            self.collection.update(ids=[id], **update_data)
            logger.info(f"Updated document with ID '{id}'.")
        except Exception as e:
            logger.error(f"Failed to update document with ID '{id}': {e}")
            raise