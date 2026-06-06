# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L2-L4]
# =============================================================================
"""
SNN-based core network replacing sequential CoreNetwork.
"""

from typing import Any, Dict, List, Optional

from apps.backend.src.ai.ed3n.snn.hormonal_modulator import HormonalModulator
from apps.backend.src.ai.ed3n.snn.lif_neuron import LIFNeuron

try:
    from apps.backend.src.ai.ed3n.relation_classifier import RelationClassifier
except ImportError:
    RelationClassifier = None

try:
    from apps.backend.src.ai.ed3n.snn.batch_reorder import (
        BatchReorderEngine,
    )
    from apps.backend.src.ai.ed3n.snn.sparse_engine import (
        SparseComputationEngine,
    )
except ImportError:
    BatchReorderEngine = None
    SparseComputationEngine = None


class SNNRelationGroup:
    """An SNN-based relation group with LIF neurons."""

    def __init__(
        self, group_type: str, modulator: Optional[HormonalModulator] = None
    ):
        self.group_type = group_type
        self.neurons: Dict[str, LIFNeuron] = {}
        self.modulator = modulator

    def add_neuron(self, neuron: LIFNeuron) -> None:
        self.neurons[neuron.key] = neuron

    def get_neuron(self, key: str) -> Optional[LIFNeuron]:
        return self.neurons.get(key)

    def connect(self, key1: str, key2: str, weight: float = 1.0) -> None:
        for k in (key1, key2):
            if k not in self.neurons:
                self.neurons[k] = LIFNeuron(key=k, group_type=self.group_type)
        self.neurons[key1].connect(key2, weight)
        self.neurons[key2].connect(key1, weight)


class SNNCore:
    """
    SNN-based core network replacing sequential CoreNetwork.
    Uses LIF neurons, batch reordering, and hormonal modulation.
    """

    def __init__(self, classifier: Optional[Any] = None):
        self.groups: Dict[str, SNNRelationGroup] = {
            "synonym": SNNRelationGroup("synonym"),
            "mapping": SNNRelationGroup("mapping"),
            "analogy": SNNRelationGroup("analogy"),
        }
        self.classifier = classifier or (
            RelationClassifier() if RelationClassifier else None
        )
        self.batch_engine = BatchReorderEngine() if BatchReorderEngine else None
        self.sparse_engine = (
            SparseComputationEngine() if SparseComputationEngine else None
        )
        self.modulator = HormonalModulator()
        self._timestep: float = 1.0

    def connect_modulator(self, modulator: HormonalModulator) -> None:
        """Use an external modulator (shared across all SNN components)."""
        self.modulator = modulator
        for group in self.groups.values():
            group.modulator = modulator

    def forward(
        self,
        input_keys: List[str],
        context: Optional[Dict[str, Any]] = None,
        max_iterations: int = 10,
    ) -> Dict[str, float]:
        """
        SNN forward pass with batch reordering.
        Follows the architecture plan's snn_forward() algorithm.
        """
        self.reset()

        self.modulator.sync_from_endocrine()
        mod_factor = self.modulator.get_modulation_factor()
        threshold_mod = 1.0 / mod_factor if mod_factor > 0 else 2.0

        relation_type = "synonym"
        if input_keys and len(input_keys) >= 2 and self.classifier:
            rt, _ = self.classifier.classify_pair(
                input_keys[0], input_keys[1], context=context
            )
            relation_type = self._group_name_for(rt)

        active_group = self.groups.get(relation_type)
        if active_group is None:
            active_group = self.groups["synonym"]

        input_currents = {k: 15.0 for k in input_keys}
        for key in input_keys:
            if key not in active_group.neurons:
                active_group.add_neuron(
                    LIFNeuron(key=key, group_type=relation_type)
                )

        batch = (
            self.batch_engine.create_initial_batch(input_keys, input_currents)
            if self.batch_engine
            else None
        )
        if self.sparse_engine:
            self.sparse_engine.activate(input_keys)

        all_spikes: Dict[int, List[str]] = {}
        iteration = 0

        while batch is not None and iteration < max_iterations:
            active_neurons = {
                k: active_group.neurons[k]
                for k in batch.neuron_keys
                if k in active_group.neurons
            }

            spiked = self.batch_engine.compute_batch(
                batch, active_neurons, self._timestep, threshold_mod
            )
            all_spikes[batch.batch_id] = spiked

            silent = [k for k in batch.neuron_keys if k not in spiked]
            if self.sparse_engine:
                self.sparse_engine.deactivate(silent)

            if spiked:
                batch = self.batch_engine.get_downstream(spiked, self)
            else:
                batch = None
            iteration += 1

        output = self.batch_engine.collect_output_spikes(all_spikes)

        if output:
            max_val = max(output.values())
            if max_val > 0:
                output = {k: v / max_val for k, v in output.items()}

        return output

    def add_relation(
        self,
        key1: str,
        relation_type: Any,
        key2: str,
        weight: float = 1.0,
    ) -> None:
        group_name = (
            self._group_name_for(relation_type)
            if not isinstance(relation_type, str)
            else relation_type
        )
        group = self.groups.get(group_name)
        if group:
            group.connect(key1, key2, weight)

    def get_activation(self, key: str) -> float:
        max_act = 0.0
        for group in self.groups.values():
            neuron = group.get_neuron(key)
            if neuron and neuron.state.spike_count > max_act:
                max_act = neuron.state.spike_count
        return min(max_act / max(max_act, 1), 1.0)

    def reset(self) -> None:
        if self.batch_engine:
            self.batch_engine.reset()
        for group in self.groups.values():
            for neuron in group.neurons.values():
                neuron.reset()

    def get_sparsity_report(self) -> Dict[str, Any]:
        return (
            self.sparse_engine.get_efficiency_report()
            if self.sparse_engine
            else {}
        )

    def _group_name_for(self, rel_type) -> str:
        mapping = {
            "SYNONYM": "synonym",
            "ANTI_SYNONYM": "synonym",
            "MAPPING": "mapping",
            "ANTI_MAPPING": "mapping",
            "ANALOGY": "analogy",
            "ANTI_ANALOGY": "analogy",
        }
        type_str = (
            str(rel_type).split(".")[-1]
            if "." in str(rel_type)
            else str(rel_type)
        )
        return mapping.get(type_str.upper(), "synonym")
