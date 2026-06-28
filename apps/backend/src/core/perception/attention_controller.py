# ANGELA-MATRIX: L0[基础层] [βδ] [A] L1-L2

from enum import Enum, auto
from typing import Any, List, Optional, Tuple

import numpy as np


class AttentionMode(Enum):
    EXPLORE = auto()
    FOCUS = auto()
    TRACK = auto()
    IDLE = auto()


class AttentionController:
    """Attention controller with saliency computation, IOR, and scan path.

    Features:
    - Center-bias + contrast saliency map from visual input
    - Inhibition of Return (IOR) — prevents revisiting recent locations
    - Scan path tracking — records fixation history
    - Candidate scoring by saliency with IOR-aware selection
    """

    def __init__(
        self,
        ior_radius: float = 0.15,
        ior_duration: float = 3.0,
        scan_path_length: int = 5,
    ):
        self.mode: AttentionMode = AttentionMode.EXPLORE
        self.last_focus_pos: Tuple[float, float] = (0.5, 0.5)
        self.current_target_id: Optional[str] = None
        self.last_saccade_time: float = 0.0
        self.ior_radius = ior_radius
        self.ior_duration = ior_duration
        self.scan_path_length = scan_path_length
        self._inhibited_locations: List[Tuple[float, float, float]] = []
        self._scan_path: List[Tuple[float, float, float]] = []
        self._fixation_history: List[Tuple[float, float, float, float]] = []
        self._saliency_map: Optional[np.ndarray] = None
        self._current_time: float = 0.0

    def update_target(
        self, pos: Tuple[float, float], target_id: Optional[str] = None
    ) -> bool:
        self._add_inhibition(self.last_focus_pos)
        self.mode = AttentionMode.FOCUS
        self.last_focus_pos = pos
        self.current_target_id = target_id
        self._fixation_history.append((pos[0], pos[1], self._current_time, 0.3))
        self._scan_path.append((pos[0], pos[1], self._current_time))
        self.last_saccade_time = self._current_time
        return True

    def get_next_focus_point(
        self, candidates: List[Any]
    ) -> Tuple[Tuple[float, float], Optional[str]]:
        if not candidates:
            return self.last_focus_pos, self.current_target_id
        self._prune_inhibition()
        best_score = -1.0
        best_pos = self.last_focus_pos
        best_id = self.current_target_id
        for c in candidates:
            pos, cid, sal = self._parse_candidate(c)
            if sal > best_score and not self._is_inhibited(pos):
                best_score = sal
                best_pos = pos
                best_id = cid
        if best_score > 0:
            self.update_target(best_pos, best_id)
        return best_pos, best_id

    def compute_saliency_map(self, visual_input: np.ndarray) -> np.ndarray:
        h, w = visual_input.shape[:2]
        center = np.array([h / 2.0, w / 2.0])
        yy, xx = np.ogrid[:h, :w]
        dist = np.sqrt((xx - center[1]) ** 2 + (yy - center[0]) ** 2)
        center_bias = 1.0 - dist / dist.max()
        gray = np.mean(visual_input, axis=2) if visual_input.ndim == 3 else visual_input
        local_std = self._local_std(gray, max(5, min(h, w) // 16))
        contrast = local_std / (local_std.max() + 1e-8)
        saliency = 0.6 * center_bias + 0.4 * contrast
        self._saliency_map = saliency
        return saliency

    @staticmethod
    def _local_std(arr: np.ndarray, kernel: int) -> np.ndarray:
        from scipy.ndimage import uniform_filter
        mean = uniform_filter(arr, kernel)
        mean_sq = uniform_filter(arr ** 2, kernel)
        return np.sqrt(np.maximum(mean_sq - mean ** 2, 0))

    @staticmethod
    def _parse_candidate(candidate: Any) -> Tuple[Tuple[float, float], Optional[str], float]:
        if isinstance(candidate, tuple):
            if len(candidate) == 2:
                return candidate[0], candidate[1], 1.0
            if len(candidate) >= 3:
                return candidate[0], candidate[1], float(candidate[2])
        if isinstance(candidate, dict):
            return (
                candidate.get("position", (0.5, 0.5)),
                candidate.get("id"),
                float(candidate.get("saliency", 0.5)),
            )
        return (0.5, 0.5), None, 0.0

    def _is_inhibited(self, pos: Tuple[float, float]) -> bool:
        self._prune_inhibition()
        return any(
            ((pos[0] - ix) ** 2 + (pos[1] - iy) ** 2) < self.ior_radius ** 2
            for ix, iy, _ in self._inhibited_locations
        )

    def _add_inhibition(self, pos: Tuple[float, float]) -> None:
        self._inhibited_locations.append((pos[0], pos[1], self._current_time + self.ior_duration))

    def _prune_inhibition(self) -> None:
        self._inhibited_locations = [
            loc for loc in self._inhibited_locations if loc[2] > self._current_time
        ]

    def get_scan_path(self) -> List[Tuple[float, float, float]]:
        return self._scan_path.copy()

    def get_fixation_history(self) -> List[Tuple[float, float, float, float]]:
        return self._fixation_history.copy()

    def set_time(self, t: float) -> None:
        self._current_time = t

    def get_saliency_at(self, pos: Tuple[float, float]) -> float:
        if self._saliency_map is None:
            return 0.5
        h, w = self._saliency_map.shape
        x = max(0, min(w - 1, int(pos[0] * w)))
        y = max(0, min(h - 1, int(pos[1] * h)))
        return float(self._saliency_map[y, x])

    def reset(self) -> None:
        self.mode = AttentionMode.EXPLORE
        self.current_target_id = None
        self.last_focus_pos = (0.5, 0.5)
        self._inhibited_locations.clear()
        self._scan_path.clear()
        self._fixation_history.clear()
        self._saliency_map = None
        self._current_time = 0.0
