"""Textual TUI — main app entry point."""
from __future__ import annotations

from textual.app import App

from .engine import GameEngine
from .title_screen import TitleScreen


class GameApp(App):
    """Text adventure TUI with multi-screen flow."""

    def __init__(self, engine: GameEngine, **kwargs):
        super().__init__(**kwargs)
        self.engine = engine

    def on_mount(self) -> None:
        self.push_screen(TitleScreen(self.engine))


def run_game():
    """Entry point — start the TUI."""
    engine = GameEngine()
    app = GameApp(engine)
    app.run()


if __name__ == "__main__":
    run_game()
