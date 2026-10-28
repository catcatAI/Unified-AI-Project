# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""Multi-role play: per-role identity, context scope, and context layering.

Phase 0 only (data model). The agent, orchestrator, and router wiring land in
later phases of ``docs/06-project-management/plans/MULTI_ROLE_PLAY_AGENT_PLAN.md``.
"""

from ai.roleplay.context import DEFAULT_TOKEN_BUDGET, RoleContext
from ai.roleplay.role import ContextScope, Role

__all__ = [
    "DEFAULT_TOKEN_BUDGET",
    "ContextScope",
    "Role",
    "RoleContext",
]
