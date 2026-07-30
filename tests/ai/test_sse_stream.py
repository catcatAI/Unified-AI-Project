"""
ANGELA-MATRIX: [L3-L4] [γδ] [B] [L2]
Tests for SSE streaming — event format + generator behavior.
"""

import json


async def _collect(gen):
    """Collect all items from an async generator into a list."""
    results = []
    async for item in gen:
        results.append(item)
    return results


class TestSSEHelpers:
    """Test the SSE helper functions directly."""

    async def test_sse_events_format(self):
        from api.routes.chat_routes import _sse_events
        events = [{"type": "test", "content": "hello"}, {"type": "done"}]
        output = await _collect(_sse_events(events))
        assert len(output) == 2
        for i, line in enumerate(output):
            assert line.startswith("data: ")
            parsed = json.loads(line[6:])
            assert parsed["type"] == events[i]["type"]

    async def test_sse_events_empty(self):
        from api.routes.chat_routes import _sse_events
        output = await _collect(_sse_events([]))
        assert len(output) == 0

    async def test_sse_events_double_newline(self):
        from api.routes.chat_routes import _sse_events
        output = await _collect(_sse_events([{"type": "ping"}]))
        assert output[0].endswith("\n\n")


class TestStreamDocEvents:
    """Test the document streaming generator (with mock pipeline)."""

    async def test_stream_yields_done_event(self):
        from api.routes.chat_routes import _stream_doc_events
        gen = _stream_doc_events("hello", None, None)
        output = await _collect(gen)
        assert len(output) >= 1
        last = json.loads(output[-1][6:])
        assert last["type"] == "control"
        assert last["content"] == "[DONE]"
