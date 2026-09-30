"""
`.env.example` must document every environment variable the code reads.

WHY this file exists
--------------------
An audit asked which defaults the project was missing. 47 environment variables
were read somewhere under `apps/backend/src` with no entry in `.env.example`, so
someone setting the project up had no documented value and no way to discover the
switch — including `ANGELA_SERVER_PORT`, `ANGELA_ROUTING_ENGINE`,
`VECTOR_DIMENSION` and the security-sensitive `ENCRYPTION_KEY`.

The file also shipped a value that contradicted the code: `LOG_LEVEL=DEBUG` while
`core/config/system_config.py` defaults to `INFO`, so every fresh install that
copied the template silently turned on verbose logging.

Both failure modes are silent and neither is caught by the test suite, so they are
asserted here. One deliberate exclusion is listed with its reason: a variable that
is legitimately not user-facing should not be forced into the template.

ANGELA-MATRIX: [L4] [δ] [B] [L1]
"""

import os
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "apps/backend/src"
ENV_EXAMPLE = ROOT / ".env.example"

# Variables that are not user-facing and must stay out of the template.
# Each needs a reason: an exclusion list without reasons becomes a dumping ground.
EXCLUDED = {
    "PATH": "provided by the OS",
    "HOME": "provided by the OS",
    "USER": "provided by the OS",
    "TERM": "provided by the OS",
    "DISPLAY": "provided by the X server",
    "WAYLAND_DISPLAY": "provided by the compositor",
    "NO_COLOR": "a CLI convention, not a project setting",
    "PYTHONPATH": "set by the interpreter, not by the project",
    "VIRTUAL_ENV": "set by the venv, not by the project",
    "LS_COLORS": "a terminal convention",
    "COLUMNS": "a terminal convention",
    "SHELL": "provided by the OS",
    "LANG": "provided by the OS",
    "LC_ALL": "provided by the OS",
    "TZ": "provided by the OS",
    "PWD": "provided by the shell",
    "OLDPWD": "provided by the shell",
    "SHLVL": "provided by the shell",
    "_": "set by the shell",
    "XDG_RUNTIME_DIR": "provided by the desktop session",
    "XDG_SESSION_TYPE": "provided by the desktop session",
    "XDG_CURRENT_DESKTOP": "provided by the desktop session",
    "GDK_BACKEND": "chosen by the graphics stack",
    "QT_QPA_PLATFORM": "chosen by the graphics stack",
    "LD_LIBRARY_PATH": "a loader concern, not a project setting",
    "SYSTEMROOT": "provided by Windows",
    "APPDATA": "provided by Windows",
    "LOCALAPPDATA": "provided by Windows",
    "USERPROFILE": "provided by Windows",
    "COMSPEC": "provided by Windows",
    "PATHEXT": "provided by Windows",
    "PROCESSOR_ARCHITECTURE": "provided by Windows",
    "NUMBER_OF_PROCESSORS": "a shell convenience",
    "PSModulePath": "provided by PowerShell",
    # Read only to *test* a condition; never part of a deployment.
    "TESTING": "test-suite internal",
    "TEST_MODE": "test-suite internal",
    "TESTING_MODE": "documented above as a real switch",
    "DEBUG": "legacy; read only by the deprecated core/config/system_config.py (0 imports)",
    "LOG_LEVEL": "legacy; read only by the deprecated core/config/system_config.py (0 imports)",
    "ENVIRONMENT": "generic; the project uses UNIFIED_AI_ENV",
    "PROJECT_ROOT": "generic; the project uses ANGELA_PROJECT_ROOT",
    "HOST": "generic; the project uses ANGELA_SERVER_HOST",
    "PORT": "generic; the project uses ANGELA_SERVER_PORT",
}

_READ = re.compile(r'os\.(?:getenv|environ\.get)\(\s*["\']([A-Z0-9_]{3,})["\']')
_READ_BRACKET = re.compile(r'os\.environ\[\s*["\']([A-Z0-9_]{3,})["\']')


def _repo_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "apps/backend/src").is_dir():
            return candidate
    raise AssertionError("could not locate the repository root")


_CONST = re.compile(r"^([A-Z][A-Z0-9_]{2,})\s*(?::\s*[^=]+)?=\s*(.+?)\s*(?:#.*)?$", re.M)


def _constants() -> dict:
    """Module-level constants, so a default written as a NAME can be resolved.

    `os.getenv("ANGELA_SERVER_HOST", SERVER_BIND_HOST)` states no literal; without
    this lookup the check would either skip it or compare a name to a value.

    Built in one pass and resolved afterwards: resolving during the scan would
    recurse, because resolving an expression needs the constant table.
    """
    raw: dict = {}
    for path in _repo_root().joinpath("apps/backend/src").rglob("*.py"):
        for name, expr in _CONST.findall(path.read_text(encoding="utf-8", errors="ignore")):
            raw.setdefault(name, expr.strip())
    resolved = {name: _resolve_expression(expr, raw) for name, expr in raw.items()}
    # one more pass so a constant defined in terms of another constant resolves
    return {name: _resolve_expression(value, raw) for name, value in resolved.items()}


def _resolve_expression(expr: str, constants: dict) -> str:
    """Reduce the handful of shapes that appear as getenv defaults to a literal.

    Anything it cannot reduce is returned unchanged, and the caller then skips the
    comparison rather than reporting a false conflict.
    """
    expr = (expr or "").strip().rstrip(",")
    if not expr:
        return ""
    if re.fullmatch(r"[A-Z][A-Z0-9_]{2,}", expr):
        # a bare constant name: follow it, but only one level deep
        return constants.get(expr, expr)
    wrapped = re.fullmatch(r"(?:str|int|float|bool)\(\s*([A-Z][A-Z0-9_]{2,})\s*\)", expr)
    if wrapped:
        # e.g. str(SERVER_PORT) — unwrap the conversion and follow the constant
        return constants.get(wrapped.group(1), expr)
    try:
        return str(eval(expr, {"__builtins__": {}}, dict(constants)))  # noqa: S307
    except Exception:
        return expr


def _balanced_default(text: str, start: int) -> str:
    """Read a getenv default, respecting nested parentheses.

    Splitting on the first ")" turned `str(SERVER_PORT` into the "default".
    """
    rest = text[start:].lstrip()
    if not rest.startswith(","):
        return ""
    rest = rest[1:].lstrip()
    depth = 0
    for index, char in enumerate(rest):
        if char in "([{":
            depth += 1
        elif char in ")]}":
            if depth == 0:
                return rest[:index].strip()
            depth -= 1
    return rest.strip()


def _code_env_vars() -> dict:
    """Env var -> the default the code passes to getenv (resolved, or empty)."""
    constants = _constants()
    found: dict = {}
    for path in _repo_root().joinpath("apps/backend/src").rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in _READ.finditer(text):
            name = match.group(1)
            if name not in found:
                found[name] = _balanced_default(text, match.end())
        for match in _READ_BRACKET.finditer(text):
            found.setdefault(match.group(1), "")
    return {k: _resolve_expression(v, constants) for k, v in found.items()}


def _documented() -> tuple:
    """(every documented name, live entries only).

    A commented entry documents a switch without setting it, so it counts for
    coverage but must not be compared against the code default: `# HAM_DISABLE_
    VECTOR_STORE=1` is a suggestion, and the code default is "0".
    """
    text = ENV_EXAMPLE.read_text(encoding="utf-8")
    all_names = {}
    live = {}
    for line in text.splitlines():
        stripped = line.strip()
        commented = stripped.startswith("#")
        if commented:
            stripped = stripped[1:].strip()
        match = re.match(r"^([A-Z0-9_]{3,})\s*=\s*(.*)$", stripped)
        if not match:
            continue
        name, value = match.group(1), match.group(2).split("#")[0].strip()
        all_names.setdefault(name, value)
        if not commented:
            live.setdefault(name, value)
    return all_names, live


@pytest.fixture(scope="module")
def code_vars() -> dict:
    return _code_env_vars()


@pytest.fixture(scope="module")
def documented() -> dict:
    return _documented()[0]


@pytest.fixture(scope="module")
def live_entries() -> dict:
    return _documented()[1]


def test_env_example_exists():
    assert ENV_EXAMPLE.is_file(), "the deployment template is missing"


def test_every_code_env_var_is_documented(code_vars, documented):
    """The defect this file was written for: switches nobody could discover."""
    missing = sorted(name for name in code_vars if name not in documented and name not in EXCLUDED)
    assert not missing, (
        "these environment variables are read by the code but absent from "
        f".env.example: {missing}"
    )


def test_documented_defaults_match_the_code(code_vars, live_entries):
    """A template that contradicts the code is worse than no template.

    This is what caught `ANGELA_WORKSPACE=./workspace` (the code defaults to the
    working directory, so the template silently redirected every file operation),
    `LOG_LEVEL=DEBUG` (code defaults to INFO), and three values I had guessed
    while writing the new entries.
    """
    conflicts = []
    for name, value in live_entries.items():
        if name not in code_vars:
            continue
        code_default = code_vars[name]
        if not value or not code_default:
            continue
        if value.startswith("<") or "<" in code_default:
            continue  # placeholder or an interpolated expression
        if value != code_default:
            conflicts.append(f"{name}: .env.example={value!r} but code default={code_default!r}")
    assert not conflicts, "documented defaults disagree with the code:\n  " + "\n  ".join(conflicts)


def test_exclusions_all_carry_a_reason():
    for name, reason in EXCLUDED.items():
        assert len(reason) > 10, f"{name} is excluded without a reason"


def test_no_real_secrets_are_committed():
    """The template must stay a template.

    §X #255 redacted leaked Google keys from the docs; this keeps the same
    guarantee for the file people actually copy.
    """
    text = ENV_EXAMPLE.read_text(encoding="utf-8")
    # Only an *uncommented* assignment can reach a real deployment. A commented
    # example showing the key format is documentation, and useful, so it is
    # allowed as long as it is obviously a placeholder.
    for line in text.splitlines():
        stripped = line.strip()
        commented = stripped.startswith("#")
        if commented:
            stripped = stripped[1:].strip()
        match = re.match(r"^([A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD)[A-Z0-9_]*)=(.*)$", stripped)
        if not match:
            continue
        name, value = match.group(1), match.group(2).split("#")[0].strip()
        if not value:
            continue  # an empty value, commented or not, asserts nothing
        # A template exists to show which slots to fill, so a self-describing
        # placeholder is the point. What must never appear is something that looks
        # like a real credential: long, and with no placeholder wording.
        lowered = value.lower().strip("\"'")
        looks_like_placeholder = (
            any(m in lowered for m in ("example", "your_", "generate", "change_me", "<"))
            or len(lowered) < 16
        )
        assert (
            looks_like_placeholder
        ), f"{name} looks like a real credential rather than a placeholder: {value!r}"


# --------------------------------------------------------------------------- #
# The other direction: a documented switch that nothing reads
# --------------------------------------------------------------------------- #
# The checks above make the code's switches discoverable. This one catches the
# mirror-image failure, which is invisible at runtime and has survived several
# audits: the template documented `BACKEND_HOST`/`BACKEND_PORT` while the code read
# `ANGELA_SERVER_HOST`/`ANGELA_SERVER_PORT`; it listed fourteen `CONTEXT_*`
# switches for features that do not exist; and it offered `STABLE_DIFFUSION_URL`
# while the image path read `ANGELA_SD_API_URL`. Setting any of them did nothing,
# and nothing said so.
#
# Only consumer roots are indexed. `tests/` is excluded on purpose: a test that
# calls `monkeypatch.setenv("ANGELA_TESTING", "true")` mentions the name while
# nothing reads it, which is precisely the failure being caught.
CONSUMER_ROOTS = (
    "apps/backend/src",
    "packages/shared-js",
    "scripts",
    "apps/desktop-app/electron_app",
    "apps/web-live2d-viewer/js",
    "apps/web-dashboard/src",
)
CONSUMER_FILES = ("docker-compose.yml", "Dockerfile", "package.json", "pyproject.toml")
CONSUMER_SUFFIXES = frozenset(
    {
        ".py",
        ".js",
        ".mjs",
        ".cjs",
        ".ts",
        ".tsx",
        ".json",
        ".yml",
        ".yaml",
        ".toml",
        ".sh",
        ".ps1",
        ".bat",
        ".cmd",
    }
)
# YAML, shell and Dockerfile comments start with "#" unambiguously, and an inline
# comment is how the trap was set: `keys.default.yaml` carried
# `base_url: "OLLAMA_BASE_URL_PLACEHOLDER" # Environment variable: OLLAMA_BASE_URL`
# and that comment was the setting's only appearance anywhere. Python and JS are
# left alone here because "#" inside a string is data, not a comment.
INLINE_COMMENT_SUFFIXES = frozenset({".yml", ".yaml", ".sh", ".ps1", ".bat", ".cmd", ".toml"})

# Documented for a runtime this repository does not own. Each needs a reason.
DOCUMENTED_FOR_ANOTHER_RUNTIME = {
    "NODE_ENV": "read by Node and Next.js themselves; project code never looks at it",
}


def _consumer_blob() -> str:
    """Every line of code/config that could read a variable, comments removed."""
    root = _repo_root()
    paths = []
    for relative in CONSUMER_ROOTS:
        directory = root / relative
        if directory.is_dir():
            paths.extend(p for p in directory.rglob("*") if p.is_file())
    paths.extend(root / name for name in CONSUMER_FILES if (root / name).is_file())

    lines = []
    for path in paths:
        if "__pycache__" in path.parts or path.suffix not in CONSUMER_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        inline = path.suffix in INLINE_COMMENT_SUFFIXES or path.name == "Dockerfile"
        for line in text.splitlines():
            if inline and " #" in line:
                line = line.split(" #", 1)[0]
            if line.strip().startswith("#"):
                continue
            lines.append(line)
    return "\n".join(lines)


def test_every_documented_env_var_is_read_by_something(documented):
    """A knob nobody reads is a promise the template cannot keep.

    Either wire it up or take it out of the template; leaving it in costs the next
    operator the time it takes to discover the switch is inert. One entry is
    exempted above with its reason.
    """
    blob = _consumer_blob()
    dead = sorted(
        name
        for name in documented
        if name not in DOCUMENTED_FOR_ANOTHER_RUNTIME and name not in blob
    )
    assert not dead, (
        "these variables are documented in .env.example but nothing under the "
        f"consumer roots reads them: {dead}"
    )


def test_exempted_documented_vars_all_carry_a_reason():
    for name, reason in DOCUMENTED_FOR_ANOTHER_RUNTIME.items():
        assert len(reason) > 20, f"{name} is exempted from the coverage contract without a reason"


def test_python_is_not_required_in_the_template():
    """`python` does not exist in this environment; the template must not imply it."""
    if os.environ.get("CI") == "true":
        return
    text = ENV_EXAMPLE.read_text(encoding="utf-8")
    assert "PYTHON_BIN=python\n" not in text
