# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Tuple


@dataclass
class TrainingExample:
    input_text: str
    expected_output: str
    input_keys: List[str]
    output_keys: List[str]
    relation_pairs: List[Tuple[str, str, str]]  # (key1, relation_type, key2)
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrainingBatch:
    examples: List[TrainingExample]
    batch_id: str
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TrainMetrics:
    phase: str  # "dictionary" | "network"
    loss: float
    accuracy: float
    learning_rate: float
    epoch: int
    samples: int
    duration_ms: float


@dataclass
class SequenceExample:
    input_text: str
    target_text: str
    input_key_seq: List[str]
    target_key_seq: List[str]
    confidence: float = 0.8
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SeqBatch:
    examples: List[SequenceExample]
    batch_id: str
    created_at: datetime = field(default_factory=datetime.now)


def training_example_to_sequence(ex: TrainingExample) -> SequenceExample:
    """Convert a TrainingExample (set-based keys) to SequenceExample (sequential)."""
    return SequenceExample(
        input_text=ex.input_text,
        target_text=ex.expected_output,
        input_key_seq=list(ex.input_keys),
        target_key_seq=list(ex.output_keys),
        confidence=ex.confidence,
        metadata=ex.metadata,
    )


def seq_batch_from_examples(
    examples: List[TrainingExample],
    batch_id: str = "",
) -> SeqBatch:
    """Convert a list of TrainingExamples into a SeqBatch.

    Each TrainingExample's input_keys become the input_key_seq
    and output_keys become the target_key_seq.
    """
    seq_examples = [training_example_to_sequence(ex) for ex in examples]
    return SeqBatch(
        examples=seq_examples,
        batch_id=batch_id or f"seq_{datetime.now().isoformat()}",
    )


def make_synthetic_seq_batch(
    sequences: List[Tuple[List[str], List[str]]],
    batch_id: str = "synthetic",
) -> SeqBatch:
    """Create a SeqBatch from raw (input_seq, target_seq) pairs.

    Args:
        sequences: List of (input_key_sequence, target_key_sequence) tuples.
        batch_id: Identifier for the batch.

    Returns:
        A SeqBatch ready for SequenceTrainer.
    """
    examples = [
        SequenceExample(
            input_text=" ".join(inp),
            target_text=" ".join(tgt),
            input_key_seq=list(inp),
            target_key_seq=list(tgt),
            confidence=0.8,
        )
        for inp, tgt in sequences
    ]
    return SeqBatch(examples=examples, batch_id=batch_id)
