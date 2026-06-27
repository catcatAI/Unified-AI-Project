"""
ANGELA-MATRIX: [L3] [β] [B] [L2]
MetricsCollectorHandler — C3 handler that tracks hook invocation counts.
"""

import logging
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)


class MetricsCollectorHandler:
    """Collects metrics on hook calls: count per hook type."""

    def __init__(self) -> None:
        self._metrics: Dict[str, Dict[str, int]] = {"counts": {}}

    def handler_for(self, hook_name: str) -> Callable[[Any], Any]:
        """Create a handler closure that records invocations for the given hook."""
        metrics = self._metrics

        async def _handler(data: Any = None) -> Any:
            metrics["counts"][hook_name] = metrics["counts"].get(hook_name, 0) + 1
            return data

        return _handler

    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics."""
        return {"counts": dict(self._metrics["counts"])}
