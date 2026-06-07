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
