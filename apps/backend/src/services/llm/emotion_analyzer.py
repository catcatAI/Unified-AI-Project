# -*- coding: utf-8 -*-
"""
Emotion Analyzer - Extracted from AngelaLLMService
===================================================
Provides keyword-based emotion recognition for Chinese text sentiment analysis.

ANGELA-MATRIX: L3 [γ] [A] [L0-L11]
"""

import logging
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger("angela_llm.emotion")


class EmotionAnalyzer:
    """Keyword-based emotion analyzer for Angela's conversation system."""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize the emotion analyzer with keyword sets and config."""
        self.config = config or {}
        self.emotion_keywords = self._init_emotion_keywords()
        self._init_emotion_config()
        logger.info(
            "Emotion recognition system initialized (supporting Simplified and Traditional Chinese)"
        )

    def _init_emotion_keywords(self) -> Dict[str, Dict]:
        """Initialize all emotion keyword sets."""
        return {
            "happy": self._init_happy_keywords(),
            "sad": self._init_sad_keywords(),
            "angry": self._init_angry_keywords(),
            "fear": self._init_fear_keywords(),
            "surprise": self._init_surprise_keywords(),
            "curious": self._init_curious_keywords(),
            "calm": self._init_calm_keywords(),
        }

    def _init_happy_keywords(self) -> dict:
        """Initialize happy emotion keywords."""
        return {
            "positive": [
                "开心", "快乐", "高兴", "喜欢", "爱", "棒", "好", "赞", "哈哈",
                "美好", "幸福", "满意", "欣赏", "感谢", "谢谢",
                "開心", "快樂", "高興", "喜歡", "愛", "棒", "好", "讚", "哈哈",
                "美好", "幸福", "滿意", "欣賞", "感謝", "謝謝",
                "好开心", "好喜欢", "太开心", "太喜欢", "真开心", "真喜欢",
                "好開心", "好喜歡", "太開心", "太喜歡", "真開心", "真喜歡",
                "😊", "😄", "🎉",
                "happy", "joy", "joyful", "glad", "delighted", "wonderful",
                "fantastic", "amazing", "great", "love", "awesome", "excellent",
                "beautiful", "fun", "exciting", "grateful", "thankful",
                "excited", "thrilled", "elated", "cheerful", "merry",
            ],
            "weight": 1.0,
        }

    def _init_sad_keywords(self) -> dict:
        """Initialize sad emotion keywords."""
        return {
            "negative": [
                "难过", "伤心", "悲伤", "哭", "痛苦", "难受", "失望",
                "遗憾", "郁闷", "糟糕", "不开心", "不喜欢", "讨厌",
                "難過", "傷心", "悲傷", "哭", "痛苦", "難受", "失望",
                "遺憾", "鬱悶", "糟糕", "不開心", "不喜歡", "討厭",
                "好难过", "好伤心", "好悲伤",
                "好難過", "好傷心", "好悲傷",
                "😢", "😭",
                "sad", "sadness", "unhappy", "depressed", "miserable",
                "heartbroken", "grief", "grieving", "lonely", "alone",
                "crying", "tears", "hurt", "painful", "sorrow",
                "melancholy", "mourn", "mourning", "devastated",
                "disappointed", "disappointment", "regret", "sorry",
            ],
            "weight": 1.0,
        }

    def _init_angry_keywords(self) -> dict:
        """Initialize angry emotion keywords."""
        return {
            "negative": [
                "生气", "愤怒", "讨厌", "恨", "烦", "气死", "火大",
                "生氣", "憤怒", "討厭", "恨", "煩", "氣死", "火大",
                "好生气", "好愤怒", "好生氣", "好憤怒",
                "😡", "😠",
                "angry", "anger", "mad", "furious", "outraged",
                "annoyed", "irritated", "frustrated", "rage",
                "hate", "hatred", "hostile", "aggressive",
                "fuming", "livid", "enraged", "infuriated",
            ],
            "weight": 1.2,
        }

    def _init_fear_keywords(self) -> dict:
        """Initialize fear emotion keywords."""
        return {
            "negative": [
                "害怕", "恐惧", "担心", "焦虑", "紧张",
                "害怕", "恐懼", "擔心", "焦慮", "緊張",
                "😨", "😱",
                "afraid", "scared", "frightened", "terrified", "horrified",
                "anxious", "nervous", "worried", "panic", "panicking",
                "fear", "fearful", "dread", "dreading", "alarmed",
                "shaken", "timid", "uneasy", "apprehensive",
                "terrifying", "frightening", "scary", "creepy",
            ],
            "weight": 1.1,
        }

    def _init_surprise_keywords(self) -> dict:
        """Initialize surprise emotion keywords."""
        return {
            "neutral": [
                "惊讶", "意外", "哇", "天哪",
                "驚訝", "意外", "哇", "天哪",
                "😲", "😮",
                "surprised", "surprise", "amazed", "astonished", "shocked",
                "stunned", "speechless", "incredible", "unexpected",
                "wow", "whoa", "unbelievable", "astounding",
                "startled", "dumbfounded", "floored",
            ],
            "weight": 0.9,
        }

    def _init_curious_keywords(self) -> dict:
        """Initialize curious emotion keywords."""
        return {
            "neutral": [
                "好奇", "想知道", "问", "什么", "怎么", "为什么",
                "想了解", "好奇宝宝", "很好奇",
                "好奇", "想知道", "問", "什麼", "怎麼", "為什麼",
                "想了解", "好奇寶寶", "很好奇",
                "curious", "curiosity", "wonder", "wondering", "interested",
                "intrigued", "fascinated", "fascinating", "tell me more",
                "how does", "why is", "what is", "explain", "understand",
                "learn", "discover", "explore", "question",
            ],
            "weight": 1.0,
        }

    def _init_calm_keywords(self) -> dict:
        """Initialize calm emotion keywords."""
        return {
            "neutral": [
                "平静", "安静", "放松", "休息",
                "平靜", "安靜", "放鬆", "休息",
                "calm", "peaceful", "relaxed", "serene", "tranquil",
                "quiet", "still", "content", "contentment", "easygoing",
                "gentle", "mellow", "soothing", "composed", "balanced",
                "meditative", "mindful", "zen", "harmony", "harmonious",
            ],
            "weight": 0.7,
        }

    def _init_emotion_config(self) -> None:
        """Initialize negation and intensifier words from config."""
        try:
            from core.config_loader import get_angela_config
            _em = get_angela_config().get("llm", {}).get("emotion", {})
        except (ImportError, FileNotFoundError, KeyError, AttributeError):
            logger.warning("_init_emotion_config failed, using empty config", exc_info=True)
            _em = {}
        self.negation_words = _em.get(
            "negation_words",
            ["不", "沒", "没", "别", "別", "非", "無", "无", "未"],
        )
        self.intensifier_words = _em.get(
            "intensifier_words",
            [
                "好", "很", "太", "非常", "超级", "特別",
                "特别", "真", "超", "極", "极", "格外", "尤其",
            ],
        )

    def _load_emotion_config(self) -> Tuple[List[str], List[str]]:
        """Load emotion config (returns negation and intensifier words)."""
        return self.negation_words, self.intensifier_words

    def _score_keyword_match(
        self, text: str, keyword: str, negation_words: list, intensifier_words: list
    ) -> Tuple[bool, bool]:
        """Score keyword match, detecting negation and intensifier proximity."""
        keyword_pos = text.find(keyword)
        has_negation = False
        for neg_word in negation_words:
            neg_pos = text.find(neg_word)
            if neg_pos != -1 and neg_pos < keyword_pos and (keyword_pos - neg_pos) <= 3:
                has_negation = True
                break
        has_intensifier = False
        for int_word in intensifier_words:
            int_pos = text.find(int_word)
            if int_pos != -1 and int_pos < keyword_pos and (keyword_pos - int_pos) <= 3:
                has_intensifier = True
                break
        return has_negation, has_intensifier

    def _score_emotion_keywords(
        self, text: str, keywords_data: dict, negation_words: list, intensifier_words: list
    ) -> Tuple[float, int]:
        """Score emotion keywords in text."""
        score = 0.0
        match_count = 0
        for keyword in keywords_data.get("positive", []):
            if keyword in text:
                has_negation, has_intensifier = self._score_keyword_match(
                    text, keyword, negation_words, intensifier_words
                )
                if has_negation:
                    score -= 0.5
                else:
                    if has_intensifier:
                        score += 1.5
                    else:
                        score += 1.0
                    match_count += 1
        for keyword in keywords_data.get("negative", []):
            if keyword in text:
                has_negation, has_intensifier = self._score_keyword_match(
                    text, keyword, negation_words, intensifier_words
                )
                if has_negation:
                    score -= 0.5
                else:
                    if has_intensifier:
                        score += 1.5
                    else:
                        score += 1.0
                    match_count += 1
        for keyword in keywords_data.get("neutral", []):
            if keyword in text:
                score += 0.8
                match_count += 1
        return score, match_count

    def _compute_emotion_result(self, emotion_scores: Dict[str, float]) -> Dict[str, Any]:
        """Compute emotion result from scores."""
        if not emotion_scores or all(score <= 0 for score in emotion_scores.values()):
            return {
                "emotion": "calm",
                "confidence": 0.5,
                "intensity": 0.3,
                "secondary_emotions": [],
            }
        positive_emotions = {k: v for k, v in emotion_scores.items() if v > 0}
        if not positive_emotions:
            return {
                "emotion": "calm",
                "confidence": 0.5,
                "intensity": 0.3,
                "secondary_emotions": [],
            }
        sorted_emotions = sorted(positive_emotions.items(), key=lambda x: x[1], reverse=True)
        primary_emotion, primary_score = sorted_emotions[0]
        if len(sorted_emotions) > 1:
            second_score = sorted_emotions[1][1]
            confidence = min(1.0, primary_score / (primary_score + second_score + 0.1))
        else:
            confidence = min(1.0, primary_score / (primary_score + 0.5))
        intensity = min(1.0, primary_score / 3.0)
        secondary_emotions = [
            {"emotion": emotion, "score": score}
            for emotion, score in sorted_emotions[1:3]
            if score > 0.5
        ]
        return {
            "emotion": primary_emotion,
            "confidence": confidence,
            "intensity": intensity,
            "secondary_emotions": secondary_emotions,
        }

    def analyze_emotion(self, text: str, response_text: str = None) -> Dict[str, Any]:
        """
        Analyze emotional state based on keyword-based multi-dimensional emotion analysis.

        Args:
            text: User input text
            response_text: Angela's response text (optional)

        Returns:
            Dict with emotion analysis results:
                - emotion: Primary emotion (happy, sad, angry, fear, surprise, curious, calm)
                - confidence: Emotion confidence (0-1)
                - intensity: Emotion intensity (0-1)
                - secondary_emotions: List of secondary emotions
        """
        negation_words, intensifier_words = self._load_emotion_config()

        emotion_scores = {}
        for emotion, keywords_data in self.emotion_keywords.items():
            score, match_count = self._score_emotion_keywords(
                text, keywords_data, negation_words, intensifier_words
            )
            if match_count > 0 or score != 0:
                emotion_scores[emotion] = score * keywords_data["weight"]

        return self._compute_emotion_result(emotion_scores)

    def analyze_response_emotion(self, response_text: str) -> Dict[str, Any]:
        """
        Analyze Angela response emotion.

        Args:
            response_text: Angela's response text

        Returns:
            Dict with emotion analysis results
        """
        return self.analyze_emotion(response_text, response_text)
