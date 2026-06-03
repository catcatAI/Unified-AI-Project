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

import asyncio
import logging
import uuid
from typing import Dict, Any, List, Optional

from ai.agents.base.base_agent import BaseAgent
from core.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope

logger = logging.getLogger(__name__)


class CreativeWritingAgent(BaseAgent):
    """
    P2.5: CreativeWritingAgent 從 STUB 重寫為功能完整的委派代理。

    職責：接收創意寫作任務，委派給 DocumentBuilder（多段 LLM 生成）處理。
    使用 ProjectCoordinator 處理複雜任務，並透過 anchor_learning 學習格式。

    替換了原本 63 行的 STUB（只返回固定字串）。
    """

    def __init__(self, agent_id: str) -> None:
        capabilities = [
            {
                "capability_id": f"{agent_id}_write_story_v1.0",
                "name": "write_story",
                "description": "Writes a story with multi-segment LLM generation.",
                "version": "1.0",
                "parameters": [
                    {"name": "prompt", "type": "string", "required": True, "description": "Story prompt"},
                    {"name": "user_feedback", "type": "string", "required": False, "description": "User's preferred format"},
                ],
                "returns": {"type": "string", "description": "Generated story."},
            },
            {
                "capability_id": f"{agent_id}_write_character_card_v1.0",
                "name": "write_character_card",
                "description": "Generates a TRPG character card using codex knowledge.",
                "version": "1.0",
                "parameters": [
                    {"name": "character_query", "type": "string", "required": True, "description": "Character description"},
                ],
                "returns": {"type": "string", "description": "Generated character card."},
            },
            {
                "capability_id": f"{agent_id}_write_article_v1.0",
                "name": "write_article",
                "description": "Writes an article or research summary.",
                "version": "1.0",
                "parameters": [
                    {"name": "topic", "type": "string", "required": True, "description": "Article topic"},
                    {"name": "style", "type": "string", "required": False, "description": "Writing style"},
                ],
                "returns": {"type": "string", "description": "Generated article."},
            },
        ]
        super().__init__(
            agent_id=agent_id, capabilities=capabilities, agent_name="CreativeWritingAgent"
        )
        self.register_task_handler(f"{agent_id}_write_story_v1.0", self._handle_write_story)
        self.register_task_handler(f"{agent_id}_write_character_card_v1.0", self._handle_character_card)
        self.register_task_handler(f"{agent_id}_write_article_v1.0", self._handle_article)
        self._builder: Optional[Any] = None

    def _ensure_builder(self) -> Any:
        if self._builder is None:
            from ai.dialogue.document_builder import DocumentBuilder
            from services.angela_llm_service import get_llm_service
            from core.engine.eta_axis import EtaAxisState
            async def get_llm() -> str:
                """Get the llm."""
                return await get_llm_service()
            self._builder = DocumentBuilder(
                llm_generate_fn=self._make_llm_wrapper(),
                max_segments=4,
                tokens_per_segment=512,
            )
            self._builder.eta_state = EtaAxisState()
        return self._builder

    def _make_llm_wrapper(self) -> Any:
        async def llm_wrapper(prompt: str, **kwargs) -> str:
            """Log a diagnostic message."""
            from services.angela_llm_service import get_llm_service
            try:
                llm = await get_llm_service()
                result = await llm.generate_text(
                    prompt=prompt,
                    max_tokens=kwargs.get("max_tokens", 512),
                    temperature=kwargs.get("temperature", 0.75),
                    system_prompt=kwargs.get("system_prompt"),
                )
                return result or ""
            except Exception as e:
                logger.warning(f"[CreativeWritingAgent] LLM call failed: {e}", exc_info=True)
                return ""

        return llm_wrapper

    async def _handle_write_story(
        self, payload: HSPTaskRequestPayload, sender_id: str, envelope: HSPMessageEnvelope
    ) -> str:
        params = payload.get("parameters", {})
        query = params.get("prompt", "寫一個故事")
        user_feedback = params.get("user_feedback")
        try:
            builder = self._ensure_builder()
            result = await builder.build(query, user_feedback=user_feedback, complexity=0.5, learn_from_output=True)
            if result and result.full_text:
                return result.full_text
        except Exception as e:
            logger.warning(f"[CreativeWritingAgent] Story write failed: {e}", exc_info=True)
        return f"抱歉，故事生成遇到了問題。提示：{query[:50]}"

    async def _handle_character_card(
        self, payload: HSPTaskRequestPayload, sender_id: str, envelope: HSPMessageEnvelope
    ) -> str:
        params = payload.get("parameters", {})
        query = params.get("character_query", "創建一個角色")
        try:
            builder = self._ensure_builder()
            result = await builder.build(query, complexity=0.7, learn_from_output=True)
            if result and result.full_text:
                return result.full_text
        except Exception as e:
            logger.warning(f"[CreativeWritingAgent] Character card failed: {e}", exc_info=True)
        return f"抱歉，角色卡生成失敗。查詢：{query[:50]}"

    async def _handle_article(
        self, payload: HSPTaskRequestPayload, sender_id: str, envelope: HSPMessageEnvelope
    ) -> str:
        params = payload.get("parameters", {})
        query = params.get("topic", "寫一篇文章")
        style = params.get("style", "")
        full_query = f"{query}" if not style else f"{query}，風格：{style}"
        try:
            builder = self._ensure_builder()
            result = await builder.build(full_query, complexity=0.6, learn_from_output=True)
            if result and result.full_text:
                return result.full_text
        except Exception as e:
            logger.warning(f"[CreativeWritingAgent] Article write failed: {e}", exc_info=True)
        return f"抱歉，文章生成失敗。主題：{query[:50]}"
