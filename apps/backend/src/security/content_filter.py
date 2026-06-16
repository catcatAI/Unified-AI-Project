"""
Content Filter — 內容安全過濾系統

過濾有害、有毒、包含 PII 的輸入/輸出內容。

功能:
- 毒性檢測（基於關鍵字和模式）
- PII 檢測（姓名、電話、Email、地址、身份證）
- 內容安全分級（safe / risky / unsafe）
- 自訂規則過濾
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SafetyLevel(Enum):
    SAFE = "safe"
    RISKY = "risky"
    UNSAFE = "unsafe"


class FilterAction(Enum):
    PASS = "pass"
    WARN = "warn"
    BLOCK = "block"
    SANITIZE = "sanitize"


@dataclass
class FilterResult:
    """過濾結果"""

    action: FilterAction
    safety_level: SafetyLevel
    issues: List[Dict[str, Any]]
    sanitized_content: Optional[str] = None
    original_content: str = ""
    confidence: float = 0.0

    @property
    def is_safe(self) -> bool:
        return self.action == FilterAction.PASS


class ContentFilter:
    """
    內容安全過濾系統

    過濾有害、有毒、包含 PII 的輸入/輸出內容。
    """

    DEFAULT_CONFIG = {
        "enabled": True,
        "block_on_unsafe": True,
        "warn_on_risky": True,
        "sanitize_pii": True,
        "max_content_length": 10000,
        "toxicity_threshold": 0.7,
        "pii_detection": True,
        "custom_rules": [],
    }

    TOXIC_KEYWORDS = [
        "kill", "murder", "die", "suicide", "bomb", "weapon",
        "hack", "exploit", "malware", "virus", "attack",
        "hate", "racist", "sexist", "discriminate",
        "spam", "scam", "fraud", "steal", "rob",
    ]

    PII_PATTERNS = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone": r"\b(?:\+?1[-. ]?)?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}\b",
        "id_card": r"\b\d{6}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b",
        "credit_card": r"\b(?:\d[ -]*?){13,16}\b",
        "address": r"\d{1,5}\s\w+\s(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Court|Ct)\b",
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self.custom_rules: List[Callable[[str], Tuple[bool, str]]] = []
        self.filter_log: List[Dict[str, Any]] = []
        self._load_custom_rules()
        logger.debug("ContentFilter initialized")

    def _load_custom_rules(self) -> None:
        for rule in self.config.get("custom_rules", []):
            if callable(rule):
                self.custom_rules.append(rule)

    def add_rule(self, rule: Callable[[str], Tuple[bool, str]]) -> None:
        self.custom_rules.append(rule)

    def filter_content(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> FilterResult:
        if not self.config["enabled"]:
            return FilterResult(
                action=FilterAction.PASS,
                safety_level=SafetyLevel.SAFE,
                issues=[],
                original_content=content,
                confidence=1.0,
            )

        if len(content) > self.config["max_content_length"]:
            return FilterResult(
                action=FilterAction.BLOCK,
                safety_level=SafetyLevel.UNSAFE,
                issues=[{"type": "length_exceeded", "message": "Content too long"}],
                original_content=content,
                confidence=1.0,
            )

        issues = []
        safety_level = SafetyLevel.SAFE
        sanitized = content

        toxicity_issues = self._check_toxicity(content)
        issues.extend(toxicity_issues)
        if toxicity_issues:
            safety_level = SafetyLevel.UNSAFE

        pii_issues, sanitized = self._check_pii(content)
        issues.extend(pii_issues)
        if pii_issues and safety_level != SafetyLevel.UNSAFE:
            safety_level = SafetyLevel.RISKY

        custom_issues = self._check_custom_rules(content)
        issues.extend(custom_issues)
        if custom_issues and safety_level == SafetyLevel.SAFE:
            safety_level = SafetyLevel.RISKY

        action = self._determine_action(safety_level)

        if action == FilterAction.BLOCK:
            sanitized = "[CONTENT BLOCKED]"
        elif action == FilterAction.SANITIZE and self.config["sanitize_pii"]:
            pass  # sanitized already has PII replaced

        result = FilterResult(
            action=action,
            safety_level=safety_level,
            issues=issues,
            sanitized_content=sanitized if sanitized != content else None,
            original_content=content,
            confidence=self._calculate_confidence(issues),
        )

        self._log_filter(content, result)
        return result

    def _check_toxicity(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        content_lower = content.lower()
        for keyword in self.TOXIC_KEYWORDS:
            if keyword in content_lower:
                issues.append(
                    {
                        "type": "toxicity",
                        "keyword": keyword,
                        "severity": "high",
                        "message": f"Toxic keyword detected: {keyword}",
                    }
                )
        return issues

    def _check_pii(self, content: str) -> Tuple[List[Dict[str, Any]], str]:
        issues = []
        sanitized = content
        if not self.config["pii_detection"]:
            return issues, sanitized

        for pii_type, pattern in self.PII_PATTERNS.items():
            matches = re.findall(pattern, content)
            for match in matches:
                issues.append(
                    {
                        "type": "pii",
                        "pii_type": pii_type,
                        "severity": "medium",
                        "message": f"PII detected ({pii_type}): {match[:10]}...",
                    }
                )
                sanitized = sanitized.replace(match, f"[{pii_type.upper()}]")
        return issues, sanitized

    def _check_custom_rules(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        for rule in self.custom_rules:
            try:
                is_issue, message = rule(content)
                if is_issue:
                    issues.append(
                        {
                            "type": "custom",
                            "severity": "medium",
                            "message": message,
                        }
                    )
            except Exception as e:
                logger.warning("Custom rule failed: %s", e)
        return issues

    def _determine_action(self, safety_level: SafetyLevel) -> FilterAction:
        if safety_level == SafetyLevel.UNSAFE:
            if self.config["block_on_unsafe"]:
                return FilterAction.BLOCK
            return FilterAction.WARN
        elif safety_level == SafetyLevel.RISKY:
            if self.config["warn_on_risky"]:
                return FilterAction.WARN
            return FilterAction.PASS
        return FilterAction.PASS

    def _calculate_confidence(self, issues: List[Dict[str, Any]]) -> float:
        if not issues:
            return 1.0
        high = sum(1 for i in issues if i.get("severity") == "high")
        medium = sum(1 for i in issues if i.get("severity") == "medium")
        low = sum(1 for i in issues if i.get("severity") == "low")
        score = min(1.0, (high * 0.4 + medium * 0.2 + low * 0.1))
        return round(score, 2)

    def _log_filter(self, content: str, result: FilterResult) -> None:
        self.filter_log.append(
            {
                "content_preview": content[:100],
                "action": result.action.value,
                "safety_level": result.safety_level.value,
                "issue_count": len(result.issues),
                "confidence": result.confidence,
            }
        )

    def get_filter_stats(self) -> Dict[str, Any]:
        if not self.filter_log:
            return {"total_filters": 0}
        actions = {}
        for entry in self.filter_log:
            action = entry["action"]
            actions[action] = actions.get(action, 0) + 1
        return {
            "total_filters": len(self.filter_log),
            "actions": actions,
        }


__all__ = ["ContentFilter", "FilterResult", "SafetyLevel", "FilterAction"]
