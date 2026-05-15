# η (Eta) Axis Implementation Plan

**Version**: 1.0
**Date**: 2026-05-15
**Status**: PLANNED
**Priority**: P10

---

## Overview

η is a new axis (7th axis after αβγδεθ) that handles **execution/operation layer** in contrast to θ's **cognitive/evaluation layer**.

### θ-η Dual Loop Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          SYSTEM                                  │
│                                                                  │
│    θ (Evaluation/Cognition)      ←────→      η (Execution/Operation)
│    ┌──────────────────┐               ┌────────────────────────┐ │
│    │ novelty=0.8     │               │ _param_adjust()        │ │
│    │ dimension_fit=0.3│               │ _compose_modules()     │ │
│    │ creativity=0.6  │               │ _expand_node_capacity()│ │
│    │ audit_intensity=│               │ _execution_feedback()  │ │
│    └──────────────────┘               └────────────────────────┘ │
│            │                                    │               │
│            │  θ.output → η.input                │               │
│            │  (intention to execute)            │               │
│            │                                    │               │
│            │  η.output → θ.input                │               │
│            │  (result feedback)                  │               │
│            │  (NOT θ self-regression)           │               │
└─────────────────────────────────────────────────────────────────┘
```

**Key insight**: This is NOT θ self-regression. θ's output goes through η (mirror) and returns to θ. This creates higher-order metacognition where θ thinks about the execution of its own thinking.

---

## Responsibility Split

| Responsibility | θ (Cognitive) | η (Execution) |
|---------------|---------------|---------------|
| Routing decision | ✅ Evaluate "should route?" | ❌ |
| Logic gate mounting | ✅ Evaluate "what logic needed?" | ✅ Execute mount |
| Arithmetic config | ✅ Evaluate "what calculation?" | ✅ Execute config |
| Dynamic axis creation | ✅ Evaluate "should create?" | ✅ Execute create |
| Node capacity expansion | ✅ Evaluate "capacity enough?" | ✅ Execute expand |
| Module parameter adjustment | ✅ Evaluate "adjust params?" | ✅ Execute adjust |
| Module composition | ✅ Evaluate "composition valid?" | ✅ Execute compose |
| Persistence | ❌ | ✅ Execute storage/recovery |

### θ keeps in θ

All existing θ fields remain in θ (as intention/intent):
- `theta_negativity`
- `doubt`
- `audit_intensity`
- `novelty`
- `complexity`
- `dimension_fit`
- `ambiguity`
- `abstraction_level`
- `creation_urge`
- `correction_urge`

---

## Module System Architecture

### Layer 0 — Atomic Modules (Cannot split further)

| Type | Description | Examples |
|------|-------------|----------|
| `LogicGate` | Logic decisions | AND, OR, NOT, XOR, threshold |
| `ArithmeticOp` | Arithmetic operations | ADD, SUB, MUL, DIV, custom_expr |
| `Aggregator` | Aggregation methods | SUM, MEAN, MAX, MIN, WEIGHTED_AVG |
| `Router` | Routing methods | DIRECT, FANOUT, MERGE, SPLIT |

### Layer 1 — Composed Modules (Built from atoms)

```python
code_quality_module = ComposedModule(
    name="code_quality",
    gates=[
        LogicGate(type="AND", inputs=["is_code", "has_bugs"]),
        LogicGate(type="threshold", threshold=0.2, input="error_rate"),
    ],
    arithmetic=[
        ArithmeticOp(expr="bugs/total*100", output="error_rate"),
    ],
    output_mapping={
        "error_rate": ["epsilon", "port:quality_alert"]
    }
)
```

### Layer 2 — Angela-adjusted Modules (With parameters)

```python
code_quality_v2 = code_quality_module.adjust(
    threshold=0.15,  # Down from 0.2
    weights=[0.7, 0.3],
)
```

### Core Concept: Adjustment Over Creation

```
OLD: Need → Create new logic gate
NEW: Need → Adjust existing module parameters
```

This prevents continuous new additions. Angela adjusts module parameters rather than creating from scratch.

---

## η Axis Fields

| Field | Type | Description |
|-------|------|-------------|
| `module_registry` | `Dict[str, ModuleConfig]` | Index of all modules (name → config) |
| `active_modules` | `List[str]` | Currently active module names |
| `execution_count` | `int` | Total execution count |
| `success_rate` | `float` | Routing success rate (0-1) |
| `parameter_tuning` | `Dict[str, float]` | Adjustment magnitude per module |
| `structural_drift` | `float` | Structural drift amount (0-1) |
| `module_composition` | `Dict[str, Any]` | Current topology snapshot |
| `pending_updates` | `List[UpdateOp]` | Pending parameter updates |

---

## Trigger Curve Design

### Signals (θ observations → η)

| Signal | Description |
|--------|-------------|
| `update_frequency` | Updates per time unit |
| `complexity_delta` | Adjacent complexity difference |
| `novelty_peak` | Peak novelty value |
| `misallocation_rate` | Misallocation rate |
| `buffer_pressure` | Buffer fullness |

### Module Invocation Curve

```
Formula:
  modules_to_call = floor(min(CAP, BASE × sigmoid(complexity × axis_count / 6)))

Constants:
  BASE = 3          # Base invocation count
  CAP = 12          # Maximum invocation (prevents explosion)
  AXIS_COUNT = 6    # Current axis count (scales with system growth)
```

#### Axis Count → Module Count Mapping

| Axis Count | Base | Complexity 0.5 | Complexity 0.8 | Complexity 1.0 |
|------------|------|----------------|----------------|----------------|
| 6 | 3 | 4 | 6 | 12 |
| 8 | 4 | 5 | 8 | 12 |
| 10 | 5 | 7 | 10 | 12 |
| 12 | 6 | 8 | 12 | 12 |
| 16 | 8 | 12 | 12 | 12 |

**Key insight**: More axes → more base invocations → but cap at 12 (prevents runaway)

### Parameter Adjustment Curve

```
Formula:
  adjustment_magnitude = min(MAX_DELTA, BASE_DELTA × sigmoid(complexity - 0.5))

Constants:
  MAX_DELTA = 0.2     # Maximum single adjustment
  BASE_DELTA = 0.15   # Base adjustment magnitude
```

| Complexity | Adjustment |
|------------|------------|
| 0.1 | 0.018 |
| 0.3 | 0.038 |
| 0.5 | 0.075 (critical point) |
| 0.7 | 0.135 |
| 0.9 | 0.190 |
| 1.0 | 0.200 (cap) |

**Key insight**: Medium complexity starts acceleration → high complexity approaches cap → no oscillation

### Adaptive Threshold

The trigger threshold itself is adaptive:
- No trigger for extended time → threshold auto-decreases
- Too frequent triggers → threshold auto-increases

```
trigger_threshold(t) = trigger_threshold(t-1) × (1 + α × (target_rate - actual_rate))
```

---

## Automatic Operation (No Authorization Required)

All existing Angela systems are automatic:

| System | Trigger | Behavior |
|--------|---------|----------|
| AnchorLearningEngine | allocation_decide() | Auto-update anchors |
| NegativityDetector | misallocation detected | Auto-correct |
| InfluenceApplicator | each update | Auto-propagate influence |
| RippleCascade | after trigger | Auto-ripple |
| GradientField | navigate_to_attractor() | Auto-navigate |

**Conclusion**: η operates automatically. No Angela authorization required.

---

## Implementation Steps

| # | Task | Priority | Description |
|---|------|----------|-------------|
| **P10.1** | η Axis Core Design | HIGH | DimensionState + 8 fields + initialization |
| **P10.2** | Atomic Module System | HIGH | LogicGate, ArithmeticOp, Aggregator, Router |
| **P10.3** | Composed Module | HIGH | Layer 1 composition logic |
| **P10.4** | Trigger Curve Implementation | HIGH | Sigmoid curves, adaptive threshold |
| **P10.5** | θ-η Feedback Loop | HIGH | θ output → η execution → θ feedback |
| **P10.6** | StateMatrixAdapter Integration | HIGH | η operations API |
| **P10.7** | Persistence | HIGH | Module + η config storage (Redis/JSON) |
| **P10.8** | HTTP API | MEDIUM | `/module/*`, `/eta/*` endpoints |
| **P10.9** | Tests | HIGH | Unit + integration tests |

---

## File Structure

```
apps/backend/src/core/autonomous/
├── eta_axis.py                    # NEW: η axis core
│   ├── ModuleConfig (dataclass)
│   ├── AtomicModule (enum)
│   ├── ComposedModule (dataclass)
│   ├── TriggerCurve (class)
│   └── EtaAxisState (class)
├── state_matrix.py                # MODIFY: Add self.eta
├── state_matrix_adapter.py        # MODIFY: Add eta property + API
├── state_persistence.py          # MODIFY: η persistence
└── services/api/
    └── state_matrix_api.py        # MODIFY: Add /eta/*, /module/* endpoints

tests/
├── test_eta_axis.py               # NEW: Unit tests
└── test_eta_integration.py        # NEW: Integration tests
```

---

## Key Classes

### ModuleConfig

```python
@dataclass
class ModuleConfig:
    name: str
    module_type: AtomicModule
    parameters: Dict[str, Any]
    tags: List[str]
    version: int
    created_at: datetime
    adjusted_count: int
```

### ComposedModule

```python
@dataclass
class ComposedModule:
    name: str
    atoms: List[ModuleConfig]
    composition: Dict[str, Any]
    output_mapping: Dict[str, List[str]]

    def adjust(self, **params) -> ComposedModule:
        """Return adjusted version with new parameters"""
```

### TriggerCurve

```python
class TriggerCurve:
    def __init__(self, base: float = 3, cap: float = 12):
        self.base = base
        self.cap = cap

    def compute_modules(self, complexity: float, axis_count: int) -> int:
        """Compute module count based on complexity and axis count"""

    def compute_delta(self, complexity: float) -> float:
        """Compute parameter adjustment magnitude"""
```

---

## Integration Points

### With θ (Cognitive Layer)

- θ observes signals → passes to η
- η executes → returns results to θ
- θ adjusts evaluation criteria based on results

### With Existing Systems

- `StateMatrixAdapter.eta`: EtaAxisState accessor
- `StateMatrixAdapter.update_eta()`: Update η fields
- `StateMatrixAdapter.invoke_modules()`: Trigger module invocation
- `StateMatrixAdapter.apply_parameter_delta()`: Apply adjustments

### With Persistence

- `StatePersistence.save()`: Save η config
- `StatePersistence.load()`: Load η config
- Auto-checkpoint: η state included in auto-save

---

## Success Criteria

1. η axis initialized with 8 fields
2. Module registry supports 4 atomic types
3. ComposedModule can combine atoms
4. Trigger curve correctly computes invocation count
5. θ-η feedback loop functions
6. StateMatrixAdapter exposes η operations
7. η state persists to Redis/JSON
8. HTTP API exposes `/eta/*` and `/module/*` endpoints
9. All tests pass

---

## Notes

- Upper cap of 12 modules prevents system explosion
- Sigmoid curves prevent oscillation at extremes
- Adaptive threshold ensures responsiveness without over-triggering
- θ-η feedback is NOT self-regression; it's reflection through execution layer
- All operations are automatic (no authorization required)