import asyncio
import logging
import uuid
import re
from typing import Dict, Any, List, Optional

from ..base.base_agent import BaseAgent
from ....core.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope

logger = logging.getLogger(__name__)

class NLPProcessingAgent(BaseAgent):
    """
    A specialized agent for natural language processing tasks.
    """

    def __init__(self, agent_id: str) -> None:
        capabilities = [
            {
                "capability_id": f"{agent_id}_text_summarization_v1.0",
                "name": "text_summarization",
                "description": "Generates concise summaries of provided text content.",
                "version": "1.0",
                "parameters": [
                    {"name": "text", "type": "string", "required": True, "description": "Text content to summarize"}
                ],
                "returns": {"type": "object", "description": "Summarized text."}
            },
            {
                "capability_id": f"{agent_id}_sentiment_analysis_v1.0",
                "name": "sentiment_analysis",
                "description": "Performs sentiment analysis on text content.",
                "version": "1.0",
                "parameters": [
                    {"name": "text", "type": "string", "required": True, "description": "Text for analysis"}
                ],
                "returns": {"type": "object", "description": "Sentiment results."}
            }
        ]
        super().__init__(agent_id=agent_id, capabilities=capabilities, agent_name="NLPProcessingAgent")

        # Register handlers
        self.register_task_handler(f"{agent_id}_text_summarization_v1.0", self._handle_summarization)
        self.register_task_handler(f"{agent_id}_sentiment_analysis_v1.0", self._handle_sentiment)

    async def _handle_summarization(self, payload: HSPTaskRequestPayload, sender_id: str, envelope: HSPMessageEnvelope) -> Dict[str, Any]:
        text = payload.get("parameters", {}).get("text", "")
        if not text: return {"summary": "", "error": "No text"}
        return {"summary": text[:100] + "...", "original_length": len(text)}

    async def _handle_sentiment(self, payload: HSPTaskRequestPayload, sender_id: str, envelope: HSPMessageEnvelope) -> Dict[str, Any]:
        text = payload.get("parameters", {}).get("text", "")
        return {"sentiment": "neutral", "score": 0.5}