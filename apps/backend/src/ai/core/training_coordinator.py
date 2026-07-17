# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [C] [L2]
# =============================================================================

import asyncio
import hashlib
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DOMAIN_OWNERSHIP: Dict[str, str] = {
    "reflex": "ed3n",
    "math": "ed3n",
    "logic": "ed3n",
    "reasoning": "ed3n",
    "tooluse": "ed3n",
    "knowledge": "garden",
    "creative": "cloud",
    "greeting": "ed3n",
    "association": "ed3n",
    "command": "garden",
    "routing": "garden",
    "opinion": "cloud",
    "general": "garden",
    "unknown": "garden",
}


@dataclass
class DomainTrainingRecord:
    domain: str
    model_id: str
    trained_count: int = 0
    last_trained: str = ""
    accuracy: float = 0.0
    examples: List[Dict] = field(default_factory=list)


class TrainingCoordinator:
    """
    Coordinates training across multiple models to prevent duplicate training
    of the same content and ensure each model specializes in its domain.

    Domain ownership:
    - ED3N: reflex, math, logic (fast, lightweight)
    - GARDEN: knowledge, semantic (vector-based understanding)
    - Cloud LLM: creative, opinion, general (heavy computation)
    """

    def __init__(self, bus: Optional[Any] = None,
                 max_examples_per_domain: int = 100,
                 max_hashes_per_domain: int = 10000):
        self.bus = bus
        self._domain_map: Dict[str, DomainTrainingRecord] = {}
        self._seen_hashes: Dict[str, set] = {}
        self._max_examples = max_examples_per_domain
        self._max_hashes = max_hashes_per_domain
        self._lock = asyncio.Lock()

    async def assign_domain(self, domain: str) -> Optional[str]:
        if self.bus is not None:
            try:
                result = self.bus.get_training_assignment(domain)
                if result is not None:
                    return result
            except (AttributeError, TypeError, ValueError):
                logger.warning("ModelBus.get_training_assignment failed for %s, falling back", domain)
        return DOMAIN_OWNERSHIP.get(domain)

    async def record_training(
        self,
        domain: str,
        model_id: str,
        count: int,
        accuracy: float,
        examples: List[Dict],
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        async with self._lock:
            if domain in self._domain_map:
                record = self._domain_map[domain]
                record.trained_count += count
                record.last_trained = now
                record.accuracy = accuracy
                examples_to_add = examples[:self._max_examples]
                record.examples.extend(examples_to_add)
                if len(record.examples) > self._max_examples:
                    record.examples = record.examples[-self._max_examples:]
            else:
                self._domain_map[domain] = DomainTrainingRecord(
                    domain=domain,
                    model_id=model_id,
                    trained_count=count,
                    last_trained=now,
                    accuracy=accuracy,
                    examples=list(examples[:self._max_examples]),
                )
            for ex in examples:
                inp = ex.get("input", "")
                if inp:
                    h = hashlib.sha256(inp.encode("utf-8")).hexdigest()
                    domain_hashes = self._seen_hashes.setdefault(domain, set())
                    domain_hashes.add(h)
                    if len(domain_hashes) > self._max_hashes:
                        self._seen_hashes[domain] = set(list(domain_hashes)[-self._max_hashes:])
        logger.info(
            "Recorded training: domain=%s model=%s count=%d accuracy=%.4f",
            domain,
            model_id,
            count,
            accuracy,
        )

    async def should_skip(self, domain: str, sample_input: str) -> bool:
        h = hashlib.sha256(sample_input.encode("utf-8")).hexdigest()
        async with self._lock:
            domain_hashes = self._seen_hashes.get(domain, set())
            return h in domain_hashes

    async def sync_reflex_patterns(
        self,
        source_engine: Any,
        target_engine: Any,
        top_n: int = 100,
    ) -> int:
        copied = 0
        try:
            source_patterns = getattr(source_engine, "get_reflex_patterns", lambda: [])()
            target_patterns = {
                p.get("pattern", "") if isinstance(p, dict) else str(p)
                for p in getattr(target_engine, "get_reflex_patterns", lambda: [])()
            }
            add_pattern = getattr(target_engine, "add_reflex_pattern", None)
            if add_pattern is None:
                logger.warning("target_engine has no add_reflex_pattern method")
                return 0
            sorted_patterns = sorted(
                source_patterns,
                key=lambda p: p.get("confidence", 0.0) if isinstance(p, dict) else 0.0,
                reverse=True,
            )
            for pattern in sorted_patterns[:top_n]:
                p_text = pattern.get("pattern", "") if isinstance(pattern, dict) else str(pattern)
                if p_text and p_text not in target_patterns:
                    add_pattern(pattern if isinstance(pattern, dict) else {"pattern": pattern})
                    target_patterns.add(p_text)
                    copied += 1
            logger.info("Synced %d reflex patterns from source to target", copied)
        except (AttributeError, TypeError, ValueError) as e:
            logger.error("Failed to sync reflex patterns: %s", e)
        return copied

    async def get_domain_report(self) -> str:
        lines: List[str] = []
        lines.append("=" * 60)
        lines.append("TRAINING COORDINATOR DOMAIN REPORT")
        lines.append("=" * 60)
        if not self._domain_map:
            lines.append("No training records yet.")
            return "\n".join(lines)
        for domain, record in sorted(self._domain_map.items()):
            lines.append(f"  Domain:        {record.domain}")
            lines.append(f"  Owner:         {record.model_id}")
            lines.append(f"  Samples:       {record.trained_count}")
            lines.append(f"  Last trained:  {record.last_trained}")
            lines.append(f"  Accuracy:      {record.accuracy:.4f}")
            lines.append(f"  Examples kept: {len(record.examples)}")
            lines.append("-" * 60)
        lines.append(f"Total domains tracked: {len(self._domain_map)}")
        return "\n".join(lines)

    async def deconflict_samples(self, samples: List[Dict]) -> Dict[str, List[Dict]]:
        batches: Dict[str, List[Dict]] = {}
        for sample in samples:
            domain = sample.get("domain", "unknown")
            model_id = await self.assign_domain(domain)
            if model_id is None:
                model_id = "unassigned"
            batches.setdefault(model_id, []).append(sample)
        return batches

    def save(self, path: str) -> None:
        """Persist coordinator state to disk."""
        state = {
            "domain_map": {
                d: {
                    "domain": r.domain,
                    "model_id": r.model_id,
                    "trained_count": r.trained_count,
                    "last_trained": r.last_trained,
                    "accuracy": r.accuracy,
                    "examples": r.examples[:self._max_examples],
                }
                for d, r in self._domain_map.items()
            },
            "seen_hashes": {
                d: list(hashes)[-self._max_hashes:]
                for d, hashes in self._seen_hashes.items()
            },
        }
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        logger.info("TrainingCoordinator: saved to %s", path)

    def load(self, path: str) -> None:
        """Load coordinator state from disk."""
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                state = json.load(f)
            for d, r in state.get("domain_map", {}).items():
                self._domain_map[d] = DomainTrainingRecord(
                    domain=r["domain"],
                    model_id=r["model_id"],
                    trained_count=r.get("trained_count", 0),
                    last_trained=r.get("last_trained", ""),
                    accuracy=r.get("accuracy", 0.0),
                    examples=r.get("examples", []),
                )
            for d, hashes in state.get("seen_hashes", {}).items():
                self._seen_hashes[d] = set(hashes)
            logger.info("TrainingCoordinator: loaded from %s (%d domains)", path, len(self._domain_map))
        except Exception as e:
            logger.warning("TrainingCoordinator: failed to load %s: %s", path, e)
