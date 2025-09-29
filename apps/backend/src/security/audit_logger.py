# src/security/audit_logger.py
"""
Audit Logging System for AI Operations
Records all AI operations for security monitoring and compliance
"""

import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from pathlib import Path

logger: Any = logging.getLogger(__name__)

class AuditEventType(Enum):
    """Types of audit events"""
    OPERATION = "operation"
    FILE_ACCESS = "file_access"
    NETWORK_ACCESS = "network_access"
    SYSTEM_COMMAND = "system_command"
    APPLICATION_CONTROL = "application_control"
    DATA_PROCESSING = "data_processing"
    SANDBOX_EXECUTION = "sandbox_execution"
    PERMISSION_CHECK = "permission_check"
    SECURITY_VIOLATION = "security_violation"
    ERROR = "error"

@dataclass
class AuditEvent:
    """An audit event record"""
    timestamp: str
    event_type: AuditEventType
    user_id: str
    operation: str
    resource: str
    action: str
    success: bool
    details: Dict[str, Any]
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class AuditLogger:
    """Main audit logging system"""
    
    def __init__(self, log_file_path: Optional[str] = None, max_log_size: int = 10000) -> None:
        self.log_file_path = log_file_path or "logs/audit.log"
        self.max_log_size = max_log_size
        self.log_buffer: List[AuditEvent] = 
        self.buffer_lock = threading.Lock
        self.file_lock = threading.Lock
        
        # Ensure log directory exists
        log_dir = Path(self.log_file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"AuditLogger initialized with log file: {self.log_file_path}")
        
    def log_event(self, event: AuditEvent):
        """Log an audit event"""
        try:
            # Add to buffer
            with self.buffer_lock:
                self.log_buffer.append(event)
                
            # Flush if buffer is full
            if len(self.log_buffer) >= 100:  # Flush every 100 events
                self._flush_buffer
                
        except Exception as e:
            logger.error(f"Error logging audit event: {e}")
            
    def log_operation(self, user_id: str, operation: str, resource: str, 
                     action: str, success: bool, details: Optional[Dict[str, Any]] = None,
                     session_id: Optional[str] = None, ip_address: Optional[str] = None, 
                     user_agent: Optional[str] = None):
        """Log a general operation"""
        event = AuditEvent(
            timestamp=datetime.now.isoformat,
            event_type=AuditEventType.OPERATION,
            user_id=user_id,
            operation=operation,
            resource=resource,
            action=action,
            success=success,
            details=details or ,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.log_event(event)
        
    def log_file_access(self, user_id: str, file_path: str, action: str, 
                       success: bool, details: Optional[Dict[str, Any]] = None,
                       session_id: Optional[str] = None, ip_address: Optional[str] = None, 
                       user_agent: Optional[str] = None):
        """Log file access"""
        event = AuditEvent(
            timestamp=datetime.now.isoformat,
            event_type=AuditEventType.FILE_ACCESS,
            user_id=user_id,
            operation="file_access",
            resource=file_path,
            action=action,
            success=success,
            details=details or ,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.log_event(event)
        
    def log_network_access(self, user_id: str, url: str, action: str, 
                          success: bool, details: Optional[Dict[str, Any]] = None,
                          session_id: Optional[str] = None, ip_address: Optional[str] = None, 
                          user_agent: Optional[str] = None):
        """Log network access"""
        event = AuditEvent(
            timestamp=datetime.now.isoformat,
            event_type=AuditEventType.NETWORK_ACCESS,
            user_id=user_id,
            operation="network_access",
            resource=url,
            action=action,
            success=success,
            details=details or ,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.log_event(event)
        
    def log_system_command(self, user_id: str, command: str, success: bool, 
                          details: Optional[Dict[str, Any]] = None,
                          session_id: Optional[str] = None, ip_address: Optional[str] = None, 
                          user_agent: Optional[str] = None):
        """Log system command execution"""
        event = AuditEvent(
            timestamp=datetime.now.isoformat,
            event_type=AuditEventType.SYSTEM_COMMAND,
            user_id=user_id,
            operation="system_command",
            resource=command,
            action="execute",
            success=success,
            details=details or ,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.log_event(event)
        
    def log_application_control(self, user_id: str, app_name: str, action: str, 
                               success: bool, details: Optional[Dict[str, Any]] = None,
                               session_id: Optional[str] = None, ip_address: Optional[str] = None, 
                               user_agent: Optional[str] = None):
        """Log application control"""
        event = AuditEvent(
            timestamp=datetime.now.isoformat,
            event_type=AuditEventType.APPLICATION_CONTROL,
            user_id=user_id,
            operation="application_control",
            resource=app_name,
            action=action,
            success=success,
            details=details or ,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.log_event(event)
        
    def log_data_processing(self, user_id: str, data_type: str, action: str, 
                           success: bool, details: Optional[Dict[str, Any]] = None,
                           session_id: Optional[str] = None, ip_address: Optional[str] = None, 
                           user_agent: Optional[str] = None):
        """Log data processing"""
        event = AuditEvent(
            timestamp=datetime.now.isoformat,
            event_type=AuditEventType.DATA_PROCESSING,
            user_id=user_id,
            operation="data_processing",
            resource=data_type,
            action=action,
            success=success,
            details=details or ,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.log_event(event)
        
    def log_sandbox_execution(self, user_id: str, script_hash: str, success: bool, 
                             details: Optional[Dict[str, Any]] = None,
                             session_id: Optional[str] = None, ip_address: Optional[str] = None, 
                             user_agent: Optional[str] = None):
        """Log sandbox execution"""
        event = AuditEvent(
            timestamp=datetime.now.isoformat,
            event_type=AuditEventType.SANDBOX_EXECUTION,
            user_id=user_id,
            operation="sandbox_execution",
            resource=script_hash,
            action="execute",
            success=success,
            details=details or ,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.log_event(event)
        
    def log_permission_check(self, user_id: str, permission_type: str, 
                            resource: str, action: str, granted: bool,
                            details: Optional[Dict[str, Any]] = None,
                            session_id: Optional[str] = None, ip_address: Optional[str] = None, 
                            user_agent: Optional[str] = None):
        """Log permission check"""
        event = AuditEvent(
            timestamp=datetime.now.isoformat,
            event_type=AuditEventType.PERMISSION_CHECK,
            user_id=user_id,
            operation="permission_check",
            resource=resource,
            action=action,
            success=granted,
            details={
                "permission_type": permission_type,
                "granted": granted,
                **(details or )
            },
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.log_event(event)
        
    def log_security_violation(self, user_id: str, violation_type: str, 
                              resource: str, details: Optional[Dict[str, Any]] = None,
                              session_id: Optional[str] = None, ip_address: Optional[str] = None, 
                              user_agent: Optional[str] = None):
        """Log security violation"""
        event = AuditEvent(
            timestamp=datetime.now.isoformat,
            event_type=AuditEventType.SECURITY_VIOLATION,
            user_id=user_id,
            operation="security_violation",
            resource=resource,
            action=violation_type,
            success=False,
            details=details or ,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.log_event(event)
        
    def log_error(self, user_id: str, error_type: str, resource: str, 
                 error_message: str, details: Optional[Dict[str, Any]] = None,
                 session_id: Optional[str] = None, ip_address: Optional[str] = None, 
                 user_agent: Optional[str] = None):
        """Log error"""
        event = AuditEvent(
            timestamp=datetime.now.isoformat,
            event_type=AuditEventType.ERROR,
            user_id=user_id,
            operation="error",
            resource=resource,
            action=error_type,
            success=False,
            details={
                "error_message": error_message,
                **(details or )
            },
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.log_event(event)
        
    def _flush_buffer(self):
        """Flush the log buffer to file"""
        try:
            with self.buffer_lock:
                if not self.log_buffer:
                    return
                    
                events_to_write = self.log_buffer.copy
                self.log_buffer.clear
                
            # Write to file with file locking
            with self.file_lock:
                # Check file size and rotate if necessary
                self._rotate_log_if_needed
                
                # Append events to log file
                with open(self.log_file_path, 'a', encoding='utf-8') as f:
                    for event in events_to_write:
                        # Convert AuditEvent to dictionary and handle enum serialization
                        event_dict = asdict(event)
                        event_dict['event_type'] = event_dict['event_type'].value
                        f.write(json.dumps(event_dict, ensure_ascii=False) + '\n')
                        
        except Exception as e:
            logger.error(f"Error flushing audit log buffer: {e}")
            
    def _rotate_log_if_needed(self):
        """Rotate log file if it exceeds maximum size"""
        try:
            if os.path.exists(self.log_file_path):
                file_size = os.path.getsize(self.log_file_path)
                if file_size > self.max_log_size:
                    # Rotate log file
                    rotated_path = f"{self.log_file_path}.{datetime.now.strftime('%Y%m%d_%H%M%S')}"
                    os.rename(self.log_file_path, rotated_path)
                    logger.info(f"Rotated audit log file to {rotated_path}")
        except Exception as e:
            logger.error(f"Error rotating audit log file: {e}")
            
    def get_recent_events(self, limit: int = 100) -> List[AuditEvent]:
        """Get recent audit events from buffer and file"""
        try:
            events = 
            
            # Get events from buffer
            with self.buffer_lock:
                events.extend(self.log_buffer[-limit:])
                
            # Get events from file
            if os.path.exists(self.log_file_path):
                with open(self.log_file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines
                    for line in reversed(lines[-(limit-len(events)):]):
                        try:
                            event_data = json.loads(line.strip)
                            # Convert event_type back to enum
                            event_data['event_type'] = AuditEventType(event_data['event_type'])
                            event = AuditEvent(**event_data)
                            events.append(event)
                        except Exception as e:
                            logger.error(f"Error parsing audit log line: {e}")
                            
            return events[-limit:]
        except Exception as e:
            logger.error(f"Error getting recent audit events: {e}")
            return 
            
    def search_events(self, user_id: Optional[str] = None, event_type: Optional[AuditEventType] = None, 
                     resource: Optional[str] = None, start_time: Optional[str] = None, 
                     end_time: Optional[str] = None) -> List[AuditEvent]:
        """Search audit events based on criteria"""
        try:
            events = 
            
            # Search in buffer
            with self.buffer_lock:
                for event in self.log_buffer:
                    if self._event_matches_criteria(event, user_id, event_type, resource, start_time, end_time):
                        events.append(event)
                        
            # Search in file
            if os.path.exists(self.log_file_path):
                with open(self.log_file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            event_data = json.loads(line.strip)
                            # Convert event_type back to enum
                            event_data['event_type'] = AuditEventType(event_data['event_type'])
                            event = AuditEvent(**event_data)
                            if self._event_matches_criteria(event, user_id, event_type, resource, start_time, end_time):
                                events.append(event)
                        except Exception as e:
                            logger.error(f"Error parsing audit log line: {e}")
                            
            return events
        except Exception as e:
            logger.error(f"Error searching audit events: {e}")
            return 
            
    def _event_matches_criteria(self, event: AuditEvent, user_id: Optional[str] = None, 
                               event_type: Optional[AuditEventType] = None, resource: Optional[str] = None,
                               start_time: Optional[str] = None, end_time: Optional[str] = None) -> bool:
        """Check if an event matches search criteria"""
        # Check user_id
        if user_id and event.user_id != user_id:
            return False
            
        # Check event_type
        if event_type and event.event_type != event_type:
            return False
            
        # Check resource
        if resource and resource not in event.resource:
            return False
            
        # Check time range
        if start_time and event.timestamp < start_time:
            return False
            
        if end_time and event.timestamp > end_time:
            return False
            
        return True