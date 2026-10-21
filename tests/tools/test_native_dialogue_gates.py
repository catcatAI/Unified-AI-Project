"""設定衛生、未拆門禁登記簿與純本地對話預算門禁的合約測試。

三道門禁守的是同一件事：**不讓「非預設配置」與「沒有拆除理由的臨時門禁」
混進版本控制**，以及**不讓純本地對話品質默默退步**。
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"


def _load(name: str):
    """Import a script by path (the module must be in sys.modules: dataclasses
    resolve their own module entry while being created)."""
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------- #
# The config hygiene gate
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def config_gate():
    return _load("check_default_config")


def test_no_user_config_layer_is_tracked(config_gate) -> None:
    """The user layer is runtime state (like .env) — it must not be committed."""
    tracked = config_gate._tracked_files()
    assert config_gate._check_user_layers(tracked) == []


def test_the_user_layer_is_git_ignored() -> None:
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", "apps/backend/configs/system/llm.user.yaml"],
        cwd=str(REPO_ROOT),
        check=False,
    )
    assert ignored.returncode == 0, "the user config layer must be git-ignored"


def test_no_api_key_literal_is_committed(config_gate) -> None:
    assert config_gate._check_key_literals(config_gate._tracked_files()) == []


def test_the_evolved_layer_cannot_open_the_cloud(config_gate) -> None:
    assert config_gate._check_deployment_mode() == []


def test_the_config_gate_passes_on_this_tree() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "check_default_config.py")],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


# --------------------------------------------------------------------------- #
# The open-gates registry
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def gates_guard():
    return _load("check_open_gates")


def test_the_registry_is_wellformed(gates_guard) -> None:
    registry = gates_guard._load()
    ci_text = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    problems = []
    for entry in registry.get("gates") or []:
        problems.extend(gates_guard.check_entry(entry, ci_text))
    assert problems == []


def test_every_registered_gate_carries_a_removal_reason(gates_guard) -> None:
    registry = gates_guard._load()
    for entry in registry.get("gates") or []:
        assert entry.get("removal_criterion", "").strip()
        assert entry.get("why_temporary", "").strip()


def test_a_vague_removal_reason_is_rejected(gates_guard) -> None:
    """「之後／視情況」這種理由不得進簿。"""
    entry = {
        "id": "vague-gate",
        "script": "scripts/check_open_gates.py",
        "opened": "2026-10-21",
        "owner": "project",
        "why_temporary": "守一個會被修好的缺陷",
        "removal_criterion": "之後視情況再說",
        "ci_step": "python scripts/check_open_gates.py",
    }
    problems = gates_guard.check_entry(
        entry, (REPO_ROOT / ".github/workflows/ci.yml").read_text("utf-8")
    )
    assert any("vague" in problem for problem in problems)


def test_a_removal_reason_without_a_checkable_condition_is_rejected(gates_guard) -> None:
    entry = {
        "id": "unmeasurable-gate",
        "script": "scripts/check_open_gates.py",
        "opened": "2026-10-21",
        "owner": "project",
        "why_temporary": "守一個會被修好的缺陷",
        "removal_criterion": "等品質變好就拆掉",
        "ci_step": "python scripts/check_open_gates.py",
    }
    problems = gates_guard.check_entry(
        entry, (REPO_ROOT / ".github/workflows/ci.yml").read_text("utf-8")
    )
    assert any("checkable" in problem for problem in problems)


def test_a_permanent_gate_is_rejected(gates_guard) -> None:
    entry = {
        "id": "permanent-gate",
        "script": "scripts/mypy_budget_gate.py",
        "permanent": True,
        "opened": "2026-10-21",
        "owner": "project",
        "why_temporary": "不需要",
        "removal_criterion": "不需要",
        "ci_step": "python scripts/mypy_budget_gate.py",
    }
    problems = gates_guard.check_entry(
        entry, (REPO_ROOT / ".github/workflows/ci.yml").read_text("utf-8")
    )
    assert any("permanent" in problem for problem in problems)


def test_a_gate_that_is_not_wired_into_ci_is_rejected(gates_guard) -> None:
    entry = {
        "id": "unwired-gate",
        "script": "scripts/check_open_gates.py",
        "opened": "2026-10-21",
        "owner": "project",
        "why_temporary": "守一個會被修好的缺陷（門檻 ≥ 0.9）",
        "removal_criterion": "當分數 ≥ 0.9 就拆（python scripts/probe_native_dialogue.py）",
        "ci_step": "python scripts/does_not_exist.py",
    }
    problems = gates_guard.check_entry(entry, "")
    assert any("ci.yml" in problem for problem in problems)


def test_the_registry_gate_passes_on_this_tree() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "check_open_gates.py")],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_the_registry_names_its_gates() -> None:
    registry = json.loads((SCRIPTS / "open_gates.json").read_text(encoding="utf-8"))
    assert registry.get("gates"), "the registry must not be empty"
    for entry in registry["gates"]:
        assert (REPO_ROOT / entry["script"]).is_file()
        if entry.get("budget"):
            assert (REPO_ROOT / entry["budget"]).is_file()


# --------------------------------------------------------------------------- #
# The native-only dialogue probe and its budget gate
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def probe():
    return _load("probe_native_dialogue")


def test_the_probe_scores_every_class(probe) -> None:
    """A canned answer, an echo, an artefact and a correct answer are distinct."""
    from services.visual_verdict import (  # noqa: F401  (the import proves the dependency)
        repetition_score,
    )

    correct = probe.score_turn(0, "What is 2+2?", "What is 2+2 = 4.0", "math", 0.1, "4.0", [])
    assert "correct" in correct.classes

    echo = probe.score_turn(
        0,
        "Who is taller, Alice or Bob?",
        "Who is taller, Alice or Bob=false",
        "unified",
        0.1,
        None,
        [],
    )
    assert "echo" in echo.classes or "artifact" in echo.classes

    artifact = probe.score_turn(
        0, "Tell me something.", "the answer is =false", "unified", 0.1, None, []
    )
    assert "artifact" in artifact.classes

    empty = probe.score_turn(0, "Tell me something.", "", "unified", 0.1, None, [])
    assert "empty" in empty.classes


def test_an_abstention_is_not_counted_as_correct(probe) -> None:
    turn = probe.score_turn(
        0,
        "A is taller than B, who is taller?",
        "agent, I don't have enough knowledge to answer this correctly yet.",
        "unified",
        0.1,
        "A is the tallest",
        [],
    )
    assert "abstain" in turn.classes
    assert not turn.answered


def test_a_repeated_answer_is_a_qa_machine(probe) -> None:
    first = probe.score_turn(0, "How are you?", "今天是个好日子！", "template", 0.1, None, [])
    second = probe.score_turn(
        1, "What is the weather?", "今天是个好日子！", "template", 0.1, None, [first]
    )
    assert "qa_machine" in second.classes


def test_the_budget_file_has_every_key_the_gate_reads() -> None:
    gate = _load("native_dialogue_budget_gate")
    budget = gate.load_budget()
    for _direction, key, _path in gate.CHECKS:
        assert key in budget, f"the budget file is missing {key!r}"
    assert "max_turns" in budget
    assert "max_seconds" in budget


def test_the_budget_gate_reports_a_violation() -> None:
    """A report that breaks the budget must fail the gate (exit 1)."""
    import tempfile

    gate = _load("native_dialogue_budget_gate")
    budget = gate.load_budget()
    report = {
        "budget": {"used_turns": 1, "used_seconds": 1.0},
        "pass2": {
            "human_score": 0.0,
            "rates": {
                "echo": 1.0,
                "artifact": 1.0,
                "qa_machine": 1.0,
                "offtopic": 1.0,
                "abstain": 1.0,
                "empty": 1.0,
            },
        },
        "progress": -1.0,
    }
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "report.json"
        path.write_text(json.dumps(report), encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "native_dialogue_budget_gate.py"),
                "--report",
                str(path),
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
    assert result.returncode == 1, result.stdout + result.stderr
    assert "超標" in result.stdout


def test_the_native_only_service_refuses_external_backends() -> None:
    """The native-only assertion must reject a non-project backend."""
    probe = _load("probe_native_dialogue")

    class Fake:
        backends = {"openai": object()}

    with pytest.raises(probe.NativeOnlyError):
        probe.assert_native_only(Fake())


def test_the_probe_only_allows_the_projects_own_backends() -> None:
    probe = _load("probe_native_dialogue")
    assert "unified" in probe.PROJECT_OWN_BACKENDS
    for external in ("openai", "anthropic", "google", "ollama", "llamacpp"):
        assert external not in probe.PROJECT_OWN_BACKENDS
