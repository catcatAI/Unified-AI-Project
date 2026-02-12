#!/usr/bin/env python3
"""
Angela AI - Unified Error Handling System
统一错误处理系统

提供统一的错误类型和错误处理机制，便于错误追踪和调试。
"""

import sys
import traceback
import logging
from typing import Any, Dict, Optional, List, Type, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json


class ErrorSeverity(Enum):
    """错误严重程度"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    FATAL = "fatal"


class ErrorCategory(Enum):
    """错误类别"""
    # 核心错误
    CORE = "core"
    
    # 配置错误
    CONFIGURATION = "configuration"
    
    # 网络/通信错误
    NETWORK = "network"
    WEBSOCKET = "websocket"
    
    # 数据库错误
    DATABASE = "database"
    
    # 记忆系统错误
    MEMORY = "memory"
    HAM_MEMORY = "ham_memory"
    
    # AI 模型错误
    AI_MODEL = "ai_model"
    LLM = "llm"
    
    # 音频错误
    AUDIO = "audio"
    TTS = "tts"
    SPEECH_RECOGNITION = "speech_recognition"
    
    # Live2D 错误
    LIVE2D = "live2d"
    RENDERING = "rendering"
    
    # 安全错误
    SECURITY = "security"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    
    # 资源错误
    RESOURCE = "resource"
    RESOURCE_POOL = "resource_pool"
    
    # IO 错误
    FILE_IO = "file_io"
    BROWSER = "browser"
    
    # 业务逻辑错误
    BUSINESS_LOGIC = "business_logic"
    VALIDATION = "validation"
    
    # 未知错误
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """错误上下文信息"""
    timestamp: datetime = field(default_factory=datetime.now)
    module: str = ""
    function: str = ""
    line: int = 0
    traceback_str: str = ""
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "module": self.module,
            "function": self.function,
            "line": self.line,
            "traceback": self.traceback_str,
            "user_id": self.user_id,
            "request_id": self.request_id,
            "additional_info": self.additional_info,
        }


class AngelaError(Exception):
    """
    Angela AI 基础错误类
    
    所有 Angela AI 相关的错误都应该继承此类。
    """
    
    # 默认错误代码
    DEFAULT_CODE = "ANGELA_ERROR"
    
    # 默认错误消息
    DEFAULT_MESSAGE = "An error occurred in Angela AI"
    
    # 默认错误类别
    DEFAULT_CATEGORY = ErrorCategory.UNKNOWN
    
    # 默认严重程度
    DEFAULT_SEVERITY = ErrorSeverity.ERROR
    
    def __init__(
        self,
        message: Optional[str] = None,
        code: Optional[str] = None,
        category: Optional[ErrorCategory] = None,
        severity: Optional[ErrorSeverity] = None,
        context: Optional[ErrorContext] = None,
        cause: Optional[Exception] = None,
        **kwargs
    ):
        self.message = message or self.DEFAULT_MESSAGE
        self.code = code or self.DEFAULT_CODE
        self.category = category or self.DEFAULT_CATEGORY
        self.severity = severity or self.DEFAULT_SEVERITY
        self.context = context or self._create_context()
        self.cause = cause
        
        # 添加额外信息
        self.context.additional_info.update(kwargs)
        
        # 调用父类初始化
        super().__init__(self.message)
    
    def _create_context(self) -> ErrorContext:
        """创建错误上下文"""
        stack = traceback.extract_stack()
        frame = stack[-2] if len(stack) >= 2 else stack[-1]
        
        return ErrorContext(
            module=frame.name,
            function=frame.name,
            line=frame.lineno,
            traceback_str="".join(traceback.format_stack()[:-1])
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "category": self.category.value,
                "severity": self.severity.value,
                "context": self.context.to_dict(),
            }
        }
    
    def to_json(self) -> str:
        """转换为 JSON"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    def log(self, logger: Optional[logging.Logger] = None) -> None:
        """记录错误日志"""
        if logger is None:
            logger = logging.getLogger(__name__)
        
        log_method = {
            ErrorSeverity.DEBUG: logger.debug,
            ErrorSeverity.INFO: logger.info,
            ErrorSeverity.WARNING: logger.warning,
            ErrorSeverity.ERROR: logger.error,
            ErrorSeverity.CRITICAL: logger.critical,
            ErrorSeverity.FATAL: logger.critical,
        }.get(self.severity, logger.error)
        
        log_method(
            f"[{self.code}] {self.message}",
            extra={
                "error_code": self.code,
                "error_category": self.category.value,
                "error_severity": self.severity.value,
                "context": self.context.to_dict(),
            }
        )
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"[{self.code}] {self.message} ({self.category.value})"
    
    def __repr__(self) -> str:
        """对象表示"""
        return f"{self.__class__.__name__}(code={self.code!r}, message={self.message!r})"


# 核心错误
class CoreError(AngelaError):
    """核心错误"""
    DEFAULT_CODE = "CORE_ERROR"
    DEFAULT_MESSAGE = "Core system error"
    DEFAULT_CATEGORY = ErrorCategory.CORE


class ConfigurationError(AngelaError):
    """配置错误"""
    DEFAULT_CODE = "CONFIG_ERROR"
    DEFAULT_MESSAGE = "Configuration error"
    DEFAULT_CATEGORY = ErrorCategory.CONFIGURATION


# 网络/通信错误
class NetworkError(AngelaError):
    """网络错误"""
    DEFAULT_CODE = "NETWORK_ERROR"
    DEFAULT_MESSAGE = "Network error"
    DEFAULT_CATEGORY = ErrorCategory.NETWORK


class WebSocketError(AngelaError):
    """WebSocket 错误"""
    DEFAULT_CODE = "WEBSOCKET_ERROR"
    DEFAULT_MESSAGE = "WebSocket error"
    DEFAULT_CATEGORY = ErrorCategory.WEBSOCKET


# 数据库错误
class DatabaseError(AngelaError):
    """数据库错误"""
    DEFAULT_CODE = "DATABASE_ERROR"
    DEFAULT_MESSAGE = "Database error"
    DEFAULT_CATEGORY = ErrorCategory.DATABASE


# 记忆系统错误
class MemoryError(AngelaError):
    """记忆系统错误"""
    DEFAULT_CODE = "MEMORY_ERROR"
    DEFAULT_MESSAGE = "Memory system error"
    DEFAULT_CATEGORY = ErrorCategory.MEMORY


class HAMMemoryError(AngelaError):
    """HAM 记忆错误"""
    DEFAULT_CODE = "HAM_MEMORY_ERROR"
    DEFAULT_MESSAGE = "HAM memory error"
    DEFAULT_CATEGORY = ErrorCategory.HAM_MEMORY


# AI 模型错误
class AIModelError(AngelaError):
    """AI 模型错误"""
    DEFAULT_CODE = "AI_MODEL_ERROR"
    DEFAULT_MESSAGE = "AI model error"
    DEFAULT_CATEGORY = ErrorCategory.AI_MODEL


class LLMError(AngelaError):
    """LLM 错误"""
    DEFAULT_CODE = "LLM_ERROR"
    DEFAULT_MESSAGE = "LLM error"
    DEFAULT_CATEGORY = ErrorCategory.LLM


# 音频错误
class AudioError(AngelaError):
    """音频错误"""
    DEFAULT_CODE = "AUDIO_ERROR"
    DEFAULT_MESSAGE = "Audio error"
    DEFAULT_CATEGORY = ErrorCategory.AUDIO


class TTSError(AngelaError):
    """TTS 错误"""
    DEFAULT_CODE = "TTS_ERROR"
    DEFAULT_MESSAGE = "Text-to-speech error"
    DEFAULT_CATEGORY = ErrorCategory.TTS


class SpeechRecognitionError(AngelaError):
    """语音识别错误"""
    DEFAULT_CODE = "SPEECH_RECOGNITION_ERROR"
    DEFAULT_MESSAGE = "Speech recognition error"
    DEFAULT_CATEGORY = ErrorCategory.SPEECH_RECOGNITION


# Live2D 错误
class Live2DError(AngelaError):
    """Live2D 错误"""
    DEFAULT_CODE = "LIVE2D_ERROR"
    DEFAULT_MESSAGE = "Live2D error"
    DEFAULT_CATEGORY = ErrorCategory.LIVE2D


class RenderingError(AngelaError):
    """渲染错误"""
    DEFAULT_CODE = "RENDERING_ERROR"
    DEFAULT_MESSAGE = "Rendering error"
    DEFAULT_CATEGORY = ErrorCategory.RENDERING


# 安全错误
class SecurityError(AngelaError):
    """安全错误"""
    DEFAULT_CODE = "SECURITY_ERROR"
    DEFAULT_MESSAGE = "Security error"
    DEFAULT_CATEGORY = ErrorCategory.SECURITY
    DEFAULT_SEVERITY = ErrorSeverity.CRITICAL


class AuthenticationError(AngelaError):
    """认证错误"""
    DEFAULT_CODE = "AUTHENTICATION_ERROR"
    DEFAULT_MESSAGE = "Authentication error"
    DEFAULT_CATEGORY = ErrorCategory.AUTHENTICATION


class AuthorizationError(AngelaError):
    """授权错误"""
    DEFAULT_CODE = "AUTHORIZATION_ERROR"
    DEFAULT_MESSAGE = "Authorization error"
    DEFAULT_CATEGORY = ErrorCategory.AUTHORIZATION


# 资源错误
class ResourceError(AngelaError):
    """资源错误"""
    DEFAULT_CODE = "RESOURCE_ERROR"
    DEFAULT_MESSAGE = "Resource error"
    DEFAULT_CATEGORY = ErrorCategory.RESOURCE


class ResourcePoolError(AngelaError):
    """资源池错误"""
    DEFAULT_CODE = "RESOURCE_POOL_ERROR"
    DEFAULT_MESSAGE = "Resource pool error"
    DEFAULT_CATEGORY = ErrorCategory.RESOURCE_POOL


# IO 错误
class FileIOError(AngelaError):
    """文件 IO 错误"""
    DEFAULT_CODE = "FILE_IO_ERROR"
    DEFAULT_MESSAGE = "File I/O error"
    DEFAULT_CATEGORY = ErrorCategory.FILE_IO


class BrowserError(AngelaError):
    """浏览器错误"""
    DEFAULT_CODE = "BROWSER_ERROR"
    DEFAULT_MESSAGE = "Browser error"
    DEFAULT_CATEGORY = ErrorCategory.BROWSER


# 业务逻辑错误
class BusinessLogicError(AngelaError):
    """业务逻辑错误"""
    DEFAULT_CODE = "BUSINESS_LOGIC_ERROR"
    DEFAULT_MESSAGE = "Business logic error"
    DEFAULT_CATEGORY = ErrorCategory.BUSINESS_LOGIC


class ValidationError(AngelaError):
    """验证错误"""
    DEFAULT_CODE = "VALIDATION_ERROR"
    DEFAULT_MESSAGE = "Validation error"
    DEFAULT_CATEGORY = ErrorCategory.VALIDATION


class NotFoundError(AngelaError):
    """资源未找到错误"""
    DEFAULT_CODE = "NOT_FOUND_ERROR"
    DEFAULT_MESSAGE = "Resource not found"
    DEFAULT_CATEGORY = ErrorCategory.BUSINESS_LOGIC


class ConflictError(AngelaError):
    """冲突错误"""
    DEFAULT_CODE = "CONFLICT_ERROR"
    DEFAULT_MESSAGE = "Resource conflict"
    DEFAULT_CATEGORY = ErrorCategory.BUSINESS_LOGIC


class RateLimitError(AngelaError):
    """速率限制错误"""
    DEFAULT_CODE = "RATE_LIMIT_ERROR"
    DEFAULT_MESSAGE = "Rate limit exceeded"
    DEFAULT_CATEGORY = ErrorCategory.BUSINESS_LOGIC


# 错误处理器
class ErrorHandler:
    """错误处理器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.error_handlers: Dict[Type[AngelaError], Callable] = {}
        self.global_handler: Optional[Callable] = None
    
    def register_handler(
        self,
        error_type: Type[AngelaError],
        handler: Callable[[AngelaError], Any]
    ) -> None:
        """注册错误处理器"""
        self.error_handlers[error_type] = handler
    
    def set_global_handler(self, handler: Callable[[AngelaError], Any]) -> None:
        """设置全局错误处理器"""
        self.global_handler = handler
    
    def handle(self, error: Exception) -> Any:
        """处理错误"""
        # 如果是 AngelaError，记录日志
        if isinstance(error, AngelaError):
            error.log(self.logger)
            
            # 查找专用处理器
            for error_type, handler in self.error_handlers.items():
                if isinstance(error, error_type):
                    return handler(error)
        
        # 使用全局处理器
        if self.global_handler:
            return self.global_handler(error)
        
        # 默认处理：重新抛出
        raise error
    
    def capture_exception(
        self,
        error: Exception,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        **kwargs
    ) -> AngelaError:
        """捕获异常并转换为 AngelaError"""
        if isinstance(error, AngelaError):
            # 更新上下文
            if user_id:
                error.context.user_id = user_id
            if request_id:
                error.context.request_id = request_id
            error.context.additional_info.update(kwargs)
            return error
        else:
            # 转换为 AngelaError
            return CoreError(
                message=str(error),
                cause=error,
                user_id=user_id,
                request_id=request_id,
                **kwargs
            )


# 全局错误处理器实例
_error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器"""
    return _error_handler


def handle_error(error: Exception) -> Any:
    """处理错误"""
    return _error_handler.handle(error)


def capture_exception(
    error: Exception,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    **kwargs
) -> AngelaError:
    """捕获异常"""
    return _error_handler.capture_exception(error, user_id, request_id, **kwargs)


# 装饰器
def handle_errors(
    default_return: Any = None,
    log_errors: bool = True,
    reraise: bool = False
):
    """错误处理装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    error = capture_exception(e)
                    error.log()
                
                if reraise:
                    raise
                
                return default_return
        return wrapper
    return decorator


def safe_execute(
    func: Callable,
    *args,
    default_return: Any = None,
    log_errors: bool = True,
    **kwargs
) -> Any:
    """安全执行函数"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            error = capture_exception(e)
            error.log()
        return default_return


if __name__ == "__main__":
    # 测试错误处理系统
    
    # 创建错误
    error = ConfigurationError(
        message="Missing required configuration",
        code="MISSING_CONFIG",
        context=ErrorContext(module="test", function="main")
    )
    
    print(f"Error: {error}")
    print(f"Dict: {error.to_dict()}")
    print(f"JSON: {error.to_json()}")
    
    # 测试错误处理
    handler = get_error_handler()
    handler.register_handler(ConfigurationError, lambda e: print(f"Handled: {e}"))
    
    try:
        raise error
    except Exception as e:
        handler.handle(e)