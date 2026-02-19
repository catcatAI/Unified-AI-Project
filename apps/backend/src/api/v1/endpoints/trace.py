"""
Angela AI v6.0 - Causal Trace API
因果追踪 API

API endpoints for querying and validating causal traces.

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-19
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
import logging

from apps.backend.src.core.tracing import (
    get_tracer,
    ChainValidator,
    LayerType,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trace", tags=["Causal Tracing"])

validator = ChainValidator()


@router.get("/status")
async def get_trace_status() -> Dict[str, Any]:
    """
    Get tracing system status.
    获取追踪系统状态。
    """
    tracer = get_tracer()
    
    return {
        "enabled": tracer.is_enabled(),
        "chain_count": tracer.get_chain_count(),
        "active_traces": len(tracer._active_traces),
        "status": "operational",
    }


@router.get("/chains")
async def list_chains(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """
    List all stored causal chains.
    列出所有存储的因果链。
    
    Args:
        limit: Maximum number of chains to return
        offset: Number of chains to skip
    """
    tracer = get_tracer()
    all_chains = tracer.get_all_chains()
    
    total = len(all_chains)
    chains = all_chains[offset:offset + limit]
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "chains": [
            {
                "root_id": chain.root_id,
                "node_count": len(chain.nodes),
                "created_at": chain.created_at.isoformat(),
                "execution_time": chain.get_execution_time(),
            }
            for chain in chains
        ],
    }


@router.get("/chain/{trace_id}")
async def get_chain(trace_id: str) -> Dict[str, Any]:
    """
    Get complete causal chain for a trace ID.
    获取追踪ID的完整因果链。
    
    Args:
        trace_id: Any trace ID within the chain
    
    Returns:
        Complete causal chain with all nodes
    """
    tracer = get_tracer()
    chain = tracer.get_chain(trace_id)
    
    if chain is None:
        raise HTTPException(
            status_code=404,
            detail=f"Causal chain not found for trace ID: {trace_id}"
        )
    
    return chain.to_dict()


@router.get("/validate/{trace_id}")
async def validate_chain(trace_id: str) -> Dict[str, Any]:
    """
    Validate causal chain integrity.
    验证因果链完整性。
    
    Args:
        trace_id: Any trace ID within the chain
    
    Returns:
        Validation result with errors and warnings
    """
    tracer = get_tracer()
    chain = tracer.get_chain(trace_id)
    
    if chain is None:
        raise HTTPException(
            status_code=404,
            detail=f"Causal chain not found for trace ID: {trace_id}"
        )
    
    result = validator.validate_chain(chain)
    
    return {
        "valid": result.valid,
        "errors": result.errors,
        "warnings": result.warnings,
        "trace_id": trace_id,
        "root_id": chain.root_id,
    }


@router.get("/stats/{trace_id}")
async def get_chain_stats(trace_id: str) -> Dict[str, Any]:
    """
    Get statistics for a causal chain.
    获取因果链的统计信息。
    
    Args:
        trace_id: Any trace ID within the chain
    
    Returns:
        Chain statistics including layer distribution and timing
    """
    tracer = get_tracer()
    chain = tracer.get_chain(trace_id)
    
    if chain is None:
        raise HTTPException(
            status_code=404,
            detail=f"Causal chain not found for trace ID: {trace_id}"
        )
    
    stats = validator.get_chain_statistics(chain)
    
    return {
        "trace_id": trace_id,
        "statistics": stats,
    }


@router.get("/layer/{trace_id}/{layer}")
async def get_layer_nodes(trace_id: str, layer: str) -> Dict[str, Any]:
    """
    Get all nodes from a specific layer in a causal chain.
    获取因果链中特定层的所有节点。
    
    Args:
        trace_id: Any trace ID within the chain
        layer: Layer identifier (L1-L6)
    
    Returns:
        All nodes from the specified layer
    """
    tracer = get_tracer()
    chain = tracer.get_chain(trace_id)
    
    if chain is None:
        raise HTTPException(
            status_code=404,
            detail=f"Causal chain not found for trace ID: {trace_id}"
        )
    
    try:
        layer_type = LayerType.from_string(layer)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid layer: {layer}. Must be L1-L6."
        )
    
    nodes = chain.get_layer_nodes(layer_type)
    
    return {
        "trace_id": trace_id,
        "layer": layer,
        "node_count": len(nodes),
        "nodes": [node.to_dict() for node in nodes],
    }


@router.get("/path/{trace_id}/{node_id}")
async def get_path_to_root(trace_id: str, node_id: str) -> Dict[str, Any]:
    """
    Get the path from a specific node back to the root.
    获取从特定节点回溯到根节点的路径。
    
    Args:
        trace_id: Any trace ID within the chain
        node_id: Target node ID
    
    Returns:
        Path from node to root
    """
    tracer = get_tracer()
    chain = tracer.get_chain(trace_id)
    
    if chain is None:
        raise HTTPException(
            status_code=404,
            detail=f"Causal chain not found for trace ID: {trace_id}"
        )
    
    node = chain.get_node(node_id)
    if node is None:
        raise HTTPException(
            status_code=404,
            detail=f"Node {node_id} not found in chain"
        )
    
    path = chain.get_path_to_root(node_id)
    
    return {
        "trace_id": trace_id,
        "node_id": node_id,
        "path_length": len(path),
        "path": [node.to_dict() for node in path],
    }


@router.post("/enable")
async def enable_tracing() -> Dict[str, str]:
    """
    Enable causal tracing.
    启用因果追踪。
    """
    tracer = get_tracer()
    tracer.enable()
    
    return {"status": "enabled", "message": "Causal tracing enabled"}


@router.post("/disable")
async def disable_tracing() -> Dict[str, str]:
    """
    Disable causal tracing.
    禁用因果追踪。
    """
    tracer = get_tracer()
    tracer.disable()
    
    return {"status": "disabled", "message": "Causal tracing disabled"}


@router.delete("/chains")
async def clear_chains() -> Dict[str, str]:
    """
    Clear all stored causal chains.
    清除所有存储的因果链。
    
    Warning: This is a destructive operation.
    """
    tracer = get_tracer()
    tracer.clear_chains()
    
    return {"status": "cleared", "message": "All causal chains cleared"}
