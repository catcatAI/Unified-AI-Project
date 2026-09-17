"""
Formalized Bootstrap Package
Exposes hardware probing and environment resolution capabilities.
"""

from .bootstrap_manager import BootstrapManager, get_bootstrap_manager
from .env_resolver import EnvResolver
from .first_run_detection import detect_first_run, log_first_run_warnings
from .hardware_probe import HardwareProbe, HardwareSpecs

__all__ = [
    "get_bootstrap_manager",
    "BootstrapManager",
    "HardwareProbe",
    "HardwareSpecs",
    "EnvResolver",
    "detect_first_run",
    "log_first_run_warnings",
]
