"""
企業級日誌系統
提供結構化日誌、錯誤追蹤和審計功能
"""

import logging
import json
import traceback
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from pathlib import Path
from enum import Enum
import asyncio
from contextvars import ContextVar
import uuid

# 上下文變量用於追蹤請求
request_id: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
session_id: ContextVar[Optional[str]] = ContextVar('session_id', default=None)

class LogLevel(Enum):
    """日誌級別"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(Enum):
    """日誌分類"""
    SYSTEM = "system"
    API = "api"
    AI = "ai"
    DATABASE = "database"
    SECURITY = "security"
    PERFORMANCE = "performance"
    BUSINESS = "business"
    AUDIT = "audit"

class EnterpriseLogger:
    """企業級日誌記錄器"""
    
    def __init__(self, name: str, log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 創建不同類型的日誌記錄器
        self.loggers = {}
        self._setup_loggers()
        
        # 錯誤統計
        self.error_stats = {
            'total_errors': 0,
            'by_category': {category.value: 0 for category in LogCategory},
            'by_level': {level.value: 0 for level in LogLevel},
            'recent_errors': []
        }
    
    def _setup_loggers(self):
        """設置各種日誌記錄器"""
        # 主日誌記錄器
        self.loggers['main'] = self._create_logger(
            'main',
            self.log_dir / 'app.log',
            logging.INFO
        )
        
        # 錯誤日誌記錄器
        self.loggers['error'] = self._create_logger(
            'error',
            self.log_dir / 'error.log',
            logging.ERROR
        )
        
        # 審計日誌記錄器
        self.loggers['audit'] = self._create_logger(
            'audit',
            self.log_dir / 'audit.log',
            logging.INFO
        )
        
        # 性能日誌記錄器
        self.loggers['performance'] = self._create_logger(
            'performance',
            self.log_dir / 'performance.log',
            logging.INFO
        )
        
        # 安全日誌記錄器
        self.loggers['security'] = self._create_logger(
            'security',
            self.log_dir / 'security.log',
            logging.WARNING
        )
    
    def _create_logger(self, name: str, filepath: Path, level: int) -> logging.Logger:
        """創建日誌記錄器"""
        logger = logging.getLogger(f"{self.name}.{name}")
        logger.setLevel(level)
        
        # 避免重複添加處理器
        if logger.handlers:
            return logger
        
        # 文件處理器（JSON 格式）
        file_handler = logging.FileHandler(filepath, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(JsonFormatter())
        
        # 控制台處理器（可讀格式）
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(ReadableFormatter())
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        # 防止日誌傳播到根記錄器
        logger.propagate = False
        
        return logger
    
    def _log(self, level: LogLevel, category: LogCategory, message: str, 
             extra: Optional[Dict[str, Any]] = None, exc_info: Optional[Exception] = None):
        """記錄日誌"""
        # 構建日誌數據
        log_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': level.value,
            'category': category.value,
            'message': message,
            'request_id': request_id.get(),
            'user_id': user_id.get(),
            'session_id': session_id.get(),
            'service': self.name,
            **(extra or {})
        }
        
        # 添加異常信息
        if exc_info:
            log_data['exception'] = {
                'type': type(exc_info).__name__,
                'message': str(exc_info),
                'traceback': traceback.format_exc()
            }
            
            # 更新錯誤統計
            self.error_stats['total_errors'] += 1
            self.error_stats['by_category'][category.value] += 1
            self.error_stats['by_level'][level.value] += 1
            
            # 記錄最近錯誤
            error_record = {
                'timestamp': log_data['timestamp'],
                'category': category.value,
                'level': level.value,
                'message': message,
                'exception_type': type(exc_info).__name__
            }
            self.error_stats['recent_errors'].append(error_record)
            
            # 只保留最近100個錯誤
            if len(self.error_stats['recent_errors']) > 100:
                self.error_stats['recent_errors'].pop(0)
        
        # 選擇合適的記錄器
        if category == LogCategory.AUDIT:
            logger = self.loggers['audit']
        elif category == LogCategory.SECURITY:
            logger = self.loggers['security']
        elif category == LogCategory.PERFORMANCE:
            logger = self.loggers['performance']
        elif level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            logger = self.loggers['error']
        else:
            logger = self.loggers['main']
        
        # 記錄日誌
        getattr(logger, level.value.lower())(json.dumps(log_data, ensure_ascii=False))
    
    def debug(self, message: str, category: LogCategory = LogCategory.SYSTEM, 
              extra: Optional[Dict[str, Any]] = None):
        """記錄調試日誌"""
        self._log(LogLevel.DEBUG, category, message, extra)
    
    def info(self, message: str, category: LogCategory = LogCategory.SYSTEM, 
             extra: Optional[Dict[str, Any]] = None):
        """記錄信息日誌"""
        self._log(LogLevel.INFO, category, message, extra)
    
    def warning(self, message: str, category: LogCategory = LogCategory.SYSTEM, 
                extra: Optional[Dict[str, Any]] = None):
        """記錄警告日誌"""
        self._log(LogLevel.WARNING, category, message, extra)
    
    def error(self, message: str, category: LogCategory = LogCategory.SYSTEM, 
              extra: Optional[Dict[str, Any]] = None, exc_info: Optional[Exception] = None):
        """記錄錯誤日誌"""
        self._log(LogLevel.ERROR, category, message, extra, exc_info)
    
    def critical(self, message: str, category: LogCategory = LogCategory.SYSTEM, 
                 extra: Optional[Dict[str, Any]] = None, exc_info: Optional[Exception] = None):
        """記錄嚴重錯誤日誌"""
        self._log(LogLevel.CRITICAL, category, message, extra, exc_info)
    
    def audit(self, action: str, resource: str, user_id: str, 
              result: str = "success", extra: Optional[Dict[str, Any]] = None):
        """記錄審計日誌"""
        audit_data = {
            'action': action,
            'resource': resource,
            'user_id': user_id,
            'result': result,
            **(extra or {})
        }
        self._log(LogLevel.INFO, LogCategory.AUDIT, f"審計: {action} on {resource}", audit_data)
    
    def security(self, event: str, severity: str = "medium", 
                 source: Optional[str] = None, extra: Optional[Dict[str, Any]] = None):
        """記錄安全日誌"""
        security_data = {
            'security_event': event,
            'severity': severity,
            'source': source,
            **(extra or {})
        }
        self._log(LogLevel.WARNING, LogCategory.SECURITY, f"安全事件: {event}", security_data)
    
    def performance(self, operation: str, duration: float, 
                    metrics: Optional[Dict[str, Any]] = None):
        """記錄性能日誌"""
        perf_data = {
            'operation': operation,
            'duration_ms': duration * 1000,
            **(metrics or {})
        }
        
        # 如果性能不佳，記錄為警告
        if duration > 1.0:  # 超過1秒
            self._log(LogLevel.WARNING, LogCategory.PERFORMANCE, 
                     f"性能警告: {operation} 耗時 {duration:.2f}秒", perf_data)
        else:
            self._log(LogLevel.INFO, LogCategory.PERFORMANCE, 
                     f"性能: {operation} 耗時 {duration:.2f}秒", perf_data)
    
    def api_request(self, method: str, endpoint: str, status_code: int, 
                   duration: float, user_id: Optional[str] = None, 
                   extra: Optional[Dict[str, Any]] = None):
        """記錄 API 請求日誌"""
        api_data = {
            'method': method,
            'endpoint': endpoint,
            'status_code': status_code,
            'duration_ms': duration * 1000,
            **(extra or {})
        }
        
        level = LogLevel.INFO
        if status_code >= 500:
            level = LogLevel.ERROR
        elif status_code >= 400:
            level = LogLevel.WARNING
        
        message = f"API {method} {endpoint} - {status_code} ({duration:.3f}s)"
        self._log(level, LogCategory.API, message, api_data)
    
    def get_error_stats(self) -> Dict[str, Any]:
        """獲取錯誤統計"""
        return {
            **self.error_stats,
            'error_rate': self._calculate_error_rate()
        }
    
    def _calculate_error_rate(self) -> float:
        """計算錯誤率"""
        # 簡化的錯誤率計算
        total_requests = sum(
            self.error_stats['by_level'][level.value] 
            for level in [LogLevel.ERROR, LogLevel.CRITICAL]
        )
        
        if total_requests == 0:
            return 0.0
        
        return min(1.0, total_requests / 1000)  # 假設基準為1000個請求
    
    async def cleanup_old_logs(self, days: int = 30):
        """清理舊日誌"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        for log_file in self.log_dir.glob("*.log*"):
            try:
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime, timezone.utc)
                if file_time < cutoff_date:
                    log_file.unlink()
                    self.info(f"已清理舊日誌文件: {log_file.name}", LogCategory.SYSTEM)
            except Exception as e:
                self.error(f"清理日誌文件失敗: {log_file.name}", LogCategory.SYSTEM, exc_info=e)

class JsonFormatter(logging.Formatter):
    """JSON 格式化器"""
    
    def format(self, record):
        # 如果記錄的消息已經是 JSON，直接返回
        try:
            json.loads(record.getMessage())
            return record.getMessage()
        except:
            # 否則包裝為 JSON
            log_data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'level': record.levelname,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }
            return json.dumps(log_data, ensure_ascii=False)

class ReadableFormatter(logging.Formatter):
    """可讀格式化器"""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

# 全局日誌記錄器實例
loggers = {}

def get_logger(name: str) -> EnterpriseLogger:
    """獲取日誌記錄器實例"""
    if name not in loggers:
        loggers[name] = EnterpriseLogger(name)
    return loggers[name]

# 裝飾器用於自動記錄
def log_execution(category: LogCategory = LogCategory.SYSTEM, 
                 level: LogLevel = LogLevel.INFO):
    """裝飾器：自動記錄函數執行"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start_time = datetime.now()
            
            try:
                result = await func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                
                logger._log(level, category, 
                          f"執行完成: {func.__name__} ({duration:.3f}s)",
                          {'function': func.__name__, 'duration': duration})
                
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                
                logger.error(f"執行失敗: {func.__name__} ({duration:.3f}s)",
                           category, exc_info=e,
                           extra={'function': func.__name__, 'duration': duration})
                raise
        
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start_time = datetime.now()
            
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                
                logger._log(level, category, 
                          f"執行完成: {func.__name__} ({duration:.3f}s)",
                          {'function': func.__name__, 'duration': duration})
                
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                
                logger.error(f"執行失敗: {func.__name__} ({duration:.3f}s)",
                           category, exc_info=e,
                           extra={'function': func.__name__, 'duration': duration})
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

# 上下文管理器用於設置請求上下文
class LogContext:
    """日誌上下文管理器"""
    
    def __init__(self, req_id: Optional[str] = None, usr_id: Optional[str] = None, 
                 sess_id: Optional[str] = None):
        self.req_id = req_id or str(uuid.uuid4())
        self.usr_id = usr_id
        self.sess_id = sess_id
        self.token_req = None
        self.token_usr = None
        self.token_sess = None
    
    def __enter__(self):
        self.token_req = request_id.set(self.req_id)
        self.token_usr = user_id.set(self.usr_id)
        self.token_sess = session_id.set(self.sess_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        request_id.reset(self.token_req)
        user_id.reset(self.token_usr)
        session_id.reset(self.token_sess)