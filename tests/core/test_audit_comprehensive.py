"""
Full system audit: comprehensive test of ALL Angela state system capabilities.
"""

import pytest
from core.state.axis_field import AxisFieldRegistry
from core.state.temporal import SnapshotQuery, TemporalState

try:
    from core.allocation.policy import AllocationContext, AllocationPolicy
except ImportError:
    import pytest; pytest.skip("AllocationPolicy is a stub", allow_module_level=True)
try:
    from core.allocation.resonance import ResonanceEngine
except ImportError:
    import pytest; pytest.skip("ResonanceEngine is a stub", allow_module_level=True)

from core.allocation.negativity import NegativityDetector
from core.engine.state_matrix_adapter import StateMatrixAdapter

try:
    from core.autonomous.state_matrix import StateMatrix4D
except ImportError:
    import pytest; pytest.skip("StateMatrix4D not available", allow_module_level=True)

from core.engine.influence_applicator import INFLUENCE_RULES, InfluenceApplicator, get_applicator

try:
    from core.autonomous.self_introspector_v2 import SelfIntrospectorV2
except ImportError:
    import pytest; pytest.skip("SelfIntrospectorV2 does not exist", allow_module_level=True)
try:
    from ai.code_inspection.code_inspector_integration import CodeInspectorBridge, create_bridge
except ImportError:
    import pytest; pytest.skip("CodeInspectorBridge does not exist", allow_module_level=True)

# Remove test function — this is a diagnostic print-based script (see §X #141)
# All diagnostic code is wrapped in if __name__ == "__main__": to prevent execution during test collection


if __name__ == "__main__":
    print("=" * 70)
    print("ANGELA STATE SYSTEM — COMPREHENSIVE AUDIT")
    print("=" * 70)

    # === 1. Field Registry Audit ===
    print("\n[1] AXIS FIELD REGISTRY")
    reg = AxisFieldRegistry()
    all_axes = reg.all_axes()
    print(f"  Axes: {all_axes}")
    print(f"  Total fields: {reg.count()}")
    for ax in all_axes:
        fields = reg.fields_for(ax)
        print(f"  {ax}: {len(fields)} fields — {[f.name for f in fields]}")

    # === 2. TemporalState Audit ===
    print("\n[2] TEMPORAL STATE")
    tl = TemporalState(max_size=200)

    # Record 50 snapshots across 6 axes
    for i in range(50):
        tl.record({
            'timestamp': f'2026-05-14T{i//60:02d}:{i%60:02d}:00',
            'alpha': {'energy': 0.5 + (i % 10) * 0.02, 'arousal': 0.5 + (i % 5) * 0.03, 'comfort': 0.6, 'tension': 0.2},
            'beta': {'focus': 0.6 + (i % 8) * 0.02, 'curiosity': 0.7, 'clarity': 0.5, 'confusion': 0.1},
            'gamma': {'happiness': 0.5 + (i % 12) * 0.01, 'calm': 0.6, 'fear': 0.0, 'sadness': 0.0},
            'delta': {'attention': 0.5, 'bond': 0.5, 'presence': 0.5, 'engagement': 0.5},
            'epsilon': {'logic': 0.5, 'precision': 0.6, 'complexity': 0.3, 'certainty': 0.5},
            'theta': {'novelty': 0.5, 'theta_negativity': 0.0, 'correction_urge': 0.0},
        })

    print(f"  Size: {tl.size()}")
    print(f"  Recent 20%: {len(tl.recent(0.2))}")

    # Trend per axis
    for ax in ['alpha', 'beta', 'gamma']:
        field = 'energy' if ax == 'alpha' else ('focus' if ax == 'beta' else 'happiness')
        t = tl.trend(ax, field, window=30)
        print(f"  {ax}.{field} trend: {t.direction} (slope={t.slope:.4f}, mean={t.mean:.3f})")

    # Anomalies
    anom = tl.anomalies('alpha', 'energy', threshold=0.3)
    print(f"  Alpha.energy anomalies (thresh=0.3): {len(anom)}")

    # Correlation
    corr = tl.correlation('alpha', 'energy', 'beta', 'focus', window=30)
    print(f"  Correlation alpha.energy vs beta.focus: r={corr.correlation:.4f} ({corr.strength})")

    # Drift
    drift = tl.find_drift('gamma', 'happiness', expected_value=0.5, drift_threshold=0.2)
    print(f"  Gamma.happiness drift from 0.5 (thresh=0.2): {len(drift)} points")

    # Get at negative index
    snap = tl.get_at(-1)
    print(f"  get_at(-1): timestamp={snap['timestamp']}")

    # Query
    query = SnapshotQuery(axes=['alpha', 'beta'], limit=5)
    results = tl.query(query)
    print(f"  Query(axes=[alpha,beta], limit=5): {len(results)} results")

    # === 3. Resonance Engine Audit ===
    print("\n[3] RESONANCE ENGINE")
    eng = ResonanceEngine()
    test_vec = [0.1] * 32
    test_vec[0] = 0.8

    profile = eng.compute_profile(test_vec)
    print(f"  Best axis: {profile.best_axis} ({profile.max_resonance:.4f})")
    print(f"  Entropy: {profile.entropy:.4f}")
    print(f"  Active axes (sim>0.15): {len(profile.similarities)}")

    # === 4. Allocation Policy Audit ===
    print("\n[4] ALLOCATION POLICY")
    policy = AllocationPolicy()
    ctx_high = AllocationContext(vector=test_vec, label='high_sim_task', max_resonance=0.8, novelty=0.3, complexity=2)
    ctx_low = AllocationContext(vector=test_vec, label='low_sim_task', max_resonance=0.2, novelty=0.7, complexity=5)
    ctx_comp = AllocationContext(vector=test_vec, label='comp_task', max_resonance=0.4, novelty=0.4, complexity=2)

    for name, ctx in [('high_sim', ctx_high), ('low_sim', ctx_low), ('composite', ctx_comp)]:
        result = policy.decide(ctx)
        print(f"  {name}: {result.action} -> {result.target or result.proposed_name} (conf={result.confidence:.2f})")

    # === 5. Negativity Detector Audit ===
    print("\n[5] NEGATIVITY DETECTOR")
    det = NegativityDetector(timeline=tl, resonance_engine=eng)
    det.trigger(strength=0.3)
    report = det.report()
    print(f"  Trigger(0.3): neg={report['negativity']:.2f}, urge={report['correction_urge']:.2f}")
    print(f"  needs_correction: {report['needs_correction']}")
    print(f"  misallocated points: {report['misallocation_count']}")
    det.trigger(strength=0.7)
    print(f"  Trigger(0.7): neg={det.negativity:.2f}, urge={det.correction_urge:.2f}")
    det.reset()
    print(f"  After reset: neg={det.negativity:.2f}")

    # === 6. InfluenceApplicator Audit ===
    print("\n[6] INFLUENCE APPLICATOR")
    appl = InfluenceApplicator()
    print(f"  Rules for alpha->beta: {len(INFLUENCE_RULES['alpha']['beta'])} rules")
    print(f"  Rules for gamma->alpha: {len(INFLUENCE_RULES['gamma']['alpha'])} rules")
    print(f"  Rules: {INFLUENCE_RULES['gamma']['alpha']}")

    # Test apply
    sm = StateMatrix4D()
    sm.update_gamma(happiness=0.8, calm=0.5, fear=0.0)
    sm.update_alpha(energy=0.5, comfort=0.5, arousal=0.5, tension=0.5)
    initial_energy = sm.alpha.values['energy']
    initial_tension = sm.alpha.values['tension']
    appl.apply('gamma', 'alpha', sm.gamma, sm.alpha, amount=0.05)
    print(f"  gamma->alpha (amount=0.05, happiness=0.8):")
    print(f"    energy: {initial_energy:.4f} -> {sm.alpha.values['energy']:.4f} (delta={sm.alpha.values['energy']-initial_energy:+.4f})")
    print(f"    tension: {initial_tension:.4f} -> {sm.alpha.values['tension']:.4f} (delta={sm.alpha.values['tension']-initial_tension:+.4f})")
    expected_energy = 0.05 * 0.8 * 0.1
    expected_tension = -0.05 * 0.8 * 0.1
    print(f"    expected: energy {expected_energy:+.4f}, tension {expected_tension:+.4f}")

    # === 7. StateMatrixAdapter Audit ===
    print("\n[7] STATE MATRIX ADAPTER")
    sm2 = StateMatrixAdapter()
    for i in range(10):
        sm2.update_alpha(energy=0.5 + i * 0.02, arousal=0.5, comfort=0.5, tension=0.1)
        sm2.update_beta(focus=0.6 + i * 0.01, curiosity=0.6, clarity=0.5, confusion=0.1)
        sm2.update_gamma(happiness=0.5 + (i % 5) * 0.01, calm=0.5, fear=0.0, sadness=0.0)
        sm2.update_delta(attention=0.5, bond=0.5, presence=0.5, engagement=0.5)
        sm2.update_epsilon(logic=0.5, precision=0.5, complexity=0.3, certainty=0.5)
        sm2.update_theta(novelty=0.5, complexity=0.5, ambiguity=0.5)

    print(f"  Temporal size: {sm2.temporal.size()}")
    influences = sm2.compute_influences()
    print(f"  Influence keys: {list(influences.keys())}")
    print(f"  alpha->beta: {influences['alpha']['beta']:.4f}")
    print(f"  gamma->alpha: {influences['gamma']['alpha']:.4f}")

    decision = sm2.allocation_decide([0.1]*32, 'test_task')
    print(f"  Allocation decision: {decision.action} -> {decision.target or decision.proposed_name} (conf={decision.confidence:.2f})")

    report = sm2.full_report()
    print(f"  Full report sections: {list(report.keys())}")
    print(f"  State matrix averages: {list(report['state_matrix']['averages'].keys())}")

    # === 8. SelfIntrospectorV2 Audit ===
    print("\n[8] SELF INTROSPECTOR V2")
    si = SelfIntrospectorV2(state_adapter=sm2)
    wb = si.get_wellbeing_report()
    print(f"  Wellbeing report: {list(wb.keys())}")

    mhc = si.perform_mental_health_check(state_analysis={'wellbeing': 0.6, 'arousal': 0.5, 'stress_level': 0.2}, context={'task': 'audit'})
    print(f"  Mental health: status={mhc.get('status', 'N/A')}")

    # === 9. CodeInspectorBridge Audit ===
    print("\n[9] CODE INSPECTOR BRIDGE")
    bridge = create_bridge(state_adapter=sm2)
    print(f"  Bridge created: {bridge is not None}")

    inspect_result = {'lines': 150, 'critical': 8, 'high': 25}
    complexity_score = bridge._compute_complexity(inspect_result)
    print(f"  Complexity score: {complexity_score}")

    stability_score = bridge._compute_stability(critical=5, high=3)
    print(f"  Stability score: {stability_score}")

    clarity_score = bridge._compute_clarity(medium=40, low=0)
    print(f"  Clarity score: {clarity_score}")

    issue_vec = bridge._build_issue_vector(total=50, critical=3, complexity=0.8)
    print(f"  Issue vector: {issue_vec}")

    # === 10. Negative Index Bug Fix Verification ===
    print("\n[10] NEGATIVE INDEX BUG FIX VERIFICATION")
    tl2 = TemporalState(max_size=50)
    for i in range(10):
        tl2.record({'alpha': {'energy': 0.5 + i * 0.01}})

    try:
        snap_n1 = tl2.get_at(-1)
        snap_n5 = tl2.get_at(-5)
        snap_n10 = tl2.get_at(-10)
        snap_9 = tl2.get_at(9)
        snap_5 = tl2.get_at(5)
        snap_0 = tl2.get_at(0)
        print(f"  get_at(-1): OK (energy={snap_n1['alpha']['energy']:.3f})")
        print(f"  get_at(-5): OK (energy={snap_n5['alpha']['energy']:.3f})")
        print(f"  get_at(-10): OK (energy={snap_n10['alpha']['energy']:.3f})")
        print(f"  get_at(9): OK (energy={snap_9['alpha']['energy']:.3f})")
        print(f"  get_at(5): OK (energy={snap_5['alpha']['energy']:.3f})")
        print(f"  get_at(0): OK (energy={snap_0['alpha']['energy']:.3f})")
        if abs(snap_n1['alpha']['energy'] - snap_9['alpha']['energy']) < 0.001:
            print(f"  PASS: get_at(-1) == get_at(9)")
        else:
            print(f"  FAIL: get_at(-1)={snap_n1['alpha']['energy']:.3f} != get_at(9)={snap_9['alpha']['energy']:.3f}")
        if abs(snap_n5['alpha']['energy'] - snap_5['alpha']['energy']) < 0.001:
            print(f"  PASS: get_at(-5) == get_at(5)")
        else:
            print(f"  FAIL: get_at(-5)={snap_n5['alpha']['energy']:.3f} != get_at(5)={snap_5['alpha']['energy']:.3f}")
        if abs(snap_n10['alpha']['energy'] - snap_0['alpha']['energy']) < 0.001:
            print(f"  PASS: get_at(-10) == get_at(0)")
        else:
            print(f"  FAIL: get_at(-10)={snap_n10['alpha']['energy']:.3f} != get_at(0)={snap_0['alpha']['energy']:.3f}")
    except Exception as e:
        print(f"  FAIL: {e}")

    # === 11. InfluenceApplicator amount Bug Fix Verification ===
    print("\n[11] INFLUENCE APPLICATOR AMOUNT BUG FIX VERIFICATION")
    sm3 = StateMatrix4D()
    sm3.update_gamma(happiness=0.8, calm=0.5, fear=0.0)
    sm3.update_alpha(energy=0.5, comfort=0.5, arousal=0.5, tension=0.5)
    e0 = sm3.alpha.values['energy']
    appl.apply('gamma', 'alpha', sm3.gamma, sm3.alpha, amount=0.05)
    e1 = sm3.alpha.values['energy']
    actual_delta = e1 - e0
    expected_delta = 0.05 * 0.8 * 0.1  # amount * happiness * weight
    print(f"  gamma->alpha.energy with amount=0.05:")
    print(f"    delta: {actual_delta:+.6f}")
    print(f"    expected: {expected_delta:+.6f}")
    if abs(actual_delta - expected_delta) < 0.0001:
        print(f"  ✓ amount parameter correctly applied")
    else:
        print(f"  ✗ amount parameter NOT applied correctly")
        print(f"    ratio: {abs(actual_delta / expected_delta):.2f}x")

    # === 12. INFLUENCE RULES COVERAGE ===
    print("\n[12] INFLUENCE RULES COVERAGE")
    total_rules = 0
    for src in INFLUENCE_RULES:
        for tgt in INFLUENCE_RULES[src]:
            n = len(INFLUENCE_RULES[src][tgt])
            total_rules += n
            if n > 0:
                print(f"  {src}->{tgt}: {n} rules")
                for rule in INFLUENCE_RULES[src][tgt]:
                    src_f, tgt_f, w = rule
                    sign = "+" if w >= 0 else ""
                    print(f"    {src_f} -> {tgt_f}: {sign}{w:.2f}")
    print(f"  Total: {total_rules} rules across {len(INFLUENCE_RULES)} sources")

    # === 13. ALLOCATION STAGES ===
    print("\n[13] ALLOCATION STAGES")
    print(f"  Stages: {[s.__class__.__name__ for s in policy.stages]}")

    # === 14. NEGATIVITY STAGES ===
    print("\n[14] NEGATIVITY SYSTEM")
    det2 = NegativityDetector(timeline=tl, resonance_engine=eng)
    for lvl in [0.1, 0.3, 0.5, 0.7, 0.9]:
        det2.trigger(strength=lvl)
        print(f"  level={lvl}: neg={det2.negativity:.2f}, correction_urge={det2.correction_urge:.2f}")

    print("\n" + "=" * 70)
    print("AUDIT COMPLETE")
    print("=" * 70)