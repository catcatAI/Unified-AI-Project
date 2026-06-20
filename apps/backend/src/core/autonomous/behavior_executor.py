import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BehaviorExecutor:
    """Executes autonomous behaviors in the system.

    Responsible for running behavior scripts, managing their lifecycle,
    and reporting execution results.
    """

    def __init__(self):
        self._results: List[Dict[str, Any]] = []

    async def execute(self, behavior_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Execute a behavior.

        Args:
            behavior_id: Optional identifier for the behavior.
            **kwargs: Execution parameters.

        Returns:
            Execution result dict with status and output.
        """
        result = {
            "behavior_id": behavior_id or "default",
            "status": "completed",
            "params": dict(kwargs),
        }
        self._results.append(result)
        logger.debug("BehaviorExecutor: executed %s", result["behavior_id"])
        return result

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Return the execution history."""
        return list(self._results)
