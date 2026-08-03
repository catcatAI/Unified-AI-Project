"""Session memory tests: chat pipeline persists user/assistant turns to session history.

Verifies the multi-turn memory chain:
  1. _handle_chat_request delegates to _run_chat_pipeline.
  2. Every response path (normal, math, gate, agent, timeout) persists the turn.
  3. The session's "messages" list is the source for /session/{id}/send history.
  4. History passed into the pipeline falls back to persisted session messages.
"""
import pytest

import api.routes.chat_routes as cr
from api.routes.chat_routes import (
    _handle_chat_request,
    _run_chat_pipeline,
    sessions,
)


@pytest.fixture(autouse=True)
def _clean_sessions():
    """Reset the module-level session store between tests."""
    sessions._sessions.clear()
    yield
    sessions._sessions.clear()


@pytest.mark.asyncio
async def test_pipeline_persists_turn_to_session_memory(monkeypatch):
    """A normal pipeline response must be written back to session messages."""

    async def fake_pipeline(*args, **kwargs):
        return {
            "response_text": "Hello from pipeline",
            "response": "Hello from pipeline",
            "source": "angela_chat_service",
            "schema_version": "2.0",
            "truncation_message": "",
            "emotion": "calm",
            "emotion_confidence": 0.6,
            "emotion_intensity": 0.4,
            "session_id": "sess-memory-test-1",
        }

    monkeypatch.setattr("api.routes.chat_routes._run_chat_pipeline", fake_pipeline)

    result = await _handle_chat_request(
        "How are you?",
        "Tester",
        history=[],
        session_id="sess-memory-test-1",
    )

    assert result["response_text"] == "Hello from pipeline"

    session = sessions.get("sess-memory-test-1")
    assert session is not None
    messages = session.get("messages", [])
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "How are you?"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Hello from pipeline"
    assert all("timestamp" in m for m in messages)


@pytest.mark.asyncio
async def test_early_return_paths_also_persist(monkeypatch):
    """Math/gate/agent/timeout early returns must still be recorded."""

    early_responses = [
        {
            "response_text": "math result",
            "response": "math result",
            "source": "math",
            "schema_version": "2.0",
            "session_id": "sess-memory-test-2",
        },
        {
            "response_text": "gate blocked",
            "response": "gate blocked",
            "source": "execution-gate",
            "schema_version": "2.0",
            "session_id": "sess-memory-test-2",
        },
        {
            "response_text": "agent routed",
            "response": "agent routed",
            "source": "agent",
            "schema_version": "2.0",
            "session_id": "sess-memory-test-2",
        },
        {
            "response_text": "timeout fallback",
            "response": "timeout fallback",
            "source": "fallback-timeout",
            "schema_version": "2.0",
            "session_id": "sess-memory-test-2",
        },
    ]

    for expected in early_responses:
        sessions._sessions.clear()

        async def fake_pipeline(*args, expected=expected, **kwargs):
            return expected

        monkeypatch.setattr("api.routes.chat_routes._run_chat_pipeline", fake_pipeline)

        await _handle_chat_request(
            "some message",
            "Tester",
            history=[],
            session_id="sess-memory-test-2",
        )

        session = sessions.get("sess-memory-test-2")
        assert session is not None
        messages = session.get("messages", [])
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == expected["response_text"]


@pytest.mark.asyncio
async def test_exception_still_persists_partial_turn(monkeypatch):
    """Even when the pipeline raises, the turn should be persisted via _latest_response."""

    # Set the module-level captured response via the module attribute so the
    # wrapper's fallback path reads it (from-import would shadow it locally).
    cr._latest_response = {
        "response_text": "partial response before crash",
        "response": "partial response before crash",
        "source": "angela_chat_service",
        "schema_version": "2.0",
        "session_id": "sess-memory-test-3",
    }

    async def fake_pipeline(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("api.routes.chat_routes._run_chat_pipeline", fake_pipeline)

    with pytest.raises(RuntimeError):
        await _handle_chat_request(
            "trigger crash",
            "Tester",
            history=[],
            session_id="sess-memory-test-3",
        )

    session = sessions.get("sess-memory-test-3")
    assert session is not None
    messages = session.get("messages", [])
    assert len(messages) == 2
    assert messages[1]["content"] == "partial response before crash"


@pytest.mark.asyncio
async def test_history_falls_back_to_session_messages(monkeypatch):
    """When the caller passes no history, persisted session messages are used."""
    sessions.set(
        "sess-memory-test-4",
        {
            "created_at": "2026-08-03T00:00:00",
            "origin": "Human",
            "user_name": "Tester",
            "messages": [
                {"role": "user", "content": "earlier turn", "timestamp": "t1"},
                {"role": "assistant", "content": "earlier answer", "timestamp": "t2"},
            ],
        },
    )

    captured = {}

    async def fake_pipeline(*args, **kwargs):
        captured["history"] = kwargs.get("history") or args[2]
        return {
            "response_text": "OK",
            "response": "OK",
            "source": "test",
            "schema_version": "2.0",
            "session_id": "sess-memory-test-4",
        }

    monkeypatch.setattr("api.routes.chat_routes._run_chat_pipeline", fake_pipeline)

    await _handle_chat_request(
        "new turn",
        "Tester",
        history=[],
        session_id="sess-memory-test-4",
    )

    assert len(captured["history"]) == 2, f"captured={captured}"
    assert captured["history"][0]["content"] == "earlier turn"
    assert captured["history"][1]["content"] == "earlier answer"


@pytest.mark.asyncio
async def test_history_bounded_to_80_messages(monkeypatch):
    """Session history is capped so unbounded growth is impossible."""
    sessions.set(
        "sess-memory-test-5",
        {
            "created_at": "2026-08-03T00:00:00",
            "origin": "Human",
            "user_name": "Tester",
            "messages": [
                {"role": "user", "content": f"old-{i}", "timestamp": "t"}
                for i in range(100)
            ],
        },
    )

    async def fake_pipeline(*args, **kwargs):
        return {
            "response_text": "bounded",
            "response": "bounded",
            "source": "test",
            "schema_version": "2.0",
            "session_id": "sess-memory-test-5",
        }

    monkeypatch.setattr("api.routes.chat_routes._run_chat_pipeline", fake_pipeline)

    await _handle_chat_request(
        "latest",
        "Tester",
        history=[],
        session_id="sess-memory-test-5",
    )

    session = sessions.get("sess-memory-test-5")
    assert len(session["messages"]) <= 80
    assert session["messages"][-1]["content"] == "bounded"
    assert session["messages"][-2]["role"] == "user"
    assert session["messages"][-2]["content"] == "latest"


# =============================================================================
# Truncation marker tests
# =============================================================================

class TestTruncationMarker:
    def test_format_chat_response_shows_marker_when_truncated(self):
        """The truncation marker is present only when the input was truncated."""
        from api.routes.chat_routes import _format_chat_response

        resp = _format_chat_response(
            "hello", None, None, "2.0", "TRUNC", "short msg", 4000, "sess-trunc-1"
        )
        assert resp["truncation_message"] == ""

        resp = _format_chat_response(
            "hello",
            None,
            None,
            "2.0",
            "TRUNC",
            "short msg",
            4000,
            "sess-trunc-1",
            was_truncated=True,
        )
        assert resp["truncation_message"] == "TRUNC"

    @pytest.mark.asyncio
    async def test_pipeline_truncation_flag_flows_to_response(self, monkeypatch):
        """A long input is truncated and the marker surfaces in the response."""
        captured = {}

        async def fake_pipeline(*args, **kwargs):
            # Emulate the real pipeline: truncate via the same helper and
            # format the response with the truncation flag.
            from api.routes.chat_routes import (
                _format_chat_response,
                _validate_and_truncate_input,
            )

            chat_cfg = {"max_message_length": 4000, "truncation_length": 1000}
            raw = args[0]
            user_message = _validate_and_truncate_input(raw, chat_cfg)
            was_truncated = len(raw) > 4000
            captured["was_truncated"] = was_truncated
            return _format_chat_response(
                "ok",
                None,
                None,
                "2.0",
                "TRUNC",
                user_message,
                4000,
                "sess-trunc-2",
                was_truncated=was_truncated,
            )

        monkeypatch.setattr("api.routes.chat_routes._run_chat_pipeline", fake_pipeline)

        result = await _handle_chat_request(
            "x" * 5000,
            "Tester",
            history=[],
            session_id="sess-trunc-2",
        )
        assert result["truncation_message"] == "TRUNC"
        assert captured["was_truncated"] is True

        result = await _handle_chat_request(
            "normal short input",
            "Tester",
            history=[],
            session_id="sess-trunc-3",
        )
        assert result["truncation_message"] == ""
        assert captured["was_truncated"] is False

    def test_validate_and_truncate_returns_clamped_message(self):
        """The input validator clamps oversized input to truncation_length."""
        from api.routes.chat_routes import _validate_and_truncate_input

        cfg = {"max_message_length": 4000, "truncation_length": 1000}
        msg = _validate_and_truncate_input("y" * 5000, cfg)
        assert len(msg) == 1000

        msg = _validate_and_truncate_input("fine", cfg)
        assert msg == "fine"



@pytest.mark.asyncio
async def test_run_chat_pipeline_exists():
    """The pipeline function exists and is async."""
    import inspect

    assert inspect.iscoroutinefunction(_run_chat_pipeline)
