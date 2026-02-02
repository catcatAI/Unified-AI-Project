"""
Configuration for pytest: Add project root and backend source to the Python path,
and set environment variables for transformers.
"""

import sys
import os
from unittest.mock import MagicMock

# Set environment variable to prevent transformers from importing TensorFlow
os.environ["TRANSFORMERS_NO_TF_IMPORT"] = "1"

# Add the project root directory to the Python path to resolve import issues.
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT) # Re-add PROJECT_ROOT

# Add the backend's source directory to the Python path for module discovery
BACKEND_SRC_PATH = os.path.join(PROJECT_ROOT, "apps", "backend", "src")
sys.path.insert(0, BACKEND_SRC_PATH) # Insert at the beginning

def pytest_configure(config):
    """
    Pytest hook to configure the test environment before tests are collected.
    Mocks TensorFlow and Keras to prevent transformers from attempting to import them,
    which causes ModuleNotFoundError when they are not installed.
    """
    # Mock tensorflow and keras to prevent transformers from trying to import them
    # This is a workaround for transformers' aggressive TensorFlow import behavior
    # even when TRANSFORMERS_NO_TF_IMPORT is set.
    sys.modules['tensorflow'] = MagicMock()
    sys.modules['tensorflow.python'] = MagicMock()
    sys.modules['tensorflow.python.trackable'] = MagicMock()
    sys.modules['keras'] = MagicMock()
    sys.modules['tf_keras'] = MagicMock()
    sys.modules['keras.src'] = MagicMock()
    sys.modules['keras.src.backend'] = MagicMock()
    sys.modules['keras.src.backend.common'] = MagicMock()
    sys.modules['keras.src.backend.common.dtypes'] = MagicMock()
    sys.modules['keras.src.backend.common.variables'] = MagicMock()
    sys.modules['keras.src.utils'] = MagicMock()
    sys.modules['keras.src.utils.naming'] = MagicMock()
    sys.modules['keras.src.utils.module_utils'] = MagicMock()
    sys.modules['keras.src.utils.audio_dataset_utils'] = MagicMock()
    sys.modules['keras.src.utils.dataset_utils'] = MagicMock()
    sys.modules['keras.src.tree'] = MagicMock()
    sys.modules['keras.src.tree.tree_api'] = MagicMock()
    sys.modules['keras.src.tree.optree_impl'] = MagicMock()
    sys.modules['transformers.integrations.tensorflow'] = MagicMock() # Specific transformers integration

    # Mock importlib.util.find_spec to explicitly state tensorflow is not available
    import importlib.util
    original_find_spec = importlib.util.find_spec
    def mock_find_spec(name, package=None):
        if name == "tensorflow":
            return None
        return original_find_spec(name, package)
    importlib.util.find_spec = mock_find_spec
    
    # Ensure that the original import in test_tool_dispatcher.py is restored
    # from apps.backend.src.core.tools.tool_dispatcher import ToolDispatcher
    # This will be handled by the sys.path modification above.