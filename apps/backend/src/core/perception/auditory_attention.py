# =============================================================================
# ANGELA-MATRIX: L0 [α] [C] L1 — Backward-compat alias
# =============================================================================
# AuditoryAttention was an empty stub. Real implementation is AttentionController.
# This file exists only for backward compatibility.
# =============================================================================

try:
    from .attention_controller import AttentionController as AuditoryAttentionController
except ImportError:
    import logging
    logging.getLogger(__name__).warning("AttentionController not available")
    AuditoryAttentionController = None
