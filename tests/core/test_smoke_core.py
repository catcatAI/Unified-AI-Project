"""P10-1: Smoke tests for core modules — parameterized for maintainability.

Consolidated from 27 standalone test functions into 4 parameterized tests.
"""

import pytest

# =============================================================================
# Group 1: Module instantiation — classes that can be created with no args
# =============================================================================

_INSTANTIABLE_MODULES = [
    ("core.intent_registry", "IntentRegistry"),
    ("core.plugin.hook_registry", "HookRegistry"),
    ("core.plugin.handlers.message_logger", "MessageLoggerHandler"),
    ("core.feedback_processor", "FeedbackProcessor"),
    ("services.handlers.file_operation_handler", "FileOperationHandler"),
    ("services.handlers.web_search_handler", "WebSearchHandler"),
    ("services.handlers.learning_handler", "LearningHandler"),
    ("services.handlers.google_drive_handler", "GoogleDriveHandler"),
    ("services.hot_reload_service", "HotReloadService"),
    ("services.math_verifier", "MathVerifier"),
    ("services.resource_awareness_service", "ResourceAwarenessService"),
    ("services.chat_service", "ChatService"),
    ("services.llm.router", "AngelaLLMService"),
    ("services.websocket_manager", "ConnectionManager"),
]


@pytest.mark.parametrize("module_path,class_name", _INSTANTIABLE_MODULES)
def test_module_instantiation(module_path: str, class_name: str) -> None:
    """Verify each core module class can be imported and instantiated."""
    import importlib

    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    instance = cls()
    assert instance is not None, f"{class_name}() returned None"


# =============================================================================
# Group 2: Config accessor functions (magic_numbers)
# =============================================================================

_CONFIG_ACCESSORS = [
    ("core.system.config.magic_numbers", "behavior_threshold", 42, None),
    ("core.system.config.magic_numbers", "loop_sleep", 0.5, None),
    ("core.system.config.magic_numbers", "timeout_value", 99, None),
    ("core.system.config.magic_numbers", "behavior_feedback", 99, "success_threshold"),
    ("core.system.config.magic_numbers", "behavior_executor", 99, "default_action_timeout"),
    ("core.system.config.magic_numbers", "timing_value", 1.5, "timeout.llm"),
    ("core.system.config.magic_numbers", "llm_param", 0.7, None),
    ("core.system.config.magic_numbers", "heartbeat_value", 99, "heartbeat.max_interval"),
]


@pytest.mark.parametrize(
    "module_path,func_name,default,real_key",
    _CONFIG_ACCESSORS,
)
def test_config_accessor_fallback(
    module_path: str, func_name: str, default: int | float, real_key: str | None
) -> None:
    """Verify each config accessor returns default for nonexistent keys.
    Where possible, also verify real config keys return non-None values.
    """
    import importlib

    module = importlib.import_module(module_path)
    func = getattr(module, func_name)
    # Fallback behavior
    assert func("nonexistent", default) == default, (
        f"{func_name} did not return default {default}"
    )
    # Real key existence (if known)
    if real_key is not None:
        val = func(real_key)
        assert val is not None, f"{func_name}({real_key!r}) returned None"


def test_tiered_loader_returns_config() -> None:
    """Verify tiered_loader.get_config returns a config object."""
    from core.system.config.tiered_loader import get_config

    cfg = get_config("standard/behavior/thresholds")
    assert cfg is not None


def test_module_manager_models_have_required_enums() -> None:
    """Verify ModuleManager model enums are importable."""
    from core.system.module_manager.models import ModuleDescriptor, ModuleInstance, ModuleStatus

    assert ModuleStatus is not None
    # Verify ModuleStatus has expected lifecycle states
    expected_states = {"DISCOVERED", "INITIALIZING", "RUNNING", "STOPPED", "DEAD"}
    actual_states = {m.name for m in ModuleStatus}
    missing = expected_states - actual_states
    assert not missing, f"ModuleStatus missing expected states: {missing}"


# =============================================================================
# Group 3: Plugin system
# =============================================================================

def test_plugin_manager_importable() -> None:
    """Verify PluginManager can be imported."""
    from core.plugin.plugin_manager import PluginManager

    assert PluginManager is not None


# =============================================================================
# Group 4: Error handling system
# =============================================================================

def test_error_enums_have_required_values() -> None:
    """Verify error handling enums have required values."""
    from core.error.error_handler import ErrorCategory, ErrorSeverity, RecoveryStrategy

    assert ErrorCategory.SYSTEM is not None
    assert ErrorSeverity.CRITICAL is not None
    assert RecoveryStrategy.RESTART is not None


def test_circuit_breaker_stores_service_name() -> None:
    """Verify CircuitBreaker instantiation with service name."""
    from core.error.error_handler import CircuitBreaker

    cb = CircuitBreaker("test_service")
    assert cb is not None
    assert cb.service_name == "test_service"


def test_error_handler_instantiation() -> None:
    """Verify ErrorHandler can be instantiated."""
    from core.error.error_handler import ErrorHandler

    eh = ErrorHandler()
    assert eh is not None


# =============================================================================
# Group 5: Scheduler
# =============================================================================

def test_waiting_scheduler_task_creation() -> None:
    """Verify ScheduledTask creation with required fields."""
    from core.waiting_scheduler import ScheduledTask

    task = ScheduledTask(
        deadline=1.0,
        submit_time=0.0,
        label="test",
        timeout=8.0,
    )
    assert task.label == "test"
    assert task.deadline == 1.0
    assert task.submit_time == 0.0
    assert task.timeout == 8.0


# =============================================================================
# Group 6: Event loop enums
# =============================================================================

def test_event_loop_enums_have_required_values() -> None:
    """Verify event loop enums have required values."""
    from core.event_loop_system import EventCategory, EventPriority

    assert EventPriority.NORMAL is not None
    assert EventCategory.USER_INTERACTION is not None
