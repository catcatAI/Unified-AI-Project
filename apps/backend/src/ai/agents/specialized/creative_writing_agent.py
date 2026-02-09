import asyncio
import logging
import uuid
from typing import Dict, Any, List, Optional

from ..base.base_agent import BaseAgent
from core.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope

logger = logging.getLogger(__name__)

class CreativeWritingAgent(BaseAgent):
    """
    A specialized agent for creative writing tasks.
    """

    def __init__(self, agent_id: str) -> None:
        capabilities = [
            {
                "capability_id": f"{agent_id}_write_story_v1.0",
                "name": "write_story",
                "description": "Writes a story.",
                "version": "1.0",
                "parameters": [
                    {"name": "prompt", "type": "string", "required": True, "description": "Story prompt"}
                ],
                "returns": {"type": "string", "description": "Generated story."}
            }
        ]
        super().__init__(agent_id=agent_id, capabilities=capabilities, agent_name="CreativeWritingAgent")

        # Register handlers
        self.register_task_handler(f"{agent_id}_write_story_v1.0", self._handle_write_story)

    async def _handle_write_story(self, payload: HSPTaskRequestPayload, sender_id: str, envelope: HSPMessageEnvelope) -> str:
        params = payload.get("parameters", {})
        return f"Once upon a time, someone asked for {params.get('prompt', 'something')}..."