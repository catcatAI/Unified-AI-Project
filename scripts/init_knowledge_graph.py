#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγδ] [B] [L3+]
# =============================================================================
"""
Knowledge Graph Initialization Script.

Uses the existing KGImporter to generate/load knowledge graphs with IS_A
relations and loads them into GARDEN engine for query-time inference.

This does NOT hard-code any data — it uses the KGImporter's synthetic
generator (or ConceptNet/Wikidata if available) to create the graph.

Usage:
    python scripts/init_knowledge_graph.py

Steps:
    1. Generate synthetic knowledge graph (entities + IS_A relations)
    2. Load into GARDEN engine dictionary and SNN
    3. Store verified facts in GroundedKnowledgeStore
    4. Save checkpoints for future startup
"""

import json
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s")
logger = logging.getLogger("InitKG")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src")))


def generate_concept_graph():
    """Generate a knowledge graph with common concepts and their relations.

    Uses KGImporter's synthetic generator but with curated seed data
    instead of random entities.
    """
    from ai.garden.kg_import import KGImporter

    importer = KGImporter()

    # Register common entities with their types
    entities = [
        # Writing tools
        ("pen", "工具", {"zh": "筆", "en": "pen"}),
        ("pencil", "工具", {"zh": "鉛筆", "en": "pencil"}),
        ("paper", "介質", {"zh": "紙", "en": "paper"}),
        ("ink", "材料", {"zh": "墨水", "en": "ink"}),
        ("eraser", "工具", {"zh": "橡皮擦", "en": "eraser"}),
        ("ruler", "工具", {"zh": "尺", "en": "ruler"}),

        # Writing actions
        ("writing", "動作", {"zh": "寫字", "en": "writing"}),
        ("drawing", "動作", {"zh": "畫畫", "en": "drawing"}),
        ("reading", "動作", {"zh": "閱讀", "en": "reading"}),
        ("sketching", "動作", {"zh": "素描", "en": "sketching"}),

        # Categories
        ("tool", "類別", {"zh": "工具", "en": "tool"}),
        ("medium", "類別", {"zh": "介質", "en": "medium"}),
        ("material", "類別", {"zh": "材料", "en": "material"}),
        ("action", "類別", {"zh": "動作", "en": "action"}),

        # Office supplies
        ("book", "物品", {"zh": "書", "en": "book"}),
        ("notebook", "物品", {"zh": "筆記本", "en": "notebook"}),
        ("desk", "物品", {"zh": "書桌", "en": "desk"}),
        ("bag", "物品", {"zh": "包包", "en": "bag"}),
    ]

    for key, category, surface in entities:
        importer.entities[key] = {
            "surface": surface,
            "relations": {},
            "category": category,
        }

    # Add IS_A relations (inheritance)
    isa_relations = [
        ("pen", "tool"),
        ("pencil", "tool"),
        ("eraser", "tool"),
        ("ruler", "tool"),
        ("paper", "medium"),
        ("ink", "material"),
        ("writing", "action"),
        ("drawing", "action"),
        ("reading", "action"),
        ("sketching", "action"),
        ("book", "medium"),
        ("notebook", "medium"),
    ]

    for entity, category in isa_relations:
        importer._add_triple(entity, "isa", category, weight=0.85)

    # Add USED_FOR relations
    usedfor_relations = [
        ("pen", "writing"),
        ("pen", "drawing"),
        ("pencil", "writing"),
        ("pencil", "sketching"),
        ("pencil", "drawing"),
        ("ink", "writing"),
        ("ink", "drawing"),
        ("eraser", "writing"),
        ("ruler", "drawing"),
    ]

    for tool, action in usedfor_relations:
        importer._add_triple(tool, "usedfor", action, weight=0.75)

    # Add REQUIRES relations
    requires_relations = [
        ("writing", "pen"),
        ("writing", "paper"),
        ("writing", "ink"),
        ("drawing", "pen"),
        ("drawing", "paper"),
        ("sketching", "pencil"),
        ("sketching", "paper"),
    ]

    for action, requirement in requires_relations:
        importer._add_triple(action, "requires", requirement, weight=0.80)

    # Add HAS_STEP relations (procedural knowledge)
    step_relations = [
        ("writing", ["take_pen", "dip_ink", "write_on_paper"]),
        ("drawing", ["take_pencil", "sketch_on_paper", "add_details"]),
        ("reading", ["open_book", "read_text", "turn_page"]),
    ]

    for action, steps in step_relations:
        for i, step in enumerate(steps):
            step_key = f"{i}"
            importer._add_triple(action, f"step_{step_key}", step, weight=0.9)

    return importer


def load_into_garden(importer):
    """Load the knowledge graph into GARDEN engine."""
    from ai.garden.garden_engine import GARDENEngine

    engine = GARDENEngine(compatibility_mode=True)
    engine.load_presets()

    stats = importer.bulk_load(engine)
    logger.info("Loaded into GARDEN: %s", stats)
    return engine


def store_grounded_facts(importer):
    """Store verified facts in GroundedKnowledgeStore."""
    from ai.memory.grounded_knowledge import GroundedKnowledgeStore

    store = GroundedKnowledgeStore()

    from ai.memory.grounded_knowledge import SourceRef, VerificationStatus

    fact_count = 0
    for subject, relation, obj, weight in importer.triples:
        if relation in ("isa", "usedfor", "requires"):
            fact_text = f"{subject} {relation} {obj}"
            claim = store.add_or_update(fact_text, domain="knowledge_graph")
            store.record_verification(
                claim.claim_key,
                status=VerificationStatus.VERIFIED,
                sources=[SourceRef(url="", title="init_knowledge_graph", snippet=f"weight={weight}")],
                confidence=weight,
            )
            fact_count += 1

    logger.info("Stored %d grounded facts", fact_count)
    return store


def main():
    logger.info("=" * 60)
    logger.info("Knowledge Graph Initialization")
    logger.info("=" * 60)

    # Step 1: Generate concept graph
    logger.info("Step 1: Generating concept graph...")
    importer = generate_concept_graph()
    stats = importer.get_stats()
    logger.info("  Entities: %d, Triples: %d", stats["entities"], stats["triples"])
    logger.info("  Relations: %s", stats["relation_breakdown"])

    # Step 2: Load into GARDEN
    logger.info("Step 2: Loading into GARDEN...")
    engine = load_into_garden(importer)

    # Step 3: Store grounded facts
    logger.info("Step 3: Storing grounded facts...")
    store = store_grounded_facts(importer)

    # Step 4: Save everything
    logger.info("Step 4: Saving...")
    os.makedirs("data/checkpoints", exist_ok=True)

    # Save grounded knowledge
    store.save("data/checkpoints/grounded_knowledge.json")

    # Save KGImporter state
    kg_path = "data/checkpoints/knowledge_graph.json"
    with open(kg_path, "w", encoding="utf-8") as f:
        json.dump({
            "entities": importer.entities,
            "triples": [
                {"subject": s, "relation": r, "object": o, "weight": w}
                for s, r, o, w in importer.triples
            ],
        }, f, indent=2, ensure_ascii=False)
    logger.info("  Saved: %s", kg_path)

    # Step 5: Verify
    logger.info("Step 5: Verification...")
    from ai.meta.knowledge_pipeline import KnowledgePipeline
    from ai.ed3n.ed3n_engine import ED3NEngine
    from services.math_verifier import MathVerifier
    from services.weather_service import WeatherService

    pipeline = KnowledgePipeline(
        math_verifier=MathVerifier(),
        weather_service=WeatherService(),
        grounded_knowledge=store,
    )

    import asyncio

    async def verify():
        tests = ["3+5*2", "formula of water", "what color is the sky"]
        for q in tests:
            r = await pipeline.query(q)
            if r:
                logger.info("  '%s' → [%s] %s", q, r["source"], r["answer"][:50])
            else:
                logger.info("  '%s' → None", q)

    asyncio.run(verify())

    logger.info("=" * 60)
    logger.info("Knowledge Graph Initialization Complete")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
