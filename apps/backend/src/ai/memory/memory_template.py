"""
记忆模板结构
============
定义回應模板的核心数据结构，用于记忆增强系统。

设计目标：
1. 减少 LLM 调用次数，提高响应速度
2. 通过模板复用，降低 Token 使用量
3. 支持动态学习和优化
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field
import json
import logging

logger = logging.getLogger(__name__)


class ResponseCategory(Enum):
    """回應类别枚举"""
    # 基础类别
    GREETING = "greeting"          # 问候
    FAREWELL = "farewell"          # 告别
    SMALL_TALK = "small_talk"      # 闲聊
    QUESTION = "question"          # 问题
    COMMAND = "command"            # 命令

    # 情绪类别
    EMOTIONAL = "emotional"        # 情绪化回應
    CASUAL = "casual"              # 随意对话

    # 高级类别
    AFFIRMATION = "affirmation"    # 肯定
    NEGATION = "negation"          # 否定
    CURIOSITY = "curiosity"        # 好奇
    INTIMACY = "intimacy"          # 亲密
    SUPPORT = "support"            # 支持
    APOLOGY = "apology"            # 道歉
    GRATITUDE = "gratitude"        # 感谢
    HELP = "help"                  # 帮助
    UNKNOWN = "unknown"            # 未知类别


@dataclass
class AngelaState:
    """
    Angela 的 αβγδ 状态映射
    用于模板匹配时的状态相似度计算
    """
    # Alpha (意识水平): 0-1, 高表示清醒活跃
    alpha: Dict[str, float] = field(default_factory=dict)

    # Beta (情绪状态): 情绪分布
    beta: Dict[str, float] = field(default_factory=dict)

    # Gamma (认知负荷): 0-1, 高表示思考中
    gamma: Dict[str, float] = field(default_factory=dict)

    # Delta (生理状态): 0-1, 表示疲劳程度
    delta: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "alpha": self.alpha,
            "beta": self.beta,
            "gamma": self.gamma,
            "delta": self.delta
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AngelaState":
        """从字典创建"""
        return cls(
            alpha=data.get("alpha", {}),
            beta=data.get("beta", {}),
            gamma=data.get("gamma", {}),
            delta=data.get("delta", {})
        )


@dataclass
class UserImpression:
    """
    用户印象模型
    用于个性化回應模板匹配
    """
    # 用户关系度: 0-1, 陌生人到亲密朋友
    relationship_level: float = 0.3

    # 用户偏好风格: formal, casual, playful, serious
    preferred_style: str = "casual"

    # 对话历史长度
    interaction_count: int = 0

    # 用户特征标签
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "relationship_level": self.relationship_level,
            "preferred_style": self.preferred_style,
            "interaction_count": self.interaction_count,
            "tags": self.tags
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserImpression":
        """从字典创建"""
        return cls(
            relationship_level=data.get("relationship_level", 0.3),
            preferred_style=data.get("preferred_style", "casual"),
            interaction_count=data.get("interaction_count", 0),
            tags=data.get("tags", [])
        )


@dataclass
class MemoryTemplate:
    """
    记忆回應模板
    ===============
    存储预计算的回應模板，用于快速检索和复用
    """
    # 基本标识
    id: str
    category: ResponseCategory
    content: str

    # 检索关键词
    keywords: List[str] = field(default_factory=list)

    # Angela 状态（用于匹配）
    angela_state: AngelaState = field(default_factory=AngelaState)

    # 用户印象（用于个性化）
    user_impression: UserImpression = field(default_factory=UserImpression)

    # 使用统计
    usage_count: int = 0
    success_rate: float = 1.0  # 初始成功率 100%

    # 时间戳
    last_used: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "category": self.category.value,
            "content": self.content,
            "keywords": self.keywords,
            "angela_state": self.angela_state.to_dict(),
            "user_impression": self.user_impression.to_dict(),
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryTemplate":
        """从字典创建"""
        # 解析类别
        category = ResponseCategory(data.get("category", "unknown"))

        # 解析时间戳
        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow()
        updated_at = datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.utcnow()
        last_used = datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None

        return cls(
            id=data["id"],
            category=category,
            content=data["content"],
            keywords=data.get("keywords", []),
            angela_state=AngelaState.from_dict(data.get("angela_state", {})),
            user_impression=UserImpression.from_dict(data.get("user_impression", {})),
            usage_count=data.get("usage_count", 0),
            success_rate=data.get("success_rate", 1.0),
            last_used=last_used,
            created_at=created_at,
            updated_at=updated_at,
            metadata=data.get("metadata", {})
        )

    def record_usage(self, success: bool = True):
        """记录使用"""
        self.usage_count += 1
        self.last_used = datetime.utcnow()

        # 更新成功率（移动平均：80% 历史 + 20% 新反馈）
        current_success = 1.0 if success else 0.0
        self.success_rate = (self.success_rate * 0.8) + (current_success * 0.2)

        self.updated_at = datetime.utcnow()

    def is_suitable_for(self, angela_state: AngelaState, user_impression: UserImpression) -> bool:
        """
        判断模板是否适合当前状态
        简化版本：只检查基本条件
        """
        # TODO: 实现更复杂的相似度计算
        return True

    def calculate_match_score(
        self,
        query: str,
        angela_state: AngelaState,
        user_impression: UserImpression
    ) -> float:
        """
        计算匹配分数
        返回 0-1 之间的分数
        """
        # 1. 关键词匹配 (30%)
        keyword_score = self._calculate_keyword_match(query)

        # 2. 状态相似度 (40%)
        state_score = self._calculate_state_similarity(angela_state)

        # 3. 用户印象匹配 (20%)
        impression_score = self._calculate_impression_similarity(user_impression)

        # 4. 成功率权重 (10%)
        success_score = self.success_rate

        # 综合评分
        total_score = (
            keyword_score * 0.30 +
            state_score * 0.40 +
            impression_score * 0.20 +
            success_score * 0.10
        )

        return total_score

    def _calculate_keyword_match(self, query: str) -> float:
        """计算关键词匹配分数"""
        if not self.keywords:
            return 0.5  # 没有关键词，中等分数

        query_lower = query.lower()
        matches = sum(1 for kw in self.keywords if kw.lower() in query_lower)
        return matches / len(self.keywords)

    def _calculate_state_similarity(self, current_state: AngelaState) -> float:
        """计算状态相似度"""
        # 简化版本：返回 0.8
        # 完整版本应该计算 αβγδ 各维度的相似度
        return 0.8

    def _calculate_impression_similarity(self, current_impression: UserImpression) -> float:
        """计算用户印象相似度"""
        # 简化版本：返回 0.7
        # 完整版本应该比较关系度和偏好风格
        return 0.7


def generate_template_id(content: str) -> str:
    """生成模板 ID"""
    import hashlib
    content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"tpl_{timestamp}_{content_hash}"


def create_template(
    content: str,
    category: ResponseCategory,
    keywords: List[str] = None,
    angela_state: AngelaState = None,
    user_impression: UserImpression = None,
    metadata: Dict[str, Any] = None
) -> MemoryTemplate:
    """
    创建新模板的便捷函数
    """
    return MemoryTemplate(
        id=generate_template_id(content),
        category=category,
        content=content,
        keywords=keywords or [],
        angela_state=angela_state or AngelaState(),
        user_impression=user_impression or UserImpression(),
        metadata=metadata or {}
    )