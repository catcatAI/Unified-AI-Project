"""
State Matrix FastAPI Router
==========================

為 StateMatrix4D 提供 HTTP API 接口。

端點：
  GET  /state/summary           — 完整狀態報告
  GET  /state/axis/{name}        — 單個軸的 values
  POST /state/axis/{name}/update — 更新軸值
  GET  /state/gradient           — 吸引子場梯度
  POST /state/navigate           — 沿梯度導航
  GET  /state/temporal/trend     — 時間趨勢查詢
  GET  /state/temporal/anomalies — 異常檢測
  POST /state/port/register      — 註冊端口
  POST /state/port/unregister    — 註銷端口
  GET  /state/port/list          — 列舉端口
  POST /state/ripple             — 應用漣漪
  GET  /state/allocation          — 分配決策
  GET  /state/negativity         — θ 自糾狀態
  POST /state/save                — 保存狀態
  POST /state/load                — 恢復狀態

使用方式:
    from api.state_matrix_api import state_matrix_router
    app.include_router(state_matrix_router, prefix="/api/v1")

Author: Angela AI v7.5
"""

from __future__ import annotations

import asyncio
import datetime
import logging
from typing import Any, Dict, List, Optional

from core.engine.state_matrix import StateMatrix4D
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Global state matrix instance (singleton pattern for API access)
_state_matrix_instance: Optional[StateMatrix4D] = None


def get_state_matrix() -> StateMatrix4D:
    """Get or create the global state matrix instance."""
    global _state_matrix_instance
    if _state_matrix_instance is None:
        _state_matrix_instance = StateMatrix4D()
    return _state_matrix_instance


# Request/Response models
class AxisUpdateRequest(BaseModel):
    """Request model for updating axis values."""
    values: Dict[str, float] = Field(default_factory=dict)


class AxisResponse(BaseModel):
    """Response model for axis data."""
    name: str
    values: Dict[str, float]
    timestamp: str


class StateSummaryResponse(BaseModel):
    """Response model for complete state summary."""
    alpha: Dict[str, float]
    beta: Dict[str, float]
    gamma: Dict[str, float]
    delta: Dict[str, float]
    epsilon: Dict[str, float]
    theta: Dict[str, float]
    timestamp: str


class RippleRequest(BaseModel):
    """Request model for applying ripple effects."""
    source_axis: str
    source_value: float
    target_axes: List[str]
    strength: float = 1.0


class AllocationRequest(BaseModel):
    """Request model for allocation decisions."""
    candidates: List[Dict[str, float]]
    dimension: str


class SaveStateRequest(BaseModel):
    """Request model for saving state."""
    filepath: Optional[str] = None


class LoadStateRequest(BaseModel):
    """Request model for loading state."""
    filepath: Optional[str] = None


# Sync helpers for file I/O (called via asyncio.to_thread to avoid blocking the event loop)
def _write_state_sync(filepath: str, state: dict) -> None:
    import json
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(state, f)


def _read_state_sync(filepath: str) -> dict:
    import json
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# Create router
state_matrix_router = APIRouter(prefix="/state", tags=["state-matrix"])


@state_matrix_router.get("/summary", response_model=StateSummaryResponse)
async def get_state_summary():
    """Get complete state matrix summary."""
    matrix = get_state_matrix()
    return {
        "alpha": dict(matrix.alpha.values or {}),
        "beta": dict(matrix.beta.values or {}),
        "gamma": dict(matrix.gamma.values or {}),
        "delta": dict(matrix.delta.values or {}),
        "epsilon": dict(matrix.epsilon.values or {}),
        "theta": dict(matrix.theta.values or {}),
        "timestamp": datetime.datetime.now().isoformat(),
    }


@state_matrix_router.get("/axis/{name}", response_model=AxisResponse)
async def get_axis(name: str):
    """Get a single axis state."""
    matrix = get_state_matrix()
    axis_map = {
        "alpha": matrix.alpha,
        "beta": matrix.beta,
        "gamma": matrix.gamma,
        "delta": matrix.delta,
        "epsilon": matrix.epsilon,
        "theta": matrix.theta,
    }
    if name not in axis_map:
        raise HTTPException(status_code=404, detail=f"Axis '{name}' not found")
    return {
        "name": name,
        "values": axis_map[name],
        "timestamp": datetime.datetime.now().isoformat(),
    }


@state_matrix_router.post("/axis/{name}/update", response_model=AxisResponse)
async def update_axis(name: str, request: AxisUpdateRequest):
    """Update a single axis with new values."""
    matrix = get_state_matrix()
    method_map = {
        "alpha": matrix.update_alpha,
        "beta": matrix.update_beta,
        "gamma": matrix.update_gamma,
        "delta": matrix.update_delta,
        "epsilon": matrix.update_epsilon,
        "theta": matrix.update_theta,
    }
    if name not in method_map:
        raise HTTPException(status_code=404, detail=f"Axis '{name}' not found")
    method_map[name](**request.values)
    return await get_axis(name)


@state_matrix_router.post("/compute-influences")
async def compute_influences():
    """Compute inter-dimensional influences."""
    matrix = get_state_matrix()
    matrix.compute_influences()
    return {"status": "computed", "influences": matrix.influences}


@state_matrix_router.get("/gradient")
async def get_gradient():
    """Get attractor field gradient."""
    matrix = get_state_matrix()
    return {"gradient": getattr(matrix, "gradient", {})}


@state_matrix_router.post("/navigate")
async def navigate(request: Dict[str, Any]):
    """Navigate along gradient."""
    matrix = get_state_matrix()
    # Placeholder for navigation logic
    return {"status": "navigated", "target": request}


@state_matrix_router.get("/temporal/trend")
async def get_temporal_trend(axis: str, key: str, window: int = 30) -> dict:
    """Get temporal trend for an axis key."""
    matrix = get_state_matrix()
    if hasattr(matrix, "temporal") and hasattr(matrix.temporal, "trend"):
        trend = matrix.temporal.trend(axis, key, window)
        return {"axis": axis, "key": key, "trend": trend}
    return {"axis": axis, "key": key, "trend": None, "note": "Temporal tracking not available"}


@state_matrix_router.get("/temporal/anomalies")
async def get_temporal_anomalies(axis: str, key: str, threshold: float = 2.0) -> dict:
    """Get temporal anomalies for an axis key."""
    matrix = get_state_matrix()
    if hasattr(matrix, "temporal") and hasattr(matrix.temporal, "anomalies"):
        anomalies = matrix.temporal.anomalies(axis, key, threshold)
        return {"axis": axis, "key": key, "anomalies": anomalies}
    return {"axis": axis, "key": key, "anomalies": [], "note": "Temporal tracking not available"}


@state_matrix_router.post("/port/register")
async def register_port(request: Dict[str, Any]) -> dict:
    """Register a port."""
    matrix = get_state_matrix()
    if hasattr(matrix, "register_port"):
        return matrix.register_port(request.get("name"), request.get("config", {}))
    logger.warning("register_port not implemented on StateMatrix4D")
    return {"status": "not_implemented", "note": "Port registration not available"}


@state_matrix_router.post("/port/unregister")
async def unregister_port(name: str) -> dict:
    """Unregister a port."""
    matrix = get_state_matrix()
    if hasattr(matrix, "unregister_port"):
        return matrix.unregister_port(name)
    logger.warning("unregister_port not implemented on StateMatrix4D")
    return {"status": "not_implemented"}


@state_matrix_router.get("/port/list")
async def list_ports() -> dict:
    """List registered ports."""
    matrix = get_state_matrix()
    if hasattr(matrix, "ports"):
        return {"ports": list(matrix.ports.keys())}
    return {"ports": []}


@state_matrix_router.post("/ripple")
async def apply_ripple(request: RippleRequest) -> dict:
    """Apply ripple effect across axes."""
    matrix = get_state_matrix()
    if hasattr(matrix, "apply_ripple"):
        matrix.apply_ripple(request.source_axis, request.source_value, request.target_axes, request.strength)
        return {"status": "applied"}
    logger.warning("apply_ripple not implemented on StateMatrix4D")
    return {"status": "not_implemented"}


@state_matrix_router.post("/allocation")
async def allocation_decide(request: AllocationRequest) -> dict:
    """Make allocation decision."""
    matrix = get_state_matrix()
    if hasattr(matrix, "allocation_decide"):
        decision = matrix.allocation_decide(request.candidates, request.dimension)
        return {"decision": decision}
    logger.warning("allocation_decide not implemented on StateMatrix4D")
    return {"status": "not_implemented"}


@state_matrix_router.get("/negativity")
async def get_negativity():
    """Get theta self-correction state."""
    matrix = get_state_matrix()
    theta = matrix.theta
    return {
        "novelty": theta.get("novelty", 0),
        "complexity": theta.get("complexity", 0),
        "ambiguity": theta.get("ambiguity", 0),
        "dimension_fit": theta.get("dimension_fit", 0),
        "creation_urge": theta.get("creation_urge", 0),
    }


@state_matrix_router.post("/save")
async def save_state(request: SaveStateRequest) -> dict:
    """Save state to file."""
    matrix = get_state_matrix()
    filepath = request.filepath or "state_matrix_save.json"
    try:
        if hasattr(matrix, "save_state"):
            matrix.save_state(filepath)
        else:
            # Fallback: serialize manually
            state = {
                "alpha": matrix.alpha,
                "beta": matrix.beta,
                "gamma": matrix.gamma,
                "delta": matrix.delta,
                "epsilon": matrix.epsilon,
                "theta": matrix.theta,
            }
            await asyncio.to_thread(_write_state_sync, filepath, state)
        return {"status": "saved", "filepath": filepath}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@state_matrix_router.post("/load")
async def load_state(request: LoadStateRequest) -> dict:
    """Load state from file."""
    matrix = get_state_matrix()
    filepath = request.filepath or "state_matrix_save.json"
    try:
        if hasattr(matrix, "load_state"):
            matrix.load_state(filepath)
        else:
            # Fallback: deserialize manually
            state = await asyncio.to_thread(_read_state_sync, filepath)
            matrix.alpha.update(state.get("alpha", {}))
            matrix.beta.update(state.get("beta", {}))
            matrix.gamma.update(state.get("gamma", {}))
            matrix.delta.update(state.get("delta", {}))
            matrix.epsilon.update(state.get("epsilon", {}))
            matrix.theta.update(state.get("theta", {}))
        return {"status": "loaded", "filepath": filepath}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))