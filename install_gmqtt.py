#!/usr/bin/env python3
"""
Script to install the gmqtt package if it's missing.
"""
import subprocess
import sys

def check_and_install_gmqtt():
    """Check if gmqtt is installed, and install it if missing."""
    try:
        import gmqtt  # type: ignore
        _ = gmqtt  # noqa: F841
        print("✅ gmqtt is already installed")
        return True
    except ImportError:
        print("❌ gmqtt is not installed. Installing now...")
        
    try:
        # Try to install gmqtt using pip
        _ = subprocess.check_call([sys.executable, "-m", "pip", "install", "gmqtt"])
        print("✅ gmqtt installed successfully")
        
        # Verify installation
        import gmqtt  # type: ignore
        _ = gmqtt  # noqa: F841
        print("✅ gmqtt imported successfully after installation")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install gmqtt: {e}")
        return False
    except ImportError as e:
        print(f"❌ gmqtt installed but still cannot be imported: {e}")
        return False

if __name__ == "__main__":
    success = check_and_install_gmqtt()
    if success:
        print("🎉 All good! gmqtt is ready to use.")
        sys.exit(0)
    else:
        print("💥 Failed to setup gmqtt. Please check your Python environment.")
        sys.exit(1)