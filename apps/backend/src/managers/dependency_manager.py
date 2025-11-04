"""Dependency Manager for Unified AI Project.
This module provides a centralized system for managing optional dependencies,
and fallback mechanisms. It allows the project to run even when some
dependencies are not available in the current environment.
"""

import os
import logging
import importlib.util
import yaml # type: ignore
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@dataclass
class DependencyStatus:
    """Tracks the status of a dependency."""
    name: str
    is_available: bool = False
    error: Optional[str] = None
    fallback_available: bool = False
    fallback_name: Optional[str] = None
    module: Optional[Any] = None
    fallback_module: Optional[Any] = None

class DependencyManager:
    """Centralized dependency management system with lazy loading."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        self._dependencies: Dict[str, DependencyStatus] = {}
        self._config: Dict[str, Any] = {}
        self._environment = os.getenv('UNIFIED_AI_ENV', 'development')

        if config_path is None:
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent.parent # Adjust path as needed
            config_path = str(project_root / "configs" / "dependency_config.yaml")

        self._load_config(config_path)
        self._setup_dependency_statuses()

    def _load_config(self, config_path: str) -> None:
        try:
            path = Path(config_path)
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f)
            else:
                logger.warning(f"配置文件不存在: {config_path}. 使用默認配置。")
                self._config = self._get_default_config()
        except Exception as e:
            logger.error(f"加載配置文件失敗: {e}. 使用默認配置。", exc_info=True)
            self._config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        return {
            'dependencies': {
                'core': [
                    {'name': 'tensorflow', 'fallbacks': ['tf_keras'], 'essential': False},
                    {'name': 'spacy', 'fallbacks': ['nltk'], 'essential': False}
                ],
                'optional': []
            },
            'environments': {
                'development': {'allow_fallbacks': True, 'warn_on_fallback': True}
            }
        }

    def _setup_dependency_statuses(self):
        all_deps = self._config.get('dependencies', {}).get('core', []) + \
                   self._config.get('dependencies', {}).get('optional', [])

        for dep_config in all_deps:
            if isinstance(dep_config, dict):
                dep_name = dep_config.get('name')
                if dep_name:
                    self._dependencies[dep_name] = DependencyStatus(dep_name)

    def _check_dependency_availability(self, dep_name: str, config: Dict[str, Any]):
        status = self._dependencies[dep_name]
        if status.is_available or status.fallback_available or status.error:
            return

        # Simplified check for TensorFlow on Windows
        if dep_name == 'tensorflow' and os.name == 'nt':
            logger.warning("Skipping direct import of 'tensorflow' on Windows.")
            status.error = "Direct import skipped on Windows."
            return

        try:
            module_to_import = config.get('import_name', dep_name.replace('-', '_'))
            spec = importlib.util.find_spec(module_to_import)
            if spec:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
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

        env_config = self._config.get('environments', {}).get(self._environment, {})
        if not env_config.get('allow_fallbacks', True):
            return

        for fallback in config.get('fallbacks', []):
            try:
                fallback_module_name = fallback.replace('-', '_')
                spec = importlib.util.find_spec(fallback_module_name)
                if spec:
                    fallback_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(fallback_module)
                    status.fallback_available = True
                    status.fallback_name = fallback
                    status.fallback_module = fallback_module
                    logger.info(f"Fallback '{fallback}' available for '{dep_name}'")
                    return
            except ImportError:
                continue

    def get_dependency(self, name: str) -> Optional[Any]:
        if name not in self._dependencies:
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
        if not status.is_available and not status.fallback_available and not status.error:
            all_deps = self._config.get('dependencies', {}).get('core', []) + \
                       self._config.get('dependencies', {}).get('optional', [])
            dep_config = next((c for c in all_deps if c.get('name') == name), None)
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
        return self.get_dependency(name) is not None

    def get_status(self, name: str) -> Optional[DependencyStatus]:
        self.get_dependency(name)
        return self._dependencies.get(name)

    def get_all_status(self) -> Dict[str, DependencyStatus]:
        for name in list(self._dependencies.keys()): # Iterate over a copy to allow modification
            self.get_dependency(name)
        return self._dependencies.copy()

    def get_dependency_report(self) -> str:
        self.get_all_status()
        report = ["\n=== Dependency Status Report ==="]
        available: List[str] = []
        fallback: List[str] = []
        unavailable: List[str] = []

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

dependency_manager = DependencyManager()

def print_dependency_report():
    """Print the dependency status report."""
    print(dependency_manager.get_dependency_report())

if __name__ == "__main__":
    print_dependency_report()
