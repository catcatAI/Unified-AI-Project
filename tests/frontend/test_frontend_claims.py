"""
ANGELA-MATRIX: [L4] [δ] [B] [L1]
The three front-end claims that were still "unverified" in
docs/VERIFICATION_REGISTER.json — because they needed a GUI.

They do not: the front end has no JS test runner, but the node harness in
``test_shared_js_behaviour.py`` can load the real sources and stub the
browser. These tests turn "unverified (no display)" into "verified
(behaviour)".
"""

import json
import re
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WEB_VIEWER = ROOT / "apps" / "web-live2d-viewer"
DESKTOP = ROOT / "apps" / "desktop-app" / "electron_app"

pytestmark = pytest.mark.skipif(
    not (ROOT / "packages" / "shared-js" / "js" / "app.js").exists(),
    reason="shared-js not vendored",
)


def _html_scripts(path: Path) -> list:
    text = path.read_text(encoding="utf-8")
    return re.findall(r'<script[^>]+src="([^"]+)"', text)


class TestAppJsIsLoaded:
    """frontend-angela-app-loads: both surfaces load app.js."""

    def test_the_web_viewer_loads_app_js(self):
        scripts = _html_scripts(WEB_VIEWER / "index.html")
        assert any("app.js" in s for s in scripts), scripts

    def test_the_desktop_app_loads_app_js(self):
        scripts = _html_scripts(DESKTOP / "index.html")
        assert any("app.js" in s for s in scripts), scripts

    def test_app_js_defines_the_angela_app_class(self):
        from tests.frontend.test_shared_js_behaviour import run_node

        result = run_node(
            textwrap.dedent("""
                const app = Object.create(cls.prototype)
                return {
                  isClass: typeof cls === 'function',
                  hasInitialize: typeof app.initialize === 'function',
                  hasHandleAction: typeof app._handleAngelaAction === 'function',
                }
                """),
            "app.js",
            "AngelaApp",
        )
        assert result["isClass"] is True
        assert result["hasInitialize"] is True
        assert result["hasHandleAction"] is True


class TestProactiveBubbles:
    """frontend-proactive-bubbles: a proactive action reaches the panel."""

    def test_a_proactive_action_is_rendered_into_the_dialogue_panel(self):
        from tests.frontend.test_shared_js_behaviour import run_node

        script = textwrap.dedent("""
            const rendered = []
            const app = Object.create(cls.prototype)
            app.addDialogueMessage = (sender, text) => { rendered.push({ sender, text }) }
            app._handleAngelaAction({ type: 'greet', message: '嗨，你回來了' })
            return { rendered }
            """)
        result = run_node(script, "app.js", "AngelaApp")
        assert result["rendered"], "the proactive action was not rendered"
        assert result["rendered"][0]["text"] == "嗨，你回來了"

    def test_an_unknown_action_still_shows_the_message_but_triggers_no_motion(self):
        """The message is the point; an unknown action must not fake a motion."""
        from tests.frontend.test_shared_js_behaviour import run_node

        script = textwrap.dedent("""
            const rendered = []
            const motions = []
            const app = Object.create(cls.prototype)
            app.addDialogueMessage = (sender, text) => { rendered.push({ sender, text }) }
            app.live2dManager = {
              setExpression: () => {},
              startMotion: (m) => { motions.push(m) },
            }
            app._handleAngelaAction({ action: 'not_a_real_action', message: 'x' })
            return { rendered, motions }
            """)
        result = run_node(script, "app.js", "AngelaApp")
        assert result["rendered"] == [{"sender": "angela", "text": "x"}]
        assert result["motions"] == []

    def test_a_greet_action_also_drives_the_live2d_motion(self):
        from tests.frontend.test_shared_js_behaviour import run_node

        script = textwrap.dedent("""
            const rendered = []
            const motions = []
            const app = Object.create(cls.prototype)
            app.addDialogueMessage = (sender, text) => { rendered.push({ sender, text }) }
            app.live2dManager = {
              setExpression: () => {},
              startMotion: (m) => { motions.push(m) },
            }
            app._handleAngelaAction({ action: 'greet', message: '嗨' })
            return { rendered, motions }
            """)
        result = run_node(script, "app.js", "AngelaApp")
        assert result["rendered"]
        assert result["motions"] == ["Wave"]


class TestHardwareEnhancementPatch:
    """webviewer-hardware-enhancement: the patch skips honestly."""

    def _run_patch(self, detector_source: str) -> dict:
        from tests.frontend.test_shared_js_behaviour import run_node

        script = textwrap.dedent(f"""
            const warnings = []
            const originalWarn = console.warn
            console.warn = (...args) => {{ warnings.push(args.join(' ')) }}
            const detector = {detector_source}
            const patched = window.HardwareEnhancementTools
              ? window.HardwareEnhancementTools.enhanceDetector(detector)
              : 'no-tools'
            console.warn = originalWarn
            const out = {{ patched, warnings }}
            console.log('__RESULT__' + JSON.stringify(out))
            """)
        # The patch is an IIFE: load it first, then exercise the exported tool.
        harness = textwrap.dedent("""
            const fs = require('fs')
            const path = process.argv[1]
            global.window = global.window || {}
            global.document = {
              readyState: 'complete',
              addEventListener() {},
              getElementById: () => null,
              querySelector: () => null,
              querySelectorAll: () => [],
              createElement: () => ({ style: {}, getContext: () => null, appendChild() {} }),
              documentElement: { style: { setProperty() {} } },
            }
            global.setInterval = () => 0
            global.clearInterval = () => {}
            const source = fs.readFileSync(path, 'utf8')
            new Function(source)()
            """)
        import subprocess

        result = subprocess.run(
            [
                "node",
                "-e",
                harness + "\n" + script,
                str(WEB_VIEWER / "js" / "hardware-enhancement-patch.js"),
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        assert "__RESULT__" in result.stdout, (
            f"node harness produced no result\nstdout: {result.stdout[-2000:]}\n"
            f"stderr: {result.stderr[-2000:]}"
        )
        # The patch itself logs to stdout; only the first line after the
        # marker is our payload.
        payload = result.stdout.split("__RESULT__", 1)[1].strip().splitlines()[0]
        return json.loads(payload)

    def test_a_detector_without_the_expected_api_is_skipped_with_a_warning(self):
        """The live detector (SystemProfileManager) has no detect() — the
        patch must say so instead of throwing."""
        result = self._run_patch("{ initialize() {}, _detectHardware() {} }")
        assert result["patched"] is False
        assert result["warnings"], "the skip was not reported"

    def test_a_null_detector_is_skipped(self):
        result = self._run_patch("null")
        assert result["patched"] is False

    def test_a_compatible_detector_is_patched(self):
        result = self._run_patch(
            "{ detect: async () => ({ ok: true }), _assessCapabilities: () => ({ caps: 1 }) }"
        )
        assert result["patched"] is True


class TestAutostartWiring:
    """settings-autostart: the preload → IPC → main.js chain is real.

    The *OS* login item still needs a desktop session to observe; the
    wiring itself is verifiable without a GUI.
    """

    def test_the_preload_exposes_the_autostart_bridge(self):
        text = (DESKTOP / "preload.js").read_text(encoding="utf-8")
        assert "ipcRenderer.invoke('autostart-set'" in text
        assert "ipcRenderer.invoke('autostart-get'" in text

    def test_main_process_handles_both_autostart_actions(self):
        text = (DESKTOP / "main.js").read_text(encoding="utf-8")
        assert "ipcMain.handle('autostart-set'" in text
        assert "ipcMain.handle('autostart-get'" in text
        # The handler must actually reach the implementation.
        assert "setAutoStartup(enable)" in text
        assert "getAutoStartupStatus()" in text

    def test_the_settings_page_uses_the_bridge(self):
        text = (ROOT / "packages" / "shared-js" / "js" / "settings.js").read_text(encoding="utf-8")
        assert "window.electronAPI.autostart" in text


class TestSettingsAreActuallyApplied:
    """settings-batch-a-b-c-d-wired: every listed setting reaches its target.

    The claim was "unverified" because the *visible* result needs Electron.
    The chain itself (settings page → the subsystem that owns the behaviour)
    is verifiable in node, and that is where a wiring bug would live.
    """

    def _applied(self) -> dict:
        """Drive the real settings page: fill the DOM, click Save."""
        import subprocess
        import tempfile

        harness = """
const fs = require('fs')
const path = process.argv[2]
let domReady = null
const listeners = {}
const values = {
  'window-opacity': '0.8', 'model-scale': '1.5', 'speech-rate': '1.2',
  'speech-pitch': '0.9', 'click-intensity': '0.7', 'touch-intensity': '0.4',
  'emotion-intensity': '0.6', 'model-select': 'default', 'render-mode': '2.5D',
  'wallpaper-mode': 'static', 'wallpaper-effect': 'blur', 'tts-engine': 'webspeech',
  'tts-voice': 'zh-TW', 'speech-language': 'zh-TW', 'sensitivity': '0.5',
  'backend-ip': '10.0.0.5', 'backend-port': '8000', 'frame-rate': '45',
  'render-quality': 'high',
}
const checked = {
  'always-on-top': true, 'auto-start': true, 'idle-mode': true,
  'auto-switch-fallback': false, 'continuous-recognition': false,
  'capture-system-audio': true, 'enable-haptics': true, 'show-click-regions': false,
  'debug-mode': true,
}
const elements = {}
const element = (id) => {
  if (!elements[id]) {
    elements[id] = {
      id,
      value: values[id] !== undefined ? values[id] : '',
      checked: checked[id] !== undefined ? checked[id] : false,
      dataset: {}, style: {}, textContent: '', innerHTML: '',
      classList: { add() {}, remove() {} },
      addEventListener: (evt, cb) => { listeners[id + ':' + evt] = cb },
      appendChild() {}, focus() {},
    }
  }
  return elements[id]
}
global.document = {
  readyState: 'complete',
  addEventListener: (evt, cb) => { if (evt === 'DOMContentLoaded') domReady = cb },
  querySelectorAll: () => [],
  querySelector: () => null,
  getElementById: (id) => element(id),
  createElement: (tag) => element('created-' + tag),
  documentElement: { style: { setProperty() {} } },
}
global.window = global.window || {}
global.confirm = () => true
// The page also reads the speech-synthesis voices and the model list.
global.window.speechSynthesis = { getVoices: () => [], onvoiceschanged: null }
global.electronAPI = global.electronAPI || {}
global.electronAPI.live2d = { getModels: () => Promise.resolve([]) }
global.electronAPI.settings = { get: () => Promise.resolve({}) }
global.electronAPI.autostart = { get: () => Promise.resolve({ enabled: false }) }
global.electronAPI.window = global.electronAPI.window || {}
global.electronAPI.window.getOpacity = () => Promise.resolve(1)
global.electronAPI.window.getBounds = () => Promise.resolve({})
// The manager holds the current settings; the page mirrors them into the
// form, exactly as it does in the real app.
global.settingsManager = {
  settings: {
    alwaysOnTop: true, autoStart: true, windowOpacity: 0.8, idleMode: true,
    sensitivity: '0.5', model: 'default', modelScale: 1.5, renderMode: '2.5D',
    autoSwitchFallback: false, wallpaperMode: 'static', wallpaperEffect: 'blur',
    ttsEngine: 'webspeech', ttsVoice: 'zh-TW', speechRate: 1.2, speechPitch: 0.9,
    speechLanguage: 'zh-TW', continuousRecognition: false, captureSystemAudio: true,
    enableHaptics: true, clickIntensity: 0.7, touchIntensity: 0.4,
    emotionIntensity: 0.6, backendIp: '10.0.0.5', backendPort: '8000',
    frameRate: '45', renderQuality: 'high', debugMode: true, showClickRegions: false,
  },
  initialize: () => Promise.resolve(),
  getAll: () => Promise.resolve({}),
  set: () => Promise.resolve(),
  setAll: () => Promise.resolve(),
}
new Function(fs.readFileSync(path, 'utf8'))()

const applied = {}
const electronCalls = {}
const app = {
  hapticHandler: {
    setEnabled: (v) => { applied.haptics = v },
    setIntensityScale: (v) => { applied.hapticScale = v },
  },
  udm: { setUserScale: (v) => { applied.modelScale = v } },
  performanceManager: {
    setPerformanceTargets: (t) => { applied.performance = t },
    setAutoAdjust: (v) => { applied.autoSwitch = v },
  },
  wallpaperHandler: {
    setRenderingMode: (v) => { applied.wallpaperMode = v },
    setEffect: (v) => { applied.wallpaperEffect = v },
  },
  audioHandler: {
    setSpeechDefaults: (d) => { applied.speech = d },
    setSpeechLanguage: (v) => { applied.speechLanguage = v },
  },
  backendWebSocket: { connect: (u) => { applied.backendUrl = u } },
  setIdleDetectionEnabled: (v) => { applied.idleMode = v },
}
window.angelaApp = app
window.electronAPI = {
  window: {
    setAlwaysOnTop: (v) => { electronCalls.alwaysOnTop = v },
    setIgnoreMouseEvents: (v) => { electronCalls.ignoreMouse = v },
    setOpacity: (v) => { electronCalls.opacity = v; return Promise.resolve({ success: true }) },
  },
  wallpaper: { setMode: (v) => { electronCalls.wallpaperMode = v; return Promise.resolve({}) } },
  systemAudio: { start: () => Promise.resolve({ success: true }) },
  debug: { setLogLevel: (v) => { electronCalls.logLevel = v; return Promise.resolve({ success: true }) } },
  backend: { setIP: (v) => { electronCalls.backendIp = v; return Promise.resolve({}) } },
  autostart: {
    get: () => Promise.resolve({ enabled: false }),
    set: (v) => { electronCalls.autostart = v; return Promise.resolve({}) },
  },
}

;(async () => {
  domReady()
  await new Promise((resolve) => setTimeout(resolve, 0))
  await listeners['save:click']()
  await new Promise((resolve) => setTimeout(resolve, 0))
  console.log('__RESULT__' + JSON.stringify({ applied, electronCalls }))
})()
"""
        with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False) as fh:
            fh.write(harness)
            script_path = fh.name
        try:
            result = subprocess.run(
                [
                    "node",
                    script_path,
                    str(ROOT / "packages" / "shared-js" / "js" / "settings.js"),
                ],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
        finally:
            Path(script_path).unlink(missing_ok=True)
        assert "__RESULT__" in result.stdout, (
            f"node harness produced no result\nstdout: {result.stdout[-2000:]}\n"
            f"stderr: {result.stderr[-2000:]}"
        )
        payload = result.stdout.split("__RESULT__", 1)[1].strip().splitlines()[0]
        return json.loads(payload)

    def test_the_subsystem_settings_reach_their_owners(self):
        out = self._applied()
        applied = out["applied"]
        assert applied.get("haptics") is True
        assert applied.get("modelScale") == 1.5
        assert applied.get("performance") == {"fps": 45, "quality": "high"}
        assert applied.get("wallpaperMode") == "static"
        assert applied.get("autoSwitch") is False
        assert applied.get("idleMode") is True
        assert applied.get("speech", {}).get("rate") == 1.2
        assert applied.get("speech", {}).get("pitch") == 0.9
        assert applied.get("speech", {}).get("voice") == "zh-TW"
        assert applied.get("speechLanguage") == "zh-TW"
        assert applied.get("hapticScale") == 0.7  # the click slider wins
        assert applied.get("wallpaperEffect") == "blur"
        assert applied.get("backendUrl") == "ws://10.0.0.5:8000/ws"

    def test_the_electron_settings_reach_the_main_process(self):
        out = self._applied()
        calls = out["electronCalls"]
        assert calls.get("alwaysOnTop") is True
        assert calls.get("ignoreMouse") is True  # showClickRegions=false → ignore clicks
        assert calls.get("opacity") == 0.8
        assert calls.get("wallpaperMode") == "static"
        assert calls.get("logLevel") == "debug"
        assert calls.get("backendIp") == "10.0.0.5"
        assert calls.get("autostart") is True
