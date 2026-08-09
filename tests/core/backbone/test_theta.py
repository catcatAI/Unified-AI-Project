# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""θ 元認知路由橋接測試（§11.3 #3 步驟 B9 — state_adapter + port_registry 注入）。"""

import pytest
from core.backbone.theta import ThetaBridge


class TestThetaBridge:
    def test_unbound_theta_values_empty(self):
        bridge = ThetaBridge()
        assert bridge.theta_values() == {}

    def test_bound_matrix_theta_values(self):
        from core.engine.state_matrix import StateMatrix4D

        sm = StateMatrix4D()
        bridge = ThetaBridge(primary_matrix=sm)
        values = bridge.theta_values()
        assert "creation_urge" in values
        assert "novelty" in values
        assert "complexity" in values

    def test_routing_report_bound(self):
        from core.engine.state_matrix import StateMatrix4D

        sm = StateMatrix4D()
        bridge = ThetaBridge(primary_matrix=sm)
        report = bridge.get_routing_report()
        assert "theta_values" in report
        assert "creation_urge" in report
        assert "theta_negativity" in report
        # θ 值不再恆為 0（有注入 matrix）
        assert report["creation_urge"] >= 0

    def test_router_created_with_port_registry(self):
        from core.engine.state_matrix import StateMatrix4D

        sm = StateMatrix4D()
        bridge = ThetaBridge(primary_matrix=sm)
        router = bridge.router()
        assert router is bridge.router()  # 單例快取
        assert router._state_adapter is not None
        assert router._port_registry is not None

    def test_bind_matrix_rebuilds_router(self):
        from core.engine.state_matrix import StateMatrix4D

        bridge = ThetaBridge()
        first = bridge.router()
        bridge.bind_matrix(StateMatrix4D())
        second = bridge.router()
        assert second is not first

    def test_resolve_route_skip_when_port_missing(self):
        from core.engine.state_matrix import StateMatrix4D
        from core.engine.theta_router import RouteAction

        bridge = ThetaBridge(primary_matrix=StateMatrix4D())
        decision = bridge.resolve_route("nonexistent_port")
        assert decision.action == RouteAction.SKIP

    def test_unavailable_report_fallback(self, monkeypatch):
        bridge = ThetaBridge()

        def boom():
            raise RuntimeError("theta router unavailable")

        monkeypatch.setattr(bridge, "router", boom)
        report = bridge.get_routing_report()
        assert report["creation_urge"] == 0
        assert report["theta_negativity"] == 0


class TestBackboneTheta:
    def test_backbone_theta_integration(self):
        from core.backbone import get_backbone, reset_backbone

        reset_backbone()
        bb = get_backbone()
        # 主幹線未註冊 matrix 時 theta_values 可能為空，但 bridge 可正常查詢
        report = bb.theta.get_routing_report()
        assert "theta_values" in report
        assert bb.theta is get_backbone().theta  # 單例
        reset_backbone()

    def test_prompt_builder_uses_backbone(self):
        """prompt_builder._get_theta_router 優先走 backbone 統一注入。"""
        from core.backbone import get_backbone, reset_backbone
        from services.llm import prompt_builder

        reset_backbone()
        bb = get_backbone()
        from core.engine.state_matrix import StateMatrix4D

        bb.register_matrix("primary", StateMatrix4D())
        router = prompt_builder._get_theta_router()
        assert router is get_backbone().theta.router()
        assert router._state_adapter is not None
        reset_backbone()
