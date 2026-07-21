#!/usr/bin/env python3
"""
Angela AI v6.0 - Causal Trace API
因果追踪 API

API endpoints for querying and validating causal traces, backed by
core/tracing/ (CausalTracer, CausalChain, ChainValidator).

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-19
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trace", tags=["Trace"])

_TRACER = None


def _get_tracer():
    """Get the global CausalTracer singleton from core/tracing/."""
    global _TRACER
    if _TRACER is None:
        try:
            from core.tracing.causal_tracer import get_tracer

            _TRACER = get_tracer()
        except Exception as e:
            logger.warning("CausalTracer not available: %s", e)
    return _TRACER


@router.get("/status")
async def get_trace_status() -> dict:
    """Get trace system status."""
    tracer = _get_tracer()
    if tracer is None:
        return {"status": "unavailable", "service": "trace", "error": "CausalTracer not loaded"}
    return {
        "status": "enabled" if tracer.is_enabled() else "disabled",
        "service": "trace",
        "chain_count": tracer.get_chain_count(),
    }


@router.get("/chain/list")
async def list_chains() -> dict:
    """List all causal chains with summary info."""
    tracer = _get_tracer()
    if tracer is None:
        raise HTTPException(status_code=503, detail="CausalTracer not available")
    chains = tracer.get_all_chains()
    summaries = []
    for c in chains:
        summaries.append(
            {
                "root_id": c.root_id,
                "node_count": len(c.nodes),
                "execution_time": c.get_execution_time(),
                "layers": sorted(set(str(n.layer) for n in c.nodes)),
                "created_at": c.created_at.isoformat(),
            }
        )
    return {"chains": summaries, "total": len(summaries)}


@router.get("/chain/{trace_id}")
async def get_chain(trace_id: str) -> dict:
    """Get a complete causal chain by trace ID."""
    tracer = _get_tracer()
    if tracer is None:
        raise HTTPException(status_code=503, detail="CausalTracer not available")
    chain = tracer.get_chain(trace_id)
    if chain is None:
        raise HTTPException(status_code=404, detail=f"Chain not found: {trace_id}")
    return {"chain": chain.to_dict()}


@router.post("/enable")
async def enable_tracing() -> dict:
    """Enable causal tracing."""
    tracer = _get_tracer()
    if tracer is None:
        raise HTTPException(status_code=503, detail="CausalTracer not available")
    tracer.enable()
    return {"status": "enabled"}


@router.post("/disable")
async def disable_tracing() -> dict:
    """Disable causal tracing."""
    tracer = _get_tracer()
    if tracer is None:
        raise HTTPException(status_code=503, detail="CausalTracer not available")
    tracer.disable()
    return {"status": "disabled"}


@router.post("/clear")
async def clear_chains() -> dict:
    """Clear all stored causal chains."""
    tracer = _get_tracer()
    if tracer is None:
        raise HTTPException(status_code=503, detail="CausalTracer not available")
    count = tracer.get_chain_count()
    tracer.clear_chains()
    return {"status": "cleared", "chains_removed": count}


@router.post("/validate/{trace_id}")
async def validate_chain(trace_id: str) -> dict:
    """Validate a causal chain's integrity using ChainValidator."""
    tracer = _get_tracer()
    if tracer is None:
        raise HTTPException(status_code=503, detail="CausalTracer not available")
    chain = tracer.get_chain(trace_id)
    if chain is None:
        raise HTTPException(status_code=404, detail=f"Chain not found: {trace_id}")
    try:
        from core.tracing.chain_validator import ChainValidator

        validator = ChainValidator()
        result = validator.validate_chain(chain)
        return {
            "valid": result.valid,
            "errors": result.errors,
            "warnings": result.warnings,
            "stats": result.stats,
        }
    except Exception as e:
        logger.error("Chain validation failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
