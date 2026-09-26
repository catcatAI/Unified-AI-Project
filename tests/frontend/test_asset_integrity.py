"""
Front-end asset integrity: every <script src> must resolve, and the vendored
shared modules must match their source.

WHY: the packaged desktop app shipped an ``index.html`` whose 32 shared modules
pointed at ``../../../packages/shared-js/js/…``. That path exists in the source
tree but not inside electron-builder's output (its ``files`` globs cannot reach
outside the app directory), so every one of them 404'd in the AppImage:
``new AngelaApp()`` threw a ReferenceError and the window never left the
"Loading Angela AI…" overlay. Development looked fine, which is why this survived
so long.

This test vendors the modules (as the start/build hooks do) and then asserts:
  1. no <script src> in any front-end entry point escapes its own directory,
  2. every non-CDN <script src> resolves on disk,
  3. each vendored copy is byte-identical to packages/shared-js/js/<file>,
  4. the launch hooks exist so the copies cannot go stale unnoticed.
"""

import filecmp
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYNC_SCRIPT = ROOT / "scripts" / "sync_shared_js.py"
SOURCE_DIR = ROOT / "packages" / "shared-js" / "js"
_SCRIPT_SRC = re.compile(r'<script[^>]+src="([^"]+)"', re.IGNORECASE)

# Surfaces whose assets are vendored by scripts/sync_shared_js.py.
WIRED_SURFACES = ("desktop", "web")

SURFACES = {
    "desktop": (
        ROOT / "apps/desktop-app/electron_app",
        ("index.html", "settings.html", "multimodal-panel.html"),
    ),
    "web": (ROOT / "apps/web-live2d-viewer", ("index.html",)),
}

# The Cubism Framework bundle is built from TypeScript by webpack and is not
# produced by any pnpm script; Live2DManager has its own WebGL path, so its
# absence is a warning, not a boot failure.
OPTIONAL = ("live2dcubismframework.bundle.js",)


@pytest.fixture(scope="module", autouse=True)
def vendored_modules():
    """Run the same vendoring step the start/build hooks run."""
    result = subprocess.run(
        [
            sys.executable,
            str(SYNC_SCRIPT),
            *[arg for name in WIRED_SURFACES for arg in ("--surface", name)],
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, f"sync_shared_js.py failed:\n{result.stdout}\n{result.stderr}"
    return result.stdout


def _script_sources(surface_dir: Path, entries):
    for entry in entries:
        path = surface_dir / entry
        if not path.is_file():
            continue
        for raw_src in _SCRIPT_SRC.findall(path.read_text(encoding="utf-8")):
            yield entry, raw_src.split("?")[0]


class TestFrontendAssetIntegrity:
    def test_no_script_escapes_its_own_directory(self):
        """Relative script paths must not climb out of the surface directory.

        `../../../packages/...` works in the source tree and breaks in every
        packaged/served artifact — the exact bug this file guards.
        """
        offenders = []
        for name in WIRED_SURFACES:
            surface_dir, entries = SURFACES[name]
            for entry, src in _script_sources(surface_dir, entries):
                if src.startswith(("http://", "https://", "//", "data:")):
                    continue
                if src.startswith("../"):
                    offenders.append(f"{name}/{entry}: {src}")
        assert not offenders, "script sources escaping the surface directory:\n" + "\n".join(
            offenders
        )

    def test_every_local_script_resolves(self):
        missing = []
        for name in WIRED_SURFACES:
            surface_dir, entries = SURFACES[name]
            for entry, src in _script_sources(surface_dir, entries):
                if src.startswith(("http://", "https://", "//", "data:")):
                    continue
                target = (surface_dir / src).resolve()
                if target.is_file():
                    continue
                if any(os.path.basename(src).endswith(opt) for opt in OPTIONAL):
                    continue
                missing.append(f"{name}/{entry}: {src}")
        assert not missing, "unresolvable <script src> (window will hang):\n" + "\n".join(
            missing
        )

    def test_vendored_copies_match_their_source(self):
        drifted = []
        for name in WIRED_SURFACES:
            surface_dir, _entries = SURFACES[name]
            vendored = surface_dir / ("libs/shared-js" if name == "desktop" else "js/shared-js")
            if not vendored.is_dir():
                drifted.append(f"{name}: vendored directory missing ({vendored})")
                continue
            for src_file in sorted(SOURCE_DIR.glob("*.js")):
                dst = vendored / src_file.name
                if not dst.is_file():
                    drifted.append(f"{name}: {src_file.name} not vendored")
                elif not filecmp.cmp(str(src_file), str(dst), shallow=False):
                    drifted.append(f"{name}: {src_file.name} differs from source")
        assert not drifted, "stale vendored shared modules:\n" + "\n".join(drifted)

    def test_vendored_copies_are_git_ignored(self):
        """Generated copies must stay out of git so drift is impossible."""
        entries = (ROOT / ".gitignore").read_text(encoding="utf-8")
        assert "apps/desktop-app/electron_app/libs/shared-js/" in entries
        assert "apps/web-live2d-viewer/js/shared-js/" in entries

    @pytest.mark.parametrize(
        "package_json",
        [
            "apps/desktop-app/package.json",
            "apps/desktop-app/electron_app/package.json",
        ],
    )
    def test_launch_and_build_run_the_sync(self, package_json):
        """Without the hook the vendored copies silently go stale."""
        data = json.loads((ROOT / package_json).read_text(encoding="utf-8"))
        scripts = data.get("scripts", {})
        for hook in ("prestart", "prebuild"):
            assert hook in scripts, f"{package_json} has no {hook} hook"
            assert "sync_shared_js.py" in scripts[hook]

    def test_check_mode_is_side_effect_free(self):
        """--check must verify without writing, so CI can use it."""
        result = subprocess.run(
            [sys.executable, str(SYNC_SCRIPT), "--check"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=300,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "all surfaces verified" in result.stdout


def _simulate_packaged(files_globs, root: Path) -> set:
    """Resolve electron-builder's ``files`` globs against a copied tree.

    Negations are evaluated first (that is electron-builder's semantics), then
    inclusions. Returns the set of relative paths that would be shipped.
    """
    import fnmatch

    candidates = set()
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            candidates.add(os.path.relpath(os.path.join(dirpath, name), root))

    def matches(rel: str, glob: str) -> bool:
        return fnmatch.fnmatch(rel, glob) or (
            glob.endswith("/**/*") and rel.startswith(glob[:-5])
        )

    shipped = set()
    for rel in candidates:
        if any(matches(rel, g[1:]) for g in files_globs if g.startswith("!")):
            continue
        if any(matches(rel, g) for g in files_globs if not g.startswith("!")):
            shipped.add(rel)
    return shipped


class TestPackagedAppCanBoot:
    """The real regression: the artifact is not the source tree.

    ``files: ["electron_app/**/*"]`` cannot reach ``packages/shared-js``, so a
    path that works in development 404s in the AppImage. This test copies the
    packaged subset into a temp dir and resolves every <script src> *inside it* —
    the same thing Electron does at runtime.
    """

    def test_packaged_tree_has_no_escaping_or_broken_scripts(self, tmp_path):
        import shutil

        app_root = ROOT / "apps/desktop-app"
        package = json.loads((app_root / "package.json").read_text(encoding="utf-8"))
        globs = package["build"]["files"]

        staging = tmp_path / "pkg"
        staging.mkdir()
        shutil.copytree(
            app_root / "electron_app", staging / "electron_app", symlinks=False
        )
        (staging / "package.json").write_text(
            (app_root / "package.json").read_text(encoding="utf-8"), encoding="utf-8"
        )

        shipped = _simulate_packaged(globs, staging)
        assert shipped, "packaging simulation produced an empty artifact"

        escaped, missing, checked = [], [], 0
        for rel in sorted(shipped):
            if not rel.endswith(".html"):
                continue
            page = staging / rel
            for raw_src in _SCRIPT_SRC.findall(page.read_text(encoding="utf-8")):
                src = raw_src.split("?")[0]
                if src.startswith(("http://", "https://", "//", "data:")):
                    continue
                checked += 1
                if src.startswith("../"):
                    escaped.append(f"{rel}: {src}")
                    continue
                if (page.parent / src).is_file():
                    continue
                if os.path.basename(src).endswith(OPTIONAL[0]):
                    continue
                missing.append(f"{rel}: {src}")
        assert checked > 20, f"simulation only saw {checked} script refs"
        assert not escaped, "packaged pages reference files outside the package:\n" + "\n".join(
            escaped
        )
        assert not missing, "packaged pages reference missing files:\n" + "\n".join(missing)

    def test_unreferenced_diagnostic_pages_are_not_shipped(self):
        """Those pages are unreachable and load modules from outside the app."""
        app_root = ROOT / "apps/desktop-app"
        globs = json.loads(
            (app_root / "package.json").read_text(encoding="utf-8")
        )["build"]["files"]
        negations = [g[1:] for g in globs if g.startswith("!")]
        for page in ("diagnose-coordinates.html", "test-detection.html", "test-character-touch.html"):
            assert any(page in g for g in negations), f"{page} would be shipped"

    def test_shared_modules_are_inside_the_packaged_subtree(self):
        """The vendored copy must live under electron_app/ to be packaged."""
        package = json.loads(
            (ROOT / "apps/desktop-app/package.json").read_text(encoding="utf-8")
        )
        assert any("electron_app/**/*" in g for g in package["build"]["files"])
        assert (ROOT / "apps/desktop-app/electron_app/libs/shared-js").is_dir()


class TestSharedGlobalsAreExported:
    """A classic <script> has no `module`, so `module.exports` never runs.

    Seven shared modules were read as `window.<symbol>` by the surfaces while
    only assigning `module.exports`. In a renderer that left every one of them
    undefined — the web viewer's chat panel and the whole multimodal panel were
    dead because `unified-shell.js` bails on `if (window.AngelaAPIClient)`.
    """

    def _shared_modules(self):
        return sorted(SOURCE_DIR.glob("*.js"))

    def _window_symbols_read_by_surfaces(self):
        import re as _re

        readers = {}
        for base in (ROOT / "apps/web-live2d-viewer", ROOT / "apps/desktop-app/electron_app"):
            for path in list(base.rglob("*.js")) + list(base.rglob("*.html")):
                text = path.read_text(encoding="utf-8", errors="ignore")
                for match in _re.finditer(r"window\.([A-Za-z_$][\w$]*)", text):
                    readers.setdefault(match.group(1), set()).add(str(path))
        return readers

    def test_every_window_symbol_read_from_a_shared_module_is_assigned(self):
        import re as _re

        readers = self._window_symbols_read_by_surfaces()
        missing = []
        for module in self._shared_modules():
            text = module.read_text(encoding="utf-8", errors="ignore")
            declared = set(
                _re.findall(r"^(?:class|function|const|let|var)\s+([A-Za-z_$][\w$]*)", text, _re.M)
            )
            for symbol in sorted(declared & readers.keys()):
                if not _re.search(rf"window\.{_re.escape(symbol)}\s*=", text):
                    missing.append(f"{module.name}: {symbol} (read as window.{symbol})")
        assert not missing, "shared modules never assigned to window:\n" + "\n".join(missing)

    def test_viewer_launcher_verifies_assets_before_serving(self):
        """scripts/start.py serves this directory; a broken page must not boot."""
        source = (ROOT / "scripts" / "start.py").read_text(encoding="utf-8")
        viewer_fn = source[source.index("def start_web_viewer"):]
        viewer_fn = viewer_fn[: viewer_fn.index("def main")]
        assert "sync_shared_js.py" in viewer_fn
        assert "--surface" in viewer_fn and "web" in viewer_fn
        assert "return None" in viewer_fn, "must refuse to serve a broken page"


class TestBootstrappablePages:
    """A page that constructs a class must load the file that defines it.

    WHY: both front-ends ended their script list and then ran
    ``new AngelaApp()`` — but *no* <script> tag referenced any file defining
    ``AngelaApp`` (``index.js`` is only a platform helper). Every module-level
    script 404-check passed, because nothing referenced a missing file; the
    breakage was a *missing* reference, which no asset test could see. The app
    could not start in development or in a packaged build.
    """

    # Globals each entry point instantiates in its inline bootstrap.
    REQUIRED_GLOBALS = {"AngelaApp"}

    DEFINERS = {
        "AngelaApp": ROOT / "packages/shared-js/js/app.js",
    }

    @pytest.mark.parametrize(
        "page",
        [
            ROOT / "apps/desktop-app/electron_app/index.html",
            ROOT / "apps/web-live2d-viewer/index.html",
        ],
        ids=["desktop", "web"],
    )
    def test_every_constructed_global_is_loaded_before_use(self, page):
        text = page.read_text(encoding="utf-8")
        for src in _SCRIPT_SRC.findall(text):
            target = (page.parent / src.split("?")[0]).resolve()
            if target.is_file():
                target.read_text(encoding="utf-8", errors="ignore")

        inline = text[text.rindex("</script>") - 4000 :]
        for symbol in self.REQUIRED_GLOBALS:
            if f"new {symbol}(" not in inline:
                continue  # this page does not construct it
            definer = self.DEFINERS[symbol]
            assert any(
                str(definer.name) in src for src in _SCRIPT_SRC.findall(text)
            ), (
                f"{page.name} constructs `new {symbol}()` but never loads a script "
                f"named {definer.name} — ReferenceError at startup"
            )

    @pytest.mark.parametrize(
        "page",
        [
            ROOT / "apps/desktop-app/electron_app/index.html",
            ROOT / "apps/web-live2d-viewer/index.html",
        ],
        ids=["desktop", "web"],
    )
    def test_app_js_is_loaded_after_its_dependencies(self, page):
        """app.js uses other modules inside its constructor, so order matters."""
        text = page.read_text(encoding="utf-8")
        sources = [src.split("?")[0] for src in _SCRIPT_SRC.findall(text)]
        names = [os.path.basename(s) for s in sources]
        assert "app.js" in names, f"{page.name} never loads app.js"
        app_index = names.index("app.js")
        for dependency in (
            "live2d-manager.js",
            "input-handler.js",
            "audio-handler.js",
            "haptic-handler.js",
            "wallpaper-handler.js",
            "unified-display-matrix.js",
        ):
            if dependency in names:
                assert names.index(dependency) < app_index, (
                    f"{dependency} must load before app.js (its constructor uses it)"
                )

    def test_no_page_loads_a_second_copy_of_the_dialogue_panel(self):
        """dialogue-ui.js builds its own panel; the page already has one.

        Loading it injected a second panel, duplicated four ids
        (#btn-send, #btn-toggle-dialogue, #dialogue-input, #dialogue-messages)
        and — because getElementById returns the first match and the injected
        container is appended last — re-bound its handlers to the page's own
        send/toggle buttons, so one click could send twice.
        """
        for page in (
            ROOT / "apps/desktop-app/electron_app/index.html",
            ROOT / "apps/web-live2d-viewer/index.html",
        ):
            assert "dialogue-ui.js" not in page.read_text(encoding="utf-8"), (
                f"{page.name} loads dialogue-ui.js on top of its own dialogue panel"
            )

    def test_proactive_speech_renders_in_the_real_panel(self):
        """_handleAngelaAction must not depend on the unloaded DialogueUI class."""
        source = (SOURCE_DIR / "app.js").read_text(encoding="utf-8")
        assert "addDialogueMessage('angela', message)" in source
        assert "this.dialogueUI" not in source.replace(
            "//    `this.dialogueUI` was always null: no page loaded dialogue-ui.js, and", ""
        ), "app.js still routes proactive speech through the never-loaded class"

    def test_shared_index_js_is_only_a_platform_helper(self):
        """Guards against mistaking index.js for the app entry point again."""
        text = (SOURCE_DIR / "index.js").read_text(encoding="utf-8")
        assert "class AngelaApp" not in text
        assert "require(" not in text and "import " not in text
