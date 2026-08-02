"""Title screen."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Footer, Label, Static

TITLE_ART = r"""
  +------------------------------------------+
  |      TEXT  ADVENTURE  GAME               |
  |   ED3N/GARDEN + Deterministic Engine     |
  +------------------------------------------+
"""


class TitleScreen(Screen):
    CSS = """
    TitleScreen { align: center middle; }
    #title-art {
        width: 100%; height: auto;
        content-align: center middle; text-align: center;
        color: $accent; padding: 1 0;
    }
    #title-sub {
        width: 100%; height: auto;
        text-align: center; color: $text-muted;
        padding: 0 0 1 0;
    }
    #lang-row {
        width: 40; height: auto;
        layout: horizontal; align: center middle; padding: 1 0;
    }
    #lang-row Label { width: auto; padding: 0 1 0 0; }
    #start-btn {
        width: 30; height: 3; margin: 1 0;
        background: $accent; color: $text;
        text-align: center; content-align: center middle;
    }
    #quit-btn {
        width: 30; height: 3; margin: 0 0 1 0;
        background: $surface; color: $text-muted;
        text-align: center; content-align: center middle;
    }
    """

    BINDINGS = [
        Binding("enter", "select", "Start"),
        Binding("q", "quit", "Quit"),
        Binding("1", "set_lang_zh"),
        Binding("2", "set_lang_en"),
        Binding("3", "set_lang_ja"),
    ]

    def __init__(self, engine, **kwargs):
        super().__init__(**kwargs)
        self.engine = engine

    def compose(self) -> ComposeResult:
        yield Static(TITLE_ART, id="title-art")
        yield Static(self.engine.i18n.t("subtitle"), id="title-sub")
        with Horizontal(id="lang-row"):
            yield Label(self.engine.i18n.t("lang_select"))
            yield Label("1:中文  2:EN  3:日本語")
        yield Static("[ {} ]".format(self.engine.i18n.t("start")), id="start-btn")
        yield Static("[ {} (q) ]".format(self.engine.i18n.t("quit")), id="quit-btn")
        yield Footer()

    def action_select(self) -> None:
        from .screens import WorldSelectScreen
        self.app.push_screen(WorldSelectScreen(self.engine))

    def action_set_lang_zh(self) -> None:
        self.engine.set_language("zh")
        self.app.pop_screen()
        self.app.push_screen(TitleScreen(self.engine))

    def action_set_lang_en(self) -> None:
        self.engine.set_language("en")
        self.app.pop_screen()
        self.app.push_screen(TitleScreen(self.engine))

    def action_set_lang_ja(self) -> None:
        self.engine.set_language("ja")
        self.app.pop_screen()
        self.app.push_screen(TitleScreen(self.engine))

    def action_quit(self) -> None:
        self.app.exit()
