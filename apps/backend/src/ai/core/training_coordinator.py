# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [C] [L2]
# =============================================================================

import asyncio
import copy
import heapq
import inspect
import json
import logging
import os
import threading
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Mapping, Optional, Tuple

from ai.data_eng.dedup import hash_domain_dedup, hash_input
from core.system.config.magic_numbers import loop_sleep

logger = logging.getLogger(__name__)

# A domain processor consumes queued samples: sync or async, receives the sample
# dict, returns None. Registered by whoever owns that model's training.
TrainingProcessor = Callable[[Dict[str, Any]], Optional[Awaitable[None]]]

# Worker tuning (config-overridable, see magic_numbers).
WORKER_INTERVAL_DEFAULT = 5.0
WORKER_BATCH_DEFAULT = 8
MAX_TRAIN_QUEUE_DEFAULT = 500

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

    def __init__(
        self,
        bus: Optional[Any] = None,
        max_examples_per_domain: int = 100,
        max_hashes_per_domain: int = 10000,
        max_eda_episodes: int = 200,
        max_eda_hashes: int = 5000,
        max_logic_episodes: int = 200,
        max_train_queue: int = MAX_TRAIN_QUEUE_DEFAULT,
    ):
        self.bus = bus
        self._domain_map: Dict[str, DomainTrainingRecord] = {}
        self._seen_hashes: Dict[str, set] = {}
        self._max_examples = max_examples_per_domain
        self._max_hashes = max_hashes_per_domain
        self._max_eda_episodes = max(1, int(max_eda_episodes))
        self._max_eda_hashes = max(1, int(max_eda_hashes))
        self._max_logic_episodes = max(1, int(max_logic_episodes))
        self._max_train_queue = max(1, int(max_train_queue))
        self._lock = asyncio.Lock()
        self._eda_episode_queue: List[Dict[str, Any]] = []
        self._eda_episode_hashes: set = set()
        self._logic_episode_queue: List[Dict[str, Any]] = []
        self._logic_episode_hashes: set = set()
        # D4 (REFACTOR_PLAN §13.4): priority queue for sorted training execution.
        # Items are (priority, insertion_order, payload); higher priority drains
        # first. Guarded by a threading lock so ingest-time enqueue never blocks
        # the main response path.
        self._train_queue: List[Tuple[float, int, Dict[str, Any]]] = []
        self._queue_counter: int = 0
        self._queue_lock = threading.Lock()
        # Training execution ownership: processors are registered by the owner of
        # each domain's model, and the coordinator's own worker dispatches queued
        # samples to them. Nothing else may drain this queue.
        self._processors: Dict[str, TrainingProcessor] = {}
        self._worker_task: Optional[asyncio.Task[None]] = None
        self._worker_stop: Optional[asyncio.Event] = None
        self._worker_stats: Dict[str, int] = {
            "processed": 0,
            "deferred": 0,
            "failed": 0,
            "dropped": 0,
        }


    async def assign_domain(self, domain: str) -> Optional[str]:
        if domain == "eda_episode":
            return None
        if self.bus is not None:
            try:
                result = self.bus.get_training_assignment(domain)
                # bus 未類型化：回傳值先判空再 str 化，守住 Optional[str] 契約。
                if result is not None:
                    return str(result)
            except (AttributeError, TypeError, ValueError):
                logger.warning(
                    "ModelBus.get_training_assignment failed for %s, falling back", domain
                )
        return DOMAIN_OWNERSHIP.get(domain)

    async def record_training(
        self,
        domain: str,
        model_id: str,
        count: int,
        accuracy: float,
        examples: List[Dict],
    ) -> None:
        if domain == "eda_episode":
            return
        now = datetime.now(timezone.utc).isoformat()
        async with self._lock:
            if domain in self._domain_map:
                record = self._domain_map[domain]
                record.trained_count += count
                record.last_trained = now
                record.accuracy = accuracy
                examples_to_add = examples[: self._max_examples]
                record.examples.extend(examples_to_add)
                if len(record.examples) > self._max_examples:
                    record.examples = record.examples[-self._max_examples :]
            else:
                self._domain_map[domain] = DomainTrainingRecord(
                    domain=domain,
                    model_id=model_id,
                    trained_count=count,
                    last_trained=now,
                    accuracy=accuracy,
                    examples=list(examples[: self._max_examples]),
                )
            for ex in examples:
                inp = ex.get("input", "")
                if inp:
                    hash_domain_dedup(
                        inp,
                        self._seen_hashes,
                        domain,
                        max_hashes_per_domain=self._max_hashes,
                    )
        logger.info(
            "Recorded training: domain=%s model=%s count=%d accuracy=%.4f",
            domain,
            model_id,
            count,
            accuracy,
        )

    async def should_skip(self, domain: str, sample_input: str) -> bool:
        h = hash_input(sample_input)
        async with self._lock:
            domain_hashes = self._seen_hashes.get(domain, set())
            return h in domain_hashes

    async def enqueue_eda_episode(self, episode: Mapping[str, Any]) -> bool:
        """Queue a sanitized EDA episode without routing it to a model trainer."""
        fingerprint = str(episode.get("fingerprint", "")).strip()
        if not fingerprint:
            return False
        async with self._lock:
            if fingerprint in self._eda_episode_hashes:
                return False
            self._eda_episode_hashes.add(fingerprint)
            self._eda_episode_queue.append(copy.deepcopy(dict(episode)))
            while len(self._eda_episode_queue) > self._max_eda_episodes:
                removed = self._eda_episode_queue.pop(0)
                removed_fingerprint = str(removed.get("fingerprint", ""))
                if removed_fingerprint:
                    self._eda_episode_hashes.discard(removed_fingerprint)
            while len(self._eda_episode_hashes) > self._max_eda_hashes:
                self._eda_episode_hashes.pop()
        return True

    async def drain_eda_episodes(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Drain queued EDA episodes in insertion order."""
        async with self._lock:
            count = (
                len(self._eda_episode_queue)
                if limit is None
                else max(0, min(limit, len(self._eda_episode_queue)))
            )
            drained = self._eda_episode_queue[:count]
            self._eda_episode_queue[:count] = []
            for episode in drained:
                fingerprint = str(episode.get("fingerprint", ""))
                if fingerprint:
                    self._eda_episode_hashes.discard(fingerprint)
        return [copy.deepcopy(episode) for episode in drained]

    def pending_eda_episode_count(self) -> int:
        return len(self._eda_episode_queue)

    async def enqueue_logic_episode(self, episode: Mapping[str, Any]) -> bool:
        """Queue a verified logic experiment without routing it to ED3N/GARDEN."""
        fingerprint = str(episode.get("fingerprint", "")).strip()
        if not fingerprint:
            return False
        async with self._lock:
            if fingerprint in self._logic_episode_hashes:
                return False
            self._logic_episode_hashes.add(fingerprint)
            self._logic_episode_queue.append(copy.deepcopy(dict(episode)))
            while len(self._logic_episode_queue) > self._max_logic_episodes:
                removed = self._logic_episode_queue.pop(0)
                removed_fingerprint = str(removed.get("fingerprint", ""))
                if removed_fingerprint:
                    self._logic_episode_hashes.discard(removed_fingerprint)
        return True

    async def drain_logic_episodes(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Drain logic experiments in insertion order."""
        async with self._lock:
            count = (
                len(self._logic_episode_queue)
                if limit is None
                else max(0, min(limit, len(self._logic_episode_queue)))
            )
            drained = self._logic_episode_queue[:count]
            self._logic_episode_queue[:count] = []
            for episode in drained:
                fingerprint = str(episode.get("fingerprint", ""))
                if fingerprint:
                    self._logic_episode_hashes.discard(fingerprint)
        return [copy.deepcopy(episode) for episode in drained]

    def pending_logic_episode_count(self) -> int:
        return len(self._logic_episode_queue)

    # ------------------------------------------------------------------
    # D4 (REFACTOR_PLAN §13.4): priority-queued, sorted training execution.
    # ------------------------------------------------------------------
    def enqueue(self, domain: str, sample: Dict[str, Any], priority: float = 0.0) -> None:
        """Queue a training sample for sorted execution (highest priority first).

        Non-blocking and cheap; safe to call on the main ingest path. The queue
        is bounded: when full, the lowest-priority item is dropped so one noisy
        domain cannot starve the others.
        """
        with self._queue_lock:
            self._queue_counter += 1
            heapq.heappush(
                self._train_queue,
                (-float(priority), self._queue_counter, {"domain": domain, "sample": sample}),
            )
            dropped = 0
            while len(self._train_queue) > self._max_train_queue:
                # Heap key is (-priority, order): the LARGEST key is the
                # lowest-priority item, so eviction must not use heappop.
                worst = max(range(len(self._train_queue)), key=lambda i: self._train_queue[i][:2])
                del self._train_queue[worst]
                heapq.heapify(self._train_queue)
                dropped += 1
        if dropped:
            self._worker_stats["dropped"] += dropped
            logger.warning(
                "Training queue full (max=%d); dropped %d lowest-priority sample(s)",
                self._max_train_queue,
                dropped,
            )

    def drain_priority_queue(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Return queued training items ordered by priority (highest first).

        The heap key is (-priority, counter), so the smallest tuple is the
        highest-priority item; nsmallest therefore drains high-priority first.
        The heap itself is rebuilt from the undrained remainder.
        """
        with self._queue_lock:
            count = (
                len(self._train_queue)
                if limit is None
                else max(0, min(limit, len(self._train_queue)))
            )
            ordered = sorted(self._train_queue, key=lambda entry: (entry[0], entry[1]))
            drained_entries = ordered[:count]
            self._train_queue = list(reversed(ordered[count:]))
            heapq.heapify(self._train_queue)
        return [payload for _prio, _order, payload in drained_entries]

    def pending_training_count(self) -> int:
        with self._queue_lock:
            return len(self._train_queue)

    # ------------------------------------------------------------------
    # Training execution ownership (the coordinator dispatches; domain owners
    # register the processor that actually trains).
    # ------------------------------------------------------------------
    def register_processor(self, domain: str, processor: TrainingProcessor) -> None:
        """Register the owner-side processor for a domain's queued samples."""
        self._processors[domain] = processor
        logger.info("Training processor registered for domain=%s", domain)

    def unregister_processor(self, domain: str) -> None:
        self._processors.pop(domain, None)

    def registered_domains(self) -> List[str]:
        return sorted(self._processors)

    def get_worker_stats(self) -> Dict[str, int]:
        stats = dict(self._worker_stats)
        stats["pending"] = self.pending_training_count()
        stats["domains"] = len(self._processors)
        return stats

    async def process_pending_training(self, limit: Optional[int] = None) -> Dict[str, int]:
        """Dispatch queued samples to their domain processor.

        Samples for a domain with no registered processor are put back on the
        queue (deferred) so ownership stays explicit instead of being silently
        dropped; processor exceptions drop only that sample.
        """
        batch_size = (
            WORKER_BATCH_DEFAULT
            if limit is None
            else max(0, int(limit))
        )
        deferred: List[Dict[str, Any]] = []
        stats = {"processed": 0, "deferred": 0, "failed": 0, "dropped": 0}
        for item in self.drain_priority_queue(batch_size):
            domain = str(item.get("domain", ""))
            processor = self._processors.get(domain)
            if processor is None:
                deferred.append(item)
                continue
            try:
                outcome = processor(item.get("sample") or {})
                if inspect.isawaitable(outcome):
                    await outcome
                stats["processed"] += 1
            except Exception as exc:  # processor failure must not kill the worker
                stats["failed"] += 1
                logger.warning(
                    "Training processor failed for domain=%s: %s", domain, exc, exc_info=True
                )
        if deferred:
            stats["deferred"] = len(deferred)
            logger.info(
                "Deferring %d training sample(s): no processor registered for %s",
                len(deferred),
                sorted({str(item.get("domain", "")) for item in deferred}),
            )
            with self._queue_lock:
                for item in deferred:
                    self._queue_counter += 1
                    heapq.heappush(
                        self._train_queue,
                        (
                            -self._priority_of(item),
                            self._queue_counter,
                            item,
                        ),
                    )
        with self._queue_lock:
            for key, value in stats.items():
                self._worker_stats[key] = self._worker_stats.get(key, 0) + value
        return stats

    def _priority_of(self, item: Dict[str, Any]) -> float:
        # Payload no longer carries its heap key; the batch was drained in
        # priority order, so re-queueing preserves the original ordering by
        # using the sample's recorded priority when present.
        try:
            return float(item.get("sample", {}).get("priority", 0.0))
        except (TypeError, ValueError):
            return 0.0

    async def _training_worker_loop(self, interval: float) -> None:
        stop = self._worker_stop
        if stop is None:  # pragma: no cover - defensive
            return
        logger.info("Training worker started (interval=%.1fs)", interval)
        while not stop.is_set():
            try:
                await self.process_pending_training()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Training worker iteration failed: %s", exc, exc_info=True)
            try:
                await asyncio.wait_for(stop.wait(), timeout=interval)
            except asyncio.TimeoutError:
                continue
        logger.info("Training worker stopped")

    async def start_training_worker(self, interval: Optional[float] = None) -> None:
        """Start the coordinator's own dispatch worker (idempotent)."""
        if self._worker_task is not None and not self._worker_task.done():
            return
        self._worker_stop = asyncio.Event()
        self._worker_task = asyncio.create_task(
            self._training_worker_loop(
                float(
                    interval
                    if interval is not None
                    else loop_sleep("training.worker_interval", WORKER_INTERVAL_DEFAULT)
                )
            )
        )

    async def stop_training_worker(self) -> None:
        """Signal the worker to stop and await its exit (idempotent)."""
        if self._worker_task is None:
            return
        if self._worker_stop is not None:
            self._worker_stop.set()
        task, self._worker_task = self._worker_task, None
        try:
            await asyncio.wait_for(task, timeout=2.0)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        self._worker_stop = None

    async def sync_reflex_patterns(
        self,
        source_engine: Any,
        target_engine: Any,
        top_n: int = 100,
    ) -> int:
        copied = 0
        try:
            source_patterns: List[Any] = getattr(source_engine, "get_reflex_patterns", lambda: [])()
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
        """Assign samples to engines with domain-aware routing.

        ED3N receives every non-EDA sample: its dictionary growth needs all
        tokens (math/logic/reasoning/knowledge concepts must exist), while its
        SNN association training filters internally to reflex/greeting/association.
        EDA episodes stay in their typed queue until a domain-specific evaluator
        decides whether they are eligible for replay or training.

        GARDEN receives only non-deterministic samples: its ``learn_batch``
        would filter deterministic math/logic facts out anyway, so skipping
        them here avoids re-processing ~40K numeric/factual samples that the
        engine can never learn from. Its SNN Hebbian + dictionary growth then
        focuses on associative/knowledge content.
        """
        batches: Dict[str, List[Dict]] = {"ed3n": [], "garden": []}
        for sample in samples:
            domain = str(sample.get("domain", "unknown")).lower()
            if domain in {"eda_episode", "logic_gate_episode"} or sample.get("kind") in {
                "eda_episode",
                "logic_gate_episode",
            }:
                continue
            batches["ed3n"].append(sample)
            if domain not in {"math", "logic"}:
                batches["garden"].append(sample)
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
                    "examples": r.examples[: self._max_examples],
                }
                for d, r in self._domain_map.items()
            },
            "seen_hashes": {
                d: list(hashes)[-self._max_hashes :] for d, hashes in self._seen_hashes.items()
            },
            "eda_episodes": self._eda_episode_queue[-self._max_eda_episodes :],
            "eda_episode_hashes": list(self._eda_episode_hashes)[-self._max_eda_hashes :],
            "logic_episodes": self._logic_episode_queue[-self._max_logic_episodes :],
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
            self._eda_episode_queue = [
                dict(episode)
                for episode in state.get("eda_episodes", [])[-self._max_eda_episodes :]
                if isinstance(episode, dict)
            ]
            self._eda_episode_hashes = {
                str(episode.get("fingerprint"))
                for episode in self._eda_episode_queue
                if episode.get("fingerprint")
            }
            self._logic_episode_queue = [
                dict(episode)
                for episode in state.get("logic_episodes", [])[-self._max_logic_episodes :]
                if isinstance(episode, dict)
            ]
            self._logic_episode_hashes = {
                str(episode.get("fingerprint"))
                for episode in self._logic_episode_queue
                if episode.get("fingerprint")
            }
            logger.info(
                "TrainingCoordinator: loaded from %s (%d domains)", path, len(self._domain_map)
            )
        except Exception as e:
            logger.warning("TrainingCoordinator: failed to load %s: %s", path, e)
