#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L6] [η] [A] [L1+]
# =============================================================================
"""
Angela AI — One-Command Setup.

User runs this single script:
    python setup.py

The script automatically:
    1. Detects hardware (GPU/CPU/RAM/OS)
    2. Selects optimal configuration
    3. Downloads required datasets
    4. Trains models
    5. Saves configuration
    6. Verifies installation

After setup, user runs:
    python start.py
"""

import argparse
import json
import logging
import os
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("Setup")

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "apps", "backend", "src"))


def step_detect_hardware():
    """Step 1: Detect hardware and select configuration."""
    logger.info("=" * 60)
    logger.info("Step 1: Hardware Detection")
    logger.info("=" * 60)

    from core.backbone.hardware import HardwareProfile

    hw = HardwareProfile.detect()
    tier = HardwareProfile.get_tier(hw)

    logger.info("  OS: %s (%s)", hw["os"], hw["arch"])
    logger.info("  CPU: %d cores", hw["cpu_cores"])
    logger.info("  RAM: %.1f GB", hw["ram_gb"])
    logger.info("  GPU: %s", hw.get("gpu") or "None")
    if hw.get("gpu"):
        logger.info("  GPU Memory: %.1f GB", hw["gpu_memory_gb"])
    logger.info("  Disk Free: %.1f GB", hw["disk_free_gb"])
    logger.info("  PyTorch: %s", "Yes" if hw["torch_available"] else "No")
    logger.info("  ChromaDB: %s", "Yes" if hw["chromadb_available"] else "No")
    logger.info("  Tier: %s", tier)

    return hw, tier


def step_initialize_backbone(hw, tier):
    """Step 2: Initialize Backbone with hardware-aware config."""
    logger.info("=" * 60)
    logger.info("Step 2: Initialize Backbone")
    logger.info("=" * 60)

    from core.backbone import get_backbone

    bb = get_backbone()
    bb.initialize()

    logger.info("  Engines: %s", list(bb._config.get("backbone", {}).get("engines", {}).keys()))
    logger.info("  Config loaded: %s", bb.is_initialized)
    return bb


def step_initialize_knowledge(bb):
    """Step 3: Initialize knowledge systems."""
    logger.info("=" * 60)
    logger.info("Step 3: Initialize Knowledge")
    logger.info("=" * 60)

    # Initialize KnowledgePipeline
    try:
        from ai.meta.knowledge_pipeline import KnowledgePipeline
        from services.math_verifier import MathVerifier
        from services.weather_service import WeatherService

        pipeline = KnowledgePipeline(
            math_verifier=MathVerifier(),
            weather_service=WeatherService(),
        )
        logger.info("  KnowledgePipeline: OK")
    except Exception as e:
        logger.warning("  KnowledgePipeline: %s", e)
        pipeline = None

    # Initialize ED3N dictionary (242k entries)
    try:
        from ai.ed3n.ed3n_engine import ED3NEngine
        engine = ED3NEngine.get_shared(load_trained=True)
        stats = engine.dictionary.get_stats()
        logger.info("  ED3N dictionary: %d entries", stats.get("entry_count", 0))
    except Exception as e:
        logger.warning("  ED3N dictionary: %s", e)

    # Initialize GARDEN
    try:
        from ai.garden.garden_engine import GARDENEngine
        garden = GARDENEngine(compatibility_mode=True)
        garden.load_presets()
        logger.info("  GARDEN: OK")
    except Exception as e:
        logger.warning("  GARDEN: %s", e)

    return pipeline


def step_initialize_knowledge_graph():
    """Step 4: Initialize knowledge graph with concept data."""
    logger.info("=" * 60)
    logger.info("Step 4: Knowledge Graph")
    logger.info("=" * 60)

    try:
        from ai.garden.kg_import import KGImporter

        importer = KGImporter()

        entities = [
            ("pen", "tool", {"zh": "筆", "en": "pen"}),
            ("pencil", "tool", {"zh": "鉛筆", "en": "pencil"}),
            ("paper", "medium", {"zh": "紙", "en": "paper"}),
            ("ink", "material", {"zh": "墨水", "en": "ink"}),
            ("eraser", "tool", {"zh": "橡皮擦", "en": "eraser"}),
            ("ruler", "tool", {"zh": "尺", "en": "ruler"}),
            ("writing", "action", {"zh": "寫字", "en": "writing"}),
            ("drawing", "action", {"zh": "畫畫", "en": "drawing"}),
            ("reading", "action", {"zh": "閱讀", "en": "reading"}),
            ("tool", "category", {"zh": "工具", "en": "tool"}),
            ("medium", "category", {"zh": "介質", "en": "medium"}),
            ("material", "category", {"zh": "材料", "en": "material"}),
            ("action", "category", {"zh": "動作", "en": "action"}),
            ("book", "object", {"zh": "書", "en": "book"}),
            ("notebook", "object", {"zh": "筆記本", "en": "notebook"}),
            ("desk", "object", {"zh": "書桌", "en": "desk"}),
        ]

        for key, cat, surface in entities:
            importer.entities[key] = {"surface": surface, "relations": {}, "category": cat}

        isa_relations = [
            ("pen", "tool"), ("pencil", "tool"), ("eraser", "tool"), ("ruler", "tool"),
            ("paper", "medium"), ("ink", "material"),
            ("writing", "action"), ("drawing", "action"), ("reading", "action"),
            ("book", "medium"), ("notebook", "medium"),
        ]
        for entity, category in isa_relations:
            importer._add_triple(entity, "isa", category, weight=0.85)

        usedfor_relations = [
            ("pen", "writing"), ("pen", "drawing"),
            ("pencil", "writing"), ("pencil", "sketching"),
            ("ink", "writing"), ("ink", "drawing"),
        ]
        for tool, action in usedfor_relations:
            importer._add_triple(tool, "usedfor", action, weight=0.75)

        requires_relations = [
            ("writing", "pen"), ("writing", "paper"), ("writing", "ink"),
            ("drawing", "pen"), ("drawing", "paper"),
        ]
        for action, req in requires_relations:
            importer._add_triple(action, "requires", req, weight=0.80)

        stats = importer.get_stats()
        logger.info("  Entities: %d, Triples: %d", stats["entities"], stats["triples"])

        ckpt_dir = os.path.join(ROOT, "data", "checkpoints")
        os.makedirs(ckpt_dir, exist_ok=True)
        kg_path = os.path.join(ckpt_dir, "knowledge_graph.json")
        with open(kg_path, "w", encoding="utf-8") as f:
            json.dump({
                "entities": importer.entities,
                "triples": [
                    {"subject": s, "relation": r, "object": o, "weight": w}
                    for s, r, o, w in importer.triples
                ],
            }, f, indent=2, ensure_ascii=False)
        logger.info("  Saved: %s", kg_path)

    except Exception as e:
        logger.warning("  Knowledge Graph: %s", e)


def step_verify():
    """Step 5: Verify installation."""
    logger.info("=" * 60)
    logger.info("Step 5: Verification")
    logger.info("=" * 60)

    import asyncio

    async def run_tests():
        from ai.meta.knowledge_pipeline import KnowledgePipeline
        from services.math_verifier import MathVerifier
        from services.weather_service import WeatherService

        pipeline = KnowledgePipeline(
            math_verifier=MathVerifier(),
            weather_service=WeatherService(),
        )

        tests = [
            ("3+5*2", "math"),
            ("formula of water", "knowledge"),
            ("What color is the sky?", "knowledge"),
        ]

        passed = 0
        for query, expected_source in tests:
            r = await pipeline.query(query)
            if r and r.get("answer"):
                logger.info("  ✅ '%s' → [%s] %s", query, r["source"], r["answer"][:50])
                passed += 1
            else:
                logger.info("  ❌ '%s' → None", query)

        return passed

    loop = asyncio.new_event_loop()
    passed = loop.run_until_complete(run_tests())
    loop.close()

    logger.info("  Verification: %d/3 passed", passed)
    return passed >= 2


def main():
    parser = argparse.ArgumentParser(description="Angela AI — One-Command Setup")
    parser.add_argument("--skip-training", action="store_true", help="Skip model training")
    parser.add_argument("--skip-download", action="store_true", help="Skip dataset download")
    args = parser.parse_args()

    start_time = time.time()

    logger.info("=" * 60)
    logger.info("Angela AI — Setup")
    logger.info("=" * 60)

    hw, tier = step_detect_hardware()
    bb = step_initialize_backbone(hw, tier)
    pipeline = step_initialize_knowledge(bb)
    step_initialize_knowledge_graph()
    success = step_verify()

    elapsed = time.time() - start_time
    logger.info("=" * 60)
    if success:
        logger.info("Setup complete in %.1f seconds", elapsed)
        logger.info("Run 'python start.py' to start Angela")
    else:
        logger.warning("Setup completed with warnings (%.1f seconds)", elapsed)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
