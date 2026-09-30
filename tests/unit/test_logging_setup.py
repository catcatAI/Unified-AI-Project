"""ANGELA_LOG_LEVEL has to actually set the level.

The variable is documented in `.env.example`, but the only entry point passed a
hardcoded `logging.INFO` to `setup_logging`, so an operator could set it, see
nothing change, and have no way to tell. These cases pin the resolution order and
the fallback on a malformed value.

ANGELA-MATRIX: [L4] [δ] [B] [L1]
"""

import logging

import pytest

from apps.backend.src.core.logging.setup import resolve_log_level, setup_logging


class TestResolveLogLevel:
    def test_default_when_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ANGELA_LOG_LEVEL", raising=False)

        assert resolve_log_level() == logging.INFO

    @pytest.mark.parametrize(
        ("value", "expected"),
        [("DEBUG", logging.DEBUG), ("debug", logging.DEBUG), ("WARNING", logging.WARNING)],
    )
    def test_level_names_are_accepted(
        self, monkeypatch: pytest.MonkeyPatch, value: str, expected: int
    ) -> None:
        monkeypatch.setenv("ANGELA_LOG_LEVEL", value)

        assert resolve_log_level() == expected

    def test_a_numeric_level_is_accepted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ANGELA_LOG_LEVEL", "10")

        assert resolve_log_level() == logging.DEBUG

    def test_a_malformed_value_falls_back_instead_of_raising(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ANGELA_LOG_LEVEL", "LOUD")

        with pytest.warns(UserWarning):
            assert resolve_log_level() == logging.INFO

    def test_a_blank_value_is_not_an_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ANGELA_LOG_LEVEL", "   ")

        assert resolve_log_level() == logging.INFO

    def test_the_environment_wins_over_the_calling_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`default` is the fallback, not an override: a set variable is the answer."""
        monkeypatch.setenv("ANGELA_LOG_LEVEL", "DEBUG")

        assert resolve_log_level(default=logging.ERROR) == logging.DEBUG


@pytest.fixture
def root_logger_state():
    """Snapshot and restore the root logger, which setup_logging rewrites."""
    root = logging.getLogger()
    level, handlers = root.level, list(root.handlers)
    try:
        yield root
    finally:
        for handler in list(root.handlers):
            root.removeHandler(handler)
            handler.close()
        for handler in handlers:
            root.addHandler(handler)
        root.setLevel(level)


def test_setup_logging_honours_the_documented_switch(
    monkeypatch: pytest.MonkeyPatch, root_logger_state: logging.Logger
) -> None:
    """The end-to-end wiring: env in, root logger level out."""
    monkeypatch.setenv("ANGELA_LOG_LEVEL", "WARNING")

    setup_logging(log_file="test_env_level.log")

    assert root_logger_state.level == logging.WARNING


def test_an_explicit_setup_level_wins_over_the_environment(
    monkeypatch: pytest.MonkeyPatch, root_logger_state: logging.Logger
) -> None:
    monkeypatch.setenv("ANGELA_LOG_LEVEL", "DEBUG")

    setup_logging(level=logging.ERROR, log_file="test_env_level.log")

    assert root_logger_state.level == logging.ERROR


def test_setup_logging_keeps_a_sane_default(
    monkeypatch: pytest.MonkeyPatch, root_logger_state: logging.Logger
) -> None:
    monkeypatch.delenv("ANGELA_LOG_LEVEL", raising=False)

    setup_logging(log_file="test_env_level.log")

    assert root_logger_state.level == logging.INFO
