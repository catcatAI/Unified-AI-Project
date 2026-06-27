import logging
import os
import sys

import pytest

logger = logging.getLogger(__name__)

project_root = os.path.join(os.path.dirname(__file__), '..', '..')


if __name__ == "__main__":
    os.chdir(project_root)

    result = pytest.main([
        '-v',
        '--tb=short',
        'apps/backend/tests/test_hsp_fixture_fix.py'
    ])

    print(f"Test result: {result}")
    sys.exit(result)