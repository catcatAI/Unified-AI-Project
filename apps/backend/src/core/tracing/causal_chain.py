"""
Angela AI v6.0 - Causal Chain Model
因果链模型

Defines the data structures for representing causal chains in Angela's execution flow.

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-19
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import uuid


class LayerType(Enum):
    """
    Angela's 6-layer architecture
    Angela的6层架构
    """
    L1 = ("L1", "Biological Layer", "生物层")
    L2 = ("L2", "Memory Layer", "记忆层")
    L3 = ("L3", "Identity Layer", "身份层")
    L4 = ("L4", "Self-Generation Layer", "自我生成层")
    L5 = ("L5", "Desktop Interaction Layer", "桌面交互层")
    L6 = ("L6", "Live2D Presentation Layer", "Live2D呈现层")
    
    def __init__(self, code: str, en_name: str, cn_name: str):
        self.code = code
        self.en_name = en_name
        self.cn_name = cn_name
    
    @classmethod
    def from_string(cls, layer_str: str) -> LayerType:
        """Parse layer string to LayerType enum"""
        layer_str = layer_str.upper().strip()
        for layer in cls:
            if layer.code == layer_str:
                return layer
        raise ValueError(f"Invalid layer: {layer_str}")
    
    def __str__(self) -> str:
        return self.code


@dataclass
class CausalNode:
    """
    A node in the causal chain representing a single action or state change.
    因果链中的节点，表示单个动作或状态变化。
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: Optional[str] = None
    layer: LayerType = LayerType.L1
    module: str = ""
    action: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary for serialization"""
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "layer": self.layer.code,
            "module": self.module,
            "action": self.action,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CausalNode:
        """Create node from dictionary"""
        return cls(
            id=data["id"],
            parent_id=data.get("parent_id"),
            layer=LayerType.from_string(data["layer"]),
            module=data.get("module", ""),
            action=data.get("action", ""),
            data=data.get("data", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


@dataclass
class CausalChain:
    """
    A complete causal chain representing the full trace from input to output.
    完整的因果链，表示从输入到输出的完整追踪。
    """
    root_id: str
    nodes: List[CausalNode] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_node(self, node: CausalNode) -> None:
        """Add a node to the chain"""
        self.nodes.append(node)
    
    def get_node(self, node_id: str) -> Optional[CausalNode]:
        """Get a node by ID"""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None
    
    def get_children(self, parent_id: str) -> List[CausalNode]:
        """Get all direct children of a node"""
        return [node for node in self.nodes if node.parent_id == parent_id]
    
    def has_layer(self, layer: LayerType) -> bool:
        """Check if chain contains any node from specified layer"""
        return any(node.layer == layer for node in self.nodes)
    
    def get_layer_nodes(self, layer: LayerType) -> List[CausalNode]:
        """Get all nodes from a specific layer"""
        return [node for node in self.nodes if node.layer == layer]
    
    def get_path_to_root(self, node_id: str) -> List[CausalNode]:
        """
        Get the path from a specific node back to the root.
        获取从特定节点回溯到根节点的路径。
        """
        path = []
        current = self.get_node(node_id)
        
        while current is not None:
            path.append(current)
            if current.parent_id is None:
                break
            current = self.get_node(current.parent_id)
        
        return list(reversed(path))
    
    def get_execution_time(self) -> float:
        """
        Calculate total execution time from first to last node.
        计算从第一个节点到最后一个节点的总执行时间。
        """
        if len(self.nodes) < 2:
            return 0.0
        
        first = min(self.nodes, key=lambda n: n.timestamp)
        last = max(self.nodes, key=lambda n: n.timestamp)
        
        return (last.timestamp - first.timestamp).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chain to dictionary for serialization"""
        return {
            "root_id": self.root_id,
            "nodes": [node.to_dict() for node in self.nodes],
            "created_at": self.created_at.isoformat(),
            "node_count": len(self.nodes),
            "execution_time": self.get_execution_time(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CausalChain:
        """Create chain from dictionary"""
        chain = cls(
            root_id=data["root_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
        )
        chain.nodes = [CausalNode.from_dict(node_data) for node_data in data["nodes"]]
        return chain
