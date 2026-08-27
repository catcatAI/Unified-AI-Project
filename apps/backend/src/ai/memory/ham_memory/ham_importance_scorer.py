# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ImportanceScorer:
    """Enhanced importance scorer with multi-dimensional evaluation"""

    # Keywords with different weight levels
    URGENT_KEYWORDS = {
        "urgent",
        "critical",
        "emergency",
        "asap",
        "immediately",
        "priority",
        "important",
        "vital",
        "essential",
        "significant",
        "重要",
        "紧急",
        "关键",
        "优先",
        "必须",
    }

    ERROR_KEYWORDS = {
        "error",
        "failure",
        "crash",
        "exception",
        "bug",
        "issue",
        "problem",
        "错误",
        "失败",
        "崩溃",
        "异常",
        "问题",
    }

    POSITIVE_KEYWORDS = {
        "success",
        "achieved",
        "completed",
        "done",
        "finished",
        "solved",
        "成功",
        "完成",
        "解决",
        "达成",
    }

    QUESTION_KEYWORDS = {
        "?",
        "？",
        "what",
        "how",
        "why",
        "when",
        "where",
        "who",
        "什么",
        "如何",
        "为什么",
        "什么时候",
        "哪里",
        "谁",
    }

    # -------------------------------------------------------------------------
    # Sub-score coefficients — named constants (previously bare literals inside
    # the _calculate_* helpers). Calibrated 2026-07-15 (§X #260); recalibrate
    # HERE, never inline, so the four-dimension weights above stay meaningful.
    # -------------------------------------------------------------------------
    # Keyword sub-scores: (per-match step, cap)
    KW_URGENT_STEP = 0.15
    KW_URGENT_CAP = 0.4
    KW_ERROR_STEP = 0.10
    KW_ERROR_CAP = 0.3
    KW_POSITIVE_STEP = 0.05
    KW_POSITIVE_CAP = 0.15
    KW_QUESTION_STEP = 0.08
    KW_QUESTION_CAP = 0.15
    # Content sub-scores
    CONTENT_LONG_LEN = 200
    CONTENT_LONG_SCORE = 0.2
    CONTENT_MEDIUM_LEN = 100
    CONTENT_MEDIUM_SCORE = 0.1
    CONTENT_CODE_BLOCK_SCORE = 0.3
    CONTENT_CONTROL_FLOW_SCORE = 0.2
    CONTENT_NUMERIC_SCORE = 0.1
    CONTENT_URL_SCORE = 0.15
    CONTENT_CAP = 0.5
    # Metadata sub-scores
    META_USER_SPEAKER_SCORE = 0.2
    META_SYSTEM_SPEAKER_SCORE = 0.1
    META_PROTECTED_SCORE = 0.3
    META_IMPORTANCE_HIGH_SCORE = 0.25
    META_IMPORTANCE_MED_SCORE = 0.1
    META_TAG_STEP = 0.05
    META_TAG_CAP = 0.15
    META_EMOTION_SCORE = 0.1
    META_CAP = 0.5
    # Access sub-scores
    ACCESS_RECENT_WINDOW_HOURS = 24
    ACCESS_FREQ_STEP = 0.05
    ACCESS_FREQ_CAP = 0.5
    ACCESS_RECENT_STEP = 0.1
    ACCESS_RECENT_CAP = 0.3

    # Time-decay sub-scores (named — were bare literals in _calculate_time_score
    # / record_access / cleanup_old_history).
    TIME_DECAY_FACTOR = 0.95        # daily exponential decay factor
    TIME_DECAY_FLOOR = 0.3          # minimum recency score for old memories
    TIME_FRESH_DAYS = 1             # no decay within this many days
    TIME_ERROR_FALLBACK = 0.5       # score when timestamp is unparseable
    ACCESS_HISTORY_MAX = 100        # per-memory access entries kept
    HISTORY_RETENTION_DAYS = 30     # default cleanup window

    def __init__(self):
        self._access_history: Dict[str, List[datetime]] = {}
        self._time_decay_factor = self.TIME_DECAY_FACTOR
        # Dimension weights (must sum to 1.0).
        self._keyword_weight = 0.30  # Weight for keyword analysis
        self._content_weight = 0.05  # Weight for content characteristics
        self._metadata_weight = 0.30  # Weight for metadata factors
        self._access_weight = 0.05  # Weight for access frequency
        self._time_weight = 0.30  # Weight for recency

    async def calculate(self, content: str, metadata: Dict[str, Any]) -> float:
        """
        Calculates an importance score for a given memory using multi-dimensional analysis.

        Factors considered:
        1. Keyword analysis (urgent, error, question keywords)
        2. Content characteristics (length, complexity)
        3. Metadata factors (speaker, protected status, custom tags)
        4. Access frequency and recency
        5. Time decay

        Args:
            content: The memory content to evaluate
            metadata: Additional metadata about the memory

        Returns:
            Importance score between 0.0 and 1.0
        """
        memory_id = metadata.get("memory_id", "")

        # Calculate individual scores
        keyword_score = self._calculate_keyword_score(content)
        content_score = self._calculate_content_score(content)
        metadata_score = self._calculate_metadata_score(metadata)
        access_score = self._calculate_access_score(memory_id)
        time_score = self._calculate_time_score(metadata.get("timestamp"))

        # Combine scores using weighted average
        total_score = (
            keyword_score * self._keyword_weight
            + content_score * self._content_weight
            + metadata_score * self._metadata_weight
            + access_score * self._access_weight
            + time_score * self._time_weight
        )

        return min(1.0, max(0.0, total_score))

    def _calculate_keyword_score(self, content: str) -> float:
        """Calculate score based on keyword presence and frequency"""
        content_lower = content.lower()
        score = 0.0

        # Urgent keywords - highest weight
        urgent_count = sum(1 for kw in self.URGENT_KEYWORDS if kw in content_lower)
        if urgent_count > 0:
            score += min(self.KW_URGENT_CAP, urgent_count * self.KW_URGENT_STEP)

        # Error keywords - high weight
        error_count = sum(1 for kw in self.ERROR_KEYWORDS if kw in content_lower)
        if error_count > 0:
            score += min(self.KW_ERROR_CAP, error_count * self.KW_ERROR_STEP)

        # Positive keywords - medium weight
        positive_count = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in content_lower)
        if positive_count > 0:
            score += min(self.KW_POSITIVE_CAP, positive_count * self.KW_POSITIVE_STEP)

        # Question keywords - questions are often important
        question_count = sum(1 for kw in self.QUESTION_KEYWORDS if kw in content_lower)
        if question_count > 0:
            score += min(self.KW_QUESTION_CAP, question_count * self.KW_QUESTION_STEP)

        return score

    def _calculate_content_score(self, content: str) -> float:
        """Calculate score based on content characteristics"""
        score = 0.0
        content_length = len(content)

        # Longer content tends to be more substantial
        if content_length > self.CONTENT_LONG_LEN:
            score += self.CONTENT_LONG_SCORE
        elif content_length > self.CONTENT_MEDIUM_LEN:
            score += self.CONTENT_MEDIUM_SCORE

        # Code or structured content (has specific patterns)
        if re.search(r"\b(function|class|def|import|from)\b", content):
            score += self.CONTENT_CODE_BLOCK_SCORE
        elif re.search(r"\b(if|for|while|return)\b", content):
            score += self.CONTENT_CONTROL_FLOW_SCORE

        # Contains numbers or measurements (factual data)
        if re.search(r"\b\d+(\.\d+)?\b", content):
            score += self.CONTENT_NUMERIC_SCORE

        # Contains URLs or references
        if re.search(r"https?://\S+", content):
            score += self.CONTENT_URL_SCORE

        return min(self.CONTENT_CAP, score)

    def _calculate_metadata_score(self, metadata: Dict[str, Any]) -> float:
        """Calculate score based on metadata factors"""
        score = 0.0

        # User messages are more important
        if metadata.get("speaker") == "user":
            score += self.META_USER_SPEAKER_SCORE
        elif metadata.get("speaker") == "system":
            score += self.META_SYSTEM_SPEAKER_SCORE

        # Protected memories are highly important
        if metadata.get("protected", False):
            score += self.META_PROTECTED_SCORE

        # Custom importance tag
        if metadata.get("importance") == "high":
            score += self.META_IMPORTANCE_HIGH_SCORE
        elif metadata.get("importance") == "medium":
            score += self.META_IMPORTANCE_MED_SCORE

        # Memories with tags might be more important
        tags = metadata.get("tags", [])
        if tags:
            score += min(self.META_TAG_CAP, len(tags) * self.META_TAG_STEP)

        # Memories with emotional context
        emotion = metadata.get("emotion", {})
        if emotion:
            score += self.META_EMOTION_SCORE

        return min(self.META_CAP, score)

    def _calculate_access_score(self, memory_id: str) -> float:
        """Calculate score based on access frequency and recency"""
        if not memory_id or memory_id not in self._access_history:
            return 0.0

        accesses = self._access_history[memory_id]
        if not accesses:
            return 0.0

        # Recent accesses (last N hours) get higher score
        now = datetime.now()
        recent_window = timedelta(hours=self.ACCESS_RECENT_WINDOW_HOURS)
        recent_accesses = [a for a in accesses if (now - a) < recent_window]

        # Base score from access frequency
        score = min(self.ACCESS_FREQ_CAP, len(accesses) * self.ACCESS_FREQ_STEP)

        # Bonus for recent accesses
        score += min(self.ACCESS_RECENT_CAP, len(recent_accesses) * self.ACCESS_RECENT_STEP)

        return score

    def _calculate_time_score(self, timestamp: Any) -> float:
        """Calculate time decay score - older memories get lower score"""
        try:
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            elif not isinstance(timestamp, datetime):
                # No timestamp -> memory is being scored at creation time,
                # so treat it as maximally recent.
                return 1.0

            now = datetime.now()
            age_days = (now - timestamp).days

            # No decay for very recent memories
            if age_days < self.TIME_FRESH_DAYS:
                return 1.0

            # Apply exponential decay
            decay = self._time_decay_factor**age_days
            return max(self.TIME_DECAY_FLOOR, decay)

        except (
            Exception
        ) as e:  # broad exception acceptable: time score fallback should return default
            logger.warning(f"Error calculating time score: {e}", exc_info=True)
            return self.TIME_ERROR_FALLBACK

    def record_access(self, memory_id: str) -> None:
        """Record that a memory was accessed"""
        if memory_id not in self._access_history:
            self._access_history[memory_id] = []

        self._access_history[memory_id].append(datetime.now())

        # Keep only recent history
        if len(self._access_history[memory_id]) > self.ACCESS_HISTORY_MAX:
            self._access_history[memory_id] = self._access_history[memory_id][
                -self.ACCESS_HISTORY_MAX :
            ]

    def cleanup_old_history(self, days: int = HISTORY_RETENTION_DAYS) -> None:
        """Remove access history older than specified days"""
        cutoff = datetime.now() - timedelta(days=days)

        for memory_id in list(self._access_history.keys()):
            self._access_history[memory_id] = [
                access for access in self._access_history[memory_id] if access > cutoff
            ]

            # Remove empty entries
            if not self._access_history[memory_id]:
                del self._access_history[memory_id]
