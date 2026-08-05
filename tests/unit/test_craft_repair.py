# -*- coding: utf-8 -*-
"""合成-修復配方（R17/R18）行為測試。

R17/R18 是 category=repair、repair_all=True 的修復服務配方：
消耗配方材料直接修復裝備，不應把不存在的「修復服務」物品塞進物品欄。
"""
import pytest
import sim_systems


@pytest.fixture(autouse=True)
def _no_random_failure(monkeypatch):
    """固定配方隨機：failure_chance 最高 0.25，回傳 0.9 保證走成功路徑。

    原先測試未固定隨機，R04（0.15）/R07 等配方約 15% 機率隨機失敗
    造成測試偶發紅——非污染，是測試本身未隔離隨機性。
    """
    monkeypatch.setattr(sim_systems._random, "random", lambda: 0.9)


class _FakeEquip:
    """最小裝備管理器（有 slots dict）"""

    def __init__(self, slots):
        self.slots = slots


def _weapon(cur_durability=10):
    return {
        "item": {
            "name": "鐵劍",
            "durability": 50,
            "current_durability": cur_durability,
        },
        "durability_loss": 50 - cur_durability,
    }


def test_repair_recipe_requires_equipment_manager():
    """無裝備管理器時：不扣材料、不產出物品。"""
    inv = ["鐵礦", "鐵礦", "鐵錠"]
    suc, res, msg = sim_systems.craft_item("R17", inv, None, None)
    assert not suc
    assert inv == ["鐵礦", "鐵礦", "鐵錠"]  # 材料保留
    assert res is None


def test_repair_recipe_repairs_damaged_equipment():
    """有損耗裝備：扣配方材料、耐久恢復、不產出「修復服務」物品。"""
    inv = ["鐵礦", "鐵礦", "鐵錠"]
    weapon = _weapon(10)
    char = {"inventory": inv}
    suc, res, msg = sim_systems.craft_item("R17", inv, _FakeEquip({"weapon": weapon}), char)
    assert suc
    assert weapon["item"]["current_durability"] == 50  # 10 → 50 恢復
    assert res is None
    assert "修復服務" not in inv
    assert inv == []  # 配方材料已扣


def test_repair_recipe_refunds_materials_when_nothing_to_repair():
    """滿耐久無物可修：退還配方材料。"""
    inv = ["鐵礦", "鐵礦", "鐵錠"]
    weapon = _weapon(50)  # 滿耐久
    char = {"inventory": inv}
    suc, res, msg = sim_systems.craft_item("R17", inv, _FakeEquip({"weapon": weapon}), char)
    assert not suc
    assert inv == ["鐵礦", "鐵礦", "鐵錠"]  # 材料退回
    assert res is None


def test_repair_recipe_r18_uses_leather_ingredients():
    """R18（修復防具）同契約：消耗皮革/布料修復防具。"""
    inv = ["皮革", "皮革", "布料"]
    armor = {
        "item": {
            "name": "皮甲",
            "durability": 40,
            "current_durability": 5,
        },
        "durability_loss": 35,
    }
    char = {"inventory": inv}
    suc, res, msg = sim_systems.craft_item("R18", inv, _FakeEquip({"armor": armor}), char)
    assert suc
    assert armor["item"]["current_durability"] == 40
    assert "修復服務" not in inv
    assert inv == []


def test_normal_recipe_unaffected():
    """一般配方（R04 治療藥水）行為不變：照常產出物品。"""
    inv = ["草藥", "草藥", "草藥", "空瓶"]
    suc, res, msg = sim_systems.craft_item("R04", inv, None, None)
    assert suc
    assert res == "治療藥水"
    assert inv == ["治療藥水"]  # 材料扣完、產出進物品欄


# ═══════════════════════════════════════════════════════════════════════════
# 魔法配方軸譜檢查（批次 31）
# ═══════════════════════════════════════════════════════════════════════════


class TestMagicCraftAxis:
    """魔法類配方（R07 魔力藥水等）需要能量或靈性親和力 ≥ 0.5。"""

    def _char(self, energy, spirit):
        return {
            "axis": {"affinity": {"物質": 0.3, "能量": energy, "靈性": spirit, "機械": 0.1, "資訊": 0.1}},
        }

    def test_low_energy_blocked(self):
        """低能量/靈性角色被擋，且不吞材料。"""
        inv = ["魔法粉", "空瓶"]  # R07 材料
        ch = self._char(0.17, 0.17)
        ok, res, msg = sim_systems.craft_item("R07", inv, None, ch)
        assert not ok
        assert "軸譜不符" in msg and "魔法" in msg
        assert inv == ["魔法粉", "空瓶"]  # 材料完整保留

    def test_high_energy_passes(self):
        """高能量角色（概念體/術士）可製作魔力藥水。"""
        inv = ["魔法粉", "空瓶"]
        ch = self._char(0.70, 0.73)
        ok, res, msg = sim_systems.craft_item("R07", inv, None, ch)
        assert ok
        assert res == "魔力藥水"

    def test_high_spirit_passes(self):
        """低能量但高靈性（靈體）也可製作靈力藥。"""
        from axis_system import check_craft_axis
        ch = self._char(0.2, 0.75)
        ok, why = check_craft_axis(ch, {"result_item": "靈力藥"})
        assert ok

    def test_magic_tags_detection(self):
        """魔法判定：tags 標 magic/elemental 或名稱含魔力/法杖等。"""
        from axis_system import is_magic_craft
        assert is_magic_craft("魔力藥水", ["consumable"])
        assert is_magic_craft("炎帝之劍", ["elemental", "magic"])
        assert not is_magic_craft("治療藥水", ["consumable"])
        assert not is_magic_craft("鳳凰之羽衣", ["beast", "natural"])
