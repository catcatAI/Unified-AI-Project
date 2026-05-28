"""C3 — HookRegistry unit tests"""

import asyncio


class TestHookRegistry:

    def setup_method(self):
        from core.plugin.hook_registry import HookRegistry
        self.r = HookRegistry()

    def test_define_and_get_hook(self):
        self.r.define_hook('test_hook', 'A test hook')
        hook = self.r.get_hook('test_hook')
        assert hook is not None
        assert hook.name == 'test_hook'
        assert hook.description == 'A test hook'

    def test_unknown_hook_returns_none(self):
        assert self.r.get_hook('nonexistent') is None

    def test_register_handler(self):
        self.r.define_hook('test_hook')
        ok = self.r.register_handler('test_hook', 'handler1', lambda d: d)
        assert ok is True

    def test_register_handler_auto_defines_hook(self):
        ok = self.r.register_handler('unknown_hook', 'h1', lambda d: d)
        assert ok is True
        assert self.r.get_hook('unknown_hook') is not None

    def test_unregister_handler(self):
        self.r.define_hook('test_hook')
        self.r.register_handler('test_hook', 'h1', lambda d: d)
        assert self.r.unregister_handler('test_hook', 'h1') is True
        assert self.r.unregister_handler('test_hook', 'nonexistent') is False

    def test_execute_hook_sync(self):
        self.r.define_hook('greet')
        self.r.register_handler('greet', 'h1', lambda d: f'Hello {d}')
        results = asyncio.run(self.r.execute_hook('greet', 'world'))
        assert len(results) == 1
        assert results[0].success is True
        assert results[0].result == 'Hello world'
        assert results[0].handler_name == 'h1'

    def test_execute_hook_no_handlers(self):
        self.r.define_hook('empty')
        results = asyncio.run(self.r.execute_hook('empty'))
        assert results == []

    def test_execute_hook_handler_error(self):
        self.r.define_hook('failing')
        def _fail(d):
            raise ValueError('oops')
        self.r.register_handler('failing', 'fail_h', _fail)
        results = asyncio.run(self.r.execute_hook('failing', 'x'))
        assert len(results) == 1
        assert results[0].success is False
        assert 'oops' in results[0].error

    def test_list_hooks(self):
        self.r.define_hook('a', 'desc a')
        self.r.define_hook('b', 'desc b')
        hooks = self.r.list_hooks()
        assert len(hooks) == 2
        names = {h['name'] for h in hooks}
        assert names == {'a', 'b'}

    def test_get_stats(self):
        self.r.define_hook('hook1', 'd1')
        self.r.register_handler('hook1', 'h1', lambda: None)
        stats = self.r.get_stats()
        assert stats['hook_count'] >= 1
        assert stats['handler_count'] >= 1
