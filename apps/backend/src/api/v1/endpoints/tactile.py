#!/usr/bin/env python3
"""
Tactile API 端點
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, List, Optional
import logging
from ....services.tactile_service import TactileService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tactile", tags=["Tactile"])

# 共享的 TactileService 實例
_tactile_service = TactileService()

@router.post("/model")
async def tactile_model(visual_data: Dict[str, Any] = Body(...)):
    """基於視覺數據建模觸覺反饋"""
    try:
        result = await _tactile_service.model_tactile_feedback(visual_data)
        return result
    except Exception as e:
        logger.error(f"Tactile modeling error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trigger")
async def trigger_tactile(trigger_data: Dict[str, Any] = Body(...)):
    """觸發物理觸覺設備"""
    try:
        device_id = trigger_data.get("device_id")
        intensity = trigger_data.get("intensity", 0.5)
        pattern = trigger_data.get("pattern", "default")
        
        result = await _tactile_service.trigger_physical_feedback(device_id, intensity, pattern)
        return result
    except Exception as e:
        logger.error(f"Tactile trigger error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/control")
async def tactile_control(params: Dict[str, Any] = Body(...)):
    """控制觸覺模組開關"""
    enabled = params.get("enabled", True)
    try:
        from ....core.sync.realtime_sync import sync_manager, SyncEvent
        await sync_manager.broadcast_event(SyncEvent(
            event_type="module_control",
            data={"module": "tactile", "enabled": enabled},
            source="api_endpoint"
        ))
        return {"status": "success", "module": "tactile", "enabled": enabled}
    except Exception as e:
        logger.error(f"Tactile control error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
