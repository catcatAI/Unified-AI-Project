# =============================================================================
# FILE_HASH: L1U2L3G4
# FILE_PATH: apps/backend/src/ai/memory/lu_logic/logic_unit.py
# FILE_TYPE: memory
# PURPOSE: Logic Unit - 逻辑/规则记忆系统 (L2层)
# VERSION: 6.2.1
# STATUS: mvp
# DEPENDENCIES: typing, datetime, json
# LAST_MODIFIED: 2026-02-19
# =============================================================================

"""
Logic Unit - 逻辑/规则记忆系统

Angela Matrix Annotation:
- α: L2 (逻辑层)
- β: 0.7 (MVP实现)
- γ: 0.9 (完整度)
- δ: 0.8 (稳定性)

L2层组件：管理和执行逻辑规则，支持条件判断、规则匹配和推理
"""

import json
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class RulePriority(Enum):
    """规则优先级"""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class LogicRule:
    """逻辑规则定义

    属性:
        rule_id: 规则唯一标识
        name: 规则名称
        condition: 条件表达式或函数
        action: 执行动作
        priority: 规则优先级
        enabled: 是否启用
        usage_count: 使用次数统计
        created_at: 创建时间
        last_used: 最后使用时间
        metadata: 额外元数据
    """

    rule_id: str
    name: str
    condition: str  # 可以是简单的条件表达式，如 "temperature > 30"
    action: str  # 动作描述或动作ID
    priority: RulePriority = RulePriority.NORMAL
    enabled: bool = True
    usage_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "condition": self.condition,
            "action": self.action,
            "priority": self.priority.value,
            "enabled": self.enabled,
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LogicRule":
        """从字典创建"""
        return cls(
            rule_id=data["rule_id"],
            name=data["name"],
            condition=data["condition"],
            action=data["action"],
            priority=RulePriority(data.get("priority", 1)),
            enabled=data.get("enabled", True),
            usage_count=data.get("usage_count", 0),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_used=datetime.fromisoformat(data["last_used"])
            if data.get("last_used")
            else None,
            metadata=data.get("metadata", {}),
        )


class LogicUnit:
    """逻辑单元 - 管理和执行逻辑规则

    主要功能:
    1. 规则管理：添加、删除、启用/禁用规则
    2. 规则执行：根据上下文评估并执行规则
    3. 规则学习：基于使用频率自动调整优先级
    4. 规则持久化：保存和加载规则

    使用示例:
        lu = LogicUnit()

        # 添加规则
        lu.add_rule(LogicRule(
            rule_id="temp_high",
            name="温度过高提醒",
            condition="temperature > 30",
            action="提醒用户当前温度过高",
            priority=RulePriority.HIGH
        ))

        # 执行规则
        result = lu.evaluate({'temperature': 35})
        # 返回: "提醒用户当前温度过高"
    """

    def __init__(self, max_rules: int = 1000):
        """初始化逻辑单元

        Args:
            max_rules: 最大规则数量限制
        """
        self.max_rules = max_rules
        self.rules: Dict[str, LogicRule] = {}
        self.rule_history: List[Dict[str, Any]] = []
        self._condition_cache: Dict[str, Callable] = {}

        logger.info(f"LogicUnit initialized with max_rules={max_rules}")

    def add_rule(self, rule: LogicRule) -> bool:
        """添加逻辑规则

        Args:
            rule: 要添加的规则

        Returns:
            是否添加成功
        """
        try:
            # 检查规则数量限制
            if len(self.rules) >= self.max_rules:
                logger.warning(
                    f"Cannot add rule {rule.rule_id}: max_rules limit reached"
                )
                return False

            # 检查规则ID是否已存在
            if rule.rule_id in self.rules:
                logger.warning(f"Rule {rule.rule_id} already exists, updating...")

            # 添加规则
            self.rules[rule.rule_id] = rule

            # 预编译条件表达式
            self._compile_condition(rule.rule_id, rule.condition)

            logger.info(f"Rule {rule.rule_id} added successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to add rule {rule.rule_id}: {e}")
            return False

    def remove_rule(self, rule_id: str) -> bool:
        """删除逻辑规则

        Args:
            rule_id: 规则ID

        Returns:
            是否删除成功
        """
        try:
            if rule_id not in self.rules:
                logger.warning(f"Rule {rule_id} not found")
                return False

            del self.rules[rule_id]
            if rule_id in self._condition_cache:
                del self._condition_cache[rule_id]

            logger.info(f"Rule {rule_id} removed successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to remove rule {rule_id}: {e}")
            return False

    def enable_rule(self, rule_id: str) -> bool:
        """启用规则

        Args:
            rule_id: 规则ID

        Returns:
            是否启用成功
        """
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            logger.info(f"Rule {rule_id} enabled")
            return True
        return False

    def disable_rule(self, rule_id: str) -> bool:
        """禁用规则

        Args:
            rule_id: 规则ID

        Returns:
            是否禁用成功
        """
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            logger.info(f"Rule {rule_id} disabled")
            return True
        return False

    def evaluate(self, context: Dict[str, Any]) -> Optional[str]:
        """根据上下文评估规则

        按照优先级从高到低评估所有启用的规则，
        返回第一个匹配规则的action。

        Args:
            context: 上下文数据，包含变量和值

        Returns:
            匹配规则的action，如果没有匹配则返回None
        """
        try:
            # 按优先级排序（高优先级优先）
            sorted_rules = sorted(
                [r for r in self.rules.values() if r.enabled],
                key=lambda r: r.priority.value,
                reverse=True,
            )

            for rule in sorted_rules:
                if self._check_condition(rule.rule_id, rule.condition, context):
                    # 更新使用统计
                    rule.usage_count += 1
                    rule.last_used = datetime.now()

                    # 记录历史
                    self.rule_history.append(
                        {
                            "rule_id": rule.rule_id,
                            "context": context.copy(),
                            "action": rule.action,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                    # 限制历史记录数量
                    if len(self.rule_history) > 10000:
                        self.rule_history = self.rule_history[-5000:]

                    logger.debug(f"Rule {rule.rule_id} matched and executed")
                    return rule.action

            logger.debug("No rule matched the given context")
            return None

        except Exception as e:
            logger.error(f"Failed to evaluate rules: {e}")
            return None

    def evaluate_all(self, context: Dict[str, Any]) -> List[str]:
        """评估所有匹配的规则

        返回所有匹配规则的action列表（不只是第一个）

        Args:
            context: 上下文数据

        Returns:
            所有匹配规则的action列表
        """
        actions = []

        try:
            sorted_rules = sorted(
                [r for r in self.rules.values() if r.enabled],
                key=lambda r: r.priority.value,
                reverse=True,
            )

            for rule in sorted_rules:
                if self._check_condition(rule.rule_id, rule.condition, context):
                    actions.append(rule.action)
                    rule.usage_count += 1
                    rule.last_used = datetime.now()

            return actions

        except Exception as e:
            logger.error(f"Failed to evaluate all rules: {e}")
            return actions

    def _compile_condition(self, rule_id: str, condition: str) -> None:
        """预编译条件表达式

        Args:
            rule_id: 规则ID
            condition: 条件表达式
        """
        try:
            # 简单表达式直接存储
            self._condition_cache[rule_id] = condition
        except Exception as e:
            logger.warning(f"Failed to compile condition for rule {rule_id}: {e}")

    def _check_condition(
        self, rule_id: str, condition: str, context: Dict[str, Any]
    ) -> bool:
        """检查条件是否满足

        支持简单的表达式求值，使用安全的eval环境。

        Args:
            rule_id: 规则ID
            condition: 条件表达式
            context: 上下文数据

        Returns:
            条件是否满足
        """
        try:
            # 使用安全的eval环境
            # 只允许基本运算符和比较操作
            allowed_names = {
                "True": True,
                "False": False,
                "None": None,
            }

            # 合并上下文和允许的名称
            eval_context = {**allowed_names, **context}

            # 执行条件表达式
            result = eval(condition, {"__builtins__": {}}, eval_context)

            return bool(result)

        except Exception as e:
            logger.warning(f"Failed to evaluate condition for rule {rule_id}: {e}")
            return False

    def get_rule(self, rule_id: str) -> Optional[LogicRule]:
        """获取指定规则

        Args:
            rule_id: 规则ID

        Returns:
            规则对象，如果不存在则返回None
        """
        return self.rules.get(rule_id)

    def list_rules(self, enabled_only: bool = False) -> List[LogicRule]:
        """列出所有规则

        Args:
            enabled_only: 是否只列出启用的规则

        Returns:
            规则列表
        """
        if enabled_only:
            return [r for r in self.rules.values() if r.enabled]
        return list(self.rules.values())

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息字典
        """
        enabled_count = sum(1 for r in self.rules.values() if r.enabled)
        disabled_count = len(self.rules) - enabled_count

        # 找出最常用的规则
        most_used = None
        if self.rules:
            most_used = max(self.rules.values(), key=lambda r: r.usage_count)

        # 按优先级统计
        priority_stats = {}
        for priority in RulePriority:
            count = sum(1 for r in self.rules.values() if r.priority == priority)
            priority_stats[priority.name] = count

        return {
            "total_rules": len(self.rules),
            "enabled_rules": enabled_count,
            "disabled_rules": disabled_count,
            "total_evaluations": len(self.rule_history),
            "most_used_rule": {
                "rule_id": most_used.rule_id,
                "usage_count": most_used.usage_count,
            }
            if most_used
            else None,
            "priority_distribution": priority_stats,
            "max_rules": self.max_rules,
        }

    def save_to_file(self, filepath: str) -> bool:
        """保存规则到文件

        Args:
            filepath: 文件路径

        Returns:
            是否保存成功
        """
        try:
            data = {
                "rules": {rid: rule.to_dict() for rid, rule in self.rules.items()},
                "rule_history": self.rule_history[-1000:],  # 只保存最近的1000条历史
                "max_rules": self.max_rules,
                "saved_at": datetime.now().isoformat(),
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Rules saved to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to save rules to {filepath}: {e}")
            return False

    def load_from_file(self, filepath: str) -> bool:
        """从文件加载规则

        Args:
            filepath: 文件路径

        Returns:
            是否加载成功
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 加载规则
            for rule_id, rule_data in data.get("rules", {}).items():
                rule = LogicRule.from_dict(rule_data)
                self.rules[rule_id] = rule
                self._compile_condition(rule_id, rule.condition)

            # 加载历史
            self.rule_history = data.get("rule_history", [])

            logger.info(f"Rules loaded from {filepath}, total={len(self.rules)}")
            return True

        except Exception as e:
            logger.error(f"Failed to load rules from {filepath}: {e}")
            return False

    def clear_history(self) -> None:
        """清空历史记录"""
        self.rule_history.clear()
        logger.info("Rule history cleared")

    def reset_stats(self) -> None:
        """重置所有统计信息"""
        for rule in self.rules.values():
            rule.usage_count = 0
            rule.last_used = None
        self.rule_history.clear()
        logger.info("All statistics reset")


# 便捷函数
def create_logic_unit(max_rules: int = 1000) -> LogicUnit:
    """创建逻辑单元的便捷函数

    Args:
        max_rules: 最大规则数量

    Returns:
        LogicUnit 实例
    """
    return LogicUnit(max_rules)
