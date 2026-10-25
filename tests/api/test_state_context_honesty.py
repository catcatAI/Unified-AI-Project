"""Phase 1 item 2 of the three-core plan — a ghost metric must not be shown.

The adjudication is binary: a quantity is either computed for real or taken
out of the prompt/context. It may never be displayed as if it were live.

Evidence behind each assertion:

- ``update_zeta()`` has zero production callers, so the four ζ sub-metrics
  are frozen defaults (memory_depth 0.6, identity_continuity 0.75, ...).
  They are therefore kept out of the axes the LLM reads.
- ``η.success_rate`` has no observation until a module has actually run —
  production registers the default modules and never executes one — and
  ``η.structural_drift`` has no producer at all yet (the plan schedules it
  for Phase 2). Both arrive as ``None``, because ``0.0`` / ``1.0`` would be
  read as measurements.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

BACKEND_SRC = Path(__file__).resolve().parents[2] / "apps" / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

import api.routes.chat_routes as chat_routes  # noqa: E402
from core.engine.eta_axis import measured_eta_metrics  # noqa: E402
from services.llm.prompt_builder import _build_core_prompt  # noqa: E402


def _eta(execution_count: int = 0, success_rate: float = 1.0):
    return SimpleNamespace(
        active_modules=["logic_gate", "direct_router"],
        execution_count=execution_count,
        success_rate=success_rate,
        structural_drift=0.0,
    )


class TestMeasuredEtaMetrics:
    def test_no_state_at_all_is_not_measured(self):
        metrics = measured_eta_metrics(None)
        assert metrics["module_count"] == 0
        assert metrics["execution_count"] == 0
        assert metrics["success_rate"] is None
        assert metrics["structural_drift"] is None

    def test_registered_but_never_executed_reports_no_success_rate(self):
        metrics = measured_eta_metrics(_eta(execution_count=0, success_rate=1.0))
        assert metrics["module_count"] == 2
        assert metrics["execution_count"] == 0
        assert metrics["success_rate"] is None, "the default 1.0 has no observation behind it"
        assert metrics["structural_drift"] is None

    def test_success_rate_appears_once_a_module_has_run(self):
        metrics = measured_eta_metrics(_eta(execution_count=5, success_rate=0.8))
        assert metrics["success_rate"] == 0.8
        assert metrics["structural_drift"] is None, "drift still has no producer"

    def test_drift_is_never_reported_as_a_measured_zero(self):
        metrics = measured_eta_metrics(_eta(execution_count=5))
        assert metrics["structural_drift"] is None


class TestStateContextInjection:
    def test_ctx_state_matrix_leaves_zeta_out_of_the_llm_context(self, monkeypatch):
        state_matrix = SimpleNamespace(
            dimensions={
                "alpha": SimpleNamespace(values={"energy": 0.7}),
                "zeta": SimpleNamespace(values={"memory_depth": 0.6, "identity_continuity": 0.75}),
            },
            theta=SimpleNamespace(values={"novelty": 0.4}),
        )
        monkeypatch.setattr(chat_routes, "_get_state_matrix", lambda: state_matrix)
        monkeypatch.setattr(chat_routes, "_get_eta_axis", lambda: _eta())

        context = {}
        chat_routes._ctx_state_matrix(context)

        axes = context["state_for_llm"]["axes"]
        assert "alpha" in axes
        assert "zeta" not in axes, "a frozen axis must not reach the LLM as current state"

    def test_ctx_state_matrix_sends_none_for_unmeasured_eta(self, monkeypatch):
        state_matrix = SimpleNamespace(
            dimensions={"alpha": SimpleNamespace(values={"energy": 0.7})},
            theta=SimpleNamespace(values={}),
        )
        monkeypatch.setattr(chat_routes, "_get_state_matrix", lambda: state_matrix)
        monkeypatch.setattr(chat_routes, "_get_eta_axis", lambda: _eta())

        context = {}
        chat_routes._ctx_state_matrix(context)

        eta = context["state_for_llm"]["eta"]
        # execution_count is a true count, so it is always present — the
        # dashboard and this test both read it to tell "0 runs" from "0.0%".
        assert eta["execution_count"] == 0
        assert eta["success_rate"] is None
        assert eta["structural_drift"] is None


class TestPromptRendering:
    def _state(self, eta):
        return {
            "axes": {
                "alpha": {"values": {"energy": 0.7}},
                "zeta": {"values": {"memory_depth": 0.6}},
            },
            "theta": {
                "novelty": 0.4,
                "theta_negativity": 0.1,
                "creation_urge": 0.2,
                "correction_urge": 0.1,
            },
            "eta": eta,
            "guidance": [],
        }

    def test_unmeasured_eta_and_frozen_zeta_are_not_printed(self):
        prompt_text = _build_core_prompt(
            self._state(
                {
                    "module_count": 6,
                    "execution_count": 0,
                    "success_rate": None,
                    "structural_drift": None,
                }
            ),
            None,
            "",
        )
        assert "ALPHA" in prompt_text
        assert "ZETA" not in prompt_text
        # Both locales' templates, whichever the manager is set to.
        for marker in ("Structural drift", "結構漂移", "Success rate", "成功率"):
            assert marker not in prompt_text, f"an unmeasured value reached the prompt: {marker}"
        # The module count is a real fact and still belongs there.
        assert ("Active modules" in prompt_text) or ("活躍模組" in prompt_text)

    def test_measured_eta_values_are_still_rendered(self):
        prompt_text = _build_core_prompt(
            self._state(
                {
                    "module_count": 3,
                    "execution_count": 7,
                    "success_rate": 0.9,
                    "structural_drift": 0.05,
                }
            ),
            None,
            "",
        )
        assert "Active modules" in prompt_text or "活躍模組" in prompt_text
        assert "90.0%" in prompt_text
        assert "0.05" in prompt_text
