# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import logging
import math
import re
from typing import Any, Dict

logger = logging.getLogger(__name__)

IMPORTANT_KEYWORDS = [
    "error",
    "critical",
    "urgent",
    "important",
    "bug",
    "crash",
    "failure",
    "security",
    "vulnerability",
    "deadline",
    "priority",
    "blocker",
]

SOURCE_WEIGHTS = {
    "user": 1.0,
    "system": 0.8,
    "internal": 0.6,
    "external": 0.7,
    "feedback": 0.9,
    "error_log": 0.85,
    "metric": 0.5,
}


class ImportanceScorer:
    def __init__(self):
        logger.debug("[ImportanceScorer] Initialized")

    def calculate(self, content: Any, metadata: Dict[str, Any]) -> float:
        """Calculate importance score based on content analysis and metadata."""
        score = 0.0
        factors = 0

        if isinstance(content, str):
            content = content.strip()
            if not content:
                return 0.0

            length_factor = min(1.0, len(content) / 1000.0)
            score += length_factor * 0.3
            factors += 1

            content_lower = content.lower()
            keyword_hits = sum(1 for kw in IMPORTANT_KEYWORDS if kw in content_lower)
            if keyword_hits > 0:
                keyword_score = min(1.0, keyword_hits / 5.0)
                score += keyword_score * 0.3
                factors += 1

            content_type_score = 0.0
            if re.search(r"(def |class |import |@|\breturn\b)", content):
                content_type_score = max(content_type_score, 0.8)
            if re.search(r"(error|exception|traceback|fail)", content_lower):
                content_type_score = max(content_type_score, 0.9)
            if content.endswith("?"):
                content_type_score = max(content_type_score, 0.6)
            if content_type_score > 0:
                score += content_type_score * 0.2
                factors += 1

        priority = metadata.get("priority")
        if priority is not None:
            try:
                p = min(1.0, max(0.0, float(priority)))
                score += p * 0.15
                factors += 1
            except (ValueError, TypeError):
                logger.warning("Failed to parse priority value: %s", priority)

        source = metadata.get("source", "internal")
        src_weight = SOURCE_WEIGHTS.get(source, 0.5)
        score += src_weight * 0.15
        factors += 1

        if metadata.get("has_code", False):
            score += 0.1
            factors += 1

        if factors > 0:
            score = score / factors

        return max(0.0, min(1.0, score))
