# ANGELA-MATRIX: [L3] [β] [B] [L2]
"""StreamJudgeWindow: rolling judgments lock only on agreement; consistency check."""

from services.llm.stream_judge import StreamJudgeWindow


def test_no_lock_before_k_agreements():
    w = StreamJudgeWindow(judge_every_tokens=1, lock_k=2)
    assert w.feed("12 * 12 = ") is None
    assert w.locked_type is None
    event = w.feed("195")
    assert w.locked_type is not None
    assert event == {"judge": "locked", "type": w.locked_type}


def test_empty_stream_never_locks():
    w = StreamJudgeWindow(judge_every_tokens=1, lock_k=2)
    assert w.feed("") is None
    assert w.feed("") is None
    assert w.locked_type is None
    assert w.finalize("")["consistent"] is False


def test_finalize_consistency_on_stable_text():
    w = StreamJudgeWindow(judge_every_tokens=2, lock_k=2)
    text = "12 * 12 = 195"
    for ch in text:
        w.feed(ch)
    report = w.finalize(text)
    assert report["full"] == "math"
    assert report["tokens"] == len(text)
    # Stable math text must converge, not flip.
    assert report["consistent"] is True


def test_greeting_stream_converges():
    w = StreamJudgeWindow(judge_every_tokens=2, lock_k=2)
    text = "你好呀！见到你真开心~"
    for ch in text:
        w.feed(ch)
    report = w.finalize(text)
    assert report["full"] == "greeting"
    assert report["consistent"] is True
