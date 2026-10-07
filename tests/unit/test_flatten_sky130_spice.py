# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""Tests for the sky130 SPICE flattener.

Every branch in this tool encodes a simulator failure that was actually hit:
unresolved ``{expr}`` substitutes kill ngspice with "Cannot compute substitute",
hand-collapsed Monte-Carlo blocks silently corrupted ``toxe`` from 4.148e-09 to
0.003443, and dropped model-card continuations produced cards with a name and no
physics. These tests pin each of those behaviours so the one-shot tool stays
trustworthy without needing the volare PDK installed.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from ai.hardware.flatten_sky130_spice import (
    collapse_monte_carlo,
    flatten,
    main,
    read_params,
    substitute,
)

# -----------------------------------------------------------------------------
# read_params
# -----------------------------------------------------------------------------


def test_read_params_collects_blocks_and_continuations(tmp_path: Path) -> None:
    deck = tmp_path / "params.spice"
    deck.write_text(
        ".param vth0 = 4.148e-09\n"
        "+ nfactor = 1.2\n"
        "* a comment between blocks\n"
        ".param toxe = 3.5e-09\n",
        encoding="utf-8",
    )
    assert read_params(deck) == {"vth0": "4.148e-09", "nfactor": "1.2", "toxe": "3.5e-09"}


def test_read_params_trailing_block_at_eof_is_not_lost(tmp_path: Path) -> None:
    deck = tmp_path / "params.spice"
    deck.write_text(".param vth0 = 4.148e-09\n+ nfactor = 1.2\n", encoding="utf-8")
    assert read_params(deck) == {"vth0": "4.148e-09", "nfactor": "1.2"}


def test_read_params_skips_malformed_lines_and_last_definition_wins(tmp_path: Path) -> None:
    deck = tmp_path / "params.spice"
    deck.write_text(
        ".param vth0 = 1.0\n.param vth0 = 2.0\n.nothing interesting here\n",
        encoding="utf-8",
    )
    assert read_params(deck) == {"vth0": "2.0"}


def test_read_params_handles_a_param_line_without_assignment(tmp_path: Path) -> None:
    # A .param line with no "=" must not crash and must not capture anything.
    deck = tmp_path / "params.spice"
    deck.write_text(
        ".param vth0 = 1.0\n.param orphan\n.param vth1 = 2.0\n",
        encoding="utf-8",
    )
    assert read_params(deck) == {"vth0": "1.0", "vth1": "2.0"}


# -----------------------------------------------------------------------------
# collapse_monte_carlo
# -----------------------------------------------------------------------------


def test_collapse_keeps_the_deterministic_base_term() -> None:
    text = "m1 d g s b sky130_fd_pr__nfet l={4.148e-09+MC_MM_SWITCH*AGAUSS(0,1.0,1)*(1)}"
    assert collapse_monte_carlo(text) == "m1 d g s b sky130_fd_pr__nfet l={4.148e-09}"


def test_collapse_without_a_base_term_reduces_to_zero() -> None:
    text = ".param mc_mm_switch = {MC_MM_SWITCH*AGAUSS(0,1.0,1)*(1)}"
    assert collapse_monte_carlo(text) == ".param mc_mm_switch = {0.0}"


def test_collapse_handles_every_mc_distribution_token() -> None:
    for token in ("AGAUSS", "AUNIF", "LUNIF", "UNIF"):
        text = "{1.5+MC_X_SWITCH*" + token + "(0,1)}"
        assert collapse_monte_carlo(text) == "{1.5}", token


def test_collapse_leaves_plain_numeric_braces_alone() -> None:
    assert collapse_monte_carlo("l={4.148e-09} w={1}") == "l={4.148e-09} w={1}"


def test_collapse_is_idempotent_across_nested_substitutions() -> None:
    text = "{1.0+MC_A_SWITCH*AGAUSS(0,1,1)} {2.0+MC_B_SWITCH*UNIF(0,1)}"
    once = collapse_monte_carlo(text)
    assert once == "{1.0} {2.0}"
    assert collapse_monte_carlo(once) == once


# -----------------------------------------------------------------------------
# substitute
# -----------------------------------------------------------------------------


def test_substitute_resolves_parameters_and_strips_braces() -> None:
    assert substitute("{tox}", {"tox": "4.148e-09"}) == "4.148e-09"


def test_substitute_evaluates_pure_numeric_expressions_first() -> None:
    # Scientific notation contains an "e", so a letter-first test would reject
    # 4.148e-09 and leave it unresolved; the numeric eval must come first.
    assert substitute("{4.148e-09}", {}) == "4.148e-09"


def test_substitute_resolves_offset_sums_by_identifier() -> None:
    assert substitute("{0+toxe}", {"toxe": "0.0034"}) == "0.0034"


def test_substitute_leaves_unknown_expressions_untouched() -> None:
    text = "{vth0_3sigma}"
    assert substitute(text, {"unrelated": "1"}) == text


def test_substitute_never_executes_code_from_braces() -> None:
    text = "{__import__('os').system('touch /tmp/pwned')}"
    assert substitute(text, {}) == text


def test_substitute_depth_limit_stops_cyclic_definitions() -> None:
    params = {"a": "{b}", "b": "{a}"}
    result = substitute("{a}", params)  # must terminate, not hang
    assert isinstance(result, str)


def test_substitute_zero_division_is_left_unresolved() -> None:
    assert substitute("{1/0}", {}) == "{1/0}"


# -----------------------------------------------------------------------------
# flatten
# -----------------------------------------------------------------------------


PARAM_FILE = ".param tox = 4.148e-09\n.param nfactor = 1.2\n"
MODEL_FILE = (
    "* binned nfet models\n"
    ".model sky130_fd_pr__nfet_01v8__model.0 nmos\n"
    "* banner comment inside the card\n"
    "+ lmin = 1.0e-07 lmax = 1.0e-06\n"
    "+ tox = {tox}\n"
    "* a standalone comment line\n"
    ".model sky130_fd_pr__nfet_01v8__model.1 nmos\n"
    "+ tox = {tox}\n"
)


def test_flatten_resolves_parameters_and_keeps_card_continuations(tmp_path: Path) -> None:
    params = tmp_path / "params.spice"
    models = tmp_path / "models.spice"
    out = tmp_path / "out" / "nested" / "flat.spice"
    params.write_text(PARAM_FILE, encoding="utf-8")
    models.write_text(MODEL_FILE, encoding="utf-8")

    cards, unresolved = flatten([models], [params], out)

    assert cards == 2
    assert unresolved == []
    text = out.read_text(encoding="utf-8")
    # The banner comment between the .model line and its + continuations must
    # not end the card early (that is what produced name-only cards).
    assert "* banner comment inside the card" in text
    assert "+ lmin = 1.0e-07 lmax = 1.0e-06" in text
    assert "+ tox = 4.148e-09" in text
    assert text.startswith("* Flattened sky130 corner models")
    assert "* parameter count: 2" in text


def test_flatten_drops_subckt_wrappers_wholesale(tmp_path: Path) -> None:
    """The known-good flattened reference contains nothing but model cards.

    A subckt wrapper's device lines reference {l}/{w}/{ad} geometry that is
    neither needed nor resolvable offline, and leaving the wrapper in makes the
    simulator discard the .model cards beside it, so the whole wrapper goes.
    """
    params = tmp_path / "params.spice"
    models = tmp_path / "models.spice"
    out = tmp_path / "flat.spice"
    params.write_text(PARAM_FILE, encoding="utf-8")
    models.write_text(
        ".subckt sky130_fd_pr__nfet_01v8 d g s b\n"
        "m1 d g s b sky130_fd_pr__nfet_01v8__model l={l} w={w} ad={ad}\n"
        ".ends\n" + MODEL_FILE,
        encoding="utf-8",
    )

    cards, unresolved = flatten([models], [params], out)

    text = out.read_text(encoding="utf-8")
    assert cards == 2
    assert ".subckt" not in text
    assert ".ends" not in text
    assert "m1 d g s b" not in text
    assert unresolved == []


def test_flatten_collects_unresolved_substitutions(tmp_path: Path) -> None:
    models = tmp_path / "models.spice"
    out = tmp_path / "flat.spice"
    models.write_text(".model m nmos\n+ tox = {tox}\n+ vth = {vth0}\n", encoding="utf-8")

    cards, unresolved = flatten([models], [], out)

    assert cards == 1
    assert unresolved == ["tox", "vth0"]
    assert "+ tox = {tox}" in out.read_text(encoding="utf-8")


def test_flatten_skips_missing_files_and_reports_no_cards(tmp_path: Path) -> None:
    out = tmp_path / "flat.spice"
    cards, unresolved = flatten([tmp_path / "nope.spice"], [tmp_path / "no-params.spice"], out)
    assert cards == 0
    assert unresolved == []
    assert "* parameter count: 0" in out.read_text(encoding="utf-8")


def test_flatten_keeps_a_card_when_a_continuation_line_starts_with_star(tmp_path: Path) -> None:
    # A continuation line beginning with "*" must not terminate the card.
    params = tmp_path / "params.spice"
    models = tmp_path / "models.spice"
    out = tmp_path / "flat.spice"
    params.write_text(".param tox = 4.148e-09\n", encoding="utf-8")
    models.write_text(
        ".model sky130_fd_pr__nfet_01v8__model.0 nmos\n"
        "+ tox = {tox}\n"
        "* this comment is inside a card\n"
        "+ lmin = 1.0e-07\n",
        encoding="utf-8",
    )
    cards, unresolved = flatten([models], [params], out)
    assert cards == 1
    assert "* this comment is inside a card" in out.read_text(encoding="utf-8")


def test_flatten_keeps_a_card_when_a_continuation_line_starts_with_plus(tmp_path: Path) -> None:
    # A continuation line beginning with "+" after the header must not terminate
    # the card (the old code dropped such cards, which left name-only models).
    params = tmp_path / "params.spice"
    models = tmp_path / "models.spice"
    out = tmp_path / "flat.spice"
    params.write_text(".param tox = 4.148e-09\n", encoding="utf-8")
    models.write_text(
        ".model sky130_fd_pr__nfet_01v8__model.0 nmos\n"
        "+ tox = {tox}\n"
        "+ lmin = 1.0e-07\n"
        "+ lmax = 1.0e-06\n",
        encoding="utf-8",
    )
    cards, unresolved = flatten([models], [params], out)
    assert cards == 1
    text = out.read_text(encoding="utf-8")
    assert "+ tox = 4.148e-09" in text
    assert "+ lmin = 1.0e-07" in text
    assert "+ lmax = 1.0e-06" in text


def test_flatten_terminates_a_card_on_a_non_continuation_line(tmp_path: Path) -> None:
    # A line that does not start with "+" or "*" while in_card terminates the
    # card (the else branch at lines 187-189). A .subckt line inside a model
    # card is one such case: it is not a continuation, not a comment, and not
    # another .model, so it ends the current card.
    params = tmp_path / "params.spice"
    models = tmp_path / "models.spice"
    out = tmp_path / "flat.spice"
    params.write_text(".param tox = 4.148e-09\n", encoding="utf-8")
    models.write_text(
        ".model sky130_fd_pr__nfet_01v8__model.0 nmos\n"
        "+ tox = {tox}\n"
        ".subckt sky130_fd_pr__nfet_01v8 d g s b\n"
        ".ends\n"
        ".model sky130_fd_pr__nfet_01v8__model.1 nmos\n"
        "+ tox = {tox}\n",
        encoding="utf-8",
    )
    cards, unresolved = flatten([models], [params], out)
    assert cards == 2
    text = out.read_text(encoding="utf-8")
    # The first card ends at .subckt; the second card is the final .model.
    assert "sky130_fd_pr__nfet_01v8__model.0" in text
    assert "sky130_fd_pr__nfet_01v8__model.1" in text
    assert ".subckt" not in text  # subckt wrappers are dropped wholesale


# -----------------------------------------------------------------------------
# main() CLI
# -----------------------------------------------------------------------------


def _run_main(monkeypatch: pytest.MonkeyPatch, argv: list[str], capsys) -> int:
    monkeypatch.setattr(sys, "argv", ["flatten_sky130_spice.py"] + argv)
    return main()


def test_main_exits_zero_when_everything_resolves(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys
) -> None:
    params = tmp_path / "params.spice"
    models = tmp_path / "models.spice"
    out = tmp_path / "flat.spice"
    params.write_text(PARAM_FILE, encoding="utf-8")
    models.write_text(MODEL_FILE, encoding="utf-8")

    code = _run_main(
        monkeypatch,
        ["--models", str(models), "--params", str(params), "--out", str(out)],
        capsys,
    )

    assert code == 0
    assert "with 2 model cards" in capsys.readouterr().out


def test_main_exits_one_and_lists_unresolved_substitutions(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys
) -> None:
    models = tmp_path / "models.spice"
    out = tmp_path / "flat.spice"
    models.write_text(".model m nmos\n+ tox = {tox}\n+ vth = {vth0}\n", encoding="utf-8")

    code = _run_main(monkeypatch, ["--models", str(models), "--out", str(out)], capsys)

    assert code == 1
    captured = capsys.readouterr()
    assert "WARNING: 2 unresolved substitutions" in captured.out
    assert "tox" in captured.out and "vth0" in captured.out


def test_main_reports_the_card_count_of_an_empty_model_set(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys
) -> None:
    out = tmp_path / "flat.spice"
    code = _run_main(
        monkeypatch,
        ["--models", str(tmp_path / "missing.spice"), "--out", str(out)],
        capsys,
    )
    assert code == 0
    assert "with 0 model cards" in capsys.readouterr().out
