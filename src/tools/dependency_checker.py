#!/usr/bin/env python3
"""
Dependency Checker Tool

This tool provides utilities to check the status of project dependencies,
identify missing packages, and suggest installation commands.
"""

import sys
import os
import importlib
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.core_ai.dependency_manager import (
        get_dependency_info,
        get_available_dependencies,
        get_unavailable_dependencies,
        get_disabled_features,
        get_installation_recommendations,
        is_dependency_available
    )
except ImportError as e:
    print(f"Warning: Could not import dependency manager: {e}")
    print("Running in standalone mode...")
    
    def get_dependency_info(name: str) -> Dict[str, Any]:
        return {'name': name, 'available': False, 'type': 'unknown'}
    
    def get_available_dependencies() -> List[str]:
        return []
    
    def get_unavailable_dependencies() -> List[str]:
        return []
    
    def get_disabled_features() -> List[str]:
        return []
    
    def get_installation_recommendations() -> Dict[str, List[str]]:
        return {}
    
    def is_dependency_available(name: str) -> bool:
        try:
            importlib.import_module(name)
            return True
        except ImportError:
            return False


class DependencyChecker:
    """Tool for checking dependency status and providing recommendations."""
    
    def __init__(self):
        self.core_dependencies = [
            'Flask', 'numpy', 'cryptography', 'requests', 'python-dotenv',
            'PyYAML', 'typing-extensions', 'paho-mqtt', 'networkx', 'psutil'
        ]
        
        self.optional_dependencies = {
            'ai': ['tensorflow', 'spacy', 'langchain'],
            'web': ['fastapi', 'uvicorn', 'pydantic', 'httpx'],
            'testing': ['pytest-asyncio', 'pytest'],
            'nlp': ['spacy', 'nltk', 'textblob'],
            'ml': ['tensorflow', 'scikit-learn', 'pandas'],
            'dev': ['black', 'flake8', 'mypy', 'pre-commit']
        }
    
    def check_dependency(self, name: str) -> Dict[str, Any]:
        """Check the status of a single dependency."""
        try:
            module = importlib.import_module(name)
            version = getattr(module, '__version__', 'unknown')
            return {
                'name': name,
                'available': True,
                'version': version,
                'module': str(module),
                'location': getattr(module, '__file__', 'built-in')
            }
        except ImportError as e:
            return {
                'name': name,
                'available': False,
                'error': str(e),
                'version': None,
                'module': None,
                'location': None
            }
    
    def check_all_dependencies(self) -> Dict[str, Any]:
        """Check the status of all project dependencies."""
        results = {
            'core': {},
            'optional': {},
            'summary': {
                'total_core': len(self.core_dependencies),
                'available_core': 0,
                'total_optional': 0,
                'available_optional': 0,
                'disabled_features': get_disabled_features()
            }
        }
        
        # Check core dependencies
        for dep in self.core_dependencies:
            status = self.check_dependency(dep)
            results['core'][dep] = status
            if status['available']:
                results['summary']['available_core'] += 1
        
        # Check optional dependencies
        for category, deps in self.optional_dependencies.items():
            results['optional'][category] = {}
            for dep in deps:
                status = self.check_dependency(dep)
                results['optional'][category][dep] = status
                results['summary']['total_optional'] += 1
                if status['available']:
                    results['summary']['available_optional'] += 1
        
        return results
    
    def get_missing_dependencies(self) -> Dict[str, List[str]]:
        """Get lists of missing dependencies by category."""
        missing = {
            'core': [],
            'optional': {}
        }
        
        # Check core dependencies
        for dep in self.core_dependencies:
            if not self.check_dependency(dep)['available']:
                missing['core'].append(dep)
        
        # Check optional dependencies
        for category, deps in self.optional_dependencies.items():
            missing['optional'][category] = []
            for dep in deps:
                if not self.check_dependency(dep)['available']:
                    missing['optional'][category].append(dep)
        
        return missing
    
    def generate_install_commands(self, missing_deps: Dict[str, Any]) -> Dict[str, str]:
        """Generate pip install commands for missing dependencies."""
        commands = {}
        
        # Core dependencies
        if missing_deps['core']:
            commands['core'] = f"pip install {' '.join(missing_deps['core'])}"
        
        # Optional dependencies by category
        for category, deps in missing_deps['optional'].items():
            if deps:
                commands[f'optional_{category}'] = f"pip install {' '.join(deps)}"
        
        # Using setup.py extras
        recommendations = get_installation_recommendations()
        for install_type, packages in recommendations.items():
            if packages:
                commands[f'extras_{install_type}'] = f"pip install -e .[{install_type}]"
        
        return commands
    
    def print_status_report(self, detailed: bool = False):
        """Print a comprehensive dependency status report."""
        print("\n" + "="*60)
        print("UNIFIED AI PROJECT - DEPENDENCY STATUS REPORT")
        print("="*60)
        
        results = self.check_all_dependencies()
        summary = results['summary']
        
        # Summary
        print(f"\n📊 SUMMARY:")
        print(f"   Core Dependencies: {summary['available_core']}/{summary['total_core']} available")
        print(f"   Optional Dependencies: {summary['available_optional']}/{summary['total_optional']} available")
        
        if summary['disabled_features']:
            print(f"   ⚠️  Disabled Features: {', '.join(summary['disabled_features'])}")
        
        # Core dependencies status
        print(f"\n🔧 CORE DEPENDENCIES:")
        for dep, status in results['core'].items():
            icon = "✅" if status['available'] else "❌"
            version_info = f" (v{status['version']})" if status.get('version') and status['version'] != 'unknown' else ""
            print(f"   {icon} {dep}{version_info}")
            
            if detailed and not status['available']:
                print(f"      Error: {status.get('error', 'Unknown error')}")
        
        # Optional dependencies status
        print(f"\n🎯 OPTIONAL DEPENDENCIES:")
        for category, deps in results['optional'].items():
            available_count = sum(1 for status in deps.values() if status['available'])
            total_count = len(deps)
            print(f"\n   📦 {category.upper()} ({available_count}/{total_count} available):")
            
            for dep, status in deps.items():
                icon = "✅" if status['available'] else "❌"
                version_info = f" (v{status['version']})" if status.get('version') and status['version'] != 'unknown' else ""
                print(f"      {icon} {dep}{version_info}")
                
                if detailed and not status['available']:
                    print(f"         Error: {status.get('error', 'Unknown error')}")
        
        # Installation recommendations
        missing = self.get_missing_dependencies()
        if missing['core'] or any(missing['optional'].values()):
            print(f"\n💡 INSTALLATION RECOMMENDATIONS:")
            commands = self.generate_install_commands(missing)
            
            for cmd_type, command in commands.items():
                print(f"\n   {cmd_type.replace('_', ' ').title()}:")
                print(f"   {command}")
        
        # Environment info
        print(f"\n🌍 ENVIRONMENT INFO:")
        print(f"   Python Version: {sys.version.split()[0]}")
        print(f"   Python Executable: {sys.executable}")
        print(f"   Project Root: {project_root}")
        print(f"   Environment: {os.getenv('UNIFIED_AI_ENV', 'development')}")
        
        print("\n" + "="*60)
    
    def export_status_json(self, output_path: Optional[str] = None) -> str:
        """Export dependency status to JSON file."""
        results = self.check_all_dependencies()
        missing = self.get_missing_dependencies()
        commands = self.generate_install_commands(missing)
        
        export_data = {
            'timestamp': str(Path(__file__).stat().st_mtime),
            'python_version': sys.version,
            'environment': os.getenv('UNIFIED_AI_ENV', 'development'),
            'project_root': str(project_root),
            'dependency_status': results,
            'missing_dependencies': missing,
            'install_commands': commands
        }
        
        if output_path is None:
            output_path = project_root / "dependency_status.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return str(output_path)


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Check dependency status for Unified AI Project"
    )
    parser.add_argument(
        '--detailed', '-d',
        action='store_true',
        help='Show detailed error information'
    )
    parser.add_argument(
        '--json', '-j',
        type=str,
        nargs='?',
        const='dependency_status.json',
        help='Export status to JSON file (optional filename)'
    )
    parser.add_argument(
        '--check',
        type=str,
        help='Check specific dependency'
    )
    
    args = parser.parse_args()
    
    checker = DependencyChecker()
    
    if args.check:
        # Check specific dependency
        status = checker.check_dependency(args.check)
        if status['available']:
            print(f"✅ {args.check} is available (version: {status.get('version', 'unknown')})")
        else:
            print(f"❌ {args.check} is not available: {status.get('error', 'Unknown error')}")
    else:
        # Full status report
        checker.print_status_report(detailed=args.detailed)
        
        if args.json:
            output_path = checker.export_status_json(args.json)
            print(f"\n📄 Status exported to: {output_path}")


if __name__ == "__main__":
    main()