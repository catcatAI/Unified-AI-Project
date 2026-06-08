# =============================================================================
# ANGELA-MATRIX: [L3] [γ] [C] [L2]
# =============================================================================

from .dictionary_layer import DictionaryEntry, DictionaryLayer
from .relation_classifier import RelationClassifier, RelationType
from .core_network import CoreNetwork, Neuron, RelationGroup
from .output_anchor import ResponseAnchorValidator, anchored_decode, compute_anchor_drift
from .ed3n_engine import ED3NEngine, ReflexLayer
from .io_analyzer import IOAnalyzer
from .telemetry import TelemetryCollector
from .training_types import (
    TrainMetrics,
    TrainingBatch,
    TrainingExample,
    SequenceExample,
    SeqBatch,
    training_example_to_sequence,
    seq_batch_from_examples,
    make_synthetic_seq_batch,
)
from .ed3n_trainer import ED3NTrainer, SequenceTrainer, JointTrainer

from .step_decoder import StepDecoder

__all__ = [
    "DictionaryEntry",
    "DictionaryLayer",
    "RelationClassifier",
    "RelationType",
    "CoreNetwork",
    "Neuron",
    "RelationGroup",
    "ResponseAnchorValidator",
    "anchored_decode",
    "compute_anchor_drift",
    "ED3NEngine",
    "ReflexLayer",
    "IOAnalyzer",
    "TelemetryCollector",
    "TrainMetrics",
    "TrainingBatch",
    "TrainingExample",
    "SequenceExample",
    "SeqBatch",
    "ED3NTrainer",
    "SequenceTrainer",
    "JointTrainer",
    "StepDecoder",
]
