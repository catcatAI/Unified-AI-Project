import asyncio
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class M5KnowledgeCore:
    """M5 Knowledge Core.
    Manages knowledge acquisition, representation, and retrieval using a simple graph-like structure.
    """

    def __init__(self):
        logger.info("M5KnowledgeCore initialized.")
        # Graph-like structure: {subject: {predicate: [object1, object2, ...]}}
        self.knowledge_base: dict[str, dict[str, list[str]]] = {}

    async def add_knowledge(
        self,
        subject: str,
        predicate: str,
        obj: str,
    ) -> dict[str, Any]:
        """Adds a new piece of knowledge as a triple (subject, predicate, object)."""
        logger.info(
            f"M5KnowledgeCore: Adding knowledge - Subject: '{subject}', Predicate: '{predicate}', Object: '{obj}'",
        )
        await asyncio.sleep(0.01)  # Simulate storage time

        subject_lower = subject.lower()
        predicate_lower = predicate.lower()
        obj_lower = obj.lower()

        if subject_lower not in self.knowledge_base:
            self.knowledge_base[subject_lower] = {}
        if predicate_lower not in self.knowledge_base[subject_lower]:
            self.knowledge_base[subject_lower][predicate_lower] = []

        if obj_lower not in self.knowledge_base[subject_lower][predicate_lower]:
            self.knowledge_base[subject_lower][predicate_lower].append(obj_lower)
            return {
                "status": "knowledge_added",
                "subject": subject,
                "predicate": predicate,
                "object": obj,
            }
        return {
            "status": "knowledge_exists",
            "subject": subject,
            "predicate": predicate,
            "object": obj,
        }

    async def retrieve_knowledge(
        self,
        subject: str | None = None,
        predicate: str | None = None,
        obj: str | None = None,
    ) -> dict[str, Any]:
        """Retrieves knowledge from the internal knowledge base based on subject, predicate, and/or object.
        Supports partial matching and returns matching triples.
        """
        logger.info(
            f"M5KnowledgeCore: Retrieving knowledge for S:'{subject}', P:'{predicate}', O:'{obj}'",
        )
        await asyncio.sleep(0.05)  # Reduced sleep for faster simulation

        matching_triples: list[tuple[str, str, str]] = []

        # Convert query parts to lowercase for case-insensitive matching
        query_subject = subject.lower() if subject else None
        query_predicate = predicate.lower() if predicate else None
        query_obj = obj.lower() if obj else None

        for s, predicates in self.knowledge_base.items():
            if query_subject and query_subject not in s:  # Partial match for subject
                continue

            for p, objects in predicates.items():
                if (
                    query_predicate and query_predicate not in p
                ):  # Partial match for predicate
                    continue

                for o in objects:
                    if query_obj and query_obj not in o:  # Partial match for object
                        continue

                    matching_triples.append((s, p, o))

        return {
            "status": "knowledge_retrieved",
            "query": {"subject": subject, "predicate": predicate, "object": obj},
            "knowledge_items": matching_triples if matching_triples else [],
            "count": len(matching_triples),
        }


if __name__ == "__main__":

    async def main():
        # Set PYTHONPATH to include the project root for module resolution
        import sys

        sys.path.insert(
            0,
            str(Path(__file__).resolve().parent.parent.parent.parent.parent),
        )

        core = M5KnowledgeCore()

        print("\n--- Test Case 1: Add Knowledge (Triples) ---")
        await core.add_knowledge("Angela", "isA", "AI_Agent")
        await core.add_knowledge("Angela", "hasGoal", "AGI")
        await core.add_knowledge("Angela", "livesIn", "Simulation")
        await core.add_knowledge("Simulation", "hasPart", "Angela")
        await core.add_knowledge("AGI", "isType", "Goal")
        await core.add_knowledge("AGI", "requires", "Learning")
        await core.add_knowledge("Learning", "isType", "Process")

        print("\n--- Test Case 2: Retrieve by Subject ---")
        result1 = await core.retrieve_knowledge(subject="Angela")
        print(f"Retrieval Result 1 (Angela): {result1}")
        assert ("angela", "isa", "ai_agent") in result1["knowledge_items"]
        assert ("angela", "hasgoal", "agi") in result1["knowledge_items"]

        print("\n--- Test Case 3: Retrieve by Predicate ---")
        result2 = await core.retrieve_knowledge(predicate="isA")
        print(f"Retrieval Result 2 (isA): {result2}")
        assert ("angela", "isa", "ai_agent") in result2["knowledge_items"]

        print("\n--- Test Case 4: Retrieve by Object ---")
        result3 = await core.retrieve_knowledge(obj="AGI")
        print(f"Retrieval Result 3 (AGI): {result3}")
        assert ("angela", "hasgoal", "agi") in result3["knowledge_items"]


        print("\n--- Test Case 5: Retrieve by Subject and Predicate ---")
        result4 = await core.retrieve_knowledge(subject="Angela", predicate="hasGoal")
        print(f"Retrieval Result 5 (Angela hasGoal): {result4}")
        assert ("angela", "hasgoal", "agi") in result4["knowledge_items"]

        print("\n--- Test Case 6: Retrieve by Predicate and Object ---")
        result5 = await core.retrieve_knowledge(predicate="isType", obj="Goal")
        print(f"Retrieval Result 5 (isType Goal): {result5}")
        assert ("agi", "istype", "goal") in result5["knowledge_items"]

        print("\n--- Test Case 7: Retrieve by Subject and Object ---")
        result6 = await core.retrieve_knowledge(subject="Simulation", obj="Angela")
        print(f"Retrieval Result 6 (Simulation Angela): {result6}")
        assert ("simulation", "haspart", "angela") in result6["knowledge_items"]

        print(
            "\n--- Test Case 8: Retrieve by all three (Subject, Predicate, Object) ---",
        )
        result7 = await core.retrieve_knowledge(
            subject="Angela",
            predicate="isA",
            obj="AI_Agent",
        )
        print(f"Retrieval Result 7 (Angela isA AI_Agent): {result7}")
        assert ("angela", "isa", "ai_agent") in result7["knowledge_items"]

        print("\n--- Test Case 9: No Match ---")
        result8 = await core.retrieve_knowledge(
            subject="NonExistent",
            predicate="has",
            obj="Nothing",
        )
        print(f"Retrieval Result 8 (No Match): {result8}")
        assert len(result8["knowledge_items"]) == 0

        print("\n--- Test Case 10: Partial Match (Subject) ---")
        result9 = await core.retrieve_knowledge(
            subject="angel",
        )  # Partial match for Angela
        print(f"Retrieval Result 9 (Partial Subject): {result9}")
        assert ("angela", "isa", "ai_agent") in result9["knowledge_items"]

        print("\n--- Test Case 11: Partial Match (Predicate) ---")
        result10 = await core.retrieve_knowledge(
            predicate="hasgo",
        )  # Partial match for hasGoal
        print(f"Retrieval Result 10 (Partial Predicate): {result10}")
        assert ("angela", "hasgoal", "agi") in result10["knowledge_items"]

        print("\n--- Test Case 12: Partial Match (Object) ---")
        result11 = await core.retrieve_knowledge(
            obj="agen",
        )  # Partial match for AI_Agent
        print(f"Retrieval Result 11 (Partial Object): {result11}")
        assert ("angela", "isa", "ai_agent") in result11["knowledge_items"]

    asyncio.run(main())
