"""
Unit Tests — CodeInspector Integration
========================================

Author: Angela AI v6.2
"""

import sys
sys.path.insert(0, 'apps/backend/src')

from core.autonomous.state_matrix_adapter import StateMatrixAdapter
from ai.code_inspection.code_inspector_integration import (
    CodeInspectorBridge, create_bridge,
)


def test_bridge_creation():
    adapter = StateMatrixAdapter()
    bridge = CodeInspectorBridge(adapter)
    assert bridge._adapter is adapter


def test_factory():
    adapter = StateMatrixAdapter()
    bridge = create_bridge(adapter)
    assert isinstance(bridge, CodeInspectorBridge)


def test_compute_complexity():
    adapter = StateMatrixAdapter()
    bridge = CodeInspectorBridge(adapter)

    result = bridge._compute_complexity({
        'critical': 2, 'high': 3, 'medium': 10, 'low': 20,
    })
    assert 0.0 <= result <= 1.0
    assert result > 0


def test_compute_stability():
    adapter = StateMatrixAdapter()
    bridge = CodeInspectorBridge(adapter)

    stability = bridge._compute_stability(critical=0, high=0)
    assert stability == 1.0

    stability = bridge._compute_stability(critical=2, high=5)
    assert stability < 1.0


def test_compute_clarity():
    adapter = StateMatrixAdapter()
    bridge = CodeInspectorBridge(adapter)

    clarity = bridge._compute_clarity(medium=0, low=0)
    assert clarity == 1.0

    clarity = bridge._compute_clarity(medium=20, low=30)
    assert clarity < 1.0


def test_build_issue_vector():
    adapter = StateMatrixAdapter()
    bridge = CodeInspectorBridge(adapter)

    vector = bridge._build_issue_vector(total=10, critical=2, complexity=0.5)
    assert len(vector) == 32
    assert vector[0] > 0
    assert vector[1] > 0
    assert vector[2] == 0.5
    assert vector[3] == 1.0


def test_category_to_axis():
    adapter = StateMatrixAdapter()
    bridge = CodeInspectorBridge(adapter)

    assert bridge.CATEGORY_TO_AXIS['security'] == 'alpha'
    assert bridge.CATEGORY_TO_AXIS['logic'] == 'epsilon'
    assert bridge.CATEGORY_TO_AXIS['type'] == 'beta'


def test_complexity_weights():
    adapter = StateMatrixAdapter()
    bridge = CodeInspectorBridge(adapter)

    assert bridge.COMPLEXITY_WEIGHTS['critical'] > bridge.COMPLEXITY_WEIGHTS['high']
    assert bridge.COMPLEXITY_WEIGHTS['high'] > bridge.COMPLEXITY_WEIGHTS['medium']


if __name__ == '__main__':
    tests = [
        test_bridge_creation,
        test_factory,
        test_compute_complexity,
        test_compute_stability,
        test_compute_clarity,
        test_build_issue_vector,
        test_category_to_axis,
        test_complexity_weights,
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
    print(f"\nCodeInspectorBridge: {passed} passed, {failed} failed")