"""
Cluster management for compute node distribution.
Consolidated from system.cluster_manager.
"""

import asyncio
import datetime
import logging
import uuid
from enum import Enum
from typing import Any, Dict

from core.system.config.magic_numbers import loop_sleep
from core.system.live_logger import status as live_status

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
    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    def register_node(self, node_id: str, node_info: Dict[str, Any]) -> bool:
        if node_id in self.nodes:
            logger.warning(f"Node '{node_id}' already registered.")
            return False
        node_info.setdefault("type", NodeType.LOCAL.value)
        node_info.setdefault("precision", PrecisionLevel.FP32.value)
        node_info.setdefault("status", "idle")
        node_info.setdefault("registered_at", datetime.datetime.now().isoformat())
        self.nodes[node_id] = node_info
        logger.info(f"Node '{node_id}' registered: {node_info}")
        return True

    def remove_node(self, node_id: str) -> bool:
        if node_id not in self.nodes:
            logger.warning(f"Node '{node_id}' not found.")
            return False
        del self.nodes[node_id]
        logger.info(f"Node '{node_id}' removed from cluster.")
        return True

    async def distribute_task(self, task_type: str, data: list) -> str:
        task_id = str(uuid.uuid4())
        async with self._lock:
            if not self.nodes:
                logger.warning("No nodes registered; task queued but not dispatched.")
                return task_id
            target_node = None
            for nid, info in self.nodes.items():
                if info.get("status") == "idle" or task_type in info.get("capabilities", []):
                    target_node = nid
                    break
            if target_node is None:
                target_node = next(iter(self.nodes))
            self.nodes[target_node]["status"] = "busy"
            logger.debug(f"Distributing task {task_id} ({task_type}) -> node '{target_node}'")
            await asyncio.sleep(loop_sleep("cluster_task_distribute", 0.1))
            self.nodes[target_node]["status"] = "idle"
        return task_id

    def get_cluster_status(self) -> Dict[str, Any]:
        return {
            "node_count": len(self.nodes),
            "nodes": {
                nid: {
                    "type": info.get("type"),
                    "precision": info.get("precision"),
                    "status": info.get("status", "unknown"),
                    "registered_at": info.get("registered_at"),
                }
                for nid, info in self.nodes.items()
            },
        }


cluster_manager = ClusterManager()
