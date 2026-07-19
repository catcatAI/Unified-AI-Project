"""
Angela AI v6.0 - Causal Chain Validator
因果链验证器

Validates causal chain integrity, completeness, and logical consistency.

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-19
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """驗證結果 / Validation result"""

    valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.valid


class ChainValidator:
    """Validates causal chain integrity and logical consistency."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def validate_chain(self, chain: Any) -> ValidationResult:
        """Validate a causal chain's integrity."""
        errors = []
        warnings = []

        if not chain.root_id:
            errors.append("Chain has no root_id")

        node_list = list(getattr(chain, "nodes", []))
        if not node_list:
            errors.append("empty")
            return ValidationResult(valid=False, errors=errors)

        node_map = {n.id: n for n in node_list}

        for node in node_list:
            if node.parent_id and node.parent_id not in node_map:
                errors.append(f"Broken link: {node.id} -> {node.parent_id}")
            if node.id == chain.root_id and node.parent_id:
                errors.append(f"root node {node.id} has parent")
            if node.id != chain.root_id and not node.parent_id:
                warnings.append(f"orphaned: {node.id}")
                errors.append(f"orphaned: {node.id}")
            if node.parent_id and node.parent_id in node_map:
                parent = node_map[node.parent_id]
                if node.timestamp < parent.timestamp:
                    errors.append(f"timestamp violation: {node.id} before {node.parent_id}")
                child_layer = getattr(node, "layer", None)
                parent_layer = getattr(parent, "layer", None)
                if (
                    child_layer is not None
                    and parent_layer is not None
                    and hasattr(child_layer, "value")
                    and hasattr(parent_layer, "value")
                ):
                    try:
                        if child_layer.value < parent_layer.value:
                            warnings.append(
                                f"backward layer transition: {parent_layer} -> {child_layer}"
                            )
                    except TypeError:
                        logger.debug(
                            "Layer comparison: incompatible types %s vs %s",
                            type(child_layer).__name__,
                            type(parent_layer).__name__,
                            exc_info=True,
                        )

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            stats=self._compute_stats(chain),
        )

    def _compute_stats(self, chain: Any) -> Dict[str, Any]:
        node_list = list(getattr(chain, "nodes", []))
        layers = sorted(set(str(getattr(n, "layer", "")) for n in node_list))
        layer_counts = {}
        for n in node_list:
            layer_key = str(getattr(n, "layer", ""))
            layer_counts[layer_key] = layer_counts.get(layer_key, 0) + 1
        exec_time = getattr(chain, "get_execution_time", lambda: 0.0)()
        return {
            "total_nodes": len(node_list),
            "root_id": chain.root_id,
            "depth": len(node_list),
            "layers": layers,
            "layer_counts": layer_counts,
            "layers_present": layers,
            "execution_time": exec_time,
        }

    def get_chain_statistics(self, chain: Any) -> Dict[str, Any]:
        return self._compute_stats(chain)

    def validate_layer_coverage(
        self, chain: Any, required_layers: Optional[List[Any]] = None
    ) -> ValidationResult:
        """Validate that all required layers are present."""
        node_list = list(getattr(chain, "nodes", []))
        present = sorted(set(str(getattr(n, "layer", "")) for n in node_list))
        if required_layers:
            req_strs = [str(l) for l in required_layers]
            missing = [l for l in req_strs if l not in present]
            if missing:
                return ValidationResult(
                    valid=False,
                    errors=[f"Missing layers: {missing}"],
                    stats={"present": present, "missing": missing},
                )
        return ValidationResult(valid=True, stats={"present": present})

    def check_consistency(self, chain: Any) -> List[str]:
        return self.validate_chain(chain).errors

    def check_completeness(self, chain: Any) -> Dict[str, Any]:
        result = self.validate_chain(chain)
        return {"complete": result.valid, "missing_links": result.errors}


__all__ = ["ChainValidator", "ValidationResult"]
