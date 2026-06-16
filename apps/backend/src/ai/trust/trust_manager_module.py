"""
Trust Manager — 基於互動的信譽評估系統

跟蹤每位用戶的信譽分數,支援:
- 信譽分數隨互動增減
- 信譽驅動的權限控制
- 持久化存儲到 HAM
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class TrustProfile:
    """單一用戶的信譽資料"""

    user_id: str
    score: float = 0.5
    interaction_count: int = 0
    positive_interactions: int = 0
    negative_interactions: int = 0
    last_interaction_time: float = field(default_factory=time.time)
    violations: List[Dict[str, Any]] = field(default_factory=list)
    granted_permissions: List[str] = field(default_factory=list)
    revoked_permissions: List[str] = field(default_factory=list)

    @property
    def trust_level(self) -> str:
        if self.score >= 0.8:
            return "high"
        elif self.score >= 0.5:
            return "medium"
        elif self.score >= 0.3:
            return "low"
        return "critical"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "score": self.score,
            "trust_level": self.trust_level,
            "interaction_count": self.interaction_count,
            "positive_interactions": self.positive_interactions,
            "negative_interactions": self.negative_interactions,
            "violations": self.violations,
            "granted_permissions": self.granted_permissions,
            "revoked_permissions": self.revoked_permissions,
        }


class TrustManager:
    """
    基於互動的信譽評估系統

    功能:
    - 跟蹤每位用戶的信譽分數
    - 信譽分數隨互動增減
    - 信譽驅動的權限控制
    - 持久化存儲到 HAM
    """

    DEFAULT_CONFIG = {
        "base_trust": 0.5,
        "positive_increment": 0.05,
        "negative_decrement": 0.1,
        "violation_penalty": 0.2,
        "recovery_rate": 0.01,
        "max_trust": 1.0,
        "min_trust": 0.0,
        "decay_rate": 0.001,
        "permission_thresholds": {
            "high": ["full_access", "admin", "delete"],
            "medium": ["read", "write", "execute"],
            "low": ["read"],
            "critical": [],
        },
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self.profiles: Dict[str, TrustProfile] = {}
        self.audit_log: List[Dict[str, Any]] = []
        logger.debug("TrustManager initialized with config: %s", self.config)

    def get_profile(self, user_id: str) -> TrustProfile:
        if user_id not in self.profiles:
            self.profiles[user_id] = TrustProfile(
                user_id=user_id,
                score=self.config["base_trust"],
            )
        return self.profiles[user_id]

    def record_interaction(
        self,
        user_id: str,
        positive: bool,
        details: Optional[Dict[str, Any]] = None,
    ) -> float:
        profile = self.get_profile(user_id)

        if positive:
            increment = self.config["positive_increment"]
            profile.score = min(
                self.config["max_trust"],
                profile.score + increment,
            )
            profile.positive_interactions += 1
        else:
            decrement = self.config["negative_decrement"]
            profile.score = max(
                self.config["min_trust"],
                profile.score - decrement,
            )
            profile.negative_interactions += 1

        profile.interaction_count += 1
        profile.last_interaction_time = time.time()

        self._log_audit(user_id, "interaction", positive, details)
        return profile.score

    def record_violation(
        self,
        user_id: str,
        violation_type: str,
        severity: str = "medium",
        details: Optional[Dict[str, Any]] = None,
    ) -> float:
        profile = self.get_profile(user_id)

        penalty = self.config["violation_penalty"]
        if severity == "high":
            penalty *= 2
        elif severity == "low":
            penalty *= 0.5

        profile.score = max(
            self.config["min_trust"],
            profile.score - penalty,
        )
        profile.violations.append(
            {
                "type": violation_type,
                "severity": severity,
                "timestamp": time.time(),
                "details": details,
            }
        )

        self._log_audit(
            user_id, "violation", False, {"type": violation_type, "severity": severity}
        )
        return profile.score

    def check_permission(self, user_id: str, permission: str) -> bool:
        profile = self.get_profile(user_id)
        level = profile.trust_level
        allowed = self.config["permission_thresholds"].get(level, [])
        return permission in allowed

    def get_allowed_permissions(self, user_id: str) -> List[str]:
        profile = self.get_profile(user_id)
        level = profile.trust_level
        return list(self.config["permission_thresholds"].get(level, []))

    def apply_decay(self) -> None:
        now = time.time()
        for profile in self.profiles.values():
            elapsed = now - profile.last_interaction_time
            days_elapsed = elapsed / 86400
            if days_elapsed > 1:
                decay = self.config["decay_rate"] * days_elapsed
                profile.score = max(
                    self.config["min_trust"],
                    profile.score - decay,
                )

    def recover_trust(self, user_id: str) -> float:
        profile = self.get_profile(user_id)
        recovery = self.config["recovery_rate"]
        profile.score = min(
            self.config["max_trust"],
            profile.score + recovery,
        )
        self._log_audit(user_id, "recovery", True, {"recovery": recovery})
        return profile.score

    def get_all_profiles(self) -> Dict[str, Dict[str, Any]]:
        return {uid: p.to_dict() for uid, p in self.profiles.items()}

    def get_trust_summary(self) -> Dict[str, Any]:
        if not self.profiles:
            return {"total_users": 0, "average_trust": 0.0}
        scores = [p.score for p in self.profiles.values()]
        return {
            "total_users": len(self.profiles),
            "average_trust": sum(scores) / len(scores),
            "high_trust": sum(1 for s in scores if s >= 0.8),
            "medium_trust": sum(1 for s in scores if 0.5 <= s < 0.8),
            "low_trust": sum(1 for s in scores if 0.3 <= s < 0.5),
            "critical_trust": sum(1 for s in scores if s < 0.3),
        }

    def _log_audit(
        self,
        user_id: str,
        action: str,
        success: bool,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.audit_log.append(
            {
                "user_id": user_id,
                "action": action,
                "success": success,
                "details": details,
                "timestamp": time.time(),
            }
        )

    def export_audit_log(self) -> List[Dict[str, Any]]:
        return list(self.audit_log)


__all__ = ["TrustManager", "TrustProfile"]
