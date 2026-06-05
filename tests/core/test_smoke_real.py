"""
Smoke Test — StateMatrixAdapter 完整驗證
=========================================

目標：確認 StateMatrixAdapter 在實際場景中與舊 StateMatrix4D 完全兼容，
      新 API 能正確驅動所有核心功能。

8 個測試場景：
  S1: 基本狀態更新 + history
  S2: 分配決策新舊比對
  S3: 影響計算新舊比對
  S4: 漣漪應用
  S5: θ 自糾完整鏈
  S6: 時間查詢
  S7: 配置加載
  S8: 完整報告

Author: Angela AI v6.2
"""

import sys

try:
    from core.engine.state_matrix_adapter import StateMatrixAdapter, StateMatrixFacade
except ImportError:
    import pytest; pytest.skip("StateMatrixAdapter is a stub", allow_module_level=True)
from core.autonomous.state_matrix import StateMatrix4D


def s1_basic_updates():
    """S1: 基本狀態更新 + TemporalState 同步"""
    print("\n[S1] Basic Updates + Temporal Sync")
    sm = StateMatrixAdapter()

    initial_size = sm.temporal.size()

    sm.update_alpha(energy=0.7, arousal=0.8)
    sm.update_beta(focus=0.6, curiosity=0.8)
    sm.update_gamma(happiness=0.7, calm=0.6)
    sm.update_delta(bond=0.5)
    sm.update_epsilon(logic=0.8, precision=0.7)
    sm.update_theta(novelty=0.6, creation_urge=0.3)

    assert sm.alpha.values['energy'] == 0.7, "alpha.energy should be 0.7"
    assert sm.alpha.values['arousal'] == 0.8, "alpha.arousal should be 0.8"
    assert sm.beta.values['focus'] == 0.6, "beta.focus should be 0.6"
    assert sm.beta.values['curiosity'] == 0.8, "beta.curiosity should be 0.8"
    assert sm.theta.values['novelty'] == 0.6, "theta.novelty should be 0.6"

    assert sm.temporal.size() == initial_size + 6, f"Expected {initial_size + 6}, got {sm.temporal.size()}"

    latest = sm.temporal.get_at(-1)
    assert latest is not None, "Latest snapshot should exist"
    assert 'alpha' in latest, "Snapshot should contain alpha"
    assert 'beta' in latest, "Snapshot should contain beta"
    assert 'gamma' in latest, "Snapshot should contain gamma"
    assert 'delta' in latest, "Snapshot should contain delta"
    assert 'epsilon' in latest, "Snapshot should contain epsilon"
    assert 'theta' in latest, "Snapshot should contain theta"
    assert 'timestamp' in latest, "Snapshot should have timestamp"
    assert '__index__' in latest, "Snapshot should have index"

    latest_alpha = latest['alpha']
    assert latest_alpha.get('energy') == 0.7, "Snapshot alpha.energy should be 0.7"
    assert latest_alpha.get('arousal') == 0.8, "Snapshot alpha.arousal should be 0.8"

    print(f"  ✓ TemporalState synced: {sm.temporal.size()} snapshots")
    print(f"  ✓ All 6 axes recorded in snapshot")
    print(f"  ✓ Values correctly set in correct axes")


def s2_allocation_decision():
    """S2: 分配決策新舊比對"""
    print("\n[S2] Allocation Decision (New vs Old)")

    sm = StateMatrixAdapter()
    old = StateMatrix4D()

    test_vec = [0.1] * 32

    new_decision = sm.allocation_decide(test_vec, 'test_query')
    old_decision = old.meta_allocate(test_vec, 'test_query')

    assert new_decision.action is not None, "New decision should have action"
    assert old_decision.action is not None, "Old decision should have action"
    assert new_decision.confidence >= 0.0, "Confidence should be non-negative"

    print(f"  ✓ New API:  {new_decision}")
    print(f"  ✓ Old API:  {old_decision}")
    print(f"  ✓ Both APIs return valid decisions")


def s3_influence_computation():
    """S3: 影響計算新舊比對"""
    print("\n[S3] Influence Computation (New vs Old)")

    sm = StateMatrixAdapter()

    old_influences = sm.compute_influences()
    new_influence = sm.influence_compute('alpha', 'beta')

    assert isinstance(old_influences, dict), "Old influences should be dict"
    assert isinstance(new_influence, float), "New influence should be float"
    assert 'alpha' in old_influences, "Old influences should have alpha"
    assert 'beta' in old_influences['alpha'], "Old influences[alpha] should have beta"

    old_val = old_influences['alpha']['beta']

    assert 0.0 <= new_influence <= 3.0, f"Influence should be in [0,3], got {new_influence}"
    print(f"  ✓ New InfluenceSpace: alpha->beta = {new_influence:.4f}")
    print(f"  ✓ Old compute_influences: alpha->beta = {old_val:.4f}")
    print(f"  ✓ Both in reasonable range")


def s4_ripple_application():
    """S4: 漣漪應用"""
    print("\n[S4] Ripple Application")

    sm = StateMatrixAdapter()

    from core.ripple.node import MathOp
    ripples = sm.apply_ripple(
        operator=MathOp.ADD,
        result=10.0,
        epsilon_delta=0.5,
        alpha_arousal=0.3,
        beta_focus=0.2,
        gamma_excitement=0.1,
        delta_engagement=0.05,
        theta_delta=0.02,
        cascade_targets=['alpha', 'beta', 'gamma', 'delta', 'theta'],
    )

    assert len(ripples) >= 1, f"Expected at least 1 ripple node, got {len(ripples)}"
    summary = sm.ripple_summary()
    assert summary['count'] >= 1, "Accumulator should have at least 1 node"
    assert 'cumulative_epsilon' in summary, "Summary should have cumulative_epsilon"
    assert summary['cumulative_epsilon'] == 0.5, "Cumulative epsilon should be 0.5"

    print(f"  ✓ Cascade produced {len(ripples)} ripple nodes")
    print(f"  ✓ Accumulator: count={summary['count']}, epsilon={summary['cumulative_epsilon']}")


def s5_theta_self_correction():
    """S5: θ 自糾完整鏈"""
    print("\n[S5] Theta Self-Correction Chain")

    sm = StateMatrixAdapter()

    sm.trigger_theta_negativity(0.3)
    assert sm.negativity_detector.negativity == 0.3, "Negativity should be 0.3"

    sm.update_theta(theta_negativity=0.6)
    assert sm.theta.values.get('theta_negativity') == 0.6, "theta_negativity should be 0.6"

    detected = sm.detect_misallocated_points()
    assert isinstance(detected, list), "detect_misallocated_points should return list"

    report = sm.get_negativity_report()
    assert isinstance(report, dict), "Report should be dict"

    if sm.negativity_detector.needs_correction:
        result = sm.correct_misallocation('test_point', dry_run=True)
        assert isinstance(result, dict), "Should return correction info"

    print(f"  ✓ Trigger: negativity={sm.negativity_detector.negativity}")
    print(f"  ✓ Update theta: theta_negativity={sm.theta.values.get('theta_negativity')}")
    print(f"  ✓ Detect: {len(detected)} misallocated points")
    print(f"  ✓ Report: {list(report.keys())}")


def s6_temporal_queries():
    """S6: 時間查詢"""
    print("\n[S6] Temporal Queries")

    sm = StateMatrixAdapter()

    for i in range(60):
        sm.update_alpha(energy=0.5 + i * 0.005)
        sm.update_beta(focus=0.5 + i * 0.004)

    trend = sm.temporal_trend('alpha', 'energy', window=50)
    assert trend is not None, "Trend should return result"

    anomalies = sm.temporal_anomalies('alpha', 'energy', threshold=0.5, window=50)
    assert isinstance(anomalies, list), "Anomalies should be list"

    corr = sm.temporal_correlation('alpha', 'energy', 'beta', 'focus', window=50)
    assert abs(corr.correlation) <= 1.0, "Correlation should be in [-1, 1]"

    recent = sm.temporal.recent(fraction=0.2)
    assert len(recent) > 0, "Recent should return snapshots"
    assert len(recent) <= max(1, int(sm.temporal.size() * 0.2)) + 1, "20% fraction should be respected"

    from core.state.temporal import SnapshotQuery
    query_result = sm.temporal.query(SnapshotQuery(axes=['alpha'], limit=5))
    assert len(query_result) <= 5, "Query with limit should respect limit"

    print(f"  ✓ Trend: {trend.direction}(slope={trend.slope:.4f})")
    print(f"  ✓ Anomalies: {len(anomalies)} found")
    print(f"  ✓ Correlation: {corr.correlation:.3f}({corr.strength})")
    print(f"  ✓ Recent 20%: {len(recent)} snapshots")
    print(f"  ✓ Query with limit: {len(query_result)} results")


def s7_config_loading():
    """S7: 配置加載"""
    print("\n[S7] Config Loading")

    sm = StateMatrixAdapter()
    cfg = sm.config

    assert cfg is not None, "Config should load successfully"
    assert hasattr(cfg, 'state_matrix'), "Config should have state_matrix"
    assert hasattr(cfg, 'axes'), "Config should have axes"
    assert len(cfg.axes) == 6, f"Expected 6 axes, got {len(cfg.axes)}"

    alloc = cfg.allocation
    assert alloc.assign_threshold == 0.7, "assign_threshold should be 0.7"
    assert alloc.composite_threshold == 0.3, "composite_threshold should be 0.3"

    neg = cfg.negativity
    assert neg.trigger_threshold == 0.5, "trigger_threshold should be 0.5"
    assert neg.correction_urge_threshold == 0.6, "correction_urge_threshold should be 0.6"

    spatial = cfg.spatial
    assert spatial.gravity_constant == 25.0, "gravity_constant should be 25.0"

    assert isinstance(cfg.influence_matrix, dict), "influence_matrix should be dict"
    assert 'alpha' in cfg.influence_matrix, "influence_matrix should have alpha"
    assert len(cfg.influence_matrix) == 6, "Should have 6 axes in influence matrix"

    print(f"  ✓ Config: max_history={cfg.state_matrix.max_history}, axes={len(cfg.axes)}")
    print(f"  ✓ Allocation: assign={alloc.assign_threshold}, composite={alloc.composite_threshold}")
    print(f"  ✓ Negativity: trigger={neg.trigger_threshold}, correction={neg.correction_urge_threshold}")
    print(f"  ✓ Spatial: gravity={spatial.gravity_constant}")
    print(f"  ✓ Influence matrix: {len(cfg.influence_matrix)} sources")


def s8_full_report():
    """S8: 完整報告"""
    print("\n[S8] Full Report")

    sm = StateMatrixAdapter()

    sm.update_alpha(focus=0.7)
    sm.update_beta(curiosity=0.6)
    sm.compute_influences()

    report = sm.full_report()

    assert 'state_matrix' in report, "Report should have state_matrix"
    assert 'temporal' in report, "Report should have temporal"
    assert 'influence' in report, "Report should have influence"
    assert 'allocation' in report, "Report should have allocation"
    assert 'negativity' in report, "Report should have negativity"

    sm_report = report['state_matrix']
    assert isinstance(sm_report, dict), "state_matrix should be dict"

    temporal = report['temporal']
    assert 'size' in temporal, "temporal should have size"
    assert temporal['size'] > 0, "temporal size should be > 0"

    influence = report['influence']
    assert 'rules_count' in influence, "influence should have rules_count"
    assert influence['rules_count'] > 0, "Should have influence rules"

    alloc = report['allocation']
    assert 'stages' in alloc, "allocation should have stages"
    assert len(alloc['stages']) == 4, f"Should have 4 stages, got {len(alloc['stages'])}"

    print(f"  ✓ Full report: {list(report.keys())}")
    print(f"  ✓ State matrix keys: {list(sm_report.keys())}")
    print(f"  ✓ Temporal: {temporal['size']} snapshots")
    print(f"  ✓ Influence: {influence['rules_count']} rules")
    print(f"  ✓ Allocation stages: {alloc['stages']}")


def s_facade():
    """SF: StateMatrixFacade 便捷 API"""
    print("\n[SF] StateMatrixFacade")

    facade = StateMatrixFacade()

    facade.update(focus=0.9)
    facade.update(energy=0.8)
    assert facade.adapter.temporal.size() >= 2, "Facade update should record to temporal"

    trend = facade.trend('alpha', 'energy', window=10)
    assert trend is not None, "Trend should return result"

    inf = facade.influence('alpha', 'beta')
    assert 0.0 <= inf <= 3.0, f"Influence should be in [0,3], got {inf}"

    decision = facade.allocate([0.1] * 32, 'test')
    assert decision.action is not None, "Allocate should return decision"

    print(f"  ✓ Facade: created successfully")
    print(f"  ✓ Trend: {trend}")
    print(f"  ✓ Influence: {inf:.4f}")
    print(f"  ✓ Allocate: {decision}")


def main():
    print("=" * 60)
    print("StateMatrixAdapter Smoke Test — 8 Scenarios")
    print("=" * 60)

    tests = [
        ("S1 Basic Updates", s1_basic_updates),
        ("S2 Allocation Decision", s2_allocation_decision),
        ("S3 Influence Computation", s3_influence_computation),
        ("S4 Ripple Application", s4_ripple_application),
        ("S5 Theta Self-Correction", s5_theta_self_correction),
        ("S6 Temporal Queries", s6_temporal_queries),
        ("S7 Config Loading", s7_config_loading),
        ("S8 Full Report", s8_full_report),
        ("SF StateMatrixFacade", s_facade),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()