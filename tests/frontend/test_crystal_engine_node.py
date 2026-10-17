"""P1-10 橋接：以 pytest 執行 crystal-cards node:test 引擎套件。

WHY: 根 package.json `test` = `pytest tests/`，純 .mjs 不會進預設門禁；
此橋讓 test_crystal_engine.mjs（11 tests：tryStack/executeCombat/
save-load 行為層）隨全量 pytest 一起跑，node 不可用時 skip。
"""

import shutil
import subprocess
from pathlib import Path

import pytest

NODE = shutil.which("node")
SCRIPT = Path(__file__).resolve().parent / "test_crystal_engine.mjs"

pytestmark = pytest.mark.skipif(NODE is None, reason="node runtime not available")


def test_crystal_engine_node_suite():
    proc = subprocess.run(
        [NODE, "--test", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, (
        f"node --test failed (rc={proc.returncode})\n"
        f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
    )
    assert "fail 0" in proc.stdout, f"expected 0 failures:\n{proc.stdout}"
