# =============================================================================
# ANGELA-MATRIX: [L3] [γδ] [C] [L3]
# =============================================================================

import asyncio
import logging
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .training_types import (
    TrainingBatch,
    TrainingExample as TTTrainingExample,
)

logger = logging.getLogger(__name__)


@dataclass
class TrainingExample:
    user_text: str
    response_text: str
    context: Dict[str, Any]
    timestamp: str = ""


@dataclass
class TrainMetrics:
    loss: float = 0.0
    accuracy: float = 0.0
    examples_used: int = 0
    duration: float = 0.0
    timestamp: str = ""


class ContinuousLearningPipeline:
    def __init__(
        self,
        engine: Optional[Any] = None,
        trainer: Optional[Any] = None,
        growth_interval: int = 10,
        train_interval: int = 50,
        min_examples_for_train: int = 20,
        auto_grow: bool = True,
        max_buffer_size: int = 500,
        max_history_size: int = 1000,
    ):
        self.engine = engine
        self.trainer = trainer
        self.growth_interval = growth_interval
        self.train_interval = train_interval
        self.min_examples_for_train = min_examples_for_train
        self.auto_grow = auto_grow
        self.max_buffer_size = max_buffer_size
        self.max_history_size = max_history_size

        self._lock = threading.RLock()
        self._interaction_count: int = 0
        self._training_buffer: List[TrainingExample] = []
        self._history: List[Dict[str, Any]] = []
        self._stats: Dict[str, Any] = {
            "total_interactions": 0,
            "concepts_discovered": 0,
            "training_runs": 0,
            "buffer_size": 0,
            "last_train_time": None,
            "last_growth_time": None,
        }

    def process_interaction(
        self, user_text: str, response_text: str, context: Dict
    ) -> Dict:
        with self._lock:
            return self._process_interaction_locked(user_text, response_text, context)

    def _process_interaction_locked(
        self, user_text: str, response_text: str, context: Dict
    ) -> Dict:
        self._interaction_count += 1
        self._stats["total_interactions"] = self._interaction_count

        new_concepts = []
        if self.auto_grow and self.engine is not None:
            if self._interaction_count % self.growth_interval == 0:
                new_concepts = self._detect_and_grow(user_text, context)

        self._queue_training_example(user_text, response_text, context)

        result: Dict[str, Any] = {
            "interaction": self._interaction_count,
            "new_concepts": new_concepts,
            "grew": len(new_concepts) > 0,
        }

        if self._should_train():
            metrics = self.train_step()
            if metrics is not None:
                result["trained"] = True
                result["metrics"] = {
                    "loss": metrics.loss,
                    "accuracy": metrics.accuracy,
                    "examples_used": metrics.examples_used,
                    "duration": metrics.duration,
                }

        self._history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "interaction": self._interaction_count,
                "user_text_preview": user_text[:50],
                "new_concepts": new_concepts,
            }
        )
        if len(self._history) > self.max_history_size:
            self._history.pop(0)

        return result

    async def process_interaction_async(
        self, user_text: str, response_text: str, context: Dict
    ) -> Dict:
        return await asyncio.to_thread(
            self.process_interaction, user_text, response_text, context
        )

    def _detect_and_grow(self, text: str, context: Dict) -> List[str]:
        if self.engine is None or self.engine.dictionary is None:
            logger.warning("Engine or dictionary not available; skipping growth.")
            return []

        new_keys = []
        dictionary = self.engine.dictionary
        existing_keys = dictionary.encode(text)
        known_surfaces: set = set()
        for k in existing_keys:
            entry = dictionary.entries.get(k)
            if entry:
                known_surfaces.update(entry.surface_forms.values())

        tokens = re.findall(r"[\w]+", text.lower())
        for token in tokens:
            if len(token) < 2:
                continue
            if token in known_surfaces:
                continue
            key = dictionary.grow(text, token, confidence=0.5)
            if key:
                new_keys.append(key)
                self._stats["concepts_discovered"] += 1

        if new_keys:
            self._stats["last_growth_time"] = datetime.now().isoformat()

        return new_keys

    def _queue_training_example(
        self, user_text: str, response_text: str, context: Dict
    ) -> None:
        example = TrainingExample(
            user_text=user_text,
            response_text=response_text,
            context=context,
            timestamp=datetime.now().isoformat(),
        )
        self._training_buffer.append(example)
        if len(self._training_buffer) > self.max_buffer_size:
            self._training_buffer.pop(0)
        self._stats["buffer_size"] = len(self._training_buffer)

    def _should_train(self) -> bool:
        return (
            len(self._training_buffer) >= self.min_examples_for_train
            and self._interaction_count % self.train_interval == 0
        )

    def train_step(self) -> Optional[TrainMetrics]:
        if not self._should_train():
            logger.info(
                "Training skipped: buffer=%d, min=%d, interactions=%d, interval=%d",
                len(self._training_buffer),
                self.min_examples_for_train,
                self._interaction_count,
                self.train_interval,
            )
            return None

        if self.trainer is None:
            logger.warning("No trainer available; skipping training step.")
            return None

        start = time.time()
        examples = self._training_buffer[:]
        try:
            tt_examples = []
            for ex in examples:
                input_keys = (
                    self.engine.dictionary.encode(ex.user_text)
                    if self.engine and self.engine.dictionary
                    else []
                )
                output_keys = (
                    self.engine.dictionary.encode(ex.response_text)
                    if self.engine and self.engine.dictionary
                    else []
                )
                tt_ex = TTTrainingExample(
                    input_text=ex.user_text,
                    expected_output=ex.response_text,
                    input_keys=input_keys,
                    output_keys=output_keys,
                    relation_pairs=[],
                    confidence=0.8,
                    metadata=ex.context if isinstance(ex.context, dict) else {},
                )
                tt_examples.append(tt_ex)
            batch = TrainingBatch(
                examples=tt_examples,
                batch_id=f"cl_{int(time.time())}_{self._interaction_count}",
            )
            if hasattr(self.trainer, "train_step"):
                raw = self.trainer.train_step(batch)
            else:
                raw = self.trainer(batch)
        except Exception as e:
            logger.exception("Training step failed: %s", e)
            return None

        duration = time.time() - start
        self._training_buffer.clear()
        self._stats["buffer_size"] = 0
        self._stats["training_runs"] += 1
        self._stats["last_train_time"] = datetime.now().isoformat()

        if isinstance(raw, dict):
            loss = raw.get("loss", 0.0)
            accuracy = raw.get("accuracy", 0.0)
        elif hasattr(raw, "loss"):
            loss = raw.loss
            accuracy = getattr(raw, "accuracy", 0.0)
        else:
            loss = 0.0
            accuracy = 0.0

        return TrainMetrics(
            loss=loss,
            accuracy=accuracy,
            examples_used=len(examples),
            duration=duration,
            timestamp=datetime.now().isoformat(),
        )

    def train_from_replay(
        self, replay_buffer: Any, batch_size: int = 32
    ) -> Optional[TrainMetrics]:
        if self.trainer is None:
            logger.warning("No trainer available; skipping replay training.")
            return None

        start = time.time()
        try:
            batch = (
                replay_buffer.sample_batch(batch_size)
                if hasattr(replay_buffer, "sample_batch")
                else []
            )
            if not batch:
                logger.info("No replay samples available.")
                return None

            if hasattr(self.trainer, "train_step"):
                raw = self.trainer.train_step(examples=batch)
            else:
                raw = self.trainer(examples=batch)
            if raw is None:
                return None
        except Exception as e:
            logger.exception("Replay training failed: %s", e)
            return None

        duration = time.time() - start
        self._stats["training_runs"] += 1
        self._stats["last_train_time"] = datetime.now().isoformat()

        if isinstance(raw, dict):
            loss = raw.get("loss", 0.0)
            accuracy = raw.get("accuracy", 0.0)
        elif hasattr(raw, "loss"):
            loss = raw.loss
            accuracy = getattr(raw, "accuracy", 0.0)
        else:
            loss = 0.0
            accuracy = 0.0

        return TrainMetrics(
            loss=loss,
            accuracy=accuracy,
            examples_used=len(batch),
            duration=duration,
            timestamp=datetime.now().isoformat(),
        )

    def save(self, save_dir: str) -> str:
        with self._lock:
            import json, os
            os.makedirs(save_dir, exist_ok=True)
            state = {
                "interaction_count": self._interaction_count,
                "stats": self._stats,
                "history": self._history[-100:],
                "buffer": [
                {
                    "user_text": ex.user_text,
                    "response_text": ex.response_text,
                    "context": ex.context,
                    "timestamp": ex.timestamp,
                }
                for ex in self._training_buffer
            ],
            "saved_at": __import__('datetime').datetime.now().isoformat(),
        }
        path = os.path.join(save_dir, "cl_state.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        logger.info("CL state saved to %s (%d interactions, %d buffered)",
                    path, self._interaction_count, len(self._training_buffer))
        return path

    @classmethod
    def load(cls, save_dir: str, engine=None, trainer=None) -> "ContinuousLearningPipeline":
        import json, os
        path = os.path.join(save_dir, "cl_state.json")
        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)

        pipeline = cls(engine=engine, trainer=trainer)
        pipeline._interaction_count = state.get("interaction_count", 0)
        pipeline._stats = state.get("stats", pipeline._stats)
        pipeline._history = state.get("history", [])

        for ex_data in state.get("buffer", []):
            example = TrainingExample(
                user_text=ex_data["user_text"],
                response_text=ex_data["response_text"],
                context=ex_data.get("context", {}),
                timestamp=ex_data.get("timestamp", ""),
            )
            pipeline._training_buffer.append(example)

        logger.info("CL state loaded from %s (%d interactions, %d buffered)",
                    path, pipeline._interaction_count, len(pipeline._training_buffer))
        return pipeline

    def get_stats(self) -> Dict:
        return dict(self._stats)

    def get_learning_report(self) -> str:
        lines = [
            "=" * 50,
            "ED3N Continuous Learning Report",
            "=" * 50,
            f"Total interactions:      {self._stats['total_interactions']}",
            f"Concepts discovered:     {self._stats['concepts_discovered']}",
            f"Training runs:           {self._stats['training_runs']}",
            f"Buffer size:             {self._stats['buffer_size']}",
            f"Last train time:         {self._stats['last_train_time'] or 'N/A'}",
            f"Last growth time:        {self._stats['last_growth_time'] or 'N/A'}",
            f"Growth interval:         {self.growth_interval}",
            f"Train interval:          {self.train_interval}",
            f"Min examples for train:  {self.min_examples_for_train}",
            f"Max buffer size:         {self.max_buffer_size}",
            f"Max history size:        {self.max_history_size}",
            f"Engine available:        {self.engine is not None}",
            f"Trainer available:       {self.trainer is not None}",
            "=" * 50,
        ]
        return "\n".join(lines)
