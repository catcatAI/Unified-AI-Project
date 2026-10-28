# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""
AI + AL Joint Training Dataset Loader.
Provides seamless discovery, loading, and batching of AI (cognitive text)
and AL (metabolic/emotional state vectors) data for training pipelines.
"""

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class AlState:
    valence: float
    arousal: float
    dominance: float
    fatigue: float
    stress: float
    health: float
    routing_mode: str


@dataclass
class AiAlRecord:
    sample_id: str
    input_text: str
    expected_response: str
    al_state_in: AlState
    al_state_out: AlState
    intent: str
    confidence: float


class AiAlDatasetLoader:
    """Loader for AI+AL joint training datasets."""

    # 锂定到仓库根，不跟 CWD 走：换个工作目录就在别处建一套 data 树
    DEFAULT_PATH = os.path.join(
        os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")
        ),
        "apps",
        "backend",
        "data",
        "processed",
        "ai_al_pilot_dataset.json",
    )

    def __init__(self, filepath: Optional[str] = None):
        self.filepath = filepath or self.DEFAULT_PATH
        self._records: List[AiAlRecord] = []
        self.load()

    def load(self) -> List[AiAlRecord]:
        """Load and parse the AI+AL dataset from disk."""
        if not os.path.exists(self.filepath):
            # Fallback: try generating if missing
            from ai.core.ai_al_joint_dataset import export_pilot_dataset_json

            export_pilot_dataset_json(self.filepath)

        with open(self.filepath, "r", encoding="utf-8") as f:
            raw = json.load(f)

        self._records = []
        for item in raw.get("examples", []):
            in_s = item["al_state_in"]
            out_s = item["al_state_out"]

            record = AiAlRecord(
                sample_id=item["sample_id"],
                input_text=item["input_text"],
                expected_response=item["expected_response"],
                al_state_in=AlState(
                    in_s["valence"],
                    in_s["arousal"],
                    in_s["dominance"],
                    in_s["fatigue"],
                    in_s["stress"],
                    in_s["health"],
                    in_s["routing_mode"],
                ),
                al_state_out=AlState(
                    out_s["valence"],
                    out_s["arousal"],
                    out_s["dominance"],
                    out_s["fatigue"],
                    out_s["stress"],
                    out_s["health"],
                    out_s["routing_mode"],
                ),
                intent=item["intent"],
                confidence=item.get("confidence", 0.9),
            )
            self._records.append(record)
        return self._records

    def get_all(self) -> List[AiAlRecord]:
        return self._records

    def get_batch(self, batch_size: int = 4) -> List[AiAlRecord]:
        """Return a batch of records for training iteration."""
        return self._records[:batch_size]

    def filter_by_routing_mode(self, mode: str) -> List[AiAlRecord]:
        """Filter records by input routing mode."""
        return [r for r in self._records if r.al_state_in.routing_mode == mode]


# Singleton helper for development tools and training loops
_default_loader: Optional[AiAlDatasetLoader] = None


def get_ai_al_loader() -> AiAlDatasetLoader:
    global _default_loader
    if _default_loader is None:
        _default_loader = AiAlDatasetLoader()
    return _default_loader
