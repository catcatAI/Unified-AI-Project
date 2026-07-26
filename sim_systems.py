from dataclasses import dataclass

@dataclass
class NPCRoutine:
    time_start: int = 0
    time_end: int = 23
    activity: str = ""
    location: str = ""
    mood: str = "neutral"

NPC_SCHEDULES = {
    "小狐丸": [
        (6, 10, "整理冰晶", "鏡湖火山口", "calm"),
        (10, 14, "巡視鏡湖", "鏡湖", "alert"),
        (14, 18, "休息", "鏡湖火山口", "rest"),
        (18, 22, "交流", "秘密鐵工廠", "friendly"),
        (22, 6, "睡眠", "鏡湖火山口", "sleep"),
    ],
    "左間小蒼蘭": [
        (7, 12, "在鐵工廠工作", "秘密鐵工廠", "focused"),
        (12, 13, "午餐休息", "秘密鐵工廠", "rest"),
        (13, 18, "繼續工作", "秘密鐵工廠", "focused"),
        (18, 21, "整理工具", "秘密鐵工廠", "calm"),
        (21, 7, "睡眠", "女僕長宿舍", "sleep"),
    ],
    "紅": [
        (6, 10, "整理貨架", "便利店", "calm"),
        (10, 18, "值班看店", "便利店", "friendly"),
        (18, 22, "晚班", "便利店", "friendly"),
        (22, 6, "睡眠", "便利店樓上", "sleep"),
    ],
}

def get_npc_activity(npc_name, hour):
    schedule = NPC_SCHEDULES.get(npc_name)
    if not schedule:
        return "休息", "", "neutral"
    for start, end, activity, location, mood in schedule:
        if start <= end:
            if start <= hour < end:
                return activity, location, mood
        else:
            if hour >= start or hour < end:
                return activity, location, mood
    return "休息", "", "neutral"

EQUIPMENT_SLOTS = [
    ("head", "頭部"), ("face", "面部"), ("neck", "頸部"),
    ("torso", "軀幹"), ("left_arm", "左臂"), ("right_arm", "右臂"),
    ("left_hand", "左手"), ("right_hand", "右手"),
    ("waist", "腰部"), ("legs", "腿部"), ("feet", "腳部"), ("back", "背部"),
]

class EquipmentManager:
    def __init__(self):
        self.slots = {s_id: None for s_id, _ in EQUIPMENT_SLOTS}

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
        for slot_id, eq in self.slots.items():
            if eq and eq["item"]:
                for stat, mult in eq["item"].get("stat_multipliers", {}).items():
                    bonuses[stat] = bonuses.get(stat, 0.0) + mult
        return bonuses

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
        ratio = cur / mx if mx > 0 else 1
        if ratio > 0.8: return "完好"
        if ratio > 0.6: return "輕微磨損"
        if ratio > 0.4: return "中度磨損"
        if ratio > 0.2: return "嚴重磨損"
        return "已損壞"

    def display(self):
        lines = ["裝備欄:"]
        for slot_id, name in EQUIPMENT_SLOTS:
            eq = self.slots.get(slot_id)
            if eq and eq["item"]:
                cond = self.condition_name(slot_id)
                lines.append("  %s: %s [%s]" % (slot_id, eq["item"].get("name", "?"), cond))
            else:
                lines.append("  %s: （空）" % slot_id)
        return "\n".join(lines)

RECIPES = [
    {"recipe_id": "R01", "name": "火焰藥水", "category": "alchemize",
     "ingredients": [{"item": "草藥", "quantity": 2}, {"item": "火元素", "quantity": 1}],
     "result_item": "火焰藥水", "result_quantity": 1, "failure_chance": 0.1},
    {"recipe_id": "R02", "name": "鐵劍", "category": "craft",
     "ingredients": [{"item": "鐵礦", "quantity": 3}, {"item": "木柄", "quantity": 1}],
     "result_item": "鐵劍", "result_quantity": 1, "failure_chance": 0.2},
    {"recipe_id": "R03", "name": "鐵錠", "category": "process",
     "ingredients": [{"item": "鐵礦", "quantity": 5}],
     "result_item": "鐵錠", "result_quantity": 2, "failure_chance": 0.0},
]

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
    if __import__("random").random() < recipe["failure_chance"]:
        return False, None, "合成失敗"
    result = recipe["result_item"]
    count = recipe["result_quantity"]
    for _ in range(count):
        inventory.append(result)
    return True, result, "合成成功: %s x%d" % (result, count)

WORLD_MAP = {
    "方碑丘": {"east": "西翼大市集", "south": "中央大圖書館", "north": "鏡湖"},
    "鏡湖": {"north": "方碑丘", "east": "海峽"},
    "西翼大市集": {"west": "方碑丘"},
    "中央大圖書館": {"north": "方碑丘"},
    "海峽": {"west": "鏡湖"},
}

REAL_ESTATE = {
    "方碑丘民居": {"type": "house", "price": 500, "functions": ["rest", "store"]},
    "西翼商鋪": {"type": "shop", "price": 800, "functions": ["trade", "store"]},
    "中央工坊": {"type": "workshop", "price": 1000, "functions": ["craft", "store"]},
}

HOUR_NAMES = {0: "子時", 6: "卯時", 8: "辰時", 12: "午時", 14: "未時", 18: "酉時", 22: "亥時"}

def get_time_desc(hour, day):
    period = "早晨" if 6 <= hour < 12 else "午後" if 12 <= hour < 18 else "夜晚"
    return "第%d天，%s（%s）" % (day, HOUR_NAMES.get(hour, "%d:00" % hour), period)

def display_world_map(current_location):
    lines = []
    lines.append('世界地図:')
    lines.append('')
    lines.append('    +--------+--------+')
    lines.append('    |  鏡湖  |        |')
    lines.append('    +--------+--------+')
    lines.append('    |        |        |')
    marker = '<-- 你' if current_location == '方碑丘' else '      '
    lines.append('    |方碑丘%s|西翼大市集|' % marker)
    lines.append('    |        |        |')
    lines.append('    +--------+--------+')
    lines.append('    |        |        |')
    lines.append('    |中央大圖|英靈殿   |')
    lines.append('    |書館    |・錬金術  |')
    lines.append('    +--------+--------+')
    lines.append('')
    lines.append('  現在位置: %s' % current_location)
    return chr(10).join(lines)
