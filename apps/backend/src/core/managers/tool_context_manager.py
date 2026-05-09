# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [A] [L7]
# [Task N.22/E2] Native AI Expansion: Tool Context Manager Spatial Memory
# =============================================================================

import logging
import uuid
from typing import Any, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ToolContextManager:
    """
    認知工具上下文的空間聯想管理器
    基於當前的 StateMatrix4D，從 memory_neuroplasticity_bridge 自動喚起最適合的情境參數。
    """

    def __init__(
        self, 
        config: Optional[Dict[str, Any]] = None,
        state_matrix: Optional[Any] = None,
        memory_bridge: Optional[Any] = None
    ):
        self.config = config or {}
        self.state_matrix = state_matrix
        self.memory_bridge = memory_bridge
        self.active_contexts: Dict[str, Dict[str, Any]] = {}
        logger.info("🛠️ [ToolContextManager] Native AI Spatial Memory associated.")

    def get_context(self, tool_id: str) -> Dict[str, Any]:
        """
        [E2] 情境自動喚起：根據當下狀態矩陣，檢索最相關的工具上下文
        """
        search_radius = 5.0
        best_context = None
        
        if self.state_matrix and self.memory_bridge:
            try:
                # 以 Gamma(情緒) 座標來尋找上下文
                pos = self.state_matrix.get_position().get("gamma", (0.0, 0.0, 0.0))
                x, y, z = pos
                
                # 從記憶橋接器透過空間接近性檢索
                nearby_mems = self.memory_bridge.retrieve_by_spatial_proximity(x, y, z, search_radius)
                
                # 尋找屬於這個 tool_id 的最近記憶
                for mem_id in nearby_mems:
                    if f"tool_{tool_id}" in mem_id:
                        mem_content = self.memory_bridge.access_memory(mem_id)
                        if isinstance(mem_content, dict):
                            best_context = mem_content
                            logger.info(f"✨ [ToolContextManager] Auto-recalled context for {tool_id} via Spatial Proximity.")
                            break
            except Exception as e:
                logger.error(f"❌ [ToolContextManager] Spatial recall failed: {e}")

        # Fallback to active contexts or default
        if not best_context:
            best_context = self.active_contexts.get(tool_id, {"tool_id": tool_id, "status": "active", "data": {}})
            
        return best_context

    def update_context(self, tool_id: str, new_context: Dict[str, Any]):
        """
        [E2] 將工具使用上下文打包為「空間錨點」並存入記憶橋接器
        """
        self.active_contexts[tool_id] = new_context
        
        if self.state_matrix and self.memory_bridge:
            try:
                pos = self.state_matrix.get_position().get("gamma", (0.0, 0.0, 0.0))
                
                # 將這段情境存成神經記憶
                mem_id = f"tool_{tool_id}_{uuid.uuid4().hex[:6]}"
                self.memory_bridge.register_memory(
                    memory_id=mem_id,
                    content=new_context,
                    emotional_weight=0.6,
                    category="tool_context",
                    tags=[tool_id],
                    initial_strength=0.8,
                    coordinate=pos
                )
                logger.info(f"💾 [ToolContextManager] Context for {tool_id} anchored at spatial pos {pos}.")
            except Exception as e:
                logger.error(f"❌ [ToolContextManager] Failed to anchor context: {e}")

    def reset_context(self, tool_id: str):
        """重置當前快取的上下文"""
        if tool_id in self.active_contexts:
            del self.active_contexts[tool_id]
        logger.debug(f"Resetting context for tool: {tool_id}")
