"""Integration: services.main_api_server imports via full module path."""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).parent.parent.parent)
SRC_PATH = str(Path(PROJECT_ROOT) / 'apps' / 'backend' / 'src')


def test_main_api_server_imports():
    """Verify the module can be imported via full dotted path.
    Uses subprocess to isolate heavy top-level module code.
    """
    code = (
        f'import sys; sys.path.insert(0, {str(PROJECT_ROOT)!r}); '
        f'sys.path.insert(0, {str(SRC_PATH)!r}); '
        'import apps.backend.src.services.main_api_server as m; '
        'print(m.__name__)'
    )
    result = subprocess.run(
        [sys.executable, '-c', code],
        capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, f'stderr: {result.stderr[:500]}'
    assert 'main_api_server' in result.stdout


def test_module_has_expected_attributes():
    """Key top-level attributes exist on the module."""
    code = (
        f'import sys; sys.path.insert(0, {str(PROJECT_ROOT)!r}); '
        f'sys.path.insert(0, {str(SRC_PATH)!r}); '
        'import apps.backend.src.services.main_api_server as m; '
        'assert hasattr(m, "app"), "missing app"; '
        'assert hasattr(m, "MainApiServer"), "missing MainApiServer"; '
        'assert hasattr(m, "message_manager"), "missing message_manager"; '
        'assert callable(getattr(m, "get_llm_service", None)), "missing get_llm_service"; '
        'assert callable(getattr(m, "setup_middleware", None)), "missing setup_middleware"; '
        'print("OK")'
    )
    result = subprocess.run(
        [sys.executable, '-c', code],
        capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, f'stderr: {result.stderr[:500]}'
    assert 'OK' in result.stdout
