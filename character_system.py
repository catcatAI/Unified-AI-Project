import json
import random as _random

CARD_DATA_PATH = "data/game_cards.json"

# =============================================================================
# ANSI color codes (INTERFACE_TERMINAL.md § 色彩)
# =============================================================================

class C:
    """ANSI color constants for terminal output."""
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


# =============================================================================
# Symbol portraits (CHARACTER_SYSTEM.md § 符號立繪)
# =============================================================================

SYMBOL_PORTRAITS = {
    "default": (
        "   ╔═╗  ╔═╗\n"
        "   ║█║  ║█║\n"
        "   ╚═╝  ╚═╝\n"
        "    ╔═╗ \n"
        "    ║█║ \n"
        "    ╚═╝ "
    ),
    "warrior": (
        "   ╔═╗  ╔═╗\n"
        "   ║█║  ║█║\n"
        "   ║█║  ║█║\n"
        "   ╚═╝  ╚═╝"
    ),
    "mage": (
        "   ╔═╗  ╔═╗\n"
        "   ║█║  ║█║\n"
        "    ║█║   \n"
        "   ╚═╝  ╚═╝"
    ),
    "merchant": (
        "   ╔═╗  ╔═╗\n"
        "   ║@║  ║@║\n"
        "   ╚═╝  ╚═╝\n"
        "    ╔═╗ \n"
        "    ║█║ \n"
        "    ╚═╝ "
    ),
    "npc": (
        "   ╔═╗  ╔═╗\n"
        "   ║█║  ║█║\n"
        "   ║█║  ║█║\n"
        "   ╚═╝  ╚═╝"
    ),
}

EMOTION_FACES = {
    "happy": "◕ ω ◕",
    "neutral": "◔ ω ◔",
    "sad": "◒ ω ◒",
    "angry": "◐ ω ◐",
    "fear": "○ ω ○",
    "focused": "◎ ω ◎",
}

SYMBOLS = {
    "CC-01": "👤",   "CC-02": "👤",   "CC-03": "🦊",   "CC-04": "👤",
    "CC-05": "👤",   "CC-06": "👤",   "CC-07": "👤",   "CC-08": "👤",
    "CC-09": "👤",   "CC-10": "👤",   "CC-11": "👤",   "CC-12": "👤",
    "CC-13": "👤",   "CC-14": "👤",   "CC-15": "👤",   "CC-16": "👤",
    "CC-17": "👤",   "CC-18": "👤",   "CC-19": "👤",   "CC-20": "👤",
    "CC-21": "👤",   "CC-22": "👤",   "CC-23": "👤",   "CC-24": "👤",
    "CC-25": "👤",   "CC-26": "👤",   "CC-27": "👤",   "CC-28": "👤",
    "CC-29": "👤",   "CC-30": "👤",   "CC-31": "👤",   "CC-32": "👤",
    "CC-33": "👤",   "CC-34": "👤",   "CC-35": "👤",   "CC-36": "👤",
    "CC-37": "👤",   "CC-38": "👤",   "CC-39": "👤",   "CC-40": "👤",
    "CC-41": "👤",   "CC-42": "👤",   "CC-43": "👤",   "CC-44": "👤",
    "CC-45": "👤",   "CC-46": "👤",   "CC-47": "👤",   "CC-48": "👤",
    "CC-49": "👤",   "CC-50": "👤",   "CC-51": "👤",   "CC-52": "👤",
    "CC-53": "👤",   "CC-54": "👤",   "CC-55": "👤",   "CC-56": "👤",
    "CC-57": "👤",   "CC-58": "👤",   "CC-59": "👤",
}
BODY_PARTS = [
    ("head", "頭部"), ("torso", "軀幹"), ("left_arm", "左上臂"),
    ("right_arm", "右上臂"), ("left_leg", "左腿"), ("right_leg", "右腿"),
]

# Race keyword detection for auto-injecting race token categories
# Maps race category → list of keywords to search in token names/values
_RACE_KEYWORDS = {
    "naval": ["艦","naval","ship","砲","魚雷","連裝","戰艦","航母","駆逐"],
    "beast": ["獣","beast","狼","爪","尾","毛皮","牙","fur","claw","tail"],
    "draconic": ["龍","竜","dragon","draconic","鱗","翼膜","吐息"],
    "mechanism": ["機械","mechan","robot","機","義體","gear","steam"],
    "element": ["炎","冰","氷","雷","風","element","魔","咒","杖","術","mana","core"],
    "spiritual": ["精霊","spirit","霊","ghost","幽","angel","天使"],
}

RED_BAR = "█"
BLUE_BAR = "▓"
GREEN_BAR = "░"
EMPTY_BAR = "·"


# =============================================================================
# Level-up system (NUMERICAL_SYSTEMS.md)
# =============================================================================

def exp_needed_for_level(level: int) -> int:
    """exp_to_next = 100 + (level - 1) * 50 per NUMERICAL_SYSTEMS.md"""
    return 100 + (level - 1) * 50


def gain_exp(character, amount: int) -> list:
    """Add EXP, auto-level-up if threshold reached. Returns list of level-up messages."""
    messages = []
    character["exp"] += amount
    while character["exp"] >= exp_needed_for_level(character["level"]):
        character["exp"] -= exp_needed_for_level(character["level"])
        character["level"] += 1
        # Level-up stat gains (NUMERICAL_SYSTEMS.md § 等級提升屬性提升)
        character["max_hp"] += 5
        character["hp"] = min(character["hp"] + 5, character["max_hp"])
        character["max_sp"] += 3
        character["sp"] = min(character["sp"] + 3, character["max_sp"])
        character["atk"] += 1
        character["defense"] += 1
        if "spd" in character:
            character["spd"] += 1
        if "karma" in character:
            character["karma"] += 1
        # Body part HP increase (distribute 5 HP across parts)
        for i, part_id in enumerate(character.get("body_parts", {})):
            bp = character["body_parts"][part_id]
            bp["max_hp"] += 1 if i < 5 else 0
        messages.append(f"✨ 升級! 你現在 Lv.{character['level']} (HP+5, SP+3, ATK+1, DEF+1)")
    return messages


def gain_exp_with_skills(character, xp_amount: int, skill_cat: str = "", skill_amount: int = 5) -> list:
    """Gain EXP and (optionally) skill EXP. Returns combined messages."""
    msgs = list(gain_exp(character, xp_amount))
    if skill_cat:
        msgs.extend(gain_skill_exp(character, skill_cat, skill_amount))
    return msgs


# =============================================================================
# Symbol portrait generation (CHARACTER_SYSTEM.md)
# =============================================================================

def get_portrait(character) -> str:
    """Return ASCII symbol portrait based on character's archetype."""
    hp_ratio = character["hp"] / character["max_hp"] if character["max_hp"] > 0 else 0
    token_list = character.get("token_list", [])
    token_cats = {t.get("category", "") for t in token_list}

    if "combat" in token_cats:
        base = SYMBOL_PORTRAITS["warrior"]
    elif "element" in token_cats or "energy" in token_cats:
        base = SYMBOL_PORTRAITS["mage"]
    elif "social" in token_cats or "craft" in token_cats:
        base = SYMBOL_PORTRAITS["merchant"]
    else:
        base = SYMBOL_PORTRAITS["default"]

    # Add emotion face
    if hp_ratio < 0.3:
        face = EMOTION_FACES["fear"]
    elif hp_ratio < 0.6:
        face = EMOTION_FACES["sad"]
    else:
        face = EMOTION_FACES["neutral"]

    # Damage overlay for low HP
    if hp_ratio < 0.25:
        overlay = "\n   ✦  ✦"
    elif hp_ratio < 0.5:
        overlay = "\n   ✦"
    else:
        overlay = ""

    name_label = character.get("name", "??")
    card_id = character.get("card_id", "")
    header = f"  {face}  {name_label}"
    if card_id:
        header += f" [{card_id}]"

    return f"{header}\n{base}{overlay}"


def load_cards():
    try:
        with open(CARD_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("cards", [])
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print("  ⚠ 角色卡文件載入失敗: %s" % e)
        print("  使用空白角色開始遊戲。")
        return []


def get_character_cards():
    all_cards = load_cards()
    return [c for c in all_cards if c.get("card_type") == "角色卡"]


def get_card_by_id(card_id):
    all_cards = load_cards()
    for c in all_cards:
        if c.get("card_id") == card_id:
            return c
    return None


def generate_character_from_card(card):
    name = card.get("name", "旅人")
    tokens = list(card.get("tokens", []))  # Copy to avoid mutating shared card list
    stats = card.get("stats", {})
    abilities = card.get("abilities", [])
    token_categories = {}
    for t in tokens:
        cat = t.get("category", "unknown")
        token_categories.setdefault(cat, []).append(t)

    vitality_tokens = [t for t in tokens if t.get("category") == "vitality"]
    combat_tokens = [t for t in tokens if t.get("category") == "combat"]
    craft_tokens = [t for t in tokens if t.get("category") == "craft"]
    knowledge_tokens = [t for t in tokens if t.get("category") == "knowledge"]
    social_tokens = [t for t in tokens if t.get("category") == "social"]
    element_tokens = [t for t in tokens if t.get("category") == "element"]
    energy_tokens = [t for t in tokens if t.get("category") == "energy"]
    exploration_tokens = [t for t in tokens if t.get("category") == "exploration"]

    max_hp = 80 + len(vitality_tokens) * 15 + int(stats.get("hp_bonus", 0)) + (1 if combat_tokens else 0) * 10
    max_sp = 30 + len(energy_tokens) * 8 + len(element_tokens) * 5
    atk = 5 + len(combat_tokens) * 3 + len(vitality_tokens) * 1 + int(stats.get("atk_bonus", 0))
    defense = 3 + len(vitality_tokens) * 2 + int(stats.get("def_bonus", 0))
    spd = 4 + len(exploration_tokens) * 2 + int(stats.get("spd_bonus", 0))
    karma = 5 + len(social_tokens) * 2 + len(knowledge_tokens) * 1 + int(stats.get("karma_bonus", 0))
    craft_skill = len(craft_tokens) * 3 + int(stats.get("craft_bonus", 0))

    # Detect race from token names/values + categories
    from sim_systems import detect_race, RACE_DATA, get_race_body_parts
    
    # Build token name/value text for race keyword detection
    _token_text = " ".join(str(t.get("name","")+t.get("value","")) for t in tokens).lower()
    _card_name = card.get("name","").lower()
    _all_text = _token_text + " " + _card_name
    
    # Inject race category tokens based on keyword detection
    _existing_cats = {t.get("category","") for t in tokens}
    for race_cat, keywords in _RACE_KEYWORDS.items():
        if race_cat not in _existing_cats:
            for kw in keywords:
                if kw in _all_text:
                    tokens.append({"category": race_cat, "name": f"{race_cat}_auto", "value": ""})
                    break
    
    race = detect_race(tokens)
    
    # Build body parts from race data
    body_part_ids = get_race_body_parts(race)
    rd = RACE_DATA.get(race, RACE_DATA["人類"])
    body_parts = {}
    # Use actual BODY_PARTS names for base parts
    bp_names = {bp[0]: bp[1] for bp in BODY_PARTS}
    num_parts = len(body_part_ids)
    base_hp = max_hp // num_parts if num_parts > 0 else max_hp
    extra = max_hp % num_parts if num_parts > 0 else 0
    for i, part_id in enumerate(body_part_ids):
        part_name = bp_names.get(part_id, part_id)
        part_hp = base_hp + (1 if i < extra else 0)
        body_parts[part_id] = {
            "name": part_name,
            "hp": part_hp,
            "max_hp": part_hp,
            "condition": "完好",
        }

    character = {
        "name": name,
        "card_id": card.get("card_id", "???"),
        "race": race,
        "tokens": token_categories,
        "token_list": tokens,
        "abilities": abilities,
        "stats": stats,
        "max_hp": max_hp,
        "hp": max_hp,
        "max_sp": max_sp,
        "sp": max_sp,
        "atk": atk,
        "defense": defense,
        "spd": spd,
        "karma": karma,
        "craft_skill": craft_skill,
        "exp": 0,
        "level": 1,
        "gold": 50,
        "body_parts": body_parts,
        "relationships": {},
        "inventory": [],
        "equipment": {},
        "location": "方碑丘",
        "day": 1,
        "hour": 8,
        "alignment": "neutral",
        "reputation": 0,
    }
    return character


def create_blank_character(name="旅人"):
    return {
        "name": name,
        "card_id": None,
        "race": "人類",
        "tokens": {},
        "token_list": [],
        "abilities": [],
        "stats": {},
        "max_hp": 100,
        "hp": 100,
        "max_sp": 50,
        "sp": 50,
        "atk": 10,
        "defense": 5,
        "spd": 5,
        "karma": 5,
        "craft_skill": 0,
        "exp": 0,
        "level": 1,
        "gold": 50,
        "body_parts": {
            pid: {"name": name, "hp": 100 // 6 + (1 if i < 100 % 6 else 0),
                  "max_hp": 100 // 6 + (1 if i < 100 % 6 else 0), "condition": "完好"}
            for i, (pid, name) in enumerate(BODY_PARTS)
        },
        "relationships": {},
        "inventory": [],
        "equipment": {},
        "location": "方碑丘",
        "day": 1,
        "hour": 8,
        "alignment": "neutral",
        "reputation": 0,
    }


def three_color_bars(hp_ratio, sp_ratio, exp_ratio, width=20):
    red_count = int(hp_ratio * width)
    blue_count = int(sp_ratio * width)
    green_count = int(exp_ratio * width)
    total = red_count + blue_count + green_count
    if total > width:
        excess = total - width
        if red_count >= excess:
            red_count -= excess
        elif blue_count >= excess:
            blue_count -= excess
        else:
            green_count -= excess
    red_str = RED_BAR * red_count
    blue_str = BLUE_BAR * blue_count
    green_str = GREEN_BAR * green_count
    empty = EMPTY_BAR * max(0, width - red_count - blue_count - green_count)
    return red_str + blue_str + green_str + empty


def display_three_bars(character):
    hp_ratio = character["hp"] / character["max_hp"] if character["max_hp"] > 0 else 0
    sp_ratio = character["sp"] / character["max_sp"] if character["max_sp"] > 0 else 0
    exp_ratio = min(1.0, character["exp"] / max(1, character["level"] * 100))
    bars = three_color_bars(hp_ratio, sp_ratio, exp_ratio)
    return bars


def display_character_sheet(character):
    lines = []
    symbol = _get_symbol(character)
    lines.append("")
    lines.append(C.CYAN + "┌" + "─" * 32 + "┐" + C.RESET)
    lines.append(C.CYAN + "│  " + C.BOLD + "%s %s" % (symbol, character["name"]) + C.RESET + " " * max(0, 26 - len(character["name"])) + C.CYAN + "│" + C.RESET)
    if character.get("card_id"):
        lines.append(C.CYAN + "│  ID: %s" % character["card_id"].ljust(29) + C.CYAN + "│" + C.RESET)
    lines.append(C.CYAN + "│  種族: %s" % character.get("race","人類").ljust(26) + C.CYAN + "│" + C.RESET)
    lines.append(C.CYAN + ("│  Lv.%d  EXP:%d/%d" % (character["level"], character["exp"], exp_needed_for_level(character["level"]))).ljust(30) + C.CYAN + "│" + C.RESET)
    lines.append(C.CYAN + "├" + "─" * 32 + "┤" + C.RESET)
    # HP bar
    hp_ratio = character["hp"] / character["max_hp"] if character["max_hp"] > 0 else 0
    hp_bar = _ansi_bar(hp_ratio, 20, C.RED)
    lines.append(C.CYAN + "│  " + C.RED + "HP" + C.RESET + ":%3d/%d" % (character["hp"], character["max_hp"]) + " " * max(0, 18 - len(str(character["hp"]) + str(character["max_hp"]))) + C.RED + hp_bar + C.RESET + C.CYAN + "│" + C.RESET)
    # SP bar
    sp_ratio = character["sp"] / character["max_sp"] if character["max_sp"] > 0 else 0
    sp_bar = _ansi_bar(sp_ratio, 20, C.BLUE)
    lines.append(C.CYAN + "│  " + C.BLUE + "SP" + C.RESET + ":%3d/%d" % (character["sp"], character["max_sp"]) + " " * max(0, 18 - len(str(character["sp"]) + str(character["max_sp"]))) + C.BLUE + sp_bar + C.RESET + C.CYAN + "│" + C.RESET)
    # Stats line
    lines.append(C.CYAN + "│  " + C.BOLD + "ATK:%3d  DEF:%3d" % (character["atk"], character["defense"]) + C.RESET + "  SPD:%d  KRM:%d" % (character.get("spd", 0), character.get("karma", 0)) + C.CYAN + "│" + C.RESET)
    # Skill line
    skills = character.get("skills", {})
    skill_str = ", ".join("%s Lv.%d" % (k, v.get("level", 1)) for k, v in skills.items())
    if skill_str:
        skill_display = skill_str[:28]
    else:
        skill_display = "(無技能)"
    lines.append(C.CYAN + "│  " + C.GREEN + skill_display.ljust(30) + C.RESET + C.CYAN + "│" + C.RESET)
    lines.append(C.CYAN + "├" + "─" * 32 + "┤" + C.RESET)
    gold = character.get("gold", 0)
    rep = character.get("reputation", 0)
    rel_count = len(character.get("relationships", {}))
    lines.append(C.CYAN + "│  " + C.YELLOW + "黃金:%d" % gold + C.RESET + "  " + C.MAGENTA + "聲望:%d" % rep + C.RESET + "  NPC:%d人" % rel_count + C.CYAN + "│" + C.RESET)
    lines.append(C.CYAN + "│  部位:" + " ".join("%s%d" % (k[0].upper(), v["hp"]) for k, v in list(character["body_parts"].items())[:3]) + C.CYAN + "│" + C.RESET)
    lines.append(C.CYAN + "└" + "─" * 32 + "┘" + C.RESET)
    lines.append("")
    return "\n".join(lines)


def _ansi_bar(ratio: float, width: int, color: str) -> str:
    """Render a colorized progress bar."""
    filled = int(ratio * width)
    bar = "█" * filled + "░" * (width - filled)
    return color + bar + C.RESET


def _get_symbol(character):
    card_id = character.get("card_id")
    if card_id and card_id in SYMBOLS:
        return SYMBOLS[card_id]
    return "👤"


def display_body_parts(character):
    lines = [C.CYAN + "身體部位:" + C.RESET]
    bp_names = dict(BODY_PARTS)
    for part_id, bp in character.get("body_parts", {}).items():
        part_name = bp.get("name", bp_names.get(part_id, part_id))
        hp = bp.get("hp", 0)
        mx = bp.get("max_hp", 1)
        ratio = hp / mx if mx > 0 else 0
        if ratio > 0.7:
            cond = "完好"
            cond_color = C.GREEN
        elif ratio > 0.4:
            cond = "受傷"
            cond_color = C.YELLOW
        elif ratio > 0:
            cond = "嚴重受傷"
            cond_color = C.RED
        else:
            cond = "失去機能"
            cond_color = C.RED + C.BOLD
        bar = _ansi_bar(ratio, 10, cond_color)
        lines.append("  %s %s %d/%d %s [%s%s%s]" % (
            part_id, part_name, hp, mx,
            bar, cond_color, cond, C.RESET))
    return "\n".join(lines)


def apply_damage(character, damage, body_part=None):
    if body_part:
        bp = character["body_parts"].get(body_part)
        if bp:
            actual = min(damage, bp["hp"])
            bp["hp"] = max(0, bp["hp"] - actual)
            if bp["hp"] <= 0:
                bp["condition"] = "失去機能"
            elif bp["hp"] < bp["max_hp"] * 0.4:
                bp["condition"] = "嚴重受傷"
            elif bp["hp"] < bp["max_hp"] * 0.7:
                bp["condition"] = "受傷"
            else:
                bp["condition"] = "完好"
            character["hp"] = sum(bp["hp"] for bp in character["body_parts"].values())
            return actual
    total_damage = 0
    for part_id, bp in character["body_parts"].items():
        if bp["hp"] <= 0:
            continue
        dmg = min(damage - total_damage, bp["hp"])
        if dmg <= 0:
            break
        bp["hp"] -= dmg
        total_damage += dmg
        if bp["hp"] <= 0:
            bp["condition"] = "失去機能"
    character["hp"] = sum(bp["hp"] for bp in character["body_parts"].values())
    return total_damage


def heal_character(character, amount):
    healed = 0
    for part_id, bp in character["body_parts"].items():
        if bp["hp"] >= bp["max_hp"]:
            continue
        heal = min(amount - healed, bp["max_hp"] - bp["hp"])
        if heal <= 0:
            break
        bp["hp"] += heal
        healed += heal
        if bp["hp"] >= bp["max_hp"]:
            bp["condition"] = "完好"
    character["hp"] = sum(bp["hp"] for bp in character["body_parts"].values())
    return healed


def add_relationship(character, npc_name, value):
    rels = character.setdefault("relationships", {})
    current = rels.get(npc_name, 0)
    rels[npc_name] = max(-100, min(100, current + value))
    return rels[npc_name]


def get_relationship(character, npc_name):
    return character.get("relationships", {}).get(npc_name, 0)


def display_relationships(character):
    rels = character.get("relationships", {})
    if not rels:
        return "  " + C.GRAY + "尚無NPC關係記錄。" + C.RESET
    lines = [C.CYAN + "  NPC關係:" + C.RESET]
    for name, val in sorted(rels.items(), key=lambda x: x[1], reverse=True):
        if val >= 50:
            emoji = "❤️"
            color = C.RED
        elif val >= 20:
            emoji = "🙂"
            color = C.GREEN
        elif val >= 0:
            emoji = "😐"
            color = C.WHITE
        elif val >= -30:
            emoji = "😟"
            color = C.YELLOW
        else:
            emoji = "😡"
            color = C.RED + C.BOLD
        if val >= 80:
            tier = "親密"
        elif val >= 50:
            tier = "友好"
        elif val >= 20:
            tier = "中立"
        else:
            tier = "敵意"
        lines.append("    %s %s%s%s: %d (%s)" % (emoji, color, name, C.RESET, val, tier))
    return "\n".join(lines)


# =============================================================================
# Quest tracking state helpers
# =============================================================================

def init_quest_state(character):
    """Initialize quest tracking in character state."""
    if "quests" not in character:
        character["quests"] = {}  # quest_id -> {status, progress, objectives_met}
    if "completed_quests" not in character:
        character["completed_quests"] = []
    return character["quests"]


def accept_quest(character, quest):
    """Accept a quest and add to tracking."""
    if quest is None:
        return False
    qs = init_quest_state(character)
    qid = quest["id"]
    if qid in qs or qid in character.get("completed_quests", []):
        return False
    qs[qid] = {
        "status": "active",
        "progress": {obj["type"] + ":" + obj["target"]: 0 for obj in quest["objectives"]},
        "objectives": [dict(obj) for obj in quest["objectives"]],
    }
    return True


def advance_quest_objective(character, quest_id, obj_type, obj_target, amount=1):
    """Advance progress on a quest objective. Returns True if just completed."""
    from sim_systems import QUESTS
    qs = character.get("quests", {})
    q = qs.get(quest_id)
    if not q or q["status"] != "active":
        return False
    key = obj_type + ":" + obj_target
    current = q["progress"].get(key, 0)
    q["progress"][key] = current + amount
    # Check if this objective is now met
    for obj in q["objectives"]:
        if obj["type"] == obj_type and obj["target"] == obj_target:
            needed = obj.get("qty", 1)
            if current < needed and current + amount >= needed:
                return True  # Just completed this objective
    return False


def check_quest_completion(character, quest_id):
    """Check if all objectives of a quest are met."""
    from sim_systems import QUESTS
    qs = character.get("quests", {})
    q = qs.get(quest_id)
    if not q:
        return False
    quest_def = next((qq for qq in QUESTS if qq["id"] == quest_id), None)
    if not quest_def:
        return False
    for obj in quest_def["objectives"]:
        key = obj["type"] + ":" + obj["target"]
        qty = obj.get("qty", 1)
        # Handle alt_item for flexible objectives
        alt_key = ""
        alt_item = obj.get("alt_item", "")
        if alt_item:
            alt_key = obj["type"] + ":" + alt_item
        progress = q["progress"].get(key, 0) or q["progress"].get(alt_key, 0)
        if progress < qty:
            return False
    return True


def complete_quest(character, quest_id):
    """Mark a quest as completed and give rewards."""
    from sim_systems import QUESTS, get_item_def
    qs = character.get("quests", {})
    quest_def = next((qq for qq in QUESTS if qq["id"] == quest_id), None)
    if not quest_def or quest_id not in qs:
        return None
    qs[quest_id]["status"] = "completed"
    character.setdefault("completed_quests", []).append(quest_id)
    gold = quest_def.get("reward_gold", 0)
    exp = quest_def.get("reward_exp", 0)
    item = quest_def.get("reward_item", "")
    character["gold"] = character.get("gold", 0) + gold
    if item:
        character.setdefault("inventory", []).append(item)
    return {"gold": gold, "exp": exp, "item": item}


def get_active_quests(character):
    """Get list of active quests with progress info."""
    from sim_systems import QUESTS
    qs = character.get("quests", {})
    result = []
    for qid, qdata in qs.items():
        if qdata["status"] == "active":
            quest_def = next((qq for qq in QUESTS if qq["id"] == qid), None)
            if quest_def:
                result.append((quest_def, qdata))
    return result


def check_quest_eligibility(character, quest, current_hour=None):
    """Check if a character can accept a quest.
    Returns (bool, reason_string).
    """
    from sim_systems import QUESTS
    if quest is None:
        return False, "任務不存在"
    conds = quest.get("conditions", {})
    
    # Check level
    req_lv = conds.get("required_level", 0)
    if req_lv > 0 and character.get("level", 1) < req_lv:
        return False, "等級不足 (需要 Lv.%d)" % req_lv
    
    # Check race
    req_race = conds.get("required_race", "")
    if req_race and character.get("race", "人類") != req_race:
        return False, "種族不符 (需要 %s)" % req_race
    
    # Check reputation
    req_rep = conds.get("required_reputation", 0)
    if req_rep > 0 and character.get("reputation", 0) < req_rep:
        return False, "聲望不足 (需要 %d)" % req_rep
    
    # Check relationships
    req_rels = conds.get("required_relationships", {})
    if req_rels:
        rels = character.get("relationships", {})
        for npc_name, needed_val in req_rels.items():
            current_val = rels.get(npc_name, 0)
            if current_val < needed_val:
                return False, "好感度不足 (%s 需要 %d, 目前 %d)" % (npc_name, needed_val, current_val)
    
    # Check prerequisite quests
    req_quests = conds.get("required_quests", [])
    if req_quests:
        completed = character.get("completed_quests", [])
        for rq in req_quests:
            if rq not in completed:
                qdef = next((qq for qq in QUESTS if qq["id"] == rq), None)
                title = qdef["title"] if qdef else rq
                return False, "需要先完成「%s」" % title
    
    # Check required tokens
    req_tokens = conds.get("required_tokens", [])
    if req_tokens:
        token_cats = {t.get("category", "") for t in character.get("token_list", [])}
        for tok in req_tokens:
            if tok not in token_cats:
                return False, "需要 [%s] 類別特質" % tok
    
    # Check time availability
    time_avail = conds.get("time_available", {})
    if time_avail:
        if current_hour is None:
            current_hour = character.get("hour", 8)
        start_h = time_avail.get("start_hour", 0)
        end_h = time_avail.get("end_hour", 24)
        if start_h <= end_h:
            if not (start_h <= current_hour < end_h):
                return False, "現在不是接取時間 (%d:00~%d:00)" % (start_h, end_h)
        else:
            # Wrap-around (e.g. 18:00~6:00)
            if not (current_hour >= start_h or current_hour < end_h):
                return False, "現在不是接取時間 (%d:00~%d:00)" % (start_h, end_h)
    
    # Check required skills
    req_skill = conds.get("required_skill", {})
    if req_skill:
        skills = character.get("skills", {})
        for sname, slevel in req_skill.items():
            cur_level = skills.get(sname, {}).get("level", 0)
            if cur_level < slevel:
                return False, "技能等級不足 (%s Lv.%d)" % (sname, slevel)
    
    return True, ""


def get_available_quests(character):
    """Get list of quests that the character can accept.
    Filters by conditions, not completed, not active.
    Returns list of (quest_def, reason_if_not_available_or_None).
    """
    from sim_systems import QUESTS
    qs = character.get("quests", {})
    completed = character.get("completed_quests", [])
    current_hour = character.get("hour", 8)
    result = []
    for q in QUESTS:
        if q["id"] in qs and qs[q["id"]]["status"] == "active":
            continue
        if q["id"] in completed:
            continue
        eligible, reason = check_quest_eligibility(character, q, current_hour)
        if eligible:
            result.append((q, None))
        else:
            result.append((q, reason))
    return result


# =============================================================================
# Vehicle state
# =============================================================================

def init_vehicle_state(character):
    if "vehicles" not in character:
        character["vehicles"] = {}  # vehicle_name -> {"owned": bool, "current": bool}
    if "riding" not in character:
        character["riding"] = None  # currently riding vehicle name


def mount_vehicle(character, vehicle_name, vehicles_state):
    """Mount a vehicle if available. Returns True if successful."""
    if vehicle_name not in vehicles_state:
        return False
    vehicle = vehicles_state[vehicle_name]
    if not vehicle.get("owned", False):
        return False
    character["riding"] = vehicle_name
    return True


def dismount_vehicle(character):
    was = character.get("riding")
    character["riding"] = None
    return was


# =============================================================================
# Skill system (CHARACTER_SYSTEM.md / NUMERICAL_SYSTEMS.md)
# =============================================================================

SKILL_CATEGORIES = ["combat", "craft", "social", "exploration", "knowledge"]
SKILL_EXP_MULTIPLIERS = {
    "combat": 2.0,
    "craft": 1.5,
    "social": 1.0,
    "exploration": 1.0,
    "knowledge": 1.2,
}


def init_skills(character):
    """Initialize skill dict from character tokens."""
    skills = {}
    token_list = character.get("token_list", [])
    for t in token_list:
        cat = t.get("category", "")
        if cat in SKILL_CATEGORIES:
            if cat not in skills:
                skills[cat] = {"level": 0, "exp": 0, "exp_to_next": 50}
            skills[cat]["level"] += 1
    character["skills"] = skills
    return skills


def gain_skill_exp(character, skill_category: str, amount: int = 5) -> list:
    """Gain skill EXP. Returns list of level-up messages."""
    messages = []
    skills = character.get("skills", {})
    if skill_category not in skills:
        skills[skill_category] = {"level": 0, "exp": 0, "exp_to_next": 50}
    skill = skills[skill_category]
    mult = SKILL_EXP_MULTIPLIERS.get(skill_category, 1.0)
    gain = int(amount * mult)
    skill["exp"] += gain
    while skill["exp"] >= skill["exp_to_next"]:
        skill["exp"] -= skill["exp_to_next"]
        skill["level"] += 1
        skill["exp_to_next"] = 50 + (skill["level"] - 1) * 25
        messages.append(f"📈 %s 技能升級! Lv.{skill['level']}" % skill_category.capitalize())
    return messages


def get_skill_modifier(character, skill_category: str) -> int:
    """Get stat modifier from skill level."""
    skill = character.get("skills", {}).get(skill_category, {})
    return skill.get("level", 0) * 2


# =============================================================================
# Reputation system effects (SIMULATION_SYSTEMS.md / WORLDS_AND_STORY.md)
# =============================================================================

def get_reputation_tier(reputation: int) -> str:
    if reputation < -10:
        return "敵意"
    elif reputation < 0:
        return "冷淡"
    elif reputation < 50:
        return "中立"
    elif reputation < 80:
        return "友好"
    else:
        return "親密"


def modify_reputation(character, amount: int):
    """Change reputation and return tier."""
    current = character.get("reputation", 0)
    character["reputation"] = max(-100, min(100, current + amount))
    return character["reputation"]
