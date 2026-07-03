import asyncio
import pytest

from shared.utils.async_utils import safe_create_task, safe_create_task_sync, gather_with_concurrency


class TestSafeCreateTask:
    @pytest.mark.asyncio
    async def test_creates_and_completes_task(self):
        async def dummy():
            return 42

        task = safe_create_task(dummy(), name="test_dummy")
        result = await task
        assert result == 42

    @pytest.mark.asyncio
    async def test_task_with_error_does_not_crash(self):
        async def failing():
            raise ValueError("expected error")

        task = safe_create_task(failing(), name="test_fail")
        with pytest.raises(ValueError, match="expected error"):
            await task

    @pytest.mark.asyncio
    async def test_on_error_callback_called(self):
        errors = []

        async def failing():
            raise ValueError("cb error")

        safe_create_task(failing(), name="test_cb", on_error=lambda e: errors.append(str(e)))
        await asyncio.sleep(0.1)
        assert len(errors) == 1
        assert "cb error" in errors[0]


class TestGatherWithConcurrency:
    @pytest.mark.asyncio
    async def test_gather_all_results(self):
        async def work(n):
            return n * 2

        results = await gather_with_concurrency(2, work(1), work(2), work(3))
        assert sorted(results) == [2, 4, 6]

    @pytest.mark.asyncio
    async def test_concurrency_limit_honored(self):
        max_concurrent = 0
        current = 0
        lock = asyncio.Lock()

        async def track(n):
            nonlocal current, max_concurrent
            async with lock:
                current += 1
                max_concurrent = max(max_concurrent, current)
            await asyncio.sleep(0.05)
            async with lock:
                current -= 1
            return n

        await gather_with_concurrency(2, track(1), track(2), track(3), track(4), track(5))
        assert max_concurrent <= 2


class TestSafeCreateTaskSync:
    def test_no_loop_returns_none(self):
        result = safe_create_task_sync(asyncio.sleep(0), name="no_loop")
        assert result is None

    @pytest.mark.asyncio
    async def test_creates_task_in_loop(self):
        async def dummy():
            return 99

        task = safe_create_task_sync(dummy(), name="sync_task")
        assert task is not None
        result = await task
        assert result == 99
