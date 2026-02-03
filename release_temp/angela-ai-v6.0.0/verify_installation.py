"""
Angela AI Installation Verification Script
Tests if Angela is properly installed and can run
"""

import sys
import os
from pathlib import Path

def check_structure():
    """Check if directory structure is correct"""
    print("📂 Checking directory structure...")
    
    required_dirs = [
        "apps/backend/src/core/autonomous",
        "apps/backend/src/ai/learning",
        "apps/backend/src/ai/memory",
        "apps/backend/src/core/lu",
        "config",
        "resources",
        "data",
        "logs",
        "temp"
    ]
    
    missing = []
    for d in required_dirs:
        if not Path(d).exists():
            missing.append(d)
            print(f"  ❌ Missing: {d}")
        else:
            print(f"  ✅ {d}")
    
    return len(missing) == 0

def check_files():
    """Check if required files exist"""
    print("\n📄 Checking required files...")
    
    required_files = [
        "run_angela.py",
        "setup.py",
        "requirements.txt",
        "apps/backend/main.py",
        "apps/backend/src/core/autonomous/__init__.py",
        "apps/backend/src/core/autonomous/digital_life_integrator.py"
    ]
    
    missing = []
    for f in required_files:
        if not Path(f).exists():
            missing.append(f)
            print(f"  ❌ Missing: {f}")
        else:
            print(f"  ✅ {f}")
    
    return len(missing) == 0

def check_imports():
    """Test critical imports"""
    print("\n🐍 Testing critical imports...")
    
    # Setup path
    backend_path = Path("apps/backend")
    sys.path.insert(0, str(backend_path))
    sys.path.insert(0, str(backend_path / "src"))
    
    critical_modules = [
        "core.autonomous",
        "core.autonomous.digital_life_integrator",
        "core.autonomous.action_executor",
        "core.autonomous.biological_integrator"
    ]
    
    failed = []
    for module in critical_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except Exception as e:
            failed.append((module, str(e)))
            print(f"  ❌ {module}: {e}")
    
    return len(failed) == 0

def check_dependencies():
    """Check if dependencies are installed"""
    print("\n📦 Checking dependencies...")
    
    critical_deps = [
        "fastapi", "uvicorn", "pydantic", "numpy", "requests"
    ]
    
    missing = []
    for dep in critical_deps:
        try:
            __import__(dep.replace("-", "_").replace("yaml", "pyyaml"))
            print(f"  ✅ {dep}")
        except ImportError:
            missing.append(dep)
            print(f"  ❌ {dep}")
    
    if missing:
        print(f"\n💡 Run: pip install {' '.join(missing)}")
    
    return len(missing) == 0

def main():
    print("=" * 60)
    print("🔍 Angela AI Installation Verification")
    print("=" * 60)
    
    checks = [
        ("Directory Structure", check_structure),
        ("Required Files", check_files),
        ("Python Imports", check_imports),
        ("Dependencies", check_dependencies)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{'='*60}")
        print(f"📋 {name}")
        print("="*60)
        success = check_func()
        results.append((name, success))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Verification Summary")
    print("=" * 60)
    
    all_passed = True
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")
        if not success:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All checks passed! Angela is ready to run.")
        print("\nStart Angela with:")
        print("  python run_angela.py")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
