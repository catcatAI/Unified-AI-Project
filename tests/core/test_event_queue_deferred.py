"""Regression tests for EventQueue.dequeue() deferred-head handling.

Previously, when the queue head was a deferred event, dequeue() re-pushed it
with the SAME (priority, sequence) key and continued — the next heappop
returned the same event, producing an infinite busy loop that held the lock
at 100% CPU. The fix bumps the sequence on re-queue and stops scanning when
the same event is seen twice in one call.
"""

import asyncio
from datetime import datetime, timedelta

import pytest

from core.event_loop_system import Event, EventPriority, EventQueue


def _make_event(event_id: str, deferred_until=None) -> Event:
    return Event(
        event_id=event_id,
        event_type="test",
        priority=EventPriority.NORMAL,
        data={},
        timestamp=datetime.now(),
        source="test",
        deferred_until=deferred_until,
    )


@pytest.mark.asyncio
async def test_deferred_head_returns_none_without_spinning():
    """A queue whose head is deferred must return None promptly (no spin)."""
    q = EventQueue()
    ev = _make_event("deferred", deferred_until=datetime.now() + timedelta(hours=1))
    q._queue = [(ev.priority.level, 1, ev)]
    q._event_map["deferred"] = ev

    # timeout guards against an infinite busy loop
    got = await asyncio.wait_for(q.dequeue(), timeout=2.0)
    assert got is None
    assert len(q._queue) == 1  # deferred event stays queued


@pytest.mark.asyncio
async def test_ready_event_dequeued_behind_deferred_head():
    """A non-deferred event must still be dequeued when a deferred one is ahead."""
    q = EventQueue()
    ev = _make_event("deferred", deferred_until=datetime.now() + timedelta(hours=1))
    q._queue = [(ev.priority.level, 1, ev)]
    q._event_map["deferred"] = ev
    await q.dequeue()

    ev2 = _make_event("ready")
    q._queue.append((ev2.priority.level, 2, ev2))
    got = await asyncio.wait_for(q.dequeue(), timeout=2.0)
    assert got is not None
    assert got.event_id == "ready"


@pytest.mark.asyncio
async def test_deferred_event_served_after_defer_elapses():
    """A deferred event is delivered once its deferred_until passes."""
    q = EventQueue()
    ev = _make_event("deferred", deferred_until=datetime.now() - timedelta(seconds=1))
    q._queue = [(ev.priority.level, 1, ev)]
    q._event_map["deferred"] = ev

    got = await asyncio.wait_for(q.dequeue(), timeout=2.0)
    assert got is not None
    assert got.event_id == "deferred"
