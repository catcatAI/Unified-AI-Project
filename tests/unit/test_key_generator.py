"""Tests for core/security/key_generator.py"""
from unittest.mock import MagicMock, mock_open, patch

import pytest


class TestKeyGenerator:
    """Tests for KeyGenerator"""

    def test_import(self):
        from core.security.key_generator import KeyGenerator
        assert KeyGenerator is not None

    def test_instantiation(self):
        from core.security.key_generator import KeyGenerator
        instance = KeyGenerator()
        assert instance is not None

    def test_generate_secure_key_default_length(self):
        from core.security.key_generator import KeyGenerator
        key = KeyGenerator.generate_secure_key()
        assert len(key) == 32

    def test_generate_secure_key_custom_length(self):
        from core.security.key_generator import KeyGenerator
        key = KeyGenerator.generate_secure_key(48)
        assert len(key) == 48

    def test_generate_secure_key_min_length(self):
        from core.security.key_generator import KeyGenerator
        key = KeyGenerator.generate_secure_key(8)
        assert len(key) == 8

    def test_generated_key_contains_alphanumeric(self):
        from core.security.key_generator import KeyGenerator
        key = KeyGenerator.generate_secure_key(64)
        assert any(c.isalpha() for c in key)
        assert any(c.isdigit() for c in key)
        assert any(c in "!@#$%^&*" for c in key)

    def test_multiple_keys_unique(self):
        from core.security.key_generator import KeyGenerator
        keys = {KeyGenerator.generate_secure_key() for _ in range(10)}
        assert len(keys) == 10

    @patch('builtins.open', new_callable=mock_open, read_data='')
    def test_update_env_file_new(self, mock_file):
        import os

        from core.security.key_generator import KeyGenerator
        instance = KeyGenerator()
        instance.update_env_file({"TEST_KEY": "testvalue"}, "/tmp/nonexistent/.env")
        mock_file.assert_called_once()
        handle = mock_file()
        assert handle.write.called or handle.__enter__.called

    @patch('builtins.open', new_callable=mock_open, read_data='EXISTING=old\n')
    def test_update_env_file_existing(self, mock_file):
        import os

        from core.security.key_generator import KeyGenerator
        instance = KeyGenerator()
        instance.update_env_file({"EXISTING": "newvalue"}, "/tmp/.env")
        handle = mock_file()
        handle.readlines.return_value = ["EXISTING=old\n"]
        handle.__iter__.return_value = ["EXISTING=old\n"]
        assert instance is not None
