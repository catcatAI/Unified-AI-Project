# =============================================================================
# ANGELA-MATRIX: L6[执行层] 全层级 [A] L2+
# =============================================================================
#
# 职责: 企业级日志系统，提供结构化日志、错误追踪和审计功能
# 维度: 涉及所有维度，记录系统事件
# 安全: 使用 Key A (后端控制) 进行审计日志记录
# 成熟度: L2+ 等级理解日志的重要性
#
# =============================================================================

import asyncio
import traceback
import uuid
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from pathlib import Path
from enum import Enum
from contextvars import ContextVar

# 上下文變量用於追蹤請求
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
session_id_var: ContextVar[Optional[str]] = ContextVar('session_id', default=None)

class LogLevel(Enum):
    """日誌級別"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class LogCategory(Enum):
    """日誌分類"""
    SYSTEM = "system"
    USER = "user"
    AI = "ai"
    NETWORK = "network"
    DATABASE = "database"
    SECURITY = "security"
    PERFORMANCE = "performance"
    AUDIT = "audit"

class EnterpriseLogger:
    """企業級日誌記錄器"""
    
    def __init__(self, name: str, log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 創建 Python logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 清除現有處理器
        self.logger.handlers.clear()
        
        # 添加文件處理器
        self._add_file_handler()
        
        # 添加控制台處理器
        self._add_console_handler()
    
    def _add_file_handler(self):
        """添加文件處理器"""
        from logging.handlers import RotatingFileHandler
        
        # 主日誌文件
        main_handler = RotatingFileHandler(
            self.log_dir / f"{self.name}.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        main_handler.setLevel(logging.DEBUG)
        
        # 錯誤日誌文件
        error_handler = RotatingFileHandler(
            self.log_dir / f"{self.name}_error.log",
            maxBytes=10*1024*1024,
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        
        # 審計日誌文件
        audit_handler = RotatingFileHandler(
            self.log_dir / f"{self.name}_audit.log",
            maxBytes=10*1024*1024,
            backupCount=10
        )
        audit_handler.setLevel(logging.INFO)
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        main_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        audit_handler.setFormatter(formatter)
        
        self.logger.addHandler(main_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(audit_handler)
    
    def _add_console_handler(self):
        """添加控制台處理器"""
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def _log(
        self,
        level: LogLevel,
        category: LogCategory,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Exception] = None
    ):
        """記錄日誌"""
        # 獲取上下文
        request_id = request_id_var.get()
        user_id = user_id_var.get()
        session_id = session_id_var.get()
        
        # 構建日誌記錄
        log_record = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': level.value,
            'category': category.value,
            'message': message,
            'request_id': request_id,
            'user_id': user_id,
            'session_id': session_id,
            'extra': extra or {}
        }
        
        # 如果有異常，添加異常信息
        if exc_info:
            log_record['exception'] = {
                'type': type(exc_info).__name__,
                'message': str(exc_info),
                'traceback': traceback.format_exc()
            }
        
        # 記錄到 Python logger
        log_level_map = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL
        }
        
        self.logger.log(
            log_level_map[level],
            json.dumps(log_record, ensure_ascii=False),
            extra=log_record
        )
    
    def debug(self, message: str, category: LogCategory = LogCategory.SYSTEM, **extra):
        """記錄 DEBUG 級別日誌"""
        self._log(LogLevel.DEBUG, category, message, extra)
    
    def info(self, message: str, category: LogCategory = LogCategory.SYSTEM, **extra):
        """記錄 INFO 級別日誌"""
        self._log(LogLevel.INFO, category, message, extra)
    
    def warning(self, message: str, category: LogCategory = LogCategory.SYSTEM, **extra):
        """記錄 WARNING 級別日誌"""
        self._log(LogLevel.WARNING, category, message, extra)
    
    def error(
        self,
        message: str,
        category: LogCategory = LogCategory.SYSTEM,
        exc_info: Optional[Exception] = None,
        **extra
    ):
        """記錄 ERROR 級別日誌"""
        self._log(LogLevel.ERROR, category, message, extra, exc_info)
    
    def critical(
        self,
        message: str,
        category: LogCategory = LogCategory.SYSTEM,
        exc_info: Optional[Exception] = None,
        **extra
    ):
        """記錄 CRITICAL 級別日誌"""
        self._log(LogLevel.CRITICAL, category, message, extra, exc_info)
    
    def audit(self, action: str, user_id: Optional[str] = None, **details):
        """記錄審計日誌"""
        if user_id:
            user_id_var.set(user_id)
        
        self._log(
            LogLevel.INFO,
            LogCategory.AUDIT,
            f"Audit: {action}",
            extra=details
        )

class LogContext:
    """日誌上下文管理器"""
    
    def __init__(
        self,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        self.request_id = request_id
        self.user_id = user_id
        self.session_id = session_id
        self.tokens = []
    
    def __enter__(self):
        if self.request_id:
            self.tokens.append(request_id_var.set(self.request_id))
        if self.user_id:
            self.tokens.append(user_id_var.set(self.user_id))
        if self.session_id:
            self.tokens.append(session_id_var.set(self.session_id))
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        for token in self.tokens:
            request_id_var.reset(token)
        return False

# 全局日誌管理器
_loggers: Dict[str, EnterpriseLogger] = {}

def get_logger(name: str) -> EnterpriseLogger:
    """獲取或創建日誌記錄器"""
    if name not in _loggers:
        _loggers[name] = EnterpriseLogger(name)
    return _loggers[name]

def set_request_context(request_id: str, user_id: Optional[str] = None, session_id: Optional[str] = None):
    """設置請求上下文"""
    if request_id:
        request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)
    if session_id:
        session_id_var.set(session_id)

def clear_request_context():
    """清除請求上下文"""
    request_id_var.set(None)
    user_id_var.set(None)
    session_id_var.set(None)