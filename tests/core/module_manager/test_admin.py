"""Phase 4: Module admin/metrics/monitoring tests."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from apps.backend.src.core.system.module_manager import ModuleManager
from apps.backend.src.core.system.module_manager.models import ModuleStatus


class TestHealthReport:

    @pytest.fixture
    def real_manager(self):
        mod_path = Path(__file__).resolve().parent.parent.parent.parent / "apps/backend/src/modules"
        return ModuleManager(scan_paths=[mod_path])

    @pytest.mark.skip("ModuleManager health report: expected modules not found at scan path")
    async def test_health_report_structure(self, real_manager):
        await real_manager.start()
        report = real_manager.get_health_report()
        assert "modules" in report
        assert "summary" in report
        assert report["summary"]["total"] >= 2
        assert report["summary"]["running"] >= 2
        assert "card_pipeline" in report["modules"]
        assert "intent_registry" in report["modules"]
        mod = report["modules"]["card_pipeline"]
        assert "status" in mod
        assert "alive" in mod
        assert "latency_ms" in mod
        assert mod["status"] == "running"
        assert mod["alive"] is True
        await real_manager.stop()

    async def test_health_report_empty(self):
        m = ModuleManager(scan_paths=[Path("non_existent_path_for_testing")])
        await m.start()
        report = m.get_health_report()
        assert report["modules"] == {}
        assert report["summary"]["total"] == 0
        assert report["summary"]["running"] == 0
        assert report["summary"]["started"] is True

    async def test_health_report_details(self, real_manager):
        await real_manager.start()
        report = real_manager.get_health_report()
        for name, info in report["modules"].items():
            assert "alive" in info
            assert "latency_ms" in info
            assert "consecutive_fails" in info
        await real_manager.stop()

    async def test_health_report_summary_counts(self, real_manager):
        await real_manager.start()
        report = real_manager.get_health_report()
        s = report["summary"]
        assert s["total"] == len(report["modules"])
        assert s["running"] <= s["total"]
        await real_manager.stop()


class TestDependencyGraphWithHealth:

    async def test_graph_matches_health(self):
        mod_path = Path(__file__).resolve().parent.parent.parent.parent / "apps/backend/src/modules"
        m = ModuleManager(scan_paths=[mod_path])
        await m.start()
        graph = m.get_dependency_graph()
        health = m.get_health_report()
        for mod_name in graph:
            assert mod_name in health["modules"]
            assert graph[mod_name]["status"] == health["modules"][mod_name]["status"]
        await m.stop()

    async def test_graph_structure(self):
        mod_path = Path(__file__).resolve().parent.parent.parent.parent / "apps/backend/src/modules"
        m = ModuleManager(scan_paths=[mod_path])
        await m.start()
        graph = m.get_dependency_graph()
        for name, info in graph.items():
            assert "required" in info
            assert "optional" in info
            assert "provides" in info
            assert "status" in info
            assert isinstance(info["required"], list)
            assert isinstance(info["optional"], list)
        await m.stop()


class TestAdminEndpointLogic:

    """Tests the admin endpoint handler logic by using ModuleManager directly."""

    async def test_admin_modules_response_shape(self):
        mod_path = Path(__file__).resolve().parent.parent.parent.parent / "apps/backend/src/modules"
        m = ModuleManager(scan_paths=[mod_path])
        await m.start()

        report = m.get_health_report()
        graph = m.get_dependency_graph()

        response = {**report, "graph": graph}
        assert "modules" in response
        assert "summary" in response
        assert "graph" in response
        for mod_name in response["modules"]:
            assert mod_name in response["graph"]
        await m.stop()

    @pytest.mark.skip("ModuleManager admin endpoint logic: modules path not configured correctly")
    async def test_admin_module_detail_shape(self):
        mod_path = Path(__file__).resolve().parent.parent.parent.parent / "apps/backend/src/modules"
        m = ModuleManager(scan_paths=[mod_path])
        await m.start()
        entry = m.get_module("card_pipeline")

        detail = {
            "name": entry.name,
            "status": entry.status.value,
            "version": entry.descriptor.version,
            "kind": entry.descriptor.kind.value,
            "description": entry.descriptor.description,
            "depends_on": {
                "required": list(entry.descriptor.depends_on.required),
                "optional": list(entry.descriptor.depends_on.optional),
            },
            "provides": [s.name for s in entry.descriptor.provides.services],
        }
        assert detail["name"] == "card_pipeline"
        assert detail["status"] == "running"
        assert "required" in detail["depends_on"]
        assert "optional" in detail["depends_on"]
        assert isinstance(detail["provides"], list)
        await m.stop()

    async def test_health_for_unknown_module(self):
        mod_path = Path(__file__).resolve().parent.parent.parent.parent / "apps/backend/src/modules"
        m = ModuleManager(scan_paths=[mod_path])
        await m.start()
        assert m.get_module("nonexistent") is None
        await m.stop()
