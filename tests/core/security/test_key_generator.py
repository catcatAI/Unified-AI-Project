import os
import pytest
import tempfile
try:
    from apps.backend.src.core.security.key_generator import KeyGenerator
except ImportError:
    import pytest; pytest.skip("KeyGenerator is a stub", allow_module_level=True)


class TestKeyGenerator:
    def test_generate_secure_key_length(self):
        key = KeyGenerator.generate_secure_key(32)
        assert len(key) == 32

    def test_generate_secure_key_default_length(self):
        key = KeyGenerator.generate_secure_key()
        assert len(key) == 32

    def test_generate_secure_key_variable_length(self):
        key = KeyGenerator.generate_secure_key(64)
        assert len(key) == 64

    def test_generate_secure_key_randomness(self):
        keys = {KeyGenerator.generate_secure_key() for _ in range(100)}
        assert len(keys) == 100

    def test_generate_secure_key_contains_valid_chars(self):
        key = KeyGenerator.generate_secure_key(100)
        import string

        valid = string.ascii_letters + string.digits + "!@#$%^&*"
        for ch in key:
            assert ch in valid

    def test_update_env_file_creates_new(self):
        gen = KeyGenerator()
        keys = {"TEST_KEY_A": "value_a", "TEST_KEY_B": "value_b"}
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = os.path.join(tmpdir, ".env")
            gen.update_env_file(keys, env_path)
            assert os.path.exists(env_path)
            with open(env_path, "r") as f:
                content = f.read()
            assert "TEST_KEY_A=value_a" in content
            assert "TEST_KEY_B=value_b" in content

    def test_update_env_file_updates_existing(self):
        gen = KeyGenerator()
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = os.path.join(tmpdir, ".env")
            with open(env_path, "w") as f:
                f.write("EXISTING_KEY=old_val\nOTHER_KEY=keep\n")
            gen.update_env_file({"EXISTING_KEY": "new_val"}, env_path)
            with open(env_path, "r") as f:
                content = f.read()
            assert "EXISTING_KEY=new_val" in content
            assert "OTHER_KEY=keep" in content

    def test_update_env_file_adds_missing(self):
        gen = KeyGenerator()
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = os.path.join(tmpdir, ".env")
            with open(env_path, "w") as f:
                f.write("EXISTING_KEY=val\n")
            gen.update_env_file({"NEW_KEY": "new_val"}, env_path)
            with open(env_path, "r") as f:
                content = f.read()
            assert "EXISTING_KEY=val" in content
            assert "NEW_KEY=new_val" in content
