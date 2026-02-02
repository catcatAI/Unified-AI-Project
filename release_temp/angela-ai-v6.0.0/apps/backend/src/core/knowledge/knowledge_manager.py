import datetime
from datetime import datetime, timezone
from typing import Any


class KnowledgeManager:
    """Manages the system's knowledge base, storing and retrieving facts."""

    def __init__(self):
        """Initializes the KnowledgeManager."""
        self._knowledge_base: list[dict[str, Any]] = []
        self._next_fact_id: int = 0
        print("KnowledgeManager initialized.")

    def add_fact(self, fact: dict[str, Any]) -> int:
        """Adds a new fact to the knowledge base.

        Args:
            fact (Dict[str, Any]): The fact to add. Expected to contain at least 'content'.

        Returns:
            int: The ID of the added fact.

        """
        fact_id = self._next_fact_id
        self._next_fact_id += 1

        if "timestamp" not in fact:
            fact["timestamp"] = datetime.datetime.now(timezone.utc).isoformat()
        fact["id"] = fact_id

        self._knowledge_base.append(fact)
        print(f"Added fact with ID: {fact_id}")
        return fact_id

    def query_knowledge(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Queries the knowledge base for facts relevant to the given query.
        Placeholder for more sophisticated semantic querying.

        Args:
            query (str): The query string.
            limit (int): The maximum number of facts to retrieve.

        Returns:
            List[Dict[str, Any]]: A list of relevant facts.

        """
        print(f"Querying knowledge for: '{query}' (placeholder)")
        # Placeholder: In a real system, this would involve semantic search,
        # inference, and knowledge graph traversal.

        # For now, return a simple filtered list based on query presence in content
        relevant_facts = [
            f
            for f in self._knowledge_base
            if query.lower() in str(f.get("content", "")).lower()
        ]
        return relevant_facts[:limit]

    def get_fact_by_id(self, fact_id: int) -> dict[str, Any] | None:
        """Retrieves a fact by its ID."""
        for fact in self._knowledge_base:
            if fact.get("id") == fact_id:
                return fact
        return None

    def get_all_facts(self) -> list[dict[str, Any]]:
        """Returns all stored facts."""
        return self._knowledge_base


if __name__ == "__main__":
    # Example Usage
    km = KnowledgeManager()

    # Add some facts
    km.add_fact(
        {
            "content": "FastAPI is a modern, fast (high-performance) web framework for building APIs with Python 3.7+.",
            "source": "docs",
        },
    )
    km.add_fact(
        {
            "content": "The BaseAgent is the foundational class for all AI agents.",
            "source": "blueprint",
        },
    )
    km.add_fact(
        {
            "content": "HSPConnector handles high-speed synchronization protocol communication.",
            "source": "blueprint",
        },
    )
    km.add_fact({"content": "The project aims for AGI Level 5.", "source": "vision"})

    # Query knowledge
    print("\n--- Facts about FastAPI ---")
    fastapi_facts = km.query_knowledge("FastAPI")
    for fact in fastapi_facts:
        print(f"ID: {fact['id']}, Content: {fact['content']}")

    print("\n--- Facts about AGI ---")
    agi_facts = km.query_knowledge("AGI")
    for fact in agi_facts:
        print(f"ID: {fact['id']}, Content: {fact['content']}")

    print("\n--- All Facts ---")
    all_facts = km.get_all_facts()
    for fact in all_facts:
        print(f"ID: {fact['id']}, Content: {fact['content']}")
