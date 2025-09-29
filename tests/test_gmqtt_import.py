#!/usr/bin/env python3
"""
Test script to verify gmqtt import and ExternalConnector functionality.
"""
import sys
import os

# Add the src directory to the path so we can import the module
_ = sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'backend', 'src'))

# Add type checking ignore for the entire file
# pyright: reportMissingImports=false

def test_gmqtt_import() -> None:
    """Test that gmqtt can be imported."""
    try:
        import gmqtt  # type: ignore
        _ = gmqtt  # noqa: F841
        _ = print("✅ gmqtt imported successfully")
        return True
    except ImportError as e:
        _ = print(f"❌ Failed to import gmqtt: {e}")
        return False

def test_external_connector_import() -> None:
    """Test that ExternalConnector can be imported."""
    try:
        from apps.backend.src.core.hsp.external.external_connector import ExternalConnector  # type: ignore
        _ = ExternalConnector  # noqa: F841
        _ = print("✅ ExternalConnector imported successfully")
        return True
    except ImportError as e:
        _ = print(f"❌ Failed to import ExternalConnector: {e}")
        return False

def test_external_connector_creation() -> None:
    """Test that ExternalConnector can be instantiated."""
    try:
        from apps.backend.src.core.hsp.external.external_connector import ExternalConnector  # type: ignore
        connector = ExternalConnector(
            ai_id="test_ai",
            broker_address="localhost",
            broker_port=1883
        )
        _ = connector  # noqa: F841
        _ = print("✅ ExternalConnector created successfully")
        return True
    except Exception as e:
        _ = print(f"❌ Failed to create ExternalConnector: {e}")
        return False

if __name__ == "__main__":
    _ = print("Testing gmqtt and ExternalConnector functionality...")
    
    success = True
    success &= test_gmqtt_import()
    success &= test_external_connector_import()
    success &= test_external_connector_creation()
    
    if success:
        _ = print("\n🎉 All tests passed!")
        _ = sys.exit(0)
    else:
        _ = print("\n💥 Some tests failed!")
        _ = sys.exit(1)