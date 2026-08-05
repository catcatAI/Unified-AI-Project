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

# Placeholders populated by game_data.expand_game()
FACTIONS = {
    "NAT-01": {
        "name": "聖諭同盟",
        "type": "nation",
        "description": "「神權引領進化」。靈子是神賜的恩典，應以符文工藝優雅地運用，而非粗暴的工業化"
    },
    "NAT-02": {
        "name": "唯靈聯邦",
        "type": "nation",
        "description": "「靈子應被工具化」。靈子不是神聖的，它是可被測量、提煉、工業化應用的資源。神靈種不是守護神，是武器"
    },
    "NAT-03": {
        "name": "永久中立地帶",
        "type": "nation",
        "description": "「不參與陣營對抗」。拒絕在聖諭同盟與唯靈聯邦之間選邊"
    },
    "NAT-04": {
        "name": "緩衝商業聯合體",
        "type": "nation",
        "description": "「利潤不選邊」。同時向聖諭同盟與唯靈聯邦出售資源、技術、與軍事物資"
    },
    "NAT-05": {
        "name": "武裝中立聯合",
        "type": "nation",
        "description": "「和平來自於力量均勢」。向所有陣營出售武器，確保任何一方都無法取得決定性優勢"
    },
    "NAT-06": {
        "name": "莫比迪克自由邦聯（簡稱「莫比迪克」）",
        "type": "nation",
        "description": "W01 靈子塵埃"
    },
    "NAT-07": {
        "name": "阿比薩深渊联邦",
        "type": "nation",
        "description": "W01 靈子塵埃"
    },
    "ORG-03": {
        "name": "紫晶石集會",
        "type": "organization",
        "description": "W01 靈子塵埃"
    },
    "ORG-04": {
        "name": "失戀集團",
        "type": "organization",
        "description": "W01 靈子塵埃"
    },
    "ORG-05": {
        "name": "終末燭光",
        "type": "organization",
        "description": "W01 靈子塵埃"
    },
    "ORG-06": {
        "name": "新世界集團",
        "type": "organization",
        "description": "W01 靈子塵埃"
    },
    "ORG-08": {
        "name": "脈動工業（Pulse Industries）",
        "type": "organization",
        "description": "W01 靈子塵埃"
    },
    "ORG-09": {
        "name": "永恆義體（Eternal Cybernetics）",
        "type": "organization",
        "description": "W01 靈子塵埃"
    },
    "ORG-10": {
        "name": "鐵砧防務（Anvil Defense）",
        "type": "organization",
        "description": "W01 靈子塵埃"
    },
    "ORG-16": {
        "name": "鼠族工業聯合體 (鼠聯)",
        "type": "organization",
        "description": "拾荒者聯盟"
    },
    "ORG-17": {
        "name": "貓族海盜聯合艦隊 (黑帆)",
        "type": "organization",
        "description": "重建者"
    },
    "ORG-18": {
        "name": "藍鰭航運",
        "type": "organization",
        "description": "太空管理"
    },
    "ORG-19": {
        "name": "潮汐基金會",
        "type": "organization",
        "description": "中世紀體制"
    },
    "ORG-20": {
        "name": "納迦皇家地熱",
        "type": "organization",
        "description": "緩衝區貿易"
    },
    "ORG-21": {
        "name": "人魚聲吶網絡",
        "type": "organization",
        "description": "前文明遺產探索"
    },
    "ORG-22": {
        "name": "海蛞蝓生技",
        "type": "organization",
        "description": "時代保存者"
    },
    "ORG-23": {
        "name": "水母幻光娛樂",
        "type": "organization",
        "description": "學術網絡"
    },
    "ORG-24": {
        "name": "海葵共生農場",
        "type": "organization",
        "description": "紀錄與歸檔"
    },
    "ORG-01": {
        "name": "彩虹戰隊",
        "type": "organization",
        "description": "正派組織，七色戰士組成的正義團隊。成員：紅（便利店員）、橙（獸醫）、黃（物理老師）等"
    },
    "ORG-02": {
        "name": "魔法少女聯合體",
        "type": "organization",
        "description": "跨集團協議網絡，設有代表理事會制度。下轄魔法少女溝通部門作為政府聯絡窗口"
    }
}
NATIONS = {
    "NAT-01": {
        "name": "聖諭同盟",
        "type": "nation",
        "description": "「神權引領進化」。靈子是神賜的恩典，應以符文工藝優雅地運用，而非粗暴的工業化"
    },
    "NAT-02": {
        "name": "唯靈聯邦",
        "type": "nation",
        "description": "「靈子應被工具化」。靈子不是神聖的，它是可被測量、提煉、工業化應用的資源。神靈種不是守護神，是武器"
    },
    "NAT-03": {
        "name": "永久中立地帶",
        "type": "nation",
        "description": "「不參與陣營對抗」。拒絕在聖諭同盟與唯靈聯邦之間選邊"
    },
    "NAT-04": {
        "name": "緩衝商業聯合體",
        "type": "nation",
        "description": "「利潤不選邊」。同時向聖諭同盟與唯靈聯邦出售資源、技術、與軍事物資"
    },
    "NAT-05": {
        "name": "武裝中立聯合",
        "type": "nation",
        "description": "「和平來自於力量均勢」。向所有陣營出售武器，確保任何一方都無法取得決定性優勢"
    },
    "NAT-06": {
        "name": "莫比迪克自由邦聯（簡稱「莫比迪克」）",
        "type": "nation",
        "description": "W01 靈子塵埃"
    },
    "NAT-07": {
        "name": "阿比薩深渊联邦",
        "type": "nation",
        "description": "W01 靈子塵埃"
    }
}
ACTIVE_RULES = {}
NPC_FACTIONS = {
    "千島 雉": [
        "ORG-03"
    ],
    "千島 忠臣": [
        "ORG-03"
    ],
    "千島鐵之介": [
        "ORG-03"
    ],
    "喪咕 雪禍咪 閃雷": [
        "ORG-01",
        "ORG-06"
    ],
    "猞妒蝕津": [
        "ORG-01",
        "ORG-06"
    ],
    "猞妒忌依": [
        "ORG-04",
        "ORG-01"
    ],
    "奶油泡芙": [
        "ORG-06"
    ],
    "鈿乾 芊蒔": [
        "ORG-04"
    ],
    "夜鈴": [
        "ORG-04",
        "ORG-01"
    ],
    "啮輪·鋼須": [
        "ORG-17"
    ],
    "暗爪·刃尾": [
        "ORG-17"
    ],
    "深痕 · 裂脊": [
        "ORG-21",
        "ORG-20"
    ],
    "漣 · 迴聲": [
        "ORG-22",
        "ORG-21"
    ],
    "沫 · 彩衣": [
        "ORG-22"
    ]
}
LOCATION_NATIONS = {
    "NAT-01": {
        "name": "聖諭同盟",
        "type": "nation",
        "description": "「神權引領進化」。靈子是神賜的恩典，應以符文工藝優雅地運用，而非粗暴的工業化"
    },
    "NAT-02": {
        "name": "唯靈聯邦",
        "type": "nation",
        "description": "「靈子應被工具化」。靈子不是神聖的，它是可被測量、提煉、工業化應用的資源。神靈種不是守護神，是武器"
    },
    "NAT-03": {
        "name": "永久中立地帶",
        "type": "nation",
        "description": "「不參與陣營對抗」。拒絕在聖諭同盟與唯靈聯邦之間選邊"
    },
    "NAT-04": {
        "name": "緩衝商業聯合體",
        "type": "nation",
        "description": "「利潤不選邊」。同時向聖諭同盟與唯靈聯邦出售資源、技術、與軍事物資"
    },
    "NAT-05": {
        "name": "武裝中立聯合",
        "type": "nation",
        "description": "「和平來自於力量均勢」。向所有陣營出售武器，確保任何一方都無法取得決定性優勢"
    },
    "NAT-06": {
        "name": "莫比迪克自由邦聯（簡稱「莫比迪克」）",
        "type": "nation",
        "description": "W01 靈子塵埃"
    },
    "NAT-07": {
        "name": "阿比薩深渊联邦",
        "type": "nation",
        "description": "W01 靈子塵埃"
    }
}
LOCATION_RULES = {}
REAL_ESTATE_KEYS = []
NPC_METADATA = {}
VEHICLE_TO_LOCATION = {}
NPC_DIALOGUES = {}

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
    "鐵錠":  {"type": "material", "weight": 1.0, "value": 35, "tags": ["metal"], "desc": "熔煉後的鐵錠"},
    "皮革":  {"type": "material", "weight": 0.8, "value": 12, "tags": ["leather"], "desc": "處理過的獸皮"},
    "布料":  {"type": "material", "weight": 0.3, "value": 8,  "tags": ["cloth"], "desc": "普通布料"},
    "水晶碎片":{"type":"material","weight":0.2,"value": 25, "tags": ["crystal"], "desc":"發著微光的水晶碎片"},
    "魔法粉": {"type": "material", "weight": 0.1, "value": 40, "tags": ["magic"], "desc": "研磨的魔法材料"},
    "龍鱗":  {"type": "material", "weight": 1.5, "value": 80, "tags": ["rare"], "desc": "閃爍的龍鱗片"},
    "靈木":  {"type": "material", "weight": 0.7, "value": 35, "tags": ["wood","magic"], "desc": "蘊含靈力的木材"},
    "絲線":  {"type": "material", "weight": 0.1, "value": 6,  "tags": ["cloth"], "desc": "精緻的絲線"},
    "黏土":  {"type": "material", "weight": 1.0, "value": 3,  "tags": ["clay"], "desc": "可塑形的黏土"},
    "毒針":  {"type": "material", "weight": 0.2, "value": 25, "tags": ["venom"], "desc": "蠍尾的毒針，可作為素材"},
    "古代硬貨":{"type":"junk", "weight": 0.1, "value": 150, "tags": ["rare"], "desc": "古代文明流通的稀有貨幣，價值不菲"},

    # ── Consumables (10) ──
    "火焰藥水":{"type":"consumable","weight":0.3,"value": 50, "heal_hp": 50, "heal_sp":10, "max_stack":10, "desc":"恢復50HP+10SP"},
    "治療藥水":{"type":"consumable","weight":0.3,"value": 40, "heal_hp": 40, "max_stack":10, "desc":"恢復40HP"},
    "魔力藥水":{"type":"consumable","weight":0.3,"value": 45, "heal_sp": 30, "max_stack":10, "desc":"恢復30SP"},
    "乾糧":   {"type":"consumable","weight":0.5,"value": 8,  "heal_hp": 12, "max_stack":20, "desc":"恢復12HP"},
    "解毒草": {"type":"consumable","weight":0.2,"value": 40, "max_stack":10, "desc":"解除中毒狀態"},
    "靈力藥": {"type":"consumable","weight":0.3,"value": 50, "heal_sp": 50, "max_stack":10, "desc":"恢復50SP"},
    "生命果": {"type":"consumable","weight":0.4,"value": 120, "heal_hp": 80, "max_stack":5, "desc":"恢復80HP（稀有）"},
    "提神茶": {"type":"consumable","weight":0.2,"value": 15, "heal_sp": 15, "max_stack":20, "desc":"恢復15SP"},
    "繃帶":   {"type":"consumable","weight":0.2,"value": 12, "heal_hp": 15, "max_stack":10, "desc":"簡易包紮，恢復15HP"},
    "濃縮藥水":{"type":"consumable","weight":0.4,"value": 100, "heal_hp": 100,"heal_sp":30, "max_stack":5, "desc":"高級恢復品"},

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
    "鐵甲": {"type":"armor","weight":5.0,"value": 200,"durability":200,"slot":"torso",
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
     "ingredients":[{"item":"鐵礦","quantity":3}],
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
     "ingredients":[{"item":"魔法粉","quantity":1},{"item":"空瓶","quantity":1}],
     "result_item":"魔力藥水","result_quantity":1,"failure_chance":0.1},
    {"recipe_id":"R08","name":"解毒草","category":"alchemize",
     "ingredients":[{"item":"草藥","quantity":2},{"item":"空瓶","quantity":1}],
     "result_item":"解毒草","result_quantity":1,"failure_chance":0.1},
    {"recipe_id":"R09","name":"靈力藥","category":"alchemize",
     "ingredients":[{"item":"靈木","quantity":1},{"item":"空瓶","quantity":1}],
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
     "ingredients":[{"item":"靈木","quantity":2},{"item":"水晶碎片","quantity":2},{"item":"魔法粉","quantity":1}],
     "result_item":"水晶法杖","result_quantity":1,"failure_chance":0.4},
    {"recipe_id":"R16","name":"生命果","category":"alchemize",
     "ingredients":[{"item":"龍鱗","quantity":1},{"item":"治療藥水","quantity":1}],
     "result_item":"生命果","result_quantity":1,"failure_chance":0.4},
    # ── Repair recipes (物品修復) ──
    {"recipe_id":"R17","name":"修復武器","category":"repair",
     "ingredients":[{"item":"鐵礦","quantity":2},{"item":"鐵錠","quantity":1}],
     "result_item":"修復服務","result_quantity":1,"failure_chance":0.0,"repair_all":True},
    {"recipe_id":"R18","name":"修復防具","category":"repair",
     "ingredients":[{"item":"皮革","quantity":2},{"item":"布料","quantity":1}],
     "result_item":"修復服務","result_quantity":1,"failure_chance":0.0,"repair_all":True},
]

def repair_equipment(equipment_manager, character, free=False):
    """Repair all equipped items using materials from inventory.
    Returns (success, message).
    free=True: 不另扣材料（材料由修復服務配方支付，如 R17/R18）。
    """
    repaired_count = 0
    for sid, eq in equipment_manager.slots.items():
        if eq and eq["item"]:
            mx = eq["item"].get("durability", 100)
            cur = eq["item"].get("current_durability", mx)
            if cur < mx:
                inv = character.get("inventory", [])
                cost_iron = 1 if "鐵礦" in inv or "鐵錠" in inv else 0
                if free or cost_iron:
                    if not free:
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

def craft_item(recipe_id, inventory, equipment=None, character=None):
    recipe = next((r for r in RECIPES if r["recipe_id"] == recipe_id), None)
    if not recipe:
        return False, None, "未知配方"
    for ing in recipe["ingredients"]:
        if inventory.count(ing["item"]) < ing["quantity"]:
            return False, None, "缺少材料: %s x%d" % (ing["item"], ing["quantity"])
    # 軸譜檢查：魔法類配方（魔力藥水/靈力藥/法杖/護身符/魔法裝備）需要能量或靈性親和力。
    if character is not None:
        from axis_system import check_craft_axis
        _ok_ax, _why_ax = check_craft_axis(character, recipe)
        if not _ok_ax:
            return False, None, _why_ax
    # 修復服務類配方（R17/R18）：前置檢查裝備管理器，避免白扣材料。
    # 修復不是產出物品——「修復服務」不在 ITEM_CATALOG，
    # 若照一般配方會把不存在的物品塞進物品欄。
    is_repair = bool(recipe.get("repair_all") or recipe.get("category") == "repair")
    if is_repair and (equipment is None or character is None):
        return False, None, "沒有裝備可修復（需要裝備管理器）"
    for ing in recipe["ingredients"]:
        for _ in range(ing["quantity"]):
            inventory.remove(ing["item"])
    if _random.random() < recipe["failure_chance"]:
        # Return some materials on fail
        for ing in recipe["ingredients"]:
            inventory.append(ing["item"])
        return False, None, "合成失敗（材料已歸還）"
    if is_repair:
        # 修復配方已支付材料，修復時不另扣（free=True）
        suc, msg = repair_equipment(equipment, character, free=True)
        if not suc:
            # 無物可修：退還材料
            for ing in recipe["ingredients"]:
                for _ in range(ing["quantity"]):
                    inventory.append(ing["item"])
        return suc, None, msg
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
    "聖十字校園":   ["哥布林","盜賊","野狼"],
    "鏡湖":         ["晶石蜘蛛","暗影靈","蛇妖"],
    "鬱鬱山":       ["巨熊","野狼","哥布林"],
    "卡洛夫角":     ["盜賊","廢鐵傀儡","蛇妖"],
    "霧海群島":     ["蛇妖","古代守衛","幽靈"],
    "秘密鐵工廠":   ["廢鐵傀儡","哥布林"],
    "便利店":       ["盜賊","哥布林"],
    "英靈殿":       ["古代守衛","幽靈","元素核心"],
    "廢棄礦坑":     ["巨熊","晶石蜘蛛","廢鐵傀儡"],
    "森林深處":     ["巨熊","野狼","蛇妖","元素核心"],
    "煙雲溫泉湖":   ["暗影靈","晶石蜘蛛"],
    "清溪河":       ["野狼","蛇妖"],
    "鏡山":         ["石像鬼","幽靈","古代守衛"],
}

def get_enemy(location: str, level: int = 1) -> Optional[dict]:
    """依地點取得敵人。level 越高越可能遭遇強敵；低等級角色不會遇到遠古/兇暴級。"""
    names = LOCATION_ENEMIES.get(location, [])
    if not names:
        return None
    # 依角色等級過濾過強敵人（遠古/凶暴/兇暴/暗影/深淵系，含繁簡體）
    strong_kw = ("遠古", "凶暴", "兇暴", "暗影", "深淵", "傳說")
    pool = names
    if level < 3:
        pool = [n for n in names if not any(k in n for k in strong_kw)]
    elif level < 5:
        pool = [n for n in names if not any(k in n for k in strong_kw)]
        if pool and _random.random() < 0.2 * (level - 2):
            strong = [n for n in names if any(k in n for k in strong_kw)]
            if strong:
                pool = strong
    if not pool:
        pool = names
    name = _random.choice(pool)
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
# WORLD MAP (14 locations — rebuilt from scene cards)
# ═══════════════════════════════════════════════════════════

WORLD_MAP = {
    "聖十字校園": {"north":"鏡湖", "east":"鬱鬱山", "south":"清溪河", "west":"便利店"},
    "鏡湖":       {"south":"聖十字校園", "east":"鏡山"},
    "鬱鬱山":     {"west":"聖十字校園", "north":"煙雲溫泉湖", "east":"卡洛夫角"},
    "卡洛夫角":   {"west":"鬱鬱山", "east":"霧海群島"},
    "霧海群島":   {"west":"卡洛夫角"},
    "秘密鐵工廠": {"east":"聖十字校園"},
    "便利店":     {"east":"聖十字校園"},
    "英靈殿":     {"east":"聖十字校園", "north":"鏡山"},
    "廢棄礦坑":   {"enter":"清溪河"},
    "森林深處":   {"east":"便利店"},
    "煙雲溫泉湖": {"south":"鬱鬱山"},
    "清溪河":     {"north":"聖十字校園"},
    "鏡山":       {"south":"英靈殿", "west":"鏡湖"},
    "農學院":     {"enter":"聖十字校園"},
    "魔女學府":   {"enter":"聖十字校園", "east":"鬱鬱山"},
    "極北冰原":   {"south":"卡洛夫角", "west":"霧海群島"},
    "鏽蝕城邦":   {"enter":"廢棄礦坑"},
    "中央大圖書館":{"west":"聖十字校園"},
    "西翼大市集":{"enter":"卡洛夫角"},
}

LOCATION_VIBES = {
    "聖十字校園": "🏛 莊嚴的學術殿堂，迴廊與鐘樓交錯",
    "鏡湖":       "💧 湖面如鏡，倒映著天空與山巒",
    "鬱鬱山":     "⛰ 蒼翠山林，小徑蜿蜒其間",
    "卡洛夫角":   "⚓ 海風吹拂的港灣，船隻往來",
    "霧海群島":   "🏝 迷霧中的群島，神秘莫測",
    "秘密鐵工廠": "🔧 鐵鎚聲不斷，火花四濺的工坊",
    "便利店":     "🏪 明亮整潔的小店，應有盡有",
    "英靈殿":     "🏛 古老的殿堂，牆上刻滿史詩",
    "廢棄礦坑":   "⛏ 幽暗深邃的礦坑，深處傳來回聲",
    "森林深處":   "🌲 密林遮天，只有獸徑可循",
    "煙雲溫泉湖": "♨ 煙霧裊繞的溫泉，水氣氤氳",
    "清溪河":     "🏞 清澈的溪流，河床鋪滿卵石",
    "鏡山":       "🗻 山峰倒映在鏡湖中，如幻似真",
    "農學院":       "🌾 翠綠的農田與實驗溫室，作物娘們忙碌著",
    "魔女學府":     "🔮 塔樓林立，靈子光芒在建築間流轉",
    "極北冰原":     "🧊 永凍的雪原，寒風呼嘯",
    "鏽蝕城邦":     "🏰 廢鐵堆砌的城市，蒸汽與灰塵瀰漫",
    "中央大圖書館": "📚 宏偉的圖書館，書架延伸到視線盡頭",
    "西翼大市集": "🏪 熱鬧的地下市集，稀有商品與情報的流通中心",
}

# ═══════════════════════════════════════════════════════════
# SCENE TYPES & ENTRY REQUIREMENTS (per MAP_AND_SCENES.md)
# ═══════════════════════════════════════════════════════════

LOCATION_TYPES = {
    "聖十字校園":   "indoor",
    "鏡湖":         "outdoor",
    "鬱鬱山":       "outdoor",
    "卡洛夫角":     "outdoor",
    "霧海群島":     "outdoor",
    "秘密鐵工廠":   "indoor",
    "便利店":       "indoor",
    "英靈殿":       "dungeon",
    "廢棄礦坑":     "dungeon",
    "森林深處":     "outdoor",
    "煙雲溫泉湖":   "outdoor",
    "清溪河":       "outdoor",
    "鏡山":         "outdoor",
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
    "卡洛夫角": {
        "type": "level",
        "min": 4,
        "fail_msg": "通往卡洛夫角的棧道已經損壞，需要足夠的經驗才能安全通過。（等級 4）",
    },
    # ════════════════════════════════════════════════════════════
    # 跨世界線門檻（依世界線文本：V3.4 靈子聚合度差異）
    # 迴廊樞紐本身不需門檻；W03 軌道站（低靈子太空學院）與
    # W04 灰燼紀元（不穩定靈子後末日）需足夠歷練才能踏入。
    "軌道居住站大學院": {
        "type": "level",
        "min": 6,
        "fail_msg": "通往 W03 軌道站 的傳送閘門需要足夠的歷練才能通過。（等級 6）",
    },
    "鏽蝕城邦": {
        "type": "level",
        "min": 6,
        "fail_msg": "W04 灰燼紀元的靈子不穩定，貿然踏入可能過載失控。（等級 6）",
    },
    "熒光沼澤": {
        "type": "level",
        "min": 6,
        "fail_msg": "W04 熒光沼澤的靈子濃度極不穩定，貿然踏入可能過載失控。（等級 6）",
    },
    "玻璃荒漠": {
        "type": "level",
        "min": 8,
        "fail_msg": "W04 玻璃荒漠核心是靈爆中心殘留，靈子濃度超過 100ppm，極度危險。（等級 8）",
    },
    "高密度大氣結晶行星": {
        "type": "level",
        "min": 6,
        "fail_msg": "夢境層需要足夠的意志力才能維持自我。（等級 6）",
    },
    "綻放混成園": {
        "type": "level",
        "min": 6,
        "fail_msg": "夢境層需要足夠的意志力才能維持自我。（等級 6）",
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
    "聖十字校園宿舍": {
        "type":"house", "price":500, "functions":["rest","store"],
        "desc":"樸素的村莊小屋", "location":"聖十字校園", "max_level":3,
        "upgrades":[
            {"level":2, "cost":300, "add_functions":["study"], "desc":"增建書房"},
            {"level":3, "cost":600, "add_functions":["guest"], "desc":"增設客房"},
        ],
    },
    "西翼商店鋪": {
        "type":"shop", "price":800, "functions":["trade"],
        "desc":"市集的小店鋪", "location":"西翼大市集", "max_level":3,
        "upgrades":[
            {"level":2, "cost":500, "add_functions":["rest"], "desc":"增設休息區"},
            {"level":3, "cost":1000, "add_functions":["craft"], "desc":"增設工坊區"},
        ],
    },
    "湖畔工坊": {
        "type":"workshop", "price":1200, "functions":["craft","rest"],
        "desc":"鏡湖旁的工坊", "location":"鏡湖", "max_level":3,
        "upgrades":[
            {"level":2, "cost":800, "add_functions":["study"], "desc":"增設研究區"},
            {"level":3, "cost":1500, "add_functions":["alchemy"], "desc":"增設煉金臺"},
        ],
    },
    "圖書館密室": {
        "type":"house", "price":2000, "functions":["rest","study"],
        "desc":"圖書館內的安靜房間", "location":"中央大圖書館", "max_level":2,
        "upgrades":[
            {"level":2, "cost":1200, "add_functions":["store"], "desc":"增設書架倉庫"},
        ],
    },
    "礦坑倉庫": {
        "type":"warehouse", "price":600, "functions":["store"],
        "desc":"廢棄礦坑旁的倉庫", "location":"廢棄礦坑", "max_level":2,
        "upgrades":[
            {"level":2, "cost":400, "add_functions":["rest"], "desc":"簡易改造為休息處"},
        ],
    },
    # ── New property types per MAP_AND_SCENES.md ──
    "森林農場": {
        "type":"farm", "price":1500, "functions":["farm","rest"],
        "desc":"森林深處的小農場", "location":"森林深處", "max_level":3,
        "upgrades":[
            {"level":2, "cost":800, "add_functions":["store"], "desc":"增設農具倉庫"},
            {"level":3, "cost":1600, "add_functions":["trade"], "desc":"增設農產直銷點"},
        ],
    },
    "鏡湖觀測塔": {
        "type":"tower", "price":2500, "functions":["study","observe"],
        "desc":"鏡湖旁的觀測塔", "location":"鏡湖", "max_level":3,
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

    # 軸譜檢查：儀式/靈性類機制（祭壇/英靈召喚台/石碑）需靈性連結、
    # 機械類（蒸氣閥門）需機械維度、能量類（爆破裝置）需能量維度。
    ax_req = reqs.get("axis", {}) or {}
    if ax_req:
        aff = character.get("axis", {}).get("affinity", {}) or {}
        missing = [
            (dim, thr) for dim, thr in ax_req.items()
            if aff.get(dim, 0.0) < thr
        ]
        if missing:
            # 每維度列出需求與目前數值（多維度如爆破裝置＝能量+機械）
            detail = "、".join(
                "%s(你 %.2f / 需 %.1f)" % (dim, aff.get(dim, 0.0), thr)
                for dim, thr in missing
            )
            return False, ("軸譜不足：%s。" % detail)

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
# ── Card deck character schedules ──
    "晞咕萊雅": [
        (6,10,  "整理圖書","中央大圖書館",  "calm"),
        (10,14, "編目文獻","中央大圖書館",  "focused"),
        (14,18, "值班",    "中央大圖書館",  "friendly"),
        (18,22, "閱讀",    "中央大圖書館",  "calm"),
        (22,6,  "睡眠",    "中央大圖書館",  "sleep"),
    ],
    "暈咔繆露": [
        (7,10,  "情感編目","中央大圖書館",  "focused"),
        (10,14, "歸檔",    "中央大圖書館",  "calm"),
        (14,18, "休息",    "鏡湖",          "rest"),
        (18,22, "閱讀小說","便利店",        "friendly"),
        (22,7,  "睡眠",    "中央大圖書館",  "sleep"),
    ],
    "冰喀啦": [
        (6,10,  "整理冰晶","鏡湖",          "calm"),
        (10,14, "巡視湖面","鏡湖",          "alert"),
        (14,18, "休息",    "秘密鐵工廠",    "rest"),
        (18,22, "交流",    "便利店",        "friendly"),
        (22,6,  "睡眠",    "鏡湖",          "sleep"),
    ],
    "小倉靜子": [
        (5,8,   "晨間訓練","聖十字校園",    "focused"),
        (8,12,  "防空訓練","卡洛夫角",      "alert"),
        (12,14, "午餐",    "便利店",        "rest"),
        (14,18, "保養裝備","秘密鐵工廠",    "focused"),
        (18,22, "巡邏",    "聖十字校園",    "alert"),
        (22,5,  "睡眠",    "聖十字校園",    "sleep"),
    ],
    "京島伊吹": [
        (7,10,  "上學",    "聖十字校園",    "focused"),
        (10,14, "學習",    "聖十字校園",    "focused"),
        (14,16, "快遞配送","卡洛夫角",      "friendly"),
        (16,18, "休息",    "便利店",        "rest"),
        (18,22, "社交",    "卡洛夫角",      "friendly"),
        (22,7,  "睡眠",    "聖十字校園",    "sleep"),
    ],
    "京島楓香": [
        (7,10,  "魔女課程","魔女學府",      "focused"),
        (10,14, "歸途術研究","魔女學府",    "focused"),
        (14,16, "休息",    "聖十字校園",    "rest"),
        (16,18, "練習",    "鏡湖",          "focused"),
        (18,22, "閱讀",    "中央大圖書館",  "calm"),
        (22,7,  "睡眠",    "聖十字校園",    "sleep"),
    ],
    "織織": [
        (6,10,  "像素調整","中央大圖書館",  "focused"),
        (10,14, "巡邏",    "聖十字校園",    "alert"),
        (14,18, "概念共鳴","煙雲溫泉湖",    "rest"),
        (18,22, "社交",    "便利店",        "friendly"),
        (22,6,  "睡眠",    "中央大圖書館",  "sleep"),
    ],
    "壞壞米亞": [
        (8,12,  "研究",    "中央大圖書館",  "focused"),
        (12,14, "午餐",    "便利店",        "friendly"),
        (14,18, "散步",    "鬱鬱山",        "calm"),
        (18,22, "夜間活動","卡洛夫角",      "friendly"),
        (22,8,  "休息",    "聖十字校園",    "sleep"),
    ],
}

# Season-based schedule variants for get_npc_activity
SEASON_SCHEDULE_VARIANTS = {
    "小狐丸": {
        "夏": [(6,10,"避暑","鏡湖","calm"),(10,14,"戲水","鏡湖","friendly"),
               (14,18,"午睡","鏡湖","rest"),(18,22,"夜遊","鏡湖","friendly"),(22,6,"睡眠","鏡湖","sleep")],
        "冬": [(7,10,"晨練","鏡湖","calm"),(10,14,"曬太陽","鏡湖","rest"),
               (14,18,"取暖","秘密鐵工廠","rest"),(18,21,"喝茶","便利店","friendly"),(21,7,"睡眠","鏡湖","sleep")],
    },
    "左間小蒼蘭": {
        "夏": [(6,11,"夏季鍛造","秘密鐵工廠","focused"),(11,13,"午休","便利店","rest"),
               (13,18,"繼續工作","秘密鐵工廠","focused"),(18,21,"散步","西翼大市集","calm"),(21,6,"睡眠","秘密鐵工廠","sleep")],
        "冬": [(8,12,"打鐵","秘密鐵工廠","focused"),(12,13,"午餐","便利店","rest"),
               (13,17,"繼續工作","秘密鐵工廠","focused"),(17,20,"整理工具","秘密鐵工廠","calm"),(20,8,"睡眠","秘密鐵工廠","sleep")],
    },
    "紅": {
        "夏": [(6,9,"進貨","西翼大市集","calm"),(9,12,"整理貨架","便利店","calm"),
               (12,18,"值班","便利店","friendly"),(18,22,"晚班","便利店","friendly"),(22,6,"休息","便利店","sleep")],
        "冬": [(7,11,"整理貨架","便利店","calm"),(11,19,"值班","便利店","friendly"),
               (19,22,"晚班","便利店","friendly"),(22,7,"休息","便利店","sleep")],
    },
    "晞咕萊雅": {
        "夏": [(6,10,"避暑","中央大圖書館","calm"),(10,14,"閱讀","中央大圖書館","focused"),
               (14,18,"午休","中央大圖書館","rest"),(18,22,"夜讀","中央大圖書館","calm"),(22,6,"休眠","中央大圖書館","sleep")],
        "冬": [(7,10,"晨讀","中央大圖書館","calm"),(10,14,"編目","中央大圖書館","focused"),
               (14,18,"暖爐休息","中央大圖書館","rest"),(18,21,"熱茶時間","便利店","friendly"),(21,7,"休眠","中央大圖書館","sleep")],
    },
    "冰喀啦": {
        "夏": [(6,10,"避暑","鏡湖","calm"),(10,14,"戲水","鏡湖","friendly"),
               (14,18,"午睡","鏡湖","rest"),(18,22,"夜遊","鏡湖","friendly"),(22,6,"睡眠","鏡湖","sleep")],
        "冬": [(7,10,"晨練","鏡湖","calm"),(10,14,"曬太陽","鏡湖","rest"),
               (14,18,"取暖","秘密鐵工廠","rest"),(18,21,"喝茶","便利店","friendly"),(21,7,"睡眠","鏡湖","sleep")],
    },
    "織織": {
        "夏": [(6,10,"像素調整","水鏡通道","focused"),(10,14,"避暑","煙雲溫泉湖","rest"),
               (14,18,"午休","煙雲溫泉湖","rest"),(18,22,"夜間巡邏","聖十字校園","alert"),(22,6,"休眠","水鏡通道","sleep")],
        "冬": [(7,11,"像素工作","水鏡通道","focused"),(11,14,"暖爐邊","便利店","rest"),
               (14,18,"繼續工作","水鏡通道","focused"),(18,21,"社交","便利店","friendly"),(21,7,"休眠","水鏡通道","sleep")],
    },
}

def get_npc_activity(npc_name, hour, season=None):
    """Get NPC activity, optionally adjusted for season."""
    if season:
        variants = SEASON_SCHEDULE_VARIANTS.get(npc_name, {})
        var = variants.get(season)
        if var:
            for start,end,activity,location,mood in var:
                if start <= end:
                    if start <= hour < end:
                        return activity,location,mood
                else:
                    if hour >= start or hour < end:
                        return activity,location,mood
            return "休息","","neutral"
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
     "desc":"聖十字校園的地下層藏著古老的秘密。",
     "conditions":{"required_level":5,"required_quests":["MQ-02"],"time_available":{"start_hour":0,"end_hour":24}},
     "objectives":[{"type":"visit","target":"聖十字校園","detail":"探索聖十字校園地下層"},
                   {"type":"visit","target":"英靈殿","detail":"探索英靈殿"}],
     "reward_exp":180,"reward_gold":80,"reward_item":"記憶水晶","reward_reputation":20,
     "next_quest":"MQ-04"},
    {"id":"MQ-04","title":"世界的盡頭","type":"main","giver":"系統",
     "desc":"前往卡洛夫角，尋找通往世界盡頭的道路。",
     "conditions":{"required_level":7,"required_quests":["MQ-03"],"time_available":{"start_hour":0,"end_hour":24}},
     "objectives":[{"type":"visit","target":"霧海群島","detail":"穿過卡洛夫角，到達霧海群島"},
                   {"type":"defeat","target":"古代守衛","qty":1,"detail":"擊敗守衛世界盡頭的古代守衛"}],
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
    {"id":"SQ-03","title":"妖精的請求","type":"side","giver":"紅",
     "desc":"便利店需要魔法粉來補充貨架上的特殊商品。",
     "conditions":{"required_race":"獸娘","required_relationships":{"紅":15},"time_available":{"start_hour":8,"end_hour":20}},
     "objectives":[{"type":"collect","target":"魔法粉","qty":2,"detail":"收集2份魔法粉"}],
     "reward_exp":50,"reward_gold":25,"reward_item":"護身符","reward_reputation":10,
     "reward_relationships":{"紅":15}},
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
     "reward_exp":110,"reward_gold":55,"reward_item":"鐵盔","reward_reputation":15},
    {"id":"SQ-06","title":"貨物運送","type":"side","giver":"紅",
     "desc":"幫紅運送一批貨物到卡洛夫角。",
     "conditions":{"required_level":4,"required_relationships":{"紅":15},"time_available":{"start_hour":6,"end_hour":20}},
     "objectives":[{"type":"visit","target":"卡洛夫角","detail":"造訪卡洛夫角"}],
     "reward_exp":85,"reward_gold":50,"reward_item":"乾糧","reward_reputation":5,
     "reward_relationships":{"紅":10}},
    {"id":"SQ-07","title":"修理工具","type":"side","giver":"左間小蒼蘭",
     "desc":"左間小蒼蘭的工具壞了，需要鐵錠修理。",
     "conditions":{"required_relationships":{"左間小蒼蘭":15},"giver_activity":"focused","time_available":{"start_hour":7,"end_hour":21}},
     "objectives":[{"type":"collect","target":"鐵錠","qty":2,"detail":"收集2個鐵錠"}],
     "reward_exp":35,"reward_gold":15,"reward_item":"匕首","reward_reputation":8,
     "reward_relationships":{"左間小蒼蘭":12}},
    {"id":"SQ-08","title":"驅除暗影","type":"side","giver":"小狐丸",
     "desc":"鏡湖附近出現暗影靈，需要清除。",
     "conditions":{"required_quests":["SQ-02"],"required_relationships":{"小狐丸":30},"time_available":{"start_hour":18,"end_hour":6}},
     "objectives":[{"type":"defeat","target":"暗影靈","qty":2,"detail":"擊敗2隻暗影靈"}],
     "reward_exp":55,"reward_gold":25,"reward_item":"魔力藥水","reward_reputation":10,
     "reward_relationships":{"小狐丸":15}},
    {"id":"SQ-09","title":"收集材料","type":"side","giver":"系統",
     "desc":"收集各種材料以充實倉庫。",
     "conditions":{"required_level":2,"time_available":{"start_hour":0,"end_hour":24}},
     "objectives":[{"type":"collect","target":"木材","qty":3,"detail":"收集3份木材", "alt_item":"木柄"},
                   {"type":"collect","target":"皮革","qty":2,"detail":"收集2份皮革"}],
     "reward_exp":45,"reward_gold":20,"reward_item":"空瓶","reward_reputation":3},
    {"id":"SQ-10","title":"探索英靈殿","type":"side","giver":"系統",
     "desc":"英靈殿最近傳出奇怪的聲音。",
     "conditions":{"required_level":4,"time_available":{"start_hour":0,"end_hour":24}},
     "objectives":[{"type":"visit","target":"英靈殿","detail":"造訪英靈殿"}],
     "reward_exp":75,"reward_gold":35,"reward_item":"古老鑰匙","reward_reputation":10},

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
     "conditions":{"required_race":"龍族","required_level":3,"time_available":{"start_hour":0,"end_hour":24}},
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
    "聖十字校園": "腳踏車",
    "鏡湖":       "小舟",
    "秘密鐵工廠": "馬車",
}

# ═══════════════════════════════════════════════════════════
# VEHICLE SPECIAL ABILITIES
# ═══════════════════════════════════════════════════════════

VEHICLE_ABILITIES = {
    "腳踏車": {
        "衝刺": {
            "name":"🚴 衝刺",
            "desc":"消耗10SP，瞬間移動到相鄰場景（不消耗時間）",
            "cost_type":"sp",
            "cost":10,
            "cooldown":0,
            "require_riding":True,
        },
    },
    "馬": {
        "突襲": {
            "name":"🐴 突襲",
            "desc":"騎乘時遭遇戰鬥獲得先制攻擊（第一回合敵人無法反擊）",
            "cost_type":"none",
            "cost":0,
            "cooldown":0,
            "require_riding":True,
            "passive":True,
        },
    },
    "馬車": {
        "貿易": {
            "name":"📦 貿易",
            "desc":"在不同城鎮間買賣貨物賺取差價（消耗30SP）",
            "cost_type":"sp",
            "cost":30,
            "cooldown":3,
            "require_riding":True,
        },
    },
    "小舟": {
        "釣魚": {
            "name":"🎣 釣魚",
            "desc":"在湖/海場景釣魚，獲得物品（消耗15SP）",
            "cost_type":"sp",
            "cost":15,
            "cooldown":1,
            "require_riding":False,
            "water_only":True,
        },
        "渡水": {
            "name":"🌊 渡水",
            "desc":"騎乘小舟時可通過水域路線，發現隱藏的水域場景",
            "cost_type":"fuel",
            "cost":10,
            "cooldown":0,
            "require_riding":True,
            "passive":True,
        },
    },
}

WATER_LOCATIONS = {
    "水上集市": {
        "desc":"漂浮在水上的神秘市集，只有駕船才能到達",
        "vibe":"🎪 熱鬧的水上市集，船隻往來穿梭",
        "type":"outdoor",
    },
    "湖心島": {
        "desc":"鏡湖中央的小島，據說有遠古遺跡",
        "vibe":"🏝 被湖水環繞的寧靜小島",
        "type":"outdoor",
    },
}


def get_vehicle_abilities(vehicle_name):
    """Get all abilities for a vehicle."""
    return VEHICLE_ABILITIES.get(vehicle_name, {})


def get_active_abilities(vehicle_name, character, location=""):
    """Get currently usable abilities based on context."""
    abilities = VEHICLE_ABILITIES.get(vehicle_name, {})
    active = []
    riding = character.get("riding") == vehicle_name if vehicle_name else False

    for key, ab in abilities.items():
        if ab.get("passive"):
            continue
        if ab.get("require_riding") and not riding:
            continue
        if ab.get("water_only"):
            is_water = any(w in location for w in ["湖","海","水","川","河"])
            if not is_water:
                continue
        cooldown_key = "ability_cd_" + key
        vs = character.get("vehicle_state", {}).get(vehicle_name, {})
        if vs.get(cooldown_key, 0) > 0:
            continue
        cost_type = ab.get("cost_type", "none")
        cost = ab.get("cost", 0)
        if cost_type == "sp" and character.get("sp", 0) < cost:
            continue
        if cost_type == "fuel":
            veh_state = character.get("vehicles", {}).get(vehicle_name, {})
            _veh_fuel = veh_state.get("fuel", 0)
            # 非數字燃料（生成載具，無限）不視為不足
            if isinstance(_veh_fuel, (int, float)) and _veh_fuel < cost:
                continue
        active.append((key, ab))
    return active


def get_water_routes(current_location, character=None):
    """Get water routes available from current location (bidirectional).

    有移動能力的角色（飛行／艦娘艦裝航行／水棲游泳）不需小舟即可渡水：
    — 飛行：飛越水域，到湖心島／水上集市
    — 艦娘：艦裝即船，自行航行
    — 水棲：游泳渡水
    一般角色仍需小舟（渡水能力）。
    """
    WATER_ROUTES = {
        "鏡湖":   {"boat_deep":"湖心島"},
        "湖心島": {"boat_back":"鏡湖"},
        "卡洛夫角":   {"boat_market":"水上集市"},
        "水上集市": {"boat_back":"卡洛夫角"},
    }
    routes = WATER_ROUTES.get(current_location, {})
    if not routes:
        return {}
    # 無角色參數（相容舊呼叫）：回傳小舟路線
    if character is None:
        return routes
    # 判定移動能力（飛行／艦裝航行／游泳）
    try:
        from axis_system import movement_abilities
        mob = movement_abilities(
            text_race=str(character.get("race", "")),
            mechanic_race=str(character.get("mechanic_race", "")),
            lineage=(character.get("axis") or {}).get("lineage", ""),
        )
    except Exception:
        mob = {"fly": False, "sail": False, "swim": False}
    # 有移動能力：直接開通水域路線（不需小舟）
    if mob.get("fly") or mob.get("sail") or mob.get("swim"):
        return routes
    # 一般角色：需騎乘小舟（或擁有小舟）才可渡水
    riding = character.get("riding")
    vehicles = character.get("vehicles", {}) or {}
    has_boat = (riding == "小舟") or ("小舟" in vehicles and vehicles.get("小舟", {}).get("owned"))
    if not has_boat:
        return {}
    return routes


def do_fishing(character, location):
    """Execute fishing ability."""
    fish_tables = {
        "鏡湖": [("水晶碎片",0.3),("魚",0.5),("空瓶",0.3),("貝殼",0.4),("魔法粉",0.15),("古老硬幣",0.05)],
        "卡洛夫角": [("魚",0.6),("貝殼",0.5),("彩色玻璃片",0.2),("幸運幣",0.1),("龍鱗",0.02)],
    }
    table = fish_tables.get(location, [("魚",0.4),("空瓶",0.3),("貝殼",0.3)])
    roll = _random.random()
    cum = 0.0
    found = None
    for item, prob in table:
        cum += prob
        if roll < cum:
            found = item
            break
    if found:
        character["inventory"].append(found)
        return "🎣 釣到了 " + found + "！", [found]
    return "🎣 釣了一會兒，但什麼都沒釣到。", []


def do_trade(character, location):
    """Execute trade ability — buy/sell goods with location prices."""
    MARKET_PRICES = {
        "聖十字校園":   {"buy":1.0, "sell":0.6, "goods":["乾糧","草藥","空瓶"]},
        "秘密鐵工廠":   {"buy":1.2, "sell":0.5, "goods":["鐵礦","鐵錠","木柄","黏土"]},
        "鏡湖":         {"buy":1.1, "sell":0.5, "goods":["水晶碎片","魔法粉","魚"]},
        "卡洛夫角":     {"buy":0.9, "sell":0.6, "goods":["貝殼","彩色玻璃片","魚","幸運幣"]},
        "便利店":       {"buy":0.9, "sell":0.6, "goods":["乾糧","提神茶","繃帶"]},
        "森林深處":     {"buy":1.0, "sell":0.5, "goods":["草藥","靈木","木柄","羽毛"]},
    }
    market = MARKET_PRICES.get(location, {"buy":1.0, "sell":0.5, "goods":["乾糧"]})
    goods = market["goods"]
    inv = character.get("inventory", [])
    gold = character.get("gold", 0)
    lines = []
    lines.append("📊 " + location + " 市場行情：")
    lines.append("  買入倍率: x" + str(market["buy"]) + "  賣出倍率: x" + str(market["sell"]))
    lines.append("  熱門商品: " + ", ".join(goods))
    # Buy
    bought = []
    for g in goods:
        base_val = sum(v.get("value",10) for k,v in [("x",ITEM_CATALOG.get(g, {}))]) if False else ITEM_CATALOG.get(g, {}).get("value", 10)
        base_val2 = 10
        # Find base value
        for k,v in ITEM_CATALOG.items():
            if k == g:
                base_val2 = v.get("value", 10)
                break
        buy_price = int(base_val2 * market["buy"])
        if gold >= buy_price:
            total_w = sum(ITEM_CATALOG.get(i,{}).get("weight",0.5) for i in inv)
            item_w = ITEM_CATALOG.get(g,{}).get("weight",0.5)
            if total_w + item_w <= MAX_INVENTORY_WEIGHT and len(inv) < MAX_INVENTORY_SLOTS:
                inv.append(g)
                gold -= buy_price
                bought.append((g, buy_price))
    if bought:
        lines.append("  ✅ 購入: " + "; ".join(g + "(" + str(p) + "G)" for g,p in bought))
    else:
        lines.append("  ⚠ 沒有足夠金幣或空間進貨")
    # Sell
    sold = []
    to_remove = []
    for item in list(inv):
        idf = ITEM_CATALOG.get(item, {})
        if idf.get("type") in ("material","junk","consumable") and len(to_remove) < 5:
            sell_price = int(idf.get("value",5) * market["sell"])
            if sell_price > 0:
                to_remove.append(item)
                gold += sell_price
                sold.append((item, sell_price))
    for item in to_remove:
        inv.remove(item)
    if sold:
        lines.append("  💰 售出: " + "; ".join(g + "(+" + str(p) + "G)" for g,p in sold))
    character["gold"] = gold
    lines.append("  💳 剩餘金幣: " + str(gold) + "G")
    profit = sum(p for _,p in sold) - sum(p for _,p in bought)
    if profit > 0:
        lines.append("  📈 本次貿易淨利: +" + str(profit) + "G")
    elif profit < 0:
        lines.append("  📉 本次貿易淨利: " + str(profit) + "G")
    return "\n".join(lines), len(bought) > 0 or len(sold) > 0



# ═══════════════════════════════════════════════════════════
# VEHICLE PARTS (per ITEM_EQUIPMENT_SYSTEM.md §載具系統)
# ═══════════════════════════════════════════════════════════

VEHICLE_PART_SLOTS = {
    "腳踏車": [("engine","引擎"),("cargo","貨架")],
    "馬":     [("engine","馬具"),("armor","馬甲"),("weapon","馬鞍")],
    "馬車":   [("engine","挽具"),("armor","裝甲"),("cargo","貨箱"),("weapon","武裝")],
    "小舟":   [("engine","船槳/帆"),("cargo","船艙"),("armor","船殼")],
}

VEHICLE_PART_CATALOG = {
    # ── Engines (速度/燃料影響) ──
    "輕量化齒輪":{
        "slot":"engine","desc":"輕量化齒輪，提升速度和燃料效率",
        "stat_multipliers":{"speed":0.3,"fuel_efficiency":0.2},
        "durability":80,"value":200,"level":1,
    },
    "強化引擎":{
        "slot":"engine","desc":"強化引擎，大幅提升速度但油耗增加",
        "stat_multipliers":{"speed":0.6,"fuel_efficiency":-0.15},
        "durability":120,"value":350,"level":2,
    },
    "節能動力":{
        "slot":"engine","desc":"節能動力系統，提升燃料效率",
        "stat_multipliers":{"speed":0.1,"fuel_efficiency":0.4},
        "durability":60,"value":280,"level":2,
    },
    "魔法推進器":{
        "slot":"engine","desc":"魔法驅動的推進器，速度大幅提升",
        "stat_multipliers":{"speed":0.8,"fuel_efficiency":-0.3},
        "durability":90,"value":500,"level":3,
    },
    # ── Armor (防禦/耐久影響) ──
    "輕型裝甲":{
        "slot":"armor","desc":"輕型裝甲板，基本防護不影響速度",
        "stat_multipliers":{"armor":0.3,"speed":-0.05},
        "durability":100,"value":180,"level":1,
    },
    "重型裝甲":{
        "slot":"armor","desc":"重型裝甲，大幅提升防護但降低速度",
        "stat_multipliers":{"armor":0.7,"speed":-0.2},
        "durability":200,"value":320,"level":2,
    },
    "魔法護盾":{
        "slot":"armor","desc":"魔法護盾產生器，平衡防護與速度",
        "stat_multipliers":{"armor":0.5,"speed":-0.05},
        "durability":80,"value":450,"level":3,
    },
    # ── Cargo (貨物容量) ──
    "加大貨箱":{
        "slot":"cargo","desc":"加大貨箱，提升載貨量",
        "stat_multipliers":{"cargo":0.5,"speed":-0.05},
        "durability":60,"value":150,"level":1,
    },
    "輕量貨箱":{
        "slot":"cargo","desc":"輕量化貨箱，不影響速度",
        "stat_multipliers":{"cargo":0.3,"speed":0.0},
        "durability":40,"value":200,"level":2,
    },
    "擴展貨艙":{
        "slot":"cargo","desc":"擴展貨艙，大幅增加容量",
        "stat_multipliers":{"cargo":0.8,"speed":-0.1},
        "durability":80,"value":300,"level":2,
    },
    # ── Weapons (戰鬥能力) ──
    "衝角":{
        "slot":"weapon","desc":"裝備衝角，可在騎乘時衝撞敵人",
        "stat_multipliers":{"atk":0.4,"speed":-0.05},
        "durability":100,"value":250,"level":1,
    },
    "騎乘弩":{
        "slot":"weapon","desc":"騎乘用弩，遠程攻擊能力",
        "stat_multipliers":{"atk":0.6,"speed":-0.1},
        "durability":70,"value":380,"level":2,
    },
    "魔法砲":{
        "slot":"weapon","desc":"小型魔法砲，強大攻擊力但沉重",
        "stat_multipliers":{"atk":1.0,"speed":-0.2},
        "durability":60,"value":600,"level":3,
    },
}

# Default no-part bonuses

def get_vehicle_part_bonuses(equipped_parts):
    """Calculate total stat bonuses from all equipped vehicle parts.
    equipped_parts: {slot_name: {part_data}} or {slot_name: None}
    Returns: {stat_name: total_bonus}
    """
    bonuses = {}
    for slot, part in equipped_parts.items():
        if not part:
            continue
        multipliers = part.get("stat_multipliers", {})
        for stat, mult in multipliers.items():
            bonuses[stat] = bonuses.get(stat, 0.0) + mult
    return bonuses


def apply_vehicle_part_bonuses(vehicle_def, equipped_parts):
    """Apply part bonuses to a copy of vehicle definition and return modified copy."""
    v = dict(vehicle_def)
    bonuses = get_vehicle_part_bonuses(equipped_parts)
    # Apply speed modifier
    if "speed" in bonuses:
        v["speed"] = max(0.3, v["speed"] * (1.0 + bonuses["speed"]))
    # Apply cargo modifier
    if "cargo" in bonuses:
        v["cargo"] = max(5, int(v["cargo"] * (1.0 + bonuses["cargo"])))
    # Apply fuel efficiency (reduces fuel_per_hour)
    if "fuel_efficiency" in bonuses:
        eff = 1.0 - bonuses["fuel_efficiency"]
        v["fuel_per_hour"] = max(0, int(v.get("fuel_per_hour", 2) * eff))
    # Apply armor (separate stat, used in combat)
    if "armor" in bonuses:
        v["armor_bonus"] = bonuses["armor"]
    # Apply attack
    if "atk" in bonuses:
        v["atk_bonus"] = bonuses["atk"]
    return v


def equip_vehicle_part(vehicle_name, part_name, character):
    """Equip a part to a vehicle. Returns (success, message).
    part_name is key into VEHICLE_PART_CATALOG.
    """
    veh_state = character.get("vehicles", {}).get(vehicle_name)
    if not veh_state or not veh_state.get("owned"):
        return False, "你沒有這個載具"
    part_def = VEHICLE_PART_CATALOG.get(part_name)
    if not part_def:
        return False, "未知部件"
    # Check level requirement
    req_level = part_def.get("level", 1)
    char_level = character.get("level", 1)
    if char_level < req_level:
        return False, "需要等級 %d 才能裝備 %s（目前: %d）" % (req_level, part_name, char_level)
    slots = VEHICLE_PART_SLOTS.get(vehicle_name, [])
    slot_id = part_def.get("slot", "")
    # Check if this vehicle has this slot
    if slot_id not in [s[0] for s in slots]:
        return False, "這個載具沒有 %s 槽位" % slot_id
    # Check if part is already in inventory
    inv = character.get("inventory", [])
    if part_name not in inv:
        return False, "物品欄中沒有這個部件"
    # Ensure vehicle has parts dict
    if "parts" not in veh_state:
        veh_state["parts"] = {}
    # Unequip old part in same slot if exists
    old_part = veh_state["parts"].get(slot_id)
    if old_part:
        inv.append(old_part)
    # Equip new part
    inv.remove(part_name)
    veh_state["parts"][slot_id] = part_name
    # Set current durability
    if "parts_durability" not in veh_state:
        veh_state["parts_durability"] = {}
    veh_state["parts_durability"][slot_id] = part_def.get("durability", 100)
    return True, "已裝備 %s → %s 的 %s槽位" % (part_name, vehicle_name, slot_id)


def unequip_vehicle_part(vehicle_name, slot_id, character):
    """Unequip a part from a vehicle slot. Returns (success, message)."""
    veh_state = character.get("vehicles", {}).get(vehicle_name)
    if not veh_state or not veh_state.get("owned"):
        return False, "你沒有這個載具"
    parts = veh_state.get("parts", {})
    if slot_id not in parts:
        return False, "該槽位沒有部件"
    part_name = parts.pop(slot_id)
    # Remove durability tracking
    veh_state.get("parts_durability", {}).pop(slot_id, None)
    # Return to inventory
    character["inventory"].append(part_name)
    return True, "已卸下 %s" % part_name


def get_vehicle_part_status(vehicle_name, character):
    """Get readable status of all parts on a vehicle."""
    veh_state = character.get("vehicles", {}).get(vehicle_name, {})
    parts = veh_state.get("parts", {})
    durabilities = veh_state.get("parts_durability", {})
    slots = VEHICLE_PART_SLOTS.get(vehicle_name, [])
    lines = []
    for slot_id, slot_name in slots:
        part_name = parts.get(slot_id)
        if part_name:
            dur = durabilities.get(slot_id, 100)
            pd = VEHICLE_PART_CATALOG.get(part_name, {})
            dur_pct = dur / max(pd.get("durability", 100), 1) * 100
            dur_color = "完好" if dur_pct > 80 else "輕度" if dur_pct > 50 else "中度" if dur_pct > 20 else "嚴重"
            lines.append("  %s [%s]: %s (耐久:%d%% %s)" % (slot_name, slot_id, part_name, dur_pct, dur_color))
        else:
            lines.append("  %s [%s]: (空)" % (slot_name, slot_id))
    return "\n".join(lines) if lines else "  此載具沒有可裝備的部件槽位。"



# ═══════════════════════════════════════════════════════════
# SCENE OBJECTS (20 objects across locations)
# ═══════════════════════════════════════════════════════════

SCENE_OBJECTS = {
    "聖十字校園": [
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
        {"id":"boat",    "name":"小舟",      "type":"vehicle","desc":"停靠在湖邊的小船","vehicle_type":"小舟","interactable":True},
        {"id":"shrine",  "name":"湖底祭壇",  "type":"mechanism","mechanism_type":"pedestal","desc":"湖中央的古老祭壇，似乎需要某種祭品",
         "state":False,"trigger_once":True,"triggered":False,
         "requirements":{"item":"水晶碎片","consume":True,"qty":3,"axis":{"靈性":0.3}},
         "effect":{"type":"reveal","items":["記憶水晶","古老鑰匙"],
                   "message":"祭壇發出耀眼的光芒！從水中浮現出了寶物！"},
         "requirements_msg":"需要在水晶祭壇上放置3枚水晶碎片（靈性連結）。",
         "failure_msg":"祭壇沒有反應...需要更多的水晶碎片與靈性連結。"},
    ],
    "卡洛夫角": [
        {"id":"lighthouse","name":"燈塔開關","type":"mechanism","mechanism_type":"lever","desc":"海峽燈塔的控制桿",
         "state":False,"trigger_once":False,"triggered":False,
         "effect":{"type":"route_open","target":"卡洛夫角","value":"east",
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
         "requirements":{"axis":{"機械":0.3}},
         "effect":{"type":"reveal","items":["龍鱗","火元素","鐵錠"],
                   "message":"閥門完全打開！蒸氣散去，露出了隱藏的儲藏室！"},
         "progress_msg":"閥門轉動了 %d/3 圈。",
         "fail_msg":"閥門紋絲不動...需要機械維度的理解。",
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
         "requirements":{"item":"古老鑰匙","level":5,"consume":False,"axis":{"靈性":0.5}},
         "effect":{"type":"summon","enemy":"古代守衛","count":1,
                   "message":"基座發出耀眼的光芒！一位古代英靈降臨了！"},
         "requirements_msg":"需要古老的鑰匙、高超的實力與靈性連結才能啟動。（Lv.5+）",
         "failure_msg":"基座毫無反應...缺乏靈性連結。"},
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
         "effect":{"type":"teleport","target":"聖十字校園",
                   "message":"你拉下了控制桿！礦車順著軌道疾馳而去..."},
         "on_repeat":"轉轍器已經被扳動過了。"},
        {"id":"explosive","name":"爆破裝置",  "type":"mechanism","mechanism_type":"pedestal","desc":"礦坑深處的爆破裝置",
         "state":False,"trigger_once":True,"triggered":False,
         "requirements":{"item":"火元素","consume":True,"qty":2,"axis":{"能量":0.4,"機械":0.3}},
         "effect":{"type":"route_open","target":"廢棄礦坑","value":"deep",
                   "message":"轟！！爆炸聲在礦坑中迴盪，通往更深處的通道被打開了！"},
         "requirements_msg":"需要2枚火元素與能量引導來引爆。",
         "failure_msg":"缺少引爆物或能量引導..."},
    ],
    "森林深處": [
        {"id":"ancient_tree","name":"古樹",  "type":"container","desc":"參天的古老巨木","contents":["靈木","靈木","生命果"],"locked":False,"interactable":True},
        {"id":"camp",    "name":"廢棄營地",  "type":"container","desc":"冒險者留下的營地","contents":["乾糧","繃帶","木柄"],"locked":False,"interactable":True},
        {"id":"monolith","name":"古老石碑",  "type":"mechanism","mechanism_type":"pedestal","desc":"刻滿符文的神秘石碑",
         "state":False,"trigger_once":True,"triggered":False,
         "requirements":{"item":"生命果","consume":True,"qty":1,"axis":{"靈性":0.3}},
         "effect":{"type":"heal","hp":999,"sp":999,
                   "message":"石碑上的符文亮起！森林的力量湧入你的體內！"},
         "requirements_msg":"需要獻上1枚生命果並以靈性連結石碑。",
         "failure_msg":"石碑沒有反應...缺乏靈性連結。"},
    ],
}


# ═══════════════════════════════════════════════════════════
# WEATHER SYSTEM
# ═══════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════
# SEASONS (per SIMULATION_SYSTEMS.md)
# ═══════════════════════════════════════════════════════════

SEASONS = ["春", "夏", "秋", "冬"]
SEASON_ICONS = {"春":"🌸","夏":"☀️","秋":"🍂","冬":"❄️"}
SEASON_NAMES = {"春":"Spring·春","夏":"Summer·夏","秋":"Autumn·秋","冬":"Winter·冬"}

# Per-season weather probability modifiers (additive base, then normalized)
SEASON_WEATHER_MODIFIERS = {
    "春": {"☀晴":-0.05,"🌧雨":+0.10,"🌫霧":+0.05,"🌩雷雨":+0.03,"❄雪":-0.02},
    "夏": {"☀晴":+0.10,"🌧雨":-0.05,"🌫霧":-0.03,"🌩雷雨":+0.08,"❄雪":-0.03},
    "秋": {"☀晴":+0.00,"🌧雨":+0.00,"🌫霧":+0.05,"🌩雷雨":-0.02,"❄雪":+0.02},
    "冬": {"☀晴":-0.08,"🌧雨":-0.03,"🌫霧":+0.08,"🌩雷雨":-0.05,"❄雪":+0.15},
}

# Per-season farming yield multipliers
SEASON_FARMING = {
    "春": {"草藥":1.5, "乾糧":1.0, "靈木":1.2, "生命果":1.0},
    "夏": {"草藥":1.2, "乾糧":1.5, "靈木":1.0, "生命果":0.8},
    "秋": {"草藥":1.0, "乾糧":1.2, "靈木":1.5, "生命果":1.2},
    "冬": {"草藥":0.6, "乾糧":0.8, "靈木":1.2, "生命果":0.5},
}

SEASON_CYCLE = 120  # Full cycle days
SEASON_THRESHOLDS = {"春":0,"夏":30,"秋":60,"冬":90}


def get_season(day):
    """Get current season based on day number."""
    cycle_day = day % SEASON_CYCLE
    if cycle_day < 30: return "春"
    if cycle_day < 60: return "夏"
    if cycle_day < 90: return "秋"
    return "冬"


def get_season_crop_bonus(season, crop):
    """Get yield multiplier for a crop in a given season."""
    return SEASON_FARMING.get(season, {}).get(crop, 1.0)


def get_season_weather_desc(weather, season):
    """Get season-specific weather description."""
    wdata = WEATHER_EFFECTS.get(weather, {})
    sdesc = wdata.get("season_desc", {}).get(season, "")
    return sdesc or wdata.get("desc", "")


WEATHER_TYPES = ["☀晴","⛅多雲","🌧雨","🌫霧","🌩雷雨","❄雪"]

def roll_weather(season=None):
    """Roll weather with optional season modifiers."""
    r = _random.random()
    mods = SEASON_WEATHER_MODIFIERS.get(season, {}) if season else {}
    # Build probability table
    probs = [
        ("☀晴", 0.40 + mods.get("☀晴", 0.0)),
        ("⛅多雲", 0.25 + mods.get("⛅多雲", 0.0)),
        ("🌧雨",  0.15 + mods.get("🌧雨", 0.0)),
        ("🌫霧",  0.10 + mods.get("🌫霧", 0.0)),
        ("🌩雷雨", 0.07 + mods.get("🌩雷雨", 0.0)),
        ("❄雪",   0.03 + mods.get("❄雪", 0.0)),
    ]
    # Normalize to ensure total = 1.0
    total = sum(p for _, p in probs)
    cum = 0.0
    for wtype, prob in probs:
        cum += prob / total
        if r < cum:
            return wtype
    return "☀晴"

WEATHER_EFFECTS = {
    "☀晴":   {"encounter":0.35, "loot_bonus":0,   "rest_bonus":1.0, "desc":"視野良好",
               "season_desc":{"春":"春光明媚，百花盛開","夏":"炎炎烈日，蟬聲陣陣","秋":"秋高氣爽，天高雲淡","冬":"晴空萬里，寒風凜冽"}},
    "⛅多雲": {"encounter":0.40, "loot_bonus":0,   "rest_bonus":0.9, "desc":"天色陰沉",
               "season_desc":{"春":"春雲淡淡","夏":"厚重的雲層","秋":"秋雲舒捲","冬":"陰雲密布"}},
    "🌧雨":  {"encounter":0.30, "loot_bonus":0.1, "rest_bonus":1.1, "desc":"雨聲掩蓋了腳步",
               "season_desc":{"春":"春雨綿綿，滋潤大地","夏":"午後雷陣雨","秋":"秋雨蕭瑟","冬":"冷雨刺骨"}},
    "🌫霧":  {"encounter":0.50, "loot_bonus":0.2, "rest_bonus":0.8, "desc":"視線受阻",
               "season_desc":{"春":"春霧迷濛，如詩如畫","夏":"蒸騰的熱霧","秋":"晨霧濃重","冬":"寒霧籠罩"}},
    "🌩雷雨":{"encounter":0.20, "loot_bonus":0.3, "rest_bonus":1.2, "desc":"雷聲轟鳴",
               "season_desc":{"春":"春雷乍響","夏":"狂風暴雨，閃電交加","秋":"秋雷悶響","冬":"冬雷震震（罕見）"}},
    "❄雪":  {"encounter":0.25, "loot_bonus":0.15,"rest_bonus":0.7, "desc":"積雪難行",
               "season_desc":{"春":"春雪消融，泥濘難行","夏":"—","秋":"初雪降臨","冬":"大雪紛飛，銀裝素裹"}},
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
# 註：required_tokens 欄位為舊 token 設計的殘留——目前無任何運行時代碼消費
#（裝備/任務已改由軸譜五維度親和力判定；此欄僅保留以相容 docs/02-game-design/
# CHARACTER_SYSTEM.md 之記載，屬文檔相容資料，勿再依賴。

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
    "龍族": {
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
    "精靈": {
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
    "draconic": "龍族",
    "mechanism": "機械",
    "element": "術士",
    "spiritual": "精靈",
}

# =============================================================================
# ANGELA-MATRIX: [L3] [β] [A] [L5]
# 物種分類架構（三軸系統）— 文本《物種分類架構（三軸系統）.txt》／卡片 WC-10
# 四套平行三軸分類軸系：獸娘/魔物娘（N-C-P）、AI（F-A-O）、義體人（C-H-B）、
# 神話種（D-O-M）。分類系譜為物種分類的文本權威來源。
# =============================================================================
SPECIES_LINEAGES = {
    "獸娘": {
        "system": "物種分類三軸系統",
        "axes": {
            "原種距離": {"N": "近原種", "S": "標準種", "F": "遠原種"},
            "人形比例": {"H": "類人型", "S": "標準型", "C": "類原型"},
            "混血譜系": {"P": "純血", "M1": "混血一級", "M2": "混血二級", "M3": "混血三級"},
        },
    },
    "AI": {
        "system": "F-A-O 三軸",
        "axes": {
            "人形模仿度": {"F0": "無形體", "F1": "抽象載體", "F2": "部分人形", "F3": "仿真人形"},
            "自主性": {"A0": "被動型", "A1": "條件型", "A2": "學習型", "A3": "完全自主"},
            "程序開放度": {"O0": "封閉黑箱", "O1": "部分開源", "O2": "完全開源"},
        },
    },
    "義體人": {
        "system": "C-H-B 三軸",
        "axes": {
            "義體化比例": {"C1": "輕度（<30%）", "C2": "中度（30%-70%）", "C3": "重度（70%-95%）", "C4": "全身義體（>95%）"},
            "外觀人形保留度": {"H1": "完全人形", "H2": "部分暴露", "H3": "非人形態"},
            "神經保留度": {"B1": "生物腦完整", "B2": "生物腦增強", "B3": "意識上傳"},
        },
    },
    "神話種": {
        "system": "D-O-M 三軸",
        "axes": {
            "神性濃度": {"D1": "傳說級", "D2": "信仰級", "D3": "原初級"},
            "原典忠實度": {"O1": "自由改編", "O2": "部分保留", "O3": "高度還原"},
            "存在維度": {"M1": "物質顯形", "M2": "靈體/概念", "M3": "跨維度"},
        },
    },
}

# 分類系譜 → 機制種族（RACE_DATA 層級）對應。分類系譜是物種分類的權威來源，
# 當角色卡具有分類系譜 token 時，優先以系譜決定機制種族，取代粗糙的 token 關鍵字偵測。
SPECIES_LINEAGE_TO_RACE = {
    "獸娘": "獸娘",
    "AI": "機械",
    "義體人": "機械",
    "神話種": "精靈",
}

# 機制種族例外：三軸分類與機制種族存在文本明示的轉化／例外。
# CC-03 星辰米亞：狐妖→艦娘（文本三軸文件備註「後轉艦娘」），機制種族維持艦娘。
# CC-34 萊姆：人類＋鬼族混血（三軸文件列 S-H-M1，屬混血譜系），無動物特徵，維持人類。
SPECIES_MECHANIC_EXCEPTIONS = {
    "CC-03": "艦娘",
    "CC-34": "人類",
    # CC-24 維爾：共振文明使者（八足晶體智慧生命），概念生命 → 精靈
    "CC-24": "精靈",
    # 龍娘卡（三軸分類 F-H-P 屬獸娘系譜，但機制種族為龍族——翼膜/龍角/龍尾、
    # TASK-03「翼膜保養」龍族任務）。CC-32 另有場所詞「魔女學府…術式」需覆蓋。
    "C15": "龍族",
    "CC-20": "龍族",
    "CC-32": "龍族",
}


def parse_species_classification(value):
    """解析分類系譜 token 值（如『獸娘｜ S-S-P（標準種、標準型、純血）』）。

    回傳 dict{lineage, code, axes}；無法解析時回傳 None。
    """
    if not value:
        return None
    v = str(value).strip()
    if "｜" in v:
        lineage, rest = v.split("｜", 1)
    elif "|" in v:
        lineage, rest = v.split("|", 1)
    else:
        return None
    lineage = lineage.strip()
    rest = rest.strip()
    code = rest.split("（")[0].strip() if "（" in rest else rest
    axes = ""
    if "（" in rest and "）" in rest:
        axes = rest.split("（", 1)[1].rsplit("）", 1)[0]
    return {"lineage": lineage, "code": code, "axes": axes}


# 文本種族 → 機制種族 關鍵字對應（來源：卡片 stats.race／源文本權威種族標記）
# 當卡片無分類系譜時，以文本種族為權威，取代舊的 token 關鍵字猜測。
# 順序重要：先匹配更特定種族（艦娘/AI/魔女/天翼種…），後匹配泛獸娘，最後才是人類。
_TEXT_RACE_RULES = [
    # 魔女先於人類：CC-29 京島楓香文本「人類（魔女學府畢業生，準大魔女）」→ 術士（魔法使用者）
    (["魔女", "術式適應體"], "術士"),
    (["人類"], "人類"),
    (["艦娘"], "艦娘"),
    # 人造精靈本質是靈體（人造僅為來源），歸精靈而非機械
    (["AI", "人造意識", "特戰人形", "義體", "賽博格", "基因強化人", "機械妖精", "機械", "人形機"], "機械"),
    # 概念怪獸／概念生物／怪獸是概念實體，不是獸娘——此規則必須在獸娘規則之前命中
    (["天翼種", "天使", "智天使", "神明", "邪神", "概念", "靈體", "神話", "世界意志", "欲墮魔", "惡意",
      "精靈", "人造精靈", "高階靈體", "怪獸"], "精靈"),
    # 龍娘：三軸分類屬獸娘系譜（F-H-P 遠原種範例），但機制種族為龍族——
    # 文本明示龍娘有龍族血脈/龍角/龍鱗/龍尾/翼膜，TASK-03「翼膜保養」required_race=龍族
    # （RACE_DATA 龍族 body_parts 含 wings/horns）。
    (["龍娘", "龍族", "龍人娘"], "龍族"),
    # 獸娘規則：明確「獸娘」優先，其餘為具體物種詞；不放泛「獸」——
    # 「怪獸／概念怪獸」含「獸」但屬概念實體（精靈），泛「獸」會誤判（CC-45/46 概念怪獸）
    (["獸娘", "狐", "貓", "兔", "狼", "蝙蝠", "拉米雅", "阿拉克涅",
      "哈比", "妖精", "魔物娘", "鼠", "納迦", "人魚", "海蛞蝓", "蛇", "兩棲"], "獸娘"),
]


def detect_race(token_list: list, species_lineage: str = None, card_id: str = None,
                text_race: str = "") -> str:
    """Detect character's race.

    優先序（文本權威）：
    1. 機制種族例外（SPECIES_MECHANIC_EXCEPTIONS，依卡片代碼）
    2. 分類系譜（三軸系統）→ 機制種族映射
    3. 文本種族關鍵字（卡片 stats.race 的明確種族詞，如『狐妖』『天翼種』『魔女』）
    4. 原始 token 類別關鍵字偵測
    5. 人類（預設）
    """
    # 例外：文本明示的轉化／例外（如 CC-03 狐妖→艦娘、CC-34 人類+鬼族混血）
    if card_id and card_id in SPECIES_MECHANIC_EXCEPTIONS:
        return SPECIES_MECHANIC_EXCEPTIONS[card_id]
    # 分類系譜為物種分類的文本權威，優先於 token 關鍵字偵測
    if species_lineage:
        race = SPECIES_LINEAGE_TO_RACE.get(species_lineage)
        # 龍娘：三軸分類屬獸娘系譜（F-H-P 遠原種範例），但機制種族為龍族——
        # 文本明示龍娘有龍族血脈/龍角/龍鱗/龍尾/翼膜，TASK-03「翼膜保養」required_race=龍族。
        # 此覆寫使系譜為獸娘但文本種族含龍娘的卡自動歸龍族（不需例外表逐卡登記）。
        if race == "獸娘" and "龍娘" in text_race:
            return "龍族"
        if race:
            return race
    # 文本種族關鍵字（卡片 stats.race）— 取代舊的純 token 猜測
    if text_race:
        for kws, race in _TEXT_RACE_RULES:
            for kw in kws:
                if kw in text_race:
                    return race
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
    # 機制種族（分類 bucket）才定義裝備槽；race 是文本種族（如「天空龍娘」），不直接進 RACE_DATA
    race = character.get("mechanic_race") or character.get("race", "人類")
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
            self.race = character.get("mechanic_race") or character.get("race", "人類")
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
    lines.append('    |  鏡湖   |  鏡山   |')
    lines.append('    +----+----+---------+')
    lines.append('    |聖校|  鬱鬱山  卡洛夫|')
    lines.append('    +----+----+----+----+')
    lines.append('    |清溪河  |  煙雲   |')
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
