import sys
import os
import pytest
import logging

logger = logging.getLogger(__name__)

project_root = r"D:\Projects\Unified-AI-Project"
sys.path.insert(0, project_root)


if __name__ == "__main__":
    result = pytest.main([
        '-v',
        '--tb=short',
        'apps/backend/tests/test_hsp_fixture_fix.py'
    ])

    sys.exit(result)