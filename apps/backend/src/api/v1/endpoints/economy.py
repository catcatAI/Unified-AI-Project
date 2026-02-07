from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Dict, Any, Optional
from src.economy.economy_manager import EconomyManager
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/economy", tags=["Economy"])

# Global instance
_economy_manager: Optional[EconomyManager] = None

def set_economy_manager(manager: EconomyManager):
    global _economy_manager
    _economy_manager = manager
    logger.info("EconomyManager instance set for API endpoint")

@router.get("/balance/{user_id}")
async def get_balance(user_id: str):
    if not _economy_manager:
        raise HTTPException(status_code=503, detail="Economy service not initialized")
    balance = _economy_manager.get_balance(user_id)
    return {"user_id": user_id, "balance": balance, "currency": "AngelaCoins"}

@router.post("/transaction")
async def process_transaction(
    user_id: str = Body(...), 
    amount: float = Body(...), 
    description: str = Body("Manual Transaction")
):
    if not _economy_manager:
        raise HTTPException(status_code=503, detail="Economy service not initialized")
    
    success = _economy_manager.add_transaction(user_id, amount, description)
    if success:
        return {"status": "success", "new_balance": _economy_manager.get_balance(user_id)}
    raise HTTPException(status_code=400, detail="Transaction failed")

@router.get("/status")
async def get_economy_status():
    if not _economy_manager:
        return {"status": "not_initialized"}
    return {
        "status": "active",
        "service": "Angela Economy System",
        "version": "1.0.0"
    }
