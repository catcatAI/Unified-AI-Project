#!/usr/bin/env python3
"""
Unified AI Project Startup Script with Dependency Fallbacks

This script provides a robust startup mechanism that:
1. Checks all dependencies before starting
2. Provides fallback options for missing dependencies
3. Configures the application based on available dependencies
4. Offers different startup modes (minimal, standard, full)
"""

import sys
import os
import argparse
import warnings
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml # Added

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.core_ai.dependency_manager import (
        get_dependency_info,
        get_available_dependencies,
        get_unavailable_dependencies,
        get_disabled_features,
        is_dependency_available
    )
    from src.tools.dependency_checker import DependencyChecker
except ImportError as e:
    print(f"Warning: Could not import dependency management modules: {e}")
    print("Some features may not be available.")
    
    # Fallback implementations
    def get_dependency_info(name: str) -> Dict[str, Any]:
        return {'name': name, 'available': False}
    
    def get_available_dependencies() -> List[str]:
        return []
    
    def get_unavailable_dependencies() -> List[str]:
        return []
    
    def get_disabled_features() -> List[str]:
        return []
    
    def is_dependency_available(name: str) -> bool:
        try:
            __import__(name)
            return True
        except ImportError:
            return False
    
    class DependencyChecker:
        def print_status_report(self, detailed=False):
            print("Dependency checker not available")


class StartupManager:
    """Manages application startup with dependency fallbacks."""
    
    def __init__(self):
        # Load dependency configuration
        config_path = Path(__file__).parent / "dependency_config.yaml"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.dependency_config = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Error: dependency_config.yaml not found at {config_path}", file=sys.stderr)
            self.dependency_config = {} # Fallback to empty config
        except yaml.YAMLError as e:
            print(f"Error parsing dependency_config.yaml: {e}", file=sys.stderr)
            self.dependency_config = {} # Fallback to empty config

        # Initialize startup modes from dependency_config.yaml
        self.startup_modes = self._load_startup_modes_from_config()
        
        self.fallback_configs = {
            'web_server': {
                'primary': 'fastapi',
                'fallbacks': ['Flask'],
                'config_changes': {
                    'Flask': {'async_support': False, 'auto_reload': True}
                }
            },
            'ai_models': {
                'primary': 'tensorflow',
                'fallbacks': ['scikit-learn', 'numpy'],
                'config_changes': {
                    'scikit-learn': {'model_type': 'traditional_ml'},
                    'numpy': {'model_type': 'basic_math'}
                }
            },
            'nlp': {
                'primary': 'spacy',
                'fallbacks': ['nltk', 'textblob'],
                'config_changes': {
                    'nltk': {'download_required': ['punkt', 'stopwords']},
                    'textblob': {'sentiment_only': True}
                }
            },
            'mqtt_client': {
                'primary': 'paho-mqtt',
                'fallbacks': ['asyncio-mqtt'],
                'config_changes': {
                    'asyncio-mqtt': {'async_mode': True}
                }
            }
        }
    
    def _load_startup_modes_from_config(self) -> Dict[str, Any]:
        """Loads startup modes from the dependency configuration."""
        modes = {}
        installation_configs = self.dependency_config.get('installation', {})
        for mode_name, details in installation_configs.items():
            # Assuming 'packages' in installation config are 'required_deps' for startup modes
            # and there are no explicit 'optional_deps' or 'features' defined in dependency_config.yaml
            # for startup modes. If needed, these would be derived or added to dependency_config.yaml.
            modes[mode_name] = {
                'description': details.get('description', f'{mode_name} installation'),
                'required_deps': details.get('packages', []),
                'optional_deps': [], # Not explicitly defined in dependency_config.yaml for installation types
                'features': details.get('features', []) # Now extracting features from dependency_config.yaml
            }
        return modes

    def check_mode_compatibility(self, mode: str) -> Dict[str, Any]:
        """Check if a startup mode is compatible with current environment."""
        if mode not in self.startup_modes:
            return {'compatible': False, 'error': f'Unknown mode: {mode}'}
        
        mode_config = self.startup_modes[mode]
        missing_required = []
        missing_optional = []
        available_features = []
        
        # Check required dependencies
        for dep in mode_config['required_deps']:
            if not is_dependency_available(dep):
                missing_required.append(dep)
        
        # Optional dependencies are not explicitly defined in dependency_config.yaml for installation types
        # so we will assume they are empty for now.
        # If optional dependencies are needed, they should be added to dependency_config.yaml.
        missing_optional = []
        
        # Determine available features based on dependencies
        for feature in mode_config['features']:
            if self._is_feature_available(feature):
                available_features.append(feature)
        
        compatible = len(missing_required) == 0
        
        return {
            'compatible': compatible,
            'mode': mode,
            'missing_required': missing_required,
            'missing_optional': missing_optional,
            'available_features': available_features,
            'disabled_features': [f for f in mode_config['features'] if f not in available_features]
        }
    
    def _is_feature_available(self, feature: str) -> bool:
        """Check if a feature is available based on dependencies."""
        feature_deps = {
            'basic_web': ['Flask'],
            'web_api': ['Flask'],  # Can fallback from FastAPI
            'hsp_communication': ['paho-mqtt'],
            'core_ai': ['numpy'],
            'ai_models': ['numpy'],  # Can work with basic math if TensorFlow unavailable
            'nlp': ['numpy'],  # Can work with basic text processing
            'machine_learning': ['numpy'],  # Can work with basic algorithms
            'knowledge_graph': ['networkx']
        }
        
        if feature not in feature_deps:
            return False # Feature not defined in feature_deps
        
        required_deps = feature_deps.get(feature, [])
        return all(is_dependency_available(dep) for dep in required_deps)
    
    def suggest_best_mode(self) -> str:
        """Suggest the best startup mode based on available dependencies."""
        mode_scores = {}
        
        for mode_name, mode_config in self.startup_modes.items():
            compatibility = self.check_mode_compatibility(mode_name)
            if compatibility['compatible']:
                # Score based on available features
                score = len(compatibility['available_features'])
                # No bonus for optional dependencies as they are not explicitly defined in dependency_config.yaml
                mode_scores[mode_name] = score
        
        if not mode_scores:
            return 'minimal'  # Fallback to minimal if nothing else works
        
        return max(mode_scores, key=mode_scores.get)
    
    def configure_fallbacks(self) -> Dict[str, Any]:
        """Configure fallback options for missing dependencies."""
        fallback_config = {}
        
        for component, config in self.fallback_configs.items():
            primary = config['primary']
            fallbacks = config['fallbacks']
            
            if is_dependency_available(primary):
                fallback_config[component] = {
                    'active': primary,
                    'type': 'primary'
                }
            else:
                # Try fallbacks
                for fallback in fallbacks:
                    if is_dependency_available(fallback):
                        fallback_config[component] = {
                            'active': fallback,
                            'type': 'fallback',
                            'config_changes': config['config_changes'].get(fallback, {})
                        }
                        break
                else:
                    fallback_config[component] = {
                        'active': None,
                        'type': 'disabled',
                        'reason': f'Neither {primary} nor fallbacks {fallbacks} are available'
                    }
        
        return fallback_config
    
    def start_application(self, mode: str = 'auto', port: int = 5000, host: str = '127.0.0.1', debug: bool = False):
        """Start the application with the specified mode and fallbacks."""
        print("🚀 Starting Unified AI Project...")
        print("="*50)
        
        # Auto-detect best mode if requested
        if mode == 'auto':
            mode = self.suggest_best_mode()
            print(f"🔍 Auto-detected best mode: {mode}")
        
        # Check mode compatibility
        compatibility = self.check_mode_compatibility(mode)
        if not compatibility['compatible']:
            print(f"❌ Mode '{mode}' is not compatible:")
            print(f"   Missing required dependencies: {compatibility['missing_required']}")
            print("\n💡 Trying to find alternative mode...")
            mode = self.suggest_best_mode()
            compatibility = self.check_mode_compatibility(mode)
            print(f"✅ Switching to mode: {mode}")
        
        # Configure fallbacks
        fallback_config = self.configure_fallbacks()
        
        # Print startup information
        print(f"\n📋 Startup Configuration:")
        print(f"   Mode: {mode} - {self.startup_modes[mode]['description']}")
        print(f"   Available Features: {', '.join(compatibility['available_features'])}")
        
        if compatibility['disabled_features']:
            print(f"   Disabled Features: {', '.join(compatibility['disabled_features'])}")
        
        
        
        print(f"\n🔧 Component Configuration:")
        for component, config in fallback_config.items():
            if config['type'] == 'primary':
                print(f"   ✅ {component}: {config['active']} (primary)")
            elif config['type'] == 'fallback':
                print(f"   🔄 {component}: {config['active']} (fallback)")
            else:
                print(f"   ❌ {component}: disabled - {config['reason']}")
        
        # Set environment variables for the application
        os.environ['UNIFIED_AI_MODE'] = mode
        os.environ['UNIFIED_AI_FALLBACK_CONFIG'] = str(fallback_config)
        
        # Start the appropriate server based on available dependencies
        web_config = fallback_config.get('web_server', {})
        if web_config.get('active') == 'fastapi' and is_dependency_available('fastapi'):
            self._start_fastapi_server(host, port, debug)
        elif web_config.get('active') == 'Flask' or is_dependency_available('Flask'):
            self._start_flask_server(host, port, debug)
        else:
            print("❌ No web server available. Running in CLI mode only.")
            self._start_cli_mode()
    
    def _start_fastapi_server(self, host: str, port: int, debug: bool):
        """Start FastAPI server."""
        try:
            print(f"\n🌐 Starting FastAPI server on http://{host}:{port}")
            # Import and start FastAPI app
            # This would be implemented based on your actual FastAPI app structure
            print("FastAPI server startup would be implemented here")
        except Exception as e:
            print(f"❌ Failed to start FastAPI server: {e}")
            print("🔄 Falling back to Flask...")
            self._start_flask_server(host, port, debug)
    
    def _start_flask_server(self, host: str, port: int, debug: bool):
        """Start Flask server."""
        try:
            print(f"\n🌐 Starting Flask server on http://{host}:{port}")
            # Import and start Flask app
            # This would be implemented based on your actual Flask app structure
            print("Flask server startup would be implemented here")
        except Exception as e:
            print(f"❌ Failed to start Flask server: {e}")
            self._start_cli_mode()
    
    def _start_cli_mode(self):
        """Start in CLI-only mode."""
        print("\n💻 Starting in CLI mode...")
        print("Available commands:")
        print("  - check-deps: Check dependency status")
        print("  - test-ai: Test AI functionality")
        print("  - exit: Exit application")
        
        while True:
            try:
                command = input("\nUnified-AI> ").strip().lower()
                if command == 'exit':
                    break
                elif command == 'check-deps':
                    checker = DependencyChecker()
                    checker.print_status_report()
                elif command == 'test-ai':
                    print("AI functionality test would be implemented here")
                else:
                    print(f"Unknown command: {command}")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Start Unified AI Project with dependency fallbacks"
    )
    parser.add_argument(
        '--mode', '-m',
        choices=['auto', 'minimal', 'standard', 'full', 'ai_focused'],
        default='auto',
        help='Startup mode (default: auto-detect)'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=5000,
        help='Port for web server (default: 5000)'
    )
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Host for web server (default: 127.0.0.1)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Only check dependencies without starting'
    )
    parser.add_argument(
        '--suggest-mode',
        action='store_true',
        help='Suggest best mode and exit'
    )
    
    args = parser.parse_args()
    
    startup_manager = StartupManager()
    
    if args.check_only:
        checker = DependencyChecker()
        checker.print_status_report(detailed=True)
        return
    
    if args.suggest_mode:
        suggested = startup_manager.suggest_best_mode()
        print(f"Suggested mode: {suggested}")
        compatibility = startup_manager.check_mode_compatibility(suggested)
        print(f"Available features: {', '.join(compatibility['available_features'])}")
        if compatibility['disabled_features']:
            print(f"Disabled features: {', '.join(compatibility['disabled_features'])}")
        return
    
    # Start the application
    startup_manager.start_application(
        mode=args.mode,
        port=args.port,
        host=args.host,
        debug=args.debug
    )


if __name__ == "__main__":
    main()