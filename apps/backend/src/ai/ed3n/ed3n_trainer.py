# =============================================================================
# ANGELA-MATRIX: [L3] [γ] [C] [L2]
# =============================================================================

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from apps.backend.src.ai.ed3n.core_network import CoreNetwork
from apps.backend.src.ai.ed3n.dictionary_layer import DictionaryLayer
from apps.backend.src.ai.ed3n.ed3n_engine import ED3NEngine
from apps.backend.src.ai.ed3n.relation_classifier import RelationClassifier
from apps.backend.src.ai.ed3n.training_types import TrainMetrics, TrainingBatch, TrainingExample

logger = logging.getLogger(__name__)


class ED3NTrainer:
    def __init__(
        self,
        engine: ED3NEngine,
        dictionary_lr: float = 0.1,
        network_lr: float = 0.05,
    ):
        self.engine = engine
        self.dictionary: DictionaryLayer = engine.dictionary
        self.network: CoreNetwork = engine.network
        self.classifier: RelationClassifier = engine.classifier
        self.dictionary_lr = dictionary_lr
        self.network_lr = network_lr
        self.replay_buffer: Optional[Any] = None
        self.training_history: List[TrainMetrics] = []

    def train_step(self, batch: TrainingBatch) -> TrainMetrics:
        start = time.perf_counter()

        metrics_a = self.train_dictionary_phase(batch.examples)
        metrics_b = self.train_network_phase(batch.examples)

        combined_loss = (metrics_a.loss + metrics_b.loss) / 2.0
        combined_acc = (metrics_a.accuracy + metrics_b.accuracy) / 2.0

        combined = TrainMetrics(
            phase="combined",
            loss=combined_loss,
            accuracy=combined_acc,
            learning_rate=(self.dictionary_lr + self.network_lr) / 2.0,
            epoch=metrics_a.epoch,
            samples=len(batch.examples),
            duration_ms=(time.perf_counter() - start) * 1000.0,
        )
        self.training_history.append(combined)
        return combined

    def train_dictionary_phase(
        self, examples: List[TrainingExample]
    ) -> TrainMetrics:
        start = time.perf_counter()
        correct = 0
        total_loss = 0.0

        for ex in examples:
            matched_keys = self.dictionary.encode(ex.input_text)

            expected_set = set(ex.input_keys)
            matched_set = set(matched_keys)
            hits = expected_set & matched_set
            misses = expected_set - matched_set

            correct += len(hits)

            for key in misses:
                surface = ex.input_text
                if key not in self.dictionary.entries:
                    new_key = self.dictionary.grow(
                        text=surface,
                        surface_form=surface,
                        confidence=ex.confidence * 0.6,
                    )
                    if new_key:
                        logger.debug("Grew entry %s for missing key", new_key)

            for key in ex.input_keys:
                entry = self.dictionary.entries.get(key)
                if entry is None:
                    continue
                match = 1.0 if key in matched_set else 0.0
                entry.confidence += self.dictionary_lr * (match - entry.confidence)

            for k1, rel_type, k2 in ex.relation_pairs:
                entry1 = self.dictionary.entries.get(k1)
                entry2 = self.dictionary.entries.get(k2)
                if entry1 is None or entry2 is None:
                    continue
                existing = entry1.relations.get(rel_type, [])
                if k2 not in existing:
                    existing.append(k2)
                    entry1.relations[rel_type] = existing
                existing2 = entry2.relations.get(rel_type, [])
                if k1 not in existing2:
                    existing2.append(k1)
                    entry2.relations[rel_type] = existing2

            total_loss += 1.0 - (len(hits) / max(len(expected_set), 1))

        n = len(examples)
        accuracy = correct / max(sum(len(e.input_keys) for e in examples), 1)
        avg_loss = total_loss / max(n, 1)

        self.dictionary._rebuild_index()

        return TrainMetrics(
            phase="dictionary",
            loss=avg_loss,
            accuracy=accuracy,
            learning_rate=self.dictionary_lr,
            epoch=0,
            samples=n,
            duration_ms=(time.perf_counter() - start) * 1000.0,
        )

    def train_network_phase(
        self, examples: List[TrainingExample]
    ) -> TrainMetrics:
        start = time.perf_counter()
        total_loss = 0.0
        total_correct = 0
        total_expected = 0

        for ex in examples:
            activations = self.network.forward(ex.input_keys)

            for expected_key in ex.output_keys:
                total_expected += 1
                actual = activations.get(expected_key, 0.0)
                expected = ex.confidence
                error = expected - actual
                total_loss += abs(error)

                if actual > 0.3 and expected > 0.5:
                    total_correct += 1

                for input_key in ex.input_keys:
                    self.network.adjust_connection(
                        input_key, expected_key, self.network_lr * error
                    )

                neuron = self._find_neuron(expected_key)
                if neuron is not None:
                    delta = self.network_lr * (actual - 0.5) * 0.1
                    neuron.threshold -= delta

        n = len(examples)
        avg_loss = total_loss / max(total_expected, 1)
        accuracy = total_correct / max(total_expected, 1)

        return TrainMetrics(
            phase="network",
            loss=avg_loss,
            accuracy=accuracy,
            learning_rate=self.network_lr,
            epoch=0,
            samples=n,
            duration_ms=(time.perf_counter() - start) * 1000.0,
        )

    def train_from_replay(self, batch_size: int = 32) -> Optional[TrainMetrics]:
        if self.replay_buffer is None:
            logger.warning("No replay buffer set; skipping replay training")
            return None

        experiences = self.replay_buffer.sample_batch(batch_size)
        if not experiences:
            return None

        examples: List[TrainingExample] = []
        for exp in experiences:
            example = TrainingExample(
                input_text=str(exp.get("state", "")),
                expected_output=str(exp.get("next_state", "")),
                input_keys=exp.get("input_keys", []),
                output_keys=exp.get("output_keys", []),
                relation_pairs=exp.get("relation_pairs", []),
                confidence=min(max(float(exp.get("reward", 0.5)), 0.0), 1.0),
            )
            examples.append(example)

        batch = TrainingBatch(
            examples=examples,
            batch_id=f"replay_{len(self.training_history)}",
        )
        return self.train_step(batch)

    def set_replay_buffer(self, buffer: Any) -> None:
        self.replay_buffer = buffer
        logger.info("Replay buffer connected to ED3NTrainer")

    def get_training_summary(self) -> Dict[str, Any]:
        if not self.training_history:
            return {"status": "no_training", "steps": 0}

        last = self.training_history[-1]
        return {
            "status": "active",
            "steps": len(self.training_history),
            "last_loss": last.loss,
            "last_accuracy": last.accuracy,
            "avg_loss": sum(m.loss for m in self.training_history)
            / len(self.training_history),
            "avg_accuracy": sum(m.accuracy for m in self.training_history)
            / len(self.training_history),
            "dictionary_lr": self.dictionary_lr,
            "network_lr": self.network_lr,
        }

    def _find_neuron(self, key: str):
        for group in self.network.groups.values():
            neuron = group.neurons.get(key)
            if neuron is not None:
                return neuron
        return None
