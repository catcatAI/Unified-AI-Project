"""
Tests for session-based temporal buffer in _fire_causal_learning.

Verifies that per-session buffers accumulate across multiple calls,
enabling Granger causality (>= 5 samples) to fire.
"""
# =============================================================================
# ANGELA-MATRIX: L3 β A L4
# =============================================================================

from unittest.mock import MagicMock, patch

from api.routes.chat_routes import _CAUSAL_BUFFERS, _get_causal_buffer


def _reset_buffers() -> None:
    """Clear the module-level buffer dict between tests."""
    _CAUSAL_BUFFERS.clear()


def test_get_causal_buffer_creates_new():
    _reset_buffers()
    buf = _get_causal_buffer("session_A")
    assert "msg_lengths" in buf
    assert "resp_lengths" in buf
    assert "engagement_ratios" in buf
    assert buf["msg_lengths"] == []


def test_get_causal_buffer_reuses_existing():
    _reset_buffers()
    buf1 = _get_causal_buffer("session_X")
    buf1["msg_lengths"].append(10.0)
    buf2 = _get_causal_buffer("session_X")
    assert buf2["msg_lengths"] == [10.0]
    assert buf1 is buf2


def test_get_causal_buffer_separate_sessions():
    _reset_buffers()
    buf_a = _get_causal_buffer("session_A")
    buf_b = _get_causal_buffer("session_B")
    buf_a["msg_lengths"].append(5.0)
    assert buf_b["msg_lengths"] == []


@patch("api.routes.chat_routes.get_causal_reasoning")
def test_fire_causal_learning_single_call(mock_get_causal):
    _reset_buffers()
    mock_causal = MagicMock()
    mock_get_causal.return_value = mock_causal

    from api.routes.chat_routes import _fire_causal_learning

    _fire_causal_learning("Hello back!", "Hi", "session_1")

    mock_causal.learn.assert_called_once()
    call_data = mock_causal.learn.call_args[0][0]
    assert call_data["variables"] == ["user_input", "angela_response"]
    # Single call -> single-element lists
    assert len(call_data["data"]["user_input"]) == 1
    assert call_data["relationships"][0]["source"] == "chat_session_1"
    strength = call_data["relationships"][0]["strength"]
    assert 0.1 <= strength <= 0.9


@patch("api.routes.chat_routes.get_causal_reasoning")
def test_fire_causal_learning_accumulates(mock_get_causal):
    _reset_buffers()
    mock_causal = MagicMock()
    mock_get_causal.return_value = mock_causal

    from api.routes.chat_routes import _fire_causal_learning

    # Simulate 6 interactions in the same session
    for i in range(6):
        _fire_causal_learning("response " * (i + 1), "query " * (i + 1), "session_acc")

    # After >= 5 calls, the 6th should pass accumulated lists
    assert mock_causal.learn.call_count == 6
    sixth_call = mock_causal.learn.call_args_list[5][0][0]
    assert len(sixth_call["data"]["user_input"]) == 6
    assert len(sixth_call["data"]["angela_response"]) == 6


@patch("api.routes.chat_routes.get_causal_reasoning")
def test_fire_causal_learning_skips_when_no_response(mock_get_causal):
    _reset_buffers()
    mock_causal = MagicMock()
    mock_get_causal.return_value = mock_causal

    from api.routes.chat_routes import _fire_causal_learning

    _fire_causal_learning("", "some query", "session_empty")
    mock_causal.learn.assert_not_called()


@patch("api.routes.chat_routes.get_causal_reasoning")
def test_fire_causal_learning_caps_buffer(mock_get_causal):
    _reset_buffers()
    mock_causal = MagicMock()
    mock_get_causal.return_value = mock_causal

    from api.routes.chat_routes import _fire_causal_learning

    # Exceed 100 entries (trigger cap at 100 -> trim to last 50)
    for i in range(110):
        _fire_causal_learning(f"resp_{i}", f"msg_{i}", "session_cap")

    assert mock_causal.learn.call_count == 110
    buf = _CAUSAL_BUFFERS["session_cap"]
    assert len(buf["msg_lengths"]) <= 100


@patch("api.routes.chat_routes.get_causal_reasoning")
def test_dynamic_strength_scales_with_engagement(mock_get_causal):
    _reset_buffers()
    mock_causal = MagicMock()
    mock_get_causal.return_value = mock_causal

    from api.routes.chat_routes import _fire_causal_learning

    # Short query, long response = high engagement -> high strength
    _fire_causal_learning("A" * 100, "B", "session_str")
    high_call = mock_causal.learn.call_args[0][0]
    high_strength = high_call["relationships"][0]["strength"]

    _reset_buffers()

    # Long query, short response = low engagement -> low strength
    _fire_causal_learning("B", "A" * 100, "session_str2")
    low_call = mock_causal.learn.call_args[0][0]
    low_strength = low_call["relationships"][0]["strength"]

    assert high_strength > low_strength


# ── TemporalState bridge tests (C³ 4.0: ingest_temporal_state) ──────────


def _reset_all():
    """Clear module-level buffers AND reset temporal state."""
    _CAUSAL_BUFFERS.clear()
    from api.routes.chat_routes import _get_causal_temporal_state
    ts = _get_causal_temporal_state()
    ts.clear()


def test_get_causal_temporal_state_creates_ts():
    _reset_all()
    from api.routes.chat_routes import _get_causal_temporal_state
    ts = _get_causal_temporal_state()
    from core.state.temporal import TemporalState
    assert isinstance(ts, TemporalState)
    assert ts.max_size == 200


def test_get_causal_temporal_state_is_singleton():
    _reset_all()
    from api.routes.chat_routes import _get_causal_temporal_state
    ts1 = _get_causal_temporal_state()
    ts2 = _get_causal_temporal_state()
    assert ts1 is ts2


@patch("api.routes.chat_routes.get_causal_reasoning")
def test_fire_causal_learning_records_temporal_snapshot(mock_get_causal):
    _reset_all()
    mock_causal = MagicMock()
    mock_get_causal.return_value = mock_causal

    from api.routes.chat_routes import _fire_causal_learning, _get_causal_temporal_state
    ts = _get_causal_temporal_state()
    assert ts.size() == 0

    _fire_causal_learning("Hello back!", "Hi", "session_ts_1")
    assert ts.size() == 1

    snapshot = ts.get_at(-1)
    assert "interaction" in snapshot
    assert "msg_length" in snapshot["interaction"]
    assert "resp_length" in snapshot["interaction"]


@patch("api.routes.chat_routes.get_causal_reasoning")
def test_ingest_temporal_state_called_after_5_interactions(mock_get_causal):
    _reset_all()
    mock_causal = MagicMock()
    # Wire the ingest_temporal_state as a mock method
    mock_causal.ingest_temporal_state = MagicMock()
    mock_get_causal.return_value = mock_causal

    from api.routes.chat_routes import _fire_causal_learning

    # 4 interactions -> ingest_temporal_state not called yet
    for i in range(4):
        _fire_causal_learning(f"resp_{i}", f"msg_{i}", "session_ts_2")
    assert mock_causal.ingest_temporal_state.call_count == 0

    # 5th interaction -> triggers ingest_temporal_state
    _fire_causal_learning("resp_5", "msg_5", "session_ts_2")
    assert mock_causal.ingest_temporal_state.call_count == 1

    # 10th interaction -> triggers again (5 more)
    for i in range(5):
        _fire_causal_learning(f"resp_{i}", f"msg_{i}", "session_ts_2")
    assert mock_causal.ingest_temporal_state.call_count == 2


@patch("api.routes.chat_routes.get_causal_reasoning")
def test_ingest_temporal_state_includes_window_param(mock_get_causal):
    _reset_all()
    mock_causal = MagicMock()
    mock_causal.ingest_temporal_state = MagicMock()
    mock_get_causal.return_value = mock_causal

    from api.routes.chat_routes import _fire_causal_learning

    for i in range(5):
        _fire_causal_learning(f"resp_{i}", f"msg_{i}", "session_ts_3")

    call_args = mock_causal.ingest_temporal_state.call_args
    assert call_args is not None
    assert call_args[1].get("window") == 20
