"""
Behavioural tests for shared-js code, executed in node from pytest.

WHY: the front-end has no JS test runner (`pnpm test` is pytest), so every
settings/menu fix in this project has been guarded by static regex assertions.
That cannot tell a working call from a plausible-looking one — the F-series
defects were all "the code looks right and never runs".

These tests load the real source file in node, stub only the browser/Electron
globals the code touches, and assert observable behaviour. They cover the pure
logic that has no GUI dependency; anything that genuinely needs a window is
tracked in docs/VERIFICATION_REGISTER.json instead.

ANGELA-MATRIX: [L4] [δ] [B] [L1]
"""

import json
import re
import shutil
import subprocess
import textwrap

import pytest

ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]
SHARED_JS = ROOT / "packages/shared-js/js"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not available")


def run_node(script: str, source_file: str, cls_name: str) -> dict:
    """Load `source_file` in node and run `script` with `cls_name` bound to it.

    The shared modules are plain browser scripts with no export statement, so the
    class is recovered by appending a return of its own name.
    """
    source = (SHARED_JS / source_file).read_text(encoding="utf-8")
    harness = f"""
const fs = require('fs')
const path = process.argv[1]
// Minimal browser surface: these classes touch document/window/canvas only
// inside methods this harness does not call.
global.window = global.window || {{}}
global.document = {{
  getElementById: () => null,
  querySelector: () => null,
  querySelectorAll: () => [],
  createElement: () => ({{ style: {{}}, getContext: () => null, appendChild() {{}} }}),
  addEventListener() {{}},
  documentElement: {{ style: {{ setProperty() {{}} }} }},
}}
global.performance = global.performance || {{ now: () => 0 }}
const source = fs.readFileSync(path, 'utf8')
// String.fromCharCode(10) instead of an escaped newline: keeps this harness free
// of backslash escaping, which is easy to get wrong through nested quoting.
const factory = new Function(
  source + String.fromCharCode(10) + "; return typeof {cls_name} !== 'undefined' ? {cls_name} : null;"
)
const cls = factory()
if (!cls) {{ console.error('CLASS_NOT_FOUND'); process.exit(3) }}
const out = (function (cls) {{
{script}
}})(cls)
console.log('__RESULT__' + JSON.stringify(out === undefined ? null : out))
"""
    result = subprocess.run(
        ["node", "-e", harness, str(SHARED_JS / source_file)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if "__RESULT__" not in result.stdout:
        raise AssertionError(
            f"node harness produced no result\nstdout: {result.stdout[-2000:]}\n"
            f"stderr: {result.stderr[-2000:]}"
        )
    return json.loads(result.stdout.split("__RESULT__", 1)[1].strip())


# --------------------------------------------------------------------------- #
# PerformanceManager.setPerformanceTargets
# --------------------------------------------------------------------------- #
def _pm_call(expr: str) -> dict:
    script = textwrap.dedent(
        f"""
        const pm = Object.create(cls.prototype)
        pm.targetFPS = 45
        pm.effectsLevel = 2
        pm.resolutionScale = 0.75
        pm.autoAdjustEnabled = false
        pm.appliedCount = 0
        pm.applyPerformanceSettings = function () {{ this.appliedCount++ }}
        return {{ applied: {expr}, state: {{ targetFPS: pm.targetFPS,
          effectsLevel: pm.effectsLevel, resolutionScale: pm.resolutionScale }},
          appliedCount: pm.appliedCount }}
        """
    )
    return run_node(script, "performance-manager.js", "PerformanceManager")


def test_set_performance_targets_applies_both_axes():
    out = _pm_call("pm.setPerformanceTargets({ fps: 120, quality: 'high' })")
    assert out["applied"] == {
        "fps": 120,
        "quality": "high",
        "effects": 3,
        "resolution": 1.0,
    }
    assert out["state"]["targetFPS"] == 120
    assert out["appliedCount"] == 1


def test_set_performance_targets_keeps_the_two_choices_independent():
    """120 FPS at medium quality is a valid combination the fixed profiles cannot express."""
    out = _pm_call("pm.setPerformanceTargets({ fps: 120, quality: 'medium' })")
    assert out["state"]["targetFPS"] == 120
    assert out["state"]["effectsLevel"] == 2


def test_set_performance_targets_accepts_a_partial_request():
    out = _pm_call("pm.setPerformanceTargets({ fps: 30 })")
    assert out["applied"] == {"fps": 30}
    assert out["state"]["effectsLevel"] == 2, "an unset axis must keep its value"
    assert out["appliedCount"] == 1


def test_set_performance_targets_rejects_junk_without_pretending():
    out = _pm_call("pm.setPerformanceTargets({ fps: 'x', quality: 'ultra' })")
    assert out["applied"] is None
    assert out["appliedCount"] == 0, "nothing usable must not be applied"


def test_set_performance_targets_reads_numeric_strings():
    """The settings page hands over DOM values, which are strings."""
    out = _pm_call("pm.setPerformanceTargets({ fps: '60', quality: 'LOW' })")
    assert out["applied"]["fps"] == 60
    assert out["applied"]["quality"] == "low"


# --------------------------------------------------------------------------- #
# The settings page must call what these components actually expose
# --------------------------------------------------------------------------- #
SETTINGS_JS = (SHARED_JS / "settings.js").read_text(encoding="utf-8")

# setting id -> the call that must appear in applySettingsToApplication.
# These are CALLS (trailing parenthesis), not mentions: a `typeof
# app.hapticHandler.setEnabled === 'function'` probe satisfies a bare-name check
# while the real call is gone, which is how a mutation slipped past the first
# version of this guard.
REQUIRED_CALLS = {
    "enableHaptics": "hapticHandler.setEnabled(",
    "modelScale": "udm.setUserScale(",
    "frameRate": "setPerformanceTargets",
    "renderQuality": "setPerformanceTargets",
    "wallpaperMode": "wallpaper.setMode",
    "backendIp": "backend.setIP",
    "backendPort": "ws://",
    # batch B
    "ttsVoice": "setSpeechDefaults(",
    "speechRate": "setSpeechDefaults(",
    "speechPitch": "setSpeechDefaults(",
    "speechLanguage": "setSpeechLanguage(",
    "clickIntensity": "setIntensityScale(",
    "touchIntensity": "setIntensityScale(",
    "wallpaperEffect": "wallpaperHandler.setEffect(",
    "emotionIntensity": "app.emotionIntensity",
}


def _apply_body() -> str:
    """Only the body of applySettingsToApplication.

    Splitting on the name alone returns the whole remainder of the file, so a
    call made by some *other* function would satisfy the guard. The first attempt
    at bounding it looked for two-space-indented siblings, but this file's
    functions are nested inside the DOMContentLoaded IIFE, so the marker never
    matched and the "bounded" body was still the whole file — which is how
    deleting an entire apply block passed. The bound is asserted, not assumed.
    """
    tail = SETTINGS_JS.split("function applySettingsToApplication", 1)[1]
    match = re.search(r"\n\s+(?:async )?function ", tail)
    assert match, "could not bound applySettingsToApplication — is the layout different?"
    body = tail[: match.start()]
    assert "function resetSettings" not in body, "body extraction ran past the function"
    return body


# setting id -> the call that must appear in applySettingsToApplication.
# These are CALLS (trailing parenthesis), not mentions: a `typeof
# app.hapticHandler.setEnabled === 'function'` probe satisfies a bare-name check
# while the real call is gone, which is how a mutation slipped past the first
# version of this guard.


def _apply_body() -> str:
    """Only the body of applySettingsToApplication.

    Splitting on the name alone returns the whole remainder of the file, so a
    call made by some *other* function would satisfy the guard — which is exactly
    the bug: `hapticHandler.setEnabled` appears in app.js's toggle path, and a
    mutation that removed the settings-page call still passed.
    """
    tail = SETTINGS_JS.split("function applySettingsToApplication", 1)[1]
    for sibling in ("\n  function ", "\n  async function "):
        idx = tail.find(sibling)
        if idx != -1:
            tail = tail[:idx]
    return tail


@pytest.mark.parametrize("setting,call", sorted(REQUIRED_CALLS.items()))
def test_setting_is_actually_applied(setting, call):
    """A collected-but-unapplied setting is the defect class this file exists for."""
    assert f"s.{setting}" in SETTINGS_JS, f"{setting} is no longer collected"
    assert call in _apply_body(), f"{setting} is saved but {call} is never called"
    # Also reference the value inside the apply body: several settings share one
    # call, so deleting just this setting's argument left both checks above green
    # while the slider stopped doing anything.
    assert f"settings.{setting}" in _apply_body(), (
        f"{setting} is collected but never read while applying settings"
    )


# --------------------------------------------------------------------------- #
# AudioHandler speech defaults
# --------------------------------------------------------------------------- #
def _audio_call(script_body: str) -> dict:
    script = textwrap.dedent(
        f"""
        global.navigator = {{}}
        global.window = global.window || {{}}
        const h = Object.create(cls.prototype)
        h.speechDefaults = {{ rate: 1, pitch: 1, voice: null, lang: null }}
        // speak() guards on this before building an utterance.
        h.synthesis = {{ speak() {{}} }}
        h.availableVoices = [{{ name: 'Tingting' }}, {{ name: 'Google US English' }}]
        h.spoken = []
        h.stopSpeaking = function () {{}}
        global.SpeechSynthesisUtterance = function (text) {{
          this.text = text
          h.lastUtterance = this
        }}
        {script_body}
        """
    )
    return run_node(script, "audio-handler.js", "AudioHandler")


def test_speech_defaults_are_persisted_and_clamped():
    out = _audio_call(
        "const got = h.setSpeechDefaults({ rate: '1.5', pitch: '9' })\n"
        "return { got, stored: h.getSpeechDefaults() }"
    )
    assert out["got"]["rate"] == 1.5
    assert out["got"]["pitch"] == 2.0, "pitch must be clamped to the 0.5-2 range"
    assert out["stored"]["rate"] == 1.5


def test_speak_uses_the_persisted_defaults():
    """The whole point: a saved slider must reach the next utterance."""
    out = _audio_call(
        "h.setSpeechDefaults({ rate: 1.4, pitch: 0.8, voice: 'Tingting', lang: 'zh-TW' })\n"
        "h.speak('你好')\n"
        "const u = h.lastUtterance\n"
        "return { rate: u.rate, pitch: u.pitch, lang: u.lang }"
    )
    assert out == {"rate": 1.4, "pitch": 0.8, "lang": "zh-TW"}


def test_per_call_options_still_win_over_defaults():
    out = _audio_call(
        "h.setSpeechDefaults({ rate: 1.4 })\n"
        "h.speak('hi', { rate: 0.9 })\n"
        "return { rate: h.lastUtterance.rate }"
    )
    assert out["rate"] == 0.9


def test_speech_defaults_reject_junk_without_corrupting_state():
    out = _audio_call(
        "const before = h.getSpeechDefaults()\n"
        "const got = h.setSpeechDefaults({ rate: 'fast' })\n"
        "return { before, after: got }"
    )
    assert out["before"] == out["after"], "an unusable value must not overwrite state"


# --------------------------------------------------------------------------- #
# HapticHandler intensity scale
# --------------------------------------------------------------------------- #
def _haptic_call(script_body: str) -> dict:
    script = textwrap.dedent(
        f"""
        global.navigator = {{ vibrate: () => {{}} }}
        global.window = global.window || {{}}
        const h = Object.create(cls.prototype)
        h.intensityScale = 1.0
        h.udm = null
        h.vibrationSupported = true
        h.vibrated = []
        h.vibrate = function (d, i) {{ h.vibrated.push([d, i]) }}
        h._getPattern = function (part, intensity) {{
          return {{ duration: 30, intensity: intensity }}
        }}
        {script_body}
        """
    )
    return run_node(script, "haptic-handler.js", "HapticHandler")


def test_haptic_intensity_scale_multiplies_the_final_intensity():
    """Assert what the *device* was told, not only what the call returned.

    A mutation that scaled the returned record but passed the raw pattern
    intensity to vibrate() satisfied a return-value-only assertion while the
    user's preference had no effect on the hardware.
    """
    out = _haptic_call(
        "const before = h.trigger('face', 0.8)\n"
        "h.setIntensityScale(0.25)\n"
        "const after = h.trigger('face', 0.8)\n"
        "return { before: before.intensity, after: after.intensity,"
        " scale: h.getIntensityScale(), device: h.vibrated }"
    )
    assert out["before"] == 0.8
    assert out["after"] == 0.2
    assert out["scale"] == 0.25
    # duration, intensity as actually sent to the device
    assert out["device"][0][1] == 0.8
    assert out["device"][1][1] == 0.2


def test_haptic_intensity_scale_rejects_out_of_range_values():
    out = _haptic_call(
        "h.setIntensityScale(0.5)\n"
        "const kept = h.setIntensityScale(5)\n"
        "return { kept, scale: h.getIntensityScale() }"
    )
    assert out["scale"] == 0.5, "an out-of-range scale must not be applied"


# --------------------------------------------------------------------------- #
# WallpaperHandler effect
# --------------------------------------------------------------------------- #
def _wallpaper_call(script_body: str) -> dict:
    script = textwrap.dedent(
        f"""
        global.window = global.window || {{}}
        const w = Object.create(cls.prototype)
        w.effect = 'none'
        w.compositionCanvas = {{ style: {{}} }}
        {script_body}
        """
    )
    return run_node(script, "wallpaper-handler.js", "WallpaperHandler")


@pytest.mark.parametrize(
    "effect,expected_filter",
    [("blur", "blur(8px)"), ("darken", "brightness(0.55)"), ("grayscale", "grayscale(1)")],
)
def test_wallpaper_effects_apply_a_real_filter(effect, expected_filter):
    out = _wallpaper_call(
        f"const applied = w.setEffect('{effect}')\n"
        "return { applied, filter: w.compositionCanvas.style.filter }"
    )
    assert out["applied"] == effect
    assert out["filter"] == expected_filter


def test_switching_back_to_none_clears_the_filter():
    out = _wallpaper_call(
        "w.setEffect('blur')\n"
        "w.setEffect('none')\n"
        "return { effect: w.getEffect(), filter: w.compositionCanvas.style.filter }"
    )
    assert out["effect"] == "none"
    assert out["filter"] == "", "the previous effect must actually be cleared"


def test_unknown_effect_falls_back_to_none_and_says_so():
    out = _wallpaper_call(
        "const applied = w.setEffect('sparkles')\n"
        "return { applied, filter: w.compositionCanvas.style.filter }"
    )
    assert out["applied"] == "none"
    assert out["filter"] == ""


def test_wallpaper_effect_is_reapplied_on_render():
    """initialize() can create the canvas after the user picked an effect."""
    out = _wallpaper_call(
        "w.setEffect('blur')\n"
        "w.compositionCanvas = { style: {} }\n"
        "w.compositionContext = { clearRect() {}, drawImage() {} }\n"
        "w.compositionCanvas.width = 100\n"
        "w.compositionCanvas.height = 100\n"
        "w._getActiveWallpaper = function () { return null }\n"
        "w.modeledObjects = []\n"
        "w.renderComposition()\n"
        "return { filter: w.compositionCanvas.style.filter }"
    )
    assert out["filter"] == "blur(8px)"


# --------------------------------------------------------------------------- #
# Settings wiring for batch B
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# AngelaApp._handleEmotionChanged — the emotionIntensity preference
# --------------------------------------------------------------------------- #
def _app_emotion_call(preference, data_intensity=0.8) -> dict:
    script = textwrap.dedent(
        f"""
        const app = Object.create(cls.prototype)
        app.emotionIntensity = {preference}
        const applied = {{}}
        app.live2dManager = {{
          setExpression: (e) => {{ applied.expression = e }},
          setParameter: (k, v) => {{ applied[k] = v }},
        }}
        app._handleEmotionChanged({{ new_emotion: 'happy', intensity: {data_intensity} }})
        return applied
        """
    )
    return run_node(script, "app.js", "AngelaApp")


def test_emotion_intensity_preference_scales_the_live2d_parameter():
    """The settings slider must actually reach ParamEmotionIntensity."""
    assert _app_emotion_call(1.0)["ParamEmotionIntensity"] == 0.8
    assert _app_emotion_call(0.5)["ParamEmotionIntensity"] == 0.4


def test_emotion_intensity_preference_cannot_invert_the_state():
    """Out-of-range preferences are clamped, not trusted."""
    assert _app_emotion_call(5)["ParamEmotionIntensity"] == 0.8
    assert _app_emotion_call(-2)["ParamEmotionIntensity"] == 0.0


def test_emotion_expression_still_maps_normally():
    out = _app_emotion_call(0.5)
    assert out["expression"] == "happy"


def test_emotion_change_without_an_intensity_falls_back_instead_of_zeroing():
    script = textwrap.dedent(
        """
        const app = Object.create(cls.prototype)
        app.emotionIntensity = 1.0
        const applied = {}
        app.live2dManager = {
          setExpression: (e) => { applied.expression = e },
          setParameter: (k, v) => { applied[k] = v },
        }
        app._handleEmotionChanged({ new_emotion: 'calm' })
        return applied
        """
    )
    out = run_node(script, "app.js", "AngelaApp")
    assert out["ParamEmotionIntensity"] == 0.5, "missing intensity must not read as 0"
