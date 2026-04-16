import logging
from enum import Enum
import uuid
import asyncio

logger = logging.getLogger(__name__)

class PrecisionLevel(Enum):
    FP32 = "FP32"
    FP16 = "FP16"
    FP8 = "FP8"
    INT8 = "INT8"
    INT4 = "INT4"

class NodeType(Enum):
    LOCAL = "LOCAL"
    EDGE = "EDGE"
    CLOUD = "CLOUD"

class ClusterManager:
    """
    Mock implementation of ClusterManager.
    The original file was deleted during a previous consolidation,
    but imports to this module still exist in the codebase.
    This stub prevents ModuleNotFoundErrors and provides graceful degradation.
    """
    def __init__(self):
        self.nodes = []

    async def distribute_task(self, task_type: str, data: list):
        """Mock task distribution."""
        task_id = str(uuid.uuid4())
        logger.debug(f"Mock distribute_task: {task_type} -> {task_id}")
        await asyncio.sleep(0.01)
        return task_id

cluster_manager = ClusterManager()
