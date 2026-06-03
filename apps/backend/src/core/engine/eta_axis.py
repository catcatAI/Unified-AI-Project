"""
η (Eta) Axis — Execution/Operation Layer
========================================

η is the 7th axis (after αβγδεθ) that handles execution/operation,
contrasting θ's cognitive/evaluation role.

Layer 0 — Atomic Modules: LogicGate, ArithmeticOp, Aggregator, Router
Layer 1 — Composed Modules: Built from atoms
Layer 2 — Adjusted Modules: Parameter-adjusted versions

Trigger Curve:
  modules_to_call = floor(min(12, 3 × sigmoid(complexity × axis_count / 6)))
  adjustment_magnitude = min(0.2, 0.15 × sigmoid(complexity - 0.5))

Author: Angela AI v6.2.1
Version: 6.2.1
Date: 2026-05-15
"""

from __future__ import annotations
