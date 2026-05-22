"""
State Matrix FastAPI Router
==========================

為 StateMatrixAdapter 提供 HTTP API 接口。

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
    from api.router import router as state_matrix_router
    app.include_router(state_matrix_router, prefix="/api/v1")

Author: Angela AI v6.2.1
"""

from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger("angela_state_matrix_api")


state_matrix_router = APIRouter(prefix="/state", tags=["state_matrix"])


class AxisUpdateRequest(BaseModel):
    values: Dict[str, float]


class NavigateRequest(BaseModel):
    target_tags: Optional[List[str]] = None
    max_steps: int = 5
    dt: float = 0.15
    threshold: float = 0.05


class PortRegisterRequest(BaseModel):
    name: str
    direction: str = Field(pattern="^(in|out|io)$")
    semantic_vector: List[float]
    priority: float = 0.5
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class PortUnregisterRequest(BaseModel):
    name: str


class RippleRequest(BaseModel):
    math_op: str
    operand: float
    cascade_targets: Optional[List[str]] = None


class AllocationRequest(BaseModel):
    vector: List[float]
    label: str = ""


class ThetaTriggerRequest(BaseModel):
    strength: float = 0.1


class SaveStateRequest(BaseModel):
    label: Optional[str] = None
    force: bool = False


class LoadStateRequest(BaseModel):
    checkpoint_id: Optional[str] = None
    tag: Optional[str] = None


_sm_instance: Optional[Any] = None


def get_state_matrix() -> Any:
    global _sm_instance
    if _sm_instance is None:
        from core.autonomous.state_matrix_adapter import StateMatrixAdapter
        _sm_instance = StateMatrixAdapter()
        logger.info("[StateMatrixAPI] StateMatrixAdapter initialized")
        from core.interfaces.service_registry import get_registry
        get_registry().register("state_matrix_persistence", _sm_instance)
    return _sm_instance


@state_matrix_router.get("/summary")
def get_summary():
    """完整狀態報告"""
    sm = get_state_matrix()
    return sm.full_report()


@state_matrix_router.get("/axis/{axis_name}")
def get_axis(axis_name: str):
    """獲取單個軸的 values"""
    sm = get_state_matrix()
    if axis_name not in sm._sm.dimensions:
        raise HTTPException(status_code=404, detail=f"Axis '{axis_name}' not found")
    return {
        "name": axis_name,
        "values": sm._sm.dimensions[axis_name].values.copy(),
        "average": sm._sm.dimensions[axis_name].get_average(),
        "weight": sm._sm.dimensions[axis_name].weight,
    }


@state_matrix_router.post("/axis/{axis_name}/update")
def update_axis(axis_name: str, req: AxisUpdateRequest):
    """更新軸值"""
    sm = get_state_matrix()
    if axis_name not in sm._sm.dimensions:
        raise HTTPException(status_code=404, detail=f"Axis '{axis_name}' not found")

    updater = getattr(sm, f"update_{axis_name}", None)
    if not updater:
        raise HTTPException(status_code=500, detail=f"No update method for '{axis_name}'")

    updater(**req.values)
    return {"status": "updated", "axis": axis_name, "values": req.values}


@state_matrix_router.get("/gradient")
def get_gradient():
    """獲取吸引子場梯度"""
    sm = get_state_matrix()
    result = sm.compute_gradient()
    if result is None:
        raise HTTPException(status_code=500, detail="GradientField not available")
    return result


@state_matrix_router.post("/navigate")
def navigate(req: NavigateRequest):
    """沿梯度導航到吸引子"""
    sm = get_state_matrix()
    result = sm.navigate_to_attractor(
        target_tags=req.target_tags,
        max_steps=req.max_steps,
        dt=req.dt,
        threshold=req.threshold,
    )
    if result is None:
        raise HTTPException(status_code=500, detail="GradientField not available")
    return result


@state_matrix_router.get("/temporal/trend")
def temporal_trend(
    axis: str = Query(...),
    field: str = Query(...),
    window: int = Query(default=50),
):
    """時間趨勢查詢"""
    sm = get_state_matrix()
    result = sm.temporal_trend(axis, field, window)
    return {"axis": axis, "field": field, "window": window, "result": str(result)}


@state_matrix_router.get("/temporal/anomalies")
def temporal_anomalies(
    axis: str = Query(...),
    field: str = Query(...),
    threshold: float = Query(default=0.3),
):
    """異常檢測"""
    sm = get_state_matrix()
    result = sm.temporal_anomalies(axis, field, threshold)
    return {"axis": axis, "field": field, "threshold": threshold, "anomalies": result}


@state_matrix_router.post("/port/register")
def register_port(req: PortRegisterRequest):
    """註冊端口"""
    sm = get_state_matrix()
    port = sm.register_port(
        name=req.name,
        direction=req.direction,
        semantic_vector=req.semantic_vector,
        priority=req.priority,
        tags=req.tags,
        metadata=req.metadata,
    )
    return {"status": "registered", "port": port.to_dict() if hasattr(port, "to_dict") else {"name": port.name}}


@state_matrix_router.post("/port/unregister")
def unregister_port(req: PortUnregisterRequest):
    """註銷端口"""
    sm = get_state_matrix()
    result = sm.unregister_port(req.name)
    return {"status": "unregistered" if result else "not_found", "name": req.name}


@state_matrix_router.get("/port/list")
def list_ports(
    direction: Optional[str] = Query(default=None),
    bound: Optional[bool] = Query(default=None),
):
    """列舉端口"""
    sm = get_state_matrix()
    ports = sm.list_ports(direction=direction, bound=bound)
    return {"total": len(ports), "ports": ports}


@state_matrix_router.post("/ripple")
def apply_ripple(req: RippleRequest):
    """應用漣漪"""
    sm = get_state_matrix()
    from core.ripple.node import MathOp
    op_map = {"MUL": MathOp.MUL, "ADD": MathOp.ADD, "SUB": MathOp.SUB, "DIV": MathOp.DIV}
    math_op = op_map.get(req.math_op.upper(), MathOp.MUL)
    nodes = sm.apply_ripple(math_op, req.operand, cascade_targets=req.cascade_targets)
    return {
        "status": "applied",
        "math_op": req.math_op,
        "operand": req.operand,
        "cascade_count": len(nodes),
    }


@state_matrix_router.post("/allocation")
def allocation_decide(req: AllocationRequest):
    """分配決策"""
    sm = get_state_matrix()
    decision = sm.allocation_decide(req.vector, req.label)
    return {
        "action": decision.action.value if hasattr(decision.action, "value") else str(decision.action),
        "target": decision.target,
        "confidence": decision.confidence,
        "reasoning": decision.reasoning,
    }


@state_matrix_router.post("/theta/trigger")
def theta_trigger(req: ThetaTriggerRequest):
    """觸發 θ 軸負值"""
    sm = get_state_matrix()
    sm.trigger_negativity(req.strength)
    report = sm.get_negativity_report()
    return {"status": "triggered", "report": report}


@state_matrix_router.get("/theta/detect")
def theta_detect():
    """檢測錯配點位"""
    sm = get_state_matrix()
    sm.trigger_negativity(0.5)
    misallocated = sm.detect_misallocated_points()
    return {"misallocated_count": len(misallocated), "points": misallocated}


@state_matrix_router.post("/theta/correct")
def theta_correct(point_id: str = Query(...), target_axis: Optional[str] = Query(default=None)):
    """校正錯配點位"""
    sm = get_state_matrix()
    result = sm.correct_misallocation(point_id, target_axis=target_axis)
    return result


@state_matrix_router.get("/negativity/report")
def negativity_report():
    """θ 自糾狀態報告"""
    sm = get_state_matrix()
    return sm.get_negativity_report()


@state_matrix_router.get("/influence")
def influence_compute(
    source: str = Query(...),
    target: str = Query(...),
):
    """軸間影響計算"""
    sm = get_state_matrix()
    result = sm.influence_compute(source, target)
    return {"source": source, "target": target, "influence": result}


@state_matrix_router.post("/save")
async def save_state(req: SaveStateRequest):
    """保存狀態快照到 Redis/JSON（持久化層）"""
    sm = get_state_matrix()
    await sm.init_persistence()
    result = await sm.save_checkpoint(label=req.label, force=req.force)
    return result


@state_matrix_router.post("/load")
async def load_state(req: LoadStateRequest):
    """從 Redis/JSON 加載狀態快照"""
    sm = get_state_matrix()
    await sm.init_persistence()
    result = await sm.load_checkpoint(checkpoint_id=req.checkpoint_id, tag=req.tag)
    return result


@state_matrix_router.get("/checkpoint/list")
async def list_checkpoints(limit: int = Query(default=10)):
    """列舉最近的快照"""
    sm = get_state_matrix()
    await sm.init_persistence()
    return await sm.list_checkpoints(limit=limit)


@state_matrix_router.delete("/checkpoint/{checkpoint_id}")
async def delete_checkpoint(checkpoint_id: str):
    """刪除指定快照"""
    sm = get_state_matrix()
    await sm.init_persistence()
    success = await sm.delete_checkpoint(checkpoint_id)
    return {"status": "deleted" if success else "failed"}


@state_matrix_router.get("/checkpoint/stats")
async def checkpoint_stats():
    """獲取持久化層狀態"""
    sm = get_state_matrix()
    await sm.init_persistence()
    return sm.get_persistence_stats()


@state_matrix_router.get("/code-inspect/report")
def code_inspect_report():
    """代碼檢查狀態報告"""
    sm = get_state_matrix()
    return sm.code_inspect_report()


@state_matrix_router.get("/attractor/list")
def list_attractors():
    """列舉所有吸引子"""
    sm = get_state_matrix()
    gf = sm.gradient_field
    if not gf:
        raise HTTPException(status_code=500, detail="GradientField not available")
    return {
        "count": len(gf.attractors),
        "attractors": [
            {
                "description": a.description,
                "tone": a.tone.value if hasattr(a.tone, "value") else str(a.tone),
                "mass": a.mass,
                "radius": a.radius,
                "tags": a.tags,
            }
            for a in gf.attractors
        ],
    }


@state_matrix_router.post("/attractor/add")
def add_attractor(
    coord: List[float],
    behavior: str,
    tone: str = "warm",
    mass: float = 1.0,
    radius: float = 0.4,
    tags: Optional[List[str]] = None,
):
    """添加自定義吸引子"""
    sm = get_state_matrix()
    result = sm.add_attractor(
        coord=tuple(coord[:5]),
        behavior=behavior,
        tone=tone,
        mass=mass,
        radius=radius,
        tags=tags,
    )
    return {"status": "added" if result else "failed"}


class MathVerifyRequest(BaseModel):
    message: str
    user_name: str = "朋友"


class CodeInspectRequest(BaseModel):
    code: str
    file_path: str = "analysis"


@state_matrix_router.post("/math/verify")
async def math_verify(req: MathVerifyRequest):
    """數學驗證 + 狀態反饋"""
    sm = get_state_matrix()
    from services.math_verifier import MathVerifier

    verifier = MathVerifier(state_matrix=sm._sm)
    result = await verifier.verify(req.message, req.user_name)

    feedback = sm.integrate_verification_result(result)

    return {
        "verification": {
            "expression": result.expression,
            "llm_answer": result.llm_answer,
            "engine_answer": result.engine_answer,
            "matches": result.matches,
            "discrepancy": result.discrepancy,
            "needs_clarification": result.needs_clarification,
            "response_text": result.response_text,
        },
        "state_feedback": feedback,
    }


@state_matrix_router.post("/code/inspect")
def code_inspect(req: CodeInspectRequest):
    """代碼檢查 + 軸狀態更新"""
    sm = get_state_matrix()
    from ai.code_inspection.code_inspector import CodeInspector

    inspector = CodeInspector()
    result = inspector.inspect_content(req.code, req.file_path)

    feedback = sm.integrate_code_inspect(result)
    return {"inspection": result, "state_feedback": feedback}


class ThetaAnalysisRequest(BaseModel):
    context: str = ""


@state_matrix_router.post("/theta/analyze")
async def theta_analyze(req: ThetaAnalysisRequest):
    """θ 觸發的 LLM 分析（當 doubt/negativity 高時）"""
    sm = get_state_matrix()
    result = await sm.ask_theta_for_analysis(req.context)
    return result


# === η (Eta) Axis API ===

class EtaUpdateRequest(BaseModel):
    active_modules: Optional[List[str]] = None
    success_rate: Optional[float] = None
    structural_drift: Optional[float] = None


class EtaInvokeRequest(BaseModel):
    inputs: Dict[str, Any] = Field(default_factory=dict)
    count: Optional[int] = None


class EtaRegisterModuleRequest(BaseModel):
    name: str
    module_type: str
    sub_type: str
    parameters: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class EtaCycleRequest(BaseModel):
    context: Optional[Dict[str, Any]] = None


@state_matrix_router.get("/eta/report")
def eta_report():
    """η 軸完整報告"""
    sm = get_state_matrix()
    return sm.get_eta_report()


@state_matrix_router.post("/eta/update")
def eta_update(req: EtaUpdateRequest):
    """更新 η 軸字段"""
    sm = get_state_matrix()
    sm.update_eta(
        active_modules=req.active_modules,
        success_rate=req.success_rate,
        structural_drift=req.structural_drift,
    )
    return {"status": "updated", "eta_report": sm.get_eta_report()}


@state_matrix_router.post("/eta/invoke")
def eta_invoke(req: EtaInvokeRequest):
    """調用 η 模組"""
    sm = get_state_matrix()
    results = sm.invoke_eta_modules(req.inputs, req.count)
    return {
        "results": [(name, r) for name, r in results],
        "execution_count": sm._eta.execution_count,
    }


@state_matrix_router.post("/eta/register-module")
def eta_register_module(req: EtaRegisterModuleRequest):
    """註冊新的 η 模組"""
    sm = get_state_matrix()
    success = sm.register_eta_module(
        name=req.name,
        module_type=req.module_type,
        sub_type=req.sub_type,
        parameters=req.parameters,
        tags=req.tags,
    )
    return {"status": "registered" if success else "failed", "eta_report": sm.get_eta_report()}


@state_matrix_router.get("/eta/signals")
def eta_signals():
    """從 θ 提取 η 觸發信號"""
    sm = get_state_matrix()
    return sm.eta_signals_from_theta()


@state_matrix_router.post("/eta/apply")
def eta_apply():
    """應用 θ 信號到 η"""
    sm = get_state_matrix()
    return sm.apply_theta_to_eta()


@state_matrix_router.post("/eta/cycle")
def eta_cycle(req: EtaCycleRequest):
    """執行完整 θ → η → θ 迴路"""
    sm = get_state_matrix()
    return sm.theta_to_eta_cycle(req.context)


@state_matrix_router.post("/eta/execute-loop")
def eta_execute_loop(input_data: Optional[Dict[str, Any]] = None):
    """執行 θ-η 主迴路"""
    sm = get_state_matrix()
    return sm.execute_theta_eta_loop(input_data)


# === Module API ===

@state_matrix_router.get("/module/list")
def list_modules():
    """列舉所有 η 模組"""
    sm = get_state_matrix()
    modules = []
    for name, config in sm._eta.module_registry.items():
        modules.append({
            "name": name,
            "type": config.module_type.name,
            "sub_type": config.sub_type.name if hasattr(config.sub_type, 'name') else str(config.sub_type),
            "parameters": config.parameters,
            "tags": config.tags,
            "version": config.version,
            "adjusted_count": config.adjusted_count,
            "active": name in sm._eta.active_modules,
        })
    return {"modules": modules, "total": len(modules), "active_count": len(sm._eta.active_modules)}


@state_matrix_router.post("/module/execute")
def module_execute(name: str = Query(...), inputs: str = "{}"):
    """執行指定模組"""
    sm = get_state_matrix()
    import json
    try:
        parsed_inputs = json.loads(inputs)
    except Exception:
        parsed_inputs = {}
    result = sm._eta.execute(name, parsed_inputs)
    return {"module": name, "result": result, "execution_count": sm._eta.execution_count}


@state_matrix_router.post("/module/adjust")
def module_adjust(
    name: str = Query(...),
    parameter: str = Query(...),
    delta: float = Query(...),
):
    """調整模組參數"""
    sm = get_state_matrix()
    sm._eta.adjust_parameter(name, parameter, delta)
    return {"status": "adjusted", "module": name, "parameter": parameter, "delta": delta}


@state_matrix_router.get("/module/active")
def list_active_modules():
    """列舉活躍模組"""
    sm = get_state_matrix()
    return {
        "active_modules": sm._eta.active_modules,
        "count": len(sm._eta.active_modules),
    }


@state_matrix_router.post("/module/activate")
def activate_module(name: str = Query(...)):
    """激活模組"""
    sm = get_state_matrix()
    success = sm._eta.activate_module(name)
    return {"status": "activated" if success else "not_found", "name": name}


@state_matrix_router.post("/module/deactivate")
def deactivate_module(name: str = Query(...)):
    """停用模組"""
    sm = get_state_matrix()
    success = sm._eta.deactivate_module(name)
    return {"status": "deactivated" if success else "not_found", "name": name}


@state_matrix_router.get("/health")
def health_check():
    """健康檢查"""
    sm = get_state_matrix()
    return {
        "status": "ok",
        "update_count": sm._sm.update_count,
        "temporal_size": sm._temporal.size(),
        "port_count": sm._port_registry.size() if hasattr(sm, "_port_registry") else 0,
    }