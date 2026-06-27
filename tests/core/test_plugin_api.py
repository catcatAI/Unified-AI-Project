"""C4+C3 — Plugin API endpoint integration tests"""

import asyncio
import json
import os
import shutil
import tempfile

from fastapi.testclient import TestClient


class TestPluginAPI:

    def setup_method(self):
        from api.v1.endpoints.plugins import router
        from core.plugin.hook_registry import HookRegistry
        from core.plugin.plugin_manager import PluginManager
        from fastapi import FastAPI

        self.r = HookRegistry()
        self.pm = PluginManager(self.r)

        import api.v1.endpoints.plugins as ep_mod
        ep_mod.hook_registry = self.r
        ep_mod.plugin_manager = self.pm

        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

        self._tmp = None

    def teardown_method(self):
        if self._tmp and os.path.exists(self._tmp):
            shutil.rmtree(self._tmp, ignore_errors=True)

    def test_list_hooks(self):
        resp = self.client.get('/plugins/hooks')
        assert resp.status_code == 200
        data = resp.json()
        assert 'hooks' in data
        assert len(data['hooks']) >= 5

    def test_list_plugins_empty(self):
        resp = self.client.get('/plugins/plugins')
        assert resp.status_code == 200
        assert resp.json()['plugins'] == []

    def test_register_plugin(self):
        resp = self.client.post('/plugins/register?name=test_plugin&version=2.0&description=A test plugin')
        assert resp.status_code == 200
        data = resp.json()
        assert data['status'] == 'registered'
        assert data['name'] == 'test_plugin'
        assert data['version'] == '2.0'

    def test_register_then_list(self):
        self.client.post('/plugins/register?name=p1')
        resp = self.client.get('/plugins/plugins')
        plugins = resp.json()['plugins']
        assert len(plugins) == 1
        assert plugins[0]['name'] == 'p1'

    def test_enable_plugin(self):
        self.client.post('/plugins/register?name=p1')
        resp = self.client.post('/plugins/plugins/p1/enable')
        assert resp.status_code == 200

    def test_disable_plugin(self):
        self.client.post('/plugins/register?name=p1')
        resp = self.client.post('/plugins/plugins/p1/disable')
        assert resp.status_code == 200
        resp = self.client.get('/plugins/plugins?enabled_only=true')
        assert resp.json()['plugins'] == []

    def test_enable_nonexistent_returns_404(self):
        resp = self.client.post('/plugins/plugins/nope/enable')
        assert resp.status_code == 404

    def test_disable_nonexistent_returns_404(self):
        resp = self.client.post('/plugins/plugins/nope/disable')
        assert resp.status_code == 404

    def test_execute_hook_no_handlers(self):
        self.client.post('/plugins/register?name=p1')
        resp = self.client.post('/plugins/hooks/on_message/execute', json={})
        assert resp.status_code == 200
        assert resp.json()['results'] == []

    def test_execute_hook_with_handler(self):
        self.client.post('/plugins/register?name=p1')
        self.pm.add_handler('p1', 'on_message', lambda d: f'echo: {d}')
        resp = self.client.post('/plugins/hooks/on_message/execute', json={'text': 'hello'})
        assert resp.status_code == 200
        results = resp.json()['results']
        assert len(results) == 1
        assert results[0]['success'] is True
        assert 'echo' in results[0]['result']

    def test_execute_nonexistent_hook_returns_404(self):
        resp = self.client.post('/plugins/hooks/bad_hook/execute', json={})
        assert resp.status_code == 404

    def test_plugin_stats(self):
        self.client.post('/plugins/register?name=p1')
        resp = self.client.get('/plugins/stats')
        assert resp.status_code == 200
        assert resp.json()['plugin_count'] == 1

    def test_plugin_stats_empty(self):
        resp = self.client.get('/plugins/stats')
        assert resp.status_code == 200
        assert resp.json()['plugin_count'] == 0

    def test_data_persistence_set_and_get(self):
        resp = self.client.post('/plugins/data/my_plugin', json={'key1': 'val1', 'key2': 42})
        assert resp.status_code == 200
        assert resp.json()['status'] == 'stored'

        resp = self.client.get('/plugins/data/my_plugin')
        assert resp.status_code == 200
        data = resp.json()
        assert data['plugin'] == 'my_plugin'
        assert len(data['data']) >= 1

    def test_data_persistence_delete(self):
        self.client.post('/plugins/data/my_plugin', json={'del_key': 'to_delete'})
        resp = self.client.delete('/plugins/data/my_plugin/del_key')
        assert resp.status_code == 200
        assert resp.json()['status'] == 'deleted'

    def test_data_empty_get(self):
        resp = self.client.get('/plugins/data/no_data_plugin')
        assert resp.status_code == 200
        assert resp.json()['data'] == {}

    def test_register_with_empty_description(self):
        resp = self.client.post('/plugins/register?name=minimal&version=1.0&description=')
        assert resp.status_code == 200
        assert resp.json()['name'] == 'minimal'

    def test_enabled_only_filter(self):
        self.client.post('/plugins/register?name=p1')
        self.client.post('/plugins/register?name=p2')
        self.client.post('/plugins/plugins/p2/disable')
        resp = self.client.get('/plugins/plugins?enabled_only=true')
        assert len(resp.json()['plugins']) == 1
        assert resp.json()['plugins'][0]['name'] == 'p1'

