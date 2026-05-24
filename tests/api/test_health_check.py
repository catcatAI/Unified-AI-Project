"""Tests for the health_check handler in isolation."""

import pytest


class TestHealthCheck:
    """Test the health_check function directly."""

    @pytest.mark.asyncio
    async def test_health_check_returns_healthy_status(self):
        from api.router import health_check
        result = await health_check()
        assert result == {"status": "healthy"}

    @pytest.mark.asyncio
    async def test_health_check_has_status_healthy(self):
        from api.router import health_check
        result = await health_check()
        assert result["status"] == "healthy"

    def test_health_check_is_coroutine_function(self):
        import inspect
        from api.router import health_check
        assert inspect.iscoroutinefunction(health_check)
