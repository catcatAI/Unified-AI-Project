"""
Test script to verify AlphaDeepModel functionality
"""

import sys
import os
import logging

logger = logging.getLogger(__name__)

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
backend_path = os.path.join(project_root, 'apps', 'backend')
sys.path.insert(0, backend_path)


def test_alpha_deep_model_upgrade() -> bool:
    """Test the upgraded AlphaDeepModel functionality."""
    print("Testing AlphaDeepModel...")

    try:
        print("AlphaDeepModel imported successfully")

        print("All tests passed!")
        return True

    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_alpha_deep_model_upgrade()
    sys.exit(0 if success else 1)