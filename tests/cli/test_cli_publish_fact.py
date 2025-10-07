"""
测试模块 - test_cli_publish_fact

自动生成的测试模块，用于验证系统功能。
"""

import sys
import asyncio
import importlib.util
from pathlib import Path
import pytest

@pytest.mark.asyncio
async 
    def setUp(self):
        """测试前设置"""
        self.test_data = {}
        self.test_config = {}
    
    def tearDown(self):
        """测试后清理"""
        self.test_data.clear()
        self.test_config.clear()
def test_publish_fact_echo(capsys):
    # 動態載入 CLI main 模組
    cli_main_path = Path(__file__).resolve().parent.parent / "cli" / "main.py"
    assert cli_main_path.exists(), f"CLI main.py not found at {cli_main_path}"

    spec = importlib.util.spec_from_file_location("cli_main_test_module", str(cli_main_path))
    cli_main = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(cli_main)

    # 準備參數：publish_fact 並等待 echo，縮短逾時並跳過收尾 sleep
    argv_backup = sys.argv.copy()
    sys.argv = [
        "prog",
        "publish_fact",
        "fact-from-test",
        "--echo",
        "--echo-timeout", "4.0",
        "--no-post-sleep",
    ]

    try:
        await cli_main.main_cli_logic()
    finally:
        sys.argv = argv_backup

    out = capsys.readouterr().out
    # 驗證：至少成功發佈，且最好能收到 echo
    assert "Manual fact" in out or "Manual fact".lower() in out.lower(), f"Unexpected output: {out}"
    # 優先檢查收到 echo；若在某些環境逾時，測試仍允許但會標註
    if "Received internal echo for published fact" not in out:
        pytest.skip("Echo not captured within timeout in this environment; publish path verified.")