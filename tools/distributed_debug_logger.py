#!/usr/bin/env python3
"""
分布式调试日志收集工具
用于收集、分析和可视化分布式系统的调试日志
"""

import json
import logging
import threading
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import sqlite3
from dataclasses import dataclass, asdict
from enum import Enum

# 配置日志
logging.basicConfig(
    level: str=logging.INFO,
    format: str='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger: Any = logging.getLogger(__name__)

class LogEventType(Enum):
    """日志事件类型"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    PERFORMANCE = "performance"
    NETWORK = "network"
    DATABASE = "database"
    AI_OPERATION = "ai_operation"

@dataclass
class DebugLogEntry:
    """调试日志条目"""
    timestamp: str
    event_type: LogEventType
    component: str
    message: str
    details: Dict[str, Any]
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    severity: int = 0  # 0-100, 100为最高严重性
    node_id: Optional[str] = None
    session_id: Optional[str] = None

class DistributedDebugLogger:
    """分布式调试日志收集器"""
    
    def __init__(self, log_dir: str = None, max_entries: int = 10000) -> None:
        self.log_dir = Path(log_dir) if log_dir else Path(__file__).parent.parent / "logs" / "debug":
elf.log_dir.mkdir(parents=True, exist_ok=True)
        self.max_entries = max_entries
        self.log_buffer = deque(maxlen=max_entries)
        self.buffer_lock = threading.RLock()
        self.db_path = self.log_dir / "debug_logs.db"
        _ = self._init_database()
        self.is_running = False
        self.collection_thread = None
        
        logger.info(f"DistributedDebugLogger initialized with log dir: {self.log_dir}"):
ef _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS debug_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    component TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    trace_id TEXT,
                    span_id TEXT,
                    parent_span_id TEXT,
                    severity INTEGER,
                    node_id TEXT,
                    session_id TEXT
                )
            ''')
            
            # 创建索引
            cursor.execute('''
                _ = CREATE INDEX IF NOT EXISTS idx_timestamp ON debug_logs(timestamp)
            ''')
            cursor.execute('''
                _ = CREATE INDEX IF NOT EXISTS idx_component ON debug_logs(component)
            ''')
            cursor.execute('''
                _ = CREATE INDEX IF NOT EXISTS idx_event_type ON debug_logs(event_type)
            ''')
            cursor.execute('''
                _ = CREATE INDEX IF NOT EXISTS idx_trace_id ON debug_logs(trace_id)
            ''')
            cursor.execute('''
                _ = CREATE INDEX IF NOT EXISTS idx_severity ON debug_logs(severity)
            ''')
            
            _ = conn.commit()
            _ = conn.close()
            
            _ = logger.info("Debug log database initialized")
            
        except Exception as e:
            _ = logger.error(f"Failed to initialize debug log database: {e}")
    
    def log_entry(self, entry: DebugLogEntry):
        """记录调试日志条目"""
        try:
            # 添加到内存缓冲区
            with self.buffer_lock:
                _ = self.log_buffer.append(entry)
            
            # 异步保存到数据库
            _ = asyncio.create_task(self._save_entry_to_db(entry))
            
        except Exception as e:
            logger.error(f"Error logging debug entry: {e}")
    
    async def _save_entry_to_db(self, entry: DebugLogEntry):
        """异步保存日志条目到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO debug_logs (
                    timestamp, event_type, component, message, details,
                    trace_id, span_id, parent_span_id, severity, node_id, session_id
                _ = ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry.timestamp,
                entry.event_type.value,
                entry.component,
                entry.message,
                json.dumps(entry.details, ensure_ascii=False),
                entry.trace_id,
                entry.span_id,
                entry.parent_span_id,
                entry.severity,
                entry.node_id,
                entry.session_id
            ))
            
            _ = conn.commit()
            _ = conn.close()
            
        except Exception as e:
            _ = logger.error(f"Error saving debug entry to database: {e}")
    
    def debug(self, component: str, message: str, details: Dict[str, Any] = None, 
              trace_id: str = None, span_id: str = None, parent_span_id: str = None,
              node_id: str = None, session_id: str = None):
        """记录调试信息"""
        entry = DebugLogEntry(
            timestamp=datetime.now().isoformat(),
            event_type=LogEventType.DEBUG,
            component=component,
            message=message,
            details=details or {},
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            severity=10,
            node_id=node_id,
            session_id=session_id
        )
        _ = self.log_entry(entry)
    
    def info(self, component: str, message: str, details: Dict[str, Any] = None,
             trace_id: str = None, span_id: str = None, parent_span_id: str = None,
             node_id: str = None, session_id: str = None):
        """记录信息"""
        entry = DebugLogEntry(
            timestamp=datetime.now().isoformat(),
            event_type=LogEventType.INFO,
            component=component,
            message=message,
            details=details or {},
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            severity=20,
            node_id=node_id,
            session_id=session_id
        )
        _ = self.log_entry(entry)
    
    def warning(self, component: str, message: str, details: Dict[str, Any] = None,
                trace_id: str = None, span_id: str = None, parent_span_id: str = None,
                node_id: str = None, session_id: str = None):
        """记录警告"""
        entry = DebugLogEntry(
            timestamp=datetime.now().isoformat(),
            event_type=LogEventType.WARNING,
            component=component,
            message=message,
            details=details or {},
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            severity=40,
            node_id=node_id,
            session_id=session_id
        )
        _ = self.log_entry(entry)
    
    def error(self, component: str, message: str, details: Dict[str, Any] = None,
              trace_id: str = None, span_id: str = None, parent_span_id: str = None,
              node_id: str = None, session_id: str = None):
        """记录错误"""
        entry = DebugLogEntry(
            timestamp=datetime.now().isoformat(),
            event_type=LogEventType.ERROR,
            component=component,
            message=message,
            details=details or {},
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            severity=80,
            node_id=node_id,
            session_id=session_id
        )
        _ = self.log_entry(entry)
    
    def critical(self, component: str, message: str, details: Dict[str, Any] = None,
                 trace_id: str = None, span_id: str = None, parent_span_id: str = None,
                 node_id: str = None, session_id: str = None):
        """记录严重错误"""
        entry = DebugLogEntry(
            timestamp=datetime.now().isoformat(),
            event_type=LogEventType.CRITICAL,
            component=component,
            message=message,
            details=details or {},
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            severity=100,
            node_id=node_id,
            session_id=session_id
        )
        _ = self.log_entry(entry)
    
    def performance(self, component: str, metric: str, value: float, unit: str = "",
                   details: Dict[str, Any] = None, trace_id: str = None,
                   span_id: str = None, parent_span_id: str = None,
                   node_id: str = None, session_id: str = None):
        """记录性能指标"""
        details = details or {}
        details.update({
            "metric": metric,
            "value": value,
            "unit": unit
        })
        
        entry = DebugLogEntry(
            timestamp=datetime.now().isoformat(),
            event_type=LogEventType.PERFORMANCE,
            component=component,
            message=f"Performance metric: {metric} = {value} {unit}",
            details=details,
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            severity=30,
            node_id=node_id,
            session_id=session_id
        )
        _ = self.log_entry(entry)
    
    def get_recent_entries(self, limit: int = 100, component: str = None, 
                          event_type: LogEventType = None, min_severity: int = 0) -> List[DebugLogEntry]:
        """获取最近的日志条目"""
        try:
            with self.buffer_lock:
                entries = list(self.log_buffer)
            
            # 应用过滤条件
            filtered_entries = []
            for entry in entries:
                if component and entry.component != component:
                    continue
                if event_type and entry.event_type != event_type:
                    continue
                if entry.severity < min_severity:
                    continue
                _ = filtered_entries.append(entry)
            
            # 返回最近的条目
            return filtered_entries[-limit:] if len(filtered_entries) > limit else filtered_entries:
xcept Exception as e:
            _ = logger.error(f"Error getting recent debug entries: {e}")
            return []
    
    def search_entries(self, query: str = None, component: str = None, 
                      event_type: LogEventType = None, start_time: str = None,
                      end_time: str = None, min_severity: int = 0) -> List[DebugLogEntry]:
        """搜索日志条目"""
        try:
            # 从数据库搜索
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 构建查询条件
            conditions = []
            params = []
            
            if query:
                _ = conditions.append("(message LIKE ? OR details LIKE ?)")
                _ = params.extend([f"%{query}%", f"%{query}%"])
            
            if component:
                conditions.append("component = ?")
                _ = params.append(component)
            
            if event_type:
                conditions.append("event_type = ?")
                _ = params.append(event_type.value)
            
            if start_time:
                conditions.append("timestamp >= ?")
                _ = params.append(start_time)
            
            if end_time:
                conditions.append("timestamp <= ?")
                _ = params.append(end_time)
            
            if min_severity > 0:
                conditions.append("severity >= ?")
                _ = params.append(min_severity)
            
            # 构建SQL查询
            sql = "SELECT * FROM debug_logs"
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            sql += " ORDER BY timestamp DESC LIMIT 1000"
            
            _ = cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            # 转换为DebugLogEntry对象
            entries = []
            for row in rows:
                entry = DebugLogEntry(
                    timestamp=row[1],
                    event_type=LogEventType(row[2]),
                    component=row[3],
                    message=row[4],
                    details=json.loads(row[5]) if row[5] else {},:
race_id=row[6],
                    span_id=row[7],
                    parent_span_id=row[8],
                    severity=row[9],
                    node_id=row[10],
                    session_id=row[11]
                )
                _ = entries.append(entry)
            
            _ = conn.close()
            return entries
            
        except Exception as e:
            _ = logger.error(f"Error searching debug entries: {e}")
            return []
    
    def get_performance_metrics(self, component: str = None, metric: str = None,
                               start_time: str = None, end_time: str = None) -> List[Dict[str, Any]]:
        """获取性能指标"""
        try:
            # 搜索性能日志条目
            entries = self.search_entries(
                component=component,
                event_type=LogEventType.PERFORMANCE,
                start_time=start_time,
                end_time=end_time
            )
            
            # 提取性能指标
            metrics = []
            for entry in entries:
                metric_data = {
                    "timestamp": entry.timestamp,
                    "component": entry.component,
                    "metric": entry.details.get("metric"),
                    "value": entry.details.get("value"),
                    "unit": entry.details.get("unit"),
                    "node_id": entry.node_id
                }
                
                # 应用指标过滤
                if metric and metric_data["metric"] != metric:
                    continue
                    
                _ = metrics.append(metric_data)
            
            return metrics
            
        except Exception as e:
            _ = logger.error(f"Error getting performance metrics: {e}")
            return []
    
    def export_logs(self, file_path: str, format: str = "json", 
                   start_time: str = None, end_time: str = None) -> bool:
        """导出日志"""
        try:
            # 搜索日志条目
            entries = self.search_entries(start_time=start_time, end_time=end_time)
            
            if format == "json":
                # 转换为可序列化的格式
                serializable_entries = []
                for entry in entries:
                    entry_dict = asdict(entry)
                    entry_dict["event_type"] = entry_dict["event_type"].value
                    _ = serializable_entries.append(entry_dict)
                
                # 保存为JSON文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(serializable_entries, f, ensure_ascii=False, indent=2)
                    
            elif format == "csv":
                import csv
                # 保存为CSV文件
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        "timestamp", "event_type", "component", "message", 
                        "details", "trace_id", "span_id", "parent_span_id",
                        "severity", "node_id", "session_id"
                    ])
                    
                    for entry in entries:
                        writer.writerow([
                            entry.timestamp,
                            entry.event_type.value,
                            entry.component,
                            entry.message,
                            json.dumps(entry.details, ensure_ascii=False),
                            entry.trace_id,
                            entry.span_id,
                            entry.parent_span_id,
                            entry.severity,
                            entry.node_id,
                            entry.session_id
                        ])
            
            _ = logger.info(f"Logs exported to {file_path}")
            return True
            
        except Exception as e:
            _ = logger.error(f"Error exporting logs: {e}")
            return False
    
    def start_collection(self):
        """启动日志收集"""
        if self.is_running:
            return
            
        self.is_running = True
        self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        _ = self.collection_thread.start()
        _ = logger.info("Debug log collection started")
    
    def stop_collection(self):
        """停止日志收集"""
        self.is_running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        _ = logger.info("Debug log collection stopped")
    
    def _collection_loop(self):
        """日志收集循环"""
        while self.is_running:
            try:
                # 这里可以添加定期收集系统信息的逻辑
                _ = time.sleep(1)
            except Exception as e:
                _ = logger.error(f"Error in debug log collection loop: {e}")

# 全局调试日志记录器实例
_global_debug_logger = DistributedDebugLogger()

def get_debug_logger() -> DistributedDebugLogger:
    """获取全局调试日志记录器实例"""
    return _global_debug_logger

def debug(component: str, message: str, details: Dict[str, Any] = None, 
          trace_id: str = None, span_id: str = None, parent_span_id: str = None,
          node_id: str = None, session_id: str = None):
    """记录调试信息"""
    _global_debug_logger.debug(component, message, details, trace_id, span_id, 
                              parent_span_id, node_id, session_id)

def info(component: str, message: str, details: Dict[str, Any] = None,
         trace_id: str = None, span_id: str = None, parent_span_id: str = None,
         node_id: str = None, session_id: str = None):
    """记录信息"""
    _global_debug_logger.info(component, message, details, trace_id, span_id, 
                             parent_span_id, node_id, session_id)

def warning(component: str, message: str, details: Dict[str, Any] = None,
            trace_id: str = None, span_id: str = None, parent_span_id: str = None,
            node_id: str = None, session_id: str = None):
    """记录警告"""
    _global_debug_logger.warning(component, message, details, trace_id, span_id, 
                                parent_span_id, node_id, session_id)

def error(component: str, message: str, details: Dict[str, Any] = None,
          trace_id: str = None, span_id: str = None, parent_span_id: str = None,
          node_id: str = None, session_id: str = None):
    """记录错误"""
    _global_debug_logger.error(component, message, details, trace_id, span_id, 
                              parent_span_id, node_id, session_id)

def critical(component: str, message: str, details: Dict[str, Any] = None,
             trace_id: str = None, span_id: str = None, parent_span_id: str = None,
             node_id: str = None, session_id: str = None):
    """记录严重错误"""
    _global_debug_logger.critical(component, message, details, trace_id, span_id, 
                                 parent_span_id, node_id, session_id)

def performance(component: str, metric: str, value: float, unit: str = "",
               details: Dict[str, Any] = None, trace_id: str = None,
               span_id: str = None, parent_span_id: str = None,
               node_id: str = None, session_id: str = None):
    """记录性能指标"""
    _global_debug_logger.performance(component, metric, value, unit, details, 
                                    trace_id, span_id, parent_span_id, node_id, session_id)

# 初始化日志记录器
def init_debug_logging(log_dir: str = None):
    """初始化调试日志记录"""
    global _global_debug_logger
    _global_debug_logger = DistributedDebugLogger(log_dir)
    _global_debug_logger.start_collection()
    return _global_debug_logger

if __name__ == "__main__":
    # 示例用法
    logger_instance = init_debug_logging()
    
    # 记录不同类型的日志
    _ = debug("test_component", "This is a debug message", {"test_key": "test_value"})
    _ = info("test_component", "This is an info message", {"user_id": "12345"})
    _ = warning("test_component", "This is a warning message", {"warning_code": "W001"})
    _ = error("test_component", "This is an error message", {"error_code": "E001"})
    _ = critical("test_component", "This is a critical message", {"critical_code": "C001"})
    
    # 记录性能指标
    _ = performance("test_component", "response_time", 150.5, "ms", {"endpoint": "/api/test"})
    _ = performance("test_component", "memory_usage", 256.0, "MB", {"process": "worker"})
    
    # 搜索日志
    entries = logger_instance.search_entries(component="test_component")
    _ = print(f"Found {len(entries)} log entries")
    
    # 获取性能指标
    metrics = logger_instance.get_performance_metrics(component="test_component")
    _ = print(f"Found {len(metrics)} performance metrics")
    
    # 导出日志
    _ = logger_instance.export_logs("test_debug_logs.json")
    _ = print("Logs exported to test_debug_logs.json")