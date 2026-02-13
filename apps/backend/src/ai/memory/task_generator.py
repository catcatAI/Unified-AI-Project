"""
智能任务生成器
==============
根据用户历史和 Angela 状态生成预计算任务

设计目标：
1. 分析用户对话模式
2. 预测用户可能的下一个问题
3. 生成智能预计算任务
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import Counter, defaultdict

from .memory_template import MemoryTemplate, ResponseCategory, AngelaState, UserImpression
from .precompute_service import PrecomputeTask

logger = logging.getLogger(__name__)


class TaskGenerator:
    """
    任务生成器
    ===========
    根据用户历史和 Angela 状态生成预计算任务
    """

    def __init__(self, max_tasks: int = 10):
        """
        初始化任务生成器

        Args:
            max_tasks: 每次生成的最大任务数
        """
        self.max_tasks = max_tasks

        # 常见对话模式
        self.common_patterns = {
            "greeting": ["你好", "早安", "晚安", "嗨", "哈喽"],
            "farewell": ["再见", "拜拜", "走了", "要去睡了"],
            "question": ["为什么", "怎么", "什么", "哪里", "如何"],
            "thanks": ["谢谢", "感谢", "谢啦"],
            "affirmation": ["是的", "对的", "好的", "没问题"],
            "emotion": ["难过", "开心", "累", "烦", "担心"],
            "curiosity": ["想了解", "想知道", "告诉", "说说"],
            "help": ["帮帮我", "帮助", "帮忙"]
        }

    def generate_idle_tasks(
        self,
        user_history: List[Dict[str, Any]],
        angela_state: AngelaState,
        user_impression: UserImpression
    ) -> List[PrecomputeTask]:
        """
        根据用户历史和 Angela 状态生成预计算任务

        Args:
            user_history: 用户对话历史
            angela_state: Angela 当前状态
            user_impression: 用户印象

        Returns:
            List[PrecomputeTask]: 预计算任务列表
        """
        tasks = []

        # 1. 分析用户模式
        patterns = self._analyze_user_patterns(user_history)

        # 2. 预测下一个问题
        predicted_queries = self._predict_next_queries(patterns, user_history)

        # 3. 建议回應类别
        suggested_categories = self._suggest_categories(angela_state)

        # 4. 生成任务
        for i, query in enumerate(predicted_queries[:self.max_tasks]):
            # 为每个查询生成任务
            category = suggested_categories[i % len(suggested_categories)]

            # 提取关键词
            keywords = self._extract_keywords(query)

            task = PrecomputeTask(
                query=query,
                category=category,
                keywords=keywords,
                angela_state=angela_state,
                user_impression=user_impression,
                context={"history": user_history[-3:] if user_history else []},
                priority=i + 1
            )

            tasks.append(task)

        logger.info(f"Generated {len(tasks)} precompute tasks")
        return tasks

    def _analyze_user_patterns(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析用户对话模式

        Args:
            history: 用户对话历史

        Returns:
            Dict[str, Any]: 用户模式分析结果
        """
        patterns = {
            "common_phrases": [],
            "preferred_topics": [],
            "interaction_style": "casual",
            "question_frequency": 0.0,
            "emotional_tone": "neutral"
        }

        if not history:
            return patterns

        # 提取用户消息
        user_messages = []
        for entry in history:
            if entry.get("role") == "user":
                user_messages.append(entry.get("content", ""))

        if not user_messages:
            return patterns

        # 1. 常见短语
        phrases = []
        for msg in user_messages:
            words = msg.split()
            if len(words) >= 2:
                phrases.append(" ".join(words[:2]))

        phrase_counter = Counter(phrases)
        patterns["common_phrases"] = phrase_counter.most_common(10)

        # 2. 问题频率
        question_count = sum(1 for msg in user_messages if "?" in msg or "吗" in msg or "?" in msg)
        patterns["question_frequency"] = question_count / len(user_messages)

        # 3. 情绪分析（简化）
        emotional_words = {
            "positive": ["开心", "高兴", "喜欢", "爱", "棒", "好"],
            "negative": ["难过", "伤心", "讨厌", "烦", "累", "痛"],
            "neutral": ["嗯", "好的", "可以", "了解"]
        }

        positive_count = sum(1 for msg in user_messages if any(w in msg for w in emotional_words["positive"]))
        negative_count = sum(1 for msg in user_messages if any(w in msg for w in emotional_words["negative"]))

        if positive_count > negative_count:
            patterns["emotional_tone"] = "positive"
        elif negative_count > positive_count:
            patterns["emotional_tone"] = "negative"
        else:
            patterns["emotional_tone"] = "neutral"

        return patterns

    def _predict_next_queries(
        self,
        patterns: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> List[str]:
        """
        预测用户可能的下一个问题

        Args:
            patterns: 用户模式
            history: 用户对话历史

        Returns:
            List[str]: 预测的查询列表
        """
        queries = []

        # 1. 基于常见短语
        for phrase, count in patterns.get("common_phrases", []):
            if count > 1:
                queries.append(phrase)

        # 2. 基于常见对话模式
        if patterns.get("question_frequency", 0) > 0.3:
            queries.extend([
                "为什么这么说？",
                "能解释一下吗？",
                "怎么做到的？"
            ])

        # 3. 基于情绪状态
        tone = patterns.get("emotional_tone", "neutral")
        if tone == "positive":
            queries.extend([
                "你也觉得很好对吧？",
                "我们什么时候再聊？"
            ])
        elif tone == "negative":
            queries.extend([
                "能安慰我吗？",
                "你会一直陪着我吗？"
            ])

        # 4. 添加一些通用预测
        queries.extend([
            "你在做什么？",
            "你好吗？",
            "能帮帮我吗？"
        ])

        # 去重
        unique_queries = list(dict.fromkeys(queries))

        return unique_queries[:self.max_tasks]

    def _suggest_categories(self, angela_state: AngelaState) -> List[ResponseCategory]:
        """
        根据 Angela 状态建议回應类别

        Args:
            angela_state: Angela 当前状态

        Returns:
            List[ResponseCategory]: 建议的类别列表
        """
        categories = []

        # 默认类别
        default_categories = [
            ResponseCategory.SMALL_TALK,
            ResponseCategory.QUESTION,
            ResponseCategory.EMOTIONAL,
            ResponseCategory.AFFIRMATION,
            ResponseCategory.CURIOSITY
        ]

        # 根据状态调整
        beta = angela_state.beta  # 情绪状态

        if beta.get("happy", 0) > 0.5:
            categories.append(ResponseCategory.GREETING)
            categories.append(ResponseCategory.INTIMACY)

        if beta.get("sad", 0) > 0.5:
            categories.append(ResponseCategory.EMOTIONAL)
            categories.append(ResponseCategory.SUPPORT)

        if angela_state.alpha.get("energy", 0) < 0.3:
            categories.append(ResponseCategory.CASUAL)
            categories.append(ResponseCategory.FAREWELL)

        # 合并并去重
        all_categories = list(set(categories + default_categories))

        return all_categories[:self.max_tasks]

    def _extract_keywords(self, query: str) -> List[str]:
        """
        从查询中提取关键词

        Args:
            query: 查询字符串

        Returns:
            List[str]: 关键词列表
        """
        # 简化版本：提取非停用词
        stopwords = {"你", "我", "他", "她", "的", "了", "吗", "呢", "吧", "啊", "是", "在", "有"}

        words = query.split()
        keywords = [w for w in words if w not in stopwords and len(w) > 1]

        return keywords[:5]  # 最多返回 5 个关键词

    def generate_task_for_query(
        self,
        query: str,
        angela_state: AngelaState,
        user_impression: UserImpression
    ) -> PrecomputeTask:
        """
        为单个查询生成预计算任务

        Args:
            query: 查询字符串
            angela_state: Angela 当前状态
            user_impression: 用户印象

        Returns:
            PrecomputeTask: 预计算任务
        """
        # 确定类别
        category = self._determine_category(query)

        # 提取关键词
        keywords = self._extract_keywords(query)

        task = PrecomputeTask(
            query=query,
            category=category,
            keywords=keywords,
            angela_state=angela_state,
            user_impression=user_impression,
            context={},
            priority=1
        )

        return task

    def _determine_category(self, query: str) -> ResponseCategory:
        """
        根据查询确定回應类别

        Args:
            query: 查询字符串

        Returns:
            ResponseCategory: 回應类别
        """
        query_lower = query.lower()

        # 检查常见模式
        for category, patterns in self.common_patterns.items():
            if any(p in query_lower for p in patterns):
                return ResponseCategory(category)

        # 默认返回 SMALL_TALK
        return ResponseCategory.SMALL_TALK