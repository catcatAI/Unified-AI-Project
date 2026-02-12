import logging
import re
from typing import Any, Dict, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ImportanceScorer:
    """Enhanced importance scorer with multi-dimensional evaluation"""
    
    # Keywords with different weight levels
    URGENT_KEYWORDS = {
        'urgent', 'critical', 'emergency', 'asap', 'immediately', 'priority',
        '重要', '紧急', '关键', '优先', '必须'
    }
    
    ERROR_KEYWORDS = {
        'error', 'failure', 'crash', 'exception', 'bug', 'issue', 'problem',
        '错误', '失败', '崩溃', '异常', '问题'
    }
    
    POSITIVE_KEYWORDS = {
        'success', 'achieved', 'completed', 'done', 'finished', 'solved',
        '成功', '完成', '解决', '达成'
    }
    
    QUESTION_KEYWORDS = {
        '?', '？', 'what', 'how', 'why', 'when', 'where', 'who',
        '什么', '如何', '为什么', '什么时候', '哪里', '谁'
    }
    
    def __init__(self):
        self._access_history: Dict[str, List[datetime]] = {}
        self._time_decay_factor = 0.95  # Daily decay factor
        self._access_weight = 0.15  # Weight for access frequency
        self._keyword_weight = 0.40  # Weight for keyword analysis
        self._content_weight = 0.25  # Weight for content characteristics
        self._metadata_weight = 0.20  # Weight for metadata factors

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
            keyword_score * self._keyword_weight +
            content_score * self._content_weight +
            metadata_score * self._metadata_weight +
            access_score * self._access_weight +
            time_score * (1.0 - self._keyword_weight - self._content_weight - 
                         self._metadata_weight - self._access_weight)
        )
        
        return min(1.0, max(0.0, total_score))

    def _calculate_keyword_score(self, content: str) -> float:
        """Calculate score based on keyword presence and frequency"""
        content_lower = content.lower()
        score = 0.0
        
        # Urgent keywords - highest weight
        urgent_count = sum(1 for kw in self.URGENT_KEYWORDS if kw in content_lower)
        if urgent_count > 0:
            score += min(0.4, urgent_count * 0.15)
        
        # Error keywords - high weight
        error_count = sum(1 for kw in self.ERROR_KEYWORDS if kw in content_lower)
        if error_count > 0:
            score += min(0.3, error_count * 0.10)
        
        # Positive keywords - medium weight
        positive_count = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in content_lower)
        if positive_count > 0:
            score += min(0.15, positive_count * 0.05)
        
        # Question keywords - questions are often important
        question_count = sum(1 for kw in self.QUESTION_KEYWORDS if kw in content_lower)
        if question_count > 0:
            score += min(0.15, question_count * 0.08)
        
        return score

    def _calculate_content_score(self, content: str) -> float:
        """Calculate score based on content characteristics"""
        score = 0.0
        content_length = len(content)
        
        # Longer content tends to be more substantial
        if content_length > 200:
            score += 0.2
        elif content_length > 100:
            score += 0.1
        
        # Code or structured content (has specific patterns)
        if re.search(r'\b(function|class|def|import|from)\b', content):
            score += 0.3
        elif re.search(r'\b(if|for|while|return)\b', content):
            score += 0.2
        
        # Contains numbers or measurements (factual data)
        if re.search(r'\b\d+(\.\d+)?\b', content):
            score += 0.1
        
        # Contains URLs or references
        if re.search(r'https?://\S+', content):
            score += 0.15
        
        return min(0.5, score)

    def _calculate_metadata_score(self, metadata: Dict[str, Any]) -> float:
        """Calculate score based on metadata factors"""
        score = 0.0
        
        # User messages are more important
        if metadata.get("speaker") == "user":
            score += 0.2
        elif metadata.get("speaker") == "system":
            score += 0.1
        
        # Protected memories are highly important
        if metadata.get("protected", False):
            score += 0.3
        
        # Custom importance tag
        if metadata.get("importance") == "high":
            score += 0.25
        elif metadata.get("importance") == "medium":
            score += 0.1
        
        # Memories with tags might be more important
        tags = metadata.get("tags", [])
        if tags:
            score += min(0.15, len(tags) * 0.05)
        
        # Memories with emotional context
        emotion = metadata.get("emotion", {})
        if emotion:
            score += 0.1
        
        return min(0.5, score)

    def _calculate_access_score(self, memory_id: str) -> float:
        """Calculate score based on access frequency and recency"""
        if not memory_id or memory_id not in self._access_history:
            return 0.0
        
        accesses = self._access_history[memory_id]
        if not accesses:
            return 0.0
        
        # Recent accesses (last 24 hours) get higher score
        now = datetime.now()
        recent_accesses = [a for a in accesses if (now - a) < timedelta(hours=24)]
        
        # Base score from access frequency
        score = min(0.5, len(accesses) * 0.05)
        
        # Bonus for recent accesses
        score += min(0.3, len(recent_accesses) * 0.1)
        
        return score

    def _calculate_time_score(self, timestamp: Any) -> float:
        """Calculate time decay score - older memories get lower score"""
        try:
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            elif not isinstance(timestamp, datetime):
                return 0.5  # Default for unknown timestamps
            
            now = datetime.now()
            age_days = (now - timestamp).days
            
            # No decay for very recent memories (< 1 day)
            if age_days < 1:
                return 1.0
            
            # Apply exponential decay
            decay = self._time_decay_factor ** age_days
            return max(0.3, decay)  # Minimum score of 0.3
            
        except Exception as e:
            logger.warning(f"Error calculating time score: {e}")
            return 0.5

    def record_access(self, memory_id: str) -> None:
        """Record that a memory was accessed"""
        if memory_id not in self._access_history:
            self._access_history[memory_id] = []
        
        self._access_history[memory_id].append(datetime.now())
        
        # Keep only recent history (last 100 accesses)
        if len(self._access_history[memory_id]) > 100:
            self._access_history[memory_id] = self._access_history[memory_id][-100:]

    def cleanup_old_history(self, days: int = 30) -> None:
        """Remove access history older than specified days"""
        cutoff = datetime.now() - timedelta(days=days)
        
        for memory_id in list(self._access_history.keys()):
            self._access_history[memory_id] = [
                access for access in self._access_history[memory_id]
                if access > cutoff
            ]
            
            # Remove empty entries
            if not self._access_history[memory_id]:
                del self._access_history[memory_id]
