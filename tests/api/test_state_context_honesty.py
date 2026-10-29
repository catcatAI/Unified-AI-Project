"""Phase 1 item 2 of the three-core plan — a ghost metric must not be shown.

The adjudication is binary: a quantity is either computed for real or taken
out of the prompt/context. It may never be displayed as if it were live.

Evidence behind each assertion:

- ``update_zeta()`` has zero production callers, so the four ζ sub-metrics
  are frozen defaults (memory_depth 0.6, identity_continuity 0.75, ...)
  and were kept out of the LLM's axes. Phase 2 item 2 computes them from
  ``TemporalState``; the rule became a per-key observation gate:
  ``_ctx_state_matrix`` sends only the keys listed in
  ``zeta_observed_fields``, and the prompt renders whatever the state
  builder vouches for. Unobserved -> absent; observed -> shown.
- ``η.success_rate`` has no observation until a module has actually run —
  production registers the default modules and never executes one, so the
  default ``1.0`` would be read as a measurement and arrives as ``None``.
- ``η.structural_drift`` gained its producer in Phase 2 item 2: composition
  vs the boot baseline (``mark_structural_baseline()``). It arrives as
  ``None`` whenever that baseline is missing (bare fake, restored state) —
  the stored ``0.0`` on such a state is not a comparison anyone made — and
  as a real number once the baseline exists, where ``0.0`` means
  "composition unchanged since boot" and is shown. Since Phase 3 item 1 it
  travels a single route: the AL snapshot (``drift.eta``) into the prompt;
  the AI layer's own context copy was removed because nothing read it, and
  ``drift.zeta`` renders the same way through ``angela.zeta.drift``.
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
        # No baseline on this fake: the 0.0 above is not a comparison, so
        # measured_eta_metrics must withhold it.
        structural_drift_observed=False,
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
        assert metrics["structural_drift"] is None, "no baseline was marked on this state"

    def test_drift_is_never_reported_as_a_measured_zero(self):
        # The fake carries a raw structural_drift of 0.0 — without a baseline
        # nobody made that comparison, so it must not be reported.
        metrics = measured_eta_metrics(_eta(execution_count=5))
        assert metrics["structural_drift"] is None

    def test_a_marked_baseline_reports_its_measured_zero(self):
        # Phase 2 item 2's producer: with the boot baseline in place the same
        # 0.0 IS a comparison ("composition unchanged since boot") and shows.
        from core.engine.eta_axis import EtaAxisState, create_default_modules

        state = EtaAxisState()
        for config in create_default_modules().values():
            state.register_module(config)
        state.mark_structural_baseline()

        metrics = measured_eta_metrics(state)
        assert state.structural_drift_observed is True
        assert metrics["structural_drift"] == 0.0

        state.unregister_module("xor_gate")
        assert measured_eta_metrics(state)["structural_drift"] > 0.0


class TestStateContextInjection:
    def test_ctx_state_matrix_leaves_unobserved_zeta_out_of_the_llm_context(self, monkeypatch):
        state_matrix = SimpleNamespace(
            dimensions={
                "alpha": SimpleNamespace(values={"energy": 0.7}),
                # The axis holds defaults — nobody has computed them yet, so
                # zeta_observed_fields is empty (cold start, one observation
                # max) and the gate must withhold the whole axis.
                "zeta": SimpleNamespace(values={"memory_depth": 0.6, "identity_continuity": 0.75}),
            },
            theta=SimpleNamespace(values={"novelty": 0.4}),
            zeta_observed_fields=frozenset(),
        )
        monkeypatch.setattr(chat_routes, "_get_state_matrix", lambda: state_matrix)
        monkeypatch.setattr(chat_routes, "_get_eta_axis", lambda: _eta())

        context = {}
        chat_routes._ctx_state_matrix(context)

        axes = context["state_for_llm"]["axes"]
        assert "alpha" in axes
        assert "zeta" not in axes, "an unobserved axis must not reach the LLM as current state"

    def test_ctx_state_matrix_sends_only_observed_zeta_keys(self, monkeypatch):
        state_matrix = SimpleNamespace(
            dimensions={
                "alpha": SimpleNamespace(values={"energy": 0.7}),
                # All four sub-metrics exist on the axis; only two of them
                # carry an observation (Phase 2 item 2) — the other two are
                # still defaults and must not be sent.
                "zeta": SimpleNamespace(
                    values={
                        "memory_depth": 0.04,
                        "temporal_coherence": 1.0,
                        "identity_continuity": 0.75,
                        "narrative_flow": 0.5,
                    }
                ),
            },
            theta=SimpleNamespace(values={"novelty": 0.4}),
            zeta_observed_fields=frozenset({"memory_depth", "temporal_coherence"}),
        )
        monkeypatch.setattr(chat_routes, "_get_state_matrix", lambda: state_matrix)
        monkeypatch.setattr(chat_routes, "_get_eta_axis", lambda: _eta())

        context = {}
        chat_routes._ctx_state_matrix(context)

        axes = context["state_for_llm"]["axes"]
        assert axes["zeta"]["values"] == {"memory_depth": 0.04, "temporal_coherence": 1.0}

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
        # Phase 3 item 1: drift is AL snapshot state (drift.eta) and never
        # enters the AI layer's own context — there is no reader for it here.
        assert "structural_drift" not in eta

    def test_measured_drift_reaches_the_prompt_only_via_the_al_snapshot(self, monkeypatch):
        # Phase 3 item 1 flip: the AI-side copy of η.structural_drift is gone
        # (no key in state_for_llm), and the same measured number reaches the
        # prompt when — and only when — the AL snapshot carries it.
        from core.life import al_state

        state_matrix = SimpleNamespace(
            dimensions={"alpha": SimpleNamespace(values={"energy": 0.7})},
            theta=SimpleNamespace(values={}),
        )
        eta = _eta(execution_count=5, success_rate=0.9)
        eta.structural_drift = 0.0
        eta.structural_drift_observed = True
        monkeypatch.setattr(chat_routes, "_get_state_matrix", lambda: state_matrix)
        monkeypatch.setattr(chat_routes, "_get_eta_axis", lambda: eta)

        context = {}
        chat_routes._ctx_state_matrix(context)

        sent = context["state_for_llm"]["eta"]
        assert "structural_drift" not in sent, "the AI layer must not carry AL drift"
        assert sent["success_rate"] == 0.9

        state = {
            "axes": {"alpha": {"values": {"energy": 0.7}}},
            "theta": {
                "novelty": 0.4,
                "theta_negativity": 0.1,
                "creation_urge": 0.2,
                "correction_urge": 0.1,
            },
            "eta": sent,
            "guidance": [],
        }
        # Snapshot supplies drift.eta -> the line renders (a measured 0.0
        # included: the observation gate already passed in measured_eta_metrics).
        monkeypatch.setattr(al_state, "_AL_SOURCES", {"drift": lambda: {"eta": 0.0}})
        prompt_text = _build_core_prompt(state, None, "")
        # The locale templates are authoritative (prompts.*.json): the value
        # line carries the "(stable)"/"(穩定)" suffix, which nothing else does.
        assert ("(stable)" in prompt_text) or ("(穩定)" in prompt_text)

        # Snapshot supplies nothing -> no line (D11: unobserved, not 0.0).
        monkeypatch.setattr(al_state, "_AL_SOURCES", {})
        prompt_text = _build_core_prompt(state, None, "")
        for marker in ("(stable)", "(穩定)"):
            assert (
                marker not in prompt_text
            ), f"drift reached the prompt without the snapshot: {marker}"


class TestPromptRendering:
    def _state(self, eta, zeta=None):
        axes = {"alpha": {"values": {"energy": 0.7}}}
        if zeta is not None:
            # What _ctx_state_matrix sends once the keys are observed.
            axes["zeta"] = {"values": zeta}
        return {
            "axes": axes,
            "theta": {
                "novelty": 0.4,
                "theta_negativity": 0.1,
                "creation_urge": 0.2,
                "correction_urge": 0.1,
            },
            "eta": eta,
            "guidance": [],
        }

    def test_unmeasured_eta_and_unobserved_zeta_are_not_printed(self, monkeypatch):
        # The cold gate output: no zeta in axes (nothing observed), eta
        # present but every unmeasured quantity None. Patch the provider
        # registry empty so a provider registered by an earlier test in the
        # same process cannot smuggle drift into this prompt.
        from core.life import al_state

        monkeypatch.setattr(al_state, "_AL_SOURCES", {})
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
        # Both locales' templates, whichever the manager is set to. The drift
        # markers are the locale texts (prompts.*.json), not the registration
        # defaults — "(stable)"/"(穩定)" is unique to a rendered drift value.
        for marker in ("(stable)", "(穩定)", "Success rate", "成功率"):
            assert marker not in prompt_text, f"an unmeasured value reached the prompt: {marker}"
        # The module count is a real fact and still belongs there.
        assert ("Active modules" in prompt_text) or ("活躍模組" in prompt_text)

    def test_observed_zeta_is_rendered(self, monkeypatch):
        # Phase 2 item 2: observed keys arrive through the gate and the
        # prompt renders them — computed values may be shown as current state.
        from core.life import al_state

        monkeypatch.setattr(al_state, "_AL_SOURCES", {})
        prompt_text = _build_core_prompt(
            self._state(
                {
                    "module_count": 3,
                    "execution_count": 0,
                    "success_rate": None,
                    "structural_drift": None,
                },
                zeta={"memory_depth": 0.04, "temporal_coherence": 1.0},
            ),
            None,
            "",
        )
        assert "ZETA" in prompt_text
        assert "memory_depth" in prompt_text
        assert "temporal_coherence" in prompt_text
        # The unmeasured eta quantities still stay out (locale-text markers).
        for marker in ("(stable)", "(穩定)", "Success rate", "成功率"):
            assert marker not in prompt_text

    def test_measured_eta_values_are_still_rendered(self, monkeypatch):
        # Phase 3 item 1: success_rate stays an AI-layer stat in
        # state_for_llm; structural_drift now comes from the AL snapshot.
        from core.life import al_state

        monkeypatch.setattr(al_state, "_AL_SOURCES", {"drift": lambda: {"eta": 0.05}})
        prompt_text = _build_core_prompt(
            self._state(
                {
                    "module_count": 3,
                    "execution_count": 7,
                    "success_rate": 0.9,
                }
            ),
            None,
            "",
        )
        assert "Active modules" in prompt_text or "活躍模組" in prompt_text
        assert "90.0%" in prompt_text
        assert "0.05" in prompt_text

    def test_zeta_drift_line_follows_the_al_snapshot(self, monkeypatch):
        # Phase 3 item 1: drift.zeta is an AL snapshot field — the prompt's
        # continuity-drift line renders if and only if the snapshot has it.
        from core.life import al_state

        state = self._state(
            {
                "module_count": 3,
                "execution_count": 0,
                "success_rate": None,
            }
        )
        monkeypatch.setattr(al_state, "_AL_SOURCES", {"drift": lambda: {"zeta": 0.12}})
        prompt_text = _build_core_prompt(state, None, "")
        assert ("Continuity drift" in prompt_text) or ("連續漂移" in prompt_text)
        assert "0.12" in prompt_text

        monkeypatch.setattr(al_state, "_AL_SOURCES", {})
        prompt_text = _build_core_prompt(state, None, "")
        for marker in ("Continuity drift", "連續漂移", "0.12"):
            assert marker not in prompt_text, f"unobserved ζ drift reached the prompt: {marker}"


class TestFormulaSnapshotRead:
    """Phase 3 item 1: the life-intensity formula line reads the AL snapshot.

    The prompt no longer reaches for the formula singleton itself — the value
    flows through ``get_al_state()`` (§9 exchange), and an unobserved value
    (None) drops the line entirely (D11).
    """

    def test_intensity_line_follows_the_snapshot(self, monkeypatch):
        from core.life import al_state
        from services.llm.prompt_builder import _formula_life_intensity_line

        monkeypatch.setattr(al_state, "_read_intensity", lambda: 0.4321)
        line = _formula_life_intensity_line()
        assert line is not None
        assert "0.4321" in line

        # Unobserved -> no line, never a fabricated 0.0000.
        monkeypatch.setattr(al_state, "_read_intensity", lambda: None)
        assert _formula_life_intensity_line() is None


class TestReplStateSnapshot:
    """The REPL ``/state`` snapshot — the third η display surface.

    It used to read ``service.state_matrix``/``service.eta_state`` off
    ChatService (attributes that never existed), so the except swallowed
    the whole snapshot in production. After the repoint it renders the
    shared singletons: bars for the axes, ``success`` n/a at 0 runs, and a
    *measured* drift line (Phase 2 item 2's boot baseline) instead of
    "no producer yet".
    """

    def test_snapshot_renders_the_shared_state_and_measured_drift(self):
        from cli.repl import _format_state_snapshot

        out = _format_state_snapshot(object())
        assert "8D State Matrix" in out
        assert "n/a (no module has executed)" in out, "0 runs must read as unmeasured"
        assert "drift" in out
        assert "n/a (no producer yet)" not in out, "the producer landed — drift is measured"
