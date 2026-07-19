"""
Crisis logging utilities — shared across services for production error logging.

Provides a single source of truth for writing to crisis_log.txt,
avoiding code duplication between error recovery, quality monitoring,
and other production hardening modules.

P38: Code quality — extracted from multimodal_error_recovery.py
     and multimodal_quality_monitor.py to eliminate duplication.

ANGELA-MATRIX: [L5] [βγδ] [B] [L4]
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)

CRISIS_LOG_PATH = "crisis_log.txt"
QUALITY_LOG_DIR = os.path.join("logs")


def write_crisis_log(level: int, details: Dict[str, Any]) -> None:
    """Write an entry to the crisis log file.

    Args:
        level: Crisis severity level (1-5, higher = more severe)
        details: Arbitrary dict describing the crisis event
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        line = f"[{timestamp}] CRISIS_LOG: Level {level} event. Details: {details}\n"
        with open(CRISIS_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception as exc:
        logger.warning("Failed to write crisis log: %s", exc)


def append_quality_log(entry: Dict[str, Any]) -> None:
    """Append a quality sample entry to the JSONL quality log file.

    Args:
        entry: Quality sample dict to log
    """
    try:
        log_path = os.path.join(QUALITY_LOG_DIR, "multimodal_quality.jsonl")
        os.makedirs(QUALITY_LOG_DIR, exist_ok=True)
        import json

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")
    except Exception as exc:
        logger.warning("Failed to write quality log: %s", exc)
