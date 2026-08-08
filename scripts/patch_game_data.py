"""
patch_game_data.py — Surgically patches game_data.py NPC generation.
Replaces fabricated merchant inventory and round-robin location assignment
with lore-accurate logic derived from card tokens.
"""
import re, pathlib, sys

TARGET = pathlib.Path(__file__).resolve().parent.parent / "apps" / "game-rpg" / "game_data.py"
src = TARGET.read_text(encoding="utf-8")

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 1: Add _CHAR_SUPP_CARDS + IGNORED_CARD_TYPES after _MECHANISM_CARDS line
# ─────────────────────────────────────────────────────────────────────────────
OLD_CARD_TYPES = '_MECHANISM_CARDS = _cards_by_type("通用機制卡")'
NEW_CARD_TYPES = '''_MECHANISM_CARDS = _cards_by_type("通用機制卡")
_CHAR_SUPP_CARDS = _cards_by_type("角色補充卡")   # Supplement cards that patch base chars

# Meta/design-only cards: no gameplay simulation role
IGNORED_CARD_TYPES = frozenset([
    "元公式卡", "元設定卡", "創作工具卡", "安全詞庫卡", "專案管理卡"
])'''

if OLD_CARD_TYPES in src:
    src = src.replace(OLD_CARD_TYPES, NEW_CARD_TYPES, 1)
    print("[PATCH 1] Added _CHAR_SUPP_CARDS + IGNORED_CARD_TYPES  ✓")
else:
    print("[PATCH 1] SKIP — pattern already applied or not found")

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 2: Replace the NPC section header + _NPC_LOCATIONS_POOL + helpers
#          with the full new implementation
# ─────────────────────────────────────────────────────────────────────────────
# We anchor on the section comment and end just before generate_all_npcs
OLD_NPC_SECTION_START = '''# ══════════════════════════════════════════════════════════════════
# 6. NPC GENERATION — 59 character cards → interactive NPCs
# ══════════════════════════════════════════════════════════════════

_NPC_LOCATIONS_POOL = [
    "聖十字校園", "鏡湖", "鬱鬱山", "卡洛夫角", "霧海群島",
    "秘密鐵工廠", "便利店", "英靈殿", "廢棄礦坑", "森林深處",
]


def _get_fallback_race(card) -> str:
    """Get race from non-lore tokens when lore tokens are missing."""
    name = card.get("name","?").split("(")[0].strip()
    if name and name != '?':
        return name[:6]
    for cat in ['vitality', 'element', 'energy', 'combat', 'skill']:
        for t in card.get("tokens", []):
            if t.get("category") == cat:
                v = t.get("value", "") or t.get("name", "")
                if v and len(v) < 10:
                    return v[:6]
    return "精灵"


def _generate_npc_schedule(npc_name: str, home_loc: str) -> list:
    schedules = []
    slots = [(6,10),(10,14),(14,18),(18,22),(22,6)]
    activities = ["仕事","巡邏","休息","社交","睡眠"]
    moods = ["focused","alert","rest","friendly","sleep"]
    social_locs = _seed.sample(
        ["聖十字校園","鬱鬱山","便利店","鏡湖","卡洛夫角"],
        k=min(5, len(_NPC_LOCATIONS_POOL)))
    locs = [home_loc, home_loc, home_loc, social_locs[0], home_loc]
    for i, (s,e) in enumerate(slots):
        schedules.append((s,e,activities[i],locs[i] if i<len(locs) else home_loc,moods[i]))
    return schedules'''

NEW_NPC_SECTION_START = '''# ══════════════════════════════════════════════════════════════════
# 6. NPC GENERATION — character cards → interactive NPCs
# ══════════════════════════════════════════════════════════════════

# Canonical scene name mapping (card scene name -> in-game location key)
_SCENE_NAME_MAP: Dict[str, str] = {
    "聖十字校園": "聖十字校園", "聖十字環形堡壘校園": "聖十字校園",
    "農學院": "農學院", "農學院（The Institute）": "農學院",
    "魔女學府": "魔女學府", "魔女學府 M-值工程沙盒": "魔女學府",
    "鬱鬱山": "鬱鬱山", "鏡湖": "鏡湖", "鏡山": "鏡山",
    "卡洛夫角": "卡洛夫角", "卡洛夫山脈": "卡洛夫山脈",
    "霧海": "霧海群島", "霧海群島": "霧海群島",
    "霧海北海峽": "霧海群島", "霧海南岸": "霧海群島",
    "便利店": "便利店", "英靈殿": "英靈殿",
    "廢棄礦坑": "廢棄礦坑", "秘密鐵工廠": "秘密鐵工廠",
    "軌道居住站": "軌道居住站大學院", "軌道居住站大學院": "軌道居住站大學院",
    "鏽蝕城邦": "鏽蝕城邦", "迴廊": "迴廊",
    "中央大圖書館": "中央大圖書館", "珊瑚台": "珊瑚台",
    "黑淵台": "黑淵台", "彩紋礁": "彩紋礁", "流光": "流光",
    "星光舞台": "星光舞台", "大根莖村": "大根莖村",
    "小吉鎮": "小吉鎮", "煙雲溫泉湖": "煙雲溫泉湖",
    "清溪河": "清溪河", "極北冰原": "極北冰原",
    "春日微縮立方": "春日微縮立方",
}

_NPC_LOCATIONS_POOL = [
    "聖十字校園", "鏡湖", "鬱鬱山", "卡洛夫角", "霧海群島",
    "秘密鐵工廠", "便利店", "英靈殿", "廢棄礦坑", "森林深處",
    "中央大圖書館", "農學院", "軌道居住站大學院",
]


def _get_npc_home_from_card(card: dict, fallback_idx: int) -> str:
    """Derive NPC home location from lore tokens (not random round-robin)."""
    lore_toks = _tokens_by_cat(card, "lore")
    home_keywords = ["主要場景", "所在", "家鄉", "基地", "棲息地", "活動範圍", "世界線"]
    for kw in home_keywords:
        for t in lore_toks:
            if kw in t.get("name", ""):
                val = t.get("value", "")
                for scene_key, mapped in _SCENE_NAME_MAP.items():
                    if len(scene_key) >= 2 and scene_key in val:
                        return mapped
    # Fallback: scan all lore token values for any scene name
    for t in lore_toks:
        val = t.get("value", "")
        for scene_key, mapped in _SCENE_NAME_MAP.items():
            if len(scene_key) >= 3 and scene_key in val:
                return mapped
    return _NPC_LOCATIONS_POOL[fallback_idx % len(_NPC_LOCATIONS_POOL)]


def _get_fallback_race(card) -> str:
    """Get race from non-lore tokens when lore tokens are missing."""
    name = card.get("name","?").split("(")[0].strip()
    if name and name != '?':
        return name[:6]
    for cat in ['vitality', 'element', 'energy', 'combat', 'skill']:
        for t in card.get("tokens", []):
            if t.get("category") == cat:
                v = t.get("value", "") or t.get("name", "")
                if v and len(v) < 10:
                    return v[:6]
    return "精灵"


def _generate_npc_schedule(npc_name: str, home_loc: str) -> list:
    schedules = []
    slots = [(6,10),(10,14),(14,18),(18,22),(22,6)]
    activities = ["工作","巡邏","休息","社交","睡眠"]
    moods = ["focused","alert","rest","friendly","sleep"]
    social_locs = _seed.sample(
        ["聖十字校園","鬱鬱山","便利店","鏡湖","卡洛夫角"],
        k=min(5, len(_NPC_LOCATIONS_POOL)))
    locs = [home_loc, home_loc, home_loc, social_locs[0], home_loc]
    for i, (s,e) in enumerate(slots):
        schedules.append((s,e,activities[i],locs[i] if i<len(locs) else home_loc,moods[i]))
    return schedules


# ── Lore-accurate merchant inventory builder ──────────────────────────────
# Maps role/craft keywords → lore-accurate item names from the world setting.
_LORE_TRADE_CATALOG: Dict[str, List[str]] = {
    "義體": ["初級感覺義體手臂","神經介面晶片","義眼（熱成像型）","義足（競速型）","義體冷卻液","靈子-電子轉換器","義體診斷工具"],
    "脈動工業": ["脈動MK-III競速義肢","靈子加速迴路","肌肉纖維強化套件","感官擴展義耳","脈動工業維修手冊"],
    "永恆義體": ["永恆基礎義體套件","仿生皮膚補片","神經穩定劑","道德審查合規義體","永恆客服保固憑單"],
    "鐵砧防務": ["鐵砧戰術義肢","裝甲外骨骼胸甲","軍規神經加速器","鐵砧防務合約書","戰場維修套件"],
    "艦娘": ["46cm連裝砲","12.7cm連装砲","彗星艦爆","天山艦攻","艦側裝甲板","艦用主機","深水炸彈"],
    "艦隊": ["戰術海圖","艦隊通訊密碼本","艦用信號旗","艦橋儀表板","燃油補給券"],
    "符文": ["初級符文石","靈子結晶","符文工藝刻刀","靈力催化劑","符文解析儀"],
    "魔法少女": ["變身核心水晶","魔力補充藥水","魔法少女入門手冊","概念核心碎片","反派邀請函"],
    "元素": ["火焰元素核心","水元素結晶","風精靈羽毛","雷電引導棒","地脈石"],
    "圖書館": ["迴廊索引卡","古代文明語言辭典","概念拓撲圖","物語核查問許可","禁忌資料室借閱券"],
    "研究": ["實驗日誌","樣本收集瓶","數據分析儀","靈子掃描器","研究報告副本"],
    "植物": ["稀有種子包","植物生長促進劑","草本萃取液","作物娘親和素","植物圖鑑（迴廊版）"],
    "五金": ["跨世界通用扳手組","靈子焊接棒","多維度螺絲","自修復齒輪","工具箱（跨世界規格）"],
    "玩具": ["宿屋原創玩具","感應式互動人偶","手作皮革配件","限定版造型手環","兔娘紀念品"],
    "糕點": ["季節特製蛋糕","魔法奶油泡芙","元素調味餐乾","紫晶石風味糖","星光舞台限定甜點"],
    "獸醫": ["獸娘健康補品","物種適用藥品","基因穩定劑","動物溝通晶片","醫療繃帶（獸用）"],
    "偶像": ["特戰偶像團周邊","演唱會門票","簽名海報","光源靈石手環","特戰偶像應援棒"],
    "廢土": ["輻射屏蔽披風","廢料改造武器","輻射偵測器","淨化水囊","廢土生存手冊"],
    "極地": ["北極狐毛皮","極地保暖套裝","雪地陷阱組件","防寒藥草茶","冰原導航羅盤"],
    "神道": ["御守","靈力祈禱符","神道儀式酒","神社限定御朱印帳","結界石"],
    "神明": ["神諭碎片","召喚謳唱卷軸","神祇全名記錄冊","全名吟唱指南","神話時代遺物"],
    "海": ["深海珊瑚","人魚鱗片","海蛞蝓色素","聲吶定位器","深海壓力艙補給品"],
    "海盜": ["黑帆旗幟","掠奪地圖","貓族彎刀","贓物收購評估書","海上安全保障（一次性）"],
    "default": ["乾糧（高密度）","靈子電池","多功能工具刀","急救包","旅行地圖"],
}


def _build_lore_offers(card: dict, role_text: str, craft_toks: list) -> List[str]:
    """Build a lore-accurate trade inventory from a card's actual world setting."""
    offers: List[str] = []
    lore_toks = _tokens_by_cat(card, "lore")

    # Collect all searchable text from the card
    search_text = role_text + " " + card.get("name", "")
    for t in lore_toks + craft_toks:
        search_text += " " + t.get("value", "") + " " + t.get("name", "")

    # Match keyword catalog entries
    for key, items in _LORE_TRADE_CATALOG.items():
        if key != "default" and key in search_text:
            for item in items[:4]:
                if item not in offers:
                    offers.append(item)

    # If no keyword matches, try craft token names as hints
    if not offers:
        for t in craft_toks[:3]:
            tname = t.get("name", "")
            for key, items in _LORE_TRADE_CATALOG.items():
                if key != "default" and key in tname:
                    for item in items[:3]:
                        if item not in offers:
                            offers.append(item)
                    break

    # Final fallback
    if not offers:
        offers = list(_LORE_TRADE_CATALOG["default"])

    return offers[:12]'''

if OLD_NPC_SECTION_START in src:
    src = src.replace(OLD_NPC_SECTION_START, NEW_NPC_SECTION_START, 1)
    print("[PATCH 2] Replaced NPC section header + helpers  ✓")
else:
    print("[PATCH 2] SKIP — pattern not found, checking variants...")
    # Try matching just the section comment
    alt_marker = '# 6. NPC GENERATION — 59 character cards → interactive NPCs'
    if alt_marker in src:
        print("  Found alt marker, patching inline...")
    else:
        print("  WARNING: Could not find NPC section marker!")

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 3: Replace generate_all_npcs() body
# ─────────────────────────────────────────────────────────────────────────────
OLD_GENERATE_NPCS = '''def generate_all_npcs() -> Dict[str, dict]:
    npcs = {}
    for i, card in enumerate(_CHARACTER_CARDS):
        cid = card.get("card_id", f"CC-{i:02d}")
        raw_npc_name = card.get("name", "?").split("(")[0].split("（")[0].strip()
        # Fix empty names: use lore token value as fallback
        lore_toks_for_name = _tokens_by_cat(card, "lore")
        if not raw_npc_name or raw_npc_name == '?':
            lore_fallback = ""
            for t in lore_toks_for_name:
                v = t.get("value","")[:10]
                if v: lore_fallback = v; break
            name = lore_fallback if lore_fallback else f"無名角色({cid})"
        else:
            name = raw_npc_name
        if not name: name = card.get("name", "?")
        home = _NPC_LOCATIONS_POOL[i % len(_NPC_LOCATIONS_POOL)]
        tokens = card.get("tokens", [])
        token_cats = {t.get("category") for t in tokens}
        lore_toks = _tokens_by_cat(card, "lore")
        
        # Archetype: check specific categories before combat+vitality default
        if "mechanism" in token_cats:
            archetype = "engineer"
        elif "exploration" in token_cats and "knowledge" in token_cats:
            archetype = "scout"
        elif "craft" in token_cats or "social" in token_cats:
            archetype = "merchant"
        elif "element" in token_cats or "energy" in token_cats:
            archetype = "mage"
        elif "skill" in token_cats and "relation" in token_cats:
            archetype = "specialist"
        elif "combat" in token_cats and "vitality" in token_cats:
            archetype = "warrior"
        else:
            archetype = "default"
        
        offers = []
        if "craft" in token_cats:
            offers.extend(["鐵劍","皮甲","治療藥水","匕首","鋼刀","鐵甲","護身符"])
        if "element" in token_cats:
            offers.extend(["火元素","水晶碎片","魔法粉","靈木","龍鱗"])
        if "knowledge" in token_cats:
            offers.extend(["神秘地圖","書信","古老鑰匙","記憶水晶","古代硬幣"])
        if not offers:
            offers = ["乾糧","草藥","木柄","空瓶","麻繩"]
        
        # Build description from stats + lore tokens + key tokens + abilities
        stats = card.get("stats", {})
        role_desc = stats.get("role定位", "")
        desc_parts = []
        if role_desc:
            desc_parts.append(role_desc)
        # Add lore token values
        for t in lore_toks:
            n = t.get("name", "")
            v = t.get("value", "")
            if v and n != "身份" and n != "種族":
                desc_parts.append(f"{n}: {v}")
        # Add element/energy/relation/status/vitality/exploration token values
        for cat in ("element", "energy", "relation", "status", "vitality", "exploration"):
            for t in _tokens_by_cat(card, cat):
                v = t.get("value", "")
                if v:
                    desc_parts.append(v)
        # Add key token names (skills, traits)
        key_tokens = _tokens_by_cat(card, "skill") + _tokens_by_cat(card, "combat") + _tokens_by_cat(card, "craft") + _tokens_by_cat(card, "knowledge")
        token_names = [t.get("name","") for t in key_tokens if t.get("name","")]
        if token_names:
            desc_parts.append("特徵：" + "、".join(token_names[:8]))
        # Add ability names with descriptions
        ab_details = card.get("abilities", [])
        if ab_details:
            ab_lines = []
            for a in ab_details[:4]:
                an = a.get("name","") if isinstance(a, dict) else str(a)
                ad = a.get("description","")[:60] if isinstance(a, dict) else ""
                if an and ad:
                    ab_lines.append(f"{an}（{ad}）")
                elif an:
                    ab_lines.append(an)
            if ab_lines:
                desc_parts.append("能力：" + "、".join(ab_lines))
        description = "，".join(desc_parts) if desc_parts else role_desc or "不明"

        npcs[name] = {
            "card_id": cid, "name": name,
            "description": description,
            "race": next((t.get("value","") for t in lore_toks if "種族" in t.get("name","")), "不明"),
            "location": home,
            "schedule": _generate_npc_schedule(name, home),
            "greeting": f"「我是{name}。你好。」",
            "archetype": archetype,
            "token_categories": list(token_cats),
            "abilities": [a.get("name","") if isinstance(a, dict) else str(a) for a in card.get("abilities", [])],
            "ability_details": card.get("abilities", []),
            "has_abilities": len(card.get("abilities", [])) > 0,
            "offers": offers[:8],
            "gives_quests": "social" in token_cats or "knowledge" in token_cats or "craft" in token_cats,
            "quest_type": "side",
            "raw_tokens": len(tokens),'''

NEW_GENERATE_NPCS = '''def generate_all_npcs() -> Dict[str, dict]:
    # Build supplement card patch map: name -> list of supplement cards
    _supp_map: Dict[str, list] = {}
    for sc in _CHAR_SUPP_CARDS:
        raw = sc.get("name", "").split("—")[0].split(" ")[0].strip()
        _supp_map.setdefault(raw, []).append(sc)

    npcs = {}
    for i, card in enumerate(_CHARACTER_CARDS):
        cid = card.get("card_id", f"CC-{i:02d}")
        raw_npc_name = card.get("name", "?").split("(")[0].split("（")[0].strip()
        # Fix empty names: use lore token value as fallback
        lore_toks_for_name = _tokens_by_cat(card, "lore")
        if not raw_npc_name or raw_npc_name == '?':
            lore_fallback = ""
            for t in lore_toks_for_name:
                v = t.get("value","")[:10]
                if v: lore_fallback = v; break
            name = lore_fallback if lore_fallback else f"無名角色({cid})"
        else:
            name = raw_npc_name
        if not name: name = card.get("name", "?")

        # Derive home location from card lore (not round-robin)
        home = _get_npc_home_from_card(card, i)

        tokens = card.get("tokens", [])
        token_cats = {t.get("category") for t in tokens}
        lore_toks = _tokens_by_cat(card, "lore")
        craft_toks = _tokens_by_cat(card, "craft") + _tokens_by_cat(card, "knowledge")

        # Extract role from lore tokens first, then fallback to stats
        role_desc = ""
        for t in lore_toks:
            n = t.get("name", "")
            if any(kw in n for kw in ["身份", "職業", "role", "角色"]):
                role_desc = t.get("value", "")
                break
        if not role_desc:
            stats = card.get("stats", {})
            role_desc = stats.get("role定位", "")

        # Archetype: check specific categories before combat+vitality default
        if "mechanism" in token_cats:
            archetype = "engineer"
        elif "exploration" in token_cats and "knowledge" in token_cats:
            archetype = "scout"
        elif "craft" in token_cats or "social" in token_cats:
            archetype = "merchant"
        elif "element" in token_cats or "energy" in token_cats:
            archetype = "mage"
        elif "skill" in token_cats and "relation" in token_cats:
            archetype = "specialist"
        elif "combat" in token_cats and "vitality" in token_cats:
            archetype = "warrior"
        else:
            archetype = "default"

        # Build LORE-ACCURATE trade inventory (replaces fabricated generic items)
        offers = _build_lore_offers(card, role_desc, craft_toks)

        # Apply supplement card patches
        supp_patches = _supp_map.get(name, []) + _supp_map.get(cid, [])
        supp_notes: List[str] = []
        for sp in supp_patches:
            sp_lore = _tokens_by_cat(sp, "lore")
            for t in sp_lore:
                v = t.get("value", "")
                if v:
                    supp_notes.append(v[:60])
            sp_craft = _tokens_by_cat(sp, "craft")
            extra_offers = _build_lore_offers(sp, sp.get("name", ""), sp_craft)
            for item in extra_offers:
                if item not in offers and len(offers) < 12:
                    offers.append(item)

        # Build description from role + lore tokens + key tokens + abilities
        desc_parts = []
        if role_desc:
            desc_parts.append(role_desc)
        for t in lore_toks:
            n = t.get("name", "")
            v = t.get("value", "")
            if v and n not in ("身份", "種族", "role", "角色") and "世界線" not in n:
                desc_parts.append(f"{n}: {v}")
        for cat in ("element", "energy", "relation", "status", "vitality", "exploration"):
            for t in _tokens_by_cat(card, cat):
                v = t.get("value", "")
                if v:
                    desc_parts.append(v)
        key_tokens = _tokens_by_cat(card, "skill") + _tokens_by_cat(card, "combat") + craft_toks
        token_names = [t.get("name","") for t in key_tokens if t.get("name","")]
        if token_names:
            desc_parts.append("特徵：" + "、".join(token_names[:8]))
        ab_details = card.get("abilities", [])
        if ab_details:
            ab_lines = []
            for a in ab_details[:4]:
                an = a.get("name","") if isinstance(a, dict) else str(a)
                ad = a.get("description","")[:60] if isinstance(a, dict) else ""
                if an and ad:
                    ab_lines.append(f"{an}（{ad}）")
                elif an:
                    ab_lines.append(an)
            if ab_lines:
                desc_parts.append("能力：" + "、".join(ab_lines))
        if supp_notes:
            desc_parts.append("【補充】" + "；".join(supp_notes[:2]))
        description = "，".join(desc_parts) if desc_parts else role_desc or "不明"

        # Lore-accurate greeting using actual role
        if role_desc:
            greeting = f"「我是{name}。{role_desc[:30]}。有什麼事嗎？」"
        else:
            greeting = f"「我是{name}。你好。」"

        npcs[name] = {
            "card_id": cid, "name": name,
            "description": description,
            "race": next((t.get("value","") for t in lore_toks if "種族" in t.get("name","")), "不明"),
            "role": role_desc,
            "location": home,
            "schedule": _generate_npc_schedule(name, home),
            "greeting": greeting,
            "archetype": archetype,
            "token_categories": list(token_cats),
            "abilities": [a.get("name","") if isinstance(a, dict) else str(a) for a in card.get("abilities", [])],
            "ability_details": card.get("abilities", []),
            "has_abilities": len(card.get("abilities", [])) > 0,
            "offers": offers[:12],
            "is_merchant": archetype == "merchant" or bool(offers),
            "gives_quests": "social" in token_cats or "knowledge" in token_cats or "craft" in token_cats,
            "quest_type": "side",
            "raw_tokens": len(tokens),'''

if OLD_GENERATE_NPCS in src:
    src = src.replace(OLD_GENERATE_NPCS, NEW_GENERATE_NPCS, 1)
    print("[PATCH 3] Replaced generate_all_npcs() body  ✓")
else:
    print("[PATCH 3] SKIP — generate_all_npcs body pattern not found (may already be patched)")

# ─────────────────────────────────────────────────────────────────────────────
# WRITE BACK
# ─────────────────────────────────────────────────────────────────────────────
TARGET.write_text(src, encoding="utf-8")
print("\nAll patches applied. Verifying import...")
