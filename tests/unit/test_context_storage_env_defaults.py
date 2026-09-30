"""The context storage knobs `.env.example` documents have to actually work.

`CONTEXT_STORAGE_DIR` and `CONTEXT_MEMORY_MAX_SIZE` were written down as the way
to configure the context system while the storage classes ignored the environment
entirely: `DiskStorage` and `MemoryStorage` only accepted constructor arguments, so
setting either variable did nothing. These cases pin the resolution order
(argument > env > default) and the fallback on a malformed value.

ANGELA-MATRIX: [L4] [δ] [B] [L1]
"""

import pytest

from apps.backend.src.ai.context.storage.disk import (
    DEFAULT_STORAGE_DIR,
    DiskStorage,
    resolve_storage_dir,
)
from apps.backend.src.ai.context.storage.memory import (
    DEFAULT_MAX_SIZE,
    MemoryStorage,
    resolve_max_size,
)


class TestStorageDirResolution:
    def test_default_when_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("CONTEXT_STORAGE_DIR", raising=False)

        assert resolve_storage_dir() == DEFAULT_STORAGE_DIR

    def test_environment_is_honoured(self, monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
        monkeypatch.setenv("CONTEXT_STORAGE_DIR", str(tmp_path / "ctx"))

        assert resolve_storage_dir() == str(tmp_path / "ctx")

    def test_explicit_argument_wins(self, monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
        monkeypatch.setenv("CONTEXT_STORAGE_DIR", str(tmp_path / "from-env"))

        assert resolve_storage_dir(str(tmp_path / "from-arg")) == str(tmp_path / "from-arg")

    def test_a_blank_value_is_not_an_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CONTEXT_STORAGE_DIR", "   ")

        assert resolve_storage_dir() == DEFAULT_STORAGE_DIR

    def test_disk_storage_creates_the_configured_directory(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path
    ) -> None:
        target = tmp_path / "ctx-store"
        monkeypatch.setenv("CONTEXT_STORAGE_DIR", str(target))

        instance = DiskStorage()

        assert instance.storage_dir == str(target)
        assert target.is_dir()


class TestMemoryMaxSizeResolution:
    def test_default_when_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("CONTEXT_MEMORY_MAX_SIZE", raising=False)

        assert resolve_max_size() == DEFAULT_MAX_SIZE

    def test_environment_is_honoured(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CONTEXT_MEMORY_MAX_SIZE", "25")

        assert resolve_max_size() == 25

    def test_explicit_argument_wins(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CONTEXT_MEMORY_MAX_SIZE", "25")

        assert resolve_max_size(100) == 100

    @pytest.mark.parametrize("value", ["lots", "0", "-3", "1.5"])
    def test_an_unusable_value_falls_back_instead_of_raising(
        self, monkeypatch: pytest.MonkeyPatch, value: str
    ) -> None:
        """This runs in the ContextManager constructor: a typo must not break boot."""
        monkeypatch.setenv("CONTEXT_MEMORY_MAX_SIZE", value)

        assert resolve_max_size() == DEFAULT_MAX_SIZE

    def test_memory_storage_uses_the_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CONTEXT_MEMORY_MAX_SIZE", "25")

        instance = MemoryStorage()

        assert instance.max_size == 25

    def test_the_cache_actually_honours_the_resolved_size(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The knob has to change behaviour, not just a stored attribute."""
        from apps.backend.src.ai.context.storage.base import Context, ContextType

        monkeypatch.setenv("CONTEXT_MEMORY_MAX_SIZE", "2")
        instance = MemoryStorage()

        for index in range(3):
            instance.save_context(Context(f"ctx-{index}", ContextType.DIALOGUE))

        assert len(instance._storage) == 2
        assert instance.load_context("ctx-0") is None
