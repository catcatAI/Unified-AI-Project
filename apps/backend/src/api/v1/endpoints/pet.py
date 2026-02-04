#!/usr/bin/env python3
"""
Desktop Pet API 端點
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional
import logging
from ....pet.pet_manager import PetManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pet", tags=["Desktop Pet"])

# 共享的 PetManager 實例 (實際應用中應由 SystemManager 管理)
_pet_manager = PetManager(
    pet_id="angela_v1",
    config={
        "initial_personality": {"curiosity": 0.8, "playfulness": 0.9},
        "initial_behaviors": {"on_interaction": "show_happiness"}
    }
)

@router.get("/status")
async def get_pet_status():
    """獲取寵物當前狀態"""
    return {
        "pet_id": _pet_manager.pet_id,
        "state": _pet_manager.get_current_state(),
        "personality": _pet_manager.personality,
        "mood": "happy", # 模擬情緒
        "emotion_intensity": 0.8
    }

@router.post("/interaction")
async def handle_interaction(interaction: Dict[str, Any] = Body(...)):
    """處理用戶與寵物的交互"""
    # 支援不同的輸入格式
    interaction_type = interaction.get("type", interaction.get("action", "unknown"))
    interaction_data = interaction.get("data", interaction)
    
    if "type" not in interaction_data:
        interaction_data["type"] = interaction_type
        
    result = _pet_manager.handle_interaction(interaction_data)
    
    # 模擬情感回饋
    emotions = {
        "pet": {"mood": "happy", "text": "Angela 覺得很舒服~"},
        "feed": {"mood": "satisfied", "text": "Angela 吃飽了，好滿足！"},
        "play": {"mood": "excited", "text": "太好玩了！再來一次！"},
        "message": {"mood": "curious", "text": "Angela 正在認真聽你說話..."}
    }
    
    emotion_info = emotions.get(interaction_type, {"mood": "neutral", "text": "Angela 眨了眨眼。"})
    
    return {
        "status": "success",
        "pet_response": emotion_info["text"],
        "emotion": emotion_info["mood"],
        "new_state": result["new_state"]
    }

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
