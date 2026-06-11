# =============================================================================
# ANGELA-MATRIX: L2-L3[记忆层/身份层] βδ [A] L2+
# =============================================================================
#
# 职责: 查询分类器 — 将用户查询分类到领域，用于 Model Bus 路由系统
# 维度: 认知维度 (β) 用于模式匹配，精神维度 (δ) 用于意图理解
# 安全: 使用 Key A (后端控制)
# 成熟度: L2+ 等级才能完全理解查询路由逻辑
#
# =============================================================================

import re
from enum import Enum
from typing import List, Pattern, Tuple

from core.system.config.magic_numbers import confidence_value, limit_value, threshold_value


class QueryType(Enum):
    REFLEX = "reflex"
    GREETING = "greeting"
    MATH = "math"
    LOGIC = "logic"
    KNOWLEDGE = "knowledge"
    CREATIVE = "creative"
    OPINION = "opinion"
    COMMAND = "command"
    UNKNOWN = "unknown"


class QueryClassifier:
    """Pattern-based query classifier for Model Bus routing."""

    def __init__(self):
        self._reflex_words: set = {
            "hi", "ok", "okay", "hey", "yo", "oh", "ah",
            "嗯", "好", "是", "不", "啊", "哦", "喂", "嗨", "噢",
        }

        self._patterns: List[Tuple[QueryType, Pattern, float]] = [
            (
                QueryType.GREETING,
                re.compile(
                    r"(你好|早上好|上午好|中午好|下午好|晚上好|晚安|"
                    r"再见|拜拜|谢谢|感谢|"
                    r"\b(hello|hi|hey|good\s*morning|good\s*afternoon|good\s*evening|good\s*bye|thanks?|bye)\b)",
                    re.IGNORECASE,
                ),
                0.9,
            ),
            (
                QueryType.MATH,
                re.compile(
                    r"(\d+\s*[\+\-\*\/]\s*\d+|"
                    r"等于|计算|加|减|乘|除|"
                    r"\b(plus|minus|times|divided\s*by|calculate|solve|equation)\b)",
                    re.IGNORECASE,
                ),
                0.85,
            ),
            (
                QueryType.LOGIC,
                re.compile(
                    r"(\b(true|false|and|or|not|if|bool|nor|xor|neither)\b|"
                    r"if\s+then|逻辑|推理|boolean|proposition)",
                    re.IGNORECASE,
                ),
                0.8,
            ),
            (
                QueryType.KNOWLEDGE,
                re.compile(
                    r"(什么是|是什么|what\s+is|how\s+(does|do|can|to)|"
                    r"why\s+(is|does|do|can)|"
                    r"\b(define|explain)\b|"
                    r"什么|谁|哪里|为什么|怎么|多少|how\s+many|what\s+are)",
                    re.IGNORECASE,
                ),
                0.7,
            ),
            (
                QueryType.CREATIVE,
                re.compile(
                    r"(写|作|创作|编|画|虚构|"
                    r"\b(write|poem|story|song|joke|"
                    r"imagine|pretend|creat|make\s+up|compose)\b|"
                    r"想象|如果|假设|绘)",
                    re.IGNORECASE,
                ),
                0.75,
            ),
            (
                QueryType.COMMAND,
                re.compile(
                    r"^((打开|关闭|启动|停止|暂停|运行|执行|帮我|请)|"
                    r"\b(open|close|start|stop|please)\b|can\s+you|could\s+you)",
                    re.IGNORECASE,
                ),
                0.8,
            ),
        ]

    def classify(self, text: str) -> Tuple[QueryType, float]:
        """Classify a query text into a QueryType with confidence score 0.0-1.0."""
        text = text.strip()

        if not text:
            return QueryType.UNKNOWN, 0.0

        if len(text) > limit_value("ai.query_classifier.max_direct_len", 200):
            return QueryType.KNOWLEDGE, confidence_value("ai.query_classifier.long_text_conf", 0.85)

        best_type = QueryType.UNKNOWN
        best_conf = 0.0

        for query_type, pattern, confidence in self._patterns:
            if pattern.search(text):
                if confidence > best_conf:
                    best_type = query_type
                    best_conf = confidence

        if text.lower() in self._reflex_words or (len(text) < limit_value("ai.query_classifier.reflex_min_len", 2) and best_conf < threshold_value("ai.query_classifier.reflex_conf_threshold", 0.5)):
            return QueryType.REFLEX, confidence_value("ai.query_classifier.reflex_conf", 0.95)

        if best_conf < threshold_value("ai.query_classifier.question_conf_threshold", 0.5) and text.rstrip().endswith("?"):
            return QueryType.KNOWLEDGE, confidence_value("ai.query_classifier.question_conf", 0.65)

        if best_conf > threshold_value("ai.query_classifier.min_accept_conf", 0.5):
            return best_type, best_conf

        return QueryType.UNKNOWN, confidence_value("ai.query_classifier.unknown_conf", 0.3)
