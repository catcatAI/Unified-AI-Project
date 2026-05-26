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

    def test_no_persistence_returns_false(self):
        self.store._persistence = None
        ok = asyncio.run(self.store.save_domain('alpha'))
        assert ok is False
        ok = asyncio.run(self.store.load_domain('alpha'))
        assert ok is False
        cnt = asyncio.run(self.store.save_all())
        assert cnt == 0
        cnt = asyncio.run(self.store.load_all())
        assert cnt == 0

    def test_save_all_dirty_tracking(self):
        from core.interfaces.persistence import JsonFileStateStore
        self.store.set_persistence(JsonFileStateStore('data/test_state/'))
        self.store.update_state('alpha', {'x': 1})
        self.store.update_state('beta', {'y': 2})
        assert self.store.is_dirty() is True
        cnt = asyncio.run(self.store.save_all())
        assert cnt >= 2
        assert self.store.is_dirty() is False
        import shutil
        shutil.rmtree('data/test_state', ignore_errors=True)

    def test_update_unknown_domain(self):
        self.store.update_state('unknown_domain', {'test': 1})
        state = self.store.get_state('unknown_domain')
        assert state.get('test') == 1

    def test_subscriber_error_does_not_crash(self):
        def bad_cb(domain, data):
            raise ValueError('subscriber error')
        self.store.subscribe('alpha', bad_cb)
        self.store.update_state('alpha', {'x': 1})
        # No crash = pass

    def test_concurrent_updates(self):
        import asyncio
        async def update_many():
            tasks = []
            for i in range(10):
                tasks.append(asyncio.to_thread(self.store.update_state, 'alpha', {f'k{i}': i}))
            await asyncio.gather(*tasks)
        asyncio.run(update_many())
        state = self.store.get_state('alpha')
        keys_found = sum(1 for k in state if k.startswith('k'))
        assert keys_found >= 1

    def test_neuro_vocabulary_domain_registered(self):
        state = self.store.get_state()
        assert 'neuro_vocabulary' in state

