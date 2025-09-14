"""
Dependency Manager for Unified AI Project
Handles dependency loading with fallback support.
"""

import importlib
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from enum import Enum
from unittest.mock import MagicMock


class DependencyStatus(Enum):
    """Status of a dependency."""
    AVAILABLE = "available"
    FALLBACK = "fallback"
    UNAVAILABLE = "unavailable"


class DependencyInfo:
    """Information about a dependency."""
    
    def __init__(self, name: str, is_available: bool, fallback_available: bool = False, fallback_name: str = None, error: str = None):
        self.name = name
        self.is_available = is_available
        self.fallback_available = fallback_available
        self.fallback_name = fallback_name
        self.error = error
        self.module = None
    
    def __repr__(self):
        return f"DependencyInfo(name={self.name}, available={self.is_available}, fallback={self.fallback_available}, fallback_name={self.fallback_name})"


class DependencyManager:
    """Manages dependencies with fallback support."""
    
    def __init__(self, config_path: str = "dependency_config.yaml"):
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._dependencies: Dict[str, DependencyInfo] = {}
        self._loaded_modules: Dict[str, Any] = {}
        
        # Load configuration if file exists
        if self.config_path.exists():
            self._load_config()
        else:
            self._use_default_config()
        
        self._setup_dependency_statuses()
    
    def _load_config(self):
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Warning: Dependency config file not found at {self.config_path}")
            self._use_default_config()
        except Exception as e:
            print(f"Warning: Could not load dependency config from {self.config_path}: {e}")
            self._use_default_config()
    
    def _use_default_config(self):
        """Use default configuration."""
        self._config = {
            'dependencies': {
                'core': [
                    {'name': 'essential_lib', 'fallbacks': ['essential_fallback'], 'essential': True},
                    {'name': 'normal_lib', 'fallbacks': ['normal_fallback'], 'essential': False},
                    {'name': 'no_fallback_lib', 'fallbacks': [], 'essential': False},
                    {'name': 'unavailable_lib', 'fallbacks': ['unavailable_fallback'], 'essential': False},
                    {'name': 'paho-mqtt', 'fallbacks': ['asyncio-mqtt'], 'essential': True},
                ]
            },
            'environments': {
                'development': {
                    'allow_fallbacks': True,
                    'warn_on_fallback': True,
                },
                'production': {
                    'allow_fallbacks': False,
                }
            }
        }
    
    def _setup_dependency_statuses(self):
        """Set up the status of all dependencies."""
        # Check environment for fallback settings
        import os
        env = os.environ.get('UNIFIED_AI_ENV', 'development')
        env_config = self._config.get('environments', {}).get(env, {})
        allow_fallbacks = env_config.get('allow_fallbacks', True)
        
        for dep_config in self._config.get('dependencies', {}).get('core', []):
            name = dep_config['name']
            fallbacks = dep_config.get('fallbacks', [])
            essential = dep_config.get('essential', False)
            
            # Try to load primary dependency
            is_available = False
            fallback_available = False
            fallback_name = None
            error = None
            
            try:
                # Handle special case for paho-mqtt -> paho.mqtt.client
                import_name = name
                if name == 'paho-mqtt':
                    import_name = 'paho.mqtt.client'
                
                module = importlib.import_module(import_name)
                self._loaded_modules[name] = module
                is_available = True
            except ImportError as e:
                error = str(e)
                # Try fallbacks only if allowed
                if allow_fallbacks or essential:
                    for fallback_name in fallbacks:
                        try:
                            module = importlib.import_module(fallback_name)
                            self._loaded_modules[fallback_name] = module
                            fallback_available = True
                            break
                        except ImportError:
                            continue
            
            self._dependencies[name] = DependencyInfo(
                name=name,
                is_available=is_available,
                fallback_available=fallback_available,
                fallback_name=fallback_name if fallback_available else None,
                error=error if not (is_available or fallback_available) else None
            )
    
    def is_available(self, dependency_name: str) -> bool:
        """Check if a dependency is available (either primary or fallback)."""
        if dependency_name not in self._dependencies:
            return False
        
        dep_info = self._dependencies[dependency_name]
        return dep_info.is_available or dep_info.fallback_available
    
    def get_status(self, dependency_name: str) -> Optional[DependencyInfo]:
        """Get the status of a dependency."""
        return self._dependencies.get(dependency_name)
    
    def get_dependency(self, dependency_name: str) -> Optional[Any]:
        """Get the loaded module for a dependency."""
        # Try primary first
        if dependency_name in self._loaded_modules:
            return self._loaded_modules[dependency_name]
        
        # Try fallbacks
        dep_info = self._dependencies.get(dependency_name)
        if dep_info and dep_info.fallback_available and dep_info.fallback_name:
            if dep_info.fallback_name in self._loaded_modules:
                return self._loaded_modules[dep_info.fallback_name]
        
        return None
    
    def list_dependencies(self) -> Dict[str, DependencyInfo]:
        """List all dependencies and their status."""
        return self._dependencies.copy()
    
    def get_all_status(self) -> Dict[str, DependencyInfo]:
        """Get all dependency status information."""
        return self._dependencies.copy()
    
    def get_dependency_report(self) -> str:
        """Generate a human-readable dependency report."""
        available = []
        fallbacks = []
        unavailable = []
        
        for name, dep_info in self._dependencies.items():
            if dep_info.is_available:
                available.append(f"- {name}")
            elif dep_info.fallback_available:
                fallbacks.append(f"- {name} (using {dep_info.fallback_name})")
            else:
                error_msg = f" - {dep_info.error}" if dep_info.error else ""
                unavailable.append(f"- {name}{error_msg}")
        
        report = []
        if available:
            report.append(f"✓ Available ({len(available)}):")
            report.extend(available)
            report.append("")
        
        if fallbacks:
            report.append(f"⚠ Using Fallbacks ({len(fallbacks)}):")
            report.extend(fallbacks)
            report.append("")
        
        if unavailable:
            report.append(f"✗ Unavailable ({len(unavailable)}):")
            report.extend(unavailable)
            report.append("")
        
        return "\n".join(report)
    
    def reload_dependency(self, dependency_name: str) -> bool:
        """Attempt to reload a dependency."""
        if dependency_name not in self._dependencies:
            return False
        
        # Clear existing module
        if dependency_name in self._loaded_modules:
            del self._loaded_modules[dependency_name]
        
        # Get dependency config
        dep_config = None
        for dep in self._config.get('dependencies', {}).get('core', []):
            if dep['name'] == dependency_name:
                dep_config = dep
                break
        
        if not dep_config:
            return False
        
        # Try to load again
        name = dep_config['name']
        fallbacks = dep_config.get('fallbacks', [])
        
        is_available = False
        fallback_available = False
        fallback_name = None
        error = None
        
        try:
            # Handle special case for paho-mqtt -> paho.mqtt.client
            import_name = name
            if name == 'paho-mqtt':
                import_name = 'paho.mqtt.client'
                
            module = importlib.import_module(import_name)
            self._loaded_modules[name] = module
            is_available = True
        except ImportError as e:
            error = str(e)
            for fallback_name in fallbacks:
                try:
                    module = importlib.import_module(fallback_name)
                    self._loaded_modules[fallback_name] = module
                    fallback_available = True
                    break
                except ImportError:
                    continue
        
        self._dependencies[name] = DependencyInfo(
            name=name,
            is_available=is_available,
            fallback_available=fallback_available,
            fallback_name=fallback_name if fallback_available else None,
            error=error if not (is_available or fallback_available) else None
        )
        
        return is_available or fallback_available