"""game-rpg CLI 端到端冒煙：echo 指令序列餵 run_game.py 進程，斷言輸出關鍵幀。

計畫 §七 顯示/交互驗證矩陣「game-rpg CLI」行的自動化驗收：
「自動化：echo 指令序列餵 run_game.py 進程，斷言輸出關鍵幀」。
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_GAME = REPO_ROOT / "apps" / "game-rpg" / "run_game.py"
CLOCK_FILE = REPO_ROOT / "apps" / "game-rpg" / "data" / "world_clock.json"
SAVE_FILE = REPO_ROOT / "apps" / "game-rpg" / "data" / "save_game.json"

COMMAND_SEQUENCE = "\n".join(["", "", "1", "6", "q", "n"]) + "\n"

KEY_FRAMES = (
    "CLI 角色扮演模擬",
    "按 Enter 開始",
    "選擇開始時代",
    "選擇你的角色",
    "你選擇了: ",
    "CC-01",
    "自動接受主線任務: 鏡湖的秘密",
    "遊戲結束。謝謝遊玩!",
)


@pytest.fixture()
def preserve_runtime_state():
    snapshots = {p: (p.read_bytes() if p.exists() else None) for p in (CLOCK_FILE, SAVE_FILE)}
    yield
    for path, data in snapshots.items():
        if data is None:
            path.unlink(missing_ok=True)
        else:
            path.write_bytes(data)


def test_run_game_echo_sequence_key_frames(preserve_runtime_state):
    proc = subprocess.run(
        [sys.executable, str(RUN_GAME)],
        input=COMMAND_SEQUENCE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(REPO_ROOT),
        timeout=90,
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"},
    )
    output = proc.stdout + proc.stderr
    assert proc.returncode == 0, f"run_game.py exited {proc.returncode}:\n{output[-3000:]}"
    assert "Traceback" not in output, output[-3000:]
    for frame in KEY_FRAMES:
        assert frame in output, f"missing key frame {frame!r} in output:\n{output[-3000:]}"
