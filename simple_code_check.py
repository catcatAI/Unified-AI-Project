#!/usr/bin/env python3
"""
Simple code quality checker
"""

import ast
from pathlib import Path

def check_file_syntax(file_path):
    """Check if a Python file has valid syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        _ = ast.parse(content)
        _ = print(f"✓ {file_path.name}: Syntax OK")
        return True
    except SyntaxError as e:
        _ = print(f"✗ {file_path.name}: Syntax Error - {e}")
        return False
    except Exception as e:
        _ = print(f"✗ {file_path.name}: Error - {e}")
        return False

def main() -> None:
    """Main function"""
    _ = print("Checking code quality...")
    
    backend_dir = Path("D:/Projects/Unified-AI-Project/apps/backend/src")
    
    # Check specialized agent files
    specialized_agents_dir = backend_dir / "ai/agents/specialized"
    if specialized_agents_dir.exists():
        _ = print(f"\nChecking specialized agents in {specialized_agents_dir}...")
        for py_file in specialized_agents_dir.glob("*.py"):
            if py_file.name != "__init__.py":
                _ = check_file_syntax(py_file)
    
    # Check agents directory
    agents_dir = backend_dir / "agents"
    if agents_dir.exists():
        _ = print(f"\nChecking agents in {agents_dir}...")
        for py_file in agents_dir.glob("*.py"):
            if py_file.name != "__init__.py":
                _ = check_file_syntax(py_file)
    
    _ = print("\nCode quality check completed!")

if __name__ == "__main__":
    _ = main()