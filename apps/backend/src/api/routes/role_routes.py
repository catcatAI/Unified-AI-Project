# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""Role catalogue endpoint (P3-1).

Read-only on purpose: roles are server-side config, so a client can discover
what it may ask for but never create one. The catalogue is exactly what
``/chat/unified`` will accept as ``role_id``.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/roles")
async def list_roles() -> Dict[str, Any]:
    """List the registered roles a client may select."""
    from ai.roleplay.runtime import get_role_orchestrator

    orchestrator = get_role_orchestrator()
    roles: List[Dict[str, Any]] = []
    for role_id in orchestrator.roles:
        agent = orchestrator.get(role_id)
        if agent is None:
            continue
        role = agent.role
        roles.append(
            {
                "role_id": role.role_id,
                "display_name": role.display_name,
                "context_scope": role.context_scope.value,
                "backend_slot": role.backend_slot,
                "memory_namespace": role.memory_namespace,
            }
        )
    return {"roles": roles}
