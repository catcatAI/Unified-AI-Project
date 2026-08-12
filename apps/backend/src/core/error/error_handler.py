"""
企業級錯誤處理系統 (向後相容 re-export)

本模組過去自行定義了 ErrorHandler / ErrorCategory / ErrorSeverity / CircuitBreaker，
但代碼庫中已有權威定義 (core.angela_error 與 shared.network_resilience)。
此處僅保留向後相容的 re-export，以消除重複定義並統一為單一真源。
RecoveryStrategy 為本模組獨有的舊枚舉，暫時保留以維持既有匯入路徑。
"""

import enum
import logging

logger = logging.getLogger(__name__)

from core.angela_error import ErrorCategory, ErrorHandler, ErrorSeverity
from shared.network_resilience import CircuitBreaker


class RecoveryStrategy(enum.Enum):
    RETRY = "retry"
    FALLBACK = "fallback"
    CIRCUIT_BREAK = "circuit_break"
    GRACEFUL_DEGRADE = "graceful_degrade"
    MANUAL_INTERVENTION = "manual_intervention"
    RESTART = "restart"
