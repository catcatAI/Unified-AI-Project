"""Shared widgets for the game TUI."""
from __future__ import annotations

from textual.widgets import Static


class BarWidget(Static):
    """Reusable stat bar display."""

    @staticmethod
    def make_bar(current: int, maximum: int, width: int = 10) -> str:
        filled = int(current / maximum * width) if maximum > 0 else 0
        return "\u2588" * filled + "\u2591" * (width - filled)
