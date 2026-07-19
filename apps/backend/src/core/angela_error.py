import enum
import json
from typing import Any, Callable, Dict, List, Optional


class ErrorSeverity(enum.Enum):
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


class ErrorCategory(enum.Enum):
    UNKNOWN = "unknown"
    CONFIGURATION = "configuration"
    VALIDATION = "validation"
    NETWORK = "network"
    RESOURCE = "resource"
    SECURITY = "security"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATABASE = "database"
    MEMORY = "memory"
    AI_MODEL = "ai_model"
    LLM = "llm"
    AUDIO = "audio"
    WEBSOCKET = "websocket"
    BUSINESS_LOGIC = "business_logic"
    RATE_LIMIT = "rate_limit"
    NOT_FOUND = "not_found"
    CORE = "core"
    INTENT = "intent"
    CARD = "card"
    MONITORING = "monitoring"
    SERVICE = "service"


class ErrorContext:
    def __init__(self, **kwargs):
        self.additional_info: Dict[str, Any] = dict(kwargs)

    def __repr__(self) -> str:
        return f"ErrorContext({self.additional_info})"


class AngelaError(Exception):
    DEFAULT_CODE = "ANGELA_ERROR"
    DEFAULT_MESSAGE = "An error occurred in Angela AI"
    DEFAULT_CATEGORY = ErrorCategory.UNKNOWN
    DEFAULT_SEVERITY = ErrorSeverity.ERROR

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        code: str = DEFAULT_CODE,
        category: ErrorCategory = DEFAULT_CATEGORY,
        severity: ErrorSeverity = DEFAULT_SEVERITY,
        cause: Optional[BaseException] = None,
        context: Optional[ErrorContext] = None,
        **extra: Any,
    ):
        self.message = message
        self.code = code
        self.category = category
        self.severity = severity
        self.cause = cause
        self.context = context or ErrorContext()
        for k, v in extra.items():
            self.context.additional_info[k] = v
        super().__init__(message)

    def __str__(self) -> str:
        return f"[{self.code}] {self.message} ({self.category.value})"

    def __repr__(self) -> str:
        return f"AngelaError(code='{self.code}', message='{self.message}', category={self.category}, severity={self.severity})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "category": self.category.value,
                "severity": self.severity.value,
            }
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


class CoreError(AngelaError):
    def __init__(self, message: str = "Core system error", details: dict = None, **kwargs):
        super().__init__(message, code="CORE_ERR", category=ErrorCategory.CORE, **kwargs)


class ConfigurationError(AngelaError):
    def __init__(self, message: str = "Configuration error", details: dict = None, **kwargs):
        super().__init__(message, code="CONFIG_ERR", category=ErrorCategory.CONFIGURATION, **kwargs)


class NetworkError(AngelaError):
    def __init__(self, message: str = "Network error", details: dict = None, **kwargs):
        super().__init__(message, code="NET_ERR", category=ErrorCategory.NETWORK, **kwargs)


class WebSocketError(AngelaError):
    def __init__(self, message: str = "WebSocket error", details: dict = None, **kwargs):
        super().__init__(message, code="WS_ERR", category=ErrorCategory.WEBSOCKET, **kwargs)


class DatabaseError(AngelaError):
    def __init__(self, message: str = "Database error", details: dict = None, **kwargs):
        super().__init__(message, code="DB_ERR", category=ErrorCategory.DATABASE, **kwargs)


class ResourceError(AngelaError):
    def __init__(self, message: str = "Resource error", details: dict = None, **kwargs):
        super().__init__(message, code="RES_ERR", category=ErrorCategory.RESOURCE, **kwargs)


class ValidationError(AngelaError):
    def __init__(self, message: str = "Validation error", details: dict = None, **kwargs):
        super().__init__(message, code="VAL_ERR", category=ErrorCategory.VALIDATION, **kwargs)


class NotFoundError(AngelaError):
    def __init__(self, message: str = "Not found", details: dict = None, **kwargs):
        super().__init__(message, code="NOT_FOUND", category=ErrorCategory.NOT_FOUND, **kwargs)


class MemoryError(AngelaError):
    def __init__(self, message: str = "Memory system error", details: dict = None, **kwargs):
        super().__init__(message, code="MEM_ERR", category=ErrorCategory.MEMORY, **kwargs)


class AIModelError(AngelaError):
    def __init__(self, message: str = "AI model error", details: dict = None, **kwargs):
        super().__init__(message, code="AI_ERR", category=ErrorCategory.AI_MODEL, **kwargs)


class LLMError(AngelaError):
    def __init__(self, message: str = "LLM error", details: dict = None, **kwargs):
        super().__init__(message, code="LLM_ERR", category=ErrorCategory.LLM, **kwargs)


class AudioError(AngelaError):
    def __init__(self, message: str = "Audio error", details: dict = None, **kwargs):
        super().__init__(message, code="AUDIO_ERR", category=ErrorCategory.AUDIO, **kwargs)


class SecurityError(AngelaError):
    def __init__(self, message: str = "Security error", details: dict = None, **kwargs):
        super().__init__(message, code="SEC_ERR", category=ErrorCategory.SECURITY, **kwargs)


class AuthenticationError(AngelaError):
    def __init__(self, message: str = "Authentication error", details: dict = None, **kwargs):
        super().__init__(message, code="AUTH_ERR", category=ErrorCategory.AUTHENTICATION, **kwargs)


class AuthorizationError(AngelaError):
    def __init__(self, message: str = "Authorization error", details: dict = None, **kwargs):
        super().__init__(message, code="AUTHZ_ERR", category=ErrorCategory.AUTHORIZATION, **kwargs)


class BusinessLogicError(AngelaError):
    def __init__(self, message: str = "Business logic error", details: dict = None, **kwargs):
        super().__init__(message, code="BIZ_ERR", category=ErrorCategory.BUSINESS_LOGIC, **kwargs)


class RateLimitError(AngelaError):
    def __init__(self, message: str = "Rate limit exceeded", details: dict = None, **kwargs):
        super().__init__(message, code="RATE_LIMIT", category=ErrorCategory.RATE_LIMIT, **kwargs)


class IntentError(AngelaError):
    def __init__(self, message: str = "Intent detection error", details: dict = None, **kwargs):
        super().__init__(message, code="INTENT_ERR", category=ErrorCategory.INTENT, **kwargs)


class CardError(AngelaError):
    def __init__(self, message: str = "Card pipeline error", details: dict = None, **kwargs):
        super().__init__(message, code="CARD_ERR", category=ErrorCategory.CARD, **kwargs)


class ServiceError(AngelaError):
    def __init__(self, message: str = "Service error", details: dict = None, **kwargs):
        super().__init__(message, code="SVC_ERR", category=ErrorCategory.SERVICE, **kwargs)


class MonitoringError(AngelaError):
    def __init__(self, message: str = "Monitoring error", details: dict = None, **kwargs):
        super().__init__(message, code="MON_ERR", category=ErrorCategory.MONITORING, **kwargs)


class ResourceNotFoundError(AngelaError):
    def __init__(
        self,
        message: str = "Resource not found",
        resource: str = "",
        details: dict = None,
        **kwargs,
    ):
        d = {"resource": resource}
        if details:
            d.update(details)
        super().__init__(message, code="NOT_FOUND_ERR", category=ErrorCategory.NOT_FOUND, **kwargs)


class ErrorHandler:
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}

    def register_handler(self, error_type: str, handler: Callable) -> None:
        self._handlers.setdefault(error_type, []).append(handler)

    def handle(self, error: Exception) -> Any:
        error_type = type(error).__name__
        handlers = self._handlers.get(error_type, [])
        results = []
        for h in handlers:
            results.append(h(error))
        return results


__all__ = [
    "AngelaError",
    "ErrorSeverity",
    "ErrorCategory",
    "ErrorContext",
    "ErrorHandler",
    "CoreError",
    "ConfigurationError",
    "ValidationError",
    "ResourceNotFoundError",
    "ServiceError",
    "MemoryError",
    "IntentError",
    "CardError",
    "MonitoringError",
    "NetworkError",
    "WebSocketError",
    "DatabaseError",
    "AIModelError",
    "LLMError",
    "AudioError",
    "SecurityError",
    "AuthenticationError",
    "AuthorizationError",
    "ResourceError",
    "NotFoundError",
    "BusinessLogicError",
    "RateLimitError",
]
