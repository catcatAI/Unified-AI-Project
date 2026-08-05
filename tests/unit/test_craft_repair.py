# -*- coding: utf-8 -*-
"""合成-修復配方（R17/R18）行為測試。

R17/R18 是 category=repair、repair_all=True 的修復服務配方：
消耗配方材料直接修復裝備，不應把不存在的「修復服務」物品塞進物品欄。
"""
import sim_systems


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
