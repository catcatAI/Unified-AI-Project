"""
Angela AI v6.0 - Causal Tracer
因果追踪器

Manages the creation and storage of causal traces across Angela's execution flow.

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-19
"""

from __future__ import annotations
from typing import Dict, Optional, Any, List
from datetime import datetime
import asyncio
import logging
from contextvars import ContextVar

from .causal_chain import CausalNode, CausalChain, LayerType

logger = logging.getLogger(__name__)

current_trace_id: ContextVar[Optional[str]] = ContextVar("current_trace_id", default=None)


class CausalTracer:
    """
    Singleton tracer for managing causal chains.
    单例追踪器，用于管理因果链。
    """
    
    _instance: Optional[CausalTracer] = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._chains: Dict[str, CausalChain] = {}
        self._active_traces: Dict[str, CausalNode] = {}
        self._max_chains = 1000
        self._enable_tracing = True
        self._initialized = True
        
        logger.info("CausalTracer initialized")
    
    def enable(self) -> None:
        """Enable tracing"""
        self._enable_tracing = True
        logger.info("Causal tracing enabled")
    
    def disable(self) -> None:
        """Disable tracing"""
        self._enable_tracing = False
        logger.info("Causal tracing disabled")
    
    def is_enabled(self) -> bool:
        """Check if tracing is enabled"""
        return self._enable_tracing
    
    def start(
        self,
        layer: str | LayerType,
        module: str,
        action: str,
        data: Optional[Dict[str, Any]] = None,
        parent_id: Optional[str] = None,
    ) -> str:
        """
        Start a new trace point.
        开始一个新的追踪点。
        
        Args:
            layer: Layer identifier (L1-L6)
            module: Module name (e.g., "endocrine_system")
            action: Action name (e.g., "hormone_update")
            data: Optional data to record
            parent_id: Optional parent trace ID for linking
        
        Returns:
            Trace ID for this operation
        """
        if not self._enable_tracing:
            return ""
        
        try:
            if isinstance(layer, str):
                layer = LayerType.from_string(layer)
            
            if parent_id is None:
                parent_id = current_trace_id.get()
            
            node = CausalNode(
                parent_id=parent_id,
                layer=layer,
                module=module,
                action=action,
                data=data or {},
                timestamp=datetime.now(),
            )
            
            self._active_traces[node.id] = node
            
            if parent_id is None:
                chain = CausalChain(root_id=node.id)
                chain.add_node(node)
                self._chains[node.id] = chain
            else:
                root_id = self._find_root_id(parent_id)
                if root_id and root_id in self._chains:
                    self._chains[root_id].add_node(node)
            
            self._cleanup_old_chains()
            
            self.set_current_trace(node.id)
            
            return node.id
            
        except Exception as e:
            logger.error(f"Error starting trace: {e}", exc_info=True)
            return ""
    
    def record(self, trace_id: str, key: str, value: Any) -> None:
        """
        Record additional data for a trace point.
        为追踪点记录额外数据。
        
        Args:
            trace_id: Trace ID returned from start()
            key: Data key
            value: Data value
        """
        if not self._enable_tracing or not trace_id:
            return
        
        try:
            if trace_id in self._active_traces:
                self._active_traces[trace_id].data[key] = value
        except Exception as e:
            logger.error(f"Error recording trace data: {e}")
    
    def finish(self, trace_id: str, result: Optional[Any] = None) -> None:
        """
        Finish a trace point.
        结束一个追踪点。
        
        Args:
            trace_id: Trace ID returned from start()
            result: Optional result value to record
        """
        if not self._enable_tracing or not trace_id:
            return
        
        try:
            if trace_id in self._active_traces:
                node = self._active_traces[trace_id]
                if result is not None:
                    node.data["result"] = result
                node.data["finished_at"] = datetime.now().isoformat()
                
                parent_id = node.parent_id
                del self._active_traces[trace_id]
                
                if parent_id:
                    self.set_current_trace(parent_id)
                else:
                    self.set_current_trace(None)
        except Exception as e:
            logger.error(f"Error finishing trace: {e}")
    
    def get_chain(self, trace_id: str) -> Optional[CausalChain]:
        """
        Get the complete causal chain for a trace ID.
        获取追踪ID的完整因果链。
        
        Args:
            trace_id: Any trace ID in the chain
        
        Returns:
            Complete causal chain or None if not found
        """
        try:
            root_id = self._find_root_id(trace_id)
            if root_id:
                return self._chains.get(root_id)
            return self._chains.get(trace_id)
        except Exception as e:
            logger.error(f"Error getting chain: {e}")
            return None
    
    def get_all_chains(self) -> List[CausalChain]:
        """Get all stored causal chains"""
        return list(self._chains.values())
    
    def get_chain_count(self) -> int:
        """Get the number of stored chains"""
        return len(self._chains)
    
    def clear_chains(self) -> None:
        """Clear all stored chains (for testing)"""
        self._chains.clear()
        self._active_traces.clear()
        logger.info("All causal chains cleared")
    
    def _find_root_id(self, trace_id: str) -> Optional[str]:
        """Find the root ID for a given trace ID"""
        for root_id, chain in self._chains.items():
            if chain.get_node(trace_id) is not None:
                return root_id
        
        if trace_id in self._active_traces:
            node = self._active_traces[trace_id]
            while node.parent_id is not None:
                parent = self._active_traces.get(node.parent_id)
                if parent is None:
                    for root_id, chain in self._chains.items():
                        if chain.get_node(node.parent_id) is not None:
                            return root_id
                    break
                node = parent
            
            if node.parent_id is None:
                return node.id
        
        return None
    
    def _cleanup_old_chains(self) -> None:
        """Remove oldest chains if limit exceeded"""
        if len(self._chains) > self._max_chains:
            sorted_chains = sorted(
                self._chains.items(),
                key=lambda x: x[1].created_at
            )
            
            to_remove = len(self._chains) - self._max_chains
            for root_id, _ in sorted_chains[:to_remove]:
                del self._chains[root_id]
            
            logger.debug(f"Cleaned up {to_remove} old chains")
    
    def set_current_trace(self, trace_id: Optional[str]) -> None:
        """
        Set the current trace ID in context.
        设置当前上下文中的追踪ID。
        
        This is used to automatically link child traces to parent traces.
        """
        current_trace_id.set(trace_id)
    
    def get_current_trace(self) -> Optional[str]:
        """Get the current trace ID from context"""
        return current_trace_id.get()


_global_tracer: Optional[CausalTracer] = None


def get_tracer() -> CausalTracer:
    """
    Get the global causal tracer instance.
    获取全局因果追踪器实例。
    """
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = CausalTracer()
    return _global_tracer
