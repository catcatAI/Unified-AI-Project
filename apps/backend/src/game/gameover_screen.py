"""Game over screen."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Static


class GameOverScreen(Screen):
    CSS = """
    GameOverScreen { align: center middle; layout: vertical; }
    #go-title {
        width: 100%; height: auto; text-align: center;
        text-style: bold; color: $error; padding: 2 0;
    }
    #go-msg {
        width: 100%; height: auto; text-align: center;
        padding: 1 0; color: $text;
    }
    #go-summary {
        width: 60; height: auto;
        border: solid $primary; padding: 1 2; margin: 1 0;
    }
    #go-restart {
        width: 30; height: 3; margin: 1 0;
        background: $accent; color: $text;
        text-align: center; content-align: center middle;
    }
    #go-quit {
        width: 30; height: 3; margin: 0 0 1 0;
        background: $surface; color: $text-muted;
        text-align: center; content-align: center middle;
    }
    """

    BINDINGS = [
        Binding("enter", "restart"),
        Binding("q", "quit"),
    ]

    def __init__(self, engine, **kwargs):
        super().__init__(**kwargs)
        self.engine = engine

    def compose(self) -> ComposeResult:
        s = self.engine.state
        i18n = self.engine.i18n

        if s.quit:
            title = i18n.t("gameover_quit")
        elif s.pc.hp <= 0:
            title = i18n.t("gameover_lose")
        else:
            title = i18n.t("gameover_win")

        summary_lines = [
            "[b]{}[/b]".format(i18n.t("summary")),
            "",
            "{}: {}".format(s.pc.name, s.pc.card_id),
            "HP:  {}/{}".format(s.pc.hp, s.pc.max_hp),
            "SP:  {}/{}".format(s.pc.spirit, s.pc.max_spirit),
            "SK:  {}/{}".format(s.pc.skill, s.pc.max_skill),
            "{}: {}".format(i18n.t("total_turns"), s.turn),
            "{}: {}".format(i18n.t("scene_info"), s.scene.name),
        ]

        yield Static(i18n.t("gameover"), id="go-title")
        yield Static(title, id="go-msg")
        yield Static("\n".join(summary_lines), id="go-summary")
        yield Static("[ {} (Enter) ]".format(i18n.t("play_again")), id="go-restart")
        yield Static("[ {} (q) ]".format(i18n.t("quit")), id="go-quit")
        yield Footer()

    def action_restart(self) -> None:
        from .title_screen import TitleScreen
        while len(self.app.screen_stack) > 1:
            self.app.pop_screen()
        self.app.push_screen(TitleScreen(self.engine))

    def action_quit(self) -> None:
        self.app.exit()
