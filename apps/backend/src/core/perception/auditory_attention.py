# ANGELA-MATRIX: L0[基础层] [A] L1

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class AuditoryAttention:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.focus_source: Optional[str] = None


# Backward compatibility alias (2026-06-07)
# Tests expect AuditoryAttentionController; actual implementation is AttentionController in attention_controller.py
try:
    from .attention_controller import AttentionController as AuditoryAttentionController
except ImportError:
    AuditoryAttentionController = None
