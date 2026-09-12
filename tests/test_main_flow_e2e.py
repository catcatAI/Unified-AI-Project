"""Main-flow e2e gate (R11): scripts/verify_main_flow_e2e.py must exit 0.

Subprocess run (~10s, no network, no user-state writes): proves the
production chain classify → gate → execute works for real inputs.
"""

import os
import subprocess
import sys


def test_main_flow_e2e_passes():
    repo_root = os.path.join(os.path.dirname(__file__), "..")
    p = subprocess.run(
        [sys.executable, os.path.join(repo_root, "scripts", "verify_main_flow_e2e.py")],
        capture_output=True,
        text=True,
        timeout=180,
        cwd=repo_root,
    )
    assert p.returncode == 0, p.stdout[-1500:] + p.stderr[-500:]
    # 不鎖死用例數（加案只改腳本）：以「通過」結尾且零 ❌ 為準。
    assert "通過" in p.stdout and "❌" not in p.stdout
