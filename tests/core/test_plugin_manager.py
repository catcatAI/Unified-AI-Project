"""C3 — PluginManager unit tests"""



class TestPluginManager:

    def setup_method(self):
        from core.plugin.hook_registry import HookRegistry
        from core.plugin.plugin_manager import PluginManager
        self.r = HookRegistry()
        self.pm = PluginManager(self.r)

    def test_register_plugin(self):
        info = self.pm.register_plugin('my_plugin', '1.0', 'Test plugin')
        assert info.name == 'my_plugin'
        assert info.version == '1.0'
        assert info.description == 'Test plugin'
        assert info.enabled is True

    def test_get_plugin(self):
        self.pm.register_plugin('p1', '1.0')
        assert self.pm.get_plugin('p1') is not None
        assert self.pm.get_plugin('nonexistent') is None

    def test_enable_disable_plugin(self):
        self.pm.register_plugin('p1', '1.0')
        assert self.pm.get_plugin('p1').enabled is True
        self.pm.disable_plugin('p1')
        assert self.pm.get_plugin('p1').enabled is False
        self.pm.enable_plugin('p1')
        assert self.pm.get_plugin('p1').enabled is True

    def test_enable_disable_nonexistent(self):
        assert self.pm.enable_plugin('nope') is False
        assert self.pm.disable_plugin('nope') is False

    def test_unregister_plugin(self):
        self.pm.register_plugin('p1', '1.0')
        assert self.pm.unregister_plugin('p1') is True
        assert self.pm.unregister_plugin('p1') is False

    def test_list_plugins(self):
        self.pm.register_plugin('a', '1.0')
        self.pm.register_plugin('b', '2.0')
        plugins = self.pm.list_plugins()
        assert len(plugins) == 2
        names = {p['name'] for p in plugins}
        assert names == {'a', 'b'}

    def test_list_plugins_enabled_only(self):
        self.pm.register_plugin('a', '1.0')
        self.pm.register_plugin('b', '2.0')
        self.pm.disable_plugin('b')
        plugins = self.pm.list_plugins(enabled_only=True)
        assert len(plugins) == 1
        assert plugins[0]['name'] == 'a'

    def test_add_handler(self):
        self.pm.register_plugin('p1', '1.0')
        ok = self.pm.add_handler('p1', 'on_message', lambda d: d)
        assert ok is True
        info = self.pm.get_plugin('p1')
        assert 'on_message' in info.hooks

    def test_add_handler_unknown_plugin(self):
        ok = self.pm.add_handler('unknown', 'on_message', lambda d: d)
        assert ok is False

    def test_execute_hook_via_manager(self):
        import asyncio
        self.pm.register_plugin('p1', '1.0')
        self.pm.add_handler('p1', 'on_message', lambda d: f'handled: {d}')
        results = asyncio.run(self.pm.execute_hook('on_message', 'test'))
        assert len(results) == 1
        assert results[0].result == 'handled: test'

    def test_standard_hooks_defined(self):
        for name in ['on_message', 'on_response', 'on_state_change', 'on_bio_event', 'on_tick']:
            assert self.r.get_hook(name) is not None, f'{name} not defined'

    def test_get_stats(self):
        self.pm.register_plugin('p1', '1.0')
        stats = self.pm.get_stats()
        assert stats['plugin_count'] == 1
        assert stats['enabled_count'] == 1
        assert 'hook_registry' in stats
