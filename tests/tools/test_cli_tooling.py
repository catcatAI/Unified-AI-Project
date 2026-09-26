"""
Regression tests for the pnpm / CLI tooling chain.

WHY this file exists
--------------------
Every script in `package.json` and `packages/cli/package.json` is a promise the
user can type. None of them were covered by a test, and three of them were
false:

* they invoked `python`, which does not exist in this environment
  (only `/usr/bin/python3`);
* `port-check` / `port-get` called port_manager with no argument, which printed
  usage text and exited — a check that checks nothing;
* `port-kill` / `port-kill-service` also called with no argument, so they could
  not kill anything, and giving `kill` a default port would have been worse.

ANGELA-MATRIX: [L4] [δ] [B] [L1]
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CLI_DIR = ROOT / "packages" / "cli" / "cli"


def _scripts_nodes(package_json: Path) -> dict:
    data = json.loads(package_json.read_text(encoding="utf-8"))
    return data.get("scripts", {})


# --------------------------------------------------------------------------- #
# 1. No script may invoke a `python` that does not exist
# --------------------------------------------------------------------------- #
_PYTHON_BARE = re.compile(r"^python(?!\w)")
_SHELL_STAGE_SPLIT = re.compile(r"&&|\|\||[;|]")


def _bare_python_invocations(command: str):
    """Only the first token of a shell stage can be an interpreter.

    Scanning the whole string would flag `pnpm lint:python` (a script *name*),
    which is harmless.
    """
    found = []
    for stage in _SHELL_STAGE_SPLIT.split(command):
        tokens = stage.strip().split()
        if tokens and _PYTHON_BARE.match(tokens[0]):
            found.append(tokens[0])
    return found


@pytest.mark.parametrize(
    "package_json",
    [
        ROOT / "package.json",
        ROOT / "packages" / "cli" / "package.json",
        ROOT / "packages" / "shared-js" / "package.json",
    ],
    ids=["root", "cli", "shared-js"],
)
def test_no_script_invokes_bare_python(package_json):
    """`python` is absent from PATH; such a script dies with exit 127."""
    offenders = {
        name: _bare_python_invocations(cmd)
        for name, cmd in _scripts_nodes(package_json).items()
        if _bare_python_invocations(cmd)
    }
    assert not offenders, f"{package_json.name} still calls a non-existent `python`: {offenders}"


def test_python_is_genuinely_absent():
    """Sanity check for the assumption above, so the guard cannot rot."""
    try:
        probe = subprocess.run(["python", "--version"], capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return  # no `python` at all — exactly the case being guarded
    assert probe.returncode != 0, "python exists here — relax test_no_script_invokes_bare_python"


# --------------------------------------------------------------------------- #
# 2. port_manager: the pnpm scripts must pass the arguments they need
# --------------------------------------------------------------------------- #
CLI_SCRIPTS = _scripts_nodes(ROOT / "packages" / "cli" / "package.json")


@pytest.mark.parametrize(
    "script,port_manager_command",
    [("port-check", "check"), ("port-get", "get-port")],
)
def test_read_only_port_scripts_pass_no_argument(script, port_manager_command):
    """No-arg is the *intended* contract for these: they must report all ports."""
    assert CLI_SCRIPTS[script].split()[-2:] == ["cli/port_manager.py", port_manager_command]


@pytest.mark.parametrize("script", ["port-kill", "port-kill-service"])
def test_destructive_port_scripts_are_not_promoted_as_npm_runnable(script):
    """`pnpm port-kill` with no argument could not kill anything.

    Rather than keep two commands that always print usage, the package scripts
    are gone: a kill must name its target.
    """
    assert script not in CLI_SCRIPTS, (
        f"`{script}` takes no argument, so it can never succeed; kill by explicit "
        f"`python3 packages/cli/cli/port_manager.py kill <port>` instead"
    )


def test_port_manager_no_arg_check_reports_every_service(capsys):
    sys.path.insert(0, str(CLI_DIR))
    try:
        import port_manager
    finally:
        sys.path.pop(0)

    port_manager.main(["check"])
    out = capsys.readouterr().out
    assert "BACKEND_API" in out
    assert "available" in out or "in use" in out


def test_port_manager_no_arg_get_port_lists_every_service(capsys):
    sys.path.insert(0, str(CLI_DIR))
    try:
        import port_manager
    finally:
        sys.path.pop(0)

    port_manager.main(["get-port"])
    out = capsys.readouterr().out
    assert "BACKEND_API:" in out
    assert "FRONTEND_DASHBOARD:" in out


def test_port_manager_kill_without_port_refuses(capsys):
    """A `kill` with no port must never default to the backend port."""
    sys.path.insert(0, str(CLI_DIR))
    try:
        import port_manager
    finally:
        sys.path.pop(0)

    called = []
    port_manager.PortManager.kill_process_by_port = lambda self, port: called.append(port)
    try:
        port_manager.main(["kill"])
    finally:
        del port_manager.PortManager.kill_process_by_port

    assert called == [], "kill defaulted to a port the user never named"
    assert "port is required" in capsys.readouterr().out


def test_port_manager_kill_service_without_name_refuses(capsys):
    sys.path.insert(0, str(CLI_DIR))
    try:
        import port_manager
    finally:
        sys.path.pop(0)

    called = []
    port_manager.PortManager.kill_existing_process = lambda self, name: called.append(name)
    try:
        port_manager.main(["kill-service"])
    finally:
        del port_manager.PortManager.kill_existing_process

    assert called == []
    out = capsys.readouterr().out
    assert "kill-service <service>" in out
    assert "Known services:" in out


# --------------------------------------------------------------------------- #
# 3. The HSP CLI must not await a synchronous initializer
# --------------------------------------------------------------------------- #
def test_hsp_cli_tolerates_sync_service_initialization():
    """`core_services.initialize_services` is sync and returns None.

    `main.py` awaited it unconditionally, so the real (non-mock) path raised
    "object NoneType can't be used in 'await' expression" and the CLI died on
    startup — a code path no test had ever executed.
    """
    source = (CLI_DIR / "main.py").read_text(encoding="utf-8")
    assert "await initialize_services(" not in source
    assert "inspect.isawaitable" in source, "guard against sync/async duality is gone"


def test_core_services_initialize_is_synchronous():
    """Pins the contract the CLI now adapts to."""
    source = (ROOT / "apps/backend/src/core_services.py").read_text(encoding="utf-8")
    body = source.split("def initialize_services", 1)[1]
    assert "async def" not in body.split("def ", 1)[0]


def test_hsp_cli_help_runs(tmp_path):
    """`--help` must not require a backend, a port, or an awaitable service."""
    result = subprocess.run(
        [sys.executable, str(CLI_DIR / "main.py"), "--help"],
        cwd=CLI_DIR.parent,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    combined = result.stdout + result.stderr
    assert "can't be used in 'await' expression" not in combined
    assert "usage" in combined.lower(), combined[-500:]


# --------------------------------------------------------------------------- #
# 4. OpenAPI / readiness must introspect the app that actually serves traffic
# --------------------------------------------------------------------------- #
def test_openapi_exporter_uses_the_production_app():
    source = (ROOT / "apps/backend/scripts/export_openapi.py").read_text(encoding="utf-8")
    assert (
        "from main import app" not in source
    ), "main:app is the legacy parallel app and omits 7 atlassian endpoints"
    assert "from services.main_api_server import app" in source


def test_readiness_audit_uses_the_production_app():
    source = (ROOT / "scripts/verify_readiness.py").read_text(encoding="utf-8")
    assert "production_app" in source
    assert (
        "app = main_module.create_app()" not in source
    ), "a readiness report built from the legacy app under-reports the API surface"
