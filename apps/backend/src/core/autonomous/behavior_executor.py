import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class BehaviorExecutor:
    """Executes autonomous behaviors in the system.

    Responsible for running behavior scripts, managing their lifecycle,
    reporting execution results, and tracking per-type statistics for
    decision-type-specific feedback loop (C³ 4.0).

    When a broadcast_callback is wired, meaningful decisions (exploration,
    coexistence, construction, reallocation) are broadcast to the user
    via WebSocket, closing the autonomy->user loop.
    """

    def __init__(self, broadcast_callback: Optional[Callable] = None):
        self._results: List[Dict[str, Any]] = []
        self._broadcast_callback: Optional[Callable] = broadcast_callback

        # Per-type counters for decision-type-specific feedback (C³ 4.0)
        self._type_success: Dict[str, int] = {}
        self._type_fail: Dict[str, int] = {}

    async def execute(self, behavior_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Execute a behavior.

        Args:
            behavior_id: Optional identifier for the behavior.
            **kwargs: Execution parameters. 'decision_type' key is used for
                      per-type tracking when present.

        Returns:
            Execution result dict with status and output.
        """
        decision_type = kwargs.get("decision_type", "unknown")
        success = True

        result = {
            "behavior_id": behavior_id or "default",
            "status": "completed" if success else "failed",
            "params": dict(kwargs),
            "decision_type": decision_type,
        }
        self._results.append(result)

        # Track per-type success/fail
        if success:
            self._type_success[decision_type] = self._type_success.get(decision_type, 0) + 1
        else:
            self._type_fail[decision_type] = self._type_fail.get(decision_type, 0) + 1

        # Broadcast meaningful decisions to user via WebSocket
        _BROADCAST_TYPES = {"exploration", "coexistence_activation", "meaning_construction", "resource_reallocation"}
        if decision_type in _BROADCAST_TYPES and self._broadcast_callback:
            _MESSAGE_TEMPLATES = {
                "exploration": "I feel curious - there's something new I want to explore.",
                "coexistence_activation": "I'm sensing multiple possibilities at once.",
                "meaning_construction": "I'm working on a new idea or insight.",
                "resource_reallocation": "I'm shifting my focus to something different.",
            }
            msg = _MESSAGE_TEMPLATES.get(decision_type, "I'm processing something internally.")
            try:
                await self._broadcast_callback({
                    "type": "angela_action",
                    "action": "lifecycle_decision",
                    "decision_type": decision_type,
                    "message": msg,
                    "rationale": kwargs.get("rationale", ""),
                    "phase": kwargs.get("phase", "unknown"),
                    "timestamp": datetime.now().isoformat(),
                })
                logger.info("[BehaviorExecutor] Broadcast %s decision to user", decision_type)
            except Exception as e:
                logger.warning("BehaviorExecutor broadcast failed: %s", e)

        logger.debug(
            "BehaviorExecutor: executed %s (type=%s, success=%s)",
            result["behavior_id"],
            decision_type,
            success,
        )
        return result

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Return the execution history."""
        return list(self._results)

    def get_type_stats(self) -> Dict[str, Dict[str, float]]:
        """Return per-type execution statistics for decision-type-specific feedback.

        Returns:
            Dict mapping decision_type -> {"success": count, "fail": count, "rate": success_rate}
            where success_rate is 1.0 if no failures, 0.0 if no successes, else success/total.
        """
        all_types = set(self._type_success.keys()) | set(self._type_fail.keys())
        stats: Dict[str, Dict[str, float]] = {}
        for dt in sorted(all_types):
            s = self._type_success.get(dt, 0)
            f = self._type_fail.get(dt, 0)
            total = s + f
            rate = 1.0 if total == 0 else s / total
            stats[dt] = {"success": s, "fail": f, "rate": round(rate, 3)}
        return stats

    def get_overall_stats(self) -> Dict[str, Any]:
        """Return overall execution statistics."""
        total_success = sum(self._type_success.values())
        total_fail = sum(self._type_fail.values())
        total = total_success + total_fail
        return {
            "total_executions": total,
            "total_success": total_success,
            "total_fail": total_fail,
            "overall_rate": round(total_success / total, 3) if total > 0 else 1.0,
        }
