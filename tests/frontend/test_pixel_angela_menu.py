"""
The pixel-angela right-click menu must not contain decorative items.

WHY: six of its seven items were created with ``addAction("…")`` and never
connected to anything, so a user right-clicking the character and picking
"LLM Control" / "RAG Knowledge" / "Bionics Dynamics" / "Angela Core" got no
reaction at all — the only working item was Exit. PyQt does not warn about
unconnected actions, and the file imports cleanly, so nothing else surfaced it.

Two rules are enforced here:
  1. every advertised action is wired to a callable that exists, and
  2. the things the labels promise are actually reachable — the two items kept
     (Pixel Physics, Default Render) must really drive renderer state.

This is the same defect class as the Electron tray/context menus, so it is
guarded the same way.
"""

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RENDERER = ROOT / "apps/pixel-angela/renderer.py"
SOURCE = RENDERER.read_text(encoding="utf-8")

# Labels that promised a control with nothing behind it. If a future backend
# message or HTTP client makes one of them real, move it to WIRED_LABELS with a
# test that proves the wiring.
UNIMPLEMENTED_LABELS = ("LLM Control", "RAG Knowledge", "Bionics Dynamics", "Angela Core")
WIRED_LABELS = ("Pixel Physics", "Default Render", "Exit")


def _menu_source() -> str:
    return SOURCE[SOURCE.index("def _init_tiered_menu(self):"): SOURCE.index("def _on_tray_activated")]


def _add_action_labels() -> list:
    return re.findall(r'addAction\(\s*"([^"]+)"', _menu_source())


class TestPixelAngelaMenu:
    def test_menu_definition_is_parseable(self):
        ast.parse(SOURCE)

    def test_every_advertised_action_is_connected(self):
        """An addAction without .triggered.connect(...) is a dead menu item.

        Handles both wiring styles: `menu.addAction("X").triggered.connect(fn)`
        and the two-step `self._x_action = menu.addAction("X")` followed by
        `self._x_action.triggered.connect(fn)`.
        """
        menu = _menu_source()
        dead = []
        # variable name -> label, for the two-step form
        pending: dict = {}
        for line in menu.split("\n"):
            assigned = re.search(r"self\.(\w+)\s*=\s*\w+\.addAction\(\s*\"([^\"]+)\"", line)
            if assigned:
                pending[assigned.group(1)] = assigned.group(2)
                continue
            connected = re.search(r"self\.(\w+)\.triggered\.connect\(", line)
            if connected:
                pending.pop(connected.group(1), None)
                continue
            inline = re.search(r'addAction\(\s*"([^"]+)"', line)
            if inline and ".triggered.connect(" not in line:
                dead.append(inline.group(1))
        dead.extend(pending.values())
        assert not dead, f"menu items with no handler: {dead}"

    def test_no_unimplemented_features_are_advertised(self):
        labels = _add_action_labels()
        for label in UNIMPLEMENTED_LABELS:
            assert label not in labels, (
                f"{label!r} is offered but has no backend control and no local "
                "implementation — a menu entry that cannot work"
            )

    @pytest.mark.parametrize("label", WIRED_LABELS)
    def test_wired_items_exist_in_the_menu(self, label):
        assert label in _add_action_labels()

    def test_pixel_physics_toggles_real_renderer_state(self):
        handler = SOURCE[SOURCE.index("def _on_toggle_pixel_physics"):]
        handler = handler[: handler.index("def _on_reset_render")]
        assert "self.physics_enabled" in handler

    def test_physics_loop_honours_the_flag(self):
        loop = SOURCE[SOURCE.index("def physics_and_render_loop"):]
        loop = loop[: loop.index("def show_native_input")]
        assert "if not self.physics_enabled:" in loop, (
            "the flag must short-circuit the physics integration, otherwise the "
            "menu item only changes a field nothing reads"
        )
        assert "self.dna.apply_dynamics" in loop

    def test_default_render_resets_real_state(self):
        handler = SOURCE[SOURCE.index("def _on_reset_render"):]
        handler = handler[: handler.index("def _on_tray_activated")]
        for field in ("angela_pos", "bubble_stack", "state", "physics_enabled"):
            assert field in handler, f"Default Render does not reset {field}"

    def test_state_flag_is_initialised(self):
        assert "self.physics_enabled = True" in SOURCE


class TestPixelAngelaTactilePath:
    def test_stiffness_is_bound_before_use(self):
        """stiffness used to be bound inside the bounds check and read outside."""
        press = SOURCE[SOURCE.index("def mousePressEvent"):]
        press = press[: press.index("def update_state")]
        assert re.search(r"stiffness\s*=\s*0\.0", press), (
            "stiffness must be initialised before the hit-test branch reads it"
        )

    def test_tactile_send_goes_through_the_client(self):
        """Reaching into client.ws raises when the socket is reconnecting."""
        press = SOURCE[SOURCE.index("def mousePressEvent"):]
        press = press[: press.index("def update_state")]
        assert "self.client.ws.send(" not in press, "must not touch client.ws directly"
        assert "self.client.send_event(" in press
        assert "self.client.event_loop is not None" in press

    def test_client_exposes_send_event(self):
        assert "async def send_event(self, payload):" in SOURCE
