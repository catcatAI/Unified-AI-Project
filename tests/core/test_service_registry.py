"""C4 — ServiceRegistry unit tests"""

import sys
sys.path.insert(0, 'apps/backend/src')


class TestServiceRegistry:

    def setup_method(self):
        from core.interfaces.service_registry import ServiceRegistry
        self.r = ServiceRegistry()

    def test_register_and_get(self):
        self.r.register('test_svc', {'hello': 'world'})
        svc = self.r.get('test_svc')
        assert svc == {'hello': 'world'}

    def test_get_nonexistent(self):
        svc = self.r.get('no_such_service')
        assert svc is None

    def test_register_twice_overwrites(self):
        self.r.register('svc', 'first')
        self.r.register('svc', 'second')
        assert self.r.get('svc') == 'second'

    def test_unregister(self):
        self.r.register('svc', 'value')
        self.r.unregister('svc')
        assert self.r.get('svc') is None

    def test_unregister_nonexistent(self):
        self.r.unregister('no_such')  # no crash

    def test_clear(self):
        self.r.register('a', 1)
        self.r.register('b', 2)
        self.r.clear()
        assert self.r.get('a') is None
        assert self.r.get('b') is None

    def test_service_names(self):
        self.r.register('x', 1)
        self.r.register('y', 2)
        assert sorted(self.r.service_names) == ['x', 'y']

    def test_type_check_pass(self):
        self.r.register('num', 42)
        svc = self.r.get('num', expected_type=int)
        assert svc == 42

    def test_type_check_mismatch(self):
        self.r.register('text', 'hello')
        svc = self.r.get('text', expected_type=int)
        assert svc == 'hello'  # returns value despite mismatch (only warns)

    def test_get_registry_returns_singleton(self):
        from core.interfaces.service_registry import get_registry
        r1 = get_registry()
        r2 = get_registry()
        assert r1 is r2

    def test_empty_registry(self):
        assert self.r.service_names == []
