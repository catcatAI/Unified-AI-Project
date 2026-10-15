"""CLI package smoke tests — cli-tests.yml 必須收集真測試（exit 5 紅燈防呆）。

此前 packages/cli 零測試檔，`pytest packages/cli -q` 恆 no-tests-collected
（exit 5）⇒ 該 workflow 觸發即紅或形同虛設。本檔提供真實 import/entry
冒煙，使該門有意義。

導入機制：本倉有多個同名 `cli` 套件會互相遮蔽（packages/cli 外層墊層
__init__.py、backend editable install 的 apps/backend/src/cli）。故以私有名
`_ucli` 掛載 packages/cli/cli（__path__ 指向目錄），相對導入（from .client
import …）在 _ucli 命名空間下正常解析，與任何 `cli` 遮蔽無關。
"""

import importlib
import sys
import types
from pathlib import Path

import pytest

_CLI_PKG_DIR = Path(__file__).resolve().parents[1] / "cli"


def _import_cli_module(leaf: str):
    """以 _ucli 私有名掛載並導入 packages/cli/cli/<leaf>.py。"""
    if "_ucli" not in sys.modules:
        pkg = types.ModuleType("_ucli")
        pkg.__path__ = [str(_CLI_PKG_DIR)]
        sys.modules["_ucli"] = pkg
    return importlib.import_module(f"_ucli.{leaf}")


@pytest.mark.parametrize("leaf", ["client", "ai_models_cli", "unified_cli"])
def test_cli_module_imports(leaf: str) -> None:
    mod = _import_cli_module(leaf)
    assert mod is not None


def test_entry_point_module_exposes_main() -> None:
    """console_scripts 目標模組必須存在且可載入（setup.py entry_points）。"""
    unified = _import_cli_module("unified_cli")
    assert hasattr(unified, "main"), "unified_cli.main missing (console entry target)"


def test_client_constructible() -> None:
    client_mod = _import_cli_module("client")
    client = client_mod.UnifiedAIClient(base_url="http://localhost:5199")
    assert client is not None
