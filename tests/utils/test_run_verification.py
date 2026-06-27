import logging
import sys

import pytest

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    result = pytest.main([
        '-v',
        '--tb=short',
        'apps/backend/tests/test_hsp_fixture_fix.py'
    ])

    sys.exit(result)