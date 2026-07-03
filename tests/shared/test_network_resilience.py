import asyncio
import pytest
from shared.network_resilience import RetryPolicy, CircuitBreaker


class TestRetryPolicy:
    @pytest.mark.asyncio
    async def test_succeeds_on_first_try(self):
        policy = RetryPolicy(max_retries=3, base_delay=0.01)

        async def success():
            return "ok"

        result = await policy.execute(success)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_retries_on_failure(self):
        attempts = 0
        policy = RetryPolicy(max_retries=3, base_delay=0.01)

        async def eventually_succeeds():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ValueError(f"Attempt {attempts} failed")
            return "success"

        result = await policy.execute(eventually_succeeds)
        assert result == "success"
        assert attempts == 3

    @pytest.mark.asyncio
    async def test_exhausts_retries(self):
        policy = RetryPolicy(max_retries=2, base_delay=0.01)

        async def always_fails():
            raise RuntimeError("persistent failure")

        with pytest.raises(RuntimeError, match="persistent failure"):
            await policy.execute(always_fails)

    @pytest.mark.asyncio
    async def test_backoff_increases_delay(self):
        delays = []
        policy = RetryPolicy(max_retries=3, base_delay=0.5, backoff_factor=2.0, max_delay=60.0)

        async def fails():
            raise ValueError("fail")

        original_sleep = asyncio.sleep
        try:
            async def tracking_sleep(d):
                delays.append(d)

            asyncio.sleep = tracking_sleep
            with pytest.raises(ValueError):
                await policy.execute(fails)
            assert len(delays) == 2  # 2 retries after first failure
            assert delays[0] == 0.5
            assert delays[1] == 1.0
        finally:
            asyncio.sleep = original_sleep


class TestCircuitBreaker:
    @pytest.mark.asyncio
    async def test_closed_circuit_passes(self):
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.1)

        async def success():
            return "ok"

        result = await cb.call(success)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_opens_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=60.0)

        async def fails():
            raise ValueError("fail")

        for _ in range(2):
            with pytest.raises(ValueError):
                await cb.call(fails)

        with pytest.raises(Exception, match="Circuit breaker is open"):
            await cb.call(fails)

    @pytest.mark.asyncio
    async def test_half_open_recovers(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.05)

        async def fails():
            raise ValueError("fail")

        async def succeeds():
            return "recovered"

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await cb.call(fails)

        # Still open
        with pytest.raises(Exception, match="Circuit breaker is open"):
            await cb.call(fails)

        # Wait for recovery
        await asyncio.sleep(0.1)

        # Half-open: success should close circuit
        result = await cb.call(succeeds)
        assert result == "recovered"

        # Circuit should be closed again
        result2 = await cb.call(succeeds)
        assert result2 == "recovered"

    @pytest.mark.asyncio
    async def test_resets_failure_count_on_success(self):
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60.0)

        async def fails():
            raise ValueError("fail")

        async def succeeds():
            return "ok"

        for _ in range(2):
            with pytest.raises(ValueError):
                await cb.call(fails)

        await cb.call(succeeds)

        # Should still be closed (counter reset)
        for _ in range(2):
            with pytest.raises(ValueError):
                await cb.call(fails)
        # 2 more failures, but threshold is 3, so still closed
        result = await cb.call(succeeds)
        assert result == "ok"
