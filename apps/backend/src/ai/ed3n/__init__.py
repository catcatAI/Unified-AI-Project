# =============================================================================
# ANGELA-MATRIX: [L3] [γ] [C] [L2]
# =============================================================================

from .continuous_learning import ContinuousLearningPipeline
from .core_network import CoreNetwork, Neuron, RelationGroup
from .dictionary_layer import DictionaryEntry, DictionaryLayer
from .ed3n_engine import ED3NEngine, ReflexLayer
from .ed3n_trainer import ED3NTrainer, JointTrainer, SequenceTrainer
from .io_analyzer import IOAnalyzer
from .output_anchor import ResponseAnchorValidator, anchored_decode, compute_anchor_drift
from .relation_classifier import RelationClassifier, RelationType
from .step_decoder import StepDecoder
from .telemetry import TelemetryCollector
from .training_types import (
    SeqBatch,
    SequenceExample,
    TrainingBatch,
    TrainingExample,
    TrainMetrics,
    make_synthetic_seq_batch,
    seq_batch_from_examples,
    training_example_to_sequence,
)

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
