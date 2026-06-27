"""
智能任务生成器
==============
根据用户历史和 Angela 状态生成预计算任务

设计目标：
1. 分析用户对话模式
2. 预测用户可能的下一个问题
3. 生成智能预计算任务
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TaskGenerator:
    """Generates precomputation tasks based on user history and Angela state."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._history: List[Dict[str, Any]] = []
        self._topic_chain: Dict[str, Dict[str, int]] = {}

    def analyze_patterns(self, recent_interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not recent_interactions:
            return {"topics": {}, "total_analyzed": 0, "transitions": {}}

        self._history.extend(recent_interactions)
        topics = {}
        prev_topic = None

        for interaction in recent_interactions:
            topic = interaction.get("topic", "general")
            topics[topic] = topics.get(topic, 0) + 1
            if prev_topic is not None:
                self._topic_chain.setdefault(prev_topic, {}).setdefault(topic, 0)
                self._topic_chain[prev_topic][topic] += 1
            prev_topic = topic

        total = len(recent_interactions)
        dominant = max(topics, key=topics.get) if topics else "general"
        return {
            "topics": topics,
            "dominant_topic": dominant,
            "total_analyzed": total,
            "transitions": dict(self._topic_chain),
        }

    def generate_tasks(self, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        tasks = []
        context = context or {}
        if self._history:
            patterns = self.analyze_patterns(self._history[-10:])
            dominant = patterns.get("dominant_topic", "general")
            tasks.append({"task_type": "precompute_response", "priority": 5, "topic": dominant, "params": context})
            top_topics = sorted(patterns.get("topics", {}).items(), key=lambda x: -x[1])[:2]
            for topic, count in top_topics:
                if count > 1:
                    tasks.append({"task_type": "prefetch_knowledge", "priority": 3, "topic": topic, "params": context})
        if not tasks:
            tasks.append({"task_type": "precompute_response", "priority": 5, "params": context})
        return tasks

    def predict_next_query(self, user_id: str) -> Optional[str]:
        if not self._history or len(self._history) < 2:
            return None
        last = self._history[-1].get("topic", "general")
        transitions = self._topic_chain.get(last, {})
        if not transitions:
            return None
        most_likely = max(transitions, key=transitions.get)
        return most_likely


__all__ = ["TaskGenerator"]
