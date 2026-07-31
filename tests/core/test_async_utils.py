"""Tests for utils.async_utils — safe task creation + concurrency-limited gather."""
import asyncio

import pytest

from utils.async_utils import gather_with_concurrency, safe_create_task


@pytest.mark.asyncio
async def test_gather_with_concurrency_returns_all_results():
    async def identity(x):
        await asyncio.sleep(0)
        return x

    results = await gather_with_concurrency(3, identity(1), identity(2), identity(3))
    assert sorted(results) == [1, 2, 3]


@pytest.mark.asyncio
async def test_gather_with_concurrency_limits_concurrency():
    active = 0
    peak = 0
    lock = asyncio.Lock()

    async def worker():
        nonlocal active, peak
        async with lock:
            active += 1
            peak = max(peak, active)
        await asyncio.sleep(0.05)
        async with lock:
            active -= 1

    await gather_with_concurrency(2, *[worker() for _ in range(6)])
    assert peak <= 2


@pytest.mark.asyncio
async def test_gather_with_concurrency_propagates_exceptions():
    async def boom():
        raise ValueError("boom")

    with pytest.raises(ValueError):
        await gather_with_concurrency(2, boom())


@pytest.mark.asyncio
async def test_safe_create_task_tracks_background_tasks():
    async def noop():
        return 42

    task = safe_create_task(noop(), name="test_noop")
    assert task is not None
    result = await asyncio.wait_for(task, timeout=5)
    assert result == 42


@pytest.mark.asyncio
async def test_safe_create_task_handles_exception():
    async def fails():
        raise RuntimeError("expected")

    task = safe_create_task(fails(), name="test_fail")
    with pytest.raises(RuntimeError):
        await asyncio.wait_for(task, timeout=5)
