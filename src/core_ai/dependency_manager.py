"""Dependency Manager for Unified AI Project

This module provides a centralized system for managing optional dependencies
and fallback mechanisms. It allows the project to run even when some
dependencies are not available in the current environment.
"""

import importlib
import logging
import os
import yaml
from typing import Dict, Any, Optional, Callable, List, Tuple, Union
from functools import wraps
import warnings
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

class DependencyStatus:
    """Tracks the status of a dependency."""
    def __init__(self, name: str, is_available: bool = False, error: Optional[str] = None, 
                 fallback_available: bool = False, fallback_name: Optional[str] = None):
        self.name = name
        self.is_available = is_available
        self.error = error
        self.fallback_available = fallback_available
        self.fallback_name = fallback_name
        self.module = None
        self.fallback_module = None

class DependencyManager:
    """Centralized dependency management system."""
    
    def __init__(self, config_path: Optional[str] = None):
        self._dependencies: Dict[str, DependencyStatus] = {}
        self._lazy_imports: Dict[str, Any] = {}
        self._fallback_handlers: Dict[str, Callable] = {}
        self._config: Dict[str, Any] = {}
        self._environment = os.getenv('UNIFIED_AI_ENV', 'development')
        
        # Load configuration
        if config_path is None:
            # Try to find config file relative to project root
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent  # Go up to project root
            config_path = project_root / "dependency_config.yaml"
        
        self._load_config(config_path)
        self._initialize_core_dependencies()
    
    def _load_config(self, config_path: Union[str, Path]):
        """Load dependency configuration from YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        except (FileNotFoundError, yaml.YAMLError) as e:
            logger.warning(
                f"Could not load dependency config from {config_path}: {e}. "
                f"Using default configuration."
            )
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration when config file is not available."""
        return {
            'dependencies': {
                'core': [
                    {'name': 'tensorflow', 'fallbacks': ['tensorflow-cpu', 'numpy'], 'essential': False, 'description': 'Machine learning framework for neural network models'},
                    {'name': 'spacy', 'fallbacks': ['nltk', 'textblob'], 'essential': False, 'description': 'Natural language processing library'},
                    {'name': 'paho-mqtt', 'fallbacks': ['asyncio-mqtt', 'gmqtt'], 'essential': True, 'description': 'MQTT client for HSP communication'},
                    {'name': 'langchain', 'fallbacks': ['openai', 'anthropic'], 'essential': False, 'description': 'LLM integration framework'},
                    {'name': 'fastapi', 'fallbacks': ['flask', 'tornado'], 'essential': True, 'description': 'Web framework for API services'},
                    {'name': 'uvicorn', 'fallbacks': ['gunicorn', 'waitress'], 'essential': True, 'description': 'ASGI server for web applications'},
                    {'name': 'networkx', 'fallbacks': ['igraph', 'graph-tool'], 'essential': True, 'description': 'Graph analysis library for knowledge graphs'},
                    {'name': 'cryptography', 'fallbacks': ['pycryptodome', 'hashlib'], 'essential': True, 'description': 'Cryptographic functions for security'}
                ],
                'optional': []
            },
            'fallback_strategies': {},
            'environments': {
                'development': {
                    'allow_fallbacks': True,
                    'warn_on_fallback': True,
                    'strict_mode': False
                }
            }
        }
    
    def _initialize_core_dependencies(self):
        """Initialize tracking for core project dependencies."""
        # Load dependencies from config
        core_deps = self._config.get('dependencies', {}).get('core', [])
        optional_deps = self._config.get('dependencies', {}).get('optional', [])
        
        for dep_config in core_deps + optional_deps:
            if isinstance(dep_config, dict):
                dep_name = dep_config.get('name')
                if dep_name:
                    self._dependencies[dep_name] = DependencyStatus(dep_name)
                    self._check_dependency_availability(dep_name, dep_config)
    
    def _check_dependency_availability(self, dep_name: str, config: Dict[str, Any]):
        """Check if a dependency and its fallbacks are available."""
        status = self._dependencies[dep_name]
        
        # Try main dependency
        try:
            module = importlib.import_module(dep_name.replace('-', '_'))
            status.is_available = True
            status.module = module
            logger.info(f"Dependency '{dep_name}' is available")
            return
        except ImportError as e:
            status.error = str(e)
            logger.warning(f"Primary dependency '{dep_name}' not available: {e}")
        
        # Check if fallbacks are allowed in current environment
        env_configs = self._config.get('environments', {})
        env_config = env_configs.get(self._environment, [])
        
        # Convert list to dict for easier access
        if isinstance(env_config, list) and env_config:
            env_dict = env_config[0] if env_config else {}
        elif isinstance(env_config, dict):
            env_dict = env_config
        else:
            env_dict = {}
            
        if not env_dict.get('allow_fallbacks', True):
            logger.warning(f"Fallbacks disabled for environment '{self._environment}'")
            return
        
        # Try fallbacks
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
        
        if not status.fallback_available and config.get('essential', False):
            logger.error(f"Essential dependency '{dep_name}' and all fallbacks unavailable")
        elif status.fallback_available:
            logger.info(f"Using fallback '{status.fallback_name}' for '{dep_name}'")
    
    def get_dependency(self, name: str) -> Optional[Any]:
        """Get a dependency module, returning fallback if main is unavailable."""
        if name not in self._dependencies:
            logger.warning(f"Unknown dependency '{name}' requested")
            return None
        
        status = self._dependencies[name]
        
        if status.is_available:
            return status.module
        elif status.fallback_available:
            logger.info(f"Using fallback '{status.fallback_name}' for '{name}'")
            return status.fallback_module
        else:
            logger.warning(f"Dependency '{name}' and fallbacks unavailable")
            return None
    
    def is_available(self, name: str) -> bool:
        """Check if a dependency (or its fallback) is available."""
        if name not in self._dependencies:
            return False
        
        status = self._dependencies[name]
        return status.is_available or status.fallback_available
    
    def get_status(self, name: str) -> Optional[DependencyStatus]:
        """Get detailed status of a dependency."""
        return self._dependencies.get(name)
    
    def get_all_status(self) -> Dict[str, DependencyStatus]:
        """Get status of all tracked dependencies."""
        return self._dependencies.copy()
    
    def register_fallback_handler(self, dep_name: str, handler: Callable):
        """Register a custom fallback handler for a dependency."""
        self._fallback_handlers[dep_name] = handler
        logger.info(f"Registered fallback handler for '{dep_name}'")
    
    def lazy_import(self, module_name: str, fallback_modules: Optional[List[str]] = None) -> Optional[Any]:
        """Perform lazy import with fallback support."""
        if module_name in self._lazy_imports:
            return self._lazy_imports[module_name]
        
        # Try main module
        try:
            module = importlib.import_module(module_name)
            self._lazy_imports[module_name] = module
            return module
        except ImportError as e:
            logger.warning(f"Failed to import '{module_name}': {e}")
        
        # Try fallbacks
        if fallback_modules:
            for fallback in fallback_modules:
                try:
                    module = importlib.import_module(fallback)
                    self._lazy_imports[module_name] = module
                    logger.info(f"Using fallback '{fallback}' for '{module_name}'")
                    return module
                except ImportError:
                    continue
        
        self._lazy_imports[module_name] = None
        return None
    
    def require_dependency(self, name: str, feature_name: str = "this feature"):
        """Decorator to require a dependency for a function."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.is_available(name):
                    error_msg = f"Cannot use {feature_name}: dependency '{name}' is not available"
                    logger.error(error_msg)
                    raise ImportError(error_msg)
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def optional_dependency(self, name: str, default_return=None, warning_message: Optional[str] = None):
        """Decorator for functions that can work without a dependency."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.is_available(name):
                    if warning_message:
                        logger.warning(warning_message)
                    else:
                        logger.warning(f"Dependency '{name}' not available, using fallback behavior")
                    return default_return
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def get_dependency_report(self) -> str:
        """Generate a human-readable dependency status report."""
        report = ["\n=== Dependency Status Report ==="]
        
        available = []
        fallback = []
        unavailable = []
        
        for name, status in self._dependencies.items():
            if status.is_available:
                available.append(name)
            elif status.fallback_available:
                fallback.append(f"{name} (using {status.fallback_name})")
            else:
                unavailable.append(f"{name} - {status.error or 'Unknown error'}")
        
        if available:
            report.append(f"\n✓ Available ({len(available)}):")
            for dep in available:
                report.append(f"  - {dep}")
        
        if fallback:
            report.append(f"\n⚠ Using Fallbacks ({len(fallback)}):")
            for dep in fallback:
                report.append(f"  - {dep}")
        
        if unavailable:
            report.append(f"\n✗ Unavailable ({len(unavailable)}):")
            for dep in unavailable:
                report.append(f"  - {dep}")
        
        report.append("\n" + "="*35)
        return "\n".join(report)

# Global dependency manager instance
dependency_manager = DependencyManager()

# Convenience functions
def get_dependency(name: str) -> Optional[Any]:
    """Get a dependency using the global manager."""
    return dependency_manager.get_dependency(name)

def is_dependency_available(name: str) -> bool:
    """Check if a dependency is available using the global manager."""
    return dependency_manager.is_available(name)

def require_dependency(name: str, feature_name: str = "this feature"):
    """Decorator to require a dependency."""
    return dependency_manager.require_dependency(name, feature_name)

def optional_dependency(name: str, default_return=None, warning_message: Optional[str] = None):
    """Decorator for optional dependencies."""
    return dependency_manager.optional_dependency(name, default_return, warning_message)

def print_dependency_report():
    """Print the dependency status report."""
    print(dependency_manager.get_dependency_report())

if __name__ == "__main__":
    # Print dependency report when run directly
    print_dependency_report()