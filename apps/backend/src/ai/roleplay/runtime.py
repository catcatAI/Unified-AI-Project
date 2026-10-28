# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""Process-wide role registry — what the chat API consults for a `role_id`.

Roles live in config (``configs/system/roles.default.yaml``), not in request
payloads: a client may *choose* a role, never define one. Unknown ids are
rejected by the caller instead of silently falling back to Angela.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List, Optional

from ai.roleplay.multi_role_orchestrator import MultiRoleOrchestrator
from ai.roleplay.role import Role

logger = logging.getLogger(__name__)

CONFIG_RELATIVE = Path("configs") / "system" / "roles.default.yaml"


def default_config_path() -> Path:
    override = os.environ.get("ANGELA_ROLES_CONFIG")
    if override:
        return Path(override).expanduser()
    # apps/backend/src/ai/roleplay/runtime.py → apps/backend
    return Path(__file__).resolve().parents[3] / CONFIG_RELATIVE


def load_roles(path: Optional[Path] = None) -> List[Role]:
    """Load role specs; a missing file disables role play instead of crashing."""
    cfg = Path(path) if path is not None else default_config_path()
    if not cfg.exists():
        logger.warning("Roles config %s not found; role play stays disabled", cfg)
        return []
    try:
        import yaml

        data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # noqa: BLE001 - a bad config must not break chat
        logger.warning("Roles config %s unreadable: %s", cfg, exc)
        return []

    roles: List[Role] = []
    for spec in data.get("roles") or []:
        if not isinstance(spec, dict):
            logger.warning("Skipping non-mapping role spec: %r", spec)
            continue
        try:
            roles.append(Role.from_dict(spec))
        except (TypeError, ValueError) as exc:
            logger.warning("Skipping invalid role %r: %s", spec, exc)
    return roles


_orchestrator: Optional[MultiRoleOrchestrator] = None


def get_role_orchestrator() -> MultiRoleOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        orchestrator = MultiRoleOrchestrator()
        for role in load_roles():
            try:
                orchestrator.register(role)
            except ValueError as exc:
                logger.warning("Role %s not registered: %s", role.role_id, exc)
        _orchestrator = orchestrator
        logger.info("Role registry ready: %s", orchestrator.roles)
    return _orchestrator


def set_role_orchestrator(orchestrator: Optional[MultiRoleOrchestrator]) -> None:
    """Swap the registry (tests, and a future hot-reload path)."""
    global _orchestrator
    _orchestrator = orchestrator


def reset_role_orchestrator() -> None:
    set_role_orchestrator(None)


def resolve_role(role_id: str) -> Optional[Role]:
    agent = get_role_orchestrator().get((role_id or "").strip())
    return agent.role if agent is not None else None


def build_role_persona(role: Role) -> str:
    """The prompt block that makes a role turn speak as that role.

    The core prompt opens with "you are Angela", so the override has to be
    explicit and say it wins. Kept short: role identity is context, not a script
    — the actual voice still comes from the model plus this role's memory.
    """
    return (
        "[角色設定（本回合優先於上述身份）]\n"
        f"你現在扮演「{role.display_name}」（role_id={role.role_id}）。"
        "用第一人稱、維持此角色一貫的語氣與立場回答；"
        "不要自稱 Angela，也不要聲稱自己是其他角色。"
        "如果不知道答案，就用這個角色的方式誠實說不知道。"
    )
