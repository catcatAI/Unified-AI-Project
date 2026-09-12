"""Playground retirement lock (R17): the standalone demo targets a rewritten
API and must fail LOUDLY with directions (exit 2), never with a traceback.
"""

import os
import subprocess
import sys


def test_playground_retired_explicitly():
    repo_root = os.path.join(os.path.dirname(__file__), "..")
    p = subprocess.run(
        [
            sys.executable,
            os.path.join(
                repo_root, "apps", "backend", "src", "core", "autonomous", "playground.py"
            ),
        ],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=repo_root,
    )
    assert p.returncode == 2, p.stdout[-500:] + p.stderr[-500:]
    assert "已退役" in p.stdout
    assert "Traceback" not in p.stdout and "Traceback" not in p.stderr
