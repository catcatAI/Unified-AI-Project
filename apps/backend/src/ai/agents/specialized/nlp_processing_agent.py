# =============================================================================
# ANGELA-MATRIX: L6[执行层] β [A] L2+
# =============================================================================
#
# 职责: 自然语言处理代理，包括文本摘要、情感分析等
# 维度: 涉及认知维度 (β) 的语言理解和处理
# 安全: 使用 Key A (后端控制) 进行文本隐私保护
# 成熟度: L2+ 等级可以使用基本的 NLP 功能
#
# 能力:
# - text_summarization: 文本摘要
# - sentiment_analysis: 情感分析
# - named_entity_recognition: 命名实体识别
# - text_classification: 文本分类
# - language_translation: 语言翻译
#
# =============================================================================

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Rule-based named entity recognition
# --------------------------------------------------------------------------- #
# Precision over recall: a gazetteer and a few suffix/honorific rules, no
# model. The patterns are deliberately conservative — a wrong entity is worse
# than a missing one for an agent that quotes its findings.
_URL_RE = re.compile(
    r"https?://[^\s\u3000\uff0c\u3002\u3001\uff1b\uff01\uff1f\uff09\u3011\u300d\u300f]+"
)
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_MONEY_RE = re.compile(
    r"(?:US\$|NT\$|\$|€|£|¥|RMB|CNY|USD|EUR|JPY)\s?\d[\d,]*(?:\.\d+)?"
    r"|\d[\d,]*(?:\.\d+)?\s?(?:元|塊|美元|人民幣|美金|欧元|日圓)"
)
_PERCENT_RE = re.compile(r"\d+(?:\.\d+)?\s?%")
_NUMBER_RE = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?(?![\w.])")
_TIME_RE = re.compile(r"(?<![\d:])\d{1,2}:\d{2}(?![\d:])")
_DATE_RE = re.compile(
    r"\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?"
    r"|\d{1,2}[-/]\d{1,2}[-/]\d{2,4}"
    r"|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}(?:,\s*\d{4})?\b"
)
_PERSON_RE = re.compile(
    r"(?P<cjk>[\u4e00-\u9fff]{1,3})(?P<honor>先生|女士|小姐|博士|教授|老師|同學)"
    r"|(?:Mr|Mrs|Ms|Dr|Prof)\.?\s+(?P<latin>[A-Z][a-z]+)"
)
# A Chinese name is the last characters before the honorific; a candidate
# containing a function word ("是/的/在") is not a name, so the shorter
# suffix is tried instead.
_NAME_FUNCTION_WORDS = set("是的了在和與跟同及也就都把被對從到很更最還又沒不你我他她")
_ORG_RE = re.compile(
    r"[\u4e00-\u9fffA-Za-z0-9]{2,20}(?:公司|集團|集团|大學|大学|学院|研究院|實驗室|实验室|銀行|银行)"
    r"|\b[A-Z][A-Za-z&\.\- ]{1,30}(?:Inc|Ltd|LLC|Corp|Corporation|Foundation)\b"
)
_LOCATION_NAMES = (
    "台灣",
    "台北",
    "新北",
    "桃園",
    "台中",
    "台南",
    "高雄",
    "基隆",
    "新竹",
    "香港",
    "澳門",
    "上海",
    "北京",
    "深圳",
    "廣州",
    "杭州",
    "成都",
    "南京",
    "武漢",
    "新加坡",
    "東京",
    "大阪",
    "首爾",
    "倫敦",
    "巴黎",
    "柏林",
    "紐約",
    "舊金山",
    "華盛頓",
)
_LOCATION_RE = re.compile("|".join(re.escape(name) for name in _LOCATION_NAMES))


def _entity(kind: str, value: str, start: int, end: int) -> Dict[str, Any]:
    return {"type": kind, "value": value, "start": start, "end": end}


def _overlaps(span: tuple, taken: list) -> bool:
    """True when the span overlaps an already-claimed span."""
    start, end = span
    return any(not (end <= other[0] or start >= other[1]) for other in taken)


def _trim_person_name(match: "re.Match"):
    """The name part of a PERSON match (value, start, end) or None.

    A Chinese honorific may follow several characters ("伴是李小姐"); the
    name is the shortest suffix without a function word ("李小姐" → "李").
    """
    cjk = match.groupdict().get("cjk")
    if not cjk:
        latin = match.groupdict().get("latin")
        if latin:
            start = match.start("latin")
            return (latin, start, start + len(latin))
        return None
    honor = match.group("honor")
    base = match.start("cjk")
    for length in range(len(cjk), 0, -1):
        candidate = cjk[len(cjk) - length :]
        if not any(ch in _NAME_FUNCTION_WORDS for ch in candidate):
            offset = base + (len(cjk) - length)
            return (candidate + honor, offset, match.end())
    return None


def extract_named_entities(text: str) -> List[Dict[str, Any]]:
    """Find the named entities in *text* (rule-based)."""
    if not text:
        return []
    entities: List[Dict[str, Any]] = []
    taken: List[tuple] = []

    def _add(kind: str, match: "re.Match") -> None:
        value = match.group()
        start, end = match.start(), match.end()
        if kind == "PERSON":
            person = _trim_person_name(match)
            if not person:
                return
            value, start, end = person
        span = (start, end)
        if _overlaps(span, taken):
            return
        taken.append(span)
        entities.append(_entity(kind, value, start, end))

    # Order matters: the most specific patterns claim their span first, so a
    # date is not also reported as three numbers.
    for pattern, kind in (
        (_URL_RE, "URL"),
        (_EMAIL_RE, "EMAIL"),
        (_MONEY_RE, "MONEY"),
        (_DATE_RE, "DATE"),
        (_TIME_RE, "TIME"),
        (_PERCENT_RE, "PERCENT"),
        (_PERSON_RE, "PERSON"),
        (_ORG_RE, "ORG"),
        (_LOCATION_RE, "LOCATION"),
        (_NUMBER_RE, "NUMBER"),
    ):
        for match in pattern.finditer(text):
            _add(kind, match)

    entities.sort(key=lambda e: (e["start"], e["end"]))
    return entities


class NLPProcessingAgent:
    """Agent for sentiment analysis, entity extraction, summarization, and text classification."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, **kwargs):
        self.config = config or {}
        self.agent_id = kwargs.get("agent_id")
        logger.info(f"NLPProcessingAgent initialized with config: {self.config}")

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text and return score and label."""
        if not text:
            return {
                "status": "error",
                "message": "No text provided",
                "score": 0.0,
                "label": "neutral",
            }
        positive_words = {
            "good",
            "great",
            "excellent",
            "happy",
            "love",
            "wonderful",
            "amazing",
            "fantastic",
            "positive",
            "best",
        }
        negative_words = {
            "bad",
            "terrible",
            "awful",
            "hate",
            "horrible",
            "worst",
            "sad",
            "angry",
            "negative",
            "poor",
        }
        words = set(text.lower().split())
        pos_count = len(words & positive_words)
        neg_count = len(words & negative_words)
        total = pos_count + neg_count
        score = 0.0
        if total > 0:
            score = (pos_count - neg_count) / total
        score = max(-1.0, min(1.0, score))
        if score > 0.2:
            label = "positive"
        elif score < -0.2:
            label = "negative"
        else:
            label = "neutral"
        logger.info(f"analyze_sentiment: score={score:.2f}, label={label}")
        return {
            "status": "success",
            "message": "Sentiment analysis complete",
            "score": score,
            "label": label,
        }

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract named entities from text.

        Rule-based (no model, no new dependency): precision over recall.
        The previous version found URLs and emails only, so every other
        entity type the agent advertises came back empty.

        Covered: URL, EMAIL, NUMBER, PERCENT, MONEY, DATE, TIME, LOCATION
        (gazetteer), ORG (suffix rule), PERSON (honorific rule).
        """
        if not text:
            return {"status": "error", "message": "No text provided", "entities": []}
        entities = extract_named_entities(text)
        logger.info(f"extract_entities: found {len(entities)} entities")
        return {
            "status": "success",
            "message": f"Extracted {len(entities)} entities",
            "entities": entities,
        }

    def summarize_text(self, text: str, max_length: int = 100) -> Dict[str, Any]:
        """Summarize text by returning first sentence up to max_length chars."""
        if not text:
            return {"status": "error", "message": "No text provided", "summary": ""}
        sentences = text.replace("! ", ". ").replace("? ", ". ").split(". ")
        summary = sentences[0] if sentences else text
        if len(summary) > max_length:
            summary = summary[:max_length].rsplit(" ", 1)[0] + "..."
        logger.info(f"summarize_text: input={len(text)} chars, summary={len(summary)} chars")
        return {
            "status": "success",
            "message": f"Summarized from {len(text)} to {len(summary)} chars",
            "summary": summary,
        }

    def classify_text(self, text: str, categories: List[str]) -> Dict[str, Any]:
        """Classify text into one of the given categories (basic keyword matching)."""
        if not text:
            return {
                "status": "error",
                "message": "No text provided",
                "category": "",
                "confidence": 0.0,
            }
        if not categories:
            return {
                "status": "error",
                "message": "No categories provided",
                "category": "",
                "confidence": 0.0,
            }
        text_lower = text.lower()
        scores = {}
        for cat in categories:
            keyword_count = sum(1 for word in cat.lower().split() if word in text_lower)
            scores[cat] = keyword_count
        best_cat = max(scores, key=lambda k: scores[k])
        best_score = scores[best_cat]
        total_keywords = sum(len(c.split()) for c in categories)
        confidence = best_score / total_keywords if total_keywords > 0 else 0.0
        logger.info(f"classify_text: category={best_cat}, confidence={confidence:.2f}")
        return {
            "status": "success",
            "message": f"Classified as '{best_cat}'",
            "category": best_cat,
            "confidence": confidence,
        }
