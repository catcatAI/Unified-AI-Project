"""
Angela AI v6.0 - Causal Chain Validator
因果链验证器

Validates causal chain integrity, completeness, and logical consistency.

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-19
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging

from .causal_chain import CausalChain, CausalNode, LayerType

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of chain validation"""
    valid: bool
    errors: List[str]
    warnings: List[str]
    
    def __bool__(self) -> bool:
        return self.valid


class ChainValidator:
    """
    Validates causal chains for integrity and logical consistency.
    验证因果链的完整性和逻辑一致性。
    """
    
    def __init__(self):
        self._layer_order = [
            LayerType.L1,
            LayerType.L2,
            LayerType.L3,
            LayerType.L4,
            LayerType.L5,
            LayerType.L6,
        ]
    
    def validate_chain(self, chain: CausalChain) -> ValidationResult:
        """
        Validate a complete causal chain.
        验证完整的因果链。
        
        Checks:
        - Chain completeness (no broken links)
        - Layer sequence validity (L1→L2→...→L6 progression allowed)
        - Logical consistency (timestamps, parent-child relationships)
        
        Returns:
            ValidationResult with status and any errors/warnings
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        if len(chain.nodes) == 0:
            errors.append("Chain is empty")
            return ValidationResult(valid=False, errors=errors, warnings=warnings)
        
        self._validate_completeness(chain, errors)
        self._validate_layer_sequence(chain, warnings)
        self._validate_timestamps(chain, errors)
        self._validate_parent_child(chain, errors)
        
        valid = len(errors) == 0
        
        return ValidationResult(valid=valid, errors=errors, warnings=warnings)
    
    def _validate_completeness(self, chain: CausalChain, errors: List[str]) -> None:
        """
        Validate chain completeness - ensure no broken links.
        验证链完整性 - 确保没有断链。
        """
        node_ids = {node.id for node in chain.nodes}
        
        for node in chain.nodes:
            if node.parent_id is not None and node.parent_id not in node_ids:
                errors.append(
                    f"Broken link: Node {node.id} references missing parent {node.parent_id}"
                )
    
    def _validate_layer_sequence(self, chain: CausalChain, warnings: List[str]) -> None:
        """
        Validate layer sequence - check if layers follow expected progression.
        验证层序列 - 检查层是否遵循预期的进展。
        
        Note: This is a warning only, as not all flows go through all layers.
        """
        layer_sequence = []
        visited_layers = set()
        
        root = chain.get_node(chain.root_id)
        if root:
            self._collect_layer_sequence(chain, root, layer_sequence, visited_layers)
        
        for i in range(len(layer_sequence) - 1):
            current_layer = layer_sequence[i]
            next_layer = layer_sequence[i + 1]
            
            current_index = self._layer_order.index(current_layer)
            next_index = self._layer_order.index(next_layer)
            
            if next_index < current_index:
                warnings.append(
                    f"Unusual layer transition: {current_layer} → {next_layer} "
                    f"(backward flow detected)"
                )
    
    def _collect_layer_sequence(
        self,
        chain: CausalChain,
        node: CausalNode,
        sequence: List[LayerType],
        visited: set
    ) -> None:
        """Recursively collect layer sequence from tree"""
        if node.id in visited:
            return
        
        visited.add(node.id)
        sequence.append(node.layer)
        
        for child in chain.get_children(node.id):
            self._collect_layer_sequence(chain, child, sequence, visited)
    
    def _validate_timestamps(self, chain: CausalChain, errors: List[str]) -> None:
        """
        Validate timestamps - ensure child timestamps are after parent timestamps.
        验证时间戳 - 确保子节点时间戳在父节点之后。
        """
        for node in chain.nodes:
            if node.parent_id is not None:
                parent = chain.get_node(node.parent_id)
                if parent and node.timestamp < parent.timestamp:
                    errors.append(
                        f"Timestamp violation: Child node {node.id} timestamp "
                        f"({node.timestamp}) is before parent {node.parent_id} "
                        f"timestamp ({parent.timestamp})"
                    )
    
    def _validate_parent_child(self, chain: CausalChain, errors: List[str]) -> None:
        """
        Validate parent-child relationships.
        验证父子关系。
        """
        root = chain.get_node(chain.root_id)
        if root is None:
            errors.append(f"Root node {chain.root_id} not found in chain")
            return
        
        if root.parent_id is not None:
            errors.append(f"Root node {chain.root_id} should not have a parent")
        
        for node in chain.nodes:
            if node.id != chain.root_id and node.parent_id is None:
                errors.append(
                    f"Non-root node {node.id} has no parent (orphaned node)"
                )
    
    def validate_layer_coverage(
        self,
        chain: CausalChain,
        required_layers: List[LayerType]
    ) -> ValidationResult:
        """
        Validate that chain covers all required layers.
        验证链覆盖所有必需的层。
        
        Args:
            chain: Causal chain to validate
            required_layers: List of layers that must be present
        
        Returns:
            ValidationResult indicating if all required layers are present
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        for layer in required_layers:
            if not chain.has_layer(layer):
                errors.append(f"Missing required layer: {layer}")
        
        valid = len(errors) == 0
        return ValidationResult(valid=valid, errors=errors, warnings=warnings)
    
    def get_chain_statistics(self, chain: CausalChain) -> Dict[str, any]:
        """
        Get statistics about a causal chain.
        获取因果链的统计信息。
        
        Returns:
            Dictionary with chain statistics
        """
        layer_counts = {}
        for layer in LayerType:
            layer_counts[layer.code] = len(chain.get_layer_nodes(layer))
        
        return {
            "total_nodes": len(chain.nodes),
            "layer_counts": layer_counts,
            "execution_time": chain.get_execution_time(),
            "root_id": chain.root_id,
            "created_at": chain.created_at.isoformat(),
            "layers_present": [
                layer.code for layer in LayerType if chain.has_layer(layer)
            ],
        }
