"""
Unit Tests — TemporalState
===========================

Author: Angela AI v6.2
"""


from core.state.temporal import TemporalState, SnapshotQuery, TrendResult, AnomalyResult, CorrelationResult


def test_record_and_get():
    tl = TemporalState(max_size=100)
    idx = tl.record({'alpha': {'focus': 0.8}, 'beta': {'curiosity': 0.6}})
    assert idx == 0
    assert tl.size() == 1

    idx2 = tl.record({'alpha': {'focus': 0.9}})
    assert idx2 == 1
    assert tl.size() == 2

    snap = tl.get_at(0)
    assert snap is not None
    assert snap['alpha']['focus'] == 0.8

    snap2 = tl.get_at(-1)
    assert snap2 is not None
    assert snap2['alpha']['focus'] == 0.9


def test_negative_index():
    tl = TemporalState()
    for i in range(5):
        tl.record({'value': float(i)})
    assert tl.get_at(-1)['value'] == 4.0
    assert tl.get_at(-2)['value'] == 3.0
    assert tl.get_at(-5)['value'] == 0.0
    assert tl.get_at(-6) is None


def test_recent():
    tl = TemporalState(max_size=200)
    for i in range(60):
        tl.record({'index': i})
    recent = tl.recent(fraction=0.2)
    assert len(recent) == 12


def test_trend_rising():
    tl = TemporalState()
    for i in range(50):
        tl.record({'alpha': {'energy': 0.3 + i * 0.01}})
    trend = tl.trend('alpha', 'energy', window=50)
    assert trend.direction in ('rising', 'stable')
    assert trend.mean > 0.3


def test_trend_insufficient_data():
    tl = TemporalState()
    tl.record({'alpha': {'energy': 0.5}})
    trend = tl.trend('alpha', 'energy', window=50)
    assert trend.direction == 'insufficient_data'


def test_anomalies():
    tl = TemporalState()
    for i in range(50):
        tl.record({'alpha': {'focus': 0.5}})
    tl.record({'alpha': {'focus': 0.99}})
    anomalies = tl.anomalies('alpha', 'focus', threshold=0.5, window=50)
    assert len(anomalies) >= 1


def test_correlation():
    tl = TemporalState()
    for i in range(50):
        tl.record({'alpha': {'focus': 0.3 + i * 0.01}, 'beta': {'focus': 0.3 + i * 0.01}})
    corr = tl.correlation('alpha', 'focus', 'beta', 'focus', window=50)
    assert abs(corr.correlation) > 0.9
    assert corr.strength in ('strong', 'moderate')


def test_find_drift():
    tl = TemporalState()
    for i in range(30):
        tl.record({'alpha': {'energy': 0.5}})
    tl.record({'alpha': {'energy': 0.9}})
    drift = tl.find_drift('alpha', 'energy', expected_value=0.5, drift_threshold=0.3)
    assert len(drift) >= 1


def test_query_by_axis():
    tl = TemporalState()
    for i in range(20):
        tl.record({'alpha': {'focus': 0.5 + i * 0.01}, 'beta': {'curiosity': 0.5}})
    result = tl.query(SnapshotQuery(axes=['alpha'], limit=5))
    assert len(result) <= 5
    for snap in result:
        assert 'alpha' in snap


def test_query_by_field():
    tl = TemporalState()
    for i in range(20):
        tl.record({'alpha': {'focus': 0.5 + i * 0.01}, 'beta': {'curiosity': 0.5}})
    result = tl.query(SnapshotQuery(fields=['focus'], limit=5))
    assert len(result) <= 5


def test_max_size_eviction():
    tl = TemporalState(max_size=10)
    for i in range(20):
        tl.record({'index': i})
    assert tl.size() == 10
    oldest = tl.get_at(0)
    assert oldest['index'] == 10


def test_clear():
    tl = TemporalState()
    for i in range(10):
        tl.record({'value': i})
    tl.clear()
    assert tl.size() == 0
    assert tl.is_empty()


def test_callback():
    tl = TemporalState()
    captured = []

    def callback(snap):
        captured.append(snap.get('value'))

    tl.on_record(callback)
    tl.record({'value': 1})
    tl.record({'value': 2})
    assert len(captured) == 2
    assert captured == [1, 2]


def test_empty_temporal():
    tl = TemporalState()
    assert tl.is_empty()
    assert tl.size() == 0
    assert tl.get_at(0) is None
    assert tl.get_field_series('alpha', 'focus', 10) == []


if __name__ == '__main__':
    tests = [
        test_record_and_get,
        test_negative_index,
        test_recent,
        test_trend_rising,
        test_trend_insufficient_data,
        test_anomalies,
        test_correlation,
        test_find_drift,
        test_query_by_axis,
        test_query_by_field,
        test_max_size_eviction,
        test_clear,
        test_callback,
        test_empty_temporal,
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
    print(f"\nTemporalState: {passed} passed, {failed} failed")