"""World select, character select, game, and game-over screens."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Label, Static

from .token_effects import apply_token_hp, apply_token_spirit, apply_token_skill_bonus


# ─────────────── World Select ───────────────

class WorldSelectScreen(Screen):
    CSS = """
    WorldSelectScreen { align: center middle; layout: vertical; }
    #ws-title {
        width: 100%; height: auto; text-align: center;
        text-style: bold; padding: 1 0; color: $accent;
    }
    .world-card {
        width: 60; height: auto;
        border: solid $primary; padding: 1 2; margin: 1 0;
    }
    #ws-back {
        width: 20; height: 3; margin: 1 0;
        text-align: center; content-align: center middle;
        background: $surface; color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("1", "select_w01"),
        Binding("2", "select_w02"),
        Binding("escape", "go_back"),
    ]

    def __init__(self, engine, **kwargs):
        super().__init__(**kwargs)
        self.engine = engine

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(self.engine.i18n.t("world_select"), id="ws-title")
        for i, w in enumerate(self.engine.get_worlds(), 1):
            yield Static(
                "[b]({}) {}[/b]\n{}".format(i, w["name"], w["desc"]),
                classes="world-card",
            )
        yield Static("[ {} (Esc) ]".format(self.engine.i18n.t("back")), id="ws-back")
        yield Footer()

    def action_select_w01(self) -> None:
        self.engine.selected_world = "W01"
        self.app.push_screen(CharacterSelectScreen(self.engine))

    def action_select_w02(self) -> None:
        self.engine.selected_world = "W02"
        self.app.push_screen(CharacterSelectScreen(self.engine))

    def action_go_back(self) -> None:
        self.app.pop_screen()


# ─────────────── Character Select ───────────────

class CharacterSelectScreen(Screen):
    CSS = """
    CharacterSelectScreen { layout: horizontal; }
    #cs-list {
        width: 1fr; height: 100%;
        border: solid $primary; padding: 1 2; overflow-y: auto;
    }
    #cs-detail {
        width: 1fr; height: 100%;
        border: solid $accent; padding: 1 2;
    }
    .char-item { height: 1; padding: 0 0; }
    .char-selected { background: $accent; color: $text; }
    #cs-page {
        width: 100%; height: 1; text-align: center;
        color: $text-muted; padding: 0 0;
    }
    #cs-confirm {
        width: 20; height: 3; margin: 1 0 0 0;
        background: $accent; color: $text;
        text-align: center; content-align: center middle;
    }
    #cs-back {
        width: 20; height: 3; margin: 1 0 0 0;
        background: $surface; color: $text-muted;
        text-align: center; content-align: center middle;
    }
    """

    BINDINGS = [
        Binding("escape", "go_back"),
        Binding("enter", "confirm_selection"),
        Binding("up", "cursor_up"),
        Binding("down", "cursor_down"),
    ]

    PAGE_SIZE = 20

    def __init__(self, engine, **kwargs):
        super().__init__(**kwargs)
        self.engine = engine
        self._chars = engine.get_characters()
        self._selected_idx = 0
        self._page_start = 0

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with VerticalScroll(id="cs-list"):
                yield Static(
                    "[b]{}[/b] [dim]({} chars, ↑↓ scroll, Enter confirm)[/dim]".format(
                        self.engine.i18n.t("char_select"), len(self._chars)
                    ),
                    id="cs-title",
                )
                yield from self._char_labels()
                yield Static(
                    "[ {} (Enter) ]".format(self.engine.i18n.t("confirm")),
                    id="cs-confirm",
                )
                yield Static(
                    "[ {} (Esc) ]".format(self.engine.i18n.t("back")),
                    id="cs-back",
                )
            with Vertical(id="cs-detail"):
                yield Static(self.engine.i18n.t("char_select"), id="cs-detail-text")
        yield Footer()

    def _char_labels(self):
        end = min(self._page_start + self.PAGE_SIZE, len(self._chars))
        for i in range(self._page_start, end):
            c = self._chars[i]
            cls = "char-selected" if i == self._selected_idx else "char-item"
            yield Static(
                "({}) {}".format(i + 1, c["name"]),
                classes=cls,
                id="char-{}".format(i),
            )

    def on_mount(self) -> None:
        self._update_detail()

    def _update_detail(self) -> None:
        if not self._chars:
            return
        c = self._chars[self._selected_idx]
        tokens = c.get("tokens", [])
        max_hp, hp = apply_token_hp(tokens)
        max_sp, sp = apply_token_spirit(tokens)
        sk_bonus = apply_token_skill_bonus(tokens)
        sk = min(50 + sk_bonus, 100)

        cats = {}
        for t in tokens:
            cat = t.get("category", "unknown")
            cats[cat] = cats.get(cat, 0) + 1
        token_summary = ", ".join(f"{k}:{v}" for k, v in sorted(cats.items(), key=lambda x: -x[1]))

        detail = (
            "[b]{}[/b] ({}/{})\n\n"
            "{}\n\n"
            "HP: {}/{} | SP: {}/{} | SK: {}/{}\n\n"
            "[b]Tokens ({})[/b]\n{}"
        ).format(
            c["name"], self._selected_idx + 1, len(self._chars),
            c.get("description", ""),
            hp, max_hp, sp, max_sp, sk, 100,
            len(tokens),
            token_summary,
        )
        detail_text = self.query_one("#cs-detail-text", Static)
        detail_text.update(detail)

    def _refresh_list(self) -> None:
        """Re-render the visible character list."""
        list_widget = self.query_one("#cs-list", VerticalScroll)
        # Remove old char labels
        for child in list_widget.children:
            if hasattr(child, 'id') and child.id and child.id.startswith("char-"):
                child.remove()
        # Re-add visible labels
        end = min(self._page_start + self.PAGE_SIZE, len(self._chars))
        for i in range(self._page_start, end):
            c = self._chars[i]
            cls = "char-selected" if i == self._selected_idx else "char-item"
            label = Static(
                "({}) {}".format(i + 1, c["name"]),
                classes=cls,
                id="char-{}".format(i),
            )
            # Insert before confirm button
            confirm_btn = self.query_one("#cs-confirm", Static)
            confirm_btn.mount(label)

    def action_cursor_up(self) -> None:
        if self._selected_idx > 0:
            self._selected_idx -= 1
            if self._selected_idx < self._page_start:
                self._page_start = max(0, self._page_start - self.PAGE_SIZE)
            self._update_detail()
            self._refresh_list()

    def action_cursor_down(self) -> None:
        if self._selected_idx < len(self._chars) - 1:
            self._selected_idx += 1
            if self._selected_idx >= self._page_start + self.PAGE_SIZE:
                self._page_start += self.PAGE_SIZE
            self._update_detail()
            self._refresh_list()

    def on_key(self, event) -> None:
        key = event.key
        if key.isdigit() and len(key) == 1:
            # Direct number input for quick select (1-9)
            idx = int(key) - 1 + self._page_start
            if 0 <= idx < len(self._chars):
                self._selected_idx = idx
                self._update_detail()
                self._refresh_list()

    def action_confirm_selection(self) -> None:
        if not self._chars:
            return
        c = self._chars[self._selected_idx]
        self.engine.new_game(pc_card_id=c["card_id"])
        self.app.push_screen(GameScreen(self.engine))

    def action_go_back(self) -> None:
        self.app.pop_screen()


# ─────────────── Game Screen ───────────────

class CharPanel(Static):
    def update_display(self, engine) -> None:
        pc = engine.state.pc
        lines = [
            "[b]{}[/b] ({})".format(pc.name, pc.card_id),
            "",
            "HP  {} {}/{}".format(pc.hp_bar, pc.hp, pc.max_hp),
            "SP  {} {}/{}".format(pc.spirit_bar, pc.spirit, pc.max_spirit),
            "SK  {} {}/{}".format(pc.skill_bar, pc.skill, pc.max_skill),
            "",
            "-- {} --".format(engine.i18n.t("equip")),
        ]
        if pc.equipment:
            for slot, item in pc.equipment.items():
                lines.append("  {}: {}".format(slot, item))
        else:
            lines.append("  {}".format(engine.i18n.t("none")))
        lines.append("")
        lines.append("-- {} --".format(engine.i18n.t("inventory")))
        if pc.inventory:
            for item in pc.inventory:
                lines.append("  * {}".format(item))
        else:
            lines.append("  {}".format(engine.i18n.t("empty")))
        self.update("\n".join(lines))


class ScenePanel(Static):
    def update_display(self, engine) -> None:
        sc = engine.state.scene
        lines = [
            "[b]{}[/b]".format(sc.name),
            "",
            "  {}".format(sc.description[:40] if sc.description else "..."),
            "",
            engine.i18n.t("scene_spirit_density", density=sc.spirit_density),
        ]
        if sc.temperature:
            lines.append(engine.i18n.t("scene_temperature", temp=sc.temperature))
        if sc.characters:
            lines.append("")
            lines.append("-- {} --".format(engine.i18n.t("nearby")))
            for c in sc.characters[:5]:
                c = c.strip()
                if c:
                    lines.append("  * {}".format(c))
        if sc.tokens:
            lines.append("")
            lines.append("-- {} --".format(engine.i18n.t("scene_info")))
            for t in sc.tokens[:4]:
                lines.append("  {}: {}".format(
                    t.get("name", ""), str(t.get("value", ""))[:30]
                ))
        self.update("\n".join(lines))


class MessageLog(VerticalScroll):
    MAX_WIDGETS = 200

    def add_message(self, msg) -> None:
        if msg.kind == "narration":
            styled = "[i dim]{}[/i dim]".format(msg.text)
        elif msg.kind == "action":
            styled = "[b cyan]> {}[/b cyan]".format(msg.text)
        elif msg.kind == "system":
            styled = "[yellow]{}[/yellow]".format(msg.text)
        else:
            styled = "[bold green]{}:[/bold green] {}".format(msg.speaker, msg.text)
        widget = Static(styled)
        self.mount(widget)
        # Prune old widgets to prevent unbounded DOM growth
        while len(self.children) > self.MAX_WIDGETS:
            self.children[0].remove()
        self.scroll_end(animate=False)


class ChoiceList(Vertical):
    def update_choices(self, choices) -> None:
        self.remove_children()
        for i, choice in enumerate(choices, 1):
            self.mount(Label("  [{}] {}".format(i, choice), classes="choice-item"))


class StatusBar(Static):
    def update_display(self, engine) -> None:
        s = engine.state
        text = "  {} {} | {} | HP:{}/{} | SP:{}/{}".format(
            engine.i18n.t("turn"), s.turn, s.scene.name,
            s.pc.hp, s.pc.max_hp, s.pc.spirit, s.pc.max_spirit,
        )
        self.update(text)


class GameScreen(Screen):
    CSS = """
    Screen {
        layout: grid; grid-size: 3;
        grid-columns: 1fr 2fr 1fr; grid-rows: 1fr auto;
    }
    #body { row-span: 1; column-span: 3; }
    CharPanel {
        height: 100%; border: solid $primary; padding: 1 2;
    }
    ScenePanel {
        height: 100%; border: solid $accent; padding: 1 2;
    }
    #center { height: 100%; border: solid $secondary; padding: 0; }
    MessageLog { height: 1fr; padding: 1 2; }
    ChoiceList {
        height: auto; max-height: 8; padding: 0 2;
        background: $surface;
    }
    ChoiceList Label { height: auto; }
    #input-hint {
        dock: bottom; height: 1; padding: 0 2;
        background: $surface; color: $text-muted;
    }
    #input-bar {
        dock: bottom; height: 3; padding: 0 2;
    }
    Input { width: 100%; }
    StatusBar {
        dock: bottom; height: 1;
        background: $primary; color: $text;
    }
    """

    BINDINGS = [
        Binding("q", "quit_game", "Quit"),
        Binding("c", "clear_log", "Clear"),
    ]

    def __init__(self, engine, **kwargs):
        super().__init__(**kwargs)
        self.engine = engine
        self._displayed_count = 0

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="body"):
            yield CharPanel(id="char-panel")
            with Vertical(id="center"):
                yield MessageLog(id="message-log")
                yield ChoiceList(id="choice-list")
            yield ScenePanel(id="scene-panel")
        yield Static(
            "[dim]1-8: choose | attack/fight: combat | rest: heal | go/move: advance | look: observe | talk: NPC | quest: quests | q: quit[/dim]",
            id="input-hint",
        )
        yield Input(
            placeholder=self.engine.i18n.t("input_hint"), id="input-bar"
        )
        yield StatusBar(id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_all()
        log = self.query_one("#message-log", MessageLog)
        for msg in self.engine.state.messages:
            log.add_message(msg)
        self._displayed_count = len(self.engine.state.messages)

    def _refresh_all(self) -> None:
        self.query_one("#char-panel", CharPanel).update_display(self.engine)
        self.query_one("#scene-panel", ScenePanel).update_display(self.engine)
        self.query_one("#choice-list", ChoiceList).update_choices(
            self.engine.state.choices
        )
        self.query_one("#status-bar", StatusBar).update_display(self.engine)

    def on_input_submitted(self, event) -> None:
        text = event.value.strip()
        event.input.value = ""
        if not text:
            return
        self.engine.process_input(text)
        log = self.query_one("#message-log", MessageLog)
        for msg in self.engine.state.messages[self._displayed_count:]:
            log.add_message(msg)
        self._displayed_count = len(self.engine.state.messages)
        self._refresh_all()
        if self.engine.is_game_over():
            from .gameover_screen import GameOverScreen
            self.app.push_screen(GameOverScreen(self.engine))

    def action_quit_game(self) -> None:
        self.engine.state.quit = True
        from .gameover_screen import GameOverScreen
        self.app.push_screen(GameOverScreen(self.engine))

    def action_clear_log(self) -> None:
        self.query_one("#message-log", MessageLog).remove_children()
