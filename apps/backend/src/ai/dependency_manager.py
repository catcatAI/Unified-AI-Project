"""Dependency Manager for Unified AI Project, ::
    This module provides a centralized system for managing optional dependencies, ::
        nd fallback mechanisms. It allows the project to run even when some
dependencies are not available in the current environment.
"""

import asyncio
import logging
import os
import sys
import time
import importlib
import random # Added missing import
import yaml
import psutil # Added missing import
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from apps.backend.src.core.hsp.types import HSPCapabilityAdvertisementPayload
from apps.backend.src.core.hsp.connector import HSPConnector

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class DependencyStatus:
    """Tracks the status of a dependency."""

    def __init__(self, name: str, is_available: bool = False, error: Optional[str] = None,
                 fallback_available: bool = False, fallback_name: Optional[str] = None):
        self.name = name
        self.is_available = is_available
        self.error = error
        self.fallback_available = fallback_available
        self.fallback_name = fallback_name
        self.module: Optional[Any] = None
        self.fallback_module: Optional[Any] = None


class DependencyManager:
    """Centralized dependency management system with lazy loading."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        self._dependencies: Dict[str, DependencyStatus] = {}
        self._config: Dict[str, Any] = {}
        self._environment = "development"  # 默认环境

        # Load configuration
        if config_path is None:
            current_dir = Path(__file__).parent
            # Adjust path to be relative to the assumed project structure
            project_root = current_dir.parent.parent
            config_path = os.path.join(project_root, "configs",
                                     "dependency_config.yaml")

        self._load_config(config_path)
        self._setup_dependency_statuses()

    def _load_config(self, config_path: Union[str, Path]):
        """Load dependency configuration from YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        except (FileNotFoundError, ImportError) as e:
            logger.warning(
                f"Could not load dependency config from {config_path} {e}. "
                f"Using default configuration."
            )
            self._config = self._get_default_config()
        except Exception as e:
            logger.warning(
                f"Could not load dependency config from {config_path} {e}. "
                f"Using default configuration."
            )
            self._config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration when config file is not available."""
        return {
            'dependencies': {
                'core': [
                    {'name': 'tensorflow', 'fallbacks': ['tf-keras'], 'essential': False},
                    {'name': 'spacy', 'fallbacks': ['nltk'], 'essential': False}
                ],
                'optional': []
            },
            'environments': {
                'development': {
                    'allow_fallbacks': True,
                    'warn_on_fallback': True,
                }
            }
        }

    def _setup_dependency_statuses(self):
        """Set up dependency status objects without loading them."""
        all_deps = self._config.get('dependencies', {}).get('core', []) + \
                   self._config.get('dependencies', {}).get('optional', [])

        for dep_config in all_deps:
            if isinstance(dep_config, dict):
                dep_name = dep_config.get('name')
                if dep_name:
                    self._dependencies[dep_name] = DependencyStatus(dep_name)

    def _check_dependency_availability(self, dep_name: str, config: Dict[str, Any]):
        """Check if a dependency and its fallbacks are available (on-demand)."""
        status = self._dependencies[dep_name]

        # Do not re-check if already checked
        if status.is_available or status.fallback_available or status.error:
            return

        # OS-specific check for tensorflow
        if dep_name == 'tensorflow' and os.name == 'nt':
            logger.warning("Skipping direct import of 'tensorflow' on Windows.")
            status.error = "Direct import skipped on Windows."
        else:
            try:
                import_name_map = {
                    'paho-mqtt': 'paho.mqtt.client',
                }
                module_to_import = import_name_map.get(dep_name, dep_name.replace('-', '_'))

                logger.debug(f"Lazily importing {module_to_import} for dependency {dep_name}")
                module = importlib.import_module(module_to_import)
                status.is_available = True
                status.module = module
                logger.info(f"Dependency '{dep_name}' is available.")
                return
            except ImportError as e:
                status.error = str(e)
                logger.warning(f"Primary dependency '{dep_name}' not available: {e}")
            except Exception as e:
                status.error = f"An unexpected error occurred: {e}"
                logger.error(f"Failed to import '{dep_name}': {e}", exc_info=True)

        # Fallback logic
        env_config = self._config.get('environments', {}).get(self._environment, {})
        if not env_config.get('allow_fallbacks', True):
            return

        for fallback in config.get('fallbacks', []):
            try:
                fallback_module = importlib.import_module(fallback.replace('-', '_'))
                status.fallback_available = True
                status.fallback_name = fallback
                status.fallback_module = fallback_module
                logger.info(f"Fallback '{fallback}' available for '{dep_name}'")
                break
            except ImportError:
                continue

    def get_dependency(self, name: str) -> Optional[Any]:
        """Get a dependency module, loading it if it hasn't been loaded yet."""
        if name not in self._dependencies:
            # Try to lazily register this dependency from the config
            all_deps = self._config.get('dependencies', {}).get('core', []) + \
                       self._config.get('dependencies', {}).get('optional', [])
            dep_config = next((c for c in all_deps if isinstance(c, dict) and c.get('name') == name), None)
            if dep_config:
                self._dependencies[name] = DependencyStatus(name)
                self._check_dependency_availability(name, dep_config)
            else:
                logger.warning(f"Unknown dependency '{name}' requested")
                return None

        status = self._dependencies[name]

        # If not yet checked, perform the check now
        if not status.is_available and not status.fallback_available and not status.error:
            all_deps = self._config.get('dependencies', {}).get('core', []) + \
                       self._config.get('dependencies', {}).get('optional', [])
            dep_config = next((c for c in all_deps if isinstance(c, dict) and c.get('name') == name), None)
            if dep_config:
                self._check_dependency_availability(name, dep_config)
            else:
                logger.error(f"Configuration for dependency '{name}' not found.")
                status.error = "Configuration not found"

        if status.is_available:
            return status.module
        elif status.fallback_available:
            logger.info(f"Using fallback '{status.fallback_name}' for '{name}'")
            return status.fallback_module
        else:
            if status.error:
                logger.warning(f"Dependency '{name}' and fallbacks unavailable. Reason: {status.error}")
            else:
                logger.warning(f"Dependency '{name}' and fallbacks unavailable.")
            return None

    def is_available(self, name: str) -> bool:
        """Check if a dependency is available, loading it if necessary."""
        return self.get_dependency(name) is not None

    def get_status(self, name: str) -> Optional[DependencyStatus]:
        """Get detailed status of a dependency."""
        # Ensure the status is up-to-date by trying to get the dependency
        self.get_dependency(name)
        return self._dependencies.get(name)

    def get_all_status(self) -> Dict[str, DependencyStatus]:
        """Get status of all tracked dependencies, checking each one."""
        for name in self._dependencies:
            self.get_dependency(name)
        return self._dependencies.copy()

    def get_dependency_report(self) -> str:
        """Generate a human-readable dependency status report."""
        # Ensure all statuses are checked before reporting
        self.get_all_status()

        report = ["\n== Dependency Status Report =="]
        available, fallback, unavailable = [], [], []

        for name, status in self._dependencies.items():
            if status.is_available:
                available.append(name)
            elif status.fallback_available:
                fallback.append(f"{name} (using {status.fallback_name})")
            else:
                unavailable.append(f"{name} - {status.error or 'Unknown error'}")

        if available:
            report.append(f"\n✓ Available ({len(available)})")
            report.extend([f"  - {dep}" for dep in available])
        if fallback:
            report.append(f"\n⚠ Using Fallbacks ({len(fallback)})")
            report.extend([f"  - {dep}" for dep in fallback])
        if unavailable:
            report.append(f"\n✗ Unavailable ({len(unavailable)})")
            report.extend([f"  - {dep}" for dep in unavailable])
        report.append("\n" + "=" * 35)
        return "\n".join(report)

# Global dependency manager instance
dependency_manager = DependencyManager()

def print_dependency_report():
    """Print the dependency status report."""
    print(dependency_manager.get_dependency_report())