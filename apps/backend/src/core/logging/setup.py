"""
Logging Setup - Unified configuration for Angela AI
Centralizes logging configuration to prevent 'log-jacking' by submodules.
"""

import logging
import os
import warnings
from pathlib import Path
from typing import Optional, Union

warnings.filterwarnings(
    "ignore",
    message=r"The pynvml package is deprecated.*",
    category=FutureWarning,
)

LOG_LEVEL_ENV = "ANGELA_LOG_LEVEL"


def resolve_log_level(default: int = logging.INFO) -> int:
    """Resolve the log level: ANGELA_LOG_LEVEL, then ``default``.

    The variable is documented in `.env.example`, so it has to be read here: the
    single entry point used to pass a hardcoded ``logging.INFO``, which made the
    documented switch do nothing at all. Accepts a level name (``DEBUG``) or a
    number, and falls back rather than raising on a typo, because a mistyped log
    level must not stop the server from starting.
    """
    raw = os.getenv(LOG_LEVEL_ENV, "").strip()
    if not raw:
        return default
    named = getattr(logging, raw.upper(), None)
    if isinstance(named, int):
        return named
    try:
        return int(raw)
    except ValueError:
        warnings.warn(
            f"{LOG_LEVEL_ENV}={raw!r} is not a logging level; using "
            f"{logging.getLevelName(default)}",
            stacklevel=2,
        )
        return default


def setup_logging(
    level: Optional[Union[int, str]] = None, log_file: str = "backend.log"
) -> logging.Logger:
    """
    Initializes the global logging system.
    Should only be called once from entry points (main.py, main_api_server.py).

    ``level`` left unset resolves from the environment; pass a level explicitly
    to override it.
    """
    if level is None:
        level = resolve_log_level()
    elif isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    # 1. Ensure log directory exists
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # 2. Configure the root logger
    # Note: EnterpriseLogger manages its own handlers,
    # but we set up a sane default for standard logging.getLogger() users.

    # Remove existing handlers to prevent duplicates
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers[:]:
            root.removeHandler(handler)

    # Main file handler
    file_handler = logging.FileHandler(log_dir / log_file, encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")
    )

    root.setLevel(level)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    # 3. Prevent submodules from re-configuring via basicConfig
    # We can't actually disable basicConfig, but we can make it do nothing
    # if it's already configured. basicConfig(force=True) is the enemy here.

    logging.info(
        f"🛡️ [Logging] Unified system initialized. Root Level: {logging.getLevelName(level)}"
    )
    return root
