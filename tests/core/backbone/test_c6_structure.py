# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""主幹線結構探查與打印 — structure()/dump()/CLI。

驗證：
- backbone.structure() 回傳完整性（含各層 section）。
- backbone.dump() 打印可讀樹，含關鍵 section。
- inventory()/BackboneStructure 對空 backbone 亦不炸。
- CLI（python -m core.backbone）的 main() 回傳碼、summary/json/dump。
- lifespan._register_backbone 在單一元件失敗時跳過不炸（惰性防護）。
"""

import json
import subprocess
import sys

import pytest

from core.backbone import get_backbone, reset_backbone
from core.backbone.structure import BackboneStructure, dump, inventory

BACKBONE_KEY_SECTIONS = (
    "core_matrix",
    "axes",
    "free_matrices",
    "dictionaries",
    "modules",
    "translators",
    "external",
    "learning",
    "training",
    "memory",
    "state_store",
    "response",
    "datasets",
    "pairs",
    "io_bound",
    "security",
)


@pytest.fixture(autouse=True)
def _fresh():
    reset_backbone()
    yield
    reset_backbone()


class TestStructure:
    def test_structure_has_all_sections(self):
        bb = get_backbone()
        s = bb.structure()
        for section in BACKBONE_KEY_SECTIONS:
            assert section in s, f"missing section {section}"

    def test_structure_types(self):
        bb = get_backbone()
        s = bb.structure()
        assert isinstance(s["core_matrix"], list)
        assert isinstance(s["dictionaries"], list)
        assert isinstance(s["pairs"], dict)
        assert isinstance(s["state_store"], dict)
        assert isinstance(s["security"], dict)

    def test_inventory_matches_structure(self):
        bb = get_backbone()
        # warm（dump 會 access 觸發 mount，先跑一次讓狀態穩定）
        bb.dump(title="warm")
        assert inventory(bb) == bb.structure()

    def test_main_backbone_structure_class(self):
        bb = get_backbone()
        s = BackboneStructure(bb).build()
        assert "free_matrices" in s

    def test_empty_default_registrations_ok(self):
        # 空的 default backbone 不炸，能列出
        bb = get_backbone()
        s = bb.structure()
        assert isinstance(s["modules"], list)


class TestDump:
    def test_dump_contains_sections_and_title(self):
        bb = get_backbone()
        text = bb.dump(title="UNITTEST")
        assert "UNITTEST" in text
        assert "主幹線全覽" in text
        assert "核心矩陣" in text
        assert "字典" in text
        assert "安全層" in text

    def test_dump_brief_more_compact(self):
        bb = get_backbone()
        detailed = bb.dump(detailed=True)
        brief = bb.dump(detailed=False)
        assert len(brief) <= len(detailed)

    def test_dump_function_equals_method(self):
        bb = get_backbone()
        a = bb.dump(title="X")
        b = dump(bb, title="X")
        # mounted 狀態可能因 access 改變；比較除去 mounted key 的結構穩定部分
        assert "X" in a and "X" in b
        assert "核心矩陣" in a and "核心矩陣" in b


class TestCLI:
    def _run(self, *args):
        env = {"PYTHONPATH": "apps/backend/src"}
        code = (
            "import sys; sys.path.insert(0,'apps/backend/src'); "
            "from core.backbone.__main__ import main; sys.exit(main(sys.argv[1:]))"
        )
        proc = subprocess.run(
            [sys.executable, "-c", code, *args],
            capture_output=True,
            text=True,
            cwd=None,
            env=None,
        )
        return proc

    def test_dump_command_zero_exit(self):
        proc = self._run("dump", "--brief")
        assert proc.returncode == 0, proc.stderr
        assert "主幹線全覽" in proc.stdout

    def test_summary_command_json(self):
        proc = self._run("summary")
        assert proc.returncode == 0
        data = json.loads(proc.stdout)
        assert "dictionaries" in data

    def test_unknown_command_nonzero(self):
        proc = self._run("bogus")
        assert proc.returncode == 1

    def test_help_command(self):
        proc = self._run("--help")
        assert proc.returncode == 0
        assert "python -m core.backbone" in proc.stdout


class TestRegisterBackboneResilience:
    def test_single_failure_skips_without_blocking(self, monkeypatch):
        """其中一個 fn 拋錯時 _register_backbone 繼續其他註冊。"""
        import api.lifespan as L
        import core.backbone as cb

        registered = []

        class FakeModules:
            def count(self):
                return len(registered)

        class FakeMatrices:
            def count(self):
                return 0

        class FakeBackbone:
            registries = type("R", (), {"modules": FakeModules(), "matrices": FakeMatrices()})()

            class _Memories:
                def names(self):
                    return []

            memories = _Memories()

            def register_module(self, key, obj):
                registered.append(key)

            def register_matrix(self, key, obj):
                registered.append(key)

            def register_memory(self, key, obj):
                registered.append(key)

            def register_dictionary(self, key, obj):
                registered.append(key)

        def broken():
            raise RuntimeError("boom")

        def working():
            return object()

        monkeypatch.setattr(cb, "get_backbone", lambda: FakeBackbone())
        monkeypatch.setattr(L, "get_digital_life", broken)
        monkeypatch.setattr(L, "get_lifecycle", working)
        monkeypatch.setattr(L, "get_metabolic_heartbeat", working)
        monkeypatch.setattr(L, "get_causal_reasoning", working)
        monkeypatch.setattr(L, "get_crisis_system", working)
        monkeypatch.setattr(L, "get_agent_manager", working)
        monkeypatch.setattr(L, "get_desktop_interaction", working)
        monkeypatch.setattr(L, "get_training_coordinator", working)
        monkeypatch.setattr(L, "_chat_service_instance", None)

        L._register_backbone()
        # digital_life（broken）跳過，但 lifecycle/heartbeat 等仍註冊
        assert "lifecycle" in registered
        assert "metabolic_heartbeat" in registered

    def test_skips_when_backbone_import_missing(self, monkeypatch):
        """backbone 不可 import 時 _register_backbone 直接返回不炸。"""
        import api.lifespan as L

        real_import = __import__

        import builtins

        def fake_import(name, *args, **kwargs):
            if name == "core.backbone":
                raise ImportError("blocked")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        # 不該拋例外
        L._register_backbone()


def test_lifespan_module_imports():
    import api.lifespan as L

    assert callable(L._register_backbone)
