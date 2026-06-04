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
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class NLPProcessingAgent:
    """Agent for sentiment analysis, entity extraction, summarization, and text classification."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        logger.info(f"NLPProcessingAgent initialized with config: {self.config}")

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text and return score and label."""
        if not text:
            return {"status": "error", "message": "No text provided", "score": 0.0, "label": "neutral"}
        positive_words = {"good", "great", "excellent", "happy", "love", "wonderful", "amazing", "fantastic", "positive", "best"}
        negative_words = {"bad", "terrible", "awful", "hate", "horrible", "worst", "sad", "angry", "negative", "poor"}
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
        return {"status": "success", "message": f"Sentiment analysis complete", "score": score, "label": label}

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract named entities from text (basic implementation)."""
        if not text:
            return {"status": "error", "message": "No text provided", "entities": []}
        import re
        url_pattern = r"https?://[^\s]+"
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        entities = []
        for match in re.finditer(url_pattern, text):
            entities.append({"type": "URL", "value": match.group(), "start": match.start(), "end": match.end()})
        for match in re.finditer(email_pattern, text):
            entities.append({"type": "EMAIL", "value": match.group(), "start": match.start(), "end": match.end()})
        logger.info(f"extract_entities: found {len(entities)} entities")
        return {"status": "success", "message": f"Extracted {len(entities)} entities", "entities": entities}

    def summarize_text(self, text: str, max_length: int = 100) -> Dict[str, Any]:
        """Summarize text by returning first sentence up to max_length chars."""
        if not text:
            return {"status": "error", "message": "No text provided", "summary": ""}
        sentences = text.replace("! ", ". ").replace("? ", ". ").split(". ")
        summary = sentences[0] if sentences else text
        if len(summary) > max_length:
            summary = summary[:max_length].rsplit(" ", 1)[0] + "..."
        logger.info(f"summarize_text: input={len(text)} chars, summary={len(summary)} chars")
        return {"status": "success", "message": f"Summarized from {len(text)} to {len(summary)} chars", "summary": summary}

    def classify_text(self, text: str, categories: List[str]) -> Dict[str, Any]:
        """Classify text into one of the given categories (basic keyword matching)."""
        if not text:
            return {"status": "error", "message": "No text provided", "category": "", "confidence": 0.0}
        if not categories:
            return {"status": "error", "message": "No categories provided", "category": "", "confidence": 0.0}
        text_lower = text.lower()
        scores = {}
        for cat in categories:
            keyword_count = sum(1 for word in cat.lower().split() if word in text_lower)
            scores[cat] = keyword_count
        best_cat = max(scores, key=scores.get)
        best_score = scores[best_cat]
        total_keywords = sum(len(c.split()) for c in categories)
        confidence = best_score / total_keywords if total_keywords > 0 else 0.0
        logger.info(f"classify_text: category={best_cat}, confidence={confidence:.2f}")
        return {"status": "success", "message": f"Classified as '{best_cat}'", "category": best_cat, "confidence": confidence}

