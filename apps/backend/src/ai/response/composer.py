"""
Response Composer - 响应片段组合系统
===================================
实现模板片段的切分与重组

核心功能：
1. 模板片段化 - 将模板切分为可复用片段
2. 片段重组 - 根据上下文组合片段生成响应
3. 平滑过渡 - 确保组合后的响应自然流畅

性能目标：组合时间 < 2ms
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class FragmentType(Enum):
    """片段类型"""

    GREETING = "greeting"
    QUESTION_RESPONSE = "question_response"
    EMOTION_EXPRESSION = "emotion_expression"
    TRANSITION = "transition"
    CLOSING = "closing"
    FILLER = "filler"


@dataclass
class Fragment:
    """响应片段"""

    id: str
    content: str
    type: FragmentType
    keywords: List[str]
    context_tags: List[str]
    priority: int = 5
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComposedResponse:
    """组合后的响应"""

    text: str
    fragments_used: List[str]
    composition_time_ms: float
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class FragmentComposer:
    """
    片段组合器
    ===========

    设计原理：
    1. 将模板切分为独立片段（问候、回答、情感、过渡、结束）
    2. 根据上下文选择合适的片段
    3. 智能拼接，确保自然流畅

    组合策略：
    - 高匹配（>0.8）：使用完整模板
    - 中匹配（0.5-0.8）：组合相关片段
    - 低匹配（<0.5）：使用通用片段 + LLM 补充
    """

    def __init__(self):
        self.fragments: Dict[str, Fragment] = {}
        self.fragment_index: Dict[FragmentType, List[str]] = {
            ftype: [] for ftype in FragmentType
        }

        self.stats = {
            "total_compositions": 0,
            "average_composition_time": 0.0,
            "fragments_used": 0,
        }

        self._init_default_fragments()

    def _init_default_fragments(self):
        """初始化默认片段库"""
        default_fragments = [
            Fragment(
                id="greeting_1",
                content="嗨！",
                type=FragmentType.GREETING,
                keywords=["你好", "嗨", "hi", "hello"],
                context_tags=["casual", "friendly"],
                priority=8,
            ),
            Fragment(
                id="greeting_2",
                content="你好呀！",
                type=FragmentType.GREETING,
                keywords=["你好", "嗨"],
                context_tags=["casual", "friendly"],
                priority=7,
            ),
            Fragment(
                id="transition_1",
                content="让我想想...",
                type=FragmentType.TRANSITION,
                keywords=[],
                context_tags=["thinking", "uncertain"],
                priority=5,
            ),
            Fragment(
                id="transition_2",
                content="关于这个问题，",
                type=FragmentType.TRANSITION,
                keywords=["问题", "疑问"],
                context_tags=["formal", "helpful"],
                priority=6,
            ),
            Fragment(
                id="emotion_happy_1",
                content="我很开心能帮到你！",
                type=FragmentType.EMOTION_EXPRESSION,
                keywords=["开心", "高兴", "帮助"],
                context_tags=["positive", "helpful"],
                priority=7,
            ),
            Fragment(
                id="closing_1",
                content="还有什么我能帮你的吗？",
                type=FragmentType.CLOSING,
                keywords=["帮助", "需要"],
                context_tags=["helpful", "polite"],
                priority=6,
            ),
            Fragment(
                id="filler_1",
                content="嗯...",
                type=FragmentType.FILLER,
                keywords=[],
                context_tags=["casual"],
                priority=3,
            ),
        ]

        for fragment in default_fragments:
            self.add_fragment(fragment)

    def add_fragment(self, fragment: Fragment):
        """添加片段到组合器"""
        self.fragments[fragment.id] = fragment
        self.fragment_index[fragment.type].append(fragment.id)
        logger.debug(f"Added fragment: {fragment.id} ({fragment.type.value})")

    def compose(
        self,
        template_fragments: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> ComposedResponse:
        """
        组合响应

        Args:
            template_fragments: 模板片段 ID 列表
            context: 上下文信息

        Returns:
            ComposedResponse: 组合后的响应
        """
        start_time = time.time()
        context = context or {}

        selected_fragments = self._select_fragments(template_fragments, context)

        response_text = self._assemble_fragments(selected_fragments, context)

        confidence = self._calculate_confidence(selected_fragments, context)

        composition_time = (time.time() - start_time) * 1000

        self._update_stats(composition_time, len(selected_fragments))

        return ComposedResponse(
            text=response_text,
            fragments_used=[f.id for f in selected_fragments],
            composition_time_ms=composition_time,
            confidence=confidence,
            metadata={
                "fragment_types": [f.type.value for f in selected_fragments],
                "context_tags": list(
                    set([tag for f in selected_fragments for tag in f.context_tags])
                ),
            },
        )

    def compose_from_template(
        self,
        template_content: str,
        match_score: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> ComposedResponse:
        """
        从模板内容组合响应

        Args:
            template_content: 模板内容
            match_score: 匹配分数
            context: 上下文

        Returns:
            ComposedResponse: 组合后的响应
        """
        start_time = time.time()
        context = context or {}

        if match_score > 0.8:
            composition_time = (time.time() - start_time) * 1000
            return ComposedResponse(
                text=template_content,
                fragments_used=["complete_template"],
                composition_time_ms=composition_time,
                confidence=match_score,
                metadata={"strategy": "complete_template"},
            )

        fragments = self._split_template(template_content, context)

        selected_fragments = self._select_fragments(
            [f.id for f in fragments], context
        )

        response_text = self._assemble_fragments(selected_fragments, context)

        confidence = self._calculate_confidence(selected_fragments, context)

        composition_time = (time.time() - start_time) * 1000

        self._update_stats(composition_time, len(selected_fragments))

        return ComposedResponse(
            text=response_text,
            fragments_used=[f.id for f in selected_fragments],
            composition_time_ms=composition_time,
            confidence=min(match_score, confidence),
            metadata={
                "strategy": "fragment_composition",
                "original_match_score": match_score,
            },
        )

    def _split_template(
        self, template: str, context: Dict[str, Any]
    ) -> List[Fragment]:
        """将模板切分为片段"""
        sentences = []
        current = ""
        for char in template:
            current += char
            if char in ["。", "！", "？", ".", "!", "?"]:
                if current.strip():
                    sentences.append(current.strip())
                current = ""

        if current.strip():
            sentences.append(current.strip())

        fragments = []
        for i, sentence in enumerate(sentences):
            ftype = self._infer_fragment_type(sentence, i, len(sentences))
            fragment = Fragment(
                id=f"temp_fragment_{i}",
                content=sentence,
                type=ftype,
                keywords=self._extract_keywords(sentence),
                context_tags=[],
                priority=5,
            )
            fragments.append(fragment)
            self.fragments[fragment.id] = fragment

        return fragments

    def _infer_fragment_type(
        self, sentence: str, index: int, total: int
    ) -> FragmentType:
        """推断片段类型"""
        if index == 0:
            if any(word in sentence for word in ["你好", "嗨", "hi", "hello"]):
                return FragmentType.GREETING

        if index == total - 1:
            if any(word in sentence for word in ["吗", "呢", "帮", "需要"]):
                return FragmentType.CLOSING

        if any(word in sentence for word in ["开心", "高兴", "难过", "抱歉"]):
            return FragmentType.EMOTION_EXPRESSION

        if any(word in sentence for word in ["让我", "想想", "关于", "对于"]):
            return FragmentType.TRANSITION

        return FragmentType.QUESTION_RESPONSE

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        stopwords = {
            "你",
            "我",
            "他",
            "她",
            "的",
            "了",
            "吗",
            "呢",
            "吧",
            "是",
            "在",
            "有",
        }
        words = []
        for char in text:
            if "\u4e00" <= char <= "\u9fff":
                words.append(char)

        keywords = [w for w in words if w not in stopwords]
        return keywords

    def _select_fragments(
        self, fragment_ids: List[str], context: Dict[str, Any]
    ) -> List[Fragment]:
        """选择合适的片段"""
        selected = []
        for fid in fragment_ids:
            fragment = self.fragments.get(fid)
            if fragment:
                selected.append(fragment)

        selected.sort(key=lambda f: f.priority, reverse=True)
        return selected

    def _assemble_fragments(
        self, fragments: List[Fragment], context: Dict[str, Any]
    ) -> str:
        """组装片段为完整响应"""
        if not fragments:
            return "我不太确定该怎么回答..."

        parts = []
        for fragment in fragments:
            parts.append(fragment.content)

        response = "".join(parts)

        response = response.replace("。。", "。")
        response = response.replace("！！", "！")
        response = response.replace("？？", "？")

        return response

    def _calculate_confidence(
        self, fragments: List[Fragment], context: Dict[str, Any]
    ) -> float:
        """计算组合置信度"""
        if not fragments:
            return 0.0

        avg_priority = sum(f.priority for f in fragments) / len(fragments)
        confidence = min(1.0, avg_priority / 10.0)

        return confidence

    def _update_stats(self, composition_time: float, fragments_count: int):
        """更新统计信息"""
        self.stats["total_compositions"] += 1
        self.stats["fragments_used"] += fragments_count

        total = self.stats["total_compositions"]
        self.stats["average_composition_time"] = (
            self.stats["average_composition_time"] * (total - 1) + composition_time
        ) / total

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()


class ResponseComposer:
    """
    响应组合器主类
    ==============

    整合 TemplateMatcher 和 FragmentComposer
    提供统一的响应组合接口
    """

    def __init__(self):
        self.fragment_composer = FragmentComposer()
        logger.info("ResponseComposer initialized")

    def compose_response(
        self,
        template_content: str,
        match_score: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> ComposedResponse:
        """
        组合响应

        Args:
            template_content: 模板内容
            match_score: 匹配分数
            context: 上下文

        Returns:
            ComposedResponse: 组合后的响应
        """
        return self.fragment_composer.compose_from_template(
            template_content, match_score, context
        )

    def add_fragment(self, fragment: Fragment):
        """添加自定义片段"""
        self.fragment_composer.add_fragment(fragment)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.fragment_composer.get_stats()
