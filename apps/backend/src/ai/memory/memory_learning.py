"""
记忆学习引擎
============
记录用户反馈并优化回應模板

设计目标：
1. 记录用户对回應的反馈
2. 使用移动平均更新成功率
3. 分析成功回應模式
4. 建议新的回應模板
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict

from .memory_template import MemoryTemplate, ResponseCategory, AngelaState, UserImpression

logger = logging.getLogger(__name__)


class MemoryLearningEngine:
    """
    记忆学习引擎
    ===========
    记录用户反馈并优化回應模板
    """

    def __init__(self, memory_manager):
        """
        初始化学习引擎

        Args:
            memory_manager: 记忆管理器实例
        """
        self.memory_manager = memory_manager

        # 反馈历史
        self.feedback_history: List[Dict[str, Any]] = []

        # 模式分析
        self.patterns: Dict[str, Any] = {
            "successful_templates": defaultdict(int),
            "failed_templates": defaultdict(int),
            "user_preferences": defaultdict(list),
            "time_patterns": defaultdict(list)
        }

        # 学习参数
        self.history_weight = 0.8  # 历史权重
        self.feedback_weight = 0.2  # 新反馈权重

        # 统计信息
        self.stats = {
            "total_feedback": 0,
            "positive_feedback": 0,
            "negative_feedback": 0,
            "templates_optimized": 0
        }

    async def record_feedback(
        self,
        template_id: str,
        feedback: bool,
        context: Dict[str, Any]
    ):
        """
        记录用户反馈
        使用移动平均更新成功率（80% 历史 + 20% 新反馈）

        Args:
            template_id: 模板 ID
            feedback: 用户反馈（True=正面，False=负面）
            context: 上下文信息
        """
        try:
            # 1. 获取模板
            template = await self.memory_manager.get_template(template_id)

            if template is None:
                logger.warning(f"Template {template_id} not found")
                return

            # 2. 更新成功率（移动平均）
            current_success = 1.0 if feedback else 0.0
            new_success_rate = (
                template.success_rate * self.history_weight +
                current_success * self.feedback_weight
            )

            template.success_rate = new_success_rate

            # 3. 记录使用
            template.record_usage(success=feedback)

            # 4. 更新模板
            await self.memory_manager.update_template(template)

            # 5. 记录反馈历史
            feedback_record = {
                "template_id": template_id,
                "feedback": feedback,
                "context": context,
                "timestamp": datetime.utcnow().isoformat(),
                "previous_success_rate": template.success_rate
            }
            self.feedback_history.append(feedback_record)

            # 6. 更新统计
            self.stats["total_feedback"] += 1
            if feedback:
                self.stats["positive_feedback"] += 1
                self.patterns["successful_templates"][template_id] += 1
            else:
                self.stats["negative_feedback"] += 1
                self.patterns["failed_templates"][template_id] += 1

            # 7. 分析用户偏好
            self._analyze_user_preferences(template, feedback, context)

            logger.info(f"Recorded feedback for template {template_id}: {feedback}")

        except Exception as e:
            logger.error(f"Error recording feedback: {e}", exc_info=True)

    def _analyze_user_preferences(
        self,
        template: MemoryTemplate,
        feedback: bool,
        context: Dict[str, Any]
    ):
        """
        分析用户偏好

        Args:
            template: 模板
            feedback: 反馈
            context: 上下文
        """
        if feedback:
            # 记录成功的类别
            self.patterns["user_preferences"][template.category.value].append(feedback)

            # 记录时间模式
            hour = datetime.utcnow().hour
            self.patterns["time_patterns"][hour].append(feedback)

    async def analyze_successful_responses(
        self,
        responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        分析成功回應模式

        Args:
            responses: 回應列表

        Returns:
            Dict[str, Any]: 分析结果
        """
        analysis = {
            "common_patterns": [],
            "preferred_categories": defaultdict(int),
            "average_length": 0.0,
            "emotional_tones": defaultdict(int)
        }

        if not responses:
            return analysis

        total_length = 0

        for response in responses:
            # 提取类别
            category = response.get("category", "unknown")
            analysis["preferred_categories"][category] += 1

            # 计算长度
            content = response.get("content", "")
            total_length += len(content)

            # 提取情绪（简化）
            if "开心" in content or "高兴" in content or "棒" in content:
                analysis["emotional_tones"]["positive"] += 1
            elif "难过" in content or "伤心" in content or "累" in content:
                analysis["emotional_tones"]["negative"] += 1
            else:
                analysis["emotional_tones"]["neutral"] += 1

        # 计算平均长度
        analysis["average_length"] = total_length / len(responses) if responses else 0

        # 找出常见模式
        sorted_categories = sorted(
            analysis["preferred_categories"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        analysis["common_patterns"] = [
            {"category": cat, "count": count}
            for cat, count in sorted_categories[:5]
        ]

        return analysis

    async def suggest_new_templates(
        self,
        patterns: Dict[str, Any]
    ) -> List[MemoryTemplate]:
        """
        根据模式建议新模板

        Args:
            patterns: 分析结果

        Returns:
            List[MemoryTemplate]: 建议的新模板列表
        """
        suggestions = []

        # 基于常见类别生成建议
        common_patterns = patterns.get("common_patterns", [])

        for pattern in common_patterns:
            category = pattern.get("category")

            # 根据类别生成建议
            if category == "greeting":
                suggestions.append(MemoryTemplate(
                    id="",
                    category=ResponseCategory.GREETING,
                    content="你好呀！今天有什么有趣的事吗？",
                    keywords=["你好", "有趣", "今天"],
                    metadata={"suggested": True, "based_on": "pattern_analysis"}
                ))
            elif category == "question":
                suggestions.append(MemoryTemplate(
                    id="",
                    category=ResponseCategory.QUESTION,
                    content="这是个好问题！让我想想...",
                    keywords=["问题", "想想"],
                    metadata={"suggested": True, "based_on": "pattern_analysis"}
                ))
            elif category == "emotional":
                suggestions.append(MemoryTemplate(
                    id="",
                    category=ResponseCategory.EMOTIONAL,
                    content="我理解你的感受，一直都在这里陪着你~",
                    keywords=["理解", "感受", "陪伴"],
                    metadata={"suggested": True, "based_on": "pattern_analysis"}
                ))

        logger.info(f"Suggested {len(suggestions)} new templates")
        return suggestions

    async def optimize_templates(self):
        """
        优化模板
        基于反馈历史优化现有模板
        """
        try:
            # 获取所有模板
            templates = await self.memory_manager.get_all_templates()

            optimized_count = 0

            for template in templates:
                # 检查是否需要优化
                if template.success_rate < 0.5 and template.usage_count > 5:
                    # 成功率低且使用次数多，考虑降级或删除
                    logger.warning(f"Template {template.id} has low success rate: {template.success_rate}")

                    # 这里可以添加优化逻辑，例如：
                    # - 调整模板内容
                    # - 降低优先级
                    # - 删除模板

                elif template.success_rate > 0.8 and template.usage_count > 10:
                    # 成功率高且使用次数多，标记为优质模板
                    logger.info(f"Template {template.id} is high quality: {template.success_rate}")

                    # 这里可以添加逻辑，例如：
                    # - 提高优先级
                    # - 推广到其他场景

            self.stats["templates_optimized"] = optimized_count
            logger.info(f"Optimized {optimized_count} templates")

        except Exception as e:
            logger.error(f"Error optimizing templates: {e}", exc_info=True)

    def get_learning_stats(self) -> Dict[str, Any]:
        """
        获取学习统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            **self.stats,
            "feedback_history_size": len(self.feedback_history),
            "patterns": {
                "successful_templates_count": len(self.patterns["successful_templates"]),
                "failed_templates_count": len(self.patterns["failed_templates"]),
                "user_preferences_count": len(self.patterns["user_preferences"])
            }
        }

    def clear_history(self):
        """清空反馈历史"""
        self.feedback_history.clear()
        logger.info("Feedback history cleared")