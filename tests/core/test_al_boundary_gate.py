"""AL 割邊門禁（Phase 3 item 4；契約 I8、計畫 §Phase 3 #4）。

兩條邊：core/life 執行期不得出站 import ``ai./services./api./integrations.``
（``if TYPE_CHECKING:`` 型別塊豁免）；AI 側接觸 ``core.life.al_state`` 只准
公共 API、模組形式只准 ``api/lifespan.py``、私有 ``al_state._`` 即違規。

真實庫狀態與「壞樣本會被抓」兩邊都釘 —— 只測真庫（永 0）的話，把掃描器
刪成 `return []` 也能過。
"""

import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
BACKEND_SRC = REPO / "apps" / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

_spec = importlib.util.spec_from_file_location(
    "check_fact_gates_under_test", REPO / "scripts" / "check_fact_gates.py"
)
assert _spec and _spec.loader
gates = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gates)


class TestTheRealTreeIsClean:
    """生產庫 0 violations（門禁本體在 check_fact_gates 全域跑，這裡另釘一份）。"""

    def test_both_facts_report_zero(self):
        facts = {f.id: f for f in gates._al_facts()}
        assert facts["al.boundary_outbound"].value == 0.0, facts["al.boundary_outbound"].evidence
        assert facts["al.snapshot_api_only"].value == 0.0, facts["al.snapshot_api_only"].evidence

    def test_the_lifespan_module_form_is_allowed(self):
        # 模組形式唯一豁免點（backbone 註冊的模組交接）。
        path = BACKEND_SRC / "api" / "lifespan.py"
        assert gates._al_scan_ai_side(path) == []


class TestOutboundScanCatchesViolations:
    def test_a_runtime_outbound_import_is_flagged(self, tmp_path):
        path = tmp_path / "mod.py"
        path.write_text("from ai.foo import Bar\n", encoding="utf-8")
        hits = gates._al_scan_outbound(path)
        assert len(hits) == 1 and "ai.foo" in hits[0]

    def test_each_banned_root_is_flagged(self, tmp_path):
        # 四個根都要抓 —— 只抓 ai.* 的門禁擋不住 services./api./integrations.
        for root in ("ai", "services", "api", "integrations"):
            path = tmp_path / f"mod_{root}.py"
            path.write_text(f"import {root}.whatever\n", encoding="utf-8")
            assert gates._al_scan_outbound(path), root

    def test_a_lazy_import_inside_a_function_is_flagged(self, tmp_path):
        # 反轉施工前 DLI 的違規就是長這樣 —— 懶 import 也出站。
        path = tmp_path / "mod.py"
        path.write_text(
            "def boot():\n    from services.thing import helper\n    return helper\n",
            encoding="utf-8",
        )
        assert len(gates._al_scan_outbound(path)) == 1

    def test_the_typechecking_block_is_exempt(self, tmp_path):
        path = tmp_path / "mod.py"
        path.write_text(
            "from __future__ import annotations\n\n"
            "from typing import TYPE_CHECKING\n\n"
            "if TYPE_CHECKING:\n    from ai.foo import Bar\n",
            encoding="utf-8",
        )
        assert gates._al_scan_outbound(path) == []

    def test_core_imports_are_not_violations(self, tmp_path):
        path = tmp_path / "mod.py"
        path.write_text(
            "from core.engine.state_matrix import StateMatrix4D\n"
            "from .al_state import birth_datetime\n",
            encoding="utf-8",
        )
        assert gates._al_scan_outbound(path) == []


class TestAiSideSnapshotApiOnly:
    def test_a_private_name_from_import_is_flagged(self, tmp_path):
        path = tmp_path / "mod.py"
        path.write_text(
            "def f():\n    from core.life.al_state import _phase_str\n    return _phase_str\n",
            encoding="utf-8",
        )
        hits = gates._al_scan_ai_side(path, "mod.py")
        assert len(hits) == 1 and "_phase_str" in hits[0]

    def test_a_public_name_from_import_is_allowed(self, tmp_path):
        path = tmp_path / "mod.py"
        path.write_text(
            "def f():\n"
            "    from core.life.al_state import get_al_state\n"
            "    return get_al_state\n",
            encoding="utf-8",
        )
        assert gates._al_scan_ai_side(path, "mod.py") == []

    def test_the_module_form_is_flagged_outside_lifespan(self, tmp_path):
        path = tmp_path / "mod.py"
        path.write_text(
            "def f():\n    from core.life import al_state\n    return al_state\n",
            encoding="utf-8",
        )
        hits = gates._al_scan_ai_side(path, "mod.py")
        assert len(hits) == 1 and "module-imports" in hits[0]

    def test_touching_a_private_attribute_is_flagged(self, tmp_path):
        path = tmp_path / "mod.py"
        path.write_text("value = al_state._read_intensity()\n", encoding="utf-8")
        hits = gates._al_scan_ai_side(path, "mod.py")
        assert len(hits) == 1 and "_private" in hits[0]

    def test_files_that_never_mention_al_state_are_skipped(self, tmp_path):
        path = tmp_path / "mod.py"
        path.write_text("VALUE = 1\n", encoding="utf-8")
        assert gates._al_scan_ai_side(path, "mod.py") == []


def test_the_facts_are_wired_into_the_hygiene_chain():
    # 漏掛進 hygiene_facts = 門禁永遠不跑（孤兒函數等於沒有門禁）。
    import inspect

    source = inspect.getsource(gates.main)
    assert "_al_facts()" in source
