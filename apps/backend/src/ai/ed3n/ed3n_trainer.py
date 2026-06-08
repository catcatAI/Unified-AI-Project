# =============================================================================
# ANGELA-MATRIX: [L3] [γ] [C] [L2]
# =============================================================================

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from .core_network import CoreNetwork
from .dictionary_layer import DictionaryLayer
from .ed3n_engine import ED3NEngine
from .relation_classifier import RelationClassifier, RelationType
from .training_types import (
    SeqBatch,
    SequenceExample,
    TrainMetrics,
    TrainingBatch,
    TrainingExample,
)

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
        self.current_epoch: int = 0
        self.best_accuracy: float = 0.0

    def train_step(self, batch: TrainingBatch) -> TrainMetrics:
        if not batch or not batch.examples:
            return TrainMetrics(phase="combined", loss=0.0, accuracy=0.0, learning_rate=(self.dictionary_lr+self.network_lr)/2, epoch=0, samples=0, duration_ms=0.0)

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
        if not examples:
            return TrainMetrics(phase="dictionary", loss=0.0, accuracy=0.0, learning_rate=self.dictionary_lr, epoch=0, samples=0, duration_ms=0.0)

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
        if not examples:
            return TrainMetrics(phase="network", loss=0.0, accuracy=0.0, learning_rate=self.network_lr, epoch=0, samples=0, duration_ms=0.0)

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

    def save(self, path: str) -> None:
        """Save trainer state (dictionary export + network params)."""
        import json, os
        from .training_types import TrainMetrics

        def _serialize(m):
            if isinstance(m, TrainMetrics):
                return {"phase": m.phase, "loss": m.loss, "accuracy": m.accuracy,
                        "learning_rate": m.learning_rate, "epoch": m.epoch,
                        "samples": m.samples, "duration_ms": m.duration_ms}
            return str(m)

        state = {
            "training_history": [_serialize(m) for m in self.training_history],
            "current_epoch": self.current_epoch,
            "best_accuracy": self.best_accuracy,
        }
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        dict_path = path.replace(".json", "_dictionary.json")
        self.dictionary.export_to_json(dict_path)
        logger.info("Trainer saved to %s (dict: %s)", path, dict_path)

    @classmethod
    def load(cls, path: str, dictionary_layer=None, core_network=None) -> "ED3NTrainer":
        """Load trainer state. Requires pre-configured dictionary and network."""
        import json, os
        from .ed3n_engine import ED3NEngine

        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)
        engine = ED3NEngine()
        if dictionary_layer:
            engine.dictionary = dictionary_layer
        if core_network:
            engine.network = core_network
        trainer = ED3NTrainer(engine)
        trainer.training_history = [
            TrainMetrics(**h) if isinstance(h, dict) else h
            for h in state.get("training_history", [])
        ]
        trainer.current_epoch = state.get("current_epoch", 0)
        trainer.best_accuracy = state.get("best_accuracy", 0.0)
        dict_path = path.replace(".json", "_dictionary.json")
        if os.path.exists(dict_path):
            engine.dictionary.import_from_json(dict_path)
        return trainer

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


class SequenceTrainer:
    def __init__(
        self,
        engine: "ED3NEngine",
        seq_lr: float = 0.1,
    ):
        self.engine = engine
        self.dictionary: DictionaryLayer = engine.dictionary
        self.network: CoreNetwork = engine.network
        self.seq_lr = seq_lr
        self.history: List[float] = []

    def train_step(self, batch: SeqBatch) -> TrainMetrics:
        if not batch or not batch.examples:
            return TrainMetrics(
                phase="sequence", loss=0.0, accuracy=0.0,
                learning_rate=self.seq_lr, epoch=0, samples=0, duration_ms=0.0,
            )

        start = time.perf_counter()
        total_loss = 0.0
        correct = 0
        total_steps = 0

        for ex in batch.examples:
            context = list(ex.input_key_seq)

            for target_key in ex.target_key_seq:
                total_steps += 1

                self.network.reset()
                activations = self.network.forward_sequential(
                    context, current_position=len(context) - 1
                )

                actual = activations.get(target_key, 0.0)
                error = 1.0 - actual
                total_loss += abs(error)

                if actual > 0.3:
                    correct += 1

                rel_key = None
                for ck in reversed(context):
                    if ck != target_key:
                        rel_key = ck
                        break
                if rel_key is not None:
                    self.network.add_directed(
                        rel_key, target_key,
                        weight=self.seq_lr * (1.0 - actual) * 0.5,
                    )
                    self.network.adjust_connection(
                        rel_key, target_key, self.seq_lr * error * 0.3,
                    )

                entry = self.dictionary.entries.get(target_key)
                if entry is not None:
                    entry.confidence = min(
                        entry.confidence + self.seq_lr * (1.0 - entry.confidence),
                        1.0,
                    )

                context.append(target_key)
                if len(context) > 8:
                    context = context[-8:]

        n = total_steps or 1
        avg_loss = total_loss / n
        accuracy = correct / n
        self.history.append(avg_loss)

        self.dictionary._rebuild_index()

        return TrainMetrics(
            phase="sequence",
            loss=avg_loss,
            accuracy=accuracy,
            learning_rate=self.seq_lr,
            epoch=0,
            samples=len(batch.examples),
            duration_ms=(time.perf_counter() - start) * 1000.0,
        )
