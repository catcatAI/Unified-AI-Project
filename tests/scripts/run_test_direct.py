import sys
import os
import pytest
import logging

logger = logging.getLogger(__name__)

project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))


if __name__ == "__main__":
    os.chdir(project_root)

    result = pytest.main([
        '-v',
        '--tb=short',
        'apps/backend/tests/hsp/test_basic.py::test_basic'
    ])

    print(f"Test result: {result}")
    sys.exit(result)