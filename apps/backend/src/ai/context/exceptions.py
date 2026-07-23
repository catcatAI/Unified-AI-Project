# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

"""Context system exceptions — base classes only.

All 15 domain-specific subclasses were removed (never imported/raised anywhere).
Keep ContextError and IntegrationError as potential base classes for future use.
"""


class ContextError(Exception):
    """Base exception for context operations."""


class IntegrationError(ContextError):
    """Base exception for integration operations."""
