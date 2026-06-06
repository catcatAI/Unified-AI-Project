"""
Angela AI v6.0 - Habit Formation System
习惯形成系统

Implements the "66 repetitions" theory of habit formation.
Tracks habit automaticity based on repetition in stable contexts.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class HabitTrace:
    """习惯痕迹 / Habit formation trace"""

    habit_id: str
    habit_name: str
    repetition_count: int  # 重复次数
    automaticity_score: float  # 自动化程度 (0-1)
    context_stability: float  # 情境稳定性
    reward_association: float  # 奖励关联强度
    is_formed: bool  # 是否已形成
    created_at: datetime = field(default_factory=datetime.now)


class HabitFormation:
    """
    习惯形成系统 / Habit Formation System

    Implements the "66 repetitions" theory of habit formation.
    Tracks habit automaticity based on repetition in stable contexts.

    Habit Formation Model:
    - Automaticity increases with repetition in stable context
    - Context stability enhances habit formation
    - Reward association strengthens habit
    - Takes ~66 repetitions to form a habit (on average)

    Example:
        >>> habit_system = HabitFormation()
        >>>
        >>> # Start a new habit
        >>> habit = habit_system.start_habit("morning_exercise")
        >>>
        >>> # Repeat in stable context (66 times theory)
        >>> for day in range(66):
        ...     habit_system.reinforce("morning_exercise", context="bedroom", reward=0.8)
        >>>
        >>> if habit_system.is_habit_formed("morning_exercise"):
        ...     print("Habit successfully formed!")
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        # Habit formation parameters
        self.repetitions_for_habit: int = self.config.get("repetitions_for_habit", 66)
        self.context_weight: float = self.config.get("context_weight", 0.3)
        self.reward_weight: float = self.config.get("reward_weight", 0.4)
        self.automaticity_threshold: float = self.config.get("automaticity_threshold", 0.7)

        # Habit storage
        self.habits: Dict[str, HabitTrace] = {}
        self.repetition_history: Dict[str, List[Tuple[str, datetime]]] = {}

    def start_habit(self, habit_id: str, habit_name: str = "") -> HabitTrace:
        """
        开始形成新习惯 / Start forming a new habit

        Args:
            habit_id: Unique habit identifier
            habit_name: Human-readable habit name

        Returns:
            HabitTrace object
        """
        habit = HabitTrace(
            habit_id=habit_id,
            habit_name=habit_name or habit_id,
            repetition_count=0,
            automaticity_score=0.0,
            context_stability=0.0,
            reward_association=0.0,
            is_formed=False,
        )

        self.habits[habit_id] = habit
        self.repetition_history[habit_id] = []

        return habit

    def reinforce(
        self, habit_id: str, context: str, reward: float = 0.5, success: bool = True
    ) -> HabitTrace:
        """
        强化习惯 / Reinforce a habit

        Args:
            habit_id: Habit identifier
            context: Context/environment where repetition occurred
            reward: Reward magnitude (0-1)
            success: Whether the repetition was successful

        Returns:
            Updated HabitTrace
        """
        if habit_id not in self.habits:
            return self.start_habit(habit_id)

        habit = self.habits[habit_id]

        if not success:
            # Failed repetition doesn't count toward habit
            return habit

        # Record repetition
        habit.repetition_count += 1
        self.repetition_history[habit_id].append((context, datetime.now()))

        # Calculate context stability
        contexts = [c for c, _ in self.repetition_history[habit_id][-20:]]
        if contexts:
            context_consistency = contexts.count(context) / len(contexts)
            habit.context_stability = context_consistency

        # Update reward association (running average)
        habit.reward_association = habit.reward_association * 0.9 + reward * 0.1

        # Calculate automaticity score
        # Based on repetition count, context stability, and reward
        repetition_factor = min(1.0, habit.repetition_count / self.repetitions_for_habit)
        context_factor = habit.context_stability * self.context_weight
        reward_factor = habit.reward_association * self.reward_weight

        habit.automaticity_score = min(
            1.0,
            repetition_factor * (1 - self.context_weight - self.reward_weight)
            + context_factor
            + reward_factor,
        )

        # Check if habit is formed
        habit.is_formed = (
            habit.automaticity_score >= self.automaticity_threshold
            and habit.repetition_count >= self.repetitions_for_habit * 0.5
        )

        return habit

    def is_habit_formed(self, habit_id: str) -> bool:
        """检查习惯是否已形成 / Check if a habit is formed"""
        if habit_id not in self.habits:
            return False
        return self.habits[habit_id].is_formed

    def get_automaticity(self, habit_id: str) -> float:
        """获取习惯自动化程度 / Get habit automaticity score"""
        if habit_id not in self.habits:
            return 0.0
        return self.habits[habit_id].automaticity_score

    def get_repetition_count(self, habit_id: str) -> int:
        """获取重复次数 / Get repetition count"""
        if habit_id not in self.habits:
            return 0
        return self.habits[habit_id].repetition_count

    def get_all_habits(self) -> Dict[str, HabitTrace]:
        """获取所有习惯 / Get all habits"""
        return self.habits.copy()
