# =============================================================================
# ANGELA-MATRIX: [L6] [αβγδ] [A/B/C] [L3+]
# =============================================================================
"""
Security module: authentication, encryption, key management, secure evaluation, and audit.

Provides:
  - AuthMiddleware: JWT token auth and API key verification
  - EncryptionUtils: Fernet encryption, password hashing, HMAC signing
  - KeyGenerator: Secure random key generation
  - KeyValidator: Key security and validity verification
  - SafeEvaluator / safe_eval: AST-based safe expression evaluation
  - SecurityAudit: Automated security scanning and scoring
"""

from core.security.auth_middleware import AuthMiddleware, get_auth_middleware
from core.security.encryption import (
    EncryptionUtils,
    encryption_utils,
    generate_csrf_token,
    sanitize_input,
    validate_password_strength,
    verify_csrf_token,
)
from core.security.key_generator import KeyGenerator
from core.security.key_validator import (
    KeyValidationResult,
    KeyValidator,
    get_key_validator,
    validate_system_keys,
)
from core.security.secure_eval import (
    EvalResult,
    SafeEvaluator,
    get_safe_evaluator,
    safe_eval,
    safe_eval_arithmetic,
)
from core.security.security_audit import SecurityAudit, get_security_audit

__all__ = [
    # Auth
    "AuthMiddleware",
    "get_auth_middleware",
    # Encryption
    "EncryptionUtils",
    "encryption_utils",
    "validate_password_strength",
    "sanitize_input",
    "generate_csrf_token",
    "verify_csrf_token",
    # Key management
    "KeyGenerator",
    "KeyValidator",
    "KeyValidationResult",
    "get_key_validator",
    "validate_system_keys",
    # Secure eval
    "safe_eval",
    "safe_eval_arithmetic",
    "SafeEvaluator",
    "EvalResult",
    "get_safe_evaluator",
    # Audit
    "SecurityAudit",
    "get_security_audit",
]
