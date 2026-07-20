# =============================================================================
# ANGELA-MATRIX: [L2] [αβγδ] [A/B/C] [L2]
# =============================================================================
"""
Shared package — cross-cutting utilities and base types.

Provides:
  - error:              ProjectError hierarchy and ErrorHandler
  - key_manager:        UnifiedKeyManager for ANGELA_KEY_A/B/C
  - network_resilience: RetryPolicy, CircuitBreaker
  - security_middleware:SignedCommunicationMiddleware
  - types:              MappableDataObject
  - utils.env_utils:    get_env, get_int_env, etc.
  - utils.hardware_detector: HardwareProfile, SystemHardwareProbe

Import directly from submodules: from shared.key_manager import get_security_key
"""

from shared.error import ErrorHandler, HSPConnectionError, ProjectError, ResourceError, SecurityError
from shared.key_manager import UnifiedKeyManager
from shared.network_resilience import CircuitBreaker, RetryPolicy
from shared.security_middleware import SignedCommunicationMiddleware

__all__ = [
    # error
    "ProjectError",
    "HSPConnectionError",
    "SecurityError",
    "ResourceError",
    "ErrorHandler",
    # key manager
    "UnifiedKeyManager",
    # network resilience
    "RetryPolicy",
    "CircuitBreaker",
    # security middleware
    "SignedCommunicationMiddleware",
]
