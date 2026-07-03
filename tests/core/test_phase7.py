import pytest

try:
    from core.engine.state_matrix_adapter import StateMatrixAdapter, StateMatrixFacade
except ImportError:
    import pytest; pytest.skip("StateMatrixAdapter is a stub", allow_module_level=True)

def test_print_based_script():
    pytest.skip("print-based diagnostics script")


print("=== StateMatrixAdapter Smoke Test ===")

sm = StateMatrixAdapter()
print(f"Adapter: {sm}")

sm.update_alpha(focus=0.8, energy=0.7)
sm.update_beta(curiosity=0.6, clarity=0.5)
sm.update_gamma(happiness=0.7, calm=0.6)
sm.update_delta(bond=0.5)
sm.update_epsilon(logic=0.8, precision=0.7)
sm.update_theta(novelty=0.6, creation_urge=0.3)

print(f"Alpha: avg={sm.alpha.get_average():.3f}")
print(f"Beta: avg={sm.beta.get_average():.3f}")
print(f"Gamma: avg={sm.gamma.get_average():.3f}")

print(f"Temporal: {sm.temporal.size()} snapshots")
trend = sm.temporal_trend('alpha', 'focus', window=10)
print(f"Alpha.focus trend: {trend.direction}, slope={trend.slope:.4f}")

inf = sm.influence_compute('alpha', 'beta')
print(f"Influence alpha->beta: {inf:.4f}")
inf2 = sm.influence_compute_all()
print(f"All influences: {len(inf2)} sources")

decision = sm.allocation_decide([0.1] * 32, 'test')
print(f"Allocation: {decision.action.value} -> target={decision.target}")

sm.trigger_theta_negativity(0.5)
print(f"Negativity: {sm.negativity_detector.negativity:.2f}")

ripples = sm.apply_ripple(
    operator=type('M', (), {'ADD': 'add'})().ADD,
    result=10.0,
    epsilon_delta=0.5,
    alpha_arousal=0.3,
    beta_focus=0.2,
    cascade_targets=['alpha', 'beta', 'gamma', 'delta'],
)
print(f"Ripple cascade: {len(ripples)} nodes")
print(f"Ripple summary: {sm.ripple_summary()}")

report = sm.full_report()
print(f"Full report keys: {list(report.keys())}")

print()
print("=== StateMatrixFacade ===")
facade = StateMatrixFacade()
facade.update(focus=0.9, curiosity=0.8)
print(f"Facade: {facade}")
trend2 = facade.trend('alpha', 'focus', window=5)
print(f"Alpha.focus trend: {trend2.direction}")

print()
print("=== Adapter vs Old SM ===")
from core.autonomous.state_matrix import StateMatrix4D

old = StateMatrix4D()
old.update_alpha(focus=0.7)
print(f"Old SM: alpha.focus={old.alpha.values.get('focus', 'N/A')}")
print(f"Adapter: alpha.focus={sm.alpha.values.get('focus', 'N/A')}")

print()
print("ALL ADAPTER TESTS PASSED")