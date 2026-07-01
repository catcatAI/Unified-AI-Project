"""Tests for GlobalSystemClock — unified time base."""
import asyncio
import pytest

from core.clock.global_system_clock import GlobalSystemClock


@pytest.fixture
def clock():
    c = GlobalSystemClock()
    yield c


@pytest.mark.asyncio
async def test_clock_properties(clock):
    assert clock.tick_rate_hz == 10.0
    assert clock.tick_count == 0
    assert not clock.is_running
    assert clock.elapsed_seconds == 0.0


@pytest.mark.asyncio
async def test_clock_start_stop(clock):
    await clock.start()
    assert clock.is_running
    assert clock.tick_count >= 0
    await clock.stop()
    assert not clock.is_running


@pytest.mark.asyncio
async def test_clock_real_ticks(clock):
    await clock.start()
    await asyncio.sleep(0.15)
    await clock.stop()
    assert clock.tick_count >= 1


@pytest.mark.asyncio
async def test_clock_now(clock):
    t1 = clock.now()
    await asyncio.sleep(0.01)
    t2 = clock.now()
    assert t2 > t1


@pytest.mark.asyncio
async def test_clock_subscribe_multi_interval(clock):
    """Use force_tick to test subscription interval logic deterministically."""
    results = []
    async def cb(tick):
        results.append(tick)
    clock.subscribe(3, cb)
    for _ in range(10):
        await clock.force_tick()
    assert results == [3, 6, 9]


@pytest.mark.asyncio
async def test_clock_subscribe_unsubscribe(clock):
    results = []
    async def cb(tick):
        results.append(tick)
    sub = clock.subscribe(2, cb)
    for _ in range(4):
        await clock.force_tick()
    assert len(results) == 2
    clock.unsubscribe(sub)
    for _ in range(4):
        await clock.force_tick()
    assert len(results) == 2


@pytest.mark.asyncio
async def test_clock_disable_enable(clock):
    results = []
    async def cb(tick):
        results.append(tick)
    sub = clock.subscribe(2, cb)
    clock.disable_subscription(sub)
    for _ in range(6):
        await clock.force_tick()
    assert len(results) == 0
    clock.enable_subscription(sub)
    for _ in range(6):
        await clock.force_tick()
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_clock_multiple_subscriptions(clock):
    results1 = []
    results2 = []
    async def cb1(tick):
        results1.append(tick)
    async def cb2(tick):
        results2.append(tick)
    clock.subscribe(3, cb1)
    clock.subscribe(5, cb2)
    for _ in range(15):
        await clock.force_tick()
    assert results1 == [3, 6, 9, 12, 15]
    assert results2 == [5, 10, 15]


@pytest.mark.asyncio
async def test_clock_callback_exception_does_not_crash(clock):
    async def bad_cb(tick):
        raise ValueError("test error")
    good_results = []
    async def good_cb(tick):
        good_results.append(tick)
    clock.subscribe(1, bad_cb)
    clock.subscribe(1, good_cb)
    for _ in range(5):
        await clock.force_tick()
    assert good_results == [1, 2, 3, 4, 5]


@pytest.mark.asyncio
async def test_clock_tick_rate_property(clock):
    c2 = GlobalSystemClock(tick_rate_hz=50.0)
    assert c2.tick_rate_hz == 50.0
    assert c2._tick_interval == 0.02


@pytest.mark.asyncio
async def test_clock_idempotent_start(clock):
    await clock.start()
    await clock.start()
    assert clock.is_running
    await clock.stop()
    assert not clock.is_running


@pytest.mark.asyncio
async def test_clock_elapsed_seconds(clock):
    await clock.start()
    await asyncio.sleep(0.06)
    await clock.stop()
    assert clock.elapsed_seconds >= 0.04


@pytest.mark.asyncio
async def test_clock_subscribe_interval_one(clock):
    results = []
    async def cb(tick):
        results.append(tick)
    clock.subscribe(0, cb)
    for _ in range(5):
        await clock.force_tick()
    assert results == [1, 2, 3, 4, 5]


@pytest.mark.asyncio
async def test_wait_for_ticks_deterministic(clock):
    """wait_for_ticks advances correctly with force_tick."""
    async def ticker():
        for _ in range(10):
            await asyncio.sleep(0.01)
            await clock.force_tick()

    task = asyncio.create_task(ticker())
    result = await clock.wait_for_ticks(5)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    assert result >= 5


@pytest.mark.asyncio
async def test_wait_for_ticks_real_time(clock):
    """wait_for_ticks advances with real clock ticks."""
    await clock.start()
    result = await clock.wait_for_ticks(5)
    await clock.stop()
    assert result >= 5


@pytest.mark.asyncio
async def test_wait_for_ticks_clamped_to_one(clock):
    """wait_for_ticks(0) should wait at least 1 tick."""
    async def ticker():
        for _ in range(5):
            await asyncio.sleep(0.01)
            await clock.force_tick()

    task = asyncio.create_task(ticker())
    result = await clock.wait_for_ticks(0)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    assert result >= 1


@pytest.mark.asyncio
async def test_wait_for_ticks_multi_waiter(clock):
    """Multiple waiters all receive correct tick count."""
    async def ticker():
        for _ in range(15):
            await asyncio.sleep(0.01)
            await clock.force_tick()

    async def waiter(n):
        return await clock.wait_for_ticks(n)

    task = asyncio.create_task(ticker())
    r1 = asyncio.create_task(waiter(5))
    r2 = asyncio.create_task(waiter(10))
    results = await asyncio.gather(r1, r2)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    assert results[0] >= 5
    assert results[1] >= 10
    assert results[0] < results[1]
