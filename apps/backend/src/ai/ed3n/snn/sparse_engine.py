# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L2-L4]
# =============================================================================
"""
Sparse computation optimization.
Only active neurons participate in each batch.
"""

from typing import Any, Dict, List, Set

from apps.backend.src.ai.ed3n.snn.lif_neuron import LIFNeuron


class SparseComputationEngine:
    """
    Reduces computation by tracking active vs inactive neurons.
    Only active neurons participate in each batch.
    """

    def __init__(self):
        self.active_neurons: Set[str] = set()
        self.inactive_neurons: Set[str] = set()
        self._computation_saved: int = 0
        self._total_computation: int = 0

    def activate(self, keys: List[str]) -> None:
        for k in keys:
            self.active_neurons.add(k)
            self.inactive_neurons.discard(k)

    def deactivate(self, keys: List[str]) -> None:
        for k in keys:
            self.inactive_neurons.add(k)
            self.active_neurons.discard(k)

    def get_active_ratio(self) -> float:
        total = len(self.active_neurons) + len(self.inactive_neurons)
        return len(self.active_neurons) / max(total, 1)

    def compute_sparse(
        self, all_neurons: Dict[str, LIFNeuron], batch_keys: List[str]
    ) -> Dict[str, LIFNeuron]:
        """
        Only return neurons that are in batch_keys AND active.
        Records how much computation was saved.
        """
        result: Dict[str, LIFNeuron] = {}
        skipped = 0
        for key in batch_keys:
            if key in self.inactive_neurons:
                skipped += 1
            elif key in all_neurons:
                result[key] = all_neurons[key]

        self._total_computation += len(batch_keys)
        self._computation_saved += skipped
        return result

    def get_efficiency_report(self) -> Dict[str, Any]:
        ratio = self._computation_saved / max(self._total_computation, 1)
        return {
            "computation_saved": self._computation_saved,
            "total_computation": self._total_computation,
            "sparsity_ratio": round(ratio, 4),
            "active_neurons": len(self.active_neurons),
            "inactive_neurons": len(self.inactive_neurons),
            "active_ratio": round(self.get_active_ratio(), 4),
        }

    def reset_metrics(self) -> None:
        self._computation_saved = 0
        self._total_computation = 0
