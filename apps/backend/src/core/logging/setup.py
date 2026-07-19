"""
Logging Setup - Unified configuration for Angela AI
Centralizes logging configuration to prevent 'log-jacking' by submodules.
"""

import logging
from pathlib import Path


def setup_logging(level=logging.INFO, log_file="backend.log") -> str:
    """
    Initializes the global logging system.
    Should only be called once from entry points (main.py, main_api_server.py).
    """
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
