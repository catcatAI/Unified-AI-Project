"""Phase 1 item 3 of the three-core plan — one instance per formula, reads
that never write.

`LifeIntensityFormula` used to be instantiated three times
(`autonomous_life_cycle`, `cyber_identity`, `prompt_builder`) and the CDM
ledger four times (+ `router`'s memory_coordinator): one life state split
across private copies — a write path beside the snapshot (contract §9).
This file holds two properties:

1. **The sharing actually happened**: the original sites now receive the
   same object, so what the prompt shows is one life's state instead of a
   private initial-value copy nobody ever fed.
2. **Reads never write**: `peek_*` and the prompt's five formula lines leave
   the shared instance untouched (no history append, no time-integral clock
   advance, no ledger booking, no callbacks) — otherwise the unification
   would turn every prompt read into a second write path polluting the one
   shared state.
"""

import sys
from pathlib import Path

BACKEND_SRC = Path(__file__).resolve().parents[2] / "apps" / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from core.active_cognition_formula import get_active_cognition_formula  # noqa: E402
from core.cdm_dividend_model import (  # noqa: E402
    CognitiveActivity,
    CognitiveInvestment,
    get_cdm_model,
)
from core.hsm_formula_system import get_hsm_formula  # noqa: E402
from core.life.autonomous_life_cycle import AutonomousLifeCycle  # noqa: E402
from core.life.cyber_identity import CyberIdentity  # noqa: E402
from core.life_intensity_formula import get_life_intensity_formula  # noqa: E402
from core.non_paradox_existence import get_non_paradox  # noqa: E402


class TestOneInstancePerFormula:
    def test_prompt_shims_return_the_shared_instances(self):
        # Phase 3 item 1 removed the ``_get_life_intensity`` shim: the prompt
        # no longer reaches past the snapshot for life intensity (contract
        # §9 — the snapshot is the only exchange quantity). The four remaining
        # shims still resolve to the one shared instance each, and the
        # life-intensity line's route is pinned by the test below.
        from services.llm.prompt_builder import (
            _get_active_cognition,
            _get_cdm,
            _get_hsm,
            _get_non_paradox,
        )

        assert _get_cdm() is get_cdm_model()
        assert _get_hsm() is get_hsm_formula()
        assert _get_active_cognition() is get_active_cognition_formula()
        assert _get_non_paradox() is get_non_paradox()

    def test_life_intensity_line_reads_the_shared_instance_via_the_snapshot(self):
        """Phase 3 item 1: one life's state, now delivered by the snapshot.

        ``_formula_life_intensity_line`` fetches ``get_al_state().intensity``,
        and ``_read_intensity`` inside the snapshot *is*
        ``get_life_intensity_formula().peek_life_intensity()`` — so what the
        prompt shows is still the single shared instance, not a private copy,
        and the read books nothing (contract §9 / D11: no observation -> no
        line, never a dressed-up default).
        """
        from core.life.al_state import get_al_state
        from services.llm.prompt_builder import _formula_life_intensity_line

        shared = get_life_intensity_formula()
        before = (
            len(shared.intensity_history),
            shared.accumulated_gap_integral,
            shared.last_calculation,
        )

        snap_intensity = get_al_state().intensity
        line = _formula_life_intensity_line()

        if snap_intensity is None:
            assert line is None, "an unobserved intensity must render nothing"
        else:
            assert abs(snap_intensity - shared.peek_life_intensity()) < 1e-9
            assert line is not None
            assert f"{snap_intensity:.4f}" in line

        assert (
            len(shared.intensity_history),
            shared.accumulated_gap_integral,
            shared.last_calculation,
        ) == before, "the prompt must read the shared instance without writing it"

    def test_lifecycle_borrows_the_shared_instances(self, tmp_path):
        alc = AutonomousLifeCycle(config=None, persist_path=tmp_path / "state.json")

        assert alc.life_intensity is get_life_intensity_formula()
        assert alc.cdm is get_cdm_model()
        assert alc.hsm is get_hsm_formula()
        assert alc.active_cognition is get_active_cognition_formula()
        assert alc.non_paradox is get_non_paradox()

    async def test_cyber_identity_shares_instead_of_recreating(self):
        identity = CyberIdentity()
        await identity.initialize()

        assert identity.life_intensity_formula is get_life_intensity_formula()
        assert identity.active_cognition_formula is get_active_cognition_formula()

    def test_repeated_fetches_return_the_same_object(self):
        assert get_life_intensity_formula() is get_life_intensity_formula()
        assert get_cdm_model() is get_cdm_model()


class TestReadsNeverWrite:
    def test_peek_life_intensity_books_nothing(self):
        formula = get_life_intensity_formula()
        before = (
            len(formula.intensity_history),
            formula.accumulated_gap_integral,
            formula.last_calculation,
        )

        for _ in range(3):
            value = formula.peek_life_intensity()

        assert 0.0 <= value <= 1.0
        assert (
            len(formula.intensity_history),
            formula.accumulated_gap_integral,
            formula.last_calculation,
        ) == before, "a read must not append history or advance the integral clock"

    def test_calculate_life_intensity_still_books_the_write_path(self):
        formula = get_life_intensity_formula()
        before = len(formula.intensity_history)

        formula.calculate_life_intensity()

        assert len(formula.intensity_history) == before + 1

    def test_peek_cdm_books_nothing(self):
        cdm = get_cdm_model()
        inv = CognitiveInvestment(
            activity_type=CognitiveActivity.INTERACTING, duration_seconds=1.0, intensity=0.5
        )
        inv.calculate_consumption()
        before = (len(cdm.outputs), cdm.total_output, len(cdm.conversion_history))

        output = cdm.peek_life_sense_output(inv)

        assert output.output_amount >= 0.0
        assert (
            len(cdm.outputs),
            cdm.total_output,
            len(cdm.conversion_history),
        ) == before, "a read must not append outputs, grow total_output or record a conversion"

    def test_calculate_cdm_still_books_the_write_path(self):
        cdm = get_cdm_model()
        inv = CognitiveInvestment(
            activity_type=CognitiveActivity.INTERACTING, duration_seconds=1.0, intensity=0.5
        )
        # resource_consumed starts at 0 and only calculate_consumption()
        # fills it — without this the booked amount would be 0.0 (which is
        # also why the prompt line has always rendered amount=0.00).
        inv.calculate_consumption()
        before = (len(cdm.outputs), cdm.total_output, len(cdm.conversion_history))

        cdm.calculate_life_sense_output(inv)

        after = (len(cdm.outputs), cdm.total_output, len(cdm.conversion_history))
        assert after[0] == before[0] + 1
        assert after[1] > before[1]
        assert after[2] == before[2] + 1

    def test_all_five_prompt_formula_lines_write_nothing(self):
        """The prompt reads the shared instances every cycle — end to end."""
        from services.llm.prompt_builder import (
            _formula_active_cognition_line,
            _formula_cdm_line,
            _formula_hsm_line,
            _formula_life_intensity_line,
            _formula_non_paradox_line,
        )

        formula = get_life_intensity_formula()
        cdm = get_cdm_model()
        before = (
            len(formula.intensity_history),
            formula.accumulated_gap_integral,
            formula.last_calculation,
            len(cdm.outputs),
            cdm.total_output,
            len(cdm.conversion_history),
        )

        for line_fn in (
            _formula_hsm_line,
            _formula_life_intensity_line,
            _formula_active_cognition_line,
            _formula_cdm_line,
            _formula_non_paradox_line,
        ):
            line_fn()

        after = (
            len(formula.intensity_history),
            formula.accumulated_gap_integral,
            formula.last_calculation,
            len(cdm.outputs),
            cdm.total_output,
            len(cdm.conversion_history),
        )
        assert after == before, "the prompt must read the shared state without writing it"
