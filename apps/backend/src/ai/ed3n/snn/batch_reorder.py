# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L2-L4]
# =============================================================================
"""
Spike-driven batch reordering engine (Section 4.2).
Only neurons that receive spikes participate in the next batch.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from .lif_neuron import LIFNeuron


@dataclass
class SNNBatch:
    batch_id: int
    neuron_keys: List[str]
    iteration: int
    input_currents: Dict[str, float]
    parent_batch: Optional[int] = None


class BatchReorderEngine:
    """
    Implements spike-driven batch reordering.
    Only neurons that receive spikes participate in the next batch.
    """

    def __init__(self):
        self.batches: List[SNNBatch] = []
        self._batch_counter: int = 0

    def create_initial_batch(
        self, neuron_keys: List[str], input_currents: Dict[str, float]
    ) -> SNNBatch:
        """First batch: all directly activated neurons."""
        batch = SNNBatch(
            batch_id=self._batch_counter,
            neuron_keys=neuron_keys,
            iteration=0,
            input_currents=input_currents,
        )
        self._batch_counter += 1
        self.batches.append(batch)
        return batch

    def get_downstream(
        self, spiked_keys: List[str], snn_network
    ) -> Optional[SNNBatch]:
        """
        Get next batch: only neurons downstream of spiked ones.
        Returns None if no downstream neurons exist.
        """
        downstream: Set[str] = set()
        for key in spiked_keys:
            for group in snn_network.groups.values():
                neuron = group.neurons.get(key)
                if neuron:
                    for post_key in neuron.output_synapses:
                        downstream.add(post_key)

        if not downstream:
            return None

        currents: Dict[str, float] = {}
        for post_key in downstream:
            current = 0.0
            for pre_key in spiked_keys:
                for group in snn_network.groups.values():
                    pre = group.neurons.get(pre_key)
                    if pre and post_key in pre.output_synapses:
                        current += pre.output_synapses[post_key] * 10.0
            currents[post_key] = current

        batch = SNNBatch(
            batch_id=self._batch_counter,
            neuron_keys=list(downstream),
            iteration=len(self.batches),
            input_currents=currents,
            parent_batch=self.batches[-1].batch_id if self.batches else None,
        )
        self._batch_counter += 1
        self.batches.append(batch)
        return batch

    def compute_batch(
        self,
        batch: SNNBatch,
        lif_neurons: Dict[str, LIFNeuron],
        dt: float = 1.0,
        threshold_modulator: float = 1.0,
    ) -> List[str]:
        """Compute one batch. Returns list of neuron keys that spiked."""
        spiked: List[str] = []
        for key in batch.neuron_keys:
            neuron = lif_neurons.get(key)
            if neuron:
                current = batch.input_currents.get(key, 0.0)
                if neuron.step(current, dt, threshold_modulator):
                    spiked.append(key)
        return spiked

    def collect_output_spikes(
        self, all_spikes: Dict[int, List[str]]
    ) -> Dict[str, float]:
        """Collect all spikes across batches. Returns {key: spike_count}."""
        result: Dict[str, float] = {}
        for batch_id, spiked_keys in all_spikes.items():
            for key in spiked_keys:
                result[key] = result.get(key, 0.0) + 1.0
        return result

    def reset(self) -> None:
        self.batches.clear()
