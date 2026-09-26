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
}


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
