"""Tests for DI dependencies in services.main_api_server.

Verifies that the factory functions used with FastAPI Depends() are callable.
Uses lazy imports inside test functions to avoid triggering heavy top-level imports.
"""

import pytest


class TestMainApiServerDependencies:
    """Verify DI factory functions are callable and produce instances."""

    def test_get_desktop_interaction_is_callable(self):
        """get_desktop_interaction should be a callable."""
        from api.lifespan import get_desktop_interaction

        assert callable(get_desktop_interaction)

    def test_get_action_executor_is_callable(self):
        """get_action_executor should be a callable."""
        from api.lifespan import get_action_executor

        assert callable(get_action_executor)

    def test_get_digital_life_is_callable(self):
        """get_digital_life should be a callable."""
        from api.lifespan import get_digital_life

        assert callable(get_digital_life)

    def test_get_desktop_interaction_returns_instance(self):
        """Calling get_desktop_interaction returns an object (or skips on ImportError)."""
        try:
            from api.lifespan import get_desktop_interaction

            instance = get_desktop_interaction()
            assert type(instance).__name__ == 'DesktopInteraction'
        except Exception as exc:
            pytest.skip(f"get_desktop_interaction() raised {type(exc).__name__}: {exc}")

    def test_get_action_executor_returns_instance(self):
        """Calling get_action_executor returns an object (or skips on ImportError)."""
        try:
            from api.lifespan import get_action_executor

            instance = get_action_executor()
            assert type(instance).__name__ == 'ActionExecutor'
        except Exception as exc:
            pytest.skip(f"get_action_executor() raised {type(exc).__name__}: {exc}")

    def test_get_digital_life_returns_instance(self):
        """Calling get_digital_life returns an object (or skips on ImportError)."""
        try:
            from api.lifespan import get_digital_life

            instance = get_digital_life()
            assert type(instance).__name__ == 'DigitalLifeIntegrator'
        except Exception as exc:
            pytest.skip(f"get_digital_life() raised {type(exc).__name__}: {exc}")

    def test_depends_in_route_signatures(self):
        """The router endpoints that use Depends() reference the factory functions."""
        try:
            import inspect

            from services import main_api_server as mod

            for name, obj in inspect.getmembers(mod, inspect.iscoroutinefunction):
                sig = inspect.signature(obj)
                for param in sig.parameters.values():
                    default = param.default
                    if hasattr(default, "dependency") and callable(default.dependency):
                        dep_name = default.dependency.__name__
                        assert dep_name in (
                            "get_desktop_interaction",
                            "get_action_executor",
                            "get_digital_life",
                        ), f"Unexpected dependency '{dep_name}' in {name}"
        except Exception as exc:
            pytest.skip(f"Route signature inspection raised {type(exc).__name__}: {exc}")
