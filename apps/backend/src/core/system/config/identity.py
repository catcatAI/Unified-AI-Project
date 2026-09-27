"""Angela's name, from configuration rather than scattered literals.

WHY this module exists
----------------------
`system/core.default.yaml` declared `ai_name` and no code ever read it, while the
name itself was hardcoded in several places. Two of those literals were also
traps: `create_soul_core(name=...)` accepted a name and then ignored it, and
`angela_agent.py` uses the string "Angela" as a *game player* name, which has
nothing to do with identity.

So the identity name lives here, reads the declared config, and keeps a default
that matches the code's historical behaviour. Changing `ai_name` in the config
now changes the self-model and soul name, and nothing else.

ANGELA-MATRIX: [L2] [β] [B] [L4]
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# The historical hardcoded value. Also the effective default, so a missing or
# broken config can never leave the system nameless.
DEFAULT_AI_NAME = "Angela"

_CACHE: Optional[str] = None


def get_ai_name(refresh: bool = False) -> str:
    """Return the configured name, falling back to `DEFAULT_AI_NAME`.

    A malformed or empty `ai_name` is reported and ignored rather than allowed to
    propagate: an unnamed self-model would be worse than a misnamed one.
    """
    global _CACHE
    if _CACHE is not None and not refresh:
        return _CACHE

    name = DEFAULT_AI_NAME
    try:
        from core.system.config.tiered_loader import get_config

        config = get_config("system/core") or {}
        raw = config.get("ai_name")
        if isinstance(raw, str) and raw.strip():
            name = raw.strip()
        elif raw is not None:
            logger.warning("ai_name in system/core is not a usable string (%r); using %s", raw, name)
    except Exception as exc:  # pragma: no cover - config unavailable
        logger.warning("Could not read ai_name from config (%s); using %s", exc, name)

    _CACHE = name
    return name


def clear_cache() -> None:
    """Drop the memoised name (config reload / tests)."""
    global _CACHE
    _CACHE = None
