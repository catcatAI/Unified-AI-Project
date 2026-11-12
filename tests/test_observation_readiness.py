# -*- coding: utf-8 -*-
"""observation_readiness.py — P5 says "insufficient sample", and this proves it.

The pre-registered stop condition (HIERARCHICAL_PLAN_FILL_GENERATION.md §6.1)
is per cell: input length bucket × topic bucket, 200 turns each, and no state
field may be 100% unobserved. These tests pin the arithmetic — in particular
that the reader never drops legacy or unstratifiable records to make the corpus
look ready.
"""

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = REPO_ROOT / "scripts" / "observation_readiness.py"

STATE_FIELDS = ("health", "emotion")


def load_tool():
    spec = importlib.util.spec_from_file_location("observation_readiness", TOOL_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


tool = load_tool()


def _record(*, length="5-8", topic="math", state=None, version=2):
    return {
        "v": version,
        "turn_id": f"t-{id(object())}",
        "session": "s",
        "day": "2026-11-12",
        "state": {"health": 0.5, "emotion": None} if state is None else state,
        "user_move": "question",
        "source": "computed",
        "in_len": 3,
        "in_len_bucket": length,
        "topic": topic,
        "out_len": 3,
        "out_len_bucket": "2-4",
        "skeleton": {},
        "skeleton_sig": "abc123",
        "consent": 1,
    }


def test_no_records_is_insufficient_not_zero_signal():
    summary = tool.summarize([], state_fields=STATE_FIELDS)
    assert summary["total_turns"] == 0
    assert summary["ready"] is False
    assert summary["verdict"] == "insufficient sample"
    assert "no observations recorded yet" in summary["reasons"]


def test_a_full_cell_becomes_ready_but_an_uncovered_state_field_does_not():
    records = [_record() for _ in range(200)]
    summary = tool.summarize(records, state_fields=STATE_FIELDS)
    # emotion is null in every record: a big corpus with one dead field is not ready
    assert summary["uncovered_state_fields"] == ["emotion"]
    assert summary["ready"] is False

    healthy = [_record(state={"health": 0.5, "emotion": 0.2}) for _ in range(200)]
    summary = tool.summarize(healthy, state_fields=STATE_FIELDS)
    assert summary["ready"] is True
    assert summary["deficits"] == []


def test_a_constant_state_field_is_reported_but_does_not_decide_readiness():
    records = [_record(state={"health": 0.5, "emotion": 0.2}) for _ in range(200)]
    summary = tool.summarize(records, state_fields=STATE_FIELDS)
    assert summary["constant_state_fields"] == ["health", "emotion"]
    assert summary["ready"] is True  # §6.1 lists no constant-field stop condition

    varied = [_record(state={"health": 0.5 if i % 2 else 0.4, "emotion": 0.2}) for i in range(200)]
    summary = tool.summarize(varied, state_fields=STATE_FIELDS)
    assert summary["constant_state_fields"] == ["emotion"]
    assert summary["state_distinct"]["health"] == 2


def test_one_turn_short_of_the_bar_is_still_insufficient():
    summary = tool.summarize([_record() for _ in range(199)], state_fields=("health",))
    assert summary["deficits"] == [
        {"in_len_bucket": "5-8", "topic": "math", "turns": 199, "missing": 1}
    ]
    assert summary["verdict"] == "insufficient sample"


def test_each_cell_is_counted_separately():
    records = [_record() for _ in range(200)] + [_record(topic="knowledge") for _ in range(200)]
    summary = tool.summarize(records, state_fields=("health",))
    assert summary["cell_count"] == 2
    assert {row["turns"] for row in summary["strata"]} == {200}


def test_legacy_records_are_counted_as_unstratifiable():
    legacy = _record(version=1)
    for field in ("in_len", "in_len_bucket", "topic"):
        legacy.pop(field)
    summary = tool.summarize([legacy], state_fields=("health",))
    assert summary["legacy_unstratifiable"] == 1
    assert summary["strata"] == []
    assert any("predate schema" in reason for reason in summary["reasons"])


def test_reader_reports_unexpected_keys_instead_of_ignoring_them(tmp_path):
    target = tmp_path / "turns-2026-11-12.jsonl"
    record = _record()
    record["response_text"] = "this must never be in the log"
    target.write_text(json.dumps(record) + "\n", encoding="utf-8")

    records, problems = tool.load_records(tmp_path)
    assert len(records) == 1
    assert any("unexpected key(s) response_text" in problem for problem in problems)


def test_reader_reports_malformed_lines(tmp_path):
    target = tmp_path / "turns-2026-11-12.jsonl"
    target.write_text("{not json}\n", encoding="utf-8")
    records, problems = tool.load_records(tmp_path)
    assert records == []
    assert any("unparsable" in problem for problem in problems)


def test_main_prints_insufficient_and_exits_nonzero(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["observation_readiness.py", "--dir", str(tmp_path)])
    assert tool.main() == 1
    captured = capsys.readouterr().out
    assert "INSUFFICIENT SAMPLE" in captured
    assert "do not run P5" in captured


def test_main_writes_the_summary_json_without_touching_the_corpus(tmp_path, monkeypatch):
    record = _record(state={"health": 0.5, "emotion": 0.2})
    (tmp_path / "turns-2026-11-12.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
    report = tmp_path / "out" / "readiness.json"
    before = (tmp_path / "turns-2026-11-12.jsonl").read_text(encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        ["observation_readiness.py", "--dir", str(tmp_path), "--json", str(report)],
    )
    assert tool.main() == 1
    summary = json.loads(report.read_text(encoding="utf-8"))
    assert summary["total_turns"] == 1
    assert summary["verdict"] == "insufficient sample"
    assert (tmp_path / "turns-2026-11-12.jsonl").read_text(encoding="utf-8") == before
