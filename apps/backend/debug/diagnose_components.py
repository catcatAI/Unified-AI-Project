#!/usr/bin/env python3
"""
诊断：核心组件可用性检测
"""

import asyncio
import logging
import os
import sys
from typing import Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class ComponentDiagnostic:
    def __init__(self) -> None:
        self.test_results: Dict[str, str] = {}

    async def diagnose_all(self) -> None:
        logger.info("Starting component diagnostics...")
        await self._check_vector_store()
        await self._check_causal_reasoning()
        self._report()

    async def _check_vector_store(self) -> None:
        logger.info("Checking vector store...")
        try:
            from ai.memory.vector_store import VectorMemoryStore

            store = VectorMemoryStore(persist_directory="./.diag_vector")
            await store.add_memory("diag_001", "diagnostic test", {"source": "diagnose"})
            count = store.vector_count
            logger.info("vector store: OK (%d vector(s))", count)
            self.test_results["vector_store"] = "PASSED"
        except Exception as e:
            logger.error("vector store: FAILED - %s", e)
            self.test_results["vector_store"] = f"ERROR: {e}"

    async def _check_causal_reasoning(self) -> None:
        logger.info("Checking causal reasoning engine...")
        try:
            from ai.reasoning.causal_reasoning_engine import CausalReasoningEngine

            engine = CausalReasoningEngine(config={"causality_threshold": 0.5})
            logger.info("causal reasoning: OK (init succeeded)")
            self.test_results["causal_reasoning"] = "PASSED"
        except Exception as e:
            logger.error("causal reasoning: FAILED - %s", e)
            self.test_results["causal_reasoning"] = f"ERROR: {e}"

    def _report(self) -> None:
        logger.info("=" * 60)
        logger.info("Diagnostic Report")
        logger.info("=" * 60)
        passed = 0
        for component, result in self.test_results.items():
            ok = result == "PASSED"
            logger.info("%s %s: %s", "OK" if ok else "FAIL", component, result)
            if ok:
                passed += 1
        logger.info("%d/%d components passed", passed, len(self.test_results))


async def main() -> None:
    diag = ComponentDiagnostic()
    await diag.diagnose_all()


if __name__ == "__main__":
    asyncio.run(main())
