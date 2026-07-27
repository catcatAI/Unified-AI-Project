"""
Simulation Systems — Complete data layer for CLI RPG.
Items: 54 | Enemies: 12 | Recipes: 16 | Locations: 10 | Quests: 14 | Vehicles: 4 | Scene objects: 20 | Junk: 20
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict
import random as _random

MAX_INVENTORY_SLOTS = 30
MAX_INVENTORY_WEIGHT = 60.0
MAX_PROPERTIES = 8

# Item stacking — add max_stack to consumables
DEFAULT_MAX_STACK = {
    "consumable": 10,
    "material": 20,
    "junk": 5,
    "quest": 1,
}

# ═══════════════════════════════════════════════════════════
# ITEM CATALOG (54 items)
# ═══════════════════════════════════════════════════════════

ITEM_CATALOG = {
    # ── Materials (13) ──
    "草藥":  {"type": "material", "weight": 0.2, "value": 10, "tags": ["herb"], "desc": "常見草藥，可用於合成"},
    "木柄":  {"type": "material", "weight": 0.5, "value": 5,  "tags": ["wood"], "desc": "武器握柄材料"},
    "鐵礦":  {"type": "material", "weight": 2.0, "value": 15, "tags": ["ore"], "desc": "未熔煉的鐵礦石"},
    "火元素":{"type": "material", "weight": 0.3, "value": 30, "tags": ["element"], "desc": "凝聚的火元素碎片"},
    "鐵錠":  {"type": "material", "weight": 1.0, "value": 20, "tags": ["metal"], "desc": "熔煉後的鐵錠"},
    "皮革":  {"type": "material", "weight": 0.8, "value": 12, "tags": ["leather"], "desc": "處理過的獸皮"},
    "布料":  {"type": "material", "weight": 0.3, "value": 8,  "tags": ["cloth"], "desc": "普通布料"},
    "水晶碎片":{"type":"material","weight":0.2,"value": 25, "tags": ["crystal"], "desc":"發著微光的水晶碎片"},
    "魔法粉": {"type": "material", "weight": 0.1, "value": 40, "tags": ["magic"], "desc": "研磨的魔法材料"},
    "龍鱗":  {"type": "material", "weight": 1.5, "value": 80, "tags": ["rare"], "desc": "閃爍的龍鱗片"},
    "靈木":  {"type": "material", "weight": 0.7, "value": 35, "tags": ["wood","magic"], "desc": "蘊含靈力的木材"},
    "絲線":  {"type": "material", "weight": 0.1, "value": 6,  "tags": ["cloth"], "desc": "精緻的絲線"},
    "黏土":  {"type": "material", "weight": 1.0, "value": 3,  "tags": ["clay"], "desc": "可塑形的黏土"},

    # ── Consumables (10) ──
    "火焰藥水":{"type":"consumable","weight":0.3,"value": 50, "heal_hp": 50, "heal_sp":10, "max_stack":10, "desc":"恢復50HP+10SP"},
    "治療藥水":{"type":"consumable","weight":0.3,"value": 40, "heal_hp": 40, "max_stack":10, "desc":"恢復40HP"},
    "魔力藥水":{"type":"consumable","weight":0.3,"value": 35, "heal_sp": 30, "max_stack":10, "desc":"恢復30SP"},
    "乾糧":   {"type":"consumable","weight":0.5,"value": 8,  "heal_hp": 12, "max_stack":20, "desc":"恢復12HP"},
    "解毒草": {"type":"consumable","weight":0.2,"value": 20, "max_stack":10, "desc":"解除中毒狀態"},
    "靈力藥": {"type":"consumable","weight":0.3,"value": 45, "heal_sp": 50, "max_stack":10, "desc":"恢復50SP"},
    "生命果": {"type":"consumable","weight":0.4,"value": 60, "heal_hp": 80, "max_stack":5, "desc":"恢復80HP（稀有）"},
    "提神茶": {"type":"consumable","weight":0.2,"value": 15, "heal_sp": 15, "max_stack":20, "desc":"恢復15SP"},
    "繃帶":   {"type":"consumable","weight":0.2,"value": 12, "heal_hp": 15, "max_stack":10, "desc":"簡易包紮，恢復15HP"},
    "濃縮藥水":{"type":"consumable","weight":0.4,"value": 80, "heal_hp": 100,"heal_sp":30, "max_stack":5, "desc":"高級恢復品"},

    # ── Weapons (7) ──
    "鐵劍":{"type":"weapon","weight":3.0,"value": 80, "durability":100,"slot":"right_hand",
            "stat_multipliers":{"atk":0.3,"spd":-0.05},"desc":"鐵劍 (+30%ATK,-5%SPD)"},
    "鋼刀":{"type":"weapon","weight":2.5,"value": 120,"durability":120,"slot":"right_hand",
            "stat_multipliers":{"atk":0.4,"spd":-0.03},"desc":"鋼刀 (+40%ATK)"},
    "木杖":{"type":"weapon","weight":1.5,"value": 25, "durability":60, "slot":"right_hand",
            "stat_multipliers":{"atk":0.1,"karma":0.2},"desc":"木杖 (+10%ATK,+20%運)"},
    "匕首":{"type":"weapon","weight":1.0,"value": 45, "durability":70, "slot":"right_hand",
            "stat_multipliers":{"atk":0.2,"spd":0.1},"desc":"匕首 (+20%ATK,+10%SPD)"},
    "長弓":{"type":"weapon","weight":2.0,"value": 90, "durability":85, "slot":"both_hands",
            "stat_multipliers":{"atk":0.35,"spd":0.05},"desc":"長弓 (+35%ATK)"},
    "盾牌":{"type":"weapon","weight":3.5,"value": 70, "durability":150,"slot":"left_hand",
            "stat_multipliers":{"defense":0.5,"spd":-0.1},"desc":"盾牌 (+50%DEF,-10%SPD)"},
    "水晶法杖":{"type":"weapon","weight":1.8,"value": 200,"durability":90, "slot":"right_hand",
               "stat_multipliers":{"atk":0.2,"defense":0.2,"karma":0.3},"desc":"水晶法杖 (全屬性提升)"},

    # ── Armor (7) ──
    "皮甲": {"type":"armor","weight":2.0,"value": 60, "durability":80, "slot":"torso",
             "stat_multipliers":{"defense":0.2,"spd":-0.05},"desc":"皮甲 (+20%DEF)"},
    "鐵甲": {"type":"armor","weight":5.0,"value": 150,"durability":200,"slot":"torso",
             "stat_multipliers":{"defense":0.4,"spd":-0.15},"desc":"鐵甲 (+40%DEF,-15%SPD)"},
    "皮帽": {"type":"armor","weight":0.5,"value": 25, "durability":50, "slot":"head",
             "stat_multipliers":{"defense":0.1},"desc":"皮帽 (+10%DEF)"},
    "鐵盔": {"type":"armor","weight":1.5,"value": 55, "durability":120,"slot":"head",
             "stat_multipliers":{"defense":0.2,"spd":-0.05},"desc":"鐵盔 (+20%DEF)"},
    "草鞋": {"type":"armor","weight":0.5,"value": 15, "durability":40, "slot":"feet",
             "stat_multipliers":{"spd":0.1},"desc":"草鞋 (+10%SPD)"},
    "鐵靴": {"type":"armor","weight":2.0,"value": 65, "durability":150,"slot":"feet",
             "stat_multipliers":{"defense":0.15,"spd":-0.08},"desc":"鐵靴 (+15%DEF)"},
    "斗篷": {"type":"armor","weight":1.0,"value": 45, "durability":60, "slot":"back",
             "stat_multipliers":{"defense":0.15,"karma":0.1},"desc":"斗篷 (+15%DEF)"},

    # ── Accessories (5) ──
    "護身符":{"type":"accessory","weight":0.1,"value":100,"durability":50, "slot":"neck",
              "stat_multipliers":{"defense":0.1,"karma":0.1},"desc":"護身符 (+10%DEF,+10%運)"},
    "戒指":  {"type":"accessory","weight":0.05,"value":80, "durability":40, "slot":"left_hand",
              "stat_multipliers":{"atk":0.1,"spd":0.05},"desc":"戒指 (+10%ATK)"},
    "手鐲":  {"type":"accessory","weight":0.1,"value":70, "durability":60, "slot":"right_hand",
              "stat_multipliers":{"defense":0.1,"karma":0.05},"desc":"手鐲 (+10%DEF)"},
    "腰帶":  {"type":"accessory","weight":0.3,"value":40, "durability":80, "slot":"waist",
              "stat_multipliers":{"spd":0.05},"desc":"腰帶 (+5%SPD)"},
    "項鍊":  {"type":"accessory","weight":0.1,"value":120,"durability":30, "slot":"neck",
              "stat_multipliers":{"karma":0.2},"desc":"項鍊 (+20%運)"},

    # ── Quest items (5) ──
    "古老鑰匙":{"type":"quest","weight":0.1,"value":0,  "desc":"生鏽的鑰匙，不知道開什麼門"},
    "神秘地圖":{"type":"quest","weight":0.1,"value":0,  "desc":"標記了某個隱藏位置的地圖"},
    "書信":   {"type":"quest","weight":0.05,"value":0, "desc":"一封未署名的信"},
    "記憶水晶":{"type":"quest","weight":0.2,"value":0,  "desc":"儲存著片段記憶的水晶"},
    "古代硬幣":{"type":"quest","weight":0.1,"value":0,  "desc":"上面刻著看不懂的文字"},

    # ── Junk / Decorative (17) ──
    "空瓶":   {"type":"junk","weight":0.2,"value":1,  "desc":"空的玻璃瓶"},
    "破布":   {"type":"junk","weight":0.3,"value":0,  "desc":"一塊破舊的布料"},
    "生鏽釘子":{"type":"junk","weight":0.1,"value":0, "desc":"已經生鏽的鐵釘"},
    "樹枝":   {"type":"junk","weight":0.4,"value":0,  "desc":"從樹上掉落的樹枝"},
    "小石頭": {"type":"junk","weight":0.3,"value":0,  "desc":"一顆普通的鵝卵石"},
    "羽毛":   {"type":"junk","weight":0.05,"value":1, "desc":"一根漂亮的鳥羽"},
    "貝殼":   {"type":"junk","weight":0.1,"value":2,  "desc":"一個螺旋貝殼"},
    "乾燥花": {"type":"junk","weight":0.1,"value":1,  "desc":"壓乾的花朵書籤"},
    "蠟燭頭": {"type":"junk","weight":0.2,"value":1,  "desc":"燒剩一半的蠟燭"},
    "麻繩":   {"type":"junk","weight":0.3,"value":2,  "desc":"一條結實的麻繩"},
    "碎陶瓷": {"type":"junk","weight":0.4,"value":0,  "desc":"破碗的碎片"},
    "舊鑰匙圈":{"type":"junk","weight":0.1,"value":1, "desc":"一個生鏽的鑰匙圈"},
    "炭筆":   {"type":"junk","weight":0.1,"value":1,  "desc":"可以用來寫字的炭筆"},
    "木雕":   {"type":"junk","weight":0.3,"value":3,  "desc":"一個小巧的木雕裝飾品"},
    "松果":   {"type":"junk","weight":0.2,"value":0,  "desc":"從松樹上掉下來的松果"},
    "彩色玻璃片":{"type":"junk","weight":0.1,"value":2,"desc":"彩色玻璃的碎片"},
    "幸運幣": {"type":"junk","weight":0.05,"value":5, "desc":"一枚據說會帶來好運的硬幣"},
}


def get_item_def(item_name: str) -> dict:
    return ITEM_CATALOG.get(item_name, {"type": "misc", "weight": 0.5, "value": 0, "desc": "不知名的東西"})

def get_junk_items() -> list:
    return [k for k, v in ITEM_CATALOG.items() if v["type"] == "junk"]


# ═══════════════════════════════════════════════════════════
# RECIPES (16 recipes)
# ═══════════════════════════════════════════════════════════

RECIPES = [
    # combine (組合)
    {"recipe_id":"R01","name":"火焰藥水","category":"alchemize",
     "ingredients":[{"item":"草藥","quantity":2},{"item":"火元素","quantity":1}],
     "result_item":"火焰藥水","result_quantity":1,"failure_chance":0.1},
    {"recipe_id":"R02","name":"鐵劍","category":"craft",
     "ingredients":[{"item":"鐵礦","quantity":3},{"item":"木柄","quantity":1}],
     "result_item":"鐵劍","result_quantity":1,"failure_chance":0.2},
    {"recipe_id":"R03","name":"鐵錠","category":"process",
     "ingredients":[{"item":"鐵礦","quantity":5}],
     "result_item":"鐵錠","result_quantity":2,"failure_chance":0.0},
    {"recipe_id":"R04","name":"治療藥水","category":"alchemize",
     "ingredients":[{"item":"草藥","quantity":3},{"item":"空瓶","quantity":1}],
     "result_item":"治療藥水","result_quantity":1,"failure_chance":0.15},
    {"recipe_id":"R05","name":"皮甲","category":"craft",
     "ingredients":[{"item":"皮革","quantity":3},{"item":"絲線","quantity":2}],
     "result_item":"皮甲","result_quantity":1,"failure_chance":0.2},
    {"recipe_id":"R06","name":"鋼刀","category":"craft",
     "ingredients":[{"item":"鐵錠","quantity":3},{"item":"木柄","quantity":1}],
     "result_item":"鋼刀","result_quantity":1,"failure_chance":0.25},
    {"recipe_id":"R07","name":"魔力藥水","category":"alchemize",
     "ingredients":[{"item":"魔法粉","quantity":2},{"item":"空瓶","quantity":1}],
     "result_item":"魔力藥水","result_quantity":1,"failure_chance":0.1},
    {"recipe_id":"R08","name":"解毒草","category":"alchemize",
     "ingredients":[{"item":"草藥","quantity":1},{"item":"水晶碎片","quantity":1}],
     "result_item":"解毒草","result_quantity":1,"failure_chance":0.1},
    {"recipe_id":"R09","name":"靈力藥","category":"alchemize",
     "ingredients":[{"item":"靈木","quantity":2},{"item":"空瓶","quantity":1}],
     "result_item":"靈力藥","result_quantity":1,"failure_chance":0.15},
    {"recipe_id":"R10","name":"護身符","category":"craft",
     "ingredients":[{"item":"絲線","quantity":3},{"item":"水晶碎片","quantity":2}],
     "result_item":"護身符","result_quantity":1,"failure_chance":0.3},
    {"recipe_id":"R11","name":"鐵甲","category":"craft",
     "ingredients":[{"item":"鐵錠","quantity":5},{"item":"皮革","quantity":2}],
     "result_item":"鐵甲","result_quantity":1,"failure_chance":0.35},
    {"recipe_id":"R12","name":"濃縮藥水","category":"alchemize",
     "ingredients":[{"item":"火焰藥水","quantity":1},{"item":"魔力藥水","quantity":1}],
     "result_item":"濃縮藥水","result_quantity":1,"failure_chance":0.3},
    {"recipe_id":"R13","name":"斗篷","category":"craft",
     "ingredients":[{"item":"布料","quantity":4},{"item":"絲線","quantity":1}],
     "result_item":"斗篷","result_quantity":1,"failure_chance":0.15},
    {"recipe_id":"R14","name":"匕首","category":"craft",
     "ingredients":[{"item":"鐵礦","quantity":2},{"item":"木柄","quantity":1}],
     "result_item":"匕首","result_quantity":1,"failure_chance":0.1},
    {"recipe_id":"R15","name":"水晶法杖","category":"craft",
     "ingredients":[{"item":"靈木","quantity":3},{"item":"水晶碎片","quantity":3},{"item":"魔法粉","quantity":2}],
     "result_item":"水晶法杖","result_quantity":1,"failure_chance":0.4},
    {"recipe_id":"R16","name":"生命果","category":"alchemize",
     "ingredients":[{"item":"龍鱗","quantity":1},{"item":"治療藥水","quantity":2}],
     "result_item":"生命果","result_quantity":1,"failure_chance":0.4},
    # ── Repair recipes (物品修復) ──
    {"recipe_id":"R17","name":"修復武器","category":"repair",
     "ingredients":[{"item":"鐵礦","quantity":2},{"item":"鐵錠","quantity":1}],
     "result_item":"修復服務","result_quantity":1,"failure_chance":0.0,"repair_all":True},
    {"recipe_id":"R18","name":"修復防具","category":"repair",
     "ingredients":[{"item":"皮革","quantity":2},{"item":"布料","quantity":1}],
     "result_item":"修復服務","result_quantity":1,"failure_chance":0.0,"repair_all":True},
]

def repair_equipment(equipment_manager, character):
    """Repair all equipped items using materials from inventory.
    Returns (success, message).
    """
    repaired_count = 0
    for sid, eq in equipment_manager.slots.items():
        if eq and eq["item"]:
            mx = eq["item"].get("durability", 100)
            cur = eq["item"].get("current_durability", mx)
            if cur < mx:
                # Repair cost: 1 iron + 1 leather per item
                inv = character.get("inventory", [])
                cost_iron = 1 if "鐵礦" in inv or "鐵錠" in inv else 0
                if cost_iron:
                    if "鐵礦" in inv:
                        inv.remove("鐵礦")
                    elif "鐵錠" in inv:
                        inv.remove("鐵錠")
                    eq["item"]["current_durability"] = mx
                    eq["durability_loss"] = 0
                    repaired_count += 1
    if repaired_count:
        return True, "修復了 %d 件裝備" % repaired_count
    return False, "沒有需要修復的裝備，或缺少修復材料"

def craft_item(recipe_id, inventory):
    recipe = next((r for r in RECIPES if r["recipe_id"] == recipe_id), None)
    if not recipe:
        return False, None, "未知配方"
    for ing in recipe["ingredients"]:
        if inventory.count(ing["item"]) < ing["quantity"]:
            return False, None, "缺少材料: %s x%d" % (ing["item"], ing["quantity"])
    for ing in recipe["ingredients"]:
        for _ in range(ing["quantity"]):
            inventory.remove(ing["item"])
    if _random.random() < recipe["failure_chance"]:
        # Return some materials on fail
        for ing in recipe["ingredients"]:
            inventory.append(ing["item"])
        return False, None, "合成失敗（材料已歸還）"
    result = recipe["result_item"]
    count = recipe["result_quantity"]
    for _ in range(count):
        inventory.append(result)
    return True, result, "合成成功: %s x%d" % (result, count)


# ═══════════════════════════════════════════════════════════
# ENEMIES (12 enemies)
# ═══════════════════════════════════════════════════════════

ENEMIES = [
    {"name":"野狼",  "hp":40,"atk":12,"def":5, "spd":6, "exp":30,"gold":10,"loot":["皮革"],          "desc":"飢餓的野狼"},
    {"name":"哥布林","hp":30,"atk":8, "def":3, "spd":4, "exp":20,"gold":5, "loot":["木柄","小石頭"],"desc":"膽小的哥布林"},
    {"name":"石像鬼","hp":80,"atk":18,"def":12,"spd":2, "exp":60,"gold":25,"loot":["鐵礦","黏土"],  "desc":"古老的石像鬼"},
    {"name":"暗影靈","hp":25,"atk":15,"def":2, "spd":8, "exp":35,"gold":15,"loot":["魔法粉"],       "desc":"飄忽的暗影生物"},
    {"name":"廢鐵傀儡","hp":100,"atk":10,"def":20,"spd":1,"exp":50,"gold":30,"loot":["鐵錠","鐵礦","生鏽釘子"],"desc":"生鏽的機械傀儡"},
    {"name":"晶石蜘蛛","hp":55,"atk":14,"def":8, "spd":7, "exp":40,"gold":20,"loot":["水晶碎片","絲線"],"desc":"結晶體的蜘蛛"},
    {"name":"盜賊", "hp":35,"atk":16,"def":4, "spd":9, "exp":45,"gold":35,"loot":["匕首","乾糧"],   "desc":"鬼祟的人形盜賊"},
    {"name":"蛇妖", "hp":45,"atk":20,"def":6, "spd":5, "exp":55,"gold":22,"loot":["解毒草","皮革"], "desc":"有毒牙的蛇妖"},
    {"name":"幽靈", "hp":20,"atk":22,"def":1, "spd":10,"exp":50,"gold":12,"loot":["魔法粉","破布"], "desc":"無實體的怨靈"},
    {"name":"巨熊", "hp":120,"atk":25,"def":10,"spd":3, "exp":80,"gold":40,"loot":["皮革","生命果"], "desc":"龐大的棕熊"},
    {"name":"元素核心","hp":60,"atk":28,"def":8, "spd":4, "exp":70,"gold":35,"loot":["火元素","水晶碎片"],"desc":"凝聚的元素能量體"},
    {"name":"古代守衛","hp":150,"atk":20,"def":25,"spd":2,"exp":100,"gold":50,"loot":["古老鑰匙","龍鱗"],"desc":"古代遺跡的守衛"},
]

LOCATION_ENEMIES = {
    "方碑丘":         ["野狼","哥布林","盜賊"],
    "鏡湖":           ["晶石蜘蛛","暗影靈","蛇妖"],
    "西翼大市集":     ["哥布林","盜賊"],
    "中央大圖書館":   ["暗影靈","石像鬼","幽靈"],
    "海峽":           ["廢鐵傀儡","石像鬼","蛇妖"],
    "秘密鐵工廠":     ["廢鐵傀儡","哥布林"],
    "便利店":         ["盜賊","哥布林"],
    "英靈殿":         ["古代守衛","幽靈","元素核心"],
    "廢棄礦坑":       ["巨熊","晶石蜘蛛","廢鐵傀儡"],
    "森林深處":       ["巨熊","野狼","蛇妖","元素核心"],
}

def get_enemy(location: str) -> Optional[dict]:
    names = LOCATION_ENEMIES.get(location, [])
    if not names:
        return None
    name = _random.choice(names)
    for e in ENEMIES:
        if e["name"] == name:
            return dict(e)
    return None

ENEMY_ENCOUNTER_CHANCE = 0.4

def resolve_combat_turn(attacker_atk, attacker_spd, defender_def, defender_hp):
    dmg = max(1, int(attacker_atk * 1.5 - defender_def * 0.5))
    crit = _random.random() < attacker_spd * 0.05
    if crit:
        dmg = int(dmg * 1.5)
    return min(dmg, defender_hp), crit


# ═══════════════════════════════════════════════════════════
# WORLD MAP (10 locations)
# ═══════════════════════════════════════════════════════════

WORLD_MAP = {
    "方碑丘":         {"east":"西翼大市集", "south":"中央大圖書館", "north":"鏡湖", "west":"森林深處"},
    "鏡湖":           {"south":"方碑丘", "east":"海峽"},
    "西翼大市集":     {"west":"方碑丘", "north":"便利店"},
    "中央大圖書館":   {"north":"方碑丘", "east":"英靈殿"},
    "海峽":           {"west":"鏡湖"},
    "秘密鐵工廠":     {"east":"方碑丘"},
    "便利店":         {"south":"西翼大市集"},
    "英靈殿":         {"west":"中央大圖書館"},
    "廢棄礦坑":       {"enter":"方碑丘"},
    "森林深處":       {"east":"方碑丘"},
}

LOCATION_VIBES = {
    "方碑丘":         "🌾 微風吹拂的寧靜村莊",
    "鏡湖":           "💧 湖面如鏡，空氣中帶著水氣",
    "西翼大市集":     "🏪 市集熱鬧，叫賣聲此起彼落",
    "中央大圖書館":   "📚 書香四溢，安靜肅穆",
    "海峽":           "🌊 海風陣陣，波濤拍打海岸",
    "秘密鐵工廠":     "🔧 鐵鎚聲與蒸氣交織，火花四濺",
    "便利店":         "🏪 明亮的小店，貨架上擺滿日常用品",
    "英靈殿":         "⚔ 古老的大殿，牆上掛滿武器與旗幟",
    "廢棄礦坑":       "⛏ 陰暗的礦坑入口，深不見底",
    "森林深處":       "🌲 參天大樹遮天蔽日，鳥鳴迴盪",
}

# ═══════════════════════════════════════════════════════════
# SCENE TYPES & ENTRY REQUIREMENTS (per MAP_AND_SCENES.md)
# ═══════════════════════════════════════════════════════════

LOCATION_TYPES = {
    "方碑丘":         "outdoor",
    "鏡湖":           "outdoor",
    "西翼大市集":     "outdoor",
    "中央大圖書館":   "indoor",
    "海峽":           "outdoor",
    "秘密鐵工廠":     "indoor",
    "便利店":         "indoor",
    "英靈殿":         "dungeon",
    "廢棄礦坑":       "dungeon",
    "森林深處":       "outdoor",
}

SCENE_TYPE_ICONS = {
    "outdoor": "🌄",
    "indoor":  "🏛",
    "dungeon": "🕳",
    "special": "✨",
}

SCENE_TYPE_NAMES = {
    "outdoor": "室外",
    "indoor":  "室內",
    "dungeon": "地下城",
    "special": "特殊",
}

ENTRY_REQUIREMENTS = {
    # Format: "location": {"type": condition_type, ...}
    # condition_type: "level" -> requires min level
    #                 "item" -> requires item in inventory
    #                 "quest" -> requires completed quest in quest log
    #                 "reputation" -> requires min reputation
    #                 "time" -> requires specific time range
    #                 "or" -> any of sub-conditions
    #                 "and" -> all of sub-conditions
    "英靈殿": {
        "type": "or",
        "conditions": [
            {"type": "level", "min": 5, "msg": "需要等級 5 以上"},
            {"type": "item", "item": "古老鑰匙", "msg": "需要「古老鑰匙」"},
            {"type": "quest", "quest_id": "MQ-03", "msg": "需要完成主線「圖書館之謎」"},
        ],
        "fail_msg": "英靈殿的大門緊閉，似乎只有夠強壯的冒險者才能打開。",
    },
    "廢棄礦坑": {
        "type": "level",
        "min": 3,
        "fail_msg": "礦坑入口的塌陷處擋住了去路。你需要更強健的體魄才能通過。（等級 3）",
    },
    "森林深處": {
        "type": "level",
        "min": 2,
        "fail_msg": "森林入口的荊棘叢生，你還沒有能力穿越。（等級 2）",
    },
    "海峽": {
        "type": "level",
        "min": 4,
        "fail_msg": "通往海峽的棧道已經損壞，需要足夠的經驗才能安全通過。（等級 4）",
    },
}


def check_entry_requirement(location, character):
    """Check if character meets entry requirements for a location.
    Returns (can_enter: bool, message: str or None).
    """
    req = ENTRY_REQUIREMENTS.get(location)
    if not req:
        return True, None  # No requirements

    fail_msg = req.get("fail_msg", "無法進入。")

    if req["type"] == "level":
        level = character.get("level", 1)
        if level >= req.get("min", 1):
            return True, None
        return False, fail_msg

    elif req["type"] == "item":
        inv = character.get("inventory", [])
        if req.get("item", "") in inv:
            return True, None
        return False, fail_msg

    elif req["type"] == "quest":
        quests = character.get("quests", {})
        qid = req.get("quest_id", "")
        qdata = quests.get(qid)
        if qdata and qdata.get("status") == "completed":
            return True, None
        return False, fail_msg

    elif req["type"] == "reputation":
        rep = character.get("reputation", 0)
        if rep >= req.get("min", 0):
            return True, None
        return False, fail_msg

    elif req["type"] == "or":
        for cond in req.get("conditions", []):
            can, _ = check_entry_requirement_by_type(cond, character)
            if can:
                return True, None
        # Show all condition hints
        hints = [cond.get("msg", "???") for cond in req.get("conditions", [])]
        hint_str = "  或 ".join(hints)
        return False, "%s（%s）" % (fail_msg, hint_str)

    elif req["type"] == "and":
        for cond in req.get("conditions", []):
            can, _ = check_entry_requirement_by_type(cond, character)
            if not can:
                return False, fail_msg
        return True, None

    return True, None


def check_entry_requirement_by_type(cond, character):
    """Check a single condition entry."""
    ctype = cond.get("type", "")
    if ctype == "level":
        level = character.get("level", 1)
        return level >= cond.get("min", 1), None
    elif ctype == "item":
        return cond.get("item", "") in character.get("inventory", []), None
    elif ctype == "quest":
        qid = cond.get("quest_id", "")
        qdata = character.get("quests", {}).get(qid)
        return qdata and qdata.get("status") == "completed", None
    elif ctype == "reputation":
        return character.get("reputation", 0) >= cond.get("min", 0), None
    return True, None


def get_entry_requirement_hint(location):
    """Get a short hint string about what is required to enter a location."""
    req = ENTRY_REQUIREMENTS.get(location)
    if not req:
        return ""

    conds = req.get("conditions", []) if req.get("type") in ("or", "and") else [req]
    hints = []
    for c in conds:
        ct = c.get("type", "")
        if ct == "level":
            hints.append("Lv.%d+" % c.get("min", 1))
        elif ct == "item":
            hints.append("「%s」" % c.get("item", "?"))
        elif ct == "quest":
            hints.append("需完成相應任務")
    if hints:
        sep = " AND " if req.get("type") == "and" else " OR "
        return " (" + sep.join(hints) + ")"
    return ""


REAL_ESTATE = {
    "方碑丘小屋": {
        "type":"house", "price":500, "functions":["rest","store"],
        "desc":"樸素的村莊小屋", "max_level":3,
        "upgrades":[
            {"level":2, "cost":300, "add_functions":["study"], "desc":"增建書房"},
            {"level":3, "cost":600, "add_functions":["guest"], "desc":"增設客房"},
        ],
    },
    "西翼商店鋪": {
        "type":"shop", "price":800, "functions":["trade"],
        "desc":"市集的小店鋪", "max_level":3,
        "upgrades":[
            {"level":2, "cost":500, "add_functions":["rest"], "desc":"增設休息區"},
            {"level":3, "cost":1000, "add_functions":["craft"], "desc":"增設工坊區"},
        ],
    },
    "湖畔工坊": {
        "type":"workshop", "price":1200, "functions":["craft","rest"],
        "desc":"鏡湖旁的工坊", "max_level":3,
        "upgrades":[
            {"level":2, "cost":800, "add_functions":["study"], "desc":"增設研究區"},
            {"level":3, "cost":1500, "add_functions":["alchemy"], "desc":"增設煉金臺"},
        ],
    },
    "圖書館密室": {
        "type":"house", "price":2000, "functions":["rest","study"],
        "desc":"圖書館內的安靜房間", "max_level":2,
        "upgrades":[
            {"level":2, "cost":1200, "add_functions":["store"], "desc":"增設書架倉庫"},
        ],
    },
    "礦坑倉庫": {
        "type":"warehouse", "price":600, "functions":["store"],
        "desc":"廢棄礦坑旁的倉庫", "max_level":2,
        "upgrades":[
            {"level":2, "cost":400, "add_functions":["rest"], "desc":"簡易改造為休息處"},
        ],
    },
    # ── New property types per MAP_AND_SCENES.md ──
    "森林農場": {
        "type":"farm", "price":1500, "functions":["farm","rest"],
        "desc":"森林深處的小農場", "max_level":3,
        "upgrades":[
            {"level":2, "cost":800, "add_functions":["store"], "desc":"增設農具倉庫"},
            {"level":3, "cost":1600, "add_functions":["trade"], "desc":"增設農產直銷點"},
        ],
    },
    "鏡湖觀測塔": {
        "type":"tower", "price":2500, "functions":["study","observe"],
        "desc":"鏡湖旁的觀測塔", "max_level":3,
        "upgrades":[
            {"level":2, "cost":1200, "add_functions":["rest"], "desc":"增設休息室"},
            {"level":3, "cost":2000, "add_functions":["teleport"], "desc":"增設傳送陣"},
        ],
    },
}

REAL_ESTATE_KEYS = list(REAL_ESTATE.keys())


# ═══════════════════════════════════════════════════════════
# MECHANISM HELPERS (per MAP_AND_SCENES.md)
# ═══════════════════════════════════════════════════════════

MECHANISM_TYPES = {
    "lever":          {"name":"拉桿",      "icon":"🕹", "desc":"扳動後觸發效果"},
    "pedestal":       {"name":"基座",      "icon":"🗿", "desc":"放置物品觸發效果"},
    "pressure_plate": {"name":"壓力板",    "icon":"⬇",  "desc":"踩踏觸發"},
    "hidden_switch":  {"name":"隱藏開關",  "icon":"🔍", "desc":"發現後觸發"},
    "gear":           {"name":"齒輪機關",  "icon":"⚙",  "desc":"多次操作後觸發"},
}

EFFECT_TYPES = {
    "teleport":    {"name":"傳送",      "icon":"🌀"},
    "route_open":  {"name":"開路",      "icon":"🛤"},
    "reveal":      {"name":"顯現",      "icon":"✨"},
    "trap":        {"name":"陷阱",      "icon":"⚠"},
    "summon":      {"name":"召喚",      "icon":"👻"},
    "heal":        {"name":"恢復",      "icon":"💚"},
    "quest_advance":{"name":"任務推進",  "icon":"⚑"},
}


def resolve_mechanism_effect(obj, character, current_location=None):
    """Resolve a mechanism's effect when activated.
    Returns (success, message, side_effects_dict).
    side_effects: { 'teleport_to': loc, 'enemy_spawn': enemy_name, 'route_add': (dir, target, cur_loc), ... }
    """
    effect = obj.get("effect", {})
    etype = effect.get("type", "")
    side = {}

    if etype == "teleport":
        target = effect.get("target", "")
        if target:
            side["teleport_to"] = target
        return True, effect.get("message", "傳送了！"), side

    elif etype == "route_open":
        target_loc = effect.get("target", "")
        direction = effect.get("value", "")
        cur_loc = current_location or "?"
        if target_loc and direction:
            side["route_add"] = (direction, target_loc, cur_loc)
        return True, effect.get("message", "新的道路出現了！"), side

    elif etype == "reveal":
        items = effect.get("items", [])
        inv = character.get("inventory", [])
        for item in items:
            inv.append(item)
        return True, effect.get("message", "獲得了物品！"), side

    elif etype == "summon":
        enemy_name = effect.get("enemy", "")
        count = effect.get("count", 1)
        if enemy_name:
            side["enemy_spawn"] = enemy_name
            side["enemy_count"] = count
        return True, effect.get("message", "敵人出現了！"), side

    elif etype == "heal":
        hp = effect.get("hp", 0)
        sp = effect.get("sp", 0)
        if hp:
            character["hp"] = min(character.get("max_hp", 100), character.get("hp", 0) + hp)
        if sp:
            character["sp"] = min(character.get("max_sp", 100), character.get("sp", 0) + sp)
        if character.get("fatigue", 0) > 0:
            character["fatigue"] = max(0, character["fatigue"] - 50)
        if character.get("pain", 0) > 0:
            character["pain"] = max(0, character["pain"] - 30)
        return True, effect.get("message", "恢復了！"), side

    elif etype == "quest_advance":
        qid = effect.get("quest_id", "")
        if qid:
            side["quest_advance"] = qid
        return True, effect.get("message", "任務進展了！"), side

    elif etype == "trap":
        dmg = effect.get("damage", 10)
        character["hp"] = max(0, character.get("hp", 100) - dmg)
        return True, effect.get("message", "觸發了陷阱！"), side

    return True, "機關啟動了，但似乎沒有任何事情發生。", side


def check_mechanism_requirements(obj, character):
    """Check if a mechanism's activation requirements are met.
    Returns (can_activate, message).
    """
    reqs = obj.get("requirements", {})
    if not reqs:
        return True, None

    # Level check
    min_lv = reqs.get("level", 0)
    if min_lv > 0 and character.get("level", 1) < min_lv:
        return False, ("需要等級 %d 以上。" % min_lv)

    # Item check
    req_item = reqs.get("item", "")
    req_qty = reqs.get("qty", 1)
    if req_item:
        inv = character.get("inventory", [])
        count = inv.count(req_item)
        if count < req_qty:
            return False, ("需要 %s x%d。（目前: %d）" % (req_item, req_qty, count))

    return True, None


def consume_mechanism_requirements(obj, character):
    """Consume items required by a mechanism."""
    reqs = obj.get("requirements", {})
    consume = reqs.get("consume", True)
    if not consume:
        return
    req_item = reqs.get("item", "")
    req_qty = reqs.get("qty", 1)
    if req_item:
        inv = character.get("inventory", [])
        for _ in range(req_qty):
            if req_item in inv:
                inv.remove(req_item)


def upgrade_property(character, property_name):
    """Upgrade an owned property to the next level.
    Returns (success, message).
    """
    owned = character.get("owned_properties", {})
    if property_name not in owned:
        return False, "你沒有這個不動產"
    re_def = REAL_ESTATE.get(property_name, {})
    upgrades = re_def.get("upgrades", [])
    if not upgrades:
        return False, "這個不動產無法升級"
    current_level = owned[property_name].get("level", 1)
    max_level = re_def.get("max_level", 1)
    if current_level >= max_level:
        return False, "已達最高等級 (%d/%d)" % (current_level, max_level)
    # Find next upgrade
    next_upgrade = None
    for upg in upgrades:
        if upg["level"] == current_level + 1:
            next_upgrade = upg
            break
    if not next_upgrade:
        return False, "沒有可用的升級"
    cost = next_upgrade["cost"]
    if character.get("gold", 0) < cost:
        return False, "金幣不足！需要 %dG" % cost
    # Apply upgrade
    character["gold"] -= cost
    owned[property_name]["level"] = current_level + 1
    owned[property_name].setdefault("functions", re_def.get("functions", []))
    for func in next_upgrade.get("add_functions", []):
        if func not in owned[property_name]["functions"]:
            owned[property_name]["functions"].append(func)
    return True, "🏠 %s 升級到 Lv.%d！花費 %dG" % (property_name, current_level + 1, cost)

def get_property_upgrade_cost(character, property_name):
    """Get the cost to upgrade a property to the next level, or None if maxed."""
    owned = character.get("owned_properties", {})
    re_def = REAL_ESTATE.get(property_name, {})
    upgrades = re_def.get("upgrades", [])
    current_level = owned.get(property_name, {}).get("level", 1)
    max_level = re_def.get("max_level", 1)
    if current_level >= max_level:
        return None
    for upg in upgrades:
        if upg["level"] == current_level + 1:
            return upg["cost"], upg.get("desc",""), upg.get("add_functions",[])
    return None

HOUR_NAMES = {0:"子時",2:"丑時",4:"寅時",6:"卯時",8:"辰時",10:"巳時",
              12:"午時",14:"未時",16:"申時",18:"酉時",20:"戌時",22:"亥時"}

def get_time_desc(hour, day):
    period = "早晨" if 6<=hour<12 else "午後" if 12<=hour<18 else "夜晚"
    return "第%d天·%s（%s）" % (day, HOUR_NAMES.get(hour, "%d:00"%hour), period)


# ═══════════════════════════════════════════════════════════
# NPC SCHEDULES (3 NPCs with full daily routines)
# ═══════════════════════════════════════════════════════════

NPC_SCHEDULES = {
    "小狐丸": [
        (6,10,  "整理冰晶","鏡湖",       "calm"),
        (10,14, "巡視湖面","鏡湖",       "alert"),
        (14,18, "休息",    "秘密鐵工廠",  "rest"),
        (18,22, "交流",    "西翼大市集",  "friendly"),
        (22,6,  "睡眠",    "鏡湖",        "sleep"),
    ],
    "左間小蒼蘭": [
        (7,12,  "打鐵",    "秘密鐵工廠",  "focused"),
        (12,13, "午餐",    "便利店",      "rest"),
        (13,18, "繼續工作","秘密鐵工廠",  "focused"),
        (18,21, "整理工具","秘密鐵工廠",  "calm"),
        (21,7,  "睡眠",    "秘密鐵工廠",  "sleep"),
    ],
    "紅": [
        (6,10,  "整理貨架","便利店",     "calm"),
        (10,18, "值班",    "便利店",      "friendly"),
        (18,22, "晚班",    "便利店",      "friendly"),
        (22,6,  "休息",    "便利店",      "sleep"),
    ],
}

def get_npc_activity(npc_name, hour):
    schedule = NPC_SCHEDULES.get(npc_name)
    if not schedule:
        return "休息","","neutral"
    for start,end,activity,location,mood in schedule:
        if start <= end:
            if start <= hour < end:
                return activity,location,mood
        else:
            if hour >= start or hour < end:
                return activity,location,mood
    return "休息","","neutral"


# ═══════════════════════════════════════════════════════════
# QUESTS (14 quests — main + side)
# ═══════════════════════════════════════════════════════════

QUESTS = [
    # ── Main Quests (with conditions) ──
    {"id":"MQ-01","title":"鏡湖的秘密","type":"main","giver":"系統",
     "desc":"探索鏡湖周邊，找出湖底發光的原因。",
     "conditions":{"required_reputation":0,"time_available":{"start_hour":0,"end_hour":24}},
     "objectives":[{"type":"visit","target":"鏡湖","detail":"造訪鏡湖"},
                   {"type":"collect","target":"水晶碎片","qty":1,"detail":"收集水晶碎片"}],
     "reward_exp":80,"reward_gold":30,"reward_item":"古老鑰匙","reward_reputation":10,
     "next_quest":"MQ-02"},
    {"id":"MQ-02","title":"大正浪漫的迴響","type":"main","giver":"左間小蒼蘭",
     "desc":"幫助左間小蒼蘭修復秘密鐵工廠的古董機械。",
     "conditions":{"required_level":3,"required_quests":["MQ-01"],"time_available":{"start_hour":7,"end_hour":21}},
     "objectives":[{"type":"visit","target":"秘密鐵工廠","detail":"拜訪秘密鐵工廠"},
                   {"type":"collect","target":"鐵錠","qty":3,"detail":"收集3個鐵錠"},
                   {"type":"collect","target":"魔法粉","qty":1,"detail":"收集魔法粉"}],
     "reward_exp":120,"reward_gold":50,"reward_item":"鋼刀","reward_reputation":15,
     "reward_relationships":{"左間小蒼蘭":20},"next_quest":"MQ-03"},
    {"id":"MQ-03","title":"圖書館之謎","type":"main","giver":"系統",
     "desc":"中央大圖書館的地下層藏著古老的秘密。",
     "conditions":{"required_level":5,"required_quests":["MQ-02"],"time_available":{"start_hour":0,"end_hour":24}},
     "objectives":[{"type":"visit","target":"中央大圖書館","detail":"造訪中央大圖書館"},
                   {"type":"visit","target":"英靈殿","detail":"探索英靈殿"}],
     "reward_exp":100,"reward_gold":40,"reward_item":"記憶水晶","reward_reputation":20,
     "next_quest":"MQ-04"},
    {"id":"MQ-04","title":"世界的盡頭","type":"main","giver":"系統",
     "desc":"前往海峽，尋找通往世界盡頭的道路。",
     "conditions":{"required_level":7,"required_quests":["MQ-03"],"time_available":{"start_hour":0,"end_hour":24}},
     "objectives":[{"type":"visit","target":"海峽","detail":"到達海峽"},
                   {"type":"defeat","target":"古代守衛","qty":1,"detail":"擊敗古代守衛"}],
     "reward_exp":200,"reward_gold":100,"reward_item":"神秘地圖","reward_reputation":30,
     "failure":{"timeout_hours":72,"on_fail":"penalty","penalty":{"gold":-50,"rep":-10}}},

    # ── Side Quests (with conditions) ──
    {"id":"SQ-01","title":"收集藥材","type":"side","giver":"紅",
     "desc":"紅需要草藥來製作藥水。",
     "conditions":{"required_relationships":{"紅":10},"time_available":{"start_hour":8,"end_hour":20}},
     "objectives":[{"type":"collect","target":"草藥","qty":5,"detail":"收集5份草藥"}],
     "reward_exp":30,"reward_gold":15,"reward_item":"治療藥水","reward_reputation":5,
     "reward_relationships":{"紅":10}},
    {"id":"SQ-02","title":"強化作戰","type":"side","giver":"小狐丸",
     "desc":"小狐丸需要一些鐵礦來強化武器。",
     "conditions":{"required_relationships":{"小狐丸":20},"time_available":{"start_hour":6,"end_hour":18}},
     "objectives":[{"type":"collect","target":"鐵礦","qty":4,"detail":"收集4個鐵礦"}],
     "reward_exp":40,"reward_gold":20,"reward_item":"鐵劍","reward_reputation":8,
     "reward_relationships":{"小狐丸":15},"next_quest":"SQ-08"},
    {"id":"SQ-03","title":"妖精的請求","type":"side","giver":"晴空",
     "desc":"機械妖精晴空需要魔法粉來維持飛行翼膜。",
     "conditions":{"required_race":"獸娘","required_relationships":{"晴空":15},"time_available":{"start_hour":8,"end_hour":20}},
     "objectives":[{"type":"collect","target":"魔法粉","qty":2,"detail":"收集2份魔法粉"}],
     "reward_exp":50,"reward_gold":25,"reward_item":"護身符","reward_reputation":10,
     "reward_relationships":{"晴空":15}},
    {"id":"SQ-04","title":"森林巡邏","type":"side","giver":"系統",
     "desc":"森林深處最近不太平靜，去巡邏一下。",
     "conditions":{"required_level":3,"time_available":{"start_hour":6,"end_hour":18}},
     "objectives":[{"type":"visit","target":"森林深處","detail":"造訪森林深處"},
                   {"type":"defeat","target":"巨熊","qty":1,"detail":"擊敗巨熊"}],
     "reward_exp":60,"reward_gold":30,"reward_item":"皮革","reward_reputation":12},
    {"id":"SQ-05","title":"礦坑探險","type":"side","giver":"系統",
     "desc":"廢棄礦坑據說有豐富的礦產資源。",
     "conditions":{"required_level":5,"time_available":{"start_hour":0,"end_hour":24}},
     "objectives":[{"type":"visit","target":"廢棄礦坑","detail":"造訪廢棄礦坑"},
                   {"type":"collect","target":"鐵礦","qty":6,"detail":"收集6個鐵礦"}],
     "reward_exp":70,"reward_gold":35,"reward_item":"鐵盔","reward_reputation":15},
    {"id":"SQ-06","title":"貨物運送","type":"side","giver":"紅",
     "desc":"幫紅運送一批貨物到西翼大市集。",
     "conditions":{"required_relationships":{"紅":15},"time_available":{"start_hour":6,"end_hour":20}},
     "objectives":[{"type":"visit","target":"西翼大市集","detail":"造訪西翼大市集"}],
     "reward_exp":25,"reward_gold":40,"reward_item":"乾糧","reward_reputation":5,
     "reward_relationships":{"紅":10}},
    {"id":"SQ-07","title":"修理工具","type":"side","giver":"左間小蒼蘭",
     "desc":"左間小蒼蘭的工具壞了，需要鐵錠修理。",
     "conditions":{"required_relationships":{"左間小蒼蘭":15},"giver_activity":"focused","time_available":{"start_hour":7,"end_hour":21}},
     "objectives":[{"type":"collect","target":"鐵錠","qty":2,"detail":"收集2個鐵錠"}],
     "reward_exp":35,"reward_gold":15,"reward_item":"匕首","reward_reputation":8,
     "reward_relationships":{"左間小蒼蘭":12}},
    {"id":"SQ-08","title":"驅除暗影","type":"side","giver":"小狐丸",
     "desc":"鏡湖附近出現暗影靈，需要清除。",
     "conditions":{"required_quests":["SQ-02"],"time_available":{"start_hour":18,"end_hour":6}},
     "objectives":[{"type":"defeat","target":"暗影靈","qty":2,"detail":"擊敗2隻暗影靈"}],
     "reward_exp":55,"reward_gold":25,"reward_item":"魔力藥水","reward_reputation":10,
     "reward_relationships":{"小狐丸":15}},
    {"id":"SQ-09","title":"收集材料","type":"side","giver":"系統",
     "desc":"收集各種材料以充實倉庫。",
     "conditions":{"required_level":2,"time_available":{"start_hour":0,"end_hour":24}},
     "objectives":[{"type":"collect","target":"木材","qty":3,"detail":"收集3份木材", "alt_item":"木柄"},
                   {"type":"collect","target":"皮革","qty":2,"detail":"收集2份皮革"}],
     "reward_exp":20,"reward_gold":10,"reward_item":"空瓶","reward_reputation":3},
    {"id":"SQ-10","title":"探索英靈殿","type":"side","giver":"系統",
     "desc":"英靈殿最近傳出奇怪的聲音。",
     "conditions":{"required_level":4,"time_available":{"start_hour":0,"end_hour":24}},
     "objectives":[{"type":"visit","target":"英靈殿","detail":"造訪英靈殿"}],
     "reward_exp":45,"reward_gold":20,"reward_item":"古老鑰匙","reward_reputation":10},

    # ── Race-specific Tasks ──
    {"id":"TASK-01","title":"艦裝調整","type":"side","giver":"系統",
     "desc":"艦裝身需要定期調整才能維持最佳戰鬥狀態。",
     "conditions":{"required_race":"艦娘","required_level":3,"time_available":{"start_hour":0,"end_hour":24}},
     "objectives":[{"type":"collect","target":"鐵礦","qty":3,"detail":"收集3個鐵礦(艦裝維護)"}],
     "reward_exp":40,"reward_gold":20,"reward_item":"鋼刀","reward_reputation":5},
    {"id":"TASK-02","title":"魔力核心充能","type":"side","giver":"系統",
     "desc":"魔力核心需要定期充能才能維持魔力輸出。",
     "conditions":{"required_race":"術士","required_level":3,"time_available":{"start_hour":0,"end_hour":24}},
     "objectives":[{"type":"collect","target":"魔法粉","qty":2,"detail":"收集2份魔法粉(充能)"}],
     "reward_exp":35,"reward_gold":25,"reward_item":"魔力藥水","reward_reputation":5},
    {"id":"TASK-03","title":"翼膜保養","type":"side","giver":"系統",
     "desc":"翼膜需要特殊材料來保養，才能維持飛行能力。",
     "conditions":{"required_race":"竜族","required_level":3,"time_available":{"start_hour":0,"end_hour":24}},
     "objectives":[{"type":"collect","target":"靈木","qty":3,"detail":"收集3份靈木(翼膜保養)"}],
     "reward_exp":50,"reward_gold":30,"reward_item":"龍鱗","reward_reputation":5},
    {"id":"TASK-04","title":"義體校準","type":"side","giver":"系統",
     "desc":"機械義體需要定期校準才能保持精確。",
     "conditions":{"required_race":"機械","required_level":3,"time_available":{"start_hour":0,"end_hour":24}},
     "objectives":[{"type":"collect","target":"鐵礦","qty":4,"detail":"收集4個鐵礦(義體校準)"}],
     "reward_exp":35,"reward_gold":25,"reward_item":"鐵錠","reward_reputation":5},

    # ── Daily Quests (reset each day) ──
    {"id":"DQ-01","title":"每日採集","type":"daily","giver":"系統",
     "desc":"每天到野外採集一些材料。",
     "conditions":{"required_level":1,"time_available":{"start_hour":0,"end_hour":24}},
     "objectives":[{"type":"collect","target":"草藥","qty":3,"detail":"採集3份草藥"}],
     "reward_exp":15,"reward_gold":5,"reward_reputation":1},
    {"id":"DQ-02","title":"每日鍛鍊","type":"daily","giver":"系統",
     "desc":"每天進行戰鬥訓練。",
     "conditions":{"required_level":1,"time_available":{"start_hour":0,"end_hour":24}},
     "objectives":[{"type":"defeat","target":"野狼","qty":1,"detail":"擊敗1隻野狼"}],
     "reward_exp":20,"reward_gold":8,"reward_reputation":1},
    {"id":"DQ-03","title":"每日交友","type":"daily","giver":"系統",
     "desc":"每天與NPC交流增進關係。",
     "conditions":{"required_level":1,"time_available":{"start_hour":0,"end_hour":24}},
     "objectives":[{"type":"social","target":"任何NPC","qty":1,"detail":"與任意NPC對話交流"}],
     "reward_exp":10,"reward_gold":5,"reward_reputation":2},
]

# Daily quest tracking — reset when day changes
DAILY_QUESTS_IDS = ["DQ-01","DQ-02","DQ-03"]
_LAST_DAILY_RESET_DAY = 0

def reset_daily_quests(character, current_day):
    """Reset daily quest completion tracking each day."""
    global _LAST_DAILY_RESET_DAY
    if current_day != _LAST_DAILY_RESET_DAY:
        _LAST_DAILY_RESET_DAY = current_day
        # Remove daily quests from completed list so they can be done again
        completed = character.get("completed_quests", [])
        character["completed_quests"] = [qid for qid in completed if qid not in DAILY_QUESTS_IDS]
        # Remove completed daily entries from quest tracking
        qs = character.get("quests", {})
        for dqid in DAILY_QUESTS_IDS:
            if dqid in qs and qs[dqid]["status"] == "completed":
                del qs[dqid]
        return True
    return False

# Race-specific task IDs
RACE_TASK_IDS = ["TASK-01","TASK-02","TASK-03","TASK-04"]



# ═══════════════════════════════════════════════════════════
# VEHICLES (4 vehicles)
# ═══════════════════════════════════════════════════════════

VEHICLES = {
    "腳踏車":{"speed":1.5,"capacity":1,"cargo":20,"fuel":100,"fuel_type":"stamina","fuel_per_hour":2,"desc":"普通的腳踏車，省力快速"},
    "馬":    {"speed":2.0,"capacity":1,"cargo":30,"fuel":80,"fuel_type":"feed","fuel_per_hour":3,"desc":"一匹溫順的馬"},
    "馬車":  {"speed":1.2,"capacity":3,"cargo":100,"fuel":120,"fuel_type":"feed","fuel_per_hour":2,"desc":"載貨用馬車"},
    "小舟":  {"speed":1.3,"capacity":2,"cargo":15,"fuel":60,"fuel_type":"stamina","fuel_per_hour":4,"desc":"簡易的小舟，可渡水"},
}

VEHICLE_LOCATIONS = {
    "方碑丘":     "腳踏車",
    "西翼大市集": "馬",
    "鏡湖":       "小舟",
    "秘密鐵工廠": "馬車",
}


# ═══════════════════════════════════════════════════════════
# SCENE OBJECTS (20 objects across locations)
# ═══════════════════════════════════════════════════════════

SCENE_OBJECTS = {
    "方碑丘": [
        {"id":"well",    "name":"水井",     "type":"container","desc":"村莊中央的老水井","contents":["空瓶","小石頭"],"locked":False,"interactable":True},
        {"id":"bench",   "name":"長椅",     "type":"decoration","desc":"一張木製長椅","interactable":True},
        {"id":"notice",  "name":"佈告欄",    "type":"decoration","desc":"貼滿了各種告示","note":"徵人啟事：需要冒險者協助處理鏡湖異變","interactable":True},
        {"id":"bell",    "name":"村莊鐘樓",  "type":"mechanism","mechanism_type":"lever","desc":"村莊中央的古老鐘樓，拉繩可以敲響大鐘",
         "state":False,"trigger_once":False,"triggered":False,
         "effect":{"type":"heal","hp":0,"sp":40,                   "message":"鐘聲響徹雲霄！悠揚的鐘聲讓身心得到了休息。"},
         "on_repeat":"鐘聲再次響起，迴盪在山谷之間。"},
    ],
    "鏡湖": [
        {"id":"crystal", "name":"水晶簇",    "type":"container","desc":"湖邊的水晶簇","contents":["水晶碎片","水晶碎片"],"locked":False,"interactable":True},
        {"id":"boat",    "name":"小木船",    "type":"vehicle","desc":"停靠在湖邊的小船","vehicle_type":"小木船","interactable":True},
        {"id":"shrine",  "name":"湖底祭壇",  "type":"mechanism","mechanism_type":"pedestal","desc":"湖中央的古老祭壇，似乎需要某種祭品",
         "state":False,"trigger_once":True,"triggered":False,
         "requirements":{"item":"水晶碎片","consume":True,"qty":3},
         "effect":{"type":"reveal","items":["記憶水晶","古老鑰匙"],
                   "message":"祭壇發出耀眼的光芒！從水中浮現出了寶物！"},
         "requirements_msg":"需要在水晶祭壇上放置3枚水晶碎片。",
         "failure_msg":"祭壇沒有反應...需要放入更多的水晶碎片。"},
    ],
    "西翼大市集": [
        {"id":"stall1",  "name":"蔬果攤",    "type":"container","desc":"擺滿新鮮蔬果的攤位","contents":["乾糧","草藥"],"locked":False,"interactable":True},
        {"id":"stall2",  "name":"雜貨攤",    "type":"container","desc":"賣著各種日用品的攤位","contents":["空瓶","麻繩","蠟燭頭"],"locked":False,"interactable":True},
    ],
    "中央大圖書館": [
        {"id":"bookshelf","name":"書架",     "type":"container","desc":"高大的書架，上面擺滿了書","contents":["書信","古老鑰匙"],"locked":False,"interactable":True},
        {"id":"desk",    "name":"閱讀桌",    "type":"decoration","desc":"一張木製閱讀桌","note":"桌上攤開了一本關於鏡湖的古老文獻","interactable":True},
        {"id":"hidden_switch","name":"隱藏書架","type":"mechanism","mechanism_type":"hidden_switch","desc":"書架上的一本書位置有些奇怪",
         "state":False,"trigger_once":True,"triggered":False,
         "effect":{"type":"reveal","items":["古老鑰匙","神秘地圖"],
                   "message":"書架緩緩滑開，露出了後方的暗格！"},
         "on_repeat":"暗格已經被打開了。"},
    ],
    "海峽": [
        {"id":"lighthouse","name":"燈塔開關","type":"mechanism","mechanism_type":"lever","desc":"海峽燈塔的控制桿",
         "state":False,"trigger_once":False,"triggered":False,
         "effect":{"type":"route_open","target":"海峽","value":"east",
                   "message":"燈塔的光芒照射向遠方，照亮了一片未知的海域！"},
         "on_repeat":"燈塔已經被點亮了。"},
    ],
    "秘密鐵工廠": [
        {"id":"forge",   "name":"熔爐",     "type":"workstation","desc":"熾熱的熔爐","station_type":"forge","interactable":True},
        {"id":"anvil",   "name":"鐵砧",     "type":"decoration","desc":"沉重的鐵砧","note":"上面有精美的雕紋","interactable":True},
        {"id":"toolbox", "name":"工具箱",    "type":"container","desc":"師傅的工具箱","contents":["鐵錠","鐵礦","鐵礦"],"locked":False,"interactable":True},
        {"id":"valve",   "name":"蒸氣閥門",  "type":"mechanism","mechanism_type":"gear","desc":"巨大的蒸氣閥門，需要多次轉動才能打開",
         "state":False,"trigger_once":False,"triggered":False,
         "charges":0,"max_charges":3,
         "effect":{"type":"reveal","items":["龍鱗","火元素","鐵錠"],
                   "message":"閥門完全打開！蒸氣散去，露出了隱藏的儲藏室！"},
         "progress_msg":"閥門轉動了 %d/3 圈。",
         "fail_msg":"閥門紋絲不動...需要更大的力量。",
         "on_repeat":"閥門已經完全打開了。"},
    ],
    "便利店": [
        {"id":"shelf1",  "name":"貨架A",    "type":"container","desc":"飲料和食品貨架","contents":["提神茶","乾糧","乾糧"],"locked":False,"interactable":True},
        {"id":"shelf2",  "name":"貨架B",    "type":"container","desc":"日用百貨貨架","contents":["繃帶","蠟燭頭","麻繩"],"locked":False,"interactable":True},
    ],
    "英靈殿": [
        {"id":"altar",   "name":"祭祀台",    "type":"container","desc":"古老的祭祀台","contents":["龍鱗","古老鑰匙"],"locked":True,"key":"古老鑰匙","interactable":True},
        {"id":"weapon_rack","name":"武器架",  "type":"container","desc":"陳列著武器的架子","contents":["鋼刀","鐵劍"],"locked":False,"interactable":True},
        {"id":"summon_pedestal","name":"英靈召喚台","type":"mechanism","mechanism_type":"pedestal","desc":"召喚古代英靈的基座",
         "state":False,"trigger_once":True,"triggered":False,
         "requirements":{"item":"古老鑰匙","level":5,"consume":False},
         "effect":{"type":"summon","enemy":"古代守衛","count":1,
                   "message":"基座發出耀眼的光芒！一位古代英靈降臨了！"},
         "requirements_msg":"需要古老的鑰匙和高超的實力才能啟動。（Lv.5+）",
         "failure_msg":"基座毫無反應..."},
        {"id":"throne","name":"王之寶座",    "type":"mechanism","mechanism_type":"pressure_plate","desc":"大殿正中央的王座",
         "state":False,"trigger_once":True,"triggered":False,
         "effect":{"type":"reveal","items":["水晶法杖","龍鱗"],
                   "message":"你坐上了王座，地面震動，暗門打開露出了寶庫！"},
         "on_repeat":"寶庫已經被打開了。"},
    ],
    "廢棄礦坑": [
        {"id":"ore_vein","name":"礦脈",     "type":"container","desc":"裸露的礦石脈","contents":["鐵礦","鐵礦","水晶碎片"],"locked":False,"interactable":True},
        {"id":"trolley", "name":"礦車",     "type":"container","desc":"廢棄的礦車","contents":["鐵礦","小石頭"],"locked":False,"interactable":True},
        {"id":"lever",   "name":"礦車控制桿","type":"mechanism","mechanism_type":"lever","desc":"控制礦車軌道的轉轍器",
         "state":False,"trigger_once":True,"triggered":False,
         "effect":{"type":"teleport","target":"方碑丘",
                   "message":"你拉下了控制桿！礦車順著軌道疾馳而去..."},
         "on_repeat":"轉轍器已經被扳動過了。"},
        {"id":"explosive","name":"爆破裝置",  "type":"mechanism","mechanism_type":"pedestal","desc":"礦坑深處的爆破裝置",
         "state":False,"trigger_once":True,"triggered":False,
         "requirements":{"item":"火元素","consume":True,"qty":2},
         "effect":{"type":"route_open","target":"廢棄礦坑","value":"deep",
                   "message":"轟！！爆炸聲在礦坑中迴盪，通往更深處的通道被打開了！"},
         "requirements_msg":"需要2枚火元素來引爆。",
         "failure_msg":"缺少引爆物..."},
    ],
    "森林深處": [
        {"id":"ancient_tree","name":"古樹",  "type":"container","desc":"參天的古老巨木","contents":["靈木","靈木","生命果"],"locked":False,"interactable":True},
        {"id":"camp",    "name":"廢棄營地",  "type":"container","desc":"冒險者留下的營地","contents":["乾糧","繃帶","木柄"],"locked":False,"interactable":True},
        {"id":"monolith","name":"古老石碑",  "type":"mechanism","mechanism_type":"pedestal","desc":"刻滿符文的神秘石碑",
         "state":False,"trigger_once":True,"triggered":False,
         "requirements":{"item":"生命果","consume":True,"qty":1},
         "effect":{"type":"heal","hp":999,"sp":999,
                   "message":"石碑上的符文亮起！森林的力量湧入你的體內！"},
         "requirements_msg":"需要獻上1枚生命果作為祭品。",
         "failure_msg":"石碑沒有反應..."},
    ],
}


# ═══════════════════════════════════════════════════════════
# WEATHER SYSTEM
# ═══════════════════════════════════════════════════════════

WEATHER_TYPES = ["☀晴","⛅多雲","🌧雨","🌫霧","🌩雷雨","❄雪"]

def roll_weather():
    r = _random.random()
    if r < 0.40: return "☀晴"
    if r < 0.65: return "⛅多雲"
    if r < 0.80: return "🌧雨"
    if r < 0.90: return "🌫霧"
    if r < 0.97: return "🌩雷雨"
    return "❄雪"

WEATHER_EFFECTS = {
    "☀晴":   {"encounter":0.35, "loot_bonus":0,   "rest_bonus":1.0, "desc":"視野良好"},
    "⛅多雲": {"encounter":0.40, "loot_bonus":0,   "rest_bonus":0.9, "desc":"天色陰沉"},
    "🌧雨":  {"encounter":0.30, "loot_bonus":0.1, "rest_bonus":1.1, "desc":"雨聲掩蓋了腳步"},
    "🌫霧":  {"encounter":0.50, "loot_bonus":0.2, "rest_bonus":0.8, "desc":"視線受阻"},
    "🌩雷雨":{"encounter":0.20, "loot_bonus":0.3, "rest_bonus":1.2, "desc":"雷聲轟鳴"},
    "❄雪":  {"encounter":0.25, "loot_bonus":0.1, "rest_bonus":1.3, "desc":"白雪覆蓋大地"},
}


# ═══════════════════════════════════════════════════════════
# RANDOM EVENT POOL
# ═══════════════════════════════════════════════════════════

RANDOM_EVENTS = [
    ("你發現地上有個錢包，裡面有5金幣。", lambda c: c.update({"gold":c.get("gold",0)+5})),
    ("一陣風吹來，你打了個噴嚏。", None),
    ("你看到遠處有一隻兔子快速跑過。", None),
    ("草叢中有沙沙聲...但什麼都沒有。", None),
    ("你聽到遠方傳來的鐘聲。", None),
    ("一隻蝴蝶停在你肩膀上，然後飛走了。", None),
    ("你撿到一根漂亮的羽毛。", lambda c: c["inventory"].append("羽毛")),
    ("地面有一個閃亮的東西——是一枚硬幣！", lambda c: c.update({"gold":c.get("gold",0)+3})),
    ("你發現了一些可食用的野莓。", lambda c: c.update({"hp":min(c["max_hp"],c["hp"]+5)})),
    ("你注意到石頭下壓著一朵乾燥花。", lambda c: c["inventory"].append("乾燥花")),
    ("你踩到一灘水，腳濕了。", None),
    ("這裡的空氣特別清新，你深呼吸了一下。", lambda c: c.update({"sp":min(c["max_sp"],c["sp"]+5)})),
    ("你看到一隻松鼠在樹上看著你。", None),
    ("路邊有一個被遺忘的貝殼。", lambda c: c["inventory"].append("貝殼")),
    ("你的影子看起來比平常長一些。", None),
]

def roll_random_event(character):
    if _random.random() < 0.2:  # 20% chance
        desc, action = _random.choice(RANDOM_EVENTS)
        print("  " + desc)
        if action:
            action(character)
        return True
    return False


# ═══════════════════════════════════════════════════════════
# RACE DATA — defines body parts, slots, bonuses per race
# ═══════════════════════════════════════════════════════════

RACE_DATA = {
    "人類": {
        "body_parts": ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg"],
        "extra_slots": [],
        "required_tokens": [],
        "innate_bonuses": {},
        "base_hp": 100, "base_sp": 50,
        "desc": "標準人型生物"
    },
    "艦娘": {
        "body_parts": ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg", "rigging_body"],
        "extra_slots": [("rigging","艦裝")],
        "required_tokens": ["naval"],
        "innate_bonuses": {"spd": 0.5},
        "base_hp": 120, "base_sp": 40,
        "desc": "擁有艦裝身的人型艦艇"
    },
    "獸娘": {
        "body_parts": ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg", "tail", "claws"],
        "extra_slots": [("tail","尾部"), ("claws","爪部")],
        "required_tokens": ["beast"],
        "innate_bonuses": {"spd": 0.3, "atk": 0.2},
        "base_hp": 110, "base_sp": 45,
        "desc": "具有動物特徵的人型生物"
    },
    "術士": {
        "body_parts": ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg", "mana_core"],
        "extra_slots": [("core","核心")],
        "required_tokens": ["element"],
        "innate_bonuses": {"karma": 0.5},
        "base_hp": 80, "base_sp": 80,
        "desc": "擁有魔力核心的魔法使用者"
    },
    "竜族": {
        "body_parts": ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg", "wings", "horns"],
        "extra_slots": [("wings","翼部"), ("horns","角部")],
        "required_tokens": ["draconic"],
        "innate_bonuses": {"atk": 0.5, "def": 0.3},
        "base_hp": 150, "base_sp": 30,
        "desc": "具有龍族血統的強大生物"
    },
    "機械": {
        "body_parts": ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg", "cyber_limbs"],
        "extra_slots": [("upgrade","升級")],
        "required_tokens": ["mechanism"],
        "innate_bonuses": {"def": 0.4, "spd": -0.1},
        "base_hp": 130, "base_sp": 20,
        "desc": "機械義體改造者"
    },
    "精霊": {
        "body_parts": ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg", "spirit_body"],
        "extra_slots": [("aura","靈裝")],
        "required_tokens": ["spiritual"],
        "innate_bonuses": {"karma": 0.3, "spd": 0.2},
        "base_hp": 60, "base_sp": 100,
        "desc": "半靈體存在的精靈"
    },
}

RACE_DETECT_MAP = {
    "naval": "艦娘",
    "beast": "獸娘",
    "draconic": "竜族",
    "mechanism": "機械",
    "element": "術士",
    "spiritual": "精霊",
}

def detect_race(token_list: list) -> str:
    """Detect character's race from their token categories."""
    cats = {t.get("category", "") for t in token_list if t.get("category")}
    for tok_cat, race in RACE_DETECT_MAP.items():
        if tok_cat in cats:
            return race
    return "人類"

def get_race_slots(race: str) -> list:
    """Get extra equipment slots for a race."""
    rd = RACE_DATA.get(race, RACE_DATA["人類"])
    return rd.get("extra_slots", [])

def get_race_body_parts(race: str) -> list:
    """Get body part IDs for a race."""
    rd = RACE_DATA.get(race, RACE_DATA["人類"])
    return rd.get("body_parts", [])

RACE_NAMES = sorted(RACE_DATA.keys())

# ═══════════════════════════════════════════════════════════
# EQUIPMENT MANAGER (12 base slots + race-specific slots)
# ═══════════════════════════════════════════════════════════

BASE_EQUIPMENT_SLOTS = [
    ("head","頭部"),("face","面部"),("neck","頸部"),
    ("torso","軀幹"),("left_arm","左臂"),("right_arm","右臂"),
    ("left_hand","左手"),("right_hand","右手"),
    ("waist","腰部"),("legs","腿部"),("feet","腳部"),("back","背部"),
]

def get_equipment_slots_for_character(character) -> list:
    """Get full equipment slots list including race-specific ones."""
    slots = list(BASE_EQUIPMENT_SLOTS)
    race = character.get("race", "人類")
    extra = get_race_slots(race)
    for slot_id, slot_name in extra:
        if (slot_id, slot_name) not in slots:
            slots.append((slot_id, slot_name))
    return slots

# For backward compatibility
EQUIPMENT_SLOTS = list(BASE_EQUIPMENT_SLOTS)

class EquipmentManager:
    def __init__(self, character=None):
        slots_base = BASE_EQUIPMENT_SLOTS
        self.race = "人類"
        if character:
            slots_base = get_equipment_slots_for_character(character)
            self.race = character.get("race", "人類")
        self.slots = {s[0]: None for s in slots_base}
        self._slot_order = slots_base

    def equip(self, slot_id, item):
        old = self.slots.get(slot_id)
        self.slots[slot_id] = {"item": item, "durability_loss": 0}
        return old

    def unequip(self, slot_id):
        eq = self.slots.get(slot_id)
        if eq:
            self.slots[slot_id] = None
            return eq["item"]
        return None

    def get_stat_bonuses(self):
        bonuses = {}
        for sid, eq in self.slots.items():
            if eq and eq["item"]:
                for stat, mult in eq["item"].get("stat_multipliers", {}).items():
                    bonuses[stat] = bonuses.get(stat, 0.0) + mult
        # Add race innate bonuses
        rd = RACE_DATA.get(self.race, {})
        for stat, mult in rd.get("innate_bonuses", {}).items():
            bonuses[stat] = bonuses.get(stat, 0.0) + mult
        return bonuses

    def apply_stat_bonuses(self, character):
        bonuses = self.get_stat_bonuses()
        token_list = character.get("token_list", [])
        base_atk = 10 + (character["level"] - 1) * 1 + len([t for t in token_list if t.get("category")=="combat"])*3
        base_def = 5 + (character["level"] - 1) * 1 + len([t for t in token_list if t.get("category")=="vitality"])*2
        base_spd = character.get("spd", 5)
        base_karma = character.get("karma", 5)
        character["atk"] = max(1, int(base_atk * (1.0 + bonuses.get("atk", 0.0))))
        character["defense"] = max(1, int(base_def * (1.0 + bonuses.get("defense", 0.0))))
        character["spd"] = max(1, int(base_spd * (1.0 + bonuses.get("spd", 0.0))))
        if "karma" in character:
            character["karma"] = max(1, int(base_karma * (1.0 + bonuses.get("karma", 0.0))))

    def use_durability(self, slot_id, amount=1):
        eq = self.slots.get(slot_id)
        if not eq or not eq["item"]:
            return False
        eq["durability_loss"] += amount
        item = eq["item"]
        max_dur = item.get("durability", 100)
        cur = max(0, max_dur - eq["durability_loss"])
        item["current_durability"] = cur
        return cur <= 0

    def condition_name(self, slot_id):
        eq = self.slots.get(slot_id)
        if not eq or not eq["item"]:
            return "空"
        cur = eq["item"].get("current_durability", eq["item"].get("durability", 100))
        mx = eq["item"].get("durability", 100)
        ratio = cur/mx if mx>0 else 1
        if ratio>0.8: return "完好"
        if ratio>0.6: return "輕微磨損"
        if ratio>0.4: return "中度磨損"
        if ratio>0.2: return "嚴重磨損"
        return "已損壞"

    def display(self):
        lines = ["%s 裝備欄:" % self.race]
        for sid, sname in self._slot_order:
            eq = self.slots.get(sid)
            if eq and eq["item"]:
                c = self.condition_name(sid)
                lines.append("  %s: %s [%s]" % (sname, eq["item"].get("name","?"), c))
            else:
                lines.append("  %s: （空）"% sname)
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
# DISPLAY HELPERS
# ═══════════════════════════════════════════════════════════

def display_world_map(current_location):
    lines = []
    lines.append('世界地図:')
    lines.append('')
    lines.append('    +---------+---------+')
    lines.append('    |  鏡湖   |  海峽   |')
    lines.append('    +----+----+----+----+')
    lines.append('    |秘鐵| 方碑丘 |西翼 |')
    lines.append('    +----+----+----+----+')
    lines.append('         |    |    |    |')
    lines.append('    +----+----+----+    +')
    lines.append('    |森林|圖書館|英靈殿|')
    lines.append('    +----+----+----+----+')
    lines.append('         |廢礦|')
    lines.append('         +----+')
    lines.append('')
    lines.append('  現在位置: ' + current_location)
    for loc, vibe in LOCATION_VIBES.items():
        if loc == current_location:
            lines.append('  ' + vibe)
            break
    return "\n".join(lines)
