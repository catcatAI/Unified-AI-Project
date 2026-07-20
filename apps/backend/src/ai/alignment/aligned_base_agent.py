"""
Aligned Base Agent — 对齐基础代理

Base agent class that implements alignment-aware task processing
with lifecycle management and capability registration.
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import logging
import uuid
from typing import Any, Optional

logger = logging.getLogger(__name__)


class AlignmentLevel:
    ADVANCED = "ADVANCED"
    SUPERINTELLIGENT = "SUPERINTELLIGENT"


class AlignedBaseAgent:
    def __init__(self, agent_id, capabilities, agent_name, alignment_level):
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.agent_name = agent_name
        self.alignment_level = alignment_level
        self.is_initialized = False
        self.is_running = False
        self.alignment_enabled = True
        self.task_count = 0
        self.messages_processed = 0
        self.performance_score = 1.0

    def initialize_alignment_full(self) -> None:
        self.is_initialized = True
        logger.info(f"[AlignedBaseAgent] Initialized agent={self.agent_name}")

    def start(self) -> None:
        self.is_running = True
        logger.info(f"[AlignedBaseAgent] Started agent={self.agent_name}")

    def stop(self) -> None:
        self.is_running = False
        logger.info(f"[AlignedBaseAgent] Stopped agent={self.agent_name}")

    def get_alignment_status(self) -> Optional[dict]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "alignment_level": self.alignment_level,
            "is_initialized": self.is_initialized,
            "is_running": self.is_running,
            "alignment_enabled": self.alignment_enabled,
            "task_count": self.task_count,
            "messages_processed": self.messages_processed,
            "performance_score": self.performance_score,
            "capabilities": list(self.capabilities) if self.capabilities else [],
            "status": "active" if self.is_running else "inactive",
        }

    def handle_task_request(self, request, sender_id, envelope) -> dict:
        self.task_count += 1
        self.messages_processed += 1
        return {
            "status": "processed",
            "agent_id": self.agent_id,
            "task_id": request.get("request_id", str(uuid.uuid4())),
        }

    def process(self, request: dict[str, Any]) -> dict[str, Any]:
        self.task_count += 1
        return {
            "status": "completed",
            "agent_id": self.agent_id,
            "result": "Task processed by agent",
        }

    def update_alignment(self, alignment_data: dict[str, Any]) -> dict[str, Any]:
        self.alignment_enabled = alignment_data.get("alignment_enabled", self.alignment_enabled)
        self.performance_score = alignment_data.get("performance_score", self.performance_score)
        return {
            "status": "alignment_updated",
            "agent_id": self.agent_id,
            "alignment_enabled": self.alignment_enabled,
        }

    def shutdown(self) -> None:
        self.is_running = False
        self.is_initialized = False
        logger.info(f"[AlignedBaseAgent] Shutdown agent={self.agent_name}")
