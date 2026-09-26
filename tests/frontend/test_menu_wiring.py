"""
Every tray / context-menu item must reach a real handler.

WHY: the desktop menus were full of items that did nothing, and nothing failed
loudly:

  * ``tray-manager.js:updateMenu()`` replaced each item's own ``click`` arrow
    with ``_handleItemClick(item)``, which looks up ``callbacks[item.id]`` — the
    *menu id* ('show', 'hide', 'about', 'start', 'stop', 'restart') — while
    ``main.js`` registers the *handler names* ('showWindow', 'hideWindow', …).
    7 of 9 tray items were dead even though ``_onShowWindow()`` and friends
    existed and were correct.
  * Five main-process context-menu channels (``reload-model``,
    ``always-on-top-changed``, ``performance-mode-changed``,
    ``wallpaper-mode-changed``, ``module-toggle``) were sent to the renderer,
    which had no listener anywhere.
  * ``hapticHandler`` has no ``setEnabled()``, although ``app.js`` probes for
    exactly that name — so the Tactile checkbox could never apply.
  * ``toggleModule`` returned ``true`` unconditionally, reporting success for
    modules that have no switch at all.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TRAY = ROOT / "apps/desktop-app/electron_app/js/tray-manager.js"
MAIN = ROOT / "apps/desktop-app/electron_app/main.js"
APP = ROOT / "packages/shared-js/js/app.js"
HAPTIC = ROOT / "packages/shared-js/js/haptic-handler.js"
PRELOAD = ROOT / "apps/desktop-app/electron_app/preload.js"

# 「启动Angela」/「停止Angela」 are intentionally gone: the Electron main process
# does not own the backend lifecycle, so they could never do anything.
TRAY_ITEMS = ("show", "hide", "settings", "about", "restart", "quit")
HANDLER_NAMES = ("showWindow", "hideWindow", "settings", "about", "restart", "quit")
UNIMPLEMENTABLE_ITEMS = ("start", "stop")
MENU_CHANNELS = (
    "reload-model",
    "always-on-top-changed",
    "performance-mode-changed",
    "wallpaper-mode-changed",
    "module-toggle",
)


class TestTrayMenu:
    def test_every_default_item_brings_its_own_click_handler(self):
        """The template must not drop item.click."""
        text = TRAY.read_text(encoding="utf-8")
        build = text[text.index("const template = items.map"): text.index("Menu.buildFromTemplate")]
        assert "item.click" in build, (
            "updateMenu() must call the item's own click handler; replacing it with "
            "callbacks[item.id] silently disabled every item whose id differs from "
            "the registered callback name"
        )

    def test_dispatch_prefers_item_handler_and_falls_back_to_id(self):
        text = TRAY.read_text(encoding="utf-8")
        dispatch = text[text.index("_handleItemClick(item, itemClick) {"):]
        dispatch = dispatch[: dispatch.index("\n  }\n")]
        assert "typeof itemClick === 'function'" in dispatch
        assert "this.callbacks[item.id]" in dispatch
        # A missing handler must be visible in the log, not a silent no-op.
        assert "console.warn" in dispatch

    def test_all_default_items_have_a_click_handler(self):
        text = TRAY.read_text(encoding="utf-8")
        defaults = text[text.index("_createDefaultMenu() {"): text.index("this.updateMenu(menuItems)")]
        for item_id in TRAY_ITEMS:
            entry = re.search(rf"id: '{item_id}',[^\n]*", defaults)
            assert entry, f"tray item {item_id!r} missing"
            assert "click:" in entry.group(0), f"tray item {item_id!r} has no click handler"

    @pytest.mark.parametrize("handler", HANDLER_NAMES)
    def test_main_registers_the_handler_the_default_items_reach(self, handler):
        """Every advertised item must have a registered callback behind it."""
        text = MAIN.read_text(encoding="utf-8")
        assert f"trayManager.on('{handler}'" in text, f"main.js never registers {handler!r}"

    @pytest.mark.parametrize("item", UNIMPLEMENTABLE_ITEMS)
    def test_unimplementable_items_are_not_advertised(self, item):
        """A menu entry that cannot work must not be offered."""
        text = TRAY.read_text(encoding="utf-8")
        defaults = text[text.index("_createDefaultMenu() {"): text.index("this.updateMenu(menuItems)")]
        assert f"id: '{item}'" not in defaults, (
            f"tray still offers {item!r} although the Electron main process does "
            "not own the backend lifecycle"
        )


class TestContextMenuChannels:
    @pytest.mark.parametrize("channel", MENU_CHANNELS)
    def test_main_sends_a_channel_the_renderer_handles(self, channel):
        main = MAIN.read_text(encoding="utf-8")
        app = APP.read_text(encoding="utf-8")
        assert f"'{channel}'" in main, f"main.js does not send {channel!r}"
        assert f"'{channel}'" in app, f"app.js has no listener for {channel!r}"

    @pytest.mark.parametrize("channel", MENU_CHANNELS)
    def test_channel_is_allowed_by_the_preload_bridge(self, channel):
        """preload drops channels outside validChannels — silently."""
        preload = PRELOAD.read_text(encoding="utf-8")
        block = preload[preload.index("const validChannels = ["):]
        block = block[: block.index("]")]
        assert f"'{channel}'" in block, f"preload would drop {channel!r}"

    @pytest.mark.parametrize(
        "channel,target",
        [
            ("performance-mode-changed", "setPerformanceMode"),
            ("wallpaper-mode-changed", "setRenderingMode"),
            ("reload-model", "switchToLive2D"),
        ],
    )
    def test_handler_calls_a_method_that_actually_exists(self, channel, target):
        app = APP.read_text(encoding="utf-8")
        handler = app[app.index(f"'{channel}'"):]
        handler = handler[: handler.index("\n    })")]
        assert target in handler, f"{channel} does not use the real {target}()"

    def test_module_toggle_warns_when_a_module_has_no_switch(self):
        app = APP.read_text(encoding="utf-8")
        toggle = app[app.index("_setupMainMenuChannels() {"): app.index("_setupKeyboardShortcuts() {")]
        assert "module-toggle" in toggle
        assert "warn('module-toggle'" in toggle, "a module without a switch must be reported"


class TestModuleToggleHonesty:
    def test_toggle_module_does_not_always_return_true(self):
        app = APP.read_text(encoding="utf-8")
        block = app[app.index("this.toggleModule = (module, enabled) => {"):]
        block = block[: block.index("\n    }\n")]
        assert "return true //" not in block
        # Every branch must be able to report "not applied".
        assert block.count("return false") >= 2

    def test_haptic_handler_exposes_set_enabled(self):
        text = HAPTIC.read_text(encoding="utf-8")
        assert "  setEnabled(enabled)" in text, (
            "app.js probes for hapticHandler.setEnabled; without it the Tactile "
            "System checkbox silently does nothing"
        )


class TestToggleFrameKeepsTheWindowWired:
    def test_toggle_frame_re_attaches_the_lost_listeners(self):
        main = MAIN.read_text(encoding="utf-8")
        block = main[main.index("label: 'Toggle Frame'"):]
        block = block[: block.index("mainWindow = newWin")]
        for marker in ("attachContextMenu(newWin)", "ready-to-show", "on('moved'", "setMinimumSize"):
            assert marker in block, f"Toggle Frame lost {marker}"

    def test_context_menu_template_is_shared_not_duplicated(self):
        main = MAIN.read_text(encoding="utf-8")
        assert main.count("Menu.buildFromTemplate([") == 1, (
            "the context-menu template must exist once; a second copy drifts"
        )
        assert "function buildContextMenuTemplate()" in main
        assert main.count("attachContextMenu(") >= 3  # definition + both call sites


class TestIpcBridgeCompleteness:
    """Every ipcMain handler must be reachable, or it is not a feature.

    WHY: main.js implemented setAutoStartup()/getAutoStartupStatus() for
    win32/darwin/linux and exposed `autostart-set` / `autostart-get`, but
    preload.js never exposed a bridge to them. The "Start Angela at login"
    checkbox in settings.html therefore saved a value that nothing applied — a
    fully implemented feature with no usable path, which no asset or menu test
    could see.
    """

    PRELOAD = ROOT / "apps/desktop-app/electron_app/preload.js"
    MAIN = ROOT / "apps/desktop-app/electron_app/main.js"

    def _handlers(self) -> set:
        return set(
            re.findall(
                r"ipcMain\.(?:on|handle)\(\s*'([^']+)'", self.MAIN.read_text(encoding="utf-8")
            )
        )

    def _invoked(self) -> set:
        return set(
            re.findall(
                r"ipcRenderer\.(?:invoke|send)\(\s*'([^']+)'",
                self.PRELOAD.read_text(encoding="utf-8"),
            )
        )

    def test_no_renderer_invocation_lacks_a_main_handler(self):
        """Otherwise every such call rejects with 'No handler registered'."""
        orphans = self._invoked() - self._handlers()
        assert not orphans, f"preload invokes channels main.js never handles: {sorted(orphans)}"

    def test_autostart_handlers_have_a_bridge(self):
        preload = self.PRELOAD.read_text(encoding="utf-8")
        assert "autostart-set" in self._handlers() and "autostart-get" in self._handlers()
        assert "autostart: {" in preload, "preload exposes no autostart namespace"
        assert "ipcRenderer.invoke('autostart-get')" in preload
        assert "ipcRenderer.invoke('autostart-set'" in preload

    def test_settings_page_actually_applies_auto_start(self):
        source = (ROOT / "packages/shared-js/js/settings.js").read_text(encoding="utf-8")
        # The calls are prettier-wrapped across lines, so match with a regex.
        call = r"electronAPI\.autostart\s*\.\s*(get|set)\s*\("
        calls = re.findall(call, source)
        assert "get" in calls, (
            "the checkbox must reflect the real login-item state, not just the last saved value"
        )
        assert "set" in calls, (
            "auto-start is read and saved but never applied to the OS — the original defect"
        )


class TestRendererEventChannels:
    """electronAPI.on() silently drops any channel outside preload's allowlist.

    WHY: preload.js guards its generic `on(channel, cb)` with a validChannels
    list and simply returns when the channel is not in it — no error, no log.
    wallpaper-handler.js subscribed to 'hardware-update', which was neither
    allowlisted nor ever sent by the main process, so the handler could not run
    while appearing to be live hardware adaptation.
    """

    PRELOAD = ROOT / "apps/desktop-app/electron_app/preload.js"
    MAIN = ROOT / "apps/desktop-app/electron_app/main.js"

    def _allowlist(self) -> set:
        preload = self.PRELOAD.read_text(encoding="utf-8")
        block = re.search(r"const validChannels = \[(.*?)\]", preload, re.S)
        assert block, "preload.js no longer has a validChannels allowlist"
        return set(re.findall(r"'([^']+)'", block.group(1)))

    def _subscriptions(self) -> dict:
        found = {}
        for f in sorted((ROOT / "packages/shared-js/js").glob("*.js")):
            text = f.read_text(encoding="utf-8", errors="ignore")
            for channel in re.findall(r"electronAPI\??\.on\(\s*'([^']+)'", text):
                found.setdefault(channel, set()).add(f.name)
        return found

    def test_every_subscription_is_allowlisted(self):
        """A non-allowlisted subscription is a guaranteed no-op."""
        unlisted = {
            channel: sorted(files)
            for channel, files in self._subscriptions().items()
            if channel not in self._allowlist()
        }
        assert not unlisted, (
            "electronAPI.on() ignores these channels, so the listeners never run: "
            f"{unlisted}"
        )

    def _producers(self) -> set:
        """Every channel the main process actually pushes to a renderer.

        The first version of this audit only looked for `webContents.send(...)`
        and concluded that the main process sends a single event. That was wrong:
        main.js also pushes through sendToMainWindow()/sendToWindow() helpers, so
        the four websocket-* channels looked dead when they are the busiest
        events in the app. Any scan of this kind has to follow the indirection.
        """
        found = set()
        for f in sorted((ROOT / "apps/desktop-app/electron_app").rglob("*.js")):
            if "/libs/" in str(f):
                continue  # vendored shared-js copy
            text = f.read_text(encoding="utf-8", errors="ignore")
            for pattern in (
                r"webContents\.send\(\s*'([^']+)'",
                r"sendToMainWindow\(\s*'([^']+)'",
                r"sendToWindow\([^,]+,\s*'([^']+)'",
                r"\.send\(\s*'([\w-]+)'",
            ):
                found.update(re.findall(pattern, text))
        return found

    def test_every_subscription_has_a_producer(self):
        """A subscribed channel nobody sends is a listener that cannot run."""
        dead = {
            channel: sorted(files)
            for channel, files in self._subscriptions().items()
            if channel not in self._producers()
        }
        assert not dead, f"subscribed renderer events with no main-process sender: {dead}"

    def test_every_allowlisted_channel_is_either_sent_or_documented(self):
        """The allowlist may exceed reality, but not silently.

        `performance-auto-adjust` and `websocket-send-result` are allowlisted and
        have neither a sender nor a subscriber today. They are recorded here so
        the pair cannot grow unnoticed.
        """
        unused = sorted(self._allowlist() - self._producers())
        assert unused == ["performance-auto-adjust", "websocket-send-result"], (
            "allowlisted channels with no sender changed; update this record"
        )


class TestNewIpcSurfacesAreComplete:
    """The batch-C IPC additions must be wired end to end, not just declared.

    WHY: main.js gained window-set-opacity / window-get-opacity /
    system-audio-start / debug-set-log-level / debug-get-log-level, and preload
    gained the matching bridges. A bridge with no handler rejects with "No handler
    registered", and a handler with no bridge is exactly the dead-end that
    autostart was.
    """

    PRELOAD = ROOT / "apps/desktop-app/electron_app/preload.js"
    MAIN = ROOT / "apps/desktop-app/electron_app/main.js"
    SETTINGS = ROOT / "packages/shared-js/js/settings.js"

    NEW_CHANNELS = [
        "window-set-opacity",
        "window-get-opacity",
        "system-audio-start",
        "debug-set-log-level",
        "debug-get-log-level",
    ]

    def test_every_new_channel_is_handled_in_main(self):
        handled = set(
            re.findall(r"ipcMain\.(?:on|handle)\(\s*'([^']+)'", self.MAIN.read_text(encoding="utf-8"))
        )
        missing = [c for c in self.NEW_CHANNELS if c not in handled]
        assert not missing, f"declared in preload but never handled: {missing}"

    def test_every_new_channel_has_a_preload_bridge(self):
        preload = self.PRELOAD.read_text(encoding="utf-8")
        for channel in self.NEW_CHANNELS:
            assert channel in preload, f"{channel} has no preload bridge"

    def test_opacity_requires_a_transparent_window(self):
        """setOpacity() is a no-op on an opaque window — the reason it can work here."""
        main = self.MAIN.read_text(encoding="utf-8")
        assert "transparent: true" in main, (
            "window.setOpacity() silently does nothing unless the window is transparent"
        )

    def test_system_audio_reports_linux_instead_of_returning_silence(self):
        main = self.MAIN.read_text(encoding="utf-8")
        body = main.split("ipcMain.handle('system-audio-start'", 1)[1]
        assert "unsupported_platform" in body.split("})", 1)[0], (
            "Linux has no loopback audio; the handler must say so rather than "
            "handing the renderer a silent stream"
        )

    def test_log_level_is_validated(self):
        body = self.MAIN.read_text(encoding="utf-8")
        body = body.split("ipcMain.handle('debug-set-log-level'", 1)[1].split("})", 1)[0]
        assert "allowed" in body and "success: false" in body

    # The settings page calls the preload *bridge*, not the channel name — the
    # channel string only exists in preload.js and main.js.
    @pytest.mark.parametrize(
        "channel,bridge_call",
        [
            ("window-set-opacity", "window.setOpacity("),
            ("system-audio-start", "systemAudio.start("),
            ("debug-set-log-level", "debug.setLogLevel("),
        ],
    )
    def test_settings_page_calls_the_bridge(self, channel, bridge_call):
        preload = self.PRELOAD.read_text(encoding="utf-8")
        assert channel in preload, f"{channel} is not bridged in preload.js"
        # The renderer is prettier-formatted, so a call can be wrapped as
        # `window.electronAPI.systemAudio\n        .start()`; compare without
        # whitespace rather than against a literal that formatting can break.
        settings = re.sub(r"\s+", "", self.SETTINGS.read_text(encoding="utf-8"))
        assert re.sub(r"\s+", "", bridge_call) in settings, (
            f"the settings page never calls {bridge_call}"
        )
