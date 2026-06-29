# ANGELA-MATRIX: L0[基础层] [A] L1

import logging
import time
from typing import Any, Dict

logger = logging.getLogger(__name__)


class GlobalInputSensor:
    """Global input sensor that monitors user activity across categories."""

    def __init__(self):
        self.activity_count: int = 0
        self.running: bool = False
        self.active_category: str = "neutral"
        self.active_window_title: str = ""
        self._last_activity_time: float = time.time()
        self.category_map: Dict[str, list] = {
            "gaming": ["game", "play", "steam"],
            "coding": ["code", "ide", "pycharm", "vscode"],
            "media": ["music", "video", "youtube", "netflix"],
            "social": ["chat", "discord", "telegram"],
            "browsing": ["browser", "chrome", "firefox"],
        }

    def start(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False

    def sniff_environment(self) -> None:
        title_lower = self.active_window_title.lower()
        found = None
        for category, keywords in self.category_map.items():
            if any(kw in title_lower for kw in keywords):
                found = category
                break
        if found:
            self.active_category = found
        elif self.active_category != "neutral":
            self.active_category = "neutral"
        self._on_activity()

    def _on_activity(self) -> None:
        self.activity_count += 1
        self._last_activity_time = time.time()

    def get_activity_metrics(self) -> Dict[str, Any]:
        now = time.time()
        elapsed = now - self._last_activity_time
        return {
            "seconds_since_last_input": elapsed,
            "input_density_bpm": 0.0,
            "is_user_active": elapsed < 1.0,
            "active_category": self.active_category,
            "window_title": self.active_window_title,
        }
