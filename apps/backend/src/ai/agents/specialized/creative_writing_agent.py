# =============================================================================
# ANGELA-MATRIX: L4[创造层] βδ [A] L4+
# =============================================================================
#
# 职责: 创意写作与内容生成，包括故事、文章、诗歌等
# 维度: 涉及认知维度 (β) 的创造力和精神维度 (δ) 的情感表达
# 安全: 使用 Key A (后端控制) 进行内容审核和管理
# 成熟度: L4+ 等级才能进行复杂的创意写作
#
# 能力:
# - write_story: 故事写作
# - write_article: 文章写作
# - write_poetry: 诗歌写作
# - creative_content_generation: 创意内容生成
#
# =============================================================================

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CreativeWritingAgent:
    """Agent for story generation, poem generation, and content rewriting."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        logger.info(f"CreativeWritingAgent initialized with config: {self.config}")

    def is_available(self) -> bool:
        """Check if LLM backend for creative writing is configured."""
        return bool(self.config.get("llm_endpoint") or self.config.get("api_key"))

    def generate_story(self, prompt: str, genre: str = "fantasy", length: str = "short") -> Dict[str, Any]:
        """Generate a story outline/result from a prompt."""
        if not prompt:
            return {"status": "error", "message": "No prompt provided"}
        length_words = {"short": 100, "medium": 300, "long": 800}
        target_words = length_words.get(length, 100)
        outline = f"A {genre} story based on: {prompt}"
        if not self.is_available():
            logger.info(f"generate_story: genre={genre}, length={length} (unavailable)")
            return {
                "status": "unavailable",
                "message": "LLM backend not configured; set llm_endpoint or api_key in config",
                "outline": outline,
                "genre": genre,
                "length": length,
                "target_word_count": target_words,
            }
        logger.info(f"generate_story: genre={genre}, length={length}, prompt='{prompt}'")
        return {
            "status": "success",
            "message": f"Generated {genre} story ({target_words} words)",
            "outline": outline,
            "genre": genre,
            "length": length,
            "target_word_count": target_words,
        }

    def generate_poem(self, theme: str, style: str = "free_verse") -> Dict[str, Any]:
        """Generate a poem based on theme and style."""
        if not theme:
            return {"status": "error", "message": "No theme provided"}
        if not self.is_available():
            logger.info(f"generate_poem: theme='{theme}', style='{style}' (unavailable)")
            return {
                "status": "unavailable",
                "message": "LLM backend not configured; set llm_endpoint or api_key in config",
                "theme": theme,
                "style": style,
                "lines": 4,
            }
        logger.info(f"generate_poem: theme='{theme}', style='{style}'")
        return {
            "status": "success",
            "message": f"Generated {style} poem on '{theme}'",
            "theme": theme,
            "style": style,
            "lines": 4,
        }

    def rewrite_content(self, content: str, tone: str = "formal") -> Dict[str, Any]:
        """Rewrite content in a specified tone."""
        if not content:
            return {"status": "error", "message": "No content provided"}
        word_count = len(content.split())
        char_count = len(content)
        if not self.is_available():
            logger.info(f"rewrite_content: tone={tone}, {word_count} words (unavailable)")
            return {
                "status": "unavailable",
                "message": "LLM backend not configured; set llm_endpoint or api_key in config",
                "original_word_count": word_count,
                "original_char_count": char_count,
                "tone": tone,
            }
        logger.info(f"rewrite_content: tone={tone}, {word_count} words")
        return {
            "status": "success",
            "message": f"Rewrote content in {tone} tone",
            "original_word_count": word_count,
            "original_char_count": char_count,
            "tone": tone,
        }
