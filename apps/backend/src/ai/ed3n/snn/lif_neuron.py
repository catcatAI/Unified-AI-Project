# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L2-L4]
# =============================================================================
"""
Leaky Integrate-and-Fire neuron model.
"""

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List


@dataclass
class LIFState:
    membrane_potential: float = 0.0
    last_spike_time: float = -float('inf')
    refractory_remaining: int = 0
    spike_count: int = 0
    threshold: float = -55.0
    resting_potential: float = -70.0
    reset_potential: float = -65.0
    membrane_resistance: float = 1.0
    time_constant: float = 10.0
    refractory_period: int = 5


class LIFNeuron:
    """
    Leaky Integrate-and-Fire neuron.
    Membrane potential integrates input current, leaks over time.
    When potential exceeds threshold, neuron fires a spike.

    dv/dt = (-(V - V_rest) + I * R_m) / τ
    """

    def __init__(self, key: str, group_type: str = "", **kwargs):
        self.key = key
        self.group_type = group_type
        self.state = LIFState(**{k: v for k, v in kwargs.items() if hasattr(LIFState, k)})
        self.input_synapses: Dict[str, float] = {}
        self.output_synapses: Dict[str, float] = {}
        self._spike_history: Deque[float] = deque(maxlen=1000)

    def step(self, input_current: float, dt: float = 1.0, threshold_modulator: float = 1.0) -> bool:
        """
        Single time step.
        Returns True if neuron fired.
        """
        if self.state.refractory_remaining > 0:
            self.state.refractory_remaining -= 1
            return False

        leak = -(self.state.membrane_potential - self.state.resting_potential) / self.state.time_constant
        drive = input_current * self.state.membrane_resistance / self.state.time_constant

        self.state.membrane_potential += (leak + drive) * dt

        effective_threshold = self.state.threshold * threshold_modulator

        if self.state.membrane_potential >= effective_threshold:
            self.state.membrane_potential = self.state.reset_potential
            self.state.refractory_remaining = self.state.refractory_period
            self.state.spike_count += 1
            self.state.last_spike_time = time.time()
            self._spike_history.append(self.state.last_spike_time)
            return True

        return False

    def receive_spike(self, pre_key: str, weight: float = 1.0) -> float:
        """Receive a spike from a pre-synaptic neuron. Returns injected current."""
        synaptic_weight = self.input_synapses.get(pre_key, weight)
        current = synaptic_weight * 10.0
        return current

    def reset(self) -> None:
        self.state.membrane_potential = self.state.resting_potential
        self.state.refractory_remaining = 0

    def get_firing_rate(self, window_ms: float = 1000.0) -> float:
        """Calculate firing rate over last window."""
        now = time.time()
        recent = [t for t in self._spike_history if (now - t) * 1000 <= window_ms]
        return len(recent) / (window_ms / 1000.0)

    def connect(self, post_key: str, weight: float) -> None:
        self.output_synapses[post_key] = weight
