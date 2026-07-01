import sys
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def mock_fernet():
    with patch("apps.backend.src.core.security.encryption.FERNET_AVAILABLE", False):
        yield


class TestEncryptionUtils:
    def test_hash_password_returns_hash_and_salt(self):
        from apps.backend.src.core.security.encryption import EncryptionUtils

        utils = EncryptionUtils()
        result = utils.hash_password("test_password")
        assert "hash" in result
        assert "salt" in result
        assert len(result["hash"]) > 0
        assert len(result["salt"]) > 0

    def test_hash_password_deterministic_with_salt(self):
        from apps.backend.src.core.security.encryption import EncryptionUtils

        utils = EncryptionUtils()
        salt = "fixed_salt_value_1234567890123456"
        result1 = utils.hash_password("same_password", salt)
        result2 = utils.hash_password("same_password", salt)
        assert result1["hash"] == result2["hash"]

    def test_verify_password_correct(self):
        from apps.backend.src.core.security.encryption import EncryptionUtils

        utils = EncryptionUtils()
        result = utils.hash_password("my_password")
        assert utils.verify_password("my_password", result["hash"], result["salt"]) is True

    def test_verify_password_incorrect(self):
        from apps.backend.src.core.security.encryption import EncryptionUtils

        utils = EncryptionUtils()
        result = utils.hash_password("my_password")
        assert utils.verify_password("wrong_password", result["hash"], result["salt"]) is False

    def test_generate_secure_token_length(self):
        from apps.backend.src.core.security.encryption import EncryptionUtils

        utils = EncryptionUtils()
        token = utils.generate_secure_token(16)
        assert len(token) > 0

    def test_generate_secure_token_default_length(self):
        from apps.backend.src.core.security.encryption import EncryptionUtils

        utils = EncryptionUtils()
        token = utils.generate_secure_token()
        assert len(token) > 32

    def test_hash_data_sha256(self):
        from apps.backend.src.core.security.encryption import EncryptionUtils

        utils = EncryptionUtils()
        h = utils.hash_data("test data", algorithm="sha256")
        assert len(h) == 64

    def test_hash_data_sha512(self):
        from apps.backend.src.core.security.encryption import EncryptionUtils

        utils = EncryptionUtils()
        h = utils.hash_data("test data", algorithm="sha512")
        assert len(h) == 128

    def test_hash_data_md5(self):
        from apps.backend.src.core.security.encryption import EncryptionUtils

        utils = EncryptionUtils()
        h = utils.hash_data("test data", algorithm="md5")
        assert len(h) == 32

    def test_hash_data_unsupported_algorithm(self):
        from apps.backend.src.core.security.encryption import EncryptionUtils

        utils = EncryptionUtils()
        with pytest.raises(ValueError, match="不支持的哈希算法"):
            utils.hash_data("test", algorithm="sha1")

    def test_hash_data_consistency(self):
        from apps.backend.src.core.security.encryption import EncryptionUtils

        utils = EncryptionUtils()
        h1 = utils.hash_data("consistent data")
        h2 = utils.hash_data("consistent data")
        assert h1 == h2

    def test_hash_data_different_inputs_different_hashes(self):
        from apps.backend.src.core.security.encryption import EncryptionUtils

        utils = EncryptionUtils()
        h1 = utils.hash_data("data A")
        h2 = utils.hash_data("data B")
        assert h1 != h2

    def test_encrypt_raises_without_fernet(self):
        from apps.backend.src.core.security.encryption import EncryptionUtils

        utils = EncryptionUtils()
        with pytest.raises(ValueError, match="Fernet not available"):
            utils.encrypt("test")

    def test_decrypt_raises_without_fernet(self):
        from apps.backend.src.core.security.encryption import EncryptionUtils

        utils = EncryptionUtils()
        with pytest.raises(ValueError, match="Fernet not available"):
            utils.decrypt(b"test")


class TestValidatePasswordStrength:
    def test_valid_password(self):
        from apps.backend.src.core.security.encryption import validate_password_strength

        result = validate_password_strength("Abcdef1!")
        assert result["valid"] is True

    def test_too_short_password(self):
        from apps.backend.src.core.security.encryption import validate_password_strength

        result = validate_password_strength("A1!")
        assert result["valid"] is False

    def test_no_special_char(self):
        from apps.backend.src.core.security.encryption import validate_password_strength

        result = validate_password_strength("Abcdefg1")
        assert result["valid"] is False

    def test_no_digit(self):
        from apps.backend.src.core.security.encryption import validate_password_strength

        result = validate_password_strength("Abcdefg!")
        assert result["valid"] is False

    def test_no_uppercase(self):
        from apps.backend.src.core.security.encryption import validate_password_strength

        result = validate_password_strength("abcdef1!")
        assert result["valid"] is False

    def test_no_lowercase(self):
        from apps.backend.src.core.security.encryption import validate_password_strength

        result = validate_password_strength("ABCDEF1!")
        assert result["valid"] is False


class TestSanitizeInput:
    def test_normal_string(self):
        from apps.backend.src.core.security.encryption import sanitize_input

        assert sanitize_input("hello world") == "hello world"

    def test_strips_dangerous_chars(self):
        from apps.backend.src.core.security.encryption import sanitize_input

        result = sanitize_input("<script>alert('xss')</script>")
        assert "<" not in result
        assert ">" not in result
        assert "'" not in result

    def test_empty_input(self):
        from apps.backend.src.core.security.encryption import sanitize_input

        assert sanitize_input("") == ""

    def test_none_input(self):
        from apps.backend.src.core.security.encryption import sanitize_input

        assert sanitize_input(None) == ""

    def test_strips_whitespace(self):
        from apps.backend.src.core.security.encryption import sanitize_input

        assert sanitize_input("  hello  ") == "hello"


class TestCsrfToken:
    def test_generate_and_verify(self):
        from apps.backend.src.core.security.encryption import generate_csrf_token, verify_csrf_token

        token = generate_csrf_token()
        assert verify_csrf_token(token, token) is True

    def test_verify_different_tokens(self):
        from apps.backend.src.core.security.encryption import generate_csrf_token, verify_csrf_token

        t1 = generate_csrf_token()
        t2 = generate_csrf_token()
        assert verify_csrf_token(t1, t2) is False


class TestEncryptionSmoke:
    """Smoke tests consolidated from tests/unit/test_encryption.py"""

    def test_import(self):
        from core.security.encryption import EncryptionUtils
        assert EncryptionUtils is not None

    @patch("core.security.encryption.FERNET_AVAILABLE", True)
    @patch("core.security.encryption.Fernet")
    def test_instantiation_with_fernet(self, mock_fernet):
        from unittest.mock import MagicMock
        from core.security.encryption import EncryptionUtils

        mock_fernet_instance = MagicMock()
        mock_fernet.return_value = mock_fernet_instance
        instance = EncryptionUtils(config={"encryption_key": "test-key-32-chars-long!!"})
        assert instance is not None
