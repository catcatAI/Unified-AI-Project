import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AutonomousFeedbackCollector:
    """Collects feedback from various sources for system improvement.

    Gathers execution results, error reports, and performance metrics
    to feed into the learning pipeline.
    """

    def __init__(self):
        self._feedback: List[Dict[str, Any]] = []

    async def collect(self, source: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """Collect feedback from a source.

        Args:
            source: Optional source identifier.
            **kwargs: Additional feedback parameters.

        Returns:
            List of collected feedback items.
        """
        item = {
            "source": source or "unknown",
            "data": dict(kwargs),
        }
        self._feedback.append(item)
        logger.debug("AutonomousFeedbackCollector: collected from %s", source)
        return [item]

    def get_all_feedback(self) -> List[Dict[str, Any]]:
        """Return all collected feedback."""
        return list(self._feedback)

    def clear(self) -> None:
        """Clear all collected feedback."""
        self._feedback.clear()
