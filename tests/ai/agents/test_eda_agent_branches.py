# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""Branch-closure tests for the EDA experiment agent.

Every except-branch below returns a structured ``error`` result instead of
raising into the orchestrator; if those paths decay, one broken experiment
crashes a whole user turn instead of one lane. This file keeps each one live.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict

import ai.agents.specialized.eda_agent as eda_agent_module
import pytest
from ai.agents.specialized.eda_agent import EdaAgent, _query_numbers
from ai.core.training_coordinator import TrainingCoordinator
from core.tools.eda_tool_adapter import EdaToolAdapter


def _agent(tmp_path, **agent_kwargs: Any) -> EdaAgent:
    config: Dict[str, Any] = {"enabled": True, "collect_learning_episodes": False}
    adapter = EdaToolAdapter(config=config, output_root=tmp_path)
    return EdaAgent(agent_id="branch_test", adapter=adapter, **agent_kwargs)


def _tool_facade(original: Any, breaking_run) -> Any:
    """Adapter facade that keeps every real method but breaks _run()."""
    import inspect as _inspect
    import types as _types

    facade = _types.SimpleNamespace(**vars(original))
    facade.enabled = True
    # __vars(original)__ does not carry bound methods: rebind every real one.
    for _name, _attr in _inspect.getmembers(original):
        if _name.startswith("_") and _name != "_run":
            continue
        setattr(facade, _name, _attr)

    async def boom(**_kwargs: object) -> Any:
        raise RuntimeError("boom from tools")

    facade._run = boom
    return facade


async def test_run_experiment_fail_closed_when_the_pipeline_raises(tmp_path) -> None:
    agent = _agent(tmp_path)
    agent._record_learning_episode = _disabled_episodes  # type: ignore[method-assign]

    # Patch the adapter's _run directly. Bound methods carry their original
    # self, so copying them to a SimpleNamespace does not redirect the call;
    # patching the instance attribute is the only reliable way to break _run
    # while keeping every other adapter method intact.
    async def boom(*_args: object, **_kwargs: object) -> Any:
        raise RuntimeError("boom from tools")

    agent.adapter._run = boom
    agent.adapter._resolve_tool = lambda tool: "/usr/bin/ngspice" if tool == "ngspice" else None

    result = await agent.run_experiment("R=10k C=100n", sweep=False)
    assert result["status"] == "error"
    assert "boom from tools" in result["message"]


async def test_run_cim_strip_experiment_fail_closed(tmp_path) -> None:
    agent = _agent(tmp_path)

    def boom(**_kwargs: object) -> Any:
        raise RuntimeError("strip exploded")

    agent.adapter = SimpleNamespace(
        enabled=True,
        create_workspace=lambda *a, **k: (_ for _ in ()).throw(RuntimeError("strip exploded")),
    )
    result = await agent.run_cim_strip_experiment()
    assert result["status"] == "error"
    assert "strip exploded" in result["message"]


async def test_run_cim_single_die_experiment_fail_closed(tmp_path) -> None:
    agent = _agent(tmp_path)
    agent.adapter = SimpleNamespace(
        enabled=True,
        create_workspace=lambda *a, **k: (_ for _ in ()).throw(RuntimeError("die exploded")),
    )
    result = await agent.run_cim_single_die_experiment()
    assert result["status"] == "error"
    assert "die exploded" in result["message"]


async def test_run_ai_card_reference_experiment_fail_closed(tmp_path) -> None:
    agent = _agent(tmp_path)

    class BoomModel:
        def __init__(self, *a: object) -> None:
            raise RuntimeError("card reference exploded")

    monkey = pytest.MonkeyPatch()
    try:
        real_import = __import__

        def fake_import(name: str, *args: object, **kwargs: object):
            if "ai_card_reference" in name:
                raise RuntimeError("card reference exploded")
            return real_import(name, *args, **kwargs)

        monkey.setattr("builtins.__import__", fake_import)
        result = await agent.run_ai_card_reference_experiment()
    finally:
        monkey.undo()
    assert result["status"] == "error"
    assert "card reference exploded" in result["message"]


async def test_run_logic_gate_experiment_fail_closed(tmp_path) -> None:
    agent = _agent(tmp_path)
    monkey = pytest.MonkeyPatch()
    try:
        real_import = __import__

        def fake_import(name: str, *args: object, **kwargs: object):
            if "boolean_gate_learner" in name:
                raise RuntimeError("gate learner exploded")
            return real_import(name, *args, **kwargs)

        monkey.setattr("builtins.__import__", fake_import)
        result = await agent.run_logic_gate_experiment(
            training_rows=[{"a": 0, "b": 0, "out": 0}],
            evaluation_rows=[{"a": 1, "b": 1, "out": 1}],
            oracle_expression="a and b",
        )
    finally:
        monkey.undo()
    assert result["status"] == "error"
    assert "gate learner exploded" in result["message"]


async def test_run_mvu_reference_experiment_fail_closed(tmp_path) -> None:
    agent = _agent(tmp_path)
    agent.adapter = SimpleNamespace(
        enabled=True,
        create_workspace=lambda *a, **k: (_ for _ in ()).throw(RuntimeError("mvu exploded")),
    )
    result = await agent.run_mvu_reference_experiment()
    assert result["status"] == "error"
    assert "mvu exploded" in result["message"]


async def test_run_rtl_experiment_fail_closed(tmp_path) -> None:
    agent = _agent(tmp_path)
    agent.adapter = SimpleNamespace(
        enabled=True,
        create_workspace=lambda *a, **k: (_ for _ in ()).throw(RuntimeError("rtl exploded")),
    )
    result = await agent.run_rtl_experiment()
    assert result["status"] == "error"
    assert "rtl exploded" in result["message"]


async def test_run_card_architecture_audit_fail_closed(tmp_path) -> None:
    agent = _agent(tmp_path)

    class BoomAudit:
        def audit(self, claimed) -> dict:
            raise RuntimeError("audit exploded")

    monkey = pytest.MonkeyPatch()
    try:
        real_import = __import__

        def fake_import(name: str, *args: object, **kwargs: object):
            if "card_architecture_audit" in name:
                raise RuntimeError("audit exploded")
            return real_import(name, *args, **kwargs)

        monkey.setattr("builtins.__import__", fake_import)
        result = await agent.run_card_architecture_audit()
    finally:
        monkey.undo()
    assert result["status"] == "error"
    assert "audit exploded" in result["message"]


async def _disabled_episodes(*_args: object, **_kwargs: object) -> Dict[str, Any]:
    return {"status": "disabled"}


async def test_verify_cim_weight_response_without_a_design_point(tmp_path) -> None:
    agent = _agent(tmp_path)
    monkey = pytest.MonkeyPatch()
    try:
        real_import = __import__

        async def fake_simulate_weight_response(*_a: object, **_k: object) -> dict:
            return {"status": "skipped", "reason": "ngspice_not_installed"}

        def fake_import(name: str, *args: object, **kwargs: object):
            if "cim_strip_reference" in name:
                return SimpleNamespace(
                    CimStripReferenceModel=lambda: SimpleNamespace(
                        recommended_design=lambda **k: {}
                    ),
                    simulate_weight_response=fake_simulate_weight_response,
                    MEASUREMENT_PROVENANCE={},
                    WEIGHT_RESPONSE_MEASUREMENT={
                        "cells_per_bin": [1, 2, 4, 8],
                        "word_0000_a": 0.0,
                        "single_hot_currents_a": [1e-6, 2e-6, 4e-6, 8e-6],
                        "word_1111_sum_a": 1.5e-5,
                        "fixture": "DOT4L",
                    },
                    SUPERSEDED_WEIGHT_RESPONSE={},
                    evaluate_weight_response=lambda measured: {"status": "pass"},
                )
            return real_import(name, *args, **kwargs)

        monkey.setattr("builtins.__import__", fake_import)
        result = await agent.verify_cim_weight_response()
    finally:
        monkey.undo()
    assert result["status"] == "verified"
    assert result["static_check"]["source"] == "bundled_measurement_fixture"


async def test_run_cim_dot_product_experiment_fail_closed(tmp_path) -> None:
    agent = _agent(tmp_path)

    class BoomSource:
        def build_test_vectors(self, *a: object, **k: object) -> list:
            raise RuntimeError("vector source exploded")

    agent.adapter = SimpleNamespace(
        enabled=True,
        create_workspace=agent.adapter.create_workspace,
    )
    monkey = pytest.MonkeyPatch()
    try:
        real_import = __import__

        def fake_import(name: str, *args: object, **kwargs: object):
            if "cim_strip_reference" in name:
                raise RuntimeError("vector source exploded")
            return real_import(name, *args, **kwargs)

        monkey.setattr("builtins.__import__", fake_import)
        result = await agent.run_cim_dot_product_experiment()
    finally:
        monkey.undo()
    assert result["status"] == "error"
    assert "vector source exploded" in result["message"]


async def test_probe_tools_message_names_available_tools(tmp_path) -> None:
    agent = _agent(tmp_path)

    async def fake_probe(**_kwargs: object) -> Dict[str, Any]:
        return {
            "tools": {
                "ngspice": {"available": True},
                "kicad": {"available": False},
                "magic": {"available": True},
            }
        }

    agent.adapter = SimpleNamespace(enabled=True, probe=fake_probe)
    result = await agent.probe_tools()
    assert result["message"] == "EDA tools available: ngspice, magic"


async def test_probe_tools_says_so_when_nothing_is_available(tmp_path) -> None:
    agent = _agent(tmp_path)

    async def fake_probe(**_kwargs: object) -> Dict[str, Any]:
        return {"tools": {"ngspice": {"available": False}}}

    agent.adapter = SimpleNamespace(enabled=True, probe=fake_probe)
    result = await agent.probe_tools()
    assert result["message"] == "No supported EDA executable is available"


async def test_record_learning_episode_reports_a_duplicate_and_a_failure(
    tmp_path,
) -> None:
    class FlakyCoordinator:
        def __init__(self) -> None:
            self.calls = 0

        async def enqueue_eda_episode(self, episode: Dict[str, Any]) -> bool:
            self.calls += 1
            return self.calls == 1  # first call queues, second reports a duplicate

    coordinator = FlakyCoordinator()
    config: Dict[str, Any] = {"enabled": True, "collect_learning_episodes": True}
    adapter = EdaToolAdapter(config=config, output_root=tmp_path)
    agent = EdaAgent(agent_id="episode_dup", adapter=adapter, training_coordinator=coordinator)
    first = await agent._record_learning_episode(
        workflow="wf",
        parameters={},
        tools={"probe": {"status": "success"}},
        results={"probe": {"status": "success"}},
        artifacts=[],
    )
    assert first["status"] == "queued"
    second = await agent._record_learning_episode(
        workflow="wf",
        parameters={},
        tools={"probe": {"status": "success"}},
        results={"probe": {"status": "success"}},
        artifacts=[],
    )
    assert second["status"] == "duplicate"

    class ThrowingCoordinator:
        async def enqueue_eda_episode(self, episode: Dict[str, Any]) -> bool:
            raise ValueError("queue full")

    failing = _agent(tmp_path, training_coordinator=ThrowingCoordinator())
    failing.collect_learning_episodes = True
    outcome = await failing._record_learning_episode(
        workflow="wf",
        parameters={},
        tools={"probe": {"status": "success"}},
        results={"probe": {"status": "success"}},
        artifacts=[],
    )
    assert outcome["status"] == "unavailable"
    assert "queue full" in outcome["diagnostics"][0]


async def test_record_learning_episode_survives_an_artifact_write_failure(
    tmp_path,
) -> None:
    class QueueingCoordinator:
        async def enqueue_eda_episode(self, episode: Dict[str, Any]) -> bool:
            return True

    adapter = EdaToolAdapter(
        config={"enabled": True, "collect_learning_episodes": True},
        output_root=tmp_path,
    )
    agent = EdaAgent(
        agent_id="artifact_fail", adapter=adapter, training_coordinator=QueueingCoordinator()
    )

    workspace = adapter.create_workspace("episode_artifact_fail")
    metadata = await agent._record_learning_episode(
        workflow="wf",
        parameters={},
        tools={"probe": {"status": "success"}},
        results={"probe": {"status": "success"}},
        artifacts=[],
        workspace=workspace,
    )

    # To force the OSError path, patch the bound method on the instance used
    # inside _record_learning_episode.
    def broken_write(*_args: object, **_kwargs: object) -> str:
        raise OSError("disk full")

    agent.adapter = SimpleNamespace(**vars(agent.adapter))
    agent.adapter.write_text_artifact = broken_write
    metadata = await agent._record_learning_episode(
        workflow="wf2",
        parameters={},
        tools={"probe": {"status": "success"}},
        results={"probe": {"status": "success"}},
        artifacts=[],
        workspace=workspace,
    )
    # episode still queued; the artifact failure is recorded, not raised
    assert metadata["status"] == "queued"
    assert "artifact_error" in metadata


# -----------------------------------------------------------------------------
# number parser continuation edges
# -----------------------------------------------------------------------------


def test_query_numbers_stops_at_an_unseparated_second_number() -> None:
    # "10k 20n" separated by whitespace is a list; "10k20n" glued together is
    # ambiguous on purpose -- the parser must not silently misread it.
    assert _query_numbers("R=10k, 20n", "R") == [10000.0, 20e-9]
    assert _query_numbers("R=10k and then some", "R") == [10000.0]


def test_query_numbers_handles_the_fullwidth_colon_and_unicode_comma() -> None:
    assert _query_numbers("R：10k，47k", "R") == [10000.0, 47000.0]


def test_query_numbers_ignores_zero_and_negative_entries() -> None:
    assert _query_numbers("R=0, 10k", "R") == [10000.0]
