import os
import pytest
from shared.utils.env_utils import get_env, get_int_env, get_float_env, get_bool_env, load_env_file


class TestGetEnv:
    def test_returns_existing_key(self, monkeypatch):
        monkeypatch.setenv("TEST_KEY", "hello")
        assert get_env("TEST_KEY") == "hello"

    def test_returns_default_for_missing_env(self):
        assert get_env("NONEXISTENT_KEY", "default_val") == "default_val"

    def test_returns_none_for_missing_no_default(self):
        assert get_env("NONEXISTENT_KEY") is None


class TestGetIntEnv:
    def test_valid_int(self, monkeypatch):
        monkeypatch.setenv("INT_KEY", "42")
        assert get_int_env("INT_KEY") == 42

    def test_default_for_missing_int(self):
        assert get_int_env("MISSING_INT", 10) == 10

    def test_invalid_returns_default_int(self, monkeypatch):
        monkeypatch.setenv("BAD_INT", "not_a_number")
        assert get_int_env("BAD_INT", 0) == 0


class TestGetFloatEnv:
    def test_valid_float(self, monkeypatch):
        monkeypatch.setenv("FLOAT_KEY", "3.14")
        assert get_float_env("FLOAT_KEY") == 3.14

    def test_default_for_missing_float(self):
        assert get_float_env("MISSING_FLOAT", 1.5) == 1.5

    def test_invalid_returns_default_float(self, monkeypatch):
        monkeypatch.setenv("BAD_FLOAT", "nan")
        assert get_float_env("BAD_FLOAT", 0.0) == 0.0


class TestGetBoolEnv:
    @pytest.mark.parametrize("raw,expected", [
        ("1", True), ("true", True), ("yes", True), ("on", True),
        ("0", False), ("false", False), ("no", False), ("off", False),
        ("anything", False),
    ])
    def test_various_values(self, monkeypatch, raw, expected):
        monkeypatch.setenv("BOOL_KEY", raw)
        assert get_bool_env("BOOL_KEY") == expected

    def test_default_for_missing_bool(self):
        assert get_bool_env("MISSING_BOOL", True) is True


class TestLoadEnvFile:
    def test_loads_valid_file(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("KEY1=val1\nKEY2=val2\n# comment\n\nKEY3=val3\n")
        result = load_env_file(str(env_file))
        assert result["KEY1"] == "val1"
        assert result["KEY2"] == "val2"
        assert result["KEY3"] == "val3"
        assert os.environ.get("KEY1") == "val1"

    def test_missing_file_returns_empty(self, tmp_path):
        result = load_env_file(str(tmp_path / "nonexistent.env"))
        assert result == {}

    def test_strips_quotes(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text('KEY="quoted_val"\n')
        result = load_env_file(str(env_file))
        assert result["KEY"] == "quoted_val"

    def test_handles_empty_lines_and_comments(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("\n# comment\n\nSIMPLE=ok\n")
        result = load_env_file(str(env_file))
        assert result["SIMPLE"] == "ok"
        assert len(result) == 1
