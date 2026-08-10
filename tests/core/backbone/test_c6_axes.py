# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""後續計畫 §3：座標軸統一 AxesRegistry + backbone 接入。

驗證：
- AxesRegistry 註冊單軸（positions / dimensions 兩種形式）。
- 三層巢狀軸譜（遊戲 AXIS_SYSTEMS：譜系→軸→位置）正確建子 registry。
- backbone.register_axes_registry / axes_registry / axes_registries 存取。
- 遊戲軸譜（apps/game-rpg/axis_system.py）可直接註冊進 registry。
"""

import pytest
from core.backbone import get_backbone, reset_backbone
from core.backbone.axes import AxesRegistry, AxisDefinition, get_axes_registry

# 對應 apps/game-rpg/axis_system.py AXIS_SYSTEMS 子集
SAMPLE_GAME_AXES = {
    "物種": {
        "原種距離": {"N": "近原種", "S": "標準種", "F": "遠原種"},
        "人形比例": {"H": "類人型", "S": "標準型", "C": "類原型"},
    },
    "AI": {
        "人形模仿度": {"F0": "無形體", "F1": "抽象載體"},
        "自主性": {"A0": "被動型", "A1": "條件型", "A2": "學習型"},
    },
}


@pytest.fixture(autouse=True)
def _fresh():
    reset_backbone()
    yield
    reset_backbone()


class TestAxesRegistry:
    def test_register_positions_axis(self):
        reg = AxesRegistry("game")
        reg.register_axis("原種距離", positions={"N": "近原種", "S": "標準種"})
        assert reg.has_axis("原種距離")
        axis = reg.axis("原種距離")
        assert axis.label_for("N") == "近原種"
        assert axis.has_position("S")

    def test_register_dimensions_axis(self):
        reg = AxesRegistry("game")
        reg.register_axis("神性濃度", dimensions=["傳說級", "信仰級"])
        assert reg.dimensions("神性濃度") == ["傳說級", "信仰級"]

    def test_missing_axis_raises(self):
        reg = AxesRegistry("game")
        with pytest.raises(KeyError):
            reg.axis("不存在的軸")
        assert reg.axis("不存在的軸", default="x") == "x"

    def test_register_axes_two_level(self):
        reg = AxesRegistry("game")
        count = reg.register_axes(
            {
                "人形比例": {"H": "類人型", "S": "標準型"},
                "自主性": ["被動型", "條件型"],
            }
        )
        assert count == 2
        assert reg.has_axis("人形比例")
        assert reg.dimensions("自主性") == ["被動型", "條件型"]

    def test_register_axes_three_level_nested(self):
        reg = AxesRegistry("game")
        count = reg.register_axes(SAMPLE_GAME_AXES)
        # 物種(2) + AI(2) = 4 軸
        assert count == 4
        assert "物種" in reg
        # 子 registry 穿透
        species = reg.axis("物種")
        assert isinstance(species, AxesRegistry)
        assert species.has_axis("原種距離")
        assert species.axis("原種距離").label_for("N") == "近原種"

    def test_axis_definition_to_dict(self):
        axis = AxisDefinition("測試軸", positions={"A": "甲"})
        d = axis.to_dict()
        assert d["name"] == "測試軸"
        assert d["positions"] == {"A": "甲"}
        assert d["dimensions"] == ["甲"]

    def test_to_dict_registry(self):
        reg = AxesRegistry("game")
        reg.register_axis("軸一", positions={"X": "x1"})
        d = reg.to_dict()
        assert "軸一" in d
        assert d["軸一"]["positions"] == {"X": "x1"}


class TestBackboneAxes:
    def test_register_and_retrieve(self):
        bb = get_backbone()
        reg = AxesRegistry("game")
        reg.register_axes(SAMPLE_GAME_AXES)
        bb.register_axes_registry("game", reg)
        got = bb.axes_registry("game")
        assert got is reg
        assert got.has_axis("物種")

    def test_default_registry_exists(self):
        bb = get_backbone()
        assert bb.axes_registry("default") is not None
        assert bb.axes_registry("missing") is None
        assert bb.axes_registry("missing", default=42) == 42

    def test_get_axes_registry_singleton(self):
        a = get_axes_registry("game")
        b = get_axes_registry("game")
        assert a is b
        c = get_axes_registry("other")
        assert c is not a


class TestRealGameAxes:
    def test_game_axis_systems_registrable(self):
        # 實際載入遊戲軸譜，確認全部都能註冊
        import sys

        sys.path.insert(0, "apps/game-rpg")
        try:
            import axis_system

            reg = AxesRegistry("game")
            count = reg.register_axes(axis_system.AXIS_SYSTEMS)
            assert count >= 9  # 四系譜 × 各 3 軸 ≠ 全 12，但至少 9
            assert "物種" in reg
            assert isinstance(reg.axis("物種"), AxesRegistry)
            # 抽一軸驗證
            species = reg.axis("物種")
            dist = species.axis("原種距離")
            assert dist.label_for("N") == "近原種"
        finally:
            sys.path.pop(0)
