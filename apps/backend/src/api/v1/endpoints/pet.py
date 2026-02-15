#!/usr/bin/env python3
"""
Desktop Pet API 端點
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional
import logging
from pet.pet_manager import PetManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pet", tags=["Desktop Pet"])

# 共享的 PetManager 實例
_pet_manager = PetManager(
    pet_id="angela_v1",
    config={
        "initial_personality": {"curiosity": 0.8, "playfulness": 0.9},
        "initial_behaviors": {"on_interaction": "show_happiness"}
    }
)

def get_pet_manager() -> PetManager:
    """獲取目前的 PetManager 實例"""
    return _pet_manager

def set_biological_integrator(integrator):
    """設置生理整合器並同步"""
    _pet_manager.biological_integrator = integrator
    _pet_manager.sync_with_biological_state()

def set_economy_manager(manager):
    """設置經濟管理器"""
    _pet_manager.set_economy_manager(manager)

@router.get("/status")
async def get_pet_status():
    """獲取寵物當前狀態 (同步生理數據後)"""
    _pet_manager.sync_with_biological_state()
    return {
        "pet_id": _pet_manager.pet_id,
        "state": _pet_manager.get_current_state(),
        "personality": _pet_manager.personality,
        "actions": _pet_manager.get_pending_actions()  # 返回並清除待執行動作
    }

@router.post("/interaction")
async def handle_interaction(interaction: Dict[str, Any] = Body(...)):
    """處理用戶與寵物的交互"""
    interaction_type = interaction.get("type", interaction.get("action", "unknown"))
    interaction_data = interaction.get("data", interaction)

    if "type" not in interaction_data:
        interaction_data["type"] = interaction_type

    # 修復：添加 await 關鍵字
    result = await _pet_manager.handle_interaction(interaction_data)

    return {
        "status": "success",
        "new_state": result["new_state"]
    }

@router.post("/position")
async def update_position(pos_data: Dict[str, Any] = Body(...)):
    """更新寵物在桌面上的位置"""
    x = pos_data.get("x", 0)
    y = pos_data.get("y", 0)
    scale = pos_data.get("scale")
    _pet_manager.update_position(x, y, scale)
    return {"status": "success", "current_position": _pet_manager.state["position"]}

@router.post("/action/trigger")
async def trigger_action(action_data: Dict[str, Any] = Body(...)):
    """手動觸發寵物動作 (用於測試或外部調用)"""
    action_type = action_data.get("type", "idle")
    data = action_data.get("data", {})
    _pet_manager.add_action(action_type, data)
    return {"status": "success", "message": f"Action {action_type} added to queue"}

@router.post("/mood/update")
async def update_mood(mood_data: Dict[str, Any] = Body(...)):
    """更新寵物情緒 (由 AI 核心調用)"""
    mood = mood_data.get("mood")
    intensity = mood_data.get("intensity", 0.5)
    logger.info(f"Updating pet mood to {mood} with intensity {intensity}")
    return {"status": "success", "current_mood": mood, "intensity": intensity}

@router.get("/config")
async def get_pet_config():
    """獲取寵物配置"""
    return {
        "name": "Angela",
        "version": "1.0.0",
        "live2d_enabled": True,
        "model_path": "assets/models/angela/model.json"
    }
