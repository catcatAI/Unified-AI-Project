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
from datetime import datetime
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
        self.fragment_index: Dict[FragmentType, List[str]] = {ftype: [] for ftype in FragmentType}

        self.stats = {
            "total_compositions": 0,
            "average_composition_time": 0.0,
            "fragments_used": 0,
        }

        self._init_default_fragments()

    def _init_default_fragments(self) -> None:
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

    def add_fragment(self, fragment: Fragment) -> None:
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
            self._update_stats(composition_time, 1)
            return ComposedResponse(
                text=template_content,
                fragments_used=["complete_template"],
                composition_time_ms=composition_time,
                confidence=match_score,
                metadata={"strategy": "complete_template"},
            )

        fragments = self._split_template(template_content, context)

        selected_fragments = self._select_fragments([f.id for f in fragments], context)

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

    def _split_template(self, template: str, context: Dict[str, Any]) -> List[Fragment]:
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
                context_tags=list(context.keys()) if context else [],
                priority=5,
            )
            fragments.append(fragment)
            self.fragments[fragment.id] = fragment

        return fragments

    def _infer_fragment_type(self, sentence: str, index: int, total: int) -> FragmentType:
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

    def _select_fragments(self, fragment_ids: List[str], context: Dict[str, Any]) -> List[Fragment]:
        """选择合适的片段"""
        selected = []
        for fid in fragment_ids:
            fragment = self.fragments.get(fid)
            if fragment:
                selected.append(fragment)

        selected.sort(key=lambda f: f.priority, reverse=True)
        return selected

    def _assemble_fragments(self, fragments: List[Fragment], context: Dict[str, Any]) -> str:
        """组装片段为完整响应"""
        if not fragments:
            return "我不太确定该怎么回答..."

        parts = []
        for fragment in fragments:
            parts.append(fragment.content)

        response = "".join(parts)

        if context:
            user_name = context.get("user_name") or context.get("name")
            if user_name:
                response = response.replace("{user_name}", user_name)

        response = response.replace("。。", "。")
        response = response.replace("！！", "！")
        response = response.replace("？？", "？")

        return response

    def _calculate_confidence(self, fragments: List[Fragment], context: Dict[str, Any]) -> float:
        """计算组合置信度"""
        if not fragments:
            return 0.0

        avg_priority = sum(f.priority for f in fragments) / len(fragments)
        base = min(1.0, avg_priority / 10.0)

        types_used = len(set(f.type for f in fragments))
        type_bonus = min(0.2, types_used * 0.05)

        context_bonus = min(0.1, len(context) * 0.02) if context else 0.0

        return min(1.0, base + type_bonus + context_bonus)

    def _update_stats(self, composition_time: float, fragments_count: int) -> None:
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


class NeuroFragment:
    """
    神经片段 (Neuro Fragment) — 带 8D 权重的语义片段
    ==============================================
    用于 NeuroBlender 的 dynamic synthesis。
    """
    def __init__(
        self,
        fragment_id: str,
        content: str,
        category: str,
        structural_type: str = "statement",
        alpha_energy: float = 0.5,
        beta_curiosity: float = 0.5,
        gamma_valence: float = 0.0,
        delta_intimacy: float = 0.3,
        epsilon_precision: float = 0.5,
        zeta_temporal: float = 0.5,
        theta_meta: float = 0.3,
        eta_execution: float = 0.5,
        context_tags: Optional[List[str]] = None,
    ):
        self.fragment_id = fragment_id
        self.content = content
        self.category = category
        self.structural_type = structural_type
        self.alpha_energy = max(0.0, min(1.0, alpha_energy))
        self.beta_curiosity = max(0.0, min(1.0, beta_curiosity))
        self.gamma_valence = max(-1.0, min(1.0, gamma_valence))
        self.delta_intimacy = max(0.0, min(1.0, delta_intimacy))
        self.epsilon_precision = max(0.0, min(1.0, epsilon_precision))
        self.zeta_temporal = max(0.0, min(1.0, zeta_temporal))
        self.theta_meta = max(0.0, min(1.0, theta_meta))
        self.eta_execution = max(0.0, min(1.0, eta_execution))
        self.context_tags = context_tags or []

    def state_vector(self) -> List[float]:
        """返回 8D 权重向量，用于余弦相似度计算"""
        return [
            self.alpha_energy,
            self.beta_curiosity,
            self.gamma_valence,
            self.delta_intimacy,
            self.epsilon_precision,
            self.zeta_temporal,
            self.theta_meta,
            self.eta_execution,
        ]


@dataclass
class ValueRangeMapping:
    """數值→語意描述映射，用於翻譯學習層（C6）"""
    axis_field: str        # e.g. "gamma.indolence"
    range_lo: float
    range_hi: float
    description: str       # LLM 或正則萃取的語意描述
    confidence: float      # 0-1，基於 usage_count
    usage_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_used_at: Optional[datetime] = None

    def covers(self, value: float) -> bool:
        """Execute the covers operation."""
        return self.range_lo <= value <= self.range_hi

    def narrow(self, value: float) -> None:
        """Execute the narrow operation."""
        self.range_lo = max(self.range_lo, value - 0.01)
        self.range_hi = min(self.range_hi, value + 0.01)


class NeuroVocabulary:
    """
    神经词汇表 (Neuro Vocabulary)
    =============================
    管理所有带 8D 标签的语义片段和數值區間映射。
    支持从 config 加载和从 TemplateLibrary 自动分解。
    """

    def __init__(self):
        self._fragments: Dict[str, NeuroFragment] = {}
        self._category_index: Dict[str, List[str]] = {}
        self._structural_index: Dict[str, List[str]] = {}
        self._value_range_mappings: Dict[str, List[ValueRangeMapping]] = {}

    def add_fragment(self, fragment: NeuroFragment) -> None:
        """Add a fragment."""
        self._fragments[fragment.fragment_id] = fragment
        self._category_index.setdefault(fragment.category, []).append(fragment.fragment_id)
        self._structural_index.setdefault(fragment.structural_type, []).append(fragment.fragment_id)

    def get_by_id(self, fid: str) -> Optional[NeuroFragment]:
        """Get the by id by self."""
        return self._fragments.get(fid)

    def get_by_category(self, category: str) -> List[NeuroFragment]:
        """Get the by category by self."""
        return [self._fragments[fid] for fid in self._category_index.get(category, []) if fid in self._fragments]

    def get_by_structural_type(self, stype: str) -> List[NeuroFragment]:
        """Get the by structural type by self."""
        return [self._fragments[fid] for fid in self._structural_index.get(stype, []) if fid in self._fragments]

    def all_fragments(self) -> List[NeuroFragment]:
        """Execute the all fragments operation."""
        return list(self._fragments.values())

    def total_count(self) -> int:
        """Execute the total count operation."""
        return len(self._fragments)

    # ── 數值區間映射（C6 翻譯學習層）────────────────────────────────────

    def get_description(self, axis_field: str, value: float) -> Optional[str]:
        """找出所有 covers(value) 的 mapping，回傳 confidence 最高的 description"""
        mappings = self._value_range_mappings.get(axis_field, [])
        if not mappings:
            return None
        candidates = [(m.confidence, m.description) for m in mappings if m.covers(value)]
        if not candidates:
            return None
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    def learn_mapping(self, axis_field: str, value: float, description: str) -> None:
        """學習或更新數值→語意映射"""
        now = datetime.now()
        existing = self._value_range_mappings.get(axis_field, [])

        for m in existing:
            if m.covers(value):
                m.narrow(value)
                m.usage_count += 1
                m.confidence = min(1.0, m.confidence + 0.05)
                m.last_used_at = now
                # 若新描述更長（更精確），取代舊描述
                if len(description) > len(m.description):
                    m.description = description
                return

        # 新增 mapping
        mappings = self._value_range_mappings.setdefault(axis_field, [])
        mappings.append(ValueRangeMapping(
            axis_field=axis_field,
            range_lo=value,
            range_hi=value,
            description=description,
            confidence=0.3,
            usage_count=1,
            created_at=now,
            last_used_at=now,
        ))

    def get_value_range_mappings(self, axis_field: str) -> List[ValueRangeMapping]:
        """回傳指定軸點位的所有 mapping"""
        return list(self._value_range_mappings.get(axis_field, []))

    def serialize_mappings(self, max_age_days: float = 90.0) -> List[Dict[str, Any]]:
        """序列化所有映射（用於持久化），可選清除過舊項目"""
        now = datetime.now()
        result = []
        stale_fields = []
        for field_name, mappings in self._value_range_mappings.items():
            alive = []
            for m in mappings:
                age = (now - m.created_at).days
                if age > max_age_days and m.usage_count < 2:
                    continue
                alive.append({
                    "axis_field": m.axis_field,
                    "range_lo": m.range_lo,
                    "range_hi": m.range_hi,
                    "description": m.description,
                    "confidence": m.confidence,
                    "usage_count": m.usage_count,
                    "created_at": m.created_at.isoformat(),
                    "last_used_at": m.last_used_at.isoformat() if m.last_used_at else None,
                })
            if alive:
                result.extend(alive)
            else:
                stale_fields.append(field_name)
        for f in stale_fields:
            del self._value_range_mappings[f]
        return result

    def load_mappings_from_config(self, config_data: List[Dict[str, Any]]) -> None:
        """從配置加載映射"""
        if not config_data:
            return
        for item in config_data:
            m = ValueRangeMapping(
                axis_field=item["axis_field"],
                range_lo=item["range_lo"],
                range_hi=item["range_hi"],
                description=item["description"],
                confidence=item.get("confidence", 0.3),
                usage_count=item.get("usage_count", 0),
                created_at=datetime.fromisoformat(item["created_at"]) if "created_at" in item else datetime.now(),
                last_used_at=datetime.fromisoformat(item["last_used_at"]) if item.get("last_used_at") else None,
            )
            self._value_range_mappings.setdefault(m.axis_field, []).append(m)

    # ── C6 Phase 5+：反向映射 + 信心衰減 ────────────────────────────────

    def find_axis_values(self, description: str, threshold: float = 0.3) -> List[Dict[str, Any]]:
        """反向映射：從語意描述找出對應的軸點位數值區間"""
        results = []
        desc_lower = description.lower()
        for field_name, mappings in self._value_range_mappings.items():
            for m in mappings:
                if m.confidence < threshold:
                    continue
                if desc_lower in m.description.lower() or m.description.lower() in desc_lower:
                    results.append({
                        "axis_field": m.axis_field,
                        "range_lo": m.range_lo,
                        "range_hi": m.range_hi,
                        "description": m.description,
                        "confidence": m.confidence,
                        "usage_count": m.usage_count,
                    })
        return results

    def get_uncovered_values(self, state_for_llm: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """找出 state 中尚未有 mapping 覆蓋的軸點位數值"""
        uncovered = []
        for axis_name, axis_data in state_for_llm.items():
            if not isinstance(axis_data, dict):
                continue
            vals = axis_data.get("values", {})
            for k, v in vals.items():
                field = f"{axis_name}.{k}"
                mappings = self._value_range_mappings.get(field, [])
                if not any(m.covers(v) for m in mappings):
                    uncovered.append({"axis_field": field, "value": v})
        return uncovered

    def decay_confidences(self, hours: float = 24.0, decay_rate: float = 0.01) -> None:
        """降低長時間未使用的 mapping 信心度"""
        now = datetime.now()
        for field_name, mappings in list(self._value_range_mappings.items()):
            alive = []
            for m in mappings:
                if m.last_used_at is None:
                    continue
                elapsed = (now - m.last_used_at).total_seconds() / 3600.0
                if elapsed > hours:
                    decay = decay_rate * (elapsed / hours)
                    m.confidence = max(0.0, m.confidence - decay)
                if m.confidence > 0.01:
                    alive.append(m)
            if alive:
                self._value_range_mappings[field_name] = alive
            else:
                del self._value_range_mappings[field_name]

    def detect_overlaps(self, axis_field: str) -> List[Dict[str, Any]]:
        """檢測同一軸點位上 range 重疊的 mappings"""
        mappings = sorted(
            self._value_range_mappings.get(axis_field, []),
            key=lambda m: m.range_lo,
        )
        overlaps = []
        for i in range(len(mappings) - 1):
            a = mappings[i]
            b = mappings[i + 1]
            if a.range_hi >= b.range_lo:
                overlaps.append({
                    "a": {"description": a.description, "range_lo": a.range_lo, "range_hi": a.range_hi, "confidence": a.confidence},
                    "b": {"description": b.description, "range_lo": b.range_lo, "range_hi": b.range_hi, "confidence": b.confidence},
                })
        return overlaps

    def sync_to_state_store(self) -> None:
        """同步數值映射到 GlobalStateStore（C5+C6 整合）"""
        self.decay_confidences()
        serialized = self.serialize_mappings()
        try:
            from core.system.state_store.global_store import state_store
            state_store.update_state("neuro_vocabulary", {"mappings": serialized})
        except Exception as e:
            logger.warning(f"[NeuroVocabulary] sync_to_state_store failed: {e}", exc_info=True)

    def restore_from_state_store(self) -> None:
        """從 GlobalStateStore 恢復數值映射"""
        try:
            from core.system.state_store.global_store import state_store
            data = state_store.get_state("neuro_vocabulary")
            mappings = data.get("mappings") if data else None
            if mappings:
                self.load_mappings_from_config(mappings)
        except Exception as e:
            logger.warning(f"[NeuroVocabulary] restore_from_state_store failed: {e}", exc_info=True)

    def load_from_config(self, config_data: List[Dict[str, Any]]) -> None:
        """从配置加载片段"""
        if not config_data:
            return
        for item in config_data:
            weights = item.get("weights", {})
            frag = NeuroFragment(
                fragment_id=item["id"],
                content=item["content"],
                category=item.get("category", "general"),
                structural_type=item.get("structural_type", "statement"),
                alpha_energy=weights.get("alpha_energy", 0.5),
                beta_curiosity=weights.get("beta_curiosity", 0.5),
                gamma_valence=weights.get("gamma_valence", 0.0),
                delta_intimacy=weights.get("delta_intimacy", 0.3),
                epsilon_precision=weights.get("epsilon_precision", 0.5),
                zeta_temporal=weights.get("zeta_temporal", 0.5),
                theta_meta=weights.get("theta_meta", 0.3),
                eta_execution=weights.get("eta_execution", 0.5),
                context_tags=item.get("context_tags"),
            )
            self.add_fragment(frag)

    def decompose_from_templates(self, library) -> int:
        """
        从 TemplateLibrary 自动分解模板为片段。
        每个句子拆成一个 NeuroFragment，权重从模板元数据推断。
        返回生成的片段数量。
        """
        count = 0
        try:
            templates = library.get_all_templates()
        except Exception:
            logger.warning("decompose_from_templates: failed to get templates", exc_info=True)
            return 0

        for tmpl in templates:
            content = getattr(tmpl, "content", "") or ""
            category = getattr(tmpl, "category", None)
            if category is None:
                category = getattr(tmpl, "metadata", {}).get("category", "general")
            else:
                category = category.value if hasattr(category, "value") else str(category)
            tmpl_id = getattr(tmpl, "id", "unknown")

            # 按标点拆分为句子（只分中句号/感叹/问号，不分英文句点避免打断省略号）
            import re as _re
            normalized = content.replace("...", "…").replace("。。", "。")
            sentences = [s.strip() for s in _re.split(r'(?<=[。！？！?!])\s*', normalized) if s.strip()]

            for i, sentence in enumerate(sentences):
                fid = f"{tmpl_id}_s{i}"
                # 推断 structural_type
                if i == 0 and any(w in sentence for w in ["早安", "晚安", "你好", "嗨", "hi"]):
                    stype = "greeting"
                elif i == len(sentences) - 1 and any(w in sentence for w in ["吗", "呢", "?","？"]):
                    stype = "closing_question"
                elif any(w in sentence for w in ["!", "！"]):
                    stype = "exclamation"
                elif any(w in sentence for w in ["让我", "想想", "关于"]):
                    stype = "transition"
                else:
                    stype = "statement"

                # 从类别推断 8D 权重
                alpha = 0.5
                beta_val = 0.4
                gamma = 0.1
                delta = 0.3
                epsilon = 0.3
                zeta = 0.4
                theta = 0.2
                eta = 0.4

                if "greeting" in category.lower():
                    alpha = 0.7; gamma = 0.5; delta = 0.4
                elif "emotional" in category.lower() or "support" in category.lower():
                    alpha = 0.3; gamma = -0.3; delta = 0.6; beta_val = 0.2
                elif "affirmation" in category.lower():
                    gamma = 0.7; alpha = 0.6; delta = 0.5
                elif "negation" in category.lower():
                    gamma = -0.4; alpha = 0.3; delta = 0.2
                elif "curiosity" in category.lower():
                    beta_val = 0.8; gamma = 0.4; alpha = 0.6
                elif "intimacy" in category.lower():
                    delta = 0.9; gamma = 0.8; alpha = 0.4
                elif "help" in category.lower():
                    epsilon = 0.6; beta_val = 0.5; alpha = 0.5
                elif "farewell" in category.lower():
                    zeta = 0.7; alpha = 0.4; gamma = 0.3

                frag = NeuroFragment(
                    fragment_id=fid,
                    content=sentence,
                    category=category,
                    structural_type=stype,
                    alpha_energy=alpha,
                    beta_curiosity=beta_val,
                    gamma_valence=gamma,
                    delta_intimacy=delta,
                    epsilon_precision=epsilon,
                    zeta_temporal=zeta,
                    theta_meta=theta,
                    eta_execution=eta,
                    context_tags=[category, stype],
                )
                self.add_fragment(frag)
                count += 1
        return count


class NeuroBlender:
    """
    神经组合引擎 (Neural Blender)
    ==============================
    根据 8D 状态矩阵 + 意图向量，动态合成回复。

    Core algorithm:
    1. Build a target 8D vector from (state_matrix, intent_vec, empathy)
    2. For each fragment in NeuroVocabulary, compute cosine similarity
       between fragment's state_vector and target vector
    3. Select top-K fragments per structural role
    4. Apply structural exploration if beta.curiosity > threshold
    5. Assemble into a coherent response
    """

    CATEGORY_INCOMPATIBLE = {
        "greeting": "farewell",
        "farewell": "greeting",
    }

    STRUCTURAL_ORDER = {
        "greeting": 0,
        "transition": 1,
        "statement": 2,
        "exclamation": 2,
        "closing_question": 3,
    }

    def __init__(self, vocabulary: Optional[NeuroVocabulary] = None):
        self.vocabulary = vocabulary or NeuroVocabulary()
        self.stats = {
            "total_syntheses": 0,
            "avg_time_ms": 0.0,
        }

    def synthesize(
        self,
        state_dict: Dict[str, Any],
        intent_vec: Optional[Dict[str, float]] = None,
        empathy_valence: float = 0.0,
        user_name: str = "朋友",
        curiosity_threshold: float = 0.7,
        top_k_per_role: int = 2,
    ) -> ComposedResponse:
        """
        合成回复。

        Args:
            state_dict: 8D 状态矩阵值 (e.g., {"alpha": {"energy": 0.8}, "beta": {"curiosity": 0.6}, ...})
            intent_vec: 意图向量 (e.g., {"math": 0.9, "casual": 0.1})
            empathy_valence: 共情分析中的 valence 值 (-1 to 1)
            user_name: 用户名
            curiosity_threshold: β.curiosity 高于此值时触发结构探索
            top_k_per_role: 每个角色选择的片段数

        Returns:
            ComposedResponse
        """
        start_time = time.time()

        # 1. Build target 8D vector from state + intent + empathy
        target = self._build_target_vector(state_dict, intent_vec, empathy_valence)

        # 2. Score fragments by cosine similarity to target
        all_frags = self.vocabulary.all_fragments()
        if not all_frags:
            return ComposedResponse(
                text=f"（{user_name}，我還在學習如何組織語言...）",
                fragments_used=[],
                composition_time_ms=(time.time() - start_time) * 1000,
                confidence=0.0,
            )

        scored = self._score_fragments(target, all_frags)

        # ---- Energy-aware fragment count ----
        alpha_energy = self._extract_alpha_energy(state_dict)
        _beh_conf = self._load_behavior_config()
        _bio_thresh = _beh_conf.get("biological_thresholds", {})
        top_k_total = self._compute_top_k_count(alpha_energy, _bio_thresh)

        # 3. Group by structural_type and pick top-K per role
        by_role = self._group_by_role(scored)
        selected = self._select_top_fragments(
            by_role, alpha_energy, _bio_thresh, top_k_total, top_k_per_role
        )

        # 4. Structural exploration (beta.curiosity high → shuffle order)
        beta_curiosity = self._extract_beta_curiosity(state_dict)

        if beta_curiosity > curiosity_threshold and len(selected) >= 3:
            selected = self._structural_exploration(selected, beta_curiosity)

        # 5. Natural assembly
        response_text = self._natural_assemble(selected)

        confidence = min(1.0, sum(sim for _, sim in scored[:5]) / max(len(scored[:5]), 1))

        elapsed_ms = (time.time() - start_time) * 1000
        self._update_stats(elapsed_ms)

        return ComposedResponse(
            text=response_text,
            fragments_used=[f.fragment_id for f in selected],
            composition_time_ms=elapsed_ms,
            confidence=confidence,
            metadata={
                "strategy": "neuro_blend",
                "target_vector": target,
                "structural_exploration": beta_curiosity > curiosity_threshold,
                "beta_curiosity": beta_curiosity,
                "empathy_valence": empathy_valence,
            },
        )

    def _score_fragments(self, target: List[float], all_frags: List[NeuroFragment]) -> List[Tuple[NeuroFragment, float]]:
        """Score fragments."""
        scored = []
        for frag in all_frags:
            sim = self._cosine_similarity(target, frag.state_vector())
            if frag.fragment_id.startswith("ng_"):
                sim = min(1.0, sim + 0.15)
            scored.append((frag, sim))
        return scored

    def _extract_alpha_energy(self, state_dict: Dict[str, Any]) -> float:
        """Extract alpha energy."""
        alpha_state = state_dict.get("alpha", {})
        if isinstance(alpha_state, dict):
            return alpha_state.get("energy", 0.5)
        return getattr(alpha_state, "energy", 0.5)

    def _load_behavior_config(self) -> Dict[str, Any]:
        """Load behavior config."""
        from core.system.config.tiered_loader import get_config
        return get_config("standard/behavior/behavior")

    def _compute_top_k_count(self, alpha_energy: float, _bio_thresh: Dict[str, Any]) -> int:
        """Compute top k count."""
        if alpha_energy < _bio_thresh.get("composer_energy_fragment_low", 0.2):
            return 2
        elif alpha_energy < _bio_thresh.get("composer_energy_fragment_medium", 0.4):
            return 4
        return 6

    def _group_by_role(self, scored: List[Tuple[NeuroFragment, float]]) -> Dict[str, List[Tuple[NeuroFragment, float]]]:
        """Group by role."""
        by_role: Dict[str, List[Tuple[NeuroFragment, float]]] = {}
        for frag, sim in scored:
            by_role.setdefault(frag.structural_type, []).append((frag, sim))
        return by_role

    def _select_top_fragments(
        self,
        by_role: Dict[str, List[Tuple[NeuroFragment, float]]],
        alpha_energy: float,
        _bio_thresh: Dict[str, Any],
        top_k_total: int,
        top_k_per_role: int,
    ) -> List[NeuroFragment]:
        """Select top fragments."""
        selected: List[NeuroFragment] = []
        seen_contents: set = set()
        def add_if_unique(frag: NeuroFragment) -> bool:
            """Add a if unique."""
            key = frag.content.strip()[:15]
            if key not in seen_contents:
                seen_contents.add(key)
                selected.append(frag)
                return True
            return False

        if alpha_energy < _bio_thresh.get("composer_energy_greeting", 0.3):
            for role in ("statement", "closing_question", "transition"):
                items = by_role.get(role, [])
                items.sort(key=lambda x: x[1], reverse=True)
                for frag, _ in items:
                    if add_if_unique(frag):
                        break
            if len(selected) > top_k_total:
                selected = selected[:top_k_total]
        else:
            for role, items in by_role.items():
                items.sort(key=lambda x: x[1], reverse=True)
                for frag, _ in items[:top_k_per_role * 2]:
                    add_if_unique(frag)
                    if len([f for f in selected if f.structural_type == role]) >= top_k_per_role:
                        break
        return selected

    def _extract_beta_curiosity(self, state_dict: Dict[str, Any]) -> float:
        """Extract beta curiosity."""
        beta_state = state_dict.get("beta", {})
        if isinstance(beta_state, dict):
            return beta_state.get("curiosity", 0.5)
        return getattr(beta_state, "curiosity", 0.5)

    def _build_target_vector(
        self,
        state_dict: Dict[str, Any],
        intent_vec: Optional[Dict[str, float]],
        empathy_valence: float,
    ) -> List[float]:
        """从状态矩阵构建目标 8D 向量"""
        # Extract values from state_dict
        alpha_dict = state_dict.get("alpha", {})
        beta_dict = state_dict.get("beta", {})
        gamma_dict = state_dict.get("gamma", {})
        delta_dict = state_dict.get("delta", {})
        epsilon_dict = state_dict.get("epsilon", {})
        zeta_dict = state_dict.get("zeta", {})
        theta_dict = state_dict.get("theta", {})
        eta_dict = state_dict.get("eta", {})

        alpha_val = self._dict_val(alpha_dict, "energy", 0.5)
        beta_val = self._dict_val(beta_dict, "curiosity", 0.5)
        gamma_val = self._dict_val(gamma_dict, "valence", 0.0) + empathy_valence * 0.3
        delta_val = self._dict_val(delta_dict, "intimacy", 0.3)
        epsilon_val = self._dict_val(epsilon_dict, "precision", 0.5)
        zeta_val = self._dict_val(zeta_dict, "temporal_coherence", 0.5)
        theta_val = self._dict_val(theta_dict, "novelty", 0.3)
        eta_val = self._dict_val(eta_dict, "execution_count", 0.5) if isinstance(eta_dict, dict) else 0.5

        # Intent influence
        if intent_vec:
            if intent_vec.get("math", 0) > 0.5:
                epsilon_val = min(1.0, epsilon_val + 0.3)
            if intent_vec.get("code", 0) > 0.5:
                epsilon_val = min(1.0, epsilon_val + 0.2)
            if intent_vec.get("casual", 0) > 0.5:
                alpha_val = max(0.0, alpha_val - 0.1)
                delta_val = min(1.0, delta_val + 0.2)

        return [
            max(0.0, min(1.0, alpha_val)),
            max(0.0, min(1.0, beta_val)),
            max(-1.0, min(1.0, gamma_val)),
            max(0.0, min(1.0, delta_val)),
            max(0.0, min(1.0, epsilon_val)),
            max(0.0, min(1.0, zeta_val)),
            max(0.0, min(1.0, theta_val)),
            max(0.0, min(1.0, eta_val)),
        ]

    def _dict_val(self, d: Any, key: str, default: float) -> float:
        """Dict val."""
        if isinstance(d, dict):
            return d.get(key, default)
        return getattr(d, key, default)

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Cosine similarity."""
        if len(v1) != len(v2) or not v1:
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        n1 = sum(a * a for a in v1) ** 0.5
        n2 = sum(b * b for b in v2) ** 0.5
        if n1 == 0 or n2 == 0:
            return 0.0
        return dot / (n1 * n2)

    def _structural_exploration(self, fragments: List[NeuroFragment], curiosity: float) -> List[NeuroFragment]:
        """当好奇心高时，尝试非传统片段排列"""
        if len(fragments) < 3:
            return fragments

        explored = list(fragments)

        # Move an exclamation to middle instead of start
        exclamations = [f for f in explored if f.structural_type == "exclamation"]
        non_exclam = [f for f in explored if f.structural_type != "exclamation"]

        if exclamations and len(non_exclam) >= 2:
            exclam = exclamations[0]
            mid = len(non_exclam) // 2
            non_exclam.insert(mid, exclam)
            explored = non_exclam

        # If curiosity is very high (>0.9), append a closing question to the front
        if curiosity > 0.9:
            closing = [f for f in explored if f.structural_type == "closing_question"]
            if closing:
                others = [f for f in explored if f.structural_type != "closing_question"]
                explored = [closing[0]] + others

        return explored

    def _natural_assemble(self, fragments: List[NeuroFragment]) -> str:
        """自然语言组装：让片段像人话一样流畅"""
        if not fragments:
            return "嗯...我在聽。"

        fragments.sort(key=lambda f: self.STRUCTURAL_ORDER.get(f.structural_type, 5))

        import re as _re

        parts = []
        prev_type = None

        for i, frag in enumerate(fragments):
            content = frag.content.strip()
            stype = frag.structural_type

            # Suppress duplicate structural types (only first instance passes)
            if stype == prev_type and stype in ("greeting", "closing_question", "transition"):
                continue

            # --- Natural flow connectors ---
            if i > 0 and parts:
                prev = parts[-1]
                # Add natural connector for statement/exclamation fragments
                if (not _re.search(r'[。！？!?）)]$', prev)
                        and stype in ("statement", "exclamation")
                        and not _re.search(r'[，、，]$', prev)):
                    content = content[0].lower() + content[1:] if content and content[0].isalpha() else content

            parts.append(content)
            prev_type = stype

        if not parts:
            return "...嗯？"

        response = "".join(parts)

        # Clean artifact patterns
        response = _re.sub(r'[。！？，]{2,}', lambda m: m.group(0)[0], response)
        response = _re.sub(r'~+', '～', response)  # normalize tilde to wave dash
        # Remove leading comma/question marks
        response = response.lstrip("，？?！!")
        # Ensure proper ending
        if not _re.search(r'[。！？!?）)]$', response):
            # 呢 is only a question word when it functions as interrogative
            if _re.search(r'[吗么]$', response):
                response += "？"
            elif _re.search(r'[吧哦啊呀]$', response):
                response += "。"
            else:
                response += "。"

        return response

    def _update_stats(self, elapsed_ms: float) -> None:
        """Update stats."""
        self.stats["total_syntheses"] += 1
        total = self.stats["total_syntheses"]
        self.stats["avg_time_ms"] = (
            self.stats["avg_time_ms"] * (total - 1) + elapsed_ms
        ) / total


class ResponseComposer:
    """
     响应组合器主类
     ==============

     整合 TemplateMatcher 和 FragmentComposer
     提供统一的响应组合接口
     """

    def __init__(self):
        self.fragment_composer = FragmentComposer()
        self.neuro_vocabulary = NeuroVocabulary()
        self.neuro_vocabulary.restore_from_state_store()
        self.neuro_blender = NeuroBlender(self.neuro_vocabulary)
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
        return self.fragment_composer.compose_from_template(template_content, match_score, context)

    def add_fragment(self, fragment: Fragment) -> None:
        """添加自定义片段"""
        self.fragment_composer.add_fragment(fragment)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.fragment_composer.get_stats()

    def load_neuro_fragments_from_config(self, config_data: List[Dict[str, Any]]) -> None:
        """从配置加载神经片段"""
        self.neuro_vocabulary.load_from_config(config_data)

    def decompose_templates_to_neuro(self, library) -> int:
        """将 TemplateLibrary 自动分解到 NeuroVocabulary"""
        return self.neuro_vocabulary.decompose_from_templates(library)

    def neuro_synthesize(
        self,
        state_dict: Dict[str, Any],
        intent_vec: Optional[Dict[str, float]] = None,
        empathy_valence: float = 0.0,
        user_name: str = "朋友",
    ) -> ComposedResponse:
        """使用 NeuroBlender 合成响应"""
        return self.neuro_blender.synthesize(
            state_dict=state_dict,
            intent_vec=intent_vec,
            empathy_valence=empathy_valence,
            user_name=user_name,
        )
