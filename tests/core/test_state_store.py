"""C5 — GlobalStateStore persistence unit tests"""

import sys, asyncio, os
sys.path.insert(0, 'apps/backend/src')


class TestGlobalStateStore:

    def setup_method(self):
        from core.system.state_store.global_store import GlobalStateStore
        self.store = GlobalStateStore()

    def test_update_and_get_state(self):
        self.store.update_state('alpha', {'energy': 0.8, 'stress': 0.2})
        state = self.store.get_state('alpha')
        assert state['energy'] == 0.8
        assert state['stress'] == 0.2

    def test_get_unknown_domain_returns_empty(self):
        state = self.store.get_state('nonexistent')
        assert state == {}

    def test_subscribe_and_notify(self):
        results = []
        def cb(domain, data):
            results.append((domain, data.get('val')))
        self.store.subscribe('beta', cb)
        self.store.update_state('beta', {'val': 42})
        assert len(results) == 1
        assert results[0] == ('beta', 42)

    def test_subscribe_global(self):
        results = []
        def cb(domain, data):
            results.append(domain)
        self.store.subscribe('_global', cb)
        self.store.update_state('alpha', {'test': 1})
        assert len(results) == 1

    def test_get_all_state(self):
        self.store.update_state('alpha', {'a': 1})
        self.store.update_state('beta', {'b': 2})
        all_state = self.store.get_state()
        assert 'alpha' in all_state
        assert 'beta' in all_state

    def test_dirty_tracking(self):
        assert self.store.is_dirty() is False
        self.store.update_state('alpha', {'x': 1})
        assert self.store.is_dirty('alpha') is True

    def test_persistence_save_domain(self):
        from core.interfaces.persistence import JsonFileStateStore
        self.store.set_persistence(JsonFileStateStore('data/test_state/'))
        self.store.update_state('alpha', {'test_val': 0.42})
        ok = asyncio.run(self.store.save_domain('alpha'))
        assert ok is True
        assert os.path.exists('data/test_state/domain_alpha.json')
        # Cleanup
        import shutil
        shutil.rmtree('data/test_state', ignore_errors=True)

    def test_persistence_round_trip(self):
        from core.interfaces.persistence import JsonFileStateStore
        self.store.set_persistence(JsonFileStateStore('data/test_state/'))
        self.store.update_state('alpha', {'round_trip': 99})
        asyncio.run(self.store.save_all())
        # Load into fresh store
        s2 = __import__('core.system.state_store.global_store', fromlist=['GlobalStateStore']).GlobalStateStore()
        s2.set_persistence(JsonFileStateStore('data/test_state/'))
        ok = asyncio.run(s2.load_domain('alpha'))
        assert ok is True
        assert s2.get_state('alpha').get('round_trip') == 99
        import shutil
        shutil.rmtree('data/test_state', ignore_errors=True)
