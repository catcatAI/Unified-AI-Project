"""
Unit Tests — InfluenceApplicator
================================

Author: Angela AI v6.2
"""


from core.engine.influence_applicator import (
    INFLUENCE_RULES,
    InfluenceApplicator,
    apply_influence_to_axis,
    get_applicator,
)


def test_applicator_basic():
    class MockDim:
        def __init__(self):
            self.values = {'focus': 0.5, 'clarity': 0.5, 'energy': 0.5}

    source = MockDim()
    target = MockDim()
    applier = InfluenceApplicator()

    applier.apply('alpha', 'beta', source, target, amount=0.1)
    assert target.values['focus'] > 0.5
    assert target.values['clarity'] > 0.5


def test_applicator_gamma_to_alpha():
    class MockDim:
        def __init__(self):
            self.values = {'energy': 0.5, 'comfort': 0.5, 'tension': 0.0}

    source = MockDim()
    source.values['happiness'] = 0.8
    target = MockDim()
    applier = InfluenceApplicator()

    applier.apply('gamma', 'alpha', source, target, amount=0.1)
    assert target.values['energy'] > 0.5


def test_applicator_no_rule():
    class MockDim:
        def __init__(self):
            self.values = {'focus': 0.5}

    source = MockDim()
    target = MockDim()
    original = target.values['focus']
    applier = InfluenceApplicator()

    applier.apply('epsilon', 'theta', source, target, amount=0.1)
    assert target.values['focus'] == original


def test_apply_influence_to_axis():
    class MockDim:
        def __init__(self):
            self.values = {'focus': 0.5}

    target = MockDim()
    source = {'focus': 0.8, 'clarity': 0.6}
    rules = [('focus', 'focus', 0.1)]

    apply_influence_to_axis(source, target, rules)
    assert target.values['focus'] > 0.5


def test_global_applicator_singleton():
    a = get_applicator()
    b = get_applicator()
    assert a is b


def test_custom_rules():
    class MockDim:
        def __init__(self):
            self.values = {'focus': 0.5}

    source = MockDim()
    source.values['happiness'] = 0.9
    target = MockDim()
    custom = {'gamma': {'alpha': [('happiness', 'energy', 0.5)]}}
    applier = InfluenceApplicator(rules=custom)

    applier.apply('gamma', 'alpha', source, target, amount=1.0)
    assert target.values['energy'] > 0.5


def test_influence_rules_structure():
    assert 'alpha' in INFLUENCE_RULES
    assert 'beta' in INFLUENCE_RULES
    assert 'gamma' in INFLUENCE_RULES
    assert 'delta' in INFLUENCE_RULES
    assert INFLUENCE_RULES['alpha']['beta']
    assert INFLUENCE_RULES['gamma']['alpha']


if __name__ == '__main__':
    tests = [
        test_applicator_basic,
        test_applicator_gamma_to_alpha,
        test_applicator_no_rule,
        test_apply_influence_to_axis,
        test_global_applicator_singleton,
        test_custom_rules,
        test_influence_rules_structure,
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
    print(f"\nInfluenceApplicator: {passed} passed, {failed} failed")