"""Contract tests for the MVE-1 emergence-boundary instrument (CORE_GAP §十一.4).

Claims pinned here (no teaching to the test):

1. the gold family is exactly the four ``dt`` rungs of the contract §5
   operator, monotone toward the target, mode carried;
2. grading is single-gold exact (dt rides the input line since round 4,
   ``gold == family[rung]``) and the rotation control is a derangement — no
   row can ever be graded against its own gold;
3. the gate numbers are the registered threshold (≥5/200 and ≤1/200);
4. the set is deterministic, leak-free, in-window (192 tokens), and its
   prompt is byte-identical to the training pair's prefix;
5. ``generate_al_dataset.py --holdout-cells`` drops exactly the declared
   cells, keeps the rng stream, and is a no-op when off (byte-identical
   defaults, so existing ``--check`` runs keep passing).
"""

from __future__ import annotations

import importlib.util
import json
import math
from typing import Dict
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "probe_emergence_boundary.py"
GEN_SCRIPT = REPO_ROOT / "scripts" / "generate_al_dataset.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def probe():
    return _load("probe_emergence_boundary_test", SCRIPT)


@pytest.fixture(scope="module")
def gen():
    return _load("generate_al_dataset_mve_test", GEN_SCRIPT)


# -- 1. the family is the contract operator, four rungs --------------------


def test_family_is_the_four_contract_rungs(probe, gen):
    baseline, targets, _ = gen._pilot_tables()
    intent = sorted(targets)[0]
    # state pinned to the wall *opposite* the target: every rung moves a
    # visible, distinct distance at 2dp, so four distinct golds are guaranteed
    state = {
        f: (gen._RANGE[f][0] if targets[intent][f] > 0 else gen._RANGE[f][1]) for f in gen._FIELDS
    }
    state["routing_mode"] = "neutral"
    golds = probe.family_golds(state, intent, baseline, targets)
    assert len(golds) == 4 == len(gen._DT_LADDER)
    assert len(set(golds)) == 4, "rungs must be distinguishable at 2dp"
    for gold in golds:
        assert "<al_out>" in gold
        assert "mode=neutral" in gold
        assert f"intent={intent}" in gold
    # monotone approach to the target: each larger dt lands no farther away
    short = {"valence": "v", "arousal": "a", "dominance": "d"}
    target = targets[intent]
    for field in gen._FIELDS:
        key = short.get(field, field)
        values = []
        for gold in golds:
            tok = next(t for t in gold.split() if t.startswith(key + "="))
            values.append(float(tok.split("=", 1)[1]))
        distances = [abs(v - target[field]) for v in values]
        # larger dt -> smaller k -> lands *closer* to the target (descending)
        assert distances == sorted(distances, reverse=True), f"{field} not monotone in dt"


def test_reference_mode_is_never_the_holdout_mode(probe):
    assert probe._ref_mode("conservative") == "exploratory"
    assert probe._ref_mode("exploratory") == "neutral"
    for mode in probe.gen.MVE1_HOLDOUT_CELLS.values():
        assert probe._ref_mode(mode) != mode


# -- 2/3. grading and gate -------------------------------------------------


def test_grade_is_family_exact(probe):
    golds = ["<al_out> v=0.10", "<al_out> v=0.20", "<al_out> v=0.30", "<al_out> v=0.40"]
    assert probe.grade("  <al_out> v=0.30  ", golds) == (True, 2)
    assert probe.grade("<al_out> v=0.31", golds) == (False, None)
    assert probe.grade("", golds) == (False, None)
    assert probe.grade("<al_out> v=0.30 extra", golds) == (False, None)


def test_rotation_control_is_a_derangement(probe):
    rows = [{"sample_id": f"mve1h_{i:04d}"} for i in range(5)]
    rows += [{"sample_id": f"mve1r_{i:04d}"} for i in range(3)]
    rot = probe.rotation_index_map(rows)
    for i, j in enumerate(rot):
        assert j != i, "the control must never grade a row against its own gold"
        assert 0 <= j < len(rows)
        # a rotation must stay inside its own set (holdout vs reference)
        assert probe._set_label(rows[i]) == probe._set_label(rows[j])
    # a per-set rotation is a cycle: every gold in the set is used exactly once
    for label in ("holdout", "reference"):
        idxs = [i for i, e in enumerate(rows) if probe._set_label(e) == label]
        assert sorted(rot[i] for i in idxs) == idxs


def test_gate_matches_the_registered_threshold(probe):
    assert probe.gate(5, 1)["pass"] is True  # the registered MVE-1 numbers
    assert probe.gate(4, 1)["pass"] is False  # 4/200 < 5/200
    assert probe.gate(5, 2)["pass"] is False  # control too high
    assert probe.gate(0, 0)["pass"] is False  # every baseline so far
    g = probe.gate(5, 1)
    assert (g["n"], g["family_min"], g["rotation_max"]) == (200, 5, 1)


def test_pair_fit_is_the_exact_training_window(probe):
    prompt = " ".join(f"w{i}" for i in range(10))
    block = "v=0.00 a=0.00"
    budget = 3 + probe._atoms(prompt) + probe._atoms(block)
    assert probe.pair_fits(prompt, block, budget) is True
    assert probe.pair_fits(prompt, block, budget - 1) is False
    # a digit-heavy block costs one atom per digit (tokenize splits numbers)
    assert probe._atoms("v=-0.35") > probe._atoms("v=0.3")


# -- 4. the set ------------------------------------------------------------


@pytest.fixture(scope="module")
def small_set(probe):
    cells = {"unknown": "conservative", "knowledge_query": "neutral"}
    return probe.build(
        total=10,
        seed=5,
        skip=10000,
        window=2000,
        cells=cells,
        max_len=192,
        min_per_cell=4,
    )


def test_small_set_is_complete_and_in_window(probe, small_set, gen):
    assert small_set["total"] == 10
    assert small_set["reference_total"] == 10
    cells = small_set["provenance"]["cells"]
    for kind, rows in (("holdout", small_set["holdout"]), ("reference", small_set["reference"])):
        for entry in rows:
            assert len(entry["family"]) == 4
            expect_mode = (
                cells[entry["intent"]]
                if kind == "holdout"
                else probe._ref_mode(cells[entry["intent"]])
            )
            assert entry["mode"] == expect_mode
            assert entry["cell"] == f"{entry['intent']}:{entry['mode']}"
            # single-gold: the graded target is exactly the rung the prompt names
            assert entry["gold"] == entry["family"][entry["rung"]]
            assert entry["dt"] == gen._DT_LADDER[entry["rung"]]
            assert probe.pair_fits(entry["prompt"], entry["gold"], 192), entry["sample_id"]


def test_prompt_is_the_training_pair_prefix(probe, small_set, gen):
    """Byte-identical to prepare_ai_al_training_data's pair, response given.

    The input line carries dt (round-4 schema), serialised through the very
    same _state_line the trainer's pairs go through — one code path, so the
    probe cannot drift from the training format.
    """
    for entry in small_set["holdout"]:
        expected_in = (
            probe.prep._state_line(entry["state_in"], entry["intent"], "in", dt=entry["dt"])
            + " | "
            + entry["text"]
        )
        expected = (expected_in + "\n" + entry["response"]).strip()
        assert entry["prompt"] == expected
        assert f"dt={entry['dt']:.2f}" in entry["prompt"]


def test_rung_slots_cycle_so_every_cell_is_balanced(probe, small_set, gen):
    """The rung comes from the append position, not a fresh draw — adding dt
    cannot touch the rng stream, and cycles give each cell an even rung mix."""
    ladder = gen._DT_LADDER
    for kind in ("holdout", "reference"):
        rows = small_set[kind]
        assert [e["rung"] for e in rows] == [i % len(ladder) for i in range(len(rows))]
        for entry in rows:
            state_line = entry["prompt"].split(" | ", 1)[0]
            assert state_line.startswith("<al_in> ")
            assert f"dt={entry['dt']:.2f}" in state_line
            # the output side is a state, never a timestep
            assert " dt=" not in entry["gold"]


def test_set_is_deterministic_and_leak_free(probe, gen, small_set):
    again = probe.build(
        total=10,
        seed=5,
        skip=10000,
        window=2000,
        cells=small_set["provenance"]["cells"],
        min_per_cell=4,
    )
    assert json.dumps(again, sort_keys=True) == json.dumps(small_set, sort_keys=True)
    assert small_set["provenance"]["overlap_with_training"] == 0
    seen = set()
    for entry in small_set["holdout"]:
        assert entry["sample_id"] not in seen
        seen.add(entry["sample_id"])


def test_underfilled_cell_fails_loudly(probe, gen):
    with pytest.raises(SystemExit):
        # a window far too small to fill the per-cell quota
        probe.build(total=10, seed=5, skip=10000, window=10, min_per_cell=4)


# -- 5. the carve ----------------------------------------------------------


def test_carve_drops_exactly_the_declared_cells(gen):
    cells = dict(gen.MVE1_HOLDOUT_CELLS)
    plain = gen.build(rows=400, seed=7)
    carved = gen.build(rows=400, seed=7, holdout_cells=cells)
    expected = [
        ex
        for ex in plain["examples"]
        if cells.get(ex["intent"]) != ex["al_state_in"]["routing_mode"]
    ]
    assert carved["examples"] == expected, "carve must drop only the cells, in place"
    dropped = len(plain["examples"]) - len(carved["examples"])
    assert dropped > 0, "the sample must actually contain held-out cell rows"
    assert carved["provenance"]["holdout_carved"] == dropped
    assert carved["provenance"]["holdout_cells"] == cells


def test_carve_off_leaves_defaults_byte_identical(gen):
    plain = gen.build(rows=60, seed=7)
    assert "holdout_cells" not in plain["provenance"]
    assert "holdout_carved" not in plain["provenance"]
    # --expose-dt is off by default for the same byte-identity reason
    assert "expose_dt" not in plain["provenance"]
    assert all("dt" not in ex for ex in plain["examples"])
    # and the flag parses to a plain dict (empty spec -> off)
    assert gen._parse_holdout_cells("") == {}
    assert gen._parse_holdout_cells("unknown:conservative, knowledge_query:neutral") == {
        "unknown": "conservative",
        "knowledge_query": "neutral",
    }
    with pytest.raises(SystemExit):
        gen._parse_holdout_cells("unknown:sideways")


def test_holdout_cells_declared_in_the_generator(gen):
    cells = gen.MVE1_HOLDOUT_CELLS
    assert "farewell" not in cells  # 16 corpus rows cannot fill a cell
    for intent, mode in cells.items():
        assert mode in gen._MODES
        assert intent in {
            gen._intent_of(s) for s in ("joke", "hello", "why x", "calculate 2+2", "hi")
        }
    # every primitive survives the carve: each intent keeps two modes, and
    # the carve covers all three modes (breadth across the composition space)
    for intent in cells:
        remaining = [m for m in gen._MODES if m != cells[intent]]
        assert len(remaining) == 2
    assert set(cells.values()) == set(gen._MODES)


def test_correlation_is_none_when_the_block_collapsed(probe):
    # 一個只吐固定塊的模型輸出方差為 0：報告 None（不可比）而不是 0.0（可比但無關）
    assert probe._pearson([0.1] * 5, [1.0, 2.0, 3.0, 4.0, 5.0]) is None
    assert probe._pearson([1.0, 2.0, 3.0, 4.0, 5.0], [0.1] * 5) is None
    assert probe._pearson([1.0], [2.0]) is None


def test_correlation_tracks_the_input_when_the_block_varies(probe):
    assert probe._pearson([1.0, 2.0, 3.0], [2.0, 4.0, 6.0]) == 1.0
    assert probe._pearson([1.0, 2.0, 3.0], [3.0, 2.0, 1.0]) == -1.0


def test_block_body_ignores_the_answer_prefix(probe):
    # 同一個狀態塊、不同的數字前綴 → body 相同（整段 distinct 會高估多樣性）
    a = "614\n<al_out> v=0.11 a=0.42 d=0.42 fatigue=0.34 stress=0.39 health=0.86 mode=exploratory intent=unknown"
    b = "993\n<al_out> v=0.11 a=0.42 d=0.42 fatigue=0.34 stress=0.39 health=0.86 mode=exploratory intent=unknown"
    assert a.strip() != b.strip()
    assert a.split(probe._MARKER, 1)[1] == b.split(probe._MARKER, 1)[1]


def test_mutation_rewrites_one_input_field_and_nothing_else(probe):
    prompt = (
        "<al_in> v=0.26 a=0.17 d=-0.88 fatigue=0.59 stress=0.05 health=0.22 "
        "mode=neutral intent=math_query dt=0.50 | 653 + 12\n665"
    )
    mutated = probe._mutate(prompt, "v", "-0.90")
    assert "v=-0.90" in mutated
    # 其餘欄位與第二行（gold response）必須逐字不變，否則擾動就不是單一變因
    assert mutated.split("\n")[1] == prompt.split("\n")[1]
    assert prompt.replace("v=0.26", "v=-0.90") == mutated


def test_mutation_is_a_noop_when_the_value_already_matches(probe):
    prompt = "<al_in> v=0.26 dt=0.50 | 1 + 1\n2"
    # 呼叫端用「有沒有變」決定是否把該列計入分母
    assert probe._mutate(prompt, "v", "0.26") == prompt
    assert probe._mutate(prompt, "dt", "2.00") != prompt


def test_body_keeps_only_the_state_block(probe):
    assert probe._body("614\n<al_out> v=0.1 a=0.2") == "v=0.1 a=0.2"
    assert probe._body("v=0.1 a=0.2") == "v=0.1 a=0.2"


_FIELD_AXIS = (
    ("v", "valence"),
    ("a", "arousal"),
    ("d", "dominance"),
    ("fatigue", "fatigue"),
    ("stress", "stress"),
    ("health", "health"),
)


def _out_row(probe, gen, state, intent, mode, dt, seed):
    """One boundary-set-shaped row: gold is the contract operator's output."""
    target = gen._pilot_tables()[1][intent]
    out = gen.transition(state, target, dt)
    fields = " ".join(f"{key}={out[axis]:.2f}" for key, axis in _FIELD_AXIS)
    gold = f"<al_out> {fields} mode={mode} intent={intent}"
    return {
        "sample_id": f"t{seed}",
        "cell": f"{intent}:{mode}",
        "intent": intent,
        "mode": mode,
        "dt": dt,
        "state_in": dict(state, routing_mode=mode),
        "gold": gold,
        "prompt": "<al_in> placeholder",
    }


def _synthetic_rows(probe, gen, n=160):
    import random

    rng = random.Random(7)
    intents = [i for i in probe._INTENTS_ORDER if i in gen._pilot_tables()[1]]
    rows = []
    for i in range(n):
        state = {f: round(rng.uniform(lo, hi), 4) for f, (lo, hi) in gen._RANGE.items()}
        rows.append(
            _out_row(
                probe,
                gen,
                state,
                intents[i % len(intents)],
                gen._MODES[i % len(gen._MODES)],
                gen._DT_LADDER[i % len(gen._DT_LADDER)],
                i,
            )
        )
    return rows


def test_gold_correlation_reports_a_ceiling_above_zero(probe, gen):
    # 契約的 out = t + (s - t)·k 是線性的：gold 對輸入的相關必須接近 1，
    # 否則模型上的「相關 ≈ 0」會被誤讀成「改成隨機輸出也一樣」。
    rows = _synthetic_rows(probe, gen)
    corr = probe._gold_correlation(rows)
    assert set(corr) == {"v", "a", "d", "fatigue", "stress", "health"}
    assert all(v is not None and v > 0.5 for v in corr.values()), corr


def test_affine_ceiling_says_the_transition_is_learnable(probe, gen):
    ceiling = probe._affine_ceiling(_synthetic_rows(probe, gen))
    assert ceiling is not None
    assert ceiling["folds"] == 5
    assert ceiling["rungs_fitted"] == len(gen._DT_LADDER)
    # 給定 dt 的線性擬合可以幾乎逐位重現演算法，所以 0/200 是模型的讀數，
    # 不是 instrument 構造上不可能達成的門檻（門檻 5/200 = 2.5%）
    assert ceiling["dt_conditioned"]["row_exact"] > 10 * probe.GATE_EXACT_MIN / probe.GATE_N
    assert min(ceiling["dt_conditioned"]["r2"].values()) > 0.99


def test_affine_ceiling_records_that_dt_is_the_whole_task(probe, gen):
    ceiling = probe._affine_ceiling(_synthetic_rows(probe, gen))
    # dt 當作一般特徵（無交互項）時只在低 dt 附近碰巧正確，逐位幾乎全減
    assert ceiling["dt_blind"]["row_exact"] < ceiling["dt_conditioned"]["row_exact"]
    assert ceiling["dt_blind"]["row_exact"] < 0.1


def test_affine_ceiling_returns_none_without_enough_rows(probe, gen):
    assert probe._affine_ceiling(_synthetic_rows(probe, gen, n=6)) is None


_FIELDS_2DP = {
    "v": ("valence", 0.30),
    "a": ("arousal", 0.40),
    "d": ("dominance", 0.70),
    "fatigue": ("fatigue", 0.22),
    "stress": ("stress", 0.18),
    "health": ("health", 0.90),
}


def _operator_row(intent, state, dt):
    """A prompt/gold pair built with the contract's own operator, 2dp text."""
    import math

    head = " ".join(f"{k}={state[k]:.2f}" for k in _FIELDS_2DP)
    prompt = f"<al_in> {head} mode=neutral intent={intent} dt={dt:.2f} | 1 + 1"
    k = math.exp(-dt)
    out = []
    for field, (_, c) in _FIELDS_2DP.items():
        out.append(f"{field}={c + (state[field] - c) * k:.2f}")
    gold = f"<al_out> {' '.join(out)} mode=neutral intent={intent}"
    return {"prompt": prompt, "gold": gold, "dt": dt, "intent": intent}


def test_contract_form_ceiling_recovers_the_operator(probe, tmp_path):
    """The ceiling must apply the contract's own operator, not imitate a model.

    Gold here is generated by ``c + (s - c)·exp(-dt)`` with ``c`` on the 2dp
    grid, so a correct ceiling is *exactly* 1.0 on a seen intent. The earlier
    affine ceiling reported 0.50 only because it fits one map per rung across
    intents, which cannot express ``c[intent]·(1 - k)``.
    """
    import random

    rng = random.Random(3)
    train = tmp_path / "train.jsonl"
    lines = []
    for i in range(40):
        state = {f: round(rng.uniform(0.0, 1.0), 2) for f in _FIELDS_2DP}
        row = _operator_row("math_query", state, 0.5 if i % 2 else 1.0)
        lines.append(json.dumps({"input": row["prompt"], "output": row["gold"]}))
    train.write_text("\n".join(lines) + "\n", encoding="utf-8")

    rows = [
        _operator_row("math_query", {f: round(rng.uniform(0.0, 1.0), 2) for f in _FIELDS_2DP}, 2.0)
        for _ in range(20)
    ]
    ceiling = probe._contract_form_ceiling(rows, train)
    assert ceiling is not None
    assert ceiling["tau"] == 1.0
    assert ceiling["seen_intent_rows"] == 20
    assert ceiling["unseen_intent_rows"] == 0
    assert ceiling["row_exact_seen"] >= 0.4
    assert min(ceiling["field_within"].values()) >= 0.7


def test_contract_form_ceiling_counts_unseen_intents_separately(probe, tmp_path):
    """An intent absent from training is unpredictable, not merely hard.

    The gate's denominator still includes those rows, so the ceiling has to
    report both numbers — otherwise "0/200" hides that part of the set could
    never be answered by any model.
    """
    import random

    rng = random.Random(5)
    train = tmp_path / "train.jsonl"
    lines = []
    for i in range(40):
        state = {f: round(rng.uniform(0.0, 1.0), 2) for f in _FIELDS_2DP}
        row = _operator_row("unknown", state, 0.5 if i % 2 else 1.0)
        lines.append(json.dumps({"input": row["prompt"], "output": row["gold"]}))
    train.write_text("\n".join(lines) + "\n", encoding="utf-8")

    state = {f: round(rng.uniform(0.0, 1.0), 2) for f in _FIELDS_2DP}
    rows = [
        _operator_row("unknown", state, 0.5),
        _operator_row("greeting", state, 0.5),
    ]
    ceiling = probe._contract_form_ceiling(rows, train)
    assert ceiling is not None
    assert ceiling["seen_intent_rows"] == 1
    assert ceiling["unseen_intent_rows"] == 1
    # the gate's denominator includes the unpredictable row: half of it can,
    # at best, never be answered
    assert ceiling["row_exact_of_all"] == round(ceiling["row_exact_seen"] / 2, 4)
    assert ceiling["row_exact_seen"] >= 0.0


def _train_rows(tmp_path, intent, n=60, seed=3):
    """A training file of contract rows (prompt/gold) for the head tests."""
    import random

    rng = random.Random(seed)
    rows = []
    for i in range(n):
        state = {f: round(rng.uniform(0.0, 1.0), 2) for f in _FIELDS_2DP}
        rows.append(_operator_row(intent, state, (0.25, 0.5, 1.0, 2.0)[i % 4]))
    train = tmp_path / f"train_{intent}.jsonl"
    train.write_text(
        "\n".join(json.dumps({"input": r["prompt"], "output": r["gold"]}) for r in rows) + "\n",
        encoding="utf-8",
    )
    return train, [(r["prompt"], r["gold"], intent) for r in rows]


def test_operator_head_learns_nineteen_parameters(probe, tmp_path):
    """19 parameters over exact arithmetic reproduce the block the LM cannot emit.

    The head is fitted by gradient descent on training rows only, so recovering
    the constants (and tau) is learning, not transcription: the operator's form
    is fixed by the contract, its 18 constants are not in the prompt.
    """
    pytest.importorskip("torch")
    _train, pairs = _train_rows(tmp_path, "math_query")
    fitted = probe._fit_operator_head(pairs, epochs=400)
    assert fitted is not None
    assert fitted["intents"] == ["math_query"]
    assert abs(fitted["tau"] - 1.0) <= 0.25
    for field, (_, constant) in _FIELDS_2DP.items():
        learned = fitted["constants"][("math_query", field)]
        assert abs(learned - constant) <= 0.05, (field, learned, constant)

    rows = probe._contract_rows([{"prompt": pr, "gold": g} for pr, g, _i in pairs[:20]])
    scored = probe._score_contract_rows(rows, fitted["constants"], fitted["tau"])
    assert scored["row_exact_seen"] >= 0.7
    assert scored["unseen_intent_rows"] == 0


def test_operator_head_leaves_unseen_intents_unanswered(probe, tmp_path):
    """A new intent's constants are unobservable, so the head must not guess them.

    This is the 80/200 of the real instrument: no arithmetic over unseen
    constants can be exact, and the head reports those rows separately instead
    of leaking them into the seen-intent rate.
    """
    pytest.importorskip("torch")
    _train, pairs = _train_rows(tmp_path, "unknown")
    fitted = probe._fit_operator_head(pairs, epochs=200)
    assert fitted is not None
    state = {f: 0.5 for f in _FIELDS_2DP}
    rows = probe._contract_rows(
        [_operator_row("unknown", state, 0.5), _operator_row("humor", state, 0.5)]
    )
    scored = probe._score_contract_rows(rows, fitted["constants"], fitted["tau"])
    assert scored["seen_intent_rows"] == 1
    assert scored["unseen_intent_rows"] == 1
    assert scored["row_exact_of_all"] <= scored["row_exact_seen"] / 2 + 1e-9


def test_value_targets_read_the_closed_grid(probe):
    """The head's targets are grid positions, not vocabulary ids."""
    vocab = type(
        "V",
        (),
        {"stoi": {f"{i / 100:.2f}": 1000 + i for i in range(-100, 101)}},
    )()
    block = "<al_out> v=0.30 a=-0.20 d=1.00 fatigue=0.22 stress=0.18 health=0.90"
    assert probe._value_targets(vocab, block) == [130, 80, 200, 122, 118, 190]
    assert probe._value_targets(vocab, "<al_out> v=0.30 a=-0.20") is None
    # a value off the 0.01 grid is not gradable (it is not a contract value)
    assert probe._value_targets(vocab, block.replace("0.90", "0.905")) is None


def test_position_index_separates_values_from_text(probe):
    """``values_end`` must sit before the ' | ' source text, ``block_start`` after it."""

    class _Vocab:
        @staticmethod
        def encode(text):
            return list(text)

    model = type("M", (), {"vocab": _Vocab})()
    prompt = "<al_in> v=0.30 | 653 + 12"
    assert probe._position_index(model, prompt, start=40, position="values_end", width=80) == 14
    assert probe._position_index(model, prompt, start=40, position="block_start", width=80) == 40
    assert probe._position_index(model, prompt, start=40, position="block_start", width=10) == 9


class TestContractTableAndCeiling:
    """§二十三: the unseen-intent rows, and the number they must be read against."""

    @staticmethod
    def _row(intent: str, state: Dict[str, float], gold: Dict[str, float], dt: float) -> dict:
        return {
            "intent": intent,
            "state": {**state, "dt": dt},
            "gold": dict(gold),
            "dt": dt,
        }

    def _targets(self) -> Dict[str, Dict[str, float]]:
        return {
            "seen": {
                "valence": 0.3,
                "arousal": 0.4,
                "dominance": 0.7,
                "fatigue": 0.2,
                "stress": 0.2,
                "health": 0.9,
            },
            "fresh": {
                "valence": 0.7,
                "arousal": 0.6,
                "dominance": 0.5,
                "fatigue": 0.15,
                "stress": 0.05,
                "health": 0.95,
            },
        }

    def _constants(self, probe, targets) -> Dict[tuple, float]:
        return {
            (name, f): targets[name][probe._FIELD_LONG[f]]
            for name in ("seen",)
            for f in probe._FIELD_KEYS
        }

    def test_unseen_intents_are_graded_when_the_table_is_given(self, probe):
        """An intent the training file never saw is answerable from the contract table."""
        targets = self._targets()
        constants = self._constants(probe, targets)
        state = {
            "v": 0.5,
            "a": 0.5,
            "d": 0.5,
            "fatigue": 0.5,
            "stress": 0.5,
            "health": 0.5,
        }
        k = math.exp(-2.0)
        gold = {
            f: round(
                targets["fresh"][probe._FIELD_LONG[f]]
                + (0.5 - targets["fresh"][probe._FIELD_LONG[f]]) * k,
                2,
            )
            for f in probe._FIELD_KEYS
        }
        row = self._row("fresh", state, gold, dt=2.0)
        without = probe._score_contract_rows([row], constants, 1.0)
        with_table = probe._score_contract_rows([row], constants, 1.0, targets=targets)
        assert without["unseen_intent_rows"] == 1 and without["row_exact_all_intents"] == 0.0
        assert with_table["unseen_intent_rows"] == 1
        assert with_table["row_exact_all_intents"] == 1.0
        assert with_table["row_exact_of_all"] == 0.0  # learned-only reading is unchanged

    def test_exact_counts_can_never_exceed_rows(self, probe):
        """Regression: the first version summed seen *rows* with unseen hits."""
        targets = self._targets()
        constants = self._constants(probe, targets)
        state = {
            "v": 0.5,
            "a": 0.5,
            "d": 0.5,
            "fatigue": 0.5,
            "stress": 0.5,
            "health": 0.5,
        }
        rows = [
            self._row(
                "seen",
                state,
                {f: targets["seen"][probe._FIELD_LONG[f]] for f in probe._FIELD_KEYS},
                dt=2.0,
            ),
            self._row(
                "fresh",
                state,
                {f: targets["fresh"][probe._FIELD_LONG[f]] for f in probe._FIELD_KEYS},
                dt=2.0,
            ),
        ]
        scored = probe._score_contract_rows(rows, constants, 1.0, targets=targets)
        assert 0.0 <= scored["row_exact_all_intents"] <= 1.0
        assert scored["row_exact_all_intents"] * scored["rows"] <= scored["rows"]

    def test_structural_ceiling_is_harder_at_short_dt(self, probe):
        """2dp input vs a 0.005 grid: error ~ 0.005*exp(-dt/tau) cares about dt."""
        targets = self._targets()
        base = targets["seen"]
        state = {
            "v": 0.505,
            "a": 0.505,
            "d": 0.505,
            "fatigue": 0.505,
            "stress": 0.505,
            "health": 0.505,
        }

        # gold computed from the *unrounded* 4dp state, printed at 2dp
        def gold(dt):
            k = math.exp(-dt / 1.0)
            return {
                f: round(base[probe._FIELD_LONG[f]] + (0.5 - base[probe._FIELD_LONG[f]]) * k, 2)
                for f in probe._FIELD_KEYS
            }

        rows = [
            self._row("seen", state, gold(0.25), 0.25),
            self._row("seen", state, gold(2.0), 2.0),
        ]
        ceiling = probe._structural_ceiling(rows, targets, base, 1.0)
        assert ceiling["by_dt"]["0.25"]["exact"] <= ceiling["by_dt"]["2.0"]["exact"]
        assert ceiling["exact"] <= ceiling["rows"]
        assert 0.0 <= ceiling["row_exact"] <= 1.0
        assert "2dp" in ceiling["reason"]

    def test_ceiling_gives_up_only_on_rounding_not_on_targets(self, probe):
        """With the exact state (no print error) every row must be exact."""
        targets = self._targets()
        base = targets["seen"]
        state = {f: 0.17 for f in probe._FIELD_KEYS}
        k = math.exp(-0.5)
        gold = {
            f: base[probe._FIELD_LONG[f]] + (0.17 - base[probe._FIELD_LONG[f]]) * k
            for f in probe._FIELD_KEYS
        }
        row = self._row("seen", state, gold, 0.5)
        # gold printed at full precision -> the operator reproduces it exactly
        ceiling = probe._structural_ceiling([row], targets, base, 1.0)
        assert ceiling["exact"] == 1
        assert ceiling["max_abs_error_median"] < 1e-9

    def test_rounding_aware_reading_separates_print_error_from_model_error(self, probe):
        """0.0055 off at dt=2 is inside printing noise but outside the bare grid."""
        targets = self._targets()
        constants = self._constants(probe, targets)
        state = {f: 0.5 for f in probe._FIELD_KEYS}
        k = math.exp(-2.0)  # aware tolerance = 0.005 * (1 + k) ~ 0.00568
        pred = {
            f: constants[("seen", f)] + (0.5 - constants[("seen", f)]) * k
            for f in probe._FIELD_KEYS
        }
        gold = {f: pred[f] - 0.0055 for f in probe._FIELD_KEYS}
        row = self._row("seen", state, gold, dt=2.0)
        scored = probe._score_contract_rows([row], constants, 1.0)
        assert scored["row_exact_seen"] == 0.0
        assert scored["row_exact_all_intents_rounding_aware"] == 1.0
        # the allowed slack grows with k, so short dt is held to a tighter bound
        tight = probe._score_contract_rows(
            [self._row("seen", state, gold, dt=0.25)], constants, 1.0
        )
        assert tight["row_exact_all_intents_rounding_aware"] == 0.0
