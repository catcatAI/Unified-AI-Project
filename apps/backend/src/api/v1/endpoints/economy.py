from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Dict, Any, Optional
from economy.economy_manager import EconomyManager
import logging

from ._deps import get_economy_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/economy", tags=["Economy"])


@router.get("/balance/{user_id}")
async def get_balance(user_id: str, manager: EconomyManager = Depends(get_economy_manager)) -> dict:
    """Get the balance by user_id."""
    balance = manager.get_balance(user_id)
    return {"user_id": user_id, "balance": balance, "currency": "AngelaCoins"}


@router.post("/transaction")
async def process_transaction(
    user_id: str = Body(...),
    amount: float = Body(...),
    description: str = Body("Manual Transaction"),
    manager: EconomyManager = Depends(get_economy_manager),
):
    """Execute the process transaction operation."""
    success = manager.add_transaction(user_id, amount, description)
    if success:
        return {"status": "success", "new_balance": manager.get_balance(user_id)}
    raise HTTPException(status_code=400, detail="Transaction failed")


@router.get("/status")
async def get_economy_status(manager: EconomyManager = Depends(get_economy_manager)) -> dict:
    """Get the economy status by manager."""
    return {"status": "active", "service": "Angela Economy System", "version": "1.0.0"}
