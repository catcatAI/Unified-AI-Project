# ANGELA-MATRIX: L0[基础层] [A] L1

from enum import Enum, auto
from typing import Any, List, Optional, Tuple


class AttentionMode(Enum):
    EXPLORE = auto()
    FOCUS = auto()
    TRACK = auto()
    IDLE = auto()


class AttentionController:
    def __init__(self):
        self.mode: AttentionMode = AttentionMode.EXPLORE
        self.last_focus_pos: Tuple[float, float] = (0.5, 0.5)
        self.current_target_id: Optional[str] = None
        self.last_saccade_time: float = 0.0

    def update_target(self, pos: Tuple[float, float], target_id: Optional[str] = None) -> bool:
        self.mode = AttentionMode.FOCUS
        self.last_focus_pos = pos
        self.current_target_id = target_id
        return True

    def get_next_focus_point(self, candidates: List[Any]) -> Tuple[Tuple[float, float], Optional[str]]:
        return self.last_focus_pos, self.current_target_id

    def reset(self) -> None:
        self.mode = AttentionMode.EXPLORE
        self.current_target_id = None
        self.last_focus_pos = (0.5, 0.5)
