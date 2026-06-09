# =============================================================================
# ANGELA-MATRIX: [L3] [γ] [C] [L2]
# =============================================================================

import logging
import random
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
        scheduled_sampling_start: float = 1.0,
        scheduled_sampling_end: float = 0.0,
        scheduled_sampling_decay: float = 0.02,
    ):
        self.engine = engine
        self.dictionary: DictionaryLayer = engine.dictionary
        self.network: CoreNetwork = engine.network
        self.seq_lr = seq_lr
        self.history: List[float] = []
        self.scheduled_sampling_prob = scheduled_sampling_start
        self.scheduled_sampling_end = scheduled_sampling_end
        self.scheduled_sampling_decay = scheduled_sampling_decay
        self.scheduled_sampling_start = scheduled_sampling_start

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

                if random.random() < self.scheduled_sampling_prob:
                    context.append(target_key)
                else:
                    predicted = max(activations, key=activations.get) if activations else target_key
                    context.append(predicted)

                if len(context) > 8:
                    context = context[-8:]

        self.scheduled_sampling_prob = max(
            self.scheduled_sampling_end,
            self.scheduled_sampling_prob - self.scheduled_sampling_decay,
        )

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

    def reset_scheduled_sampling(self) -> None:
        self.scheduled_sampling_prob = self.scheduled_sampling_start

    def save(self, path: str) -> None:
        import json, os

        state = {
            "history": self.history,
            "scheduled_sampling_prob": self.scheduled_sampling_prob,
            "seq_lr": self.seq_lr,
            "scheduled_sampling_start": self.scheduled_sampling_start,
            "scheduled_sampling_end": self.scheduled_sampling_end,
            "scheduled_sampling_decay": self.scheduled_sampling_decay,
        }
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        logger.info("SequenceTrainer saved to %s", path)

    @classmethod
    def load(cls, path: str, engine: "ED3NEngine") -> "SequenceTrainer":
        import json

        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)
        trainer = cls(
            engine=engine,
            seq_lr=state.get("seq_lr", 0.1),
            scheduled_sampling_start=state.get("scheduled_sampling_start", 1.0),
            scheduled_sampling_end=state.get("scheduled_sampling_end", 0.0),
            scheduled_sampling_decay=state.get("scheduled_sampling_decay", 0.02),
        )
        trainer.history = state.get("history", [])
        trainer.scheduled_sampling_prob = state.get("scheduled_sampling_prob", trainer.scheduled_sampling_start)
        return trainer


class JointTrainer:
    def __init__(
        self,
        engine: "ED3NEngine",
        dict_lr: float = 0.1,
        network_lr: float = 0.05,
        seq_lr: float = 0.1,
        anchor_weight: float = 0.15,
    ):
        self.engine = engine
        self.dictionary: DictionaryLayer = engine.dictionary
        self.ed3n_trainer = ED3NTrainer(engine, dict_lr, network_lr)
        self.seq_trainer = SequenceTrainer(engine, seq_lr)
        self.anchor_weight = anchor_weight
        self.history: List[Dict[str, float]] = []

    def train_step(
        self,
        batch: TrainingBatch,
        seq_batch: Optional[SeqBatch] = None,
    ) -> TrainMetrics:
        start = time.perf_counter()

        metrics = self.ed3n_trainer.train_step(batch)

        seq_metrics = None
        if seq_batch is not None and seq_batch.examples:
            seq_metrics = self.seq_trainer.train_step(seq_batch)

        anchor_loss = self._compute_anchor_loss(batch)

        loss = metrics.loss
        if seq_metrics is not None:
            loss = (loss + seq_metrics.loss) * 0.5
        loss += anchor_loss * self.anchor_weight

        combined = TrainMetrics(
            phase="joint",
            loss=round(loss, 6),
            accuracy=metrics.accuracy,
            learning_rate=(self.ed3n_trainer.dictionary_lr + self.ed3n_trainer.network_lr) * 0.5,
            epoch=self.ed3n_trainer.current_epoch,
            samples=len(batch.examples) + (len(seq_batch.examples) if seq_batch else 0),
            duration_ms=(time.perf_counter() - start) * 1000.0,
        )
        self.history.append({
            "phase": "joint",
            "loss": combined.loss,
            "accuracy": combined.accuracy,
            "anchor_loss": anchor_loss,
            "samples": combined.samples,
        })
        return combined

    def _compute_anchor_loss(self, batch: TrainingBatch) -> float:
        from .output_anchor import compute_anchor_drift

        if not batch or not batch.examples:
            return 0.0
        total_drift = 0.0
        for ex in batch.examples:
            if ex.input_keys and ex.output_keys:
                total_drift += compute_anchor_drift(
                    ex.input_keys, ex.output_keys, self.dictionary
                )
        return round(total_drift / max(len(batch.examples), 1), 4)

    def get_summary(self) -> Dict[str, Any]:
        if not self.history:
            return {"status": "no_training", "steps": 0}
        last = self.history[-1]
        return {
            "status": "active",
            "steps": len(self.history),
            "last_loss": last["loss"],
            "last_accuracy": last["accuracy"],
            "last_anchor_loss": last.get("anchor_loss", 0.0),
            "anchor_weight": self.anchor_weight,
        }

    def save(self, path: str) -> None:
        import json, os

        state = {
            "anchor_weight": self.anchor_weight,
            "dict_lr": self.ed3n_trainer.dictionary_lr,
            "network_lr": self.ed3n_trainer.network_lr,
            "seq_lr": self.seq_trainer.seq_lr,
            "history": self.history,
        }
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        ed3n_path = path.replace(".json", "_ed3n.json")
        seq_path = path.replace(".json", "_seq.json")
        self.ed3n_trainer.save(ed3n_path)
        self.seq_trainer.save(seq_path)
        logger.info("JointTrainer saved to %s (ed3n: %s, seq: %s)", path, ed3n_path, seq_path)

    @classmethod
    def load(cls, path: str, engine: "ED3NEngine") -> "JointTrainer":
        import json, os

        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)
        trainer = cls(
            engine=engine,
            dict_lr=state.get("dict_lr", 0.1),
            network_lr=state.get("network_lr", 0.05),
            seq_lr=state.get("seq_lr", 0.1),
            anchor_weight=state.get("anchor_weight", 0.15),
        )
        ed3n_path = path.replace(".json", "_ed3n.json")
        seq_path = path.replace(".json", "_seq.json")
        if os.path.exists(ed3n_path):
            loaded = ED3NTrainer.load(ed3n_path)
            trainer.ed3n_trainer.training_history = loaded.training_history
            trainer.ed3n_trainer.current_epoch = loaded.current_epoch
            trainer.ed3n_trainer.best_accuracy = loaded.best_accuracy
        if os.path.exists(seq_path):
            loaded_seq = SequenceTrainer.load(seq_path, engine)
            trainer.seq_trainer.history = loaded_seq.history
            trainer.seq_trainer.scheduled_sampling_prob = loaded_seq.scheduled_sampling_prob
        trainer.history = state.get("history", [])
        return trainer
