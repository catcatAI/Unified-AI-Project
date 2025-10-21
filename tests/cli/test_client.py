"""
测试模块 - test_client

自动生成的测试模块,用于验证系统功能。
"""

import os
import json
import types
import builtins
import importlib
from cli.client import UnifiedAIClient

class DummyResp:
    def __init__(self, status_code=200, payload=None, text=''):
        self.status_code = status_code
        self._payload = payload
        self.text = text
    def json(self):
        if self._payload is None:
            raise ValueError('no json')
        return self._payload
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")



    def setUp(self):
        """测试前设置"""
        self.test_data = {}
        self.test_config = {}
    
    def tearDown(self):
        """测试后清理"""
        self.test_data.clear()
        self.test_config.clear()
def test_client_base_url_env(monkeypatch):
    monkeypatch.setenv('CLI_BASE_URL', 'http://example.com:9999')
    c = UnifiedAIClient()
    assert c.base_url == 'http://example.com:9999'


def test_health_check_success(monkeypatch):
    calls = {}
    def fake_get(url, headers=None, params=None, timeout=None):
        calls['url'] = url
        return DummyResp(200, { 'status': 'healthy' })
    import requests
    monkeypatch.setattr(requests, 'get', fake_get)

    c = UnifiedAIClient(base_url='http://localhost:8000')
    res = c.health_check()
    assert res.get('status') == 'healthy'
    assert calls['url'].endswith('/api/v1/health')


def test_chat_error_to_dict(monkeypatch):
    def fake_post(url, headers=None, json=None, params=None, timeout=None):
        return DummyResp(500, None, text='server error')
    import requests
    monkeypatch.setattr(requests, 'post', fake_post)

    c = UnifiedAIClient(base_url='http://localhost:8000')
    res = c.chat('hi')
    assert 'error' in res
