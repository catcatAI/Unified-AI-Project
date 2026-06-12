"""
Unit Tests — SelfIntrospectorV2 (N.22.6)
=========================================

Author: Angela AI v6.2
"""


try:
    from core.engine.state_matrix_adapter import StateMatrixAdapter
except ImportError:
    import pytest; pytest.skip("StateMatrixAdapter is a stub", allow_module_level=True)
try:
    from core.autonomous.self_introspector_v2 import SelfIntrospectorV2
except ImportError:
    import pytest; pytest.skip("SelfIntrospectorV2 not implemented", allow_module_level=True)


def test_record_wellbeing():
    adapter = StateMatrixAdapter()
    insp = SelfIntrospectorV2(adapter)

    insp.record_wellbeing(0.8, {'context': 'test'})
    insp.record_wellbeing(0.7)
    insp.record_wellbeing(0.6)

    assert adapter.temporal.size() == 3


def test_mental_health_check_trend():
    adapter = StateMatrixAdapter()
    insp = SelfIntrospectorV2(adapter)

    for w in [0.5, 0.52, 0.54, 0.56, 0.58, 0.60, 0.62, 0.64, 0.66, 0.68]:
        insp.record_wellbeing(w)

    state = {'wellbeing': 0.7, 'arousal': 0.5, 'stress_level': 0.1, 'valence': 0.0}
    report = insp.perform_mental_health_check(state, {})

    assert report['status'] in ('healthy', 'strained')
    assert 'wellbeing_trend' in report


def test_mental_health_check_critical():
    adapter = StateMatrixAdapter()
    insp = SelfIntrospectorV2(adapter)

    state = {'wellbeing': 0.1, 'arousal': 0.9, 'stress_level': 0.9, 'valence': -0.5}
    report = insp.perform_mental_health_check(state, {})

    assert report['status'] == 'strained'
    assert 'CRITICAL_STRESS_LEVEL' in report['anomalies']


def test_intent_alignment_proceed():
    adapter = StateMatrixAdapter()
    insp = SelfIntrospectorV2(adapter)

    result = insp.check_intent_alignment_v2(
        action_name='test_action',
        action_vector=[0.1, 0.1, 0.1],
        current_coord=[0.5, 0.5, 0.5],
        intent_target=[0.6, 0.6, 0.6],
    )

    assert 'alignment' in result
    assert 'dissonance_score' in result
    assert 'is_conflicting' in result
    assert result['decision_override'] in ('PROCEED', 'THROTTLE')


def test_intent_alignment_throttle():
    adapter = StateMatrixAdapter()
    insp = SelfIntrospectorV2(adapter, dissonance_threshold=0.1)

    result = insp.check_intent_alignment_v2(
        action_name='big_action',
        action_vector=[1.0, 1.0, 1.0],
        current_coord=[0.0, 0.0, 0.0],
        intent_target=[1.0, 1.0, 1.0],
    )

    assert 'is_conflicting' in result


def test_cognitive_dissonance():
    adapter = StateMatrixAdapter()
    insp = SelfIntrospectorV2(adapter)

    expected = {'focus': 0.8, 'energy': 0.7}
    actual = {'focus': 0.3, 'energy': 0.9}

    result = insp.detect_cognitive_dissonance(expected, actual)

    assert 'dissonance_score' in result
    assert result['dissonance_score'] > 0
    assert 'needs_correction' in result


def test_adapt_threshold():
    adapter = StateMatrixAdapter()
    insp = SelfIntrospectorV2(adapter, dissonance_threshold=0.6)

    insp.adapt_dissonance_threshold(post_wellbeing=0.7, pre_wellbeing=0.5)
    assert insp._dissonance_threshold >= 0.6

    insp.adapt_dissonance_threshold(post_wellbeing=0.3, pre_wellbeing=0.7)
    assert insp._dissonance_threshold <= 0.65


def test_wellbeing_report():
    adapter = StateMatrixAdapter()
    insp = SelfIntrospectorV2(adapter)

    for w in [0.5 + i * 0.01 for i in range(20)]:
        insp.record_wellbeing(w)

    report = insp.get_wellbeing_report(window=20)

    assert 'trend' in report
    assert 'self_correlation' in report
    assert 'anomalies_count' in report
    assert report['trend']['direction'] in ('rising', 'stable')


if __name__ == '__main__':
    tests = [
        test_record_wellbeing,
        test_mental_health_check_trend,
        test_mental_health_check_critical,
        test_intent_alignment_proceed,
        test_intent_alignment_throttle,
        test_cognitive_dissonance,
        test_adapt_threshold,
        test_wellbeing_report,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"FAIL {t.__name__}: {e}")
            failed += 1
    print(f"\nSelfIntrospectorV2: {passed} passed, {failed} failed")