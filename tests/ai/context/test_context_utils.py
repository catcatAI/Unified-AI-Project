"""ai.context.utils 工具函数测试"""

from cryptography.fernet import Fernet

from apps.backend.src.ai.context.storage.base import Context, ContextStatus, ContextType
from apps.backend.src.ai.context.utils import (
    calculate_context_hash,
    compress_context_data,
    decompress_context_data,
    decrypt_context_data,
    deserialize_context,
    encrypt_context_data,
    filter_context_content,
    merge_contexts,
    serialize_context,
    validate_context,
)


def _make_context(content=None, tags=None):
    ctx = Context("test-1", ContextType.MEMORY)
    if content:
        ctx.content = content
    if tags:
        ctx.tags = tags
    return ctx


class TestSerializeContext:
    def test_roundtrip_preserves_fields(self):
        ctx = _make_context(content={"msg": "hello"}, tags=["t1"])
        restored = deserialize_context(serialize_context(ctx))
        assert restored.context_id == "test-1"
        assert restored.context_type == ContextType.MEMORY
        assert restored.content == {"msg": "hello"}
        assert restored.tags == ["t1"]
        assert restored.status == ContextStatus.ACTIVE

    def test_returns_bytes(self):
        ctx = _make_context()
        assert isinstance(serialize_context(ctx), bytes)


class TestCompressContextData:
    def test_roundtrip(self):
        data = b"x" * 1000
        compressed = compress_context_data(data)
        assert len(compressed) < len(data)
        assert decompress_context_data(compressed) == data


class TestEncryptDecrypt:
    def test_roundtrip_with_key(self):
        key = Fernet.generate_key()
        data = b"secret payload"
        encrypted = encrypt_context_data(data, key)
        assert encrypted != data
        assert decrypt_context_data(encrypted, key) == data

    def test_without_key_returns_raw(self):
        data = b"plain"
        assert encrypt_context_data(data) == data
        assert decrypt_context_data(data) == data

    def test_wrong_key_fails(self):
        key1 = Fernet.generate_key()
        key2 = Fernet.generate_key()
        encrypted = encrypt_context_data(b"data", key1)
        try:
            decrypt_context_data(encrypted, key2)
        except Exception:
            pass
        else:
            raise AssertionError("decrypt with wrong key should fail")


class TestCalculateContextHash:
    def test_deterministic(self):
        ctx = _make_context(content={"a": 1})
        assert calculate_context_hash(ctx) == calculate_context_hash(ctx)

    def test_changes_with_content(self):
        ctx1 = _make_context(content={"a": 1})
        ctx2 = _make_context(content={"a": 2})
        assert calculate_context_hash(ctx1) != calculate_context_hash(ctx2)

    def test_hexdigest_length(self):
        ctx = _make_context()
        assert len(calculate_context_hash(ctx)) == 64


class TestValidateContext:
    def test_valid_context(self):
        assert validate_context(_make_context()) is True

    def test_empty_id_invalid(self):
        ctx = Context("", ContextType.MEMORY)
        assert validate_context(ctx) is False

    def test_future_created_at_invalid(self):
        ctx = _make_context()
        ctx.created_at = ctx.created_at.replace(year=2099)
        assert validate_context(ctx) is False


class TestMergeContexts:
    def test_merges_content_metadata_tags(self):
        ctx1 = _make_context(content={"a": 1, "b": 2}, tags=["x"])
        ctx2 = _make_context(content={"b": 20, "c": 3}, tags=["y"])
        ctx2.context_id = "test-2"
        merged = merge_contexts(ctx1, ctx2)
        assert merged.context_id == "test-1+test-2"
        assert merged.content == {"a": 1, "b": 20, "c": 3}
        assert set(merged.tags) == {"x", "y"}

    def test_created_at_takes_minimum(self):
        ctx1 = _make_context()
        ctx2 = _make_context()
        ctx1.created_at = ctx1.created_at.replace(year=2020)
        merged = merge_contexts(ctx1, ctx2)
        assert merged.created_at.year == 2020


class TestFilterContextContent:
    def test_keeps_allowed_keys(self):
        result = filter_context_content({"a": 1, "b": 2, "c": 3}, ["a", "c"])
        assert result == {"a": 1, "c": 3}

    def test_missing_keys_omitted(self):
        result = filter_context_content({"a": 1}, ["a", "b"])
        assert result == {"a": 1}
