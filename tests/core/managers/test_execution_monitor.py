"""
Tests for ExecutionMonitor — command execution wrapper.

Focus areas:
  - shell=False is the default for execute_command signature
  - Function signatures match expected API
  - Factory function returns a monitor instance
"""

import pytest


class TestShellDefault:
    """Verify shell=False is the default and signature is correct."""

    def test_execute_command_has_shell_param_default_false(self):
        from core.managers.execution_monitor import ExecutionMonitor

        import inspect

        sig = inspect.signature(ExecutionMonitor.execute_command)
        assert "shell" in sig.parameters
        assert sig.parameters["shell"].default is False

    def test_execute_async_command_has_shell_param_default_false(self):
        from core.managers.execution_monitor import ExecutionMonitor

        import inspect

        sig = inspect.signature(ExecutionMonitor.execute_async_command)
        assert "shell" in sig.parameters
        assert sig.parameters["shell"].default is False

    def test_execute_command_accepts_string_or_list(self):
        from core.managers.execution_monitor import ExecutionMonitor

        import inspect

        sig = inspect.signature(ExecutionMonitor.execute_command)
        param = sig.parameters["command"]
        # Should accept Union[str, List[str]]
        assert param.annotation is not inspect.Parameter.empty


class TestMonitorInstantiation:
    """Basic instantiation and config defaults."""

    def test_default_config_applied(self):
        from core.managers.execution_monitor import ExecutionMonitor, ExecutionConfig

        monitor = ExecutionMonitor()
        assert isinstance(monitor.config, ExecutionConfig)
        assert monitor.config.default_timeout == 60.0
        assert monitor.config.adaptive_timeout is True

    def test_custom_config(self):
        from core.managers.execution_monitor import ExecutionMonitor, ExecutionConfig

        config = ExecutionConfig(default_timeout=120.0, adaptive_timeout=False)
        monitor = ExecutionMonitor(config)
        assert monitor.config.default_timeout == 120.0
        assert monitor.config.adaptive_timeout is False


class TestFactoryFunctions:
    """Global convenience factories."""

    def test_get_execution_monitor_returns_instance(self):
        from core.managers.execution_monitor import get_execution_monitor

        monitor = get_execution_monitor()
        from core.managers.execution_monitor import ExecutionMonitor

        assert isinstance(monitor, ExecutionMonitor)

    def test_get_execution_monitor_is_singleton(self):
        from core.managers.execution_monitor import get_execution_monitor

        m1 = get_execution_monitor()
        m2 = get_execution_monitor()
        assert m1 is m2

    def test_execute_with_monitoring_is_callable(self):
        from core.managers.execution_monitor import execute_with_monitoring

        assert callable(execute_with_monitoring)

    def test_execute_async_with_monitoring_is_callable(self):
        from core.managers.execution_monitor import execute_async_with_monitoring

        import inspect

        assert inspect.iscoroutinefunction(execute_async_with_monitoring)
