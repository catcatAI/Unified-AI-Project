"""
ANGELA-MATRIX: [L3] [β] [B] [L2]
AuditLoggerHandler — C3 handler that logs all hook activity at DEBUG level.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Callable

logger = logging.getLogger(__name__)


class AuditLoggerHandler:
    """Logs all hook activity at DEBUG level for debugging."""

    def handler_for(self, hook_name: str) -> Callable[[Any], Any]:
        """Create a handler closure that logs hook invocations."""

        async def _handler(data: Any = None) -> Any:
            summary = {}
            if isinstance(data, dict):
                summary = {k: v for k, v in list(data.items())[:5]}
            logger.debug(
                "[Plugin:AuditLogger] hook=%s | data_summary=%s | ts=%s",
                hook_name,
                summary,
                datetime.now(timezone.utc).isoformat(),
            )
            return data

        return _handler
