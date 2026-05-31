"""P10-1: Smoke tests for top core modules — verify importability."""


def test_import_intent_registry():
    from core.intent_registry import IntentRegistry
    r = IntentRegistry()
    assert r is not None


def test_import_tiered_loader():
    from core.system.config.tiered_loader import get_config
    cfg = get_config("standard/behavior/thresholds")
    assert cfg is not None


def test_import_magic_numbers():
    from core.system.config.magic_numbers import behavior_threshold, loop_sleep, timeout_value
    assert behavior_threshold("nonexistent", 42) == 42
    assert loop_sleep("nonexistent", 0.5) == 0.5
    assert timeout_value("nonexistent", 99) == 99


def test_import_module_manager_models():
    from core.system.module_manager.models import ModuleDescriptor, ModuleInstance, ModuleStatus
    assert ModuleStatus is not None


def test_import_hook_registry():
    from core.plugin.hook_registry import HookRegistry
    r = HookRegistry()
    assert r is not None


def test_import_plugin_manager():
    from core.plugin.plugin_manager import PluginManager
    assert PluginManager is not None


def test_import_message_logger_handler():
    from core.plugin.handlers.message_logger import MessageLoggerHandler
    h = MessageLoggerHandler()
    assert h is not None


def test_import_file_operation_handler():
    from services.handlers.file_operation_handler import FileOperationHandler
    h = FileOperationHandler()
    assert h is not None


def test_import_web_search_handler():
    from services.handlers.web_search_handler import WebSearchHandler
    h = WebSearchHandler()
    assert h is not None


def test_import_learning_handler():
    from services.handlers.learning_handler import LearningHandler
    h = LearningHandler()
    assert h is not None


def test_import_google_drive_handler():
    from services.handlers.google_drive_handler import GoogleDriveHandler
    h = GoogleDriveHandler()
    assert h is not None


def test_import_hot_reload_module():
    from modules.hot_reload_service import HotReloadService
    h = HotReloadService()
    assert h is not None


def test_import_math_verifier_module():
    from modules.math_verifier import MathVerifier
    v = MathVerifier()
    assert v is not None


def test_import_resource_awareness_module():
    from modules.resource_awareness_service import ResourceAwarenessService
    r = ResourceAwarenessService()
    assert r is not None


def test_import_chat_service():
    from services.chat_service import ChatService
    c = ChatService()
    assert c is not None


def test_import_llm_router():
    from services.llm.router import AngelaLLMService
    l = AngelaLLMService()
    assert l is not None


def test_import_feedback_processor():
    from core.feedback_processor import FeedbackProcessor
    f = FeedbackProcessor()
    assert f is not None
    assert f.success_threshold == 0.7


def test_import_behavior_feedback():
    from core.system.config.magic_numbers import behavior_feedback
    assert behavior_feedback("success_threshold") is not None
    assert behavior_feedback("nonexistent", 99) == 99


def test_import_behavior_executor():
    from core.system.config.magic_numbers import behavior_executor
    assert behavior_executor("default_action_timeout") is not None
    assert behavior_executor("nonexistent", 99) == 99


def test_import_timing_value():
    from core.system.config.magic_numbers import timing_value
    assert timing_value("nonexistent", 1.5) == 1.5
    assert timing_value("timeout.llm") is not None


def test_import_llm_param():
    from core.system.config.magic_numbers import llm_param
    assert llm_param("nonexistent", 0.7) == 0.7


def test_import_heartbeat_value():
    from core.system.config.magic_numbers import heartbeat_value
    assert heartbeat_value("heartbeat.max_interval") is not None
    assert heartbeat_value("nonexistent", 99) == 99


def test_import_error_handler():
    from core.error.error_handler import ErrorCategory, ErrorSeverity, RecoveryStrategy
    assert ErrorCategory.SYSTEM is not None
    assert ErrorSeverity.CRITICAL is not None
    assert RecoveryStrategy.RESTART is not None


def test_import_circuit_breaker():
    from core.error.error_handler import CircuitBreaker
    cb = CircuitBreaker("test_service")
    assert cb is not None
    assert cb.service_name == "test_service"


def test_import_error_handler_context():
    from core.error.error_handler import ErrorHandler
    eh = ErrorHandler()
    assert eh is not None


def test_import_waiting_scheduler():
    from core.waiting_scheduler import WaitingScheduler, ScheduledTask
    assert ScheduledTask is not None
    task = ScheduledTask(
        deadline=1.0,
        submit_time=0.0,
        label="test",
        timeout=8.0,
    )
    assert task.label == "test"


def test_import_event_loop_enums():
    from core.event_loop_system import EventPriority, EventCategory
    assert EventPriority.NORMAL is not None
    assert EventCategory.USER_INTERACTION is not None
