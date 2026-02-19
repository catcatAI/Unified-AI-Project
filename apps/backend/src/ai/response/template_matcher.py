"""
Template Matcher - 基于哈希的模板匹配系统
========================================
实现快速模板检索和匹配度计算

核心功能：
1. 输入文本哈希化，快速查找模板
2. 计算匹配度分数 (0.0-1.0)
3. 支持精确匹配、语义匹配、模糊匹配

性能目标：匹配计算 < 5ms
"""

import hashlib
import time
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class MatchLevel(Enum):
    """匹配级别"""

    EXACT = "exact"
    SEMANTIC = "semantic"
    FUZZY = "fuzzy"
    NO_MATCH = "no_match"


@dataclass
class MatchResult:
    """匹配结果"""

    score: float
    level: MatchLevel
    template_id: str
    template_content: str
    match_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Template:
    """模板数据结构"""

    id: str
    content: str
    patterns: List[str]
    keywords: List[str]
    hash_exact: str
    hash_semantic: str
    usage_count: int = 0
    success_rate: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class TemplateMatcher:
    """
    模板匹配器 - 基于哈希的快速检索系统
    ==========================================

    设计原理：
    1. 精确哈希 (hash_exact): 完全一致的输入 → 直接命中
    2. 语义哈希 (hash_semantic): 归一化后的文本 → 语义匹配
    3. 关键词哈希 (hash_keywords): 关键词组合 → 模糊匹配

    哈希表结构：
    {
        "hash_value": [template_id1, template_id2, ...],
        ...
    }
    """

    def __init__(self):
        self.templates: Dict[str, Template] = {}
        self.hash_index_exact: Dict[str, List[str]] = {}
        self.hash_index_semantic: Dict[str, List[str]] = {}
        self.keyword_index: Dict[str, List[str]] = {}

        self.stats = {
            "total_matches": 0,
            "exact_matches": 0,
            "semantic_matches": 0,
            "fuzzy_matches": 0,
            "no_matches": 0,
            "average_match_time": 0.0,
        }

    def add_template(
        self,
        template_id: str,
        content: str,
        patterns: List[str],
        keywords: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """添加模板到匹配器"""
        hash_exact = self._compute_exact_hash(content)
        hash_semantic = self._compute_semantic_hash(content)

        template = Template(
            id=template_id,
            content=content,
            patterns=patterns,
            keywords=keywords,
            hash_exact=hash_exact,
            hash_semantic=hash_semantic,
            metadata=metadata or {},
        )

        self.templates[template_id] = template

        if hash_exact not in self.hash_index_exact:
            self.hash_index_exact[hash_exact] = []
        self.hash_index_exact[hash_exact].append(template_id)

        if hash_semantic not in self.hash_index_semantic:
            self.hash_index_semantic[hash_semantic] = []
        self.hash_index_semantic[hash_semantic].append(template_id)

        for keyword in keywords:
            kw_hash = self._compute_keyword_hash(keyword)
            if kw_hash not in self.keyword_index:
                self.keyword_index[kw_hash] = []
            self.keyword_index[kw_hash].append(template_id)

        logger.debug(f"Added template: {template_id}")

    def match(
        self, user_input: str, context: Optional[Dict[str, Any]] = None
    ) -> MatchResult:
        """
        匹配用户输入到模板

        Args:
            user_input: 用户输入文本
            context: 上下文信息（可选）

        Returns:
            MatchResult: 匹配结果
        """
        start_time = time.time()

        hash_exact = self._compute_exact_hash(user_input)
        if hash_exact in self.hash_index_exact:
            template_ids = self.hash_index_exact[hash_exact]
            template_id = template_ids[0]
            template = self.templates[template_id]

            match_time = (time.time() - start_time) * 1000
            self._update_stats(MatchLevel.EXACT, match_time)

            return MatchResult(
                score=1.0,
                level=MatchLevel.EXACT,
                template_id=template_id,
                template_content=template.content,
                match_time_ms=match_time,
                metadata={
                    "match_type": "exact_hash",
                    "usage_count": template.usage_count,
                },
            )

        hash_semantic = self._compute_semantic_hash(user_input)
        if hash_semantic in self.hash_index_semantic:
            template_ids = self.hash_index_semantic[hash_semantic]
            best_match = self._rank_templates(template_ids, user_input, context)

            if best_match:
                template_id, score = best_match
                template = self.templates[template_id]

                match_time = (time.time() - start_time) * 1000
                self._update_stats(MatchLevel.SEMANTIC, match_time)

                return MatchResult(
                    score=score,
                    level=MatchLevel.SEMANTIC,
                    template_id=template_id,
                    template_content=template.content,
                    match_time_ms=match_time,
                    metadata={
                        "match_type": "semantic_hash",
                        "usage_count": template.usage_count,
                    },
                )

        keywords = self._extract_keywords(user_input)
        fuzzy_candidates = self._find_keyword_matches(keywords)

        if fuzzy_candidates:
            best_match = self._rank_templates(fuzzy_candidates, user_input, context)

            if best_match:
                template_id, score = best_match
                if score > 0.5:
                    template = self.templates[template_id]

                    match_time = (time.time() - start_time) * 1000
                    self._update_stats(MatchLevel.FUZZY, match_time)

                    return MatchResult(
                        score=score,
                        level=MatchLevel.FUZZY,
                        template_id=template_id,
                        template_content=template.content,
                        match_time_ms=match_time,
                        metadata={
                            "match_type": "keyword_fuzzy",
                            "usage_count": template.usage_count,
                        },
                    )

        match_time = (time.time() - start_time) * 1000
        self._update_stats(MatchLevel.NO_MATCH, match_time)

        return MatchResult(
            score=0.0,
            level=MatchLevel.NO_MATCH,
            template_id="",
            template_content="",
            match_time_ms=match_time,
            metadata={"match_type": "no_match"},
        )

    def _compute_exact_hash(self, text: str) -> str:
        """计算精确哈希（保留原始格式）"""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    def _compute_semantic_hash(self, text: str) -> str:
        """计算语义哈希（归一化后）"""
        normalized = self._normalize_text(text)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]

    def _compute_keyword_hash(self, keyword: str) -> str:
        """计算关键词哈希"""
        return hashlib.sha256(keyword.encode("utf-8")).hexdigest()[:8]

    def _normalize_text(self, text: str) -> str:
        """文本归一化"""
        text = text.lower()
        text = text.replace(" ", "")
        text = text.replace("?", "")
        text = text.replace("!", "")
        text = text.replace("。", "")
        text = text.replace("？", "")
        text = text.replace("！", "")
        text = text.replace("，", "")
        text = text.replace(",", "")
        return text

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        stopwords = {
            "你",
            "我",
            "他",
            "她",
            "它",
            "的",
            "了",
            "吗",
            "呢",
            "吧",
            "啊",
            "是",
            "在",
            "有",
            "这",
            "那",
            "个",
            "和",
            "与",
            "或",
            "但",
        }

        words = []
        current_word = ""
        for char in text:
            if "\u4e00" <= char <= "\u9fff":
                if current_word:
                    words.append(current_word)
                    current_word = ""
                words.append(char)
            else:
                current_word += char

        if current_word:
            words.append(current_word.strip())

        keywords = [w for w in words if w not in stopwords and len(w) > 0]
        return keywords

    def _find_keyword_matches(self, keywords: List[str]) -> List[str]:
        """基于关键词查找候选模板"""
        candidates = set()
        for keyword in keywords:
            kw_hash = self._compute_keyword_hash(keyword)
            if kw_hash in self.keyword_index:
                candidates.update(self.keyword_index[kw_hash])
        return list(candidates)

    def _rank_templates(
        self,
        template_ids: List[str],
        user_input: str,
        context: Optional[Dict[str, Any]],
    ) -> Optional[Tuple[str, float]]:
        """对候选模板进行排序，返回最佳匹配"""
        if not template_ids:
            return None

        scores = []
        for template_id in template_ids:
            template = self.templates.get(template_id)
            if not template:
                continue

            score = self._calculate_similarity(user_input, template)
            score *= template.success_rate
            scores.append((template_id, score))

        if not scores:
            return None

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[0]

    def _calculate_similarity(self, text: str, template: Template) -> float:
        """计算相似度"""
        text_keywords = set(self._extract_keywords(text))
        template_keywords = set(template.keywords)

        if not text_keywords or not template_keywords:
            return 0.0

        intersection = text_keywords.intersection(template_keywords)
        union = text_keywords.union(template_keywords)

        jaccard = len(intersection) / len(union) if union else 0.0

        return min(0.95, jaccard * 1.2)

    def _update_stats(self, match_level: MatchLevel, match_time: float):
        """更新统计信息"""
        self.stats["total_matches"] += 1

        if match_level == MatchLevel.EXACT:
            self.stats["exact_matches"] += 1
        elif match_level == MatchLevel.SEMANTIC:
            self.stats["semantic_matches"] += 1
        elif match_level == MatchLevel.FUZZY:
            self.stats["fuzzy_matches"] += 1
        else:
            self.stats["no_matches"] += 1

        total = self.stats["total_matches"]
        self.stats["average_match_time"] = (
            self.stats["average_match_time"] * (total - 1) + match_time
        ) / total

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()

    def record_template_usage(self, template_id: str, success: bool):
        """记录模板使用情况"""
        template = self.templates.get(template_id)
        if not template:
            return

        template.usage_count += 1

        alpha = 0.9
        template.success_rate = (
            alpha * template.success_rate + (1 - alpha) * (1.0 if success else 0.0)
        )

        logger.debug(
            f"Template {template_id} usage: {template.usage_count}, success_rate: {template.success_rate:.2f}"
        )
