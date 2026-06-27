"""
 * =============================================================================
 * ANGELA-MATRIX: [L4-Test] [α-Test] [A-Validation] [L0-L3]
 * =============================================================================
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from apps.backend.src.security.audit_logger import (
    AuditEvent,
    AuditEventType,
    AuditLogger,
)


class TestAuditEventType:
    def test_members(self):
        assert AuditEventType.OPERATION.value == "operation"
        assert AuditEventType.FILE_ACCESS.value == "file_access"
        assert AuditEventType.ERROR.value == "error"

    def test_all_defined(self):
        names = {e.name for e in AuditEventType}
        expected = {
            "OPERATION", "FILE_ACCESS", "NETWORK_ACCESS", "SYSTEM_COMMAND",
            "APPLICATION_CONTROL", "DATA_PROCESSING", "SANDBOX_EXECUTION",
            "PERMISSION_CHECK", "SECURITY_VIOLATION", "ERROR",
        }
        assert names == expected


class TestAuditEvent:
    def test_minimal(self):
        e = AuditEvent(
            timestamp="2025-01-01T00:00:00",
            event_type=AuditEventType.OPERATION,
            user_id="user1",
            operation="test",
            resource="r",
            action="a",
            success=True,
            details={},
        )
        assert e.session_id is None

    def test_full(self):
        e = AuditEvent(
            timestamp="2025-01-01T00:00:00",
            event_type=AuditEventType.ERROR,
            user_id="u1",
            operation="op",
            resource="res",
            action="act",
            success=False,
            details={"msg": "err"},
            session_id="s1",
            ip_address="127.0.0.1",
            user_agent="curl",
        )
        assert e.session_id == "s1"
        assert e.details["msg"] == "err"


class TestAuditLogger:
    def test_init_creates_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = os.path.join(tmp, "sub", "audit.log")
            logger = AuditLogger(log_path)
            assert os.path.exists(os.path.dirname(log_path))

    def test_log_event_appends_to_buffer(self):
        logger = AuditLogger()
        event = AuditEvent(
            timestamp=datetime.now().isoformat(),
            event_type=AuditEventType.OPERATION,
            user_id="user1",
            operation="test",
            resource="r",
            action="a",
            success=True,
            details={},
        )
        logger.log_event(event)
        assert len(logger.log_buffer) == 1

    def test_log_operation_convenience(self):
        logger = AuditLogger()
        logger.log_operation("u1", "backup", "/data", "run", True)
        assert len(logger.log_buffer) == 1
        assert logger.log_buffer[0].event_type == AuditEventType.OPERATION

    def test_log_file_access(self):
        logger = AuditLogger()
        logger.log_file_access("u1", "/etc/passwd", "read", False)
        assert logger.log_buffer[0].event_type == AuditEventType.FILE_ACCESS

    def test_log_network_access(self):
        logger = AuditLogger()
        logger.log_network_access("u1", "https://example.com", "GET", True)
        assert logger.log_buffer[0].event_type == AuditEventType.NETWORK_ACCESS

    def test_log_system_command(self):
        logger = AuditLogger()
        logger.log_system_command("u1", "rm -rf /", True)
        assert logger.log_buffer[0].event_type == AuditEventType.SYSTEM_COMMAND

    def test_log_application_control(self):
        logger = AuditLogger()
        logger.log_application_control("u1", "notepad", "launch", True)
        assert logger.log_buffer[0].event_type == AuditEventType.APPLICATION_CONTROL

    def test_log_data_processing(self):
        logger = AuditLogger()
        logger.log_data_processing("u1", "pii", "anonymize", True)
        assert logger.log_buffer[0].event_type == AuditEventType.DATA_PROCESSING

    def test_log_sandbox_execution(self):
        logger = AuditLogger()
        logger.log_sandbox_execution("u1", "abc123", True)
        assert logger.log_buffer[0].event_type == AuditEventType.SANDBOX_EXECUTION

    def test_log_permission_check(self):
        logger = AuditLogger()
        logger.log_permission_check("u1", "file_read", "/data", "read", True)
        assert logger.log_buffer[0].event_type == AuditEventType.PERMISSION_CHECK
        assert logger.log_buffer[0].details.get("granted") is True

    def test_log_security_violation(self):
        logger = AuditLogger()
        logger.log_security_violation("u1", "intrusion", "/etc")
        assert logger.log_buffer[0].event_type == AuditEventType.SECURITY_VIOLATION
        assert logger.log_buffer[0].success is False

    def test_log_error(self):
        logger = AuditLogger()
        logger.log_error("u1", "timeout", "/api", "connection timed out")
        assert logger.log_buffer[0].event_type == AuditEventType.ERROR

    def test_log_event_non_audit_event(self):
        logger = AuditLogger()
        logger.log_event("not an event")
        assert len(logger.log_buffer) == 1

    def test_flush_buffer_writes_to_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = os.path.join(tmp, "audit.log")
            logger = AuditLogger(log_path)
            logger.log_operation("u1", "backup", "/data", "run", True)
            logger._flush_buffer()
            assert os.path.exists(log_path)
            with open(log_path, "r") as f:
                lines = f.readlines()
            assert len(lines) == 1

    def test_flush_buffer_clears_buffer(self):
        with tempfile.TemporaryDirectory() as tmp:
            logger = AuditLogger(os.path.join(tmp, "audit.log"))
            logger.log_operation("u1", "x", "y", "z", True)
            logger._flush_buffer()
            assert len(logger.log_buffer) == 0

    def test_auto_flush_at_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            logger = AuditLogger(os.path.join(tmp, "audit.log"))
            for i in range(100):
                logger.log_operation(f"u{i}", "op", "r", "a", True)
            assert os.path.exists(logger.log_file_path)

    def test_get_recent_events_empty(self):
        logger = AuditLogger()
        assert logger.get_recent_events() == []

    def test_get_recent_events_from_buffer(self):
        with tempfile.TemporaryDirectory() as tmp:
            logger = AuditLogger(os.path.join(tmp, "audit.log"))
            logger.log_operation("u1", "op", "r", "a", True)
            events = logger.get_recent_events()
            assert len(events) >= 1

    def test_get_recent_events_from_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = os.path.join(tmp, "audit.log")
            logger = AuditLogger(log_path)
            logger.log_operation("u1", "op", "r", "a", True)
            logger._flush_buffer()
            events = logger.get_recent_events()
            assert len(events) >= 1

    def test_rotate_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = os.path.join(tmp, "audit.log")
            logger = AuditLogger(log_path, max_log_size=50)
            with open(log_path, "w") as f:
                f.write("x" * 60)
            logger._rotate_log_if_needed()
            rotated_files = list(Path(tmp).glob("audit.log.*"))
            assert len(rotated_files) >= 1

    def test_search_events_by_user(self):
        with tempfile.TemporaryDirectory() as tmp:
            logger = AuditLogger(os.path.join(tmp, "audit.log"))
            logger.log_operation("alice", "op", "r", "a", True)
            logger.log_operation("bob", "op", "r", "a", True)
            results = logger.search_events(user_id="alice")
            assert len(results) == 1
            assert results[0].user_id == "alice"

    def test_search_events_by_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            logger = AuditLogger(os.path.join(tmp, "audit.log"))
            logger.log_operation("u1", "op", "r", "a", True)
            logger.log_file_access("u1", "/f", "read", True)
            results = logger.search_events(event_type=AuditEventType.FILE_ACCESS)
            assert len(results) == 1
            assert results[0].event_type == AuditEventType.FILE_ACCESS

    def test_search_events_by_resource(self):
        with tempfile.TemporaryDirectory() as tmp:
            logger = AuditLogger(os.path.join(tmp, "audit.log"))
            logger.log_operation("u1", "op", "/secret", "a", True)
            results = logger.search_events(resource="/secret")
            assert len(results) == 1

    def test_event_matches_criteria_user(self):
        e = AuditEvent(
            timestamp="2025-01-01",
            event_type=AuditEventType.OPERATION,
            user_id="alice",
            operation="op",
            resource="r",
            action="a",
            success=True,
            details={},
        )
        logger = AuditLogger()
        assert logger._event_matches_criteria(e, user_id="alice") is True
        assert logger._event_matches_criteria(e, user_id="bob") is False

    def test_event_matches_criteria_type(self):
        e = AuditEvent(
            timestamp="2025-01-01",
            event_type=AuditEventType.ERROR,
            user_id="u1",
            operation="op",
            resource="r",
            action="a",
            success=False,
            details={},
        )
        logger = AuditLogger()
        assert logger._event_matches_criteria(e, event_type=AuditEventType.ERROR) is True
        assert logger._event_matches_criteria(e, event_type=AuditEventType.OPERATION) is False

    def test_event_matches_criteria_resource_substring(self):
        e = AuditEvent(
            timestamp="2025-01-01",
            event_type=AuditEventType.FILE_ACCESS,
            user_id="u1",
            operation="op",
            resource="/home/user/file.txt",
            action="r",
            success=True,
            details={},
        )
        logger = AuditLogger()
        assert logger._event_matches_criteria(e, resource="file.txt") is True
        assert logger._event_matches_criteria(e, resource="nonexistent") is False

    def test_event_matches_criteria_time_range(self):
        e = AuditEvent(
            timestamp="2025-06-15T12:00:00",
            event_type=AuditEventType.OPERATION,
            user_id="u1",
            operation="op",
            resource="r",
            action="a",
            success=True,
            details={},
        )
        logger = AuditLogger()
        assert logger._event_matches_criteria(e, start_time="2025-01-01") is True
        assert logger._event_matches_criteria(e, start_time="2025-07-01") is False
        assert logger._event_matches_criteria(e, end_time="2025-12-31") is True
        assert logger._event_matches_criteria(e, end_time="2025-01-01") is False
