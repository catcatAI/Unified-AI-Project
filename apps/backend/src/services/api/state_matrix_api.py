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
from typing import Any, Dict, List, Optional, cast

from core.engine.state_matrix import StateMatrix4D, get_shared_state_matrix
from core.utils import safe_error
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


def get_state_matrix() -> StateMatrix4D:
    """Get the shared state matrix instance (DLI writes, HTTP API reads)."""
    return get_shared_state_matrix()


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
def _sanitize_state_path(filepath: str) -> str:
    import os
    import re

    # Allow only safe characters, prevent traversal
    # Keep basename only if traversal detected
    if ".." in filepath or filepath.startswith("/") or ":" in filepath:
        filepath = os.path.basename(filepath)
    # Only allow alphanumeric, dash, underscore, dot, slash (for relative)
    filepath = re.sub(r"[^a-zA-Z0-9._\-/]", "_", filepath)
    # Force within data/state/ dir
    base = os.path.abspath("data/state")
    os.makedirs(base, exist_ok=True)
    abs_path = os.path.abspath(os.path.join(base, os.path.basename(filepath)))
    if os.path.commonpath([abs_path, base]) != base:
        raise ValueError(f"Invalid filepath: {filepath}")
    return abs_path


def _write_state_sync(filepath: str, state: dict) -> None:
    import json

    filepath = _sanitize_state_path(filepath)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(state, f)


def _read_state_sync(filepath: str) -> dict:
    import json

    filepath = _sanitize_state_path(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        return cast(dict, json.load(f))


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
    axis = axis_map[name]
    return {
        "name": name,
        "values": dict(axis.values or {}),
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
    influences = matrix.compute_influences()
    return {"status": "computed", "influences": influences}


@state_matrix_router.get("/gradient")
async def get_gradient():
    """Get attractor field gradient."""
    matrix = get_state_matrix()
    return {"gradient": getattr(matrix, "gradient", {})}


@state_matrix_router.post("/navigate")
async def navigate(request: Dict[str, Any]):
    """Navigate along gradient."""
    matrix = get_state_matrix()
    target_axis = request.get("target_axis")
    target_values = request.get("target_values", {})

    if not target_axis:
        raise HTTPException(status_code=400, detail="target_axis is required")

    axis_map = {
        "alpha": matrix.alpha,
        "beta": matrix.beta,
        "gamma": matrix.gamma,
        "delta": matrix.delta,
        "epsilon": matrix.epsilon,
        "theta": matrix.theta,
    }
    if target_axis not in axis_map:
        raise HTTPException(status_code=404, detail=f"Axis '{target_axis}' not found")

    axis = axis_map[target_axis]
    if hasattr(axis, "update") and target_values:
        axis.update(**target_values)
        logger.info("Navigated axis '%s' to values: %s", target_axis, target_values)

    axis_values = getattr(axis, "values", None)
    return {
        "status": "navigated",
        "target_axis": target_axis,
        "values": dict(axis_values) if axis_values else target_values,
        "timestamp": datetime.datetime.now().isoformat(),
    }


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
    """Register a port on an axis.

    The port registry lives on the matrix (``matrix.ports``), so the
    endpoint acts on the real registry instead of answering
    ``not_implemented`` (audit 2026-10-20).
    """
    matrix = get_state_matrix()
    registry = getattr(matrix, "ports", None)
    if registry is None:
        raise HTTPException(status_code=501, detail="Port registry not available")
    axis = str(request.get("axis") or request.get("name") or "").strip()
    if not axis:
        raise HTTPException(status_code=400, detail="axis is required")
    config = request.get("config") or {}
    if not isinstance(config, dict):
        raise HTTPException(status_code=400, detail="config must be an object")
    registry.register_port(axis, config)
    port = registry.get_port(axis) or {}
    return {"status": "registered", "axis": axis, "port": port}


@state_matrix_router.post("/port/unregister")
async def unregister_port(name: str) -> dict:
    """Remove the port of an axis (and any binding to it)."""
    matrix = get_state_matrix()
    registry = getattr(matrix, "ports", None)
    if registry is None:
        raise HTTPException(status_code=501, detail="Port registry not available")
    removed = registry.unregister_port(name)
    return {"status": "unregistered" if removed else "not_found", "axis": name}


@state_matrix_router.get("/port/list")
async def list_ports() -> dict:
    """List the registered ports (optionally only the bound ones)."""
    matrix = get_state_matrix()
    registry = getattr(matrix, "ports", None)
    if registry is None:
        raise HTTPException(status_code=501, detail="Port registry not available")
    return {"ports": registry.list_ports()}


def _ripple_payload(request: RippleRequest) -> Dict[str, Any]:
    """Map the API request onto the ripple engine's flat delta schema.

    The engine (``ai.memory.domain_ripple``) speaks in per-axis delta keys
    (``beta_focus``, ``alpha_arousal``, …), while the endpoint speaks in
    axes. The mapping keeps the two views consistent instead of silently
    dropping the request.
    """
    from ai.memory.domain_ripple import _RIPPLE_KEY_MAP

    payload: Dict[str, Any] = {}
    for target in request.target_axes:
        if target == "epsilon":
            payload["epsilon_delta"] = request.source_value
            continue
        for delta_key, (axis_name, _key) in _RIPPLE_KEY_MAP.items():
            if axis_name == target:
                payload[delta_key] = request.source_value
    return payload


@state_matrix_router.post("/ripple")
async def apply_ripple(request: RippleRequest) -> dict:
    """Apply ripple effect across axes.

    The ripple engine (``ai.memory.domain_ripple``) is the real
    implementation; the endpoint drives it against the live matrix.
    """
    matrix = get_state_matrix()
    payload = _ripple_payload(request)
    if not payload:
        raise HTTPException(
            status_code=400,
            detail=f"no rippleable key for target axes {request.target_axes}",
        )
    try:
        from ai.memory.domain_ripple import apply_ripple_to_state

        apply_ripple_to_state(matrix, payload, scale=request.strength)
    except Exception as exc:
        logger.error("Ripple application failed: %s", safe_error(exc))
        raise HTTPException(status_code=500, detail="Ripple application failed") from exc
    return {"status": "applied", "ripple": payload, "strength": request.strength}


@state_matrix_router.post("/allocation")
async def allocation_decide(request: AllocationRequest) -> dict:
    """Make an allocation decision.

    The matrix allocates through θ (``meta_allocate``); the candidates are
    scored against the allocation policy and the decision is reported with
    the axis it targets.
    """
    matrix = get_state_matrix()
    if not request.candidates:
        raise HTTPException(status_code=400, detail="candidates must not be empty")
    vector: List[float] = []
    for candidate in request.candidates:
        for value in candidate.values():
            vector.append(float(value))
    if not vector:
        raise HTTPException(status_code=400, detail="candidates carry no values")
    try:
        decision = matrix.meta_allocate(vector, request.dimension)
    except Exception as exc:
        logger.error("Allocation decision failed: %s", safe_error(exc))
        raise HTTPException(status_code=500, detail="Allocation decision failed") from exc
    return {
        "decision": {
            "action": getattr(decision, "action", None),
            "target": getattr(decision, "target", None),
            "confidence": getattr(decision, "confidence", None),
            "reasoning": getattr(decision, "reasoning", ""),
        }
    }


@state_matrix_router.get("/negativity")
async def get_negativity():
    """Get theta self-correction state."""
    matrix = get_state_matrix()
    theta = matrix.theta
    values = dict(theta.values or {})
    return {
        "novelty": values.get("novelty", 0),
        "complexity": values.get("complexity", 0),
        "ambiguity": values.get("ambiguity", 0),
        "dimension_fit": values.get("dimension_fit", 0),
        "creation_urge": values.get("creation_urge", 0),
    }


@state_matrix_router.post("/save")
async def save_state(request: SaveStateRequest) -> dict:
    """Save state to file."""
    matrix = get_state_matrix()
    filepath = _sanitize_state_path(request.filepath or "state_matrix_save.json")
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
        raise HTTPException(status_code=500, detail=safe_error(e))


@state_matrix_router.post("/load")
async def load_state(request: LoadStateRequest) -> dict:
    """Load state from file."""
    matrix = get_state_matrix()
    filepath = _sanitize_state_path(request.filepath or "state_matrix_save.json")
    try:
        if hasattr(matrix, "load_state"):
            matrix.load_state(filepath)
        else:
            # Fallback: deserialize manually
            state = await asyncio.to_thread(_read_state_sync, filepath)
            matrix.alpha.update(**state.get("alpha", {}))
            matrix.beta.update(**state.get("beta", {}))
            matrix.gamma.update(**state.get("gamma", {}))
            matrix.delta.update(**state.get("delta", {}))
            matrix.epsilon.update(**state.get("epsilon", {}))
            matrix.theta.update(**state.get("theta", {}))
        return {"status": "loaded", "filepath": filepath}
    except Exception as e:
        raise HTTPException(status_code=500, detail=safe_error(e))
