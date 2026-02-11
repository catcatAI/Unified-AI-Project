#!/usr/bin/env python3
"""
AI运维系统API路由
提供AI运维功能的REST API接口
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from datetime import datetime

import asyncio

from ai.ops.intelligent_ops_manager import IntelligentOpsManager, get_intelligent_ops_manager

router = APIRouter(prefix="/ops", tags=["AI运维"])

# 依赖注入
async def get_ops_manager() -> IntelligentOpsManager:
    """获取智能运维管理器"""
    return await get_intelligent_ops_manager()

@router.get("/dashboard")
async def get_ops_dashboard(ops_manager: IntelligentOpsManager = Depends(get_ops_manager)):
    """获取运维仪表板数据"""
    try:
        dashboard_data = await ops_manager.get_ops_dashboard_data()
        return JSONResponse(content=dashboard_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取仪表板数据失败: {str(e)}")

@router.get("/insights")
async def get_insights(
    insight_type: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 50,
    ops_manager: IntelligentOpsManager = Depends(get_ops_manager)
):
    """获取运维洞察"""
    try:
        insights = await ops_manager.get_insights(
            insight_type=insight_type,
            severity=severity,
            limit=limit
        )
        return JSONResponse(content=[{
            "insight_id": insight.insight_id,
            "insight_type": insight.insight_type,
            "severity": insight.severity,
            "title": insight.title,
            "description": insight.description,
            "affected_components": insight.affected_components,
            "recommendations": insight.recommendations,
            "confidence": insight.confidence,
            "timestamp": insight.timestamp.isoformat() if hasattr(insight.timestamp, 'isoformat') else str(insight.timestamp),
            "auto_actionable": insight.auto_actionable
        } for insight in insights])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取洞察失败: {str(e)}")

@router.post("/insights/{insight_id}/action")
async def execute_manual_action(
    insight_id: str,
    action_data: Dict[str, Any],
    ops_manager: IntelligentOpsManager = Depends(get_ops_manager)
):
    """执行手动操作"""
    try:
        action_type = action_data.get("action_type")
        parameters = action_data.get("parameters", {})
        
        success = await ops_manager.execute_manual_action(
            insight_id, action_type, parameters
        )
        
        if success:
            return JSONResponse(content={"status": "success", "message": "操作执行成功"})
        else:
            return JSONResponse(content={"status": "error", "message": "操作执行失败"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行操作失败: {str(e)}")

@router.post("/metrics")
async def collect_system_metrics(
    metrics_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    ops_manager: IntelligentOpsManager = Depends(get_ops_manager)
):
    """收集系统指标"""
    try:
        component_id = metrics_data.get("component_id")
        component_type = metrics_data.get("component_type")
        metrics = metrics_data.get("metrics", {})
        
        # 异步收集指标
        background_tasks.add_task(
            ops_manager.collect_metrics,
            component_id, component_type, metrics
        )
        return {"status": "success", "message": "指标收集任务已提交"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提交指标收集任务失败: {str(e)}")
