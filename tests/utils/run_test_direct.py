import sys
import pytest
import logging

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    import os

    result = pytest.main([
        '-v',
        '--tb=short',
        'apps/backend/tests/hsp/test_basic.py::test_basic'
    ])

    print(f"Test result: {result}")
    sys.exit(result)