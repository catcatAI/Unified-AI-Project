# =============================================================================
# ANGELA-MATRIX: [L3-L5] [βδεθζη] [A] [L3+]
# =============================================================================
#
# 职责: Angela Review Engine API 路由
# 维度: 认知(β) 精神(δ) 環境(ε) 元認知(θ) 連通(ζ) 執行(η)
# 安全: 使用 Key A (后端控制)
# 成熟度: L3+ 等级才能理解审查逻辑
#
# 端点:
#   GET /api/v1/review/            — 完整审查报告
#   GET /api/v1/review/{dimension} — 单维度审查
#   GET /api/v1/review/score       — 综合评分
#
# =============================================================================

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(tags=["review"])

_REVIEW_ENGINE = None


def _get_engine():
    global _REVIEW_ENGINE
    if _REVIEW_ENGINE is None:
        try:
            from ai.meta.angela_review_engine import AngelaReviewEngine

            _REVIEW_ENGINE = AngelaReviewEngine()
        except Exception as e:
            logger.warning("AngelaReviewEngine not available: %s", e)
    return _REVIEW_ENGINE


def set_review_engine(engine) -> None:
    global _REVIEW_ENGINE
    _REVIEW_ENGINE = engine


@router.get("/review/")
async def get_full_review():
    """执行完整多维度项目审查。"""
    engine = _get_engine()
    if engine is None:
        raise HTTPException(status_code=503, detail="Review engine not available")
    reports = engine.run_full_review()
    return {
        "success": True,
        "reports": {k: v.to_dict() for k, v in reports.items()},
        "composite_score": engine.get_composite_score(reports),
    }


@router.get("/review/{dimension}")
async def get_dimension_review(dimension: str):
    """执行指定维度的审查。

    维度: design, code, markdown, consistency, training
    """
    engine = _get_engine()
    if engine is None:
        raise HTTPException(status_code=503, detail="Review engine not available")
    try:
        report = engine.run_review(dimension)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "success": True,
        "report": report.to_dict(),
    }


@router.get("/review/score")
async def get_composite_score():
    """获取综合评分（所有维度的加权平均）。"""
    engine = _get_engine()
    if engine is None:
        raise HTTPException(status_code=503, detail="Review engine not available")
    reports = engine.run_full_review()
    return {
        "success": True,
        "composite_score": engine.get_composite_score(reports),
        "dimensions": {k: v.score for k, v in reports.items()},
    }


@router.get("/review/summary")
async def get_review_summary():
    """获取可读的审查摘要文本。"""
    engine = _get_engine()
    if engine is None:
        raise HTTPException(status_code=503, detail="Review engine not available")
    reports = engine.run_full_review()
    return {
        "success": True,
        "summary": engine.generate_summary(reports),
        "composite_score": engine.get_composite_score(reports),
    }


@router.post("/review/code")
async def review_specific_files(files: list[str]):
    """审查指定的代码文件。"""
    engine = _get_engine()
    if engine is None:
        raise HTTPException(status_code=503, detail="Review engine not available")
    from ai.meta.angela_review_engine import CodeReviewer
    from pathlib import Path

    src_root = Path(__file__).resolve().parent.parent.parent
    report = CodeReviewer(src_root).review(target_files=files)
    return {
        "success": True,
        "report": report.to_dict(),
    }
