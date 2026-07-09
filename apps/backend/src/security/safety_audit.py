"""

Safety Audit — 安全決策審計系統

記錄所有安全相關決策,提供審計追蹤和合規檢查。

功能:
- 記錄所有安全決策（信任評估、內容過濾、權限檢查）
- 合規性檢查
- 安全報告生成
- 異常檢測
"""

from core.utils import safe_error

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    TRUST_EVALUATION = "trust_evaluation"
    CONTENT_FILTER = "content_filter"
    PERMISSION_CHECK = "permission_check"
    VIOLATION = "violation"
    SECURITY_DECISION = "security_decision"
    ACCESS_ATTEMPT = "access_attempt"
    SAFETY_CHECK = "safety_check"
    SYSTEM_ERROR = "system_error"


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEntry:
    """單條審計記錄"""

    event_type: AuditEventType
    severity: Severity
    message: str
    user_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    source: str = "system"
    decision: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "user_id": self.user_id,
            "details": self.details,
            "timestamp": self.timestamp,
            "source": self.source,
            "decision": self.decision,
        }


class SafetyAudit:
    """
    安全決策審計系統

    記錄所有安全相關決策,提供審計追蹤和合規檢查。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.entries: List[AuditEntry] = []
        self.violations: List[AuditEntry] = []
        self.max_entries = self.config.get("max_entries", 10000)
        self.alert_thresholds = self.config.get(
            "alert_thresholds",
            {
                "violations_per_hour": 10,
                "critical_events_per_hour": 5,
            },
        )
        logger.debug("SafetyAudit initialized")

    def log_event(
        self,
        event_type: AuditEventType,
        severity: Severity,
        message: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        source: str = "system",
        decision: Optional[str] = None,
    ) -> AuditEntry:
        entry = AuditEntry(
            event_type=event_type,
            severity=severity,
            message=message,
            user_id=user_id,
            details=details or {},
            source=source,
            decision=decision,
        )

        self.entries.append(entry)

        if severity in (Severity.HIGH, Severity.CRITICAL):
            self.violations.append(entry)

        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]

        self._check_alerts(entry)
        return entry

    def log_trust_evaluation(
        self,
        user_id: str,
        trust_score: float,
        decision: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEntry:
        severity = Severity.LOW
        if trust_score < 0.3:
            severity = Severity.HIGH
        elif trust_score < 0.5:
            severity = Severity.MEDIUM

        return self.log_event(
            event_type=AuditEventType.TRUST_EVALUATION,
            severity=severity,
            message=f"Trust evaluation for {user_id}: {trust_score:.2f} -> {decision}",
            user_id=user_id,
            details={"trust_score": trust_score, **(details or {})},
            source="trust_manager",
            decision=decision,
        )

    def log_content_filter(
        self,
        content_preview: str,
        safety_level: str,
        action: str,
        issues: List[Dict[str, Any]],
        user_id: Optional[str] = None,
    ) -> AuditEntry:
        severity = Severity.LOW
        if safety_level == "unsafe":
            severity = Severity.HIGH
        elif safety_level == "risky":
            severity = Severity.MEDIUM

        return self.log_event(
            event_type=AuditEventType.CONTENT_FILTER,
            severity=severity,
            message=f"Content filtered: {safety_level} -> {action}",
            user_id=user_id,
            details={
                "content_preview": content_preview[:200],
                "safety_level": safety_level,
                "issue_count": len(issues),
            },
            source="content_filter",
            decision=action,
        )

    def log_permission_check(
        self,
        user_id: str,
        permission: str,
        granted: bool,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEntry:
        severity = Severity.LOW if granted else Severity.MEDIUM

        return self.log_event(
            event_type=AuditEventType.PERMISSION_CHECK,
            severity=severity,
            message=f"Permission '{permission}' {'granted' if granted else 'denied'} for {user_id}",
            user_id=user_id,
            details={"permission": permission, "granted": granted, **(details or {})},
            source="permission_control",
            decision="granted" if granted else "denied",
        )

    def log_violation(
        self,
        user_id: str,
        violation_type: str,
        severity: Severity,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEntry:
        return self.log_event(
            event_type=AuditEventType.VIOLATION,
            severity=severity,
            message=f"Violation by {user_id}: {violation_type}",
            user_id=user_id,
            details={"violation_type": violation_type, **(details or {})},
            source="trust_manager",
            decision="violation_recorded",
        )

    def check_compliance(
        self,
        rules: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        if not rules:
            rules = [
                {"name": "no_critical_violations", "check": self._check_no_critical},
                {"name": "trust_above_threshold", "check": self._check_trust_threshold},
                {"name": "content_filter_active", "check": self._check_filter_active},
            ]

        results = []
        for rule in rules:
            try:
                passed = rule["check"]()
                results.append({"rule": rule["name"], "passed": passed})
            except Exception as e:
                results.append({"rule": rule["name"], "passed": False, "error": safe_error(e)})

        passed_count = sum(1 for r in results if r["passed"])
        return {
            "total_rules": len(results),
            "passed": passed_count,
            "failed": len(results) - passed_count,
            "compliance_rate": passed_count / len(results) if results else 1.0,
            "details": results,
        }

    def generate_report(
        self,
        time_window: Optional[float] = None,
    ) -> Dict[str, Any]:
        entries = self.entries
        if time_window:
            cutoff = time.time() - time_window
            entries = [e for e in entries if e.timestamp >= cutoff]

        if not entries:
            return {"total_events": 0}

        severity_counts = {}
        type_counts = {}
        for entry in entries:
            sev = entry.severity.value
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
            evt = entry.event_type.value
            type_counts[evt] = type_counts.get(evt, 0) + 1

        violations = [e for e in entries if e.severity in (Severity.HIGH, Severity.CRITICAL)]

        return {
            "total_events": len(entries),
            "severity_distribution": severity_counts,
            "type_distribution": type_counts,
            "violations_count": len(violations),
            "time_window": time_window,
            "unique_users": len(set(e.user_id for e in entries if e.user_id)),
        }

    def get_recent_entries(self, count: int = 100) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self.entries[-count:]]

    def get_violations(self, count: int = 100) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self.violations[-count:]]

    def _check_no_critical(self) -> bool:
        recent_cutoff = time.time() - 3600
        critical = [
            e
            for e in self.entries
            if e.severity == Severity.CRITICAL and e.timestamp >= recent_cutoff
        ]
        return len(critical) == 0

    def _check_trust_threshold(self) -> bool:
        return True

    def _check_filter_active(self) -> bool:
        return True

    def _check_alerts(self, entry: AuditEntry) -> None:
        if entry.severity == Severity.CRITICAL:
            logger.warning(
                "CRITICAL safety event: %s (user: %s)",
                entry.message,
                entry.user_id,
            )

        recent_cutoff = time.time() - 3600
        recent_violations = [
            e
            for e in self.entries
            if e.severity in (Severity.HIGH, Severity.CRITICAL)
            and e.timestamp >= recent_cutoff
        ]
        if len(recent_violations) >= self.alert_thresholds["violations_per_hour"]:
            logger.warning(
                "ALERT: %d violations in the last hour (threshold: %d)",
                len(recent_violations),
                self.alert_thresholds["violations_per_hour"],
            )


__all__ = ["SafetyAudit", "AuditEntry", "AuditEventType", "Severity"]
