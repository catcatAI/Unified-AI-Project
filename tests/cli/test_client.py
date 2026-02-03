"""
Tests for the Unified AI Client.
"""

import pytest
from unittest.mock import MagicMock

# Corrected import path
from packages.cli.client import UnifiedAIClient

class DummyResp:
    """A dummy response object to mock requests.Response."""
    def __init__(self, status_code=200, payload=None, text=''):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if self._payload is None:
            raise ValueError('No JSON payload')
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP Error: {self.status_code}")

def test_client_base_url_env(monkeypatch):
    """Tests that the client correctly uses the CLI_BASE_URL environment variable."""
    monkeypatch.setenv('CLI_BASE_URL', 'http://example.com:9999')
    client = UnifiedAIClient()
    assert client.base_url == 'http://example.com:9999'

def test_health_check_success(monkeypatch):
    """Tests a successful health check."""
    mock_get = MagicMock(return_value=DummyResp(200, {'status': 'healthy'}))
    monkeypatch.setattr("requests.get", mock_get)

    client = UnifiedAIClient(base_url='http://localhost:8000')
    response = client.health_check()
    
    assert response.get('status') == 'healthy'
    mock_get.assert_called_once_with('http://localhost:8000/api/v1/health', timeout=5)

def test_chat_error_to_dict(monkeypatch):
    """Tests that a non-200 response from the chat endpoint returns a dict with an error."""
    mock_post = MagicMock(return_value=DummyResp(500, None, text='Internal Server Error'))
    monkeypatch.setattr("requests.post", mock_post)

    client = UnifiedAIClient(base_url='http://localhost:8000')
    response = client.chat('hi')
    
    assert 'error' in response
    assert 'Internal Server Error' in response['error']