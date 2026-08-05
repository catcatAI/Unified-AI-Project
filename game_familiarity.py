"""
Familiarity System — Progressive NPC information revelation.

PCs start knowing nothing about an NPC beyond a vague visual descriptor.
Through interaction (greeting, chatting, gifting, questing), they gain
familiarity XP, unlocking increasingly detailed information at each level.

Level 0: 未知  — Vague archetype label only
Level 1: 初識  — Name + race
Level 2: 知悉  — Role description + offers
Level 3: 熟悉  — Full description + abilities
Level 4: 親密  — Schedule + deep lore
Level 5: 羈絆  — Relationship bonus + secrets
"""

import random

FAMILIARITY_LEVEL_NAMES = {
    0: "未知",
    1: "初識",
    2: "知悉",
    3: "熟悉",
    4: "親密",
    5: "羈絆",
}

XP_THRESHOLDS = [0, 6, 20, 50, 100, 180]

XP_GAINS = {
    "greet": 3,
    "chat": 8,
    "gift": 12,
    "quest": 20,
    "special": 30,
}

ARCHETYPE_LABELS = {
    "warrior": "戰士",
    "merchant": "商販",
    "mage": "法師",
    "scout": "探險者",
    "engineer": "技師",
    "specialist": "專家",
    "default": "旅人",
}

DESCRIPTOR_PREFIXES = {
    "warrior": ["沉穩的", "銳利的", "歷戰的", "剛毅的"],
    "merchant": ["精明的", "忙碌的", "笑容可掬的", "算盤不離手的"],
    "mage": ["神秘的", "深思的", "眼中閃著微光的", "氣質飄渺的"],
    "scout": ["敏捷的", "四處張望的", "身輕如燕的", "警覺的"],
    "engineer": ["認真的", "手上沾著機油的", "戴著護目鏡的", "敲打著零件的"],
    "specialist": ["目光銳利的", "散發專業氣場的", "若有所思的"],
    "default": ["看起來普通的", "神色自若的", "靜靜站著的"],
}


def _calc_level(xp):
    for lvl in range(5, -1, -1):
        if xp >= XP_THRESHOLDS[lvl]:
            return lvl
    return 0


def get_level(character, npc_name):
    return character.get("familiarity", {}).get(npc_name, {}).get("level", 0)


def get_xp(character, npc_name):
    return character.get("familiarity", {}).get(npc_name, {}).get("xp", 0)


def gain_familiarity(character, npc_name, action):
    xp = XP_GAINS.get(action, 5)
    familiarities = character.setdefault("familiarity", {})
    state = familiarities.setdefault(npc_name, {"level": 0, "xp": 0})
    state["xp"] += xp
    new_level = _calc_level(state["xp"])
    if new_level > state["level"]:
        old_level = state["level"]
        state["level"] = new_level
        return new_level
    return None


def generate_vague_label(archetype, race, npc_name=""):
    """Generate description like [神秘的貓娘法師] for unknown NPCs."""
    arch_label = ARCHETYPE_LABELS.get(archetype, "旅人")
    prefixes = DESCRIPTOR_PREFIXES.get(archetype, ["一位"])
    prefix = random.choice(prefixes)

    if race and race not in ("不明", "?", ""):
        race_short = race.split("（")[0].strip()
        # 避免 [:6] 把全形字元切半（如「像素貓娘「概念」→「像素貓娘「概」）；
        # 截斷時以「…」標示，且不與職業標籤重複（種族名已含職業意義時不疊加）
        if len(race_short) > 8:
            race_short = race_short[:8] + "…"
        arch_extra = arch_label if arch_label not in race_short else ""
        parts = [prefix, race_short, arch_extra]
    else:
        parts = [prefix, arch_label]

    return "[" + "".join(p for p in parts if p) + "]"


def get_display_name(character, npc_name, npc_data):
    level = get_level(character, npc_name)
    if level < 1:
        archetype = npc_data.get("archetype", "default") if npc_data else "default"
        race = npc_data.get("race", "") if npc_data else ""
        return generate_vague_label(archetype, race, npc_name)
    return npc_name


def get_level_name(character, npc_name):
    level = get_level(character, npc_name)
    return FAMILIARITY_LEVEL_NAMES.get(level, "未知")


def get_revealed_info(character, npc_name, npc_metadata):
    """Return progressively revealed NPC info based on familiarity level."""
    level = get_level(character, npc_name)
    info = {"level": level, "level_name": FAMILIARITY_LEVEL_NAMES.get(level, "未知")}
    arch = npc_metadata.get("archetype", "default") if npc_metadata else "default"
    race = npc_metadata.get("race", "") if npc_metadata else ""

    if level < 1:
        info["display_name"] = generate_vague_label(arch, race, npc_name)
        info["description"] = "你還不認識這個" + ARCHETYPE_LABELS.get(arch, "旅人") + "。"
        return info

    info["display_name"] = npc_name
    info["race"] = race or "不明"

    if level >= 2:
        desc = (npc_metadata.get("description", "") if npc_metadata else "")
        info["role_hint"] = desc[:80] if desc else ""
        info["offers"] = (npc_metadata.get("offers", []) if npc_metadata else [])[:3]

    if level >= 3:
        info["description"] = (npc_metadata.get("description", "") if npc_metadata else "")
        ab_details = (npc_metadata.get("ability_details", []) if npc_metadata else [])
        info["abilities"] = [a.get("name", "") for a in ab_details if isinstance(a, dict)]
        info["archetype"] = ARCHETYPE_LABELS.get(arch, "旅人")

    if level >= 4:
        info["token_categories"] = (npc_metadata.get("token_categories", []) if npc_metadata else [])
        info["location"] = (npc_metadata.get("location", "") if npc_metadata else "")

    if level >= 5:
        info["secrets_unlocked"] = True

    return info


LEVEL_UP_MESSAGES = {
    1: "你開始記住這個人的模樣了——對方叫%s。",
    2: "你和%s聊過幾次，大概知道對方是做什麼的。",
    3: "你已經很熟悉%s了——對方的能力與經歷你都了解。",
    4: "你和%s之間有著深厚的信任。你知道對方的習慣與秘密。",
    5: "羈絆——你與%s之間有著超越言語的連結。",
}


def get_level_up_message(npc_name, new_level):
    msg = LEVEL_UP_MESSAGES.get(new_level, "你對%s的了解加深了。")
    return msg % npc_name


def init_familiarity(character):
    """Ensure familiarity dict exists in character."""
    if "familiarity" not in character:
        character["familiarity"] = {}
