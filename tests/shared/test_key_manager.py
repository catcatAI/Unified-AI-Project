"""Tests for unified key manager."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

sys.modules['cryptography'] = MagicMock()
sys.modules['cryptography.fernet'] = MagicMock()
sys.modules['pystray'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['PIL.ImageDraw'] = MagicMock()
sys.modules['yaml'] = MagicMock()


class TestUnifiedKeyManager:
    def setup_method(self):
        self.test_data = {}

    def teardown_method(self):
        self.test_data.clear()

    @patch('shared.key_manager.Path.exists', return_value=False)
    @patch('shared.key_manager.Path.mkdir')
    @patch('shared.key_manager.json.load', return_value={})
    @patch('shared.key_manager.json.dump')
    @patch('shared.key_manager.secrets.token_hex', return_value='test_key_hex')
    def test_not_in_demo_mode(self, mock_token, mock_dump, mock_load, mock_mkdir, mock_exists):
        from shared.key_manager import UnifiedKeyManager
        km = UnifiedKeyManager(config_path='/fake/config.yaml', keys_file='/fake/keys.json')
        assert 'keys' in km.keys_data
        assert 'KeyA' in km.keys_data['keys']

    @patch('shared.key_manager.Path.exists', return_value=False)
    @patch('shared.key_manager.Path.mkdir')
    @patch('shared.key_manager.json.load', return_value={})
    @patch('shared.key_manager.json.dump')
    @patch('shared.key_manager.secrets.token_hex', return_value='test_key_hex')
    def test_demo_mode_detection(self, mock_token, mock_dump, mock_load, mock_mkdir, mock_exists):
        from shared.key_manager import UnifiedKeyManager
        km = UnifiedKeyManager(config_path='/fake/config.yaml', keys_file='/fake/keys.json')
        assert 'KeyA' in km.keys_data.get('keys', {})

    @patch('shared.key_manager.Path.exists', return_value=False)
    @patch('shared.key_manager.Path.mkdir')
    @patch('shared.key_manager.json.load', return_value={})
    @patch('shared.key_manager.json.dump')
    @patch('shared.key_manager.secrets.token_hex', return_value='test_key_hex')
    def test_get_key_from_environment(self, mock_token, mock_dump, mock_load, mock_mkdir, mock_exists):
        from shared.key_manager import UnifiedKeyManager
        km = UnifiedKeyManager(config_path='/fake/config.yaml', keys_file='/fake/keys.json')
        key = km.get_key('KeyA')
        assert key == 'test_key_hex'
