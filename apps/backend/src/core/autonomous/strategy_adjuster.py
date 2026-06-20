import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class StrategyAdjuster:
    """Adjusts execution strategies based on feedback and context.

    Examines execution results and suggests strategy modifications
    (e.g., timeout values, retry logic, priority adjustments).
    """

    def __init__(self):
        self._adjustments: Dict[str, Any] = {}

    async def adjust(self, strategy: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Adjust a strategy based on given parameters.

        Args:
            strategy: Current strategy dict to adjust.
            **kwargs: Override parameters for specific adjustments.

        Returns:
            Adjusted strategy dict.
        """
        current = dict(strategy or {})
        current.update(kwargs)
        adjustment_id = f"adj_{id(current)}"
        self._adjustments[adjustment_id] = dict(current)
        logger.debug("StrategyAdjuster: applied adjustment %s", adjustment_id)
        return current

    def get_adjustment_history(self) -> Dict[str, Any]:
        """Return the history of all adjustments made."""
        return dict(self._adjustments)
