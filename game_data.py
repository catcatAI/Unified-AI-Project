"""
game_data.py — MASSIVE content expansion for CLI RPG.
Generates 3000+ entities from card data + real-world analogies.
"""
import json, os, random as _random
from typing import Any, Dict, List, Optional
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
CARD_PATH = DATA_DIR / "game_cards.json"

# ══════════════════════════════════════════════════════════════════
# Supplement data: items/equipment/enemies not in the card deck
# (NAVAL_DATA, ANIMAL_DATA, HERBAL_ITEMS, ELEMENTAL_ITEMS, etc.)
# ══════════════════════════════════════════════════════════════════
SUPPLEMENT_PATH = DATA_DIR / "game_supplement.json"
_SUPPLEMENT: dict = {}
if SUPPLEMENT_PATH.exists():
    try:
        with open(SUPPLEMENT_PATH, "r", encoding="utf-8") as _f:
            _SUPPLEMENT = json.load(_f)
    except Exception as _e:
        print(f"WARNING: Failed to load supplement data from {SUPPLEMENT_PATH}: {_e}")
        _SUPPLEMENT = {}
else:
    print(f"WARNING: Supplement file not found: {SUPPLEMENT_PATH}")

# 固定種子：世界內容（配方/任務/容器/社交地點）確定性生成。
# 若用時間種子，每次啟動配方表不同，存檔引用的配方/任務 ID 會因重啟而失效。
_seed = _random.Random(20260720)

def _load_cards() -> dict:
    if CARD_PATH.exists():
        with open(CARD_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"cards": [], "cards_by_type": {}, "token_by_category": {}}

_CARD_DATA = _load_cards()
_ALL_CARDS: list = _CARD_DATA.get("cards", [])

def _cards_by_type(t: str) -> list:
    return [c for c in _ALL_CARDS if c.get("card_type") == t]

_CHARACTER_CARDS = _cards_by_type("角色卡")
_SCENE_CARDS = _cards_by_type("場景卡")
_STORY_CARDS = _cards_by_type("劇情節點卡")
_ORG_CARDS = _cards_by_type("組織卡")
_NATION_CARDS = _cards_by_type("國家卡")
_RULE_CARDS = _cards_by_type("規則卡")
_SKILL_CARDS = _cards_by_type("技能卡")
_STORYLINE_CARDS = _cards_by_type("故事線卡") + _cards_by_type("故事線補充卡")
_WORLD_CORE_CARDS = _cards_by_type("世界觀核心卡")
_MECHANISM_CARDS = _cards_by_type("通用機制卡")
_CHAR_SUPP_CARDS = _cards_by_type("角色補充卡")   # Supplement cards that patch base chars

# Meta/design-only cards: no gameplay simulation role
IGNORED_CARD_TYPES = frozenset([
    "元公式卡", "元設定卡", "創作工具卡", "安全詞庫卡", "專案管理卡"
])

def _tokens_by_cat(card, cat: str) -> list:
    return [t for t in card.get("tokens", []) if t.get("category") == cat]

# ══════════════════════════════════════════════════════════════════
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
    "月之宮殿": "月之宮殿", "廣寒殿": "月之宮殿", "月球": "月之宮殿",
    "森林深處": "森林深處", "古老森林": "森林深處", "萬物之庭": "森林深處",
}

# ══════════════════════════════════════════════════════════════════
# 世界線權威表（依場景卡文本）：每個可探索地點屬於哪條世界線
# 場景卡明載：S06 鏽蝕城邦（W04）、S07 熒光沼澤（W04）、S08 玻璃荒漠（W04）、
# S12/W03 軌道居住站大學院（W03）、SC-01/SC-09 農學院（SL-11）、
# SC-02 魔女學府 M-值工程沙盒（SL-10）、S03 煙雲溫泉湖（W04，卡名後綴）、
# S02 鬱鬱山（W01，貨物流入 W02）、S10/S11 夢境層（跨世界共享）、
# SC-20 星光舞台（W01＋迴廊）。未列出者屬 W01 主世界線。
_LOCATION_WORLD_LINES: Dict[str, str] = {
    # W03 軌道居住站（V3.4：低靈子、電子最高精度）
    "軌道居住站大學院": "W03",
    # W04 灰燼紀元（V3.4：不穩定靈子、電子大量損壞）
    "鏽蝕城邦": "W04", "熒光沼澤": "W04", "玻璃荒漠": "W04",
    # SL-10/SL-11 是文本系列標記；農學院與魔女學府是 W01 地理的「界域內」延伸
    # （手寫邊：聖十字校園 enter 農學院/魔女學府、鬱鬱山 east 魔女學府）——歸 W01，
    # 非分離世界線。
    "農學院": "W01",
    "魔女學府": "W01", "魔女學府 M-值工程沙盒": "W01",
    # 夢境層（跨世界共享，非任一世界線）
    "高密度大氣結晶行星": "夢境層", "綻放混成園": "夢境層",
    # W02 琥珀紀元（絕對無魔，應用物理統治的硬核中世紀村落——
    # Ver 3.1：小吉鎮/大根莖村「世界：W02琥珀紀元」）
    "小吉鎮": "W02", "大根莖村": "W02",
    # 迴廊（連接各世界線的橋樑）
    "迴廊": "迴廊",
    # 星光舞台（W01 偶像劇場＋迴廊投影）
    "星光舞台": "W01+迴廊",
    # 星光舞台子區域（演唱會模式等 12 個：W01+迴廊）
    "演唱會模式": "W01+迴廊", "戰術模式": "W01+迴廊",
    "切換瞬間": "W01+迴廊", "首爾奧林匹克體育場": "W01+迴廊",
    "後台更衣室": "W01+迴廊", "直播控制室": "W01+迴廊",
    "伺服器核心室": "W01+迴廊", "異常輸出時刻": "W01+迴廊",
    "舞台切換盲區": "W01+迴廊",
}


def get_location_world_line(loc_name: str) -> str:
    """回傳地點所屬世界線（依場景卡文本權威表，未列者預設 W01）。"""
    return _LOCATION_WORLD_LINES.get(loc_name, "W01")

_NPC_LOCATIONS_POOL = [
    "聖十字校園", "鏡湖", "鬱鬱山", "卡洛夫角", "霧海群島",
    "秘密鐵工廠", "便利店", "英靈殿", "廢棄礦坑", "森林深處",
    "中央大圖書館", "農學院", "軌道居住站大學院",
]


def _get_npc_home_from_card(card: dict, fallback_idx: int) -> str:
    """Derive NPC home location from card data (text authority).

    優先序（文本權威）：
    1. 卡片 stats.location（已清潔的主要場景，如『神社』『彩紋礁』『黑淵台聲吶站』）
    2. lore token 關鍵字（主要場景/所在/棲息地等）
    3. 隨機池（僅當卡片完全無位置資訊時）
    """
    # 1. 已清潔的 stats.location 優先（文本明載的主要場景）
    stats = card.get("stats", {}) or {}
    loc = str(stats.get("location") or "").strip()
    if loc:
        for scene_key, mapped in _SCENE_NAME_MAP.items():
            if len(scene_key) >= 2 and scene_key in loc:
                return mapped
        # 直接命中可探索地點
        import sim_systems as _ss
        wm = getattr(_ss, "WORLD_MAP", {})
        if loc in wm:
            return loc
    # 2. lore token 關鍵字掃描（舊機制保留為 fallback）
    lore_toks = _tokens_by_cat(card, "lore")
    home_keywords = ["主要場景", "所在", "家鄉", "基地", "棲息地", "活動範圍", "世界線"]
    for kw in home_keywords:
        for t in lore_toks:
            if kw in t.get("name", ""):
                val = str(t.get("value", ""))  # token value 可能是 int（如善惡值）
                for scene_key, mapped in _SCENE_NAME_MAP.items():
                    if len(scene_key) >= 2 and scene_key in val:
                        return mapped
    # Fallback: scan all lore token values for any scene name
    for t in lore_toks:
        val = str(t.get("value", ""))
        for scene_key, mapped in _SCENE_NAME_MAP.items():
            if len(scene_key) >= 3 and scene_key in val:
                return mapped
    return _NPC_LOCATIONS_POOL[fallback_idx % len(_NPC_LOCATIONS_POOL)]


def _species_home_override(race_text: str = "", role_text: str = "") -> str:
    """種族/職業基地覆寫：卡片無明確地點時，依種族與職業的常理歸屬地。

    優先序：職業（軌道管家→軌道站）> 種族（艦娘→港鎮、人魚→黑淵台）。
    """
    if not race_text and not role_text:
        return ""
    # 職業：軌道站莊園管家 → 軌道居住站大學院（收窄關鍵字，避免軌道砲/大學院教授誤導）
    if any(k in (role_text or "") for k in ("軌道站", "太空站", "軌道居住", "軌道大學院")):
        return "軌道居住站大學院"
    # 種族：星艦/太空艦娘 → 軌道居住站大學院（星艦是太空船不是海船）
    if any(k in (race_text or "") for k in ("星艦", "太空", "宇宙")):
        return "軌道居住站大學院"
    # 種族：艦娘 → 港鎮（卡洛夫角）；人魚 → 黑淵台聲吶站
    if "艦娘" in (race_text or ""):
        return "卡洛夫角"
    if "人魚" in (race_text or ""):
        return "黑淵台"
    return ""


def _extract_race_from_card(card) -> str:
    """Extract race from stats.race (primary), fallback to lore tokens, then name.
    
    Priority: stats.race (from game_cards.json) > lore tokens > token categories > name.
    """
    stats = card.get("stats", {})
    stats_race = stats.get("race", "")
    if stats_race and stats_race not in ("實證主義角色", "不明", ""):
        return stats_race
    lore_toks = _tokens_by_cat(card, "lore")
    race_from_lore = next((t.get("value","") for t in lore_toks if "種族" in t.get("name","")), "")
    if race_from_lore:
        return race_from_lore
    # Try token category name as race hint
    for cat in ['vitality', 'element', 'energy', 'combat', 'skill']:
        for t in card.get("tokens", []):
            if t.get("category") == cat:
                v = t.get("value", "") or t.get("name", "")
                if v and len(v) < 15:
                    return v[:12]
    # Use card name as fallback
    name = card.get("name","?").split("(")[0].strip()
    if name and name != '?' and not any(kw in name for kw in ["", " "]):
        return name[:10]
    # Extreme fallback: use token category names
    cats = list(set(t.get("category","") for t in card.get("tokens",[]) if t.get("category","")))
    if cats:
        return cats[0][:8]
    return "不明"


def _build_abilities_from_skills(card: dict, all_cards: list) -> list:
    """Generate abilities from SK-* skill cards instead of hardcoded templates."""
    # Build a mapping: token category -> skill card
    skill_cards = [c for c in all_cards if c.get("card_type", "") == "技能卡"]
    _cat_skill_map: dict = {}
    
    # Card-ID-based mapping (primary): maps SK card ID prefix to token category
    _SK_CATEGORY_MAP = {
        # Knowledge skills
        "SK-01": ["knowledge"],  # 植物學：北極生態
        "SK-02": ["knowledge"],  # 地質學：靈子礦脈
        "SK-04": ["knowledge"],  # 文獻學：舊時代解讀
        "SK-05": ["knowledge"],  # 妖精生態學
        "SK-16": ["knowledge"],  # 天翼技：知識掠取
        # Combat skills
        "SK-06": ["combat"],     # 格鬥：十字禁錮
        "SK-08": ["combat"],     # 弓道：靜心射擊
        "SK-09": ["combat"],     # 陷阱製作：極地狩獵
        # Element/Magic skills
        "SK-11": ["element"],    # 道術：五雷正法
        "SK-12": ["element"],    # 魔法：集束魔炮
        "SK-17": ["element"],    # 四季更迭（聯合施法）
        # Energy skills
        "SK-13": ["energy"],     # 奇蹟：奇蹟賜予於我
        # Craft skills
        "SK-03": ["craft", "mechanism"],  # 機械工程：螺旋葉輪
        "SK-07": ["craft"],      # 工藝：機械加工
        "SK-14": ["craft"],      # 妖精技：螢光開關
        "SK-21": ["craft", "tech"],  # 義體醫師
        "SK-22": ["craft"],      # 換裝義體
        # Skill specialty
        "SK-15": ["skill"],      # 精靈技：觀測結晶
        # Social skills
        "SK-10": ["social"],     # 潛伏：無聲移動
        "SK-18": ["social"],     # 打電話（通訊操作）
        # Tech skills
        "SK-19": ["tech"],       # 上網（網絡操作）
        "SK-20": ["tech"],       # 駭客（入侵系統）
    }
    
    for sc in skill_cards:
        sc_id = sc.get("card_id", "")
        sc_name = sc.get("name", "")
        sc_tokens = sc.get("tokens", [])
        sc_ability = next((t.get("value", "") for t in sc_tokens if t.get("category") == "ability"), "")
        
        # Primary: lookup by card_id
        keywords = []
        for sk_prefix, cats in _SK_CATEGORY_MAP.items():
            if sc_id.startswith(sk_prefix):
                keywords.extend(cats)
                break
        
        # Fallback: keyword-based matching for non-SK skill cards
        if not keywords:
            for kw, cat in [
                (["植物","botany"], "knowledge"), (["地質","geology"], "knowledge"),
                (["文獻","philology"], "knowledge"), (["妖精生態","fairy"], "knowledge"),
                (["格鬥","martial"], "combat"), (["弓道","archer"], "combat"),
                (["陷阱","trap"], "combat"), (["道術"], "element"),
                (["四季","魔法","magic"], "element"), (["奇蹟","miracle"], "energy"),
                (["種族"], "vitality"), (["妖精技"], "craft"),
                (["有翼","wing"], "skill"), (["機械工","mechanical"], "craft"),
                (["工藝","craft"], "craft"), (["潛伏","stealth"], "social"),
                (["打電話","telecom"], "social"), (["上網","internet"], "tech"),
                (["駭客","hack"], "tech"), (["義體","prosthetic"], "tech"),
            ]:
                if any(k in sc_name for k in kw):
                    keywords.append(cat)
        
        for kw in keywords:
            _cat_skill_map.setdefault(kw, []).append({"name": sc_name, "desc": sc_ability})
    
    result = []
    existing = card.get("abilities", [])
    if existing:
        # Use existing abilities from card deck (already populated)
        return existing
    
    # Generate from token categories using SK card mapping
    tokens = card.get("tokens", [])
    cats_found = set()
    for t in tokens:
        cat = t.get("category", "")
        if cat:
            cats_found.add(cat)
    
    # Build abilities from matched skill cards
    used_skills = []
    for cat in ["combat", "element", "energy", "craft", "skill", "knowledge", "social", "exploration", "vitality", "mechanism", "tech"]:
        if cat in cats_found and cat in _cat_skill_map:
            for sk in _cat_skill_map[cat]:
                if sk["name"] not in used_skills:
                    result.append({
                        "name": sk["name"],
                        "description": sk["desc"],
                        "type": cat,
                        "level": 1,
                    })
                    used_skills.append(sk["name"])
                    if len(result) >= 3:
                        break
        if len(result) >= 3:
            break
    
    # Fallback: race-based generic ability
    if not result:
        race = card.get("stats", {}).get("race", "")
        if race:
            result.append({
                "name": f"{race[:10]}的能力",
                "description": f"{race[:10]}的基本能力",
                "type": "general",
                "level": 1,
            })
        else:
            result.append({
                "name": "基礎能力",
                "description": "基本的戰鬥與生活能力",
                "type": "general",
                "level": 1,
            })
    
    return result[:5]



def _generate_npc_schedule(npc_name: str, home_loc: str, race_text: str = "") -> list:
    """產生 NPC 作息排程。夜行性角色（蝙蝠娘等文本明言夜行）晝伏夜出：
    白天睡眠、傍晚起床、夜晚活動——符合常理與文本。
    """
    # 夜行性判定：文本種族含 夜行/蝙蝠 等關鍵字
    _night_active = any(kw in (race_text or "") for kw in ("夜行", "蝙蝠娘", "蝙蝠"))
    if _night_active:
        # 晝伏夜出：睡眠(6-18) → 起床活動(18-22) → 夜間活動(22-2) → 深夜活動(2-6)
        slots = [(6, 18), (18, 22), (22, 2), (2, 6)]
        activities = ["睡眠", "工作", "巡邏", "社交"]
        moods = ["sleep", "focused", "alert", "friendly"]
        social_locs = _seed.sample(
            ["聖十字校園", "鬱鬱山", "便利店", "鏡湖", "卡洛夫角"],
            k=min(5, len(_NPC_LOCATIONS_POOL)))
        locs = [home_loc, home_loc, social_locs[0], social_locs[1] if len(social_locs) > 1 else home_loc]
        schedules = []
        for i, (s, e) in enumerate(slots):
            schedules.append((s, e, activities[i], locs[i] if i < len(locs) else home_loc, moods[i]))
        return schedules
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
    "圖紙艦娘": ["試作型艦裝設計圖","靈子驅動原型機","艦娘裝備藍圖","試驗型砲塔","未完成的艦裝零件"],
    "艦隊": ["戰術海圖","艦隊通訊密碼本","艦用信號旗","艦橋儀表板","燃油補給券"],
    "符文": ["初級符文石","靈子結晶","符文工藝刻刀","靈力催化劑","符文解析儀"],
    "魔法少女": ["變身核心水晶","魔力補充藥水","魔法少女入門手冊","概念核心碎片","反派邀請函"],
    "元素": ["火焰元素核心","水元素結晶","風精靈羽毛","雷電引導棒","地脈石"],
    "圖書館": ["迴廊索引卡","古代文明語言辭典","概念拓撲圖","物語核查問許可","禁忌資料室借閱券"],
    "圖書館管理員": ["迴廊索引卡","古代文明語言辭典","概念拓撲圖","物語核查問許可","禁忌資料室借閱券","館藏副本（限量）"],
    "研究": ["實驗日誌","樣本收集瓶","數據分析儀","靈子掃描器","研究報告副本"],
    "田野調查": ["野外調查記錄本","標本採集組件","生態觀測儀","妖精生態手冊","迴廊路徑記憶石"],
    "植物": ["稀有種子包","植物生長促進劑","草本萃取液","作物娘親和素","植物圖鑑（迴廊版）"],
    "農學院": ["作物娘親和素","稀有種子包","農學研究報告","GSI-4感知擴展儀","植物生態觀察日誌"],
    "五金": ["跨世界通用扳手組","靈子焊接棒","多維度螺絲","自修復齒輪","工具箱（跨世界規格）"],
    "五金店": ["跨世界通用扳手組","靈子焊接棒","多維度螺絲","自修復齒輪","工具箱（跨世界規格）"],
    "跨世界交易": ["跨世界匯票","多元宇宙護照","世界線轉換費率表","異界商品鑑定書","通用貨幣換算器"],
    "玩具": ["宿屋原創玩具","感應式互動人偶","手作皮革配件","限定版造型手環","兔娘紀念品"],
    "玩具製造": ["宿屋系列感應玩具","可編程互動人偶","手作皮革束帶","限定版月兔手環","客製化訂製服務券"],
    "成人玩具": ["宿屋原創成人玩具","高感度感知人偶","手作皮革配件","限定版造型手環","兔娘紀念品（限成人）"],
    "糕點": ["季節特製蛋糕","魔法奶油泡芙","元素調味餐乾","紫晶石風味糖","星光舞台限定甜點"],
    "烘焙": ["季節特製蛋糕","魔法奶油泡芙","紫暗元素糖霜","創意造型餅乾","食材學教材"],
    "獸醫": ["獸娘健康補品","物種適用藥品","基因穩定劑","動物溝通晶片","醫療繃帶（獸用）"],
    "偶像": ["特戰偶像團周邊","演唱會門票","簽名海報","光源靈石手環","特戰偶像應援棒"],
    "廢土": ["輻射屏蔽披風","廢料改造武器","輻射偵測器","淨化水囊","廢土生存手冊"],
    "輻射": ["輻射屏蔽披風","輻射偵測器","重金屬解毒劑","廢土生存手冊","淨化水囊"],
    "廢料": ["廢料改造零件","廢棄機械核心","鏽蝕城邦地圖","廢料鑑定工具","翻新材料包"],
    "極地": ["北極狐毛皮","極地保暖套裝","雪地陷阱組件","防寒藥草茶","冰原導航羅盤"],
    "北極狐": ["北極狐毛皮製品","極地保暖套裝","雪地陷阱組件","防寒藥草茶","冰原導航羅盤"],
    "極地獵手": ["極地獵具組","雪地偽裝套件","極地生存口糧","防寒急救藥包","獵物追蹤儀"],
    "神道": ["御守","靈力祈禱符","神道儀式酒","神社限定御朱印帳","結界石"],
    "巫女": ["神社御守","靈力祈禱符","弓道練習靶","神社限定御朱印帳","結界石"],
    "弓道": ["練習用弓","靈子箭矢","弓道手套","靜心符咒","弓弦蠟"],
    "神明": ["神諭碎片","召喚謳唱卷軸","神祇全名記錄冊","全名吟唱指南","神話時代遺物"],
    "校長": ["聖十字校章","學生手冊","入學許可申請表","校園地圖","神學教材（高級）"],
    "管家": ["軌道站設施維護手冊","管家禮儀指南","貴族餐具組","清潔用具（頂級）","龍息香薰"],
    "客服": ["客服禮儀手冊","溝通技巧卡牌","水元素補給品","安撫情緒晶石","藍水元素飾品"],
    "油漆": ["靛色元素塗料","油漆師傅工具組","色彩調配指南","防水塗料","顏料石"],
    "街頭技客": ["基因強化注射器","電子改造工具包","駭客程序卷軸","街頭市場情報","改造義體配件"],
    "造兵": ["軍工設計圖紙","精密機械零件","砲塔運作手冊","大正時代兵器圖鑑","靈子傳導裝置"],
    "機械": ["精密機械零件","靈子焊接棒","機械診斷儀","修復工具組","齒輪潤滑油"],
    "工匠": ["工匠工具組","精密零件箱","合金材料","加工技術手冊","訂製品委託券"],
    "海": ["深海珊瑚","人魚鱗片","海蛞蝓色素","聲吶定位器","深海壓力艙補給品"],
    "海盜": ["黑帆旗幟","掠奪地圖","貓族彎刀","贓物收購評估書","海上安全保障（一次性）"],
    "統治": ["鏽蝕城邦通行證","廢料稅收憑單","城邦守衛雇用合約","領地劃分地圖","廢墟知識手冊"],
    "教師": ["教學材料","課程許可卡","實驗器材組","參考書籍","補習課時間券"],
    "物理": ["物理實驗器材","黃雷元素電容","物理學教材","能量轉換計算器","電路板"],
    "default": ["乾糧（高密度）","靈子電池","多功能工具刀","急救包","旅行地圖"],
}

# ────────────────────────────────────────────────────────────────
# NPC 個人商店道具目錄（依 _LORE_TRADE_CATALOG 卡片語境）
# 卡片 NPC 的 offers 引用大量語境道具（義體/艦娘/符文/神話/廢土/極地等），
# 這些道具必須存在於 ITEM_CATALOG，NPC 個人商店才能真正販賣——否則
# NPC_METADATA.offers 是死資料（商店固定只賣 5 種，語境庫存全丟）。
# 規則化生成 + 重點手寫覆寫。魔法/電子關鍵字標記正確的世界線分類
# （batch 41/42：W02 絕對無魔、W03 電子加成、W04 過載）。
# ────────────────────────────────────────────────────────────────
_NPC_SHOP_ITEM_OVERRIDES: Dict[str, dict] = {
    # 艦娘（tech 武器）
    "12.7cm連装砲":   {"type": "weapon", "tags": ["weapon", "tech"], "value": 280, "weight": 6.0, "desc": "艦娘使用的 12.7cm 連裝砲"},
    "彗星艦爆":       {"type": "weapon", "tags": ["weapon", "tech"], "value": 320, "weight": 2.0, "desc": "艦娘搭載的彗星艦上爆擊機"},
    "天山艦攻":       {"type": "weapon", "tags": ["weapon", "tech"], "value": 300, "weight": 2.0, "desc": "艦娘搭載的天山艦上攻擊機"},
    "戰術海圖":       {"type": "material", "tags": ["document"], "value": 120, "weight": 0.4, "desc": "標記戰術航線的海圖"},
    "艦隊通訊密碼本": {"type": "material", "tags": ["document"], "value": 140, "weight": 0.4, "desc": "艦隊通訊使用的密碼本"},
    "艦用信號旗":     {"type": "material", "tags": ["material"], "value": 60, "weight": 0.5, "desc": "艦隊傳訊用的信號旗"},
    "艦橋儀表板":     {"type": "material", "tags": ["tech"], "value": 200, "weight": 2.0, "desc": "艦橋使用的儀表板"},
    # 靈子/魔法混合（世界線敏感）
    "靈子驅動原型機": {"type": "accessory", "tags": ["tech", "magic", "rare"], "value": 520, "weight": 1.5, "desc": "試作型靈子驅動裝置"},
    "靈子電池":       {"type": "material", "tags": ["tech", "magic"], "value": 80, "weight": 0.5, "desc": "儲存靈子能量的電池"},
    "靈子結晶":       {"type": "material", "tags": ["magic", "crystal"], "value": 90, "weight": 0.4, "desc": "凝聚靈子能量的結晶"},
    "靈子掃描器":     {"type": "material", "tags": ["tech"], "value": 220, "weight": 1.0, "desc": "掃描靈子濃度的手持儀器"},
    "靈子焊接棒":     {"type": "material", "tags": ["tech"], "value": 160, "weight": 1.2, "desc": "以靈子加熱的焊接棒"},
    "靈子箭矢":       {"type": "weapon", "tags": ["weapon", "magic"], "value": 130, "weight": 0.3, "desc": "灌注靈力的箭矢"},
    "靈子-電子轉換器": {"type": "material", "tags": ["tech", "magic"], "value": 240, "weight": 1.0, "desc": "靈子與電子能量互換的轉換器"},
    # 神話/神明（magic）
    "神諭碎片":       {"type": "material", "tags": ["magic", "rare"], "value": 400, "weight": 0.3, "desc": "神話時代遺留的神諭碎片"},
    "召喚謳唱卷軸":   {"type": "consumable", "tags": ["consumable", "magic"], "value": 350, "weight": 0.2, "desc": "記載召喚謳唱的卷軸"},
    "神祇全名記錄冊": {"type": "material", "tags": ["magic", "document"], "value": 500, "weight": 0.8, "desc": "記載神祇全名的記錄冊"},
    "全名吟唱指南":   {"type": "material", "tags": ["magic", "document"], "value": 450, "weight": 0.6, "desc": "正確吟唱神祇全名的指南"},
    "神話時代遺物":   {"type": "material", "tags": ["magic", "rare"], "value": 380, "weight": 1.0, "desc": "神話時代留存下來的遺物"},
    # 魔法少女
    "魔法少女入門手冊": {"type": "material", "tags": ["magic", "document"], "value": 120, "weight": 0.5, "desc": "魔法少女的入門教學手冊"},
    "變身核心水晶":   {"type": "material", "tags": ["magic", "crystal", "rare"], "value": 340, "weight": 0.4, "desc": "魔法少女變身的核心水晶"},
    "概念核心碎片":   {"type": "material", "tags": ["magic", "rare"], "value": 290, "weight": 0.3, "desc": "凝聚概念的碎片"},
    "反派邀請函":     {"type": "material", "tags": ["document"], "value": 70, "weight": 0.1, "desc": "來路不明的反派邀請函"},
    # 符文/元素（magic）
    "初級符文石":     {"type": "material", "tags": ["magic", "crystal"], "value": 80, "weight": 0.5, "desc": "刻有初級符文的石頭"},
    "符文工藝刻刀":   {"type": "material", "tags": ["magic", "tool"], "value": 150, "weight": 0.4, "desc": "雕刻符文的工藝刻刀"},
    "符文解析儀":     {"type": "material", "tags": ["magic", "tech"], "value": 210, "weight": 1.0, "desc": "解析符文結構的儀器"},
    "火焰元素核心":   {"type": "material", "tags": ["magic", "crystal"], "value": 180, "weight": 0.6, "desc": "凝聚火焰元素的結晶核心"},
    "水元素結晶":     {"type": "material", "tags": ["magic", "crystal"], "value": 160, "weight": 0.6, "desc": "凝聚水元素的結晶"},
    "風精靈羽毛":     {"type": "material", "tags": ["magic"], "value": 110, "weight": 0.1, "desc": "風精靈脫落的羽毛"},
    "雷電引導棒":     {"type": "weapon", "tags": ["weapon", "magic"], "value": 170, "weight": 1.5, "desc": "引導雷電之力的棍棒"},
    "地脈石":         {"type": "material", "tags": ["magic", "crystal"], "value": 130, "weight": 0.8, "desc": "蘊含地脈之力的石頭"},
    "黃雷元素電容":   {"type": "material", "tags": ["tech", "magic"], "value": 190, "weight": 0.8, "desc": "儲存黃雷元素能量的電容"},
    "靛色元素塗料":   {"type": "material", "tags": ["magic"], "value": 95, "weight": 0.6, "desc": "蘊含靛色元素的塗料"},
    "紫暗元素糖霜":   {"type": "consumable", "tags": ["consumable", "magic"], "value": 55, "weight": 0.2, "desc": "以紫暗元素調味的糖霜"},
    # 義體/科技（tech）
    "初級感覺義體手臂": {"type": "accessory", "tags": ["tech"], "value": 240, "weight": 2.0, "desc": "初級的感覺義體手臂"},
    "神經介面晶片":   {"type": "accessory", "tags": ["tech"], "value": 280, "weight": 0.2, "desc": "連接神經與機器的介面晶片"},
    "義眼（熱成像型）": {"type": "accessory", "tags": ["tech"], "value": 260, "weight": 0.3, "desc": "具熱成像功能的義眼"},
    "義足（競速型）": {"type": "accessory", "tags": ["tech"], "value": 250, "weight": 1.5, "desc": "競速用義足"},
    "義體冷卻液":     {"type": "consumable", "tags": ["consumable", "tech"], "value": 90, "weight": 0.4, "desc": "冷卻義體運作的液體", "heal_sp": 8},
    "義體診斷工具":   {"type": "material", "tags": ["tech", "tool"], "value": 140, "weight": 0.8, "desc": "診斷義體狀態的工具"},
    "GSI-4感知擴展儀": {"type": "accessory", "tags": ["tech"], "value": 300, "weight": 0.8, "desc": "擴展感知能力的 GSI-4 儀器"},
    "動物溝通晶片":   {"type": "accessory", "tags": ["tech"], "value": 150, "weight": 0.2, "desc": "輔助與動物溝通的晶片"},
    "電子改造工具包": {"type": "material", "tags": ["tech", "tool"], "value": 180, "weight": 1.5, "desc": "街頭技客的電子改造工具包"},
    "駭客程序卷軸":   {"type": "consumable", "tags": ["consumable", "tech"], "value": 150, "weight": 0.2, "desc": "封存駭客程序的卷軸", "heal_sp": 15},
    "靈子加速迴路":   {"type": "accessory", "tags": ["tech", "magic"], "value": 360, "weight": 0.6, "desc": "加速靈子運算的迴路"},
    "肌肉纖維強化套件": {"type": "accessory", "tags": ["tech"], "value": 310, "weight": 1.2, "desc": "強化肌肉纖維的套件"},
    "感官擴展義耳":   {"type": "accessory", "tags": ["tech"], "value": 230, "weight": 0.3, "desc": "擴展聽覺的義耳"},
    "仿生皮膚補片":   {"type": "material", "tags": ["tech"], "value": 120, "weight": 0.2, "desc": "修補義體外觀的仿生皮膚補片"},
    "神經穩定劑":     {"type": "consumable", "tags": ["consumable", "tech"], "value": 170, "weight": 0.3, "desc": "穩定神經訊號的藥劑", "heal_hp": 15, "heal_sp": 8},
    "裝甲外骨骼胸甲": {"type": "armor", "tags": ["armor", "tech"], "value": 420, "weight": 8.0, "desc": "外骨骼式裝甲胸甲"},
    "軍規神經加速器": {"type": "accessory", "tags": ["tech", "rare"], "value": 480, "weight": 0.5, "desc": "軍規級神經加速器"},
    "戰場維修套件":   {"type": "material", "tags": ["tech", "tool"], "value": 190, "weight": 1.5, "desc": "戰場緊急維修套件"},
    # 神道（magic）
    "神社限定御朱印帳": {"type": "material", "tags": ["document"], "value": 100, "weight": 0.4, "desc": "神社限定版的御朱印帳"},
    "結界石":         {"type": "material", "tags": ["magic", "crystal"], "value": 120, "weight": 0.8, "desc": "佈設結界的石頭"},
    "弓道練習靶":     {"type": "material", "tags": ["material"], "value": 45, "weight": 2.0, "desc": "弓道練習用靶"},
    "練習用弓":       {"type": "weapon", "tags": ["weapon"], "value": 110, "weight": 1.5, "desc": "弓道練習用弓"},
    "弓道手套":       {"type": "accessory", "tags": ["accessory"], "value": 40, "weight": 0.2, "desc": "弓道專用手套"},
    "靜心符咒":       {"type": "consumable", "tags": ["consumable", "magic"], "value": 60, "weight": 0.1, "desc": "安定心神的符咒", "heal_sp": 10},
    "弓弦蠟":         {"type": "material", "tags": ["material"], "value": 25, "weight": 0.2, "desc": "保養弓弦的蠟"},
    # reviewer 修正：規則生成誤分類的重點道具 + 任務目標補齊
    "多功能工具刀":   {"type": "material", "tags": ["tool"], "value": 130, "weight": 0.6, "desc": "多功能工具刀，冒險者常用工具"},
    "急救包":         {"type": "consumable", "tags": ["consumable"], "value": 60, "weight": 0.6, "desc": "緊急止血包紮的急救包", "heal_hp": 20},
    "木材":           {"type": "material", "tags": ["wood", "material"], "value": 15, "weight": 1.0, "desc": "未加工的木頭，建築與製作材料"},
    # 消耗品補實效（reviewer：無 heal_hp/heal_sp 的消耗品使用時補 0）
    "魔力補充藥水":   {"type": "consumable", "tags": ["consumable", "magic"], "value": 60, "weight": 0.3, "desc": "補充魔力的藥水", "heal_sp": 30},
    "魔法奶油泡芙":   {"type": "consumable", "tags": ["consumable", "magic"], "value": 45, "weight": 0.2, "desc": "注入魔力的奶油泡芙", "heal_sp": 15, "heal_hp": 10},
    "靈力催化劑":     {"type": "consumable", "tags": ["consumable", "magic"], "value": 140, "weight": 0.2, "desc": "催化靈力流動的藥劑", "heal_sp": 25},
    "靈力祈禱符":     {"type": "consumable", "tags": ["consumable", "magic"], "value": 70, "weight": 0.1, "desc": "灌注靈力的祈禱符", "heal_sp": 10},
    "基因強化注射器": {"type": "consumable", "tags": ["consumable", "tech"], "value": 260, "weight": 0.4, "desc": "注入基因強化藥劑的注射器", "heal_hp": 35},
    "基因穩定劑":     {"type": "consumable", "tags": ["consumable", "tech"], "value": 200, "weight": 0.3, "desc": "穩定基因改造副作用的藥劑", "heal_hp": 25, "heal_sp": 10},
    "御守":           {"type": "consumable", "tags": ["consumable", "magic"], "value": 50, "weight": 0.1, "desc": "神社的御守護身符", "heal_sp": 8},
    "神社御守":       {"type": "consumable", "tags": ["consumable", "magic"], "value": 55, "weight": 0.1, "desc": "神社特別加持的御守", "heal_sp": 10},
    "神道儀式酒":     {"type": "consumable", "tags": ["consumable"], "value": 65, "weight": 0.6, "desc": "神道儀式使用的清酒", "heal_sp": 12},
    "防寒藥草茶":     {"type": "consumable", "tags": ["consumable"], "value": 40, "weight": 0.3, "desc": "驅寒的藥草茶", "heal_hp": 15},
    "極地生存口糧":   {"type": "consumable", "tags": ["consumable"], "value": 45, "weight": 0.4, "desc": "極地特製的高熱量口糧", "heal_hp": 18},
    "防寒急救藥包":   {"type": "consumable", "tags": ["consumable"], "value": 70, "weight": 0.6, "desc": "極地用急救藥包", "heal_hp": 25},
    "淨化水囊":       {"type": "consumable", "tags": ["consumable"], "value": 35, "weight": 0.5, "desc": "過濾淨化的水囊", "heal_hp": 12},
    "重金屬解毒劑":   {"type": "consumable", "tags": ["consumable"], "value": 90, "weight": 0.3, "desc": "解除重金屬中毒的藥劑", "heal_hp": 20},
    "季節特製蛋糕":   {"type": "consumable", "tags": ["consumable"], "value": 55, "weight": 0.3, "desc": "季節限定的特製蛋糕", "heal_hp": 15, "heal_sp": 10},
    "創意造型餅乾":   {"type": "consumable", "tags": ["consumable"], "value": 30, "weight": 0.2, "desc": "造型可愛的手工餅乾", "heal_hp": 10},
    "元素調味餐乾":   {"type": "consumable", "tags": ["consumable", "magic"], "value": 50, "weight": 0.3, "desc": "以元素調味的餐乾", "heal_hp": 12, "heal_sp": 8},
    "獸娘健康補品":   {"type": "consumable", "tags": ["consumable"], "value": 85, "weight": 0.4, "desc": "獸娘專用的健康補品", "heal_hp": 22},
    "物種適用藥品":   {"type": "consumable", "tags": ["consumable"], "value": 75, "weight": 0.3, "desc": "適用各種物種的藥品", "heal_hp": 20},
}


def _build_npc_shop_item_def(name: str) -> dict:
    """規則化生成 NPC 商店道具定義（名稱關鍵字分類）。
    覆蓋 _NPC_SHOP_ITEM_OVERRIDES 未列出的語境道具，確保 offers 全部可販賣。"""
    def _rare_mult(nm):
        if any(k in nm for k in ("限定", "試作", "原型", "軍規", "頂級", "神明", "神祇",
                                 "傳說", "高感度", "獨家", "限量", "深海")):
            return 3.0
        if any(k in nm for k in ("初級", "練習", "普通", "原創", "基礎")):
            return 0.6
        return 1.0
    mult = _rare_mult(name)
    # 文件/書類
    if any(k in name for k in ("手冊", "圖鑑", "指南", "辭典", "海圖", "地圖", "筆記", "記錄",
                               "教材", "許可", "護照", "匯票", "憑單", "門票", "合約", "藍圖",
                               "設計圖", "索引卡", "表", "憑證", "禮儀")):
        return {"type": "material", "tags": ["document"], "value": int(90 * mult),
                "weight": 0.5, "desc": f"{name}，記錄重要資訊的文檔"}
    # 武器
    if any(k in name for k in ("砲", "艦爆", "艦攻", "彎刀", "弓", "劍", "刀", "槍", "獵具", "棒")):
        return {"type": "weapon", "tags": ["weapon"], "value": int(140 * mult),
                "weight": 3.0, "desc": f"{name}，一件趁手的武器"}
    # 防具
    if any(k in name for k in ("披風", "鎧", "裝甲", "護具", "套裝", "胸甲", "盾")):
        return {"type": "armor", "tags": ["armor"], "value": int(160 * mult),
                "weight": 4.0, "desc": f"{name}，提供防護的裝備"}
    # 飾品
    if any(k in name for k in ("手環", "飾品", "晶石", "耳", "配件")):
        return {"type": "accessory", "tags": ["accessory"], "value": int(120 * mult),
                "weight": 0.3, "desc": f"{name}，精巧的飾品"}
    # 消耗品
    if any(k in name for k in ("藥", "劑", "卷軸", "符", "御守", "茶", "酒", "水", "口糧",
                               "餅乾", "蛋糕", "糖", "補給", "餐乾", "蜜", "湯", "點心", "飲料")):
        return {"type": "consumable", "tags": ["consumable"], "value": int(50 * mult),
                "weight": 0.3, "desc": f"{name}，可使用的消耗品"}
    # 科技/儀器
    if any(k in name for k in ("義體", "義肢", "義眼", "義足", "注射器", "驅動", "儀", "掃描",
                               "偵測", "定位", "計算", "診斷", "工具", "電池", "晶片", "迴路",
                               "零件", "機械", "電容")):
        return {"type": "material", "tags": ["tech"], "value": int(180 * mult),
                "weight": 1.0, "desc": f"{name}，科技產物"}
    # 材料
    return {"type": "material", "tags": ["material"], "value": int(60 * mult),
            "weight": 0.5, "desc": f"{name}，可交易的材料"}



def _build_lore_offers(card: dict, role_text: str, craft_toks: list) -> List[str]:
    """Build a lore-accurate trade inventory from a card's actual world setting."""
    offers: List[str] = []
    lore_toks = _tokens_by_cat(card, "lore")

    # Priority 1: Extract 身份 (identity/job) token — the most reliable source
    identity_text = ""
    for t in lore_toks:
        if t.get("name", "") in ("身份", "職業", "定位", "角色", "工作", "職稱"):
            identity_text = t.get("value", "")
            break

    # Build a comprehensive search string, identity first for priority
    search_text = identity_text + " " + role_text + " " + card.get("name", "")
    for t in lore_toks + craft_toks:
        search_text += " " + t.get("value", "") + " " + t.get("name", "")

    # Match keyword catalog entries (longer keys first to avoid false substring hits)
    sorted_keys = sorted(
        ((k, v) for k, v in _LORE_TRADE_CATALOG.items() if k != "default"),
        key=lambda kv: -len(kv[0])
    )
    for key, items in sorted_keys:
        if key in search_text:
            for item in items[:4]:
                if item not in offers:
                    offers.append(item)

    # If no keyword matches, try craft token names as hints
    if not offers:
        for t in craft_toks[:4]:
            tname = t.get("name", "")
            for key, items in sorted_keys:
                if key in tname:
                    for item in items[:3]:
                        if item not in offers:
                            offers.append(item)
                    break

    # Final fallback
    if not offers:
        offers = list(_LORE_TRADE_CATALOG["default"])

    return offers[:12]

def generate_all_npcs() -> Dict[str, dict]:
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

        # 卡片完全無地點資訊時，依種族/職業常理覆寫基地（艦娘在港鎮、人魚在聲吶站等）
        if not str((card.get("stats") or {}).get("location") or "").strip():
            _ov = _species_home_override(
                race_text=_extract_race_from_card(card), role_text=role_desc)
            if _ov:
                home = _ov

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
            # Use race or lore for a better generic greeting
            race_hint = _extract_race_from_card(card)
            if race_hint and race_hint != "不明":
                greeting = f"「我是{name}，{race_hint}。你找我？」"
            else:
                greeting = f"「我是{name}。你好。」"

        npcs[name] = {
            "card_id": cid, "name": name,
            "description": description,
            "race": _extract_race_from_card(card),
            "role": role_desc,
            "location": home,
            "schedule": _generate_npc_schedule(name, home, _extract_race_from_card(card)),
            "greeting": greeting,
            "archetype": archetype,
            "token_categories": list(token_cats),
            "abilities": [a.get("name","") if isinstance(a, dict) else str(a) for a in card.get("abilities", [])],
            "ability_details": _build_abilities_from_skills(card, _CHARACTER_CARDS),
            "has_abilities": True,
            "offers": offers[:12],
            "is_merchant": archetype == "merchant" or bool(offers),
            "gives_quests": "social" in token_cats or "knowledge" in token_cats or "craft" in token_cats,
            "quest_type": "side",
            "raw_tokens": len(tokens),
        }
    return npcs

ALL_NPCS = generate_all_npcs()


# ══════════════════════════════════════════════════════════════════
# 6b. SKILL GENERATION — from skill cards (SK-01~SK-22)
# ══════════════════════════════════════════════════════════════════

def generate_all_skills() -> dict:
    skills = {}
    for card in _SKILL_CARDS:
        cid = card.get("card_id", "SK-??")
        name = card.get("name", "").strip()
        if not name:
            continue
        tokens = card.get("tokens", [])
        desc = ""
        for t in tokens:
            if t.get("category") == "ability":
                desc = t.get("value", t.get("name", ""))
                break
        if not desc:
            desc = name.split("：")[-1] if "：" in name else name
        # Determine primary category from name
        cat = "general"
        if any(kw in name for kw in ["道術","魔法","奇蹟","四季"]):
            cat = "magic"
        elif any(kw in name for kw in ["格鬥","弓道","陷阱"]):
            cat = "combat"
        elif any(kw in name for kw in ["潛伏","駭客"]):
            cat = "stealth"
        elif any(kw in name for kw in ["植物","地質","文獻","妖精"]):
            cat = "knowledge"
        elif any(kw in name for kw in ["機械","工藝","換裝","義體"]):
            cat = "craft"
        elif any(kw in name for kw in ["打電話","上網"]):
            cat = "tech"
        skills[cid] = {
            "name": name,
            "description": desc,
            "category": cat,
            "source_card": cid,
            "trainable": True,
            "level": 1,
        }
    return skills

ALL_SKILLS = generate_all_skills()


# ══════════════════════════════════════════════════════════════════
# 6c. STORYLINE GENERATION — from storyline cards (SL-01~SL-11)
# ══════════════════════════════════════════════════════════════════

def generate_all_storyline_quests() -> list:
    quests = []
    for card in _STORYLINE_CARDS:
        cid = card.get("card_id", "SL-??")
        name = card.get("name", "").strip()
        if not name:
            continue
        tokens = card.get("tokens", [])
        theme = ""
        for t in tokens:
            if t.get("category") == "lore" and "核心" in t.get("name",""):
                theme = t.get("value", t.get("name", ""))
                break
        if not theme:
            theme = name
        quests.append({
            "id": f"{cid}-MAIN",
            "title": name,
            "description": theme,
            "quest_type": "main",
            "objectives": [{"type": "story", "target": cid, "description": f"探索 {name} 的故事線", "require_action": "advance", "require_times": 3}],
            "rewards": [f"完成 {name} 主線劇情"],
            "source_card_id": cid,
        })
    return quests

ALL_STORYLINE_QUESTS = generate_all_storyline_quests()


# ══════════════════════════════════════════════════════════════════
# 6d. WORLD CORE GENERATION — from world core cards (WC/W series)
# ══════════════════════════════════════════════════════════════════

def generate_world_modifiers() -> dict:
    modifiers = {}
    for card in _WORLD_CORE_CARDS:
        cid = card.get("card_id", "WC-??")
        name = card.get("name", "").strip()
        tokens = card.get("tokens", [])
        desc = ""
        for t in tokens:
            if t.get("category") == "lore":
                desc = t.get("value", t.get("name", ""))
                break
        if not desc:
            desc = name
        modifiers[cid] = {
            "name": name,
            "description": desc,
            "effect": "world_modifier",
        }
    return modifiers

ALL_WORLD_MODIFIERS = generate_world_modifiers()


# ══════════════════════════════════════════════════════════════════
# 7. ITEM GENERATION — assemble all items
# ══════════════════════════════════════════════════════════════════

def _make_item(name: str, typ: str, slot: str, atk: float, dfn: float, spd: float,
               krm: float, dur: int, val: int, desc: str, tags: list) -> dict:
    d = {"type": typ, "weight": 2.0, "value": val, "desc": desc, "tags": tags}
    sm = {}
    if atk != 0: sm["atk"] = atk
    if dfn != 0: sm["defense"] = dfn
    if spd != 0: sm["spd"] = spd
    if krm != 0: sm["karma"] = krm
    if typ in ("weapon","armor","accessory"):
        d["durability"] = dur
        d["slot"] = slot
        d["stat_multipliers"] = sm
    if typ == "consumable":
        d["weight"] = 0.3
    if typ == "junk":
        d["weight"] = 0.2
    # 軸譜交互：裝備可交互性由角色軸譜親和力決定（axis_system.evaluate_equipment
    # 依 tags 即時判定主交互維度）；required_race 僅為無軸譜角色
    # （人類/艦娘等未分類）的後備提示，不再以 token 猜種族。
    # Race/archetype restriction based on tags
    # Race-specific: only characters with matching race can equip
    if "naval" in tags:
        d["required_race"] = "艦娘"
        d["required_archetype"] = "combat"
    elif "elemental" in tags or "magic" in tags:
        d["required_race"] = "術士"
        d["required_archetype"] = "element"
    elif "beast" in tags or "natural" in tags:
        d["required_race"] = "獸娘"
        d["required_archetype"] = "vitality"
    elif "draconic" in tags:
        d["required_race"] = "龍族"
        d["required_archetype"] = "combat"
    elif "mechanical" in tags:
        d["required_race"] = "機械"
        d["required_archetype"] = "mechanism"
    elif "spiritual" in tags:
        d["required_race"] = "精靈"
        d["required_archetype"] = "energy"
    return d

def generate_all_items() -> Dict[str, dict]:
    items = {}
    
    # Naval weapons
    for _entry_n in _SUPPLEMENT.get("naval_data", []):
        name, typ, slot, atk, dfn, dur, val = _entry_n["name"], _entry_n["type"], _entry_n["slot"], _entry_n["atk_mult"], _entry_n["def_mult"], _entry_n["durability"], _entry_n["value"]
        nation, ship = _entry_n.get("nation", ""), _entry_n.get("ship_class", "")
        items[name] = _make_item(name, typ, slot, atk, dfn, 0, 0, dur, val,
                                 f"{nation} {ship}", ["naval","rare"] if val>300 else ["naval"])
    
    # Animal items
    for _entry_a in _SUPPLEMENT.get("animal_data", []):
        name, typ, slot, atk, dfn, spd, krm, dur, val, species, biome = _entry_a["name"], _entry_a["type"], _entry_a["slot"], _entry_a["atk_mult"], _entry_a["def_mult"], _entry_a["spd_mult"], _entry_a["karma_mult"], _entry_a["durability"], _entry_a["value"], _entry_a["species"], _entry_a["biome"]
        items[name] = _make_item(name, typ, slot, atk, dfn, spd, krm, dur, val,
                                 f"{species}（{biome}）", ["beast","natural"])
    
    # Elemental
    for _entry_e in _SUPPLEMENT.get("elemental_items", []):
        name, typ, slot, atk, dfn, desc, val, dur = _entry_e["name"], _entry_e["type"], _entry_e["slot"], _entry_e["atk_mult"], _entry_e["def_mult"], _entry_e["description"], _entry_e["value"], _entry_e["durability"]
        items[name] = _make_item(name, typ, slot, atk, dfn, 0, 0, dur, val,
                                 desc, ["elemental","magic"])
    
    # Herbal
    for _entry_h in _SUPPLEMENT.get("herbal_items", []):
        name, typ, wt, val, hp, sp, desc = _entry_h["name"], _entry_h["type"], _entry_h["weight"], _entry_h["value"], _entry_h["heal_hp"], _entry_h["heal_sp"], _entry_h["description"]
        d = {"type": typ, "weight": wt, "value": val, "desc": desc, "tags": ["herbal"]}
        if hp: d["heal_hp"] = abs(hp)
        if sp: d["heal_sp"] = abs(sp)
        items[name] = d
    
    # Junk
    for name in _SUPPLEMENT.get("junk_items", []):
        items[name] = {"type": "junk", "weight": 0.2, "value": 0,
                       "desc": f"一個{name}。", "tags": ["junk"]}
    
    # Card ability items — generate up to 600
    card_item_count = 0
    item_names_set = set(items.keys())
    _cat_item_types = _SUPPLEMENT.get("cat_item_types", {})
    for card in _CHARACTER_CARDS:
        tokens = card.get("tokens", [])
        cid = card.get('card_id','?')
        # Generate items from token categories
        # （排除物種分類 token：分類系譜是描述性資料，不應變成物品）
        for i, t in enumerate(tokens):
            cat = t.get("category","")
            tok_name = t.get("name","")[:15]
            if not tok_name or not cat: continue
            if tok_name in ("分類系譜", "物種分類"):
                continue
            key = f"{cid}:{tok_name}"
            if key in item_names_set or card_item_count >= 2000:
                continue
            item_type = _cat_item_types.get(cat)
            if item_type:
                typ, slot, atk, dfn, spd, krm, dur, val = item_type
                items[key] = _make_item(key, typ, slot, atk, dfn, spd, krm, dur, val,
                                        f"{tok_name}之力", ["card_item", cat])
                item_names_set.add(key)
                card_item_count += 1
        # Generate from abilities too
        for ability in card.get("abilities", []):
            aname = ability.get("name", "")
            if not aname: continue
            key = f"{cid}:{aname}"
            if key in item_names_set or card_item_count >= 2000:
                continue
            items[key] = _make_item(key, "accessory", "neck", 0.1, 0.1, 0.05, 0.15,
                                    50, 80, f"{aname[:15]}", ["card_item", "ability"])
            item_names_set.add(key)
            card_item_count += 1
    
    # Token-generic items from each NPC
    for card in _CHARACTER_CARDS:
        token_cats = {t.get("category") for t in card.get("tokens", [])}
        cid = card.get('card_id','?')
        for cat in token_cats:
            if cat in _cat_item_types and card_item_count < 600:
                key = f"{cid}:{cat}結晶"
                if key not in item_names_set:
                    typ, slot, atk, dfn, spd, krm, dur, val = _cat_item_types[cat]
                    items[key] = _make_item(key, typ, slot, atk, dfn, spd, krm, dur, val,
                                            f"{cat}結晶", ["card_item", cat])
                    item_names_set.add(key)
                    card_item_count += 1
    
    print(f"[game_data] Generated {len(items)} items")
    return items

ALL_ITEMS = generate_all_items()


# ══════════════════════════════════════════════════════════════════
# 8. ENEMY GENERATION — 400+
# ══════════════════════════════════════════════════════════════════

# Animal enemies template (from supplement)
_ANIMAL_ENEMIES_TEMPLATE = _SUPPLEMENT.get("animal_enemies_template", [])


def _generate_enemies_from_template() -> list:
    enemies = []
    for _entry in _ANIMAL_ENEMIES_TEMPLATE:
        name, hp, atk, dfn, spd, exp_, gold, loot, desc, biome = _entry["name"], _entry["base_hp"], _entry["base_atk"], _entry["base_def"], _entry["base_spd"], _entry["exp_mod"], _entry["gold_mod"], _entry["loot"], _entry["desc"], _entry["biome"]
        enemies.append({"name":name,"hp":hp,"atk":atk,"def":dfn,"spd":spd,
                        "exp":exp_,"gold":gold,"loot":list(loot),"desc":desc})
        # Tier 2: stronger variant
        enemies.append({"name":f"凶暴{name}","hp":int(hp*1.8),"atk":int(atk*1.5),"def":int(dfn*1.3),
                        "spd":min(spd+2,15),"exp":int(exp_*1.5),"gold":int(gold*1.5),
                        "loot":list(loot)+(["魔法粉"] if len(loot)<3 else []),"desc":f"兇暴化的{desc}"})
        # Tier 3: elite variant
        enemies.append({"name":f"遠古{name}","hp":int(hp*3.0),"atk":int(atk*2.2),"def":int(dfn*2.0),
                        "spd":min(spd+4,18),"exp":int(exp_*2.5),"gold":int(gold*2.5),
                        "loot":list(loot)+["龍鱗","靈木"],"desc":f"存活於古代的{desc}"})
    return enemies

# Card shadow enemies (from each character card combat tokens)
def _generate_card_enemies() -> list:
    enemies = []
    for card in _CHARACTER_CARDS:
        combat_tokens = _tokens_by_cat(card, "combat")
        # 卡片名可能用全形括號（如「小無（Xiǎ…」）——split("(") 對全形括號無效
        # 會產生「小無（Xiǎ之影」這種缺右括號的壞名字。全形/半形括號都切。
        _raw_name = card.get("name", "?")
        for _sep in ("(", "（", "[", "［"):
            _raw_name = _raw_name.split(_sep)[0]
        name = _raw_name.strip()[:6]
        shadow_name = f"{name}之影"
        base_hp = 45 + len(combat_tokens)*10 if combat_tokens else 40
        base_atk = 14 + len(combat_tokens)*3 if combat_tokens else 12
        base_def = 5 + len(combat_tokens)*2 if combat_tokens else 4
        enemies.append({"name":shadow_name,"hp":base_hp,"atk":base_atk,"def":base_def,
                        "spd":5,"exp":40+len(combat_tokens)*10,"gold":20+len(combat_tokens)*5,
                        "loot":["魔法粉","水晶碎片"],"desc":"從卡片現身的影子"})
        # Stronger variant
        enemies.append({"name":f"深淵{shadow_name}","hp":int(base_hp*2.5),"atk":int(base_atk*2.0),
                        "def":int(base_def*1.8),"spd":8,"exp":int(40+len(combat_tokens)*25),
                        "gold":int(20+len(combat_tokens)*12),"loot":["龍鱗","靈木","魔力藥水"],
                        "desc":"從深淵現身的強大影子"})
    return enemies

# ────────────────────────────────────────────────────────────────
# W03/W04 世界線專屬敵人 — 依《世界線錨定 — 補充欄位》權威表：
#   W04 灰燼紀元（後末日時代，不穩定聚合）：灰燼行者、拾荒王、螢光獵手
#   W03 軌道居住站（宇宙時代，極低聚合）   ：下層工業港機械系
#   Ver 3.1 S07 熒光沼澤：變異兩棲生物（原人類長期暴露熒光沼澤，
#   體型增大 2-3 倍，食物鏈頂端，具攻擊性）
#   Ver 3.1 S08 玻璃荒漠：靈爆中心殘留（>100ppm），舊時代設施封存
# ────────────────────────────────────────────────────────────────
def _generate_world_line_enemies() -> list:
    enemies = []
    # W04 玻璃荒漠 / 鏽蝕城邦 — 靈爆後廢土掠奪者
    enemies.append({"name": "灰燼行者", "hp": 120, "atk": 25, "def": 15, "spd": 7,
                    "exp": 90, "gold": 40, "loot": ["廢鐵", "魔力藥水"],
                    "desc": "靈爆後廢土上遊蕩的灰燼行者"})
    enemies.append({"name": "灰燼行者長", "hp": 200, "atk": 32, "def": 20, "spd": 9,
                    "exp": 150, "gold": 80, "loot": ["廢鐵", "龍鱗", "魔力藥水"],
                    "desc": "灰燼行者中的首領，劫掠廢土聚落"})
    # W04 熒光沼澤 — 變異兩棲生物（世界線錨定實證：螢光獵手）
    enemies.append({"name": "螢光獵手", "hp": 110, "atk": 24, "def": 12, "spd": 10,
                    "exp": 85, "gold": 35, "loot": ["熒光藻", "水晶碎片"],
                    "desc": "長期暴露熒光沼澤的變異兩棲生物，具趨光性與攻擊性"})
    enemies.append({"name": "沼澤變異體", "hp": 180, "atk": 30, "def": 16, "spd": 12,
                    "exp": 140, "gold": 70, "loot": ["熒光藻", "靈木", "水晶碎片"],
                    "desc": "熒光沼澤食物鏈頂端的巨大變異體"})
    # W04 鏽蝕城邦 — 拾荒王（世界線錨定實證）
    enemies.append({"name": "拾荒王", "hp": 230, "atk": 28, "def": 26, "spd": 6,
                    "exp": 170, "gold": 120, "loot": ["廢鐵", "龍鱗", "靈木"],
                    "desc": "鏽蝕城邦的拾荒王，統領廢土拾荒者"})
    # W03 軌道居住站下層工業港 — 機械系（宇宙時代電子環境）
    enemies.append({"name": "站內巡邏無人機", "hp": 70, "atk": 22, "def": 18, "spd": 11,
                    "exp": 75, "gold": 30, "loot": ["廢鐵", "電子零件"],
                    "desc": "軌道居住站下層工業港的巡邏無人機"})
    enemies.append({"name": "軌道站維修機械", "hp": 130, "atk": 18, "def": 28, "spd": 4,
                    "exp": 95, "gold": 45, "loot": ["廢鐵", "電子零件", "護身符"],
                    "desc": "失控的軌道站維修機械，攻擊所有進入工業港的生物"})
    return enemies


# Elemental enemies (from supplement)
_ELEMENTAL_ENEMIES = _SUPPLEMENT.get("elemental_enemies", [])

def generate_all_enemies() -> list:
    enemies = _generate_enemies_from_template()  # 60 enemies
    enemies.extend(_generate_card_enemies())      # ~118 enemies
    enemies.extend(_generate_world_line_enemies())  # W03/W04 專屬
    for entry in _SUPPLEMENT.get("elemental_enemies", []):
        name, hp, atk, dfn, spd, exp_, gold, loot, desc = entry["name"], entry["hp"], entry["atk"], entry["def"], entry["spd"], entry["exp"], entry["gold"], entry["loot"], entry["desc"]
        enemies.append({"name":name,"hp":hp,"atk":atk,"def":dfn,"spd":spd,
                        "exp":exp_,"gold":gold,"loot":list(loot),"desc":desc})
        # Tier 2 for elemental
        enemies.append({"name":f"大{name}","hp":int(hp*2.2),"atk":int(atk*1.8),"def":int(dfn*1.5),
                        "spd":min(spd+2,16),"exp":int(exp_*2),"gold":int(gold*2),
                        "loot":list(loot)+["龍鱗"],"desc":f"強大的{desc}"})
    return enemies

ALL_ENEMIES = generate_all_enemies()
# Should be ~60 + ~118 + 20 = ~198 enemies


# ══════════════════════════════════════════════════════════════════
# 9. LOCATION GENERATION
# ══════════════════════════════════════════════════════════════════

def generate_locations() -> dict:
    locs = {}
    for card in _SCENE_CARDS:
        sid = card.get("card_id","S??")
        raw_loc_name = card.get("name","?").split("·")[-1].strip()
        if not raw_loc_name or len(raw_loc_name) > 8:
            # 名稱含括號描述（如「（夢境層）」）或過長時：取括號前完整基底名
            #——不再 [:8] 強制截斷（會砍掉完整名尾巴，如 聖十字環形堡壘校園→校）
            raw_loc_name = card.get("name","?").split("（")[0].split("(")[0].strip()
        # Fix empty names: use lore token value as fallback
        lore_toks_for_loc = _tokens_by_cat(card, "lore")
        if not raw_loc_name or raw_loc_name == '?':
            lore_fallback = ""
            for t in lore_toks_for_loc:
                v = t.get("value","")[:15]
                if v: lore_fallback = v; break
            name = lore_fallback if lore_fallback else f"未命名場景({sid})"
        else:
            name = raw_loc_name
        lore_tokens = _tokens_by_cat(card, "lore")
        vibe = "📍 未知之地"
        for t in lore_tokens:
            v = t.get("value","")
            if "校園" in v or "教室" in v: vibe = "📚 求學之地"
            elif "湖" in v or "水" in v: vibe = "💧 水邊"
            elif "市" in v or "市場" in v: vibe = "🏪 熱鬧市集"
            elif "地下" in v or "洞" in v: vibe = "🕳 地下"
            elif "空" in v or "星" in v: vibe = "✨ 星空"
        locs[sid] = {"name":name,"vibe":vibe,"card_id":sid}
    return locs

ALL_LOCATIONS = generate_locations()


# ══════════════════════════════════════════════════════════════════
# 10. QUEST GENERATION — use ALL 76 story nodes
# ══════════════════════════════════════════════════════════════════

def generate_quests() -> list:
    quests = []
    locations_pool = ["聖十字校園","鏡湖","鬱鬱山","卡洛夫角","霧海群島",
                      "秘密鐵工廠","便利店","英靈殿","廢棄礦坑","森林深處","煙雲溫泉湖","清溪河","鏡山"]
    
    # From all story nodes
    npc_names = list(ALL_NPCS.keys())
    for i, card in enumerate(_STORY_CARDS):
        raw_name = card.get("name","?").split("（")[0].strip()[:20]
        lore_tokens = _tokens_by_cat(card, "lore")
        story = ""
        for t in lore_tokens:
            v = t.get("value","")
            story = v[:60]
        if not story: story = f"調查關於{raw_name}的線索。"
        # Fix empty names: use first lore token value as fallback
        if not raw_name or raw_name == '?':
            lore_fallback = ""
            for t in lore_tokens:
                lore_fallback = t.get("value","")[:20]
                if lore_fallback: break
            name = lore_fallback if lore_fallback else f"未命名EP({i+1})"
        else:
            name = raw_name
        loc_target = _seed.choice(locations_pool)
        qtype = "main" if i < 15 else "side"
        qid = f"SN-{i+1:02d}"
        reward_exp = 20 + i * 3
        reward_gold = 8 + i * 2
        # Add conditions with level requirement scaling with index
        req_level = max(1, i // 15)  # later nodes require higher level
        q = {
            "id": qid, "title": name[:20], "type": qtype,
            "giver": _seed.choice(npc_names),
            "desc": story[:80],
            "conditions": {
                "required_level": req_level,
                "time_available": {"start_hour": 0, "end_hour": 24},
            },
            "objectives": [
                {"type":"visit","target":loc_target,"detail":f"前往{loc_target}"},
                {"type":"collect","target":_seed.choice(["水晶碎片","鐵礦","魔法粉","靈木","草藥","皮革"]),
                 "qty":_seed.randint(1,3),"detail":"收集指定物品"},
            ],
            "reward_exp": reward_exp, "reward_gold": reward_gold,
            "reward_reputation": max(2, i // 10),
            "reward_item": _seed.choice(["治療藥水","鐵劍","護身符","鋼刀","記憶水晶","皮甲","斗篷","匕首","靈力藥","生命果"]),
        }
        quests.append(q)
    
    # NPC-generated quests (with conditions based on NPC attributes)
    for i, (npc_name, npc_data) in enumerate(ALL_NPCS.items()):
        if npc_data.get("gives_quests") and i < 60:
            cats = npc_data.get("token_categories", [])
            loc = npc_data.get("location", "聖十字校園")
            qid = f"NPC-{i+1:02d}"
            req_rel = {npc_name: 20 + _seed.randint(0, 20)}
            conditions = {
                "required_relationships": req_rel,
                "time_available": {"start_hour": 8, "end_hour": 20},
            }
            if "craft" in cats:
                quests.append({"id":qid,"title":f"{npc_name}的委託","type":"side","giver":npc_name,
                    "desc":"需要你幫忙收集材料。",
                    "conditions": dict(conditions),
                    "objectives":[{"type":"collect","target":_seed.choice(["鐵礦","皮革","靈木","草藥"]),"qty":_seed.randint(2,5),"detail":"收集材料"}],
                    "reward_exp":30+_seed.randint(0,30),"reward_gold":15+_seed.randint(0,20),
                    "reward_reputation":5,"reward_relationships":{npc_name: 10},
                    "reward_item":_seed.choice(["治療藥水","匕首","鐵劍","護身符","皮甲"])})
            elif "combat" in cats:
                conditions["required_level"] = 3
                # 目標敵人從該 NPC 家所在地的敵人群選，確保任務可完成
                # （固定清單會選出目標地點根本不存在的敵人，造成任務卡死）
                import sim_systems as _ss
                loc_pool = list(_ss.LOCATION_ENEMIES.get(loc, []))
                # 排除強敵：前綴（凶暴/遠古/深淵）或數值超標（ATK≥20 或 HP≥90）
                # ——Lv3 討伐任務不該要求打古代守衛/巨熊/元素核心等無前綴強敵
                _enemy_by_name = {e["name"]: e for e in _ss.ENEMIES}
                def _too_strong(n):
                    if any(k in n for k in ("遠古","凶暴","兇暴","深淵")):
                        return True
                    e = _enemy_by_name.get(n)
                    return bool(e and (e.get("atk", 0) >= 20 or e.get("hp", 0) >= 90))
                _plain = [n for n in loc_pool if not _too_strong(n)]
                _target_pool = _plain or loc_pool
                if not _target_pool:
                    # 該地點沒有敵人群：退而求其次，改為收集任務而非討伐
                    quests.append({"id":qid,"title":f"{npc_name}的委託","type":"side","giver":npc_name,
                        "desc":"需要你幫忙收集材料。",
                        "conditions": dict(conditions),
                        "objectives":[{"type":"collect","target":_seed.choice(["鐵礦","皮革","靈木","草藥"]),"qty":_seed.randint(2,5),"detail":"收集材料"}],
                        "reward_exp":30+_seed.randint(0,30),"reward_gold":15+_seed.randint(0,20),
                        "reward_reputation":5,"reward_relationships":{npc_name: 10},
                        "reward_item":_seed.choice(["治療藥水","匕首","鐵劍","護身符","皮甲"])})
                else:
                    target_enemy = _seed.choice(_target_pool)
                    quests.append({"id":qid,"title":f"{npc_name}的討伐","type":"side","giver":npc_name,
                        "desc":"附近的敵人需要討伐。",
                        "conditions": dict(conditions),
                        "objectives":[{"type":"visit","target":loc,"detail":f"前往{loc}"},
                                      {"type":"defeat","target":target_enemy,"qty":_seed.randint(1,3),"detail":"擊敗指定敵人"}],
                        "reward_exp":40+_seed.randint(0,40),"reward_gold":20+_seed.randint(0,30),
                        "reward_reputation":8,"reward_relationships":{npc_name: 12},
                        "reward_item":_seed.choice(["鋼刀","鐵甲","生命果","火焰藥水","靈力藥"])})
            elif "knowledge" in cats:
                quests.append({"id":qid,"title":f"{npc_name}的探索","type":"side","giver":npc_name,
                    "desc":"探索並帶回見聞。",
                    "conditions": dict(conditions),
                    "objectives":[{"type":"visit","target":_seed.choice(["聖十字校園","英靈殿","森林深處"]),"detail":"前往指定地點"}],
                    "reward_exp":25+_seed.randint(0,25),"reward_gold":10+_seed.randint(0,15),
                    "reward_reputation":6,"reward_relationships":{npc_name: 10},
                    "reward_item":_seed.choice(["記憶水晶","神秘地圖","書信","魔力藥水","護身符"])})

    print(f"[game_data] Generated {len(quests)} quests")
    return quests

ALL_QUESTS = generate_quests()


# ══════════════════════════════════════════════════════════════════
# 11. SCENE OBJECT GENERATION — 200+
# ══════════════════════════════════════════════════════════════════

_LOCATIONS_FOR_OBJECTS = _SUPPLEMENT.get("locations_for_objects", [])

def generate_scene_objects() -> Dict[str, list]:
    objects = {}
    container_pool = [
        (["草藥","空瓶","小石頭"],"木箱","木箱"),
        (["魔法粉","水晶碎片","靈木"],"魔法箱","發光箱"),
        (["乾糧","治療藥水","繃帶"],"保管箱","應急箱"),
        (["鐵礦","黏土","樹枝"],"礦石箱","礦石箱"),
        (["書信","羽毛","貝殼"],"小箱","帶鎖小箱"),
        (["皮革","布","絲線"],"材料箱","素材箱"),
        (["火元素","空瓶","蠟燭頭"],"實驗箱","實驗箱"),
        (["古代硬貨","記憶水晶","神秘地圖"],"舊箱","遠古之箱"),
        (["靈木","龍鱗","魔法粉"],"貴重品箱","貴重品箱"),
        (["草藥","解毒草","靈芝"],"藥箱","藥箱"),
        (["木柄","鐵礦","麻繩"],"道具箱","道具箱"),
        (["治療藥水","火焰藥水","魔力藥水"],"藥品棚","藥品棚"),
        (["乾燥花","彩色玻璃片","貝殼"],"裝飾箱","飾品箱"),
        (["鐵錠","鐵礦","鐵劍"],"武器箱","武器箱"),
        (["書信","神秘地圖","乾燥花"],"信件箱","書信箱"),
    ]
    deco_pool = [
        "看板","長椅","街燈","雕像","花壇","旗幟","噴水池","水井",
        "告示板","鐘樓","吊橋","鳥籠","營火遺跡","石牆","城門",
    ]
    ws_pool = [("鍛造台","forge"),("作業台","workbench"),("鍊金釜","alchemy"),
               ("魔法陣","enchant"),("雕刻台","carve"),("調合台","blend")]
    
    for loc in _SUPPLEMENT.get("locations_for_objects", []):
        loc_objs = []
        # 2-3 containers
        for _ in range(_seed.randint(2,3)):
            ct = _seed.choice(container_pool)
            items, cname, cdesc = ct
            cid = f"box_{loc}_{len(loc_objs)}"
            loc_objs.append({"id":cid,"name":f"{cname}({loc[:2]})","type":"container",
                             "desc":cdesc,"contents":_seed.sample(items,min(3,len(items))),
                             "locked":_seed.random()<0.15,"interactable":True})
        # 1-2 decorations
        for _ in range(_seed.randint(1,2)):
            d = _seed.choice(deco_pool)
            loc_objs.append({"id":f"dec_{loc}_{len(loc_objs)}","name":d,"type":"decoration",
                             "desc":f"一個{d}。","note":"沒有特別之處。","interactable":True})
        # 0-1 workstation
        if _seed.random() < 0.5:
            ws = _seed.choice(ws_pool)
            loc_objs.append({"id":f"ws_{loc}","name":ws[0],"type":"workstation",
                             "desc":f"{ws[0]}。","station_type":ws[1],"interactable":True})
        objects[loc] = loc_objs
    return objects

ALL_SCENE_OBJECTS = generate_scene_objects()


# ══════════════════════════════════════════════════════════════════
# 12. RECIPE GENERATION
# ══════════════════════════════════════════════════════════════════

def generate_recipes() -> list:
    recipes = []
    item_names = list(ALL_ITEMS.keys())
    # 配方材料：beast/natural/elemental/herb 標籤皆可當材料（含野獸掉落物如狼王毛皮/熊之臂力），
    # 唯獨排除 naval 軍武（砲/魚雷/戰鬥機）——軍武不應成為其他物品的製作材料
    material_tags = [k for k, v in ALL_ITEMS.items()
                     if v.get("tags") and "naval" not in v["tags"]
                     and ("beast" in v["tags"] or "natural" in v["tags"]
                          or "elemental" in v["tags"] or "herb" in v["tags"])]
    weapon_types = [k for k, v in ALL_ITEMS.items() if v.get("type") == "weapon"]
    consumable_types = [k for k, v in ALL_ITEMS.items() if v.get("type") == "consumable"]
    
    # Generate up to 400 recipes
    used_pairs = set()
    for i, name in enumerate(item_names[:1000]):
        if i >= 400: break
        item = ALL_ITEMS[name]
        if item["type"] in ("junk",) or not item.get("tags"):
            continue
        # 軍武（naval）只能從商店/掉落/任務獲得，不可合成（避免野獸材料造砲的荒謬配方）
        if "naval" in item.get("tags", []):
            continue
        result_val = ALL_ITEMS[name].get("value", 0)
        # 配方經濟學：材料總成本不得超過結果價值（合成至少打平，不做虧本生意）
        if result_val <= 0:
            continue
        if item["type"] not in ("material", "ingredient", "consumable", "weapon", "armor", "accessory"):
            continue
        cheap_mats = [m for m in material_tags if m != name
                      and ALL_ITEMS[m].get("value", 0) <= result_val]
        if len(cheap_mats) < 2:
            continue
        mat = _seed.sample(cheap_mats, min(3, len(cheap_mats)))
        if len(mat) < 2: continue
        pair_key = tuple(sorted(mat[:2]))
        if pair_key in used_pairs: continue
        used_pairs.add(pair_key)
        q1, q2 = _seed.randint(1, 2), _seed.randint(1, 2)
        cost = ALL_ITEMS[mat[0]].get("value", 0) * q1 + ALL_ITEMS[mat[1]].get("value", 0) * q2
        if cost > result_val:
            continue
        cat_choices = ["craft","alchemize","process","combine"]
        cat = _seed.choice(cat_choices)
        recipes.append({
            "recipe_id": f"GD-{i+1:04d}",
            "name": f"{name[:12]}製作",
            "category": cat,
            "ingredients": [{"item": mat[0], "quantity": q1},
                           {"item": mat[1], "quantity": q2}],
            "result_item": name, "result_quantity": 1,
            "failure_chance": round(_seed.uniform(0.05, 0.35), 2),
        })
    
    # Potion recipes (consumable + material)
    # 藥水材料只用自然/植物/元素類的低價材料（排除 naval 軍武與高價野獸掉落物
    # ——狼王毛皮/熊之臂力不應成為藥水材料，也不該讓藥水配方虧本）
    potion_materials = [k for k, v in ALL_ITEMS.items()
                        if v.get("tags") and ("natural" in v["tags"] or "elemental" in v["tags"]
                        or "herb" in v["tags"])
                        and v.get("type") in ("material", "ingredient", "consumable")
                        and v.get("value", 0) <= 60]
    if not potion_materials:
        potion_materials = ["草藥", "靈木", "魔法粉"]
    # 材料價值查詢：ALL_ITEMS 與 sim_systems.ITEM_CATALOG 合併（fallback 材料在 ITEM_CATALOG）
    import sim_systems as _ss
    _value_of = {**{k: (v.get("value") or 0) for k, v in ALL_ITEMS.items()},
                 **{k: (v.get("value") or 0) for k, v in _ss.ITEM_CATALOG.items()}}
    _ctype_val = lambda c: _value_of.get(c, 0)
    for i, ctype in enumerate(consumable_types):
        # 排除自指（材料=結果，避免「治療藥水調合：治療藥水 x2」的荒謬配方）
        _pool = [m for m in potion_materials if m != ctype] or potion_materials
        if not _pool:
            continue
        ctype_val = _ctype_val(ctype)
        # 低價值消耗品（艾草/薄荷/蒲公英等路邊採集物）不值得煉製——直接跳過
        if ctype_val < 40:
            continue
        # 材料成本必須 ≤ 結果價值×1.5，避免虧本配方（無誘因的合成）
        _cheap = [m for m in _pool if _value_of.get(m, 0) <= ctype_val * 1.5]
        if not _cheap:
            continue
        mat = _seed.choice(_cheap)
        aux = _seed.choice(["空瓶","魔法粉","靈木"])
        aux_val = _value_of.get(aux, 0) or 1
        q_mat = _seed.randint(1, 2)
        cost = _value_of.get(mat, 0) * q_mat + aux_val
        if cost > ctype_val * 1.5:
            continue
        rid = f"GD-POT{i+1:04d}"
        recipes.append({
            "recipe_id": rid, "name": f"{ctype[:10]}調合",
            "category": "alchemize",
            "ingredients": [{"item": mat, "quantity": q_mat},
                           {"item": aux, "quantity": 1}],
            "result_item": ctype, "result_quantity": _seed.randint(1,2),
            "failure_chance": round(_seed.uniform(0.1, 0.3), 2),
        })
    
    print(f"[game_data] Generated {len(recipes)} recipes")
    return recipes

ALL_RECIPES = generate_recipes()


# ══════════════════════════════════════════════════════════════════
# 13. VEHICLES
# ══════════════════════════════════════════════════════════════════

ALL_VEHICLES = {
    "自行車":{"speed":1.5,"capacity":1,"cargo":20,"fuel":"human","desc":"輕快的自行車"},
    "登山自行車":{"speed":1.8,"capacity":1,"cargo":15,"fuel":"human","desc":"善於越野的自行車"},
    "馬":{"speed":2.0,"capacity":1,"cargo":30,"fuel":"feed","desc":"駿馬"},
    "駿馬":{"speed":2.5,"capacity":1,"cargo":25,"fuel":"feed","desc":"純血的駿馬"},
    "馬車":{"speed":1.2,"capacity":3,"cargo":100,"fuel":"feed","desc":"荷馬車"},
    "大型馬車":{"speed":1.0,"capacity":5,"cargo":300,"fuel":"feed","desc":"大型運輸馬車"},
    "小舟":{"speed":1.3,"capacity":2,"cargo":15,"fuel":"human","desc":"渡河的小舟"},
    "漁船":{"speed":1.5,"capacity":4,"cargo":100,"fuel":"sail","desc":"捕魚用的船"},
    "機車":{"speed":2.5,"capacity":1,"cargo":10,"fuel":"gas","desc":"快速的二輪車"},
    "重型機車":{"speed":2.8,"capacity":2,"cargo":20,"fuel":"gas","desc":"大型二輪車"},
    "吉普車":{"speed":2.0,"capacity":4,"cargo":200,"fuel":"gas","desc":"越野走破車"},
    "帆船":{"speed":1.8,"capacity":6,"cargo":500,"fuel":"wind","desc":"帆船"},
    "大型帆船":{"speed":2.0,"capacity":12,"cargo":1200,"fuel":"wind","desc":"大型帆船"},
    "熱氣球":{"speed":1.5,"capacity":3,"cargo":50,"fuel":"fire","desc":"飛行的熱氣球"},
    "蒸氣機車":{"speed":3.0,"capacity":10,"cargo":1000,"fuel":"coal","desc":"蒸氣機車（軌道限定）"},
    "魔法掃帚":{"speed":2.8,"capacity":1,"cargo":5,"fuel":"magic","desc":"魔女的掃帚"},
    "魔法飛毯":{"speed":3.0,"capacity":2,"cargo":30,"fuel":"magic","desc":"飛行的飛毯"},
    "飛空艇":{"speed":2.5,"capacity":8,"cargo":800,"fuel":"magic","desc":"魔導飛空艇"},
    "龍騎乘":{"speed":3.5,"capacity":1,"cargo":10,"fuel":"bond","desc":"與龍的羈絆翱翔天際"},
    "雪橇":{"speed":1.8,"capacity":2,"cargo":40,"fuel":"dog","desc":"狗拉雪橇"},
}


# ══════════════════════════════════════════════════════════════════
# 14. REAL ESTATE
# ══════════════════════════════════════════════════════════════════

ALL_REAL_ESTATE = {
    # 地點依名稱/描述與地圖場景對應（湖畔工房/圖書室/廢坑倉庫/聖十字校園小屋
    # 與 sim_systems 手寫房地產重複，不再生成）
    "卡洛夫商店":{"type":"shop","price":800,"functions":["trade"],"desc":"市集小店鋪","location":"卡洛夫角"},
    "燈塔":{"type":"house","price":1500,"functions":["rest","study"],"desc":"眺望大海的燈塔","location":"卡洛夫角"},
    "森林小屋":{"type":"house","price":900,"functions":["rest","store"],"desc":"森林中的隱居小屋","location":"森林深處"},
    "展望台":{"type":"tower","price":2500,"functions":["study","rest"],"desc":"觀星用的展望台","location":"鏡山"},
    "鏡湖別莊":{"type":"house","price":3000,"functions":["rest","craft","store"],"desc":"鏡湖畔的別莊","location":"鏡湖"},
    "工房擴建":{"type":"workshop","price":1800,"functions":["craft","store"],"desc":"工房的擴建區","location":"聖十字校園"},
    "秘密藏身處":{"type":"house","price":1500,"functions":["rest","store"],"desc":"祕密的藏身處","location":"秘密鐵工廠"},
    "市集倉庫":{"type":"warehouse","price":400,"functions":["store"],"desc":"市集的小倉庫","location":"西翼大市集"},
    "海岸小屋":{"type":"house","price":1200,"functions":["rest"],"desc":"海岸邊的小屋","location":"霧海南岸"},
    "魔法塔":{"type":"tower","price":5000,"functions":["study","craft","rest"],"desc":"魔力匯聚的塔","location":"魔女學府"},
    "古道旅店":{"type":"house","price":800,"functions":["rest","store"],"desc":"古道旁的旅店","location":"卡洛夫山脈"},
    "英靈祠":{"type":"shrine","price":3000,"functions":["rest","study"],"desc":"供奉英靈的祠堂","location":"英靈殿"},
    "大樹之家":{"type":"house","price":2000,"functions":["rest","store","craft"],"desc":"建在大樹上的家","location":"綻放混成園"},
    "礦山公社":{"type":"warehouse","price":1000,"functions":["store"],"desc":"礦山的行政辦公室","location":"廢棄礦坑"},
    "天空豪宅":{"type":"house","price":4000,"functions":["rest","study","craft"],"desc":"高台上的豪宅","location":"霧海群島"},
}


# ══════════════════════════════════════════════════════════════════
# 15. DIALOGUE GENERATION
# ══════════════════════════════════════════════════════════════════

def generate_npc_dialogues() -> Dict[str, list]:
    dialogues = {}
    for name, npc_data in ALL_NPCS.items():
        cats = npc_data.get("token_categories", [])
        lines = [npc_data.get("greeting", "「你好啊。」")]
        if "combat" in cats: lines.extend(["「戰鬥的話就交給我吧。」","「實戰才是最好的老師。」","「武器的保養很重要。」"])
        if "craft" in cats: lines.extend(["「要我幫你做點什麼嗎？」","「只要有材料，什麼都能做出來。」","「讓你看見工匠的手藝。」"])
        if "knowledge" in cats: lines.extend(["「來聊聊我所知道的吧。」","「知識就是力量。」","「多讀點書準沒錯。」"])
        if "social" in cats: lines.extend(["「願意陪我說說話嗎？」","「今天天氣真不錯呢。」","「要一起吃飯嗎？」"])
        if "element" in cats: lines.extend(["「我能感受到元素的力量……」","「自然的能量正滿溢而出。」","「元素的平衡非常重要。」"])
        if "energy" in cats: lines.extend(["「靈力正充盈著呢。」","「我能感受到氣的流動。」","「幫能量充個電吧。」"])
        if "lore" in cats: lines.extend(["「想聽聽古老的故事嗎？」","「這片土地流傳著古老的傳說。」","「歷史總是不斷重演。」"])
        if "exploration" in cats: lines.extend(["「我們去探索新的地方吧。」","「把地圖拿來給我看。」","「荒野中飄散著冒險的氣息。」"])
        lines.append("「下次再見。」")
        # Add random flavor
        flavors = [f"「{name}微微笑了。」",f"「{name}若有所思地沉思著。」",f"「{name}眺望著遠方。」"]
        lines.extend(flavors)
        dialogues[name] = lines
    return dialogues

ALL_DIALOGUES = generate_npc_dialogues()


# ══════════════════════════════════════════════════════════════════
# INTEGRATION — merge game_data into sim_systems
# ══════════════════════════════════════════════════════════════════

def expand_game():
    import sim_systems
    
    cnt = {"items":0,"enemies":0,"enemy_dist":0,"npcs":0,"quests":0,
           "vehicles":0,"estate":0,"objs":0,"recipes":0}
    
    # Items
    for k, v in ALL_ITEMS.items():
        if k not in sim_systems.ITEM_CATALOG:
            sim_systems.ITEM_CATALOG[k] = v
            cnt["items"] += 1

    # 世界線材料：W03/W04 敵人的 loot（依 S07 熒光沼澤「藻類可提煉
    # 低級乙太燃料」、W03 下層工業港電子環境）。補進目錄避免掉落
    # 顯示不存在的道具。
    for _iname, _idata in (
        ("熒光藻", {"type": "material", "weight": 0.1, "value": 30,
                     "tags": ["herbal", "alchemy"],
                     "desc": "熒光沼澤的發光藻類，可提煉低級乙太燃料"}),
        ("電子零件", {"type": "material", "weight": 0.3, "value": 45,
                       "tags": ["tech"],
                       "desc": "軌道居住站的精密電子零件"}),
        ("廢鐵", {"type": "material", "weight": 2.0, "value": 12,
                   "tags": ["junk", "metal"],
                   "desc": "鏽蝕的廢鐵，熔煉後可再利用"}),
        ("木材", {"type": "material", "weight": 1.0, "value": 15,
                   "tags": ["wood", "material"],
                   "desc": "未加工的木頭，建築與製作材料"}),
    ):
        if _iname not in sim_systems.ITEM_CATALOG:
            sim_systems.ITEM_CATALOG[_iname] = _idata
            cnt["items"] += 1

    # NPC 個人商店道具補齊移至 expand_game 尾部（NPC_METADATA 建立之後執行）：
    # 卡片 NPC 的 offers 引用大量語境道具（義體/艦娘/符文/神話/廢土/極地等），
    # 這些必須存在於 ITEM_CATALOG，個人商店才能販賣。手寫覆寫優先（世界線
    # 分類正確），其餘規則化生成。
    
    # Enemies
    existing_e = {e["name"] for e in sim_systems.ENEMIES}
    for e in ALL_ENEMIES:
        if e["name"] not in existing_e:
            sim_systems.ENEMIES.append(e)
            existing_e.add(e["name"])

    # 森林系敵人補木材掉落（SQ-09「收集材料」需木材×3，先前木材 0 掉落
    # → 任務永不可完成）。依常理：木柄/木製武器的敵人（哥布林）與
    # 森林棲息生物（森狼/野豬/巨熊/大鹿/虎）都可能攜帶或留下木材。
    _WOOD_ENEMY_KEYS = ("哥布林", "森狼", "野豬", "巨熊", "大鹿", "虎",
                        "狼", "樹精", "木乃", "野人")
    for e in sim_systems.ENEMIES:
        _loot = list(e.get("loot", []) or [])
        if "木材" in _loot:
            continue
        if any(_k in e["name"] for _k in _WOOD_ENEMY_KEYS):
            e["loot"] = _loot + ["木材"]
        
    # ════════════════════════════════════════════════
    # Card system integration: ORG/NAT/RC
    # ════════════════════════════════════════════════
    # FACTIONS/NATIONS 由 sim_systems 基底提供（名稱與描述已正確），不再覆寫。
    
    # Rules (from RC cards)
    _new_rules = {
  "RC-01": {
    "name": "迴廊 (The Corridor)",
    "lore": "連接多元宇宙各個世界線的「橋樑」，由概念、數據流、意識碎片和世界法則交織而成的虛無維度",
    "mechanism": "資訊與邏輯概念匯聚之地"
  },
  "RC-02": {
    "name": "未命名規則(RC-02)",
    "lore": "",
    "mechanism": "使用D12，預見的本質不穩定，波動較小"
  },
  "RC-03": {
    "name": "未命名規則(RC-03)",
    "lore": "",
    "mechanism": "使用D20"
  },
  "RC-05": {
        "name": "聖十字校園 · 地下遺跡深層休眠區",
    "lore": "迴廊（The Corridor）· 物語核（RC-02）邊緣",
    "mechanism": ""
  },
  "RC-06": {
    "name": "森幽小徑（Shadow-wood Pathway）",
    "lore": "迴廊 · 物語核邊緣",
    "mechanism": ""
  },
  "RC-07": {
    "name": "暈輝湖（Glow-water Cavity）",
    "lore": "迴廊 · 物語核邊緣",
    "mechanism": ""
  },
  "RC-08": {
    "name": "阿拉克涅小鎮（Arachne Town）",
    "lore": "迴廊 · 物語核邊緣",
    "mechanism": ""
  },
  "RC-09": {
    "name": "拉米雅小鎮（Lamia Town）",
    "lore": "迴廊 · 物語核邊緣",
    "mechanism": ""
  },
  "RC-10": {
        "name": "聖十字校園 · 地下市集區（Trade Bazaar）",
    "lore": "迴廊 · 物語核邊緣",
    "mechanism": ""
  },
  "RC-11": {
    "name": "概念學術高等學校（The Academy）",
    "lore": "迴廊 · 物語核邊緣",
    "mechanism": ""
  },
  "RC-12": {
    "name": "蝠群襲掠婚規則（Bat Flock Raid-Wedding Code）",
    "lore": "W01 靈子塵埃（煦掠族群）",
    "mechanism": "透過「捕食儀式化」篩選具備警覺性與回應意願的伴侶"
  },
  "RC-13": {
    "name": "至高神祇命名混合算法（Theonymic Blending Algorithm）",
    "lore": "W01 靈子塵埃（神話層）",
    "mechanism": "將神祇在不同文化與時期的稱呼「碎片」透過演算法混合為全名，並簡化為日常使用姓名。"
  },
  "RC-14": {
    "name": "神祇召喚全名吟唱規則（Theonymic Invocation Rule）",
    "lore": "跨世界線（適用於W01神話層及任何存在「全名」的高位存在）",
    "mechanism": "將「召喚神祇」從單純的擲骰判定，轉變為需要玩家「實際唸出全名」的表演環節，增加遊戲的荒誕性與儀式感"
  },
  "RC-15": {
    "name": "鼠立方（Rodent Cube）",
    "lore": "W01 靈子塵埃",
    "mechanism": ""
  },
  "RC-16": {
    "name": "黑帆掠奪者（Black Sail Reaver）",
    "lore": "W01 靈子塵埃",
    "mechanism": ""
  }
}
    for _rid, _rdata in _new_rules.items():
        if _rid not in sim_systems.ACTIVE_RULES:
            sim_systems.ACTIVE_RULES[_rid] = _rdata
    

    # Assign NPC affiliations based on relation tokens
    # (Injects org info into NPC data where relation tokens exist)
    _npc_faction_map = {}
    for card in _CHARACTER_CARDS:
        raw_name = card.get('name','?').split('(')[0].strip()
        if not raw_name: raw_name = '?'
        _candidates = []
        if raw_name in ALL_NPCS:
            _candidates.append(raw_name)
        else:
            for an in ALL_NPCS:
                if raw_name and (raw_name in an or an[:max(2,len(raw_name))] == raw_name[:max(2,len(raw_name))]):
                    _candidates.append(an)
        relation_tokens = [t for t in card.get('tokens',[]) if t.get('category')=='relation']
        for rt in relation_tokens:
            rel_name = rt.get('name','')
            for ocid, odata in sim_systems.FACTIONS.items():
                fname = odata.get('name','').lower()
                if rel_name.lower() in fname or fname in rel_name.lower():
                    for cn in _candidates:
                        _npc_faction_map[cn] = ocid
                    break
    
    # Assign factions from mapping
    if not hasattr(sim_systems, 'NPC_FACTIONS'):
        sim_systems.NPC_FACTIONS = {}
    for npc_name, ocid in _npc_faction_map.items():
        sim_systems.NPC_FACTIONS[npc_name] = ocid
    
    # Location-based fallback for ALL NPCs
    _loc_to_faction = {}
    for lid, lv in sim_systems.FACTIONS.items():
        fl = (str(lv.get('lore','')) + str(lv.get('name',''))).lower()
        for loc in sim_systems.WORLD_MAP:
            ll = loc.lower()
            if len(ll) >= 2 and ll[:2] in fl:
                _loc_to_faction[loc] = lid
                break
    # Fallback: assign faction based on NPC home location
    for npc_name in list(ALL_NPCS.keys()):
        if npc_name not in sim_systems.NPC_FACTIONS:
            nl = ALL_NPCS.get(npc_name, {}).get('location', '')
            if nl in _loc_to_faction:
                sim_systems.NPC_FACTIONS[npc_name] = _loc_to_faction[nl]
    # Additional fallback: use LOCATION_NATIONS for faction assignment
    if not sim_systems.NPC_FACTIONS or len(sim_systems.NPC_FACTIONS) == 0:
        _loc_to_nat = getattr(sim_systems, "LOCATION_NATIONS", {}) or {}
        for npc_name in list(ALL_NPCS.keys()):
            if npc_name not in sim_systems.NPC_FACTIONS:
                nl = ALL_NPCS[npc_name].get("location", "")
                nat_id = _loc_to_nat.get(nl) if isinstance(_loc_to_nat, dict) else None
                if nat_id and hasattr(sim_systems, "NATIONS"):
                    nn = str(sim_systems.NATIONS.get(nat_id, {}).get("name", "")).lower()
                    for fid, fv in sim_systems.FACTIONS.items():
                        fn = str(fv.get("name", "")).lower()
                        if fn and nn and (fn[:4] in nn or nn[:4] in fn):
                            sim_systems.NPC_FACTIONS[npc_name] = fid
                            break
    
    # Assign territory to locations from NAT cards
    # Simple approach: assign nations to locations based on lore keywords
    _loc_nation_map = {}
    for loc_name in list(sim_systems.WORLD_MAP.keys()):
        for nid, ndata in sim_systems.NATIONS.items():
            ndesc = ndata.get('lore','') + ndata.get('name','')
            # Very simple heuristic: check if location appears in nation lore
            if len(loc_name) >= 2 and any(sub in ndesc for sub in [loc_name, loc_name[::-1][:4], loc_name[:4]]):
                _loc_nation_map[loc_name] = nid
                break
    # Always assign when we have data (placeholder exists but is empty)
    if not sim_systems.LOCATION_NATIONS:
        sim_systems.LOCATION_NATIONS = _loc_nation_map
    
    # Track which rules are active at which locations
    _loc_rules = {}
    for loc_name in list(sim_systems.WORLD_MAP.keys()):
        for rid, rdata in sim_systems.ACTIVE_RULES.items():
            rdesc = rdata.get('lore','') + rdata.get('name','')
            if len(loc_name) >= 2 and any(sub in rdesc for sub in [loc_name, loc_name[::-1][:4], loc_name[:4]]):
                if loc_name not in _loc_rules:
                    _loc_rules[loc_name] = []
                _loc_rules[loc_name].append(rid)
    if not sim_systems.LOCATION_RULES:
        sim_systems.LOCATION_RULES = _loc_rules
    
    # Fallback: use location vibes to assign nations
    if not _loc_nation_map or not any(v for v in _loc_nation_map.values()):
        if hasattr(sim_systems, "LOCATION_VIBES"):
            _vibe_to_nation = {
                '\U0001f33e': 'NAT-06',  # 🌾 EAR OF RICE -> 聖十字校園
                '\U0001f4a7': 'NAT-06',  # 💧 DROPLET -> 鏡湖
                '\U0001f3ea': 'NAT-04',  # 🏪 CONVENIENCE STORE -> 卡洛夫角, 便利店
                '\U0001f4da': 'NAT-02',  # 📚 BOOKS -> 聖十字校園
                '\U0001f30a': 'NAT-06',  # 🌊 WATER WAVE -> 卡洛夫角
                '\U0001f527': 'NAT-05',  # 🔧 WRENCH -> 秘密鐵工廠
                '\U00002694': 'NAT-05',  # ⚔ CROSSED SWORDS -> 英靈殿
                '\U000026cf': 'NAT-05',  # ⛏ PICK -> 廢棄礦坑
                '\U0001f332': 'NAT-03',  # 🌲 EVERGREEN TREE -> 森林深處
            }
            for loc_name in sim_systems.WORLD_MAP:
                if loc_name not in _loc_nation_map or not _loc_nation_map.get(loc_name):
                    vibe = sim_systems.LOCATION_VIBES.get(loc_name, "")
                    for vibe_emoji, nid in _vibe_to_nation.items():
                        if vibe_emoji in vibe:
                            _loc_nation_map[loc_name] = nid
                            break
    print(f"[game_data] Factions: {len(sim_systems.FACTIONS)}, Nations: {len(sim_systems.NATIONS)}, Rules: {len(sim_systems.ACTIVE_RULES)}")
    
    # Skills (from SK-01~SK-22)
    sim_systems.ALL_SKILLS = ALL_SKILLS
    print(f"[game_data] Skills: {len(ALL_SKILLS)}")
    
    # Storyline quests (from SL cards)
    existing_qids = {q["id"] for q in sim_systems.QUESTS}
    for sq in ALL_STORYLINE_QUESTS:
        if sq["id"] not in existing_qids:
            sim_systems.QUESTS.append(sq)
            existing_qids.add(sq["id"])
            cnt["quests"] += 1
    # Also push to game engine's quest log if accessible
    print(f"[game_data] Storyline quests: +{len(ALL_STORYLINE_QUESTS)}")
    
    # World modifiers (from WC/W series)
    sim_systems.WORLD_MODIFIERS = ALL_WORLD_MODIFIERS
    print(f"[game_data] World modifiers: {len(ALL_WORLD_MODIFIERS)}")

    cnt["enemies"] += 1
    
    # Enemy distribution
    # 強敵（凶暴/遠古/深淵/W03/W04 專屬）不得隨機塞進新手安全區——
    # 原先隨機指派讓便利店出現遠古水馬、軌道站維修機械（W03）等，違反常理。
    # 安全區：新手村/校園/湖畔/溪畔/W02 村落（絕對無魔安全區）。
    _SAFE_LOCS = {"便利店", "聖十字校園", "鏡湖", "清溪河", "小吉鎮", "大根莖村"}
    loc_list = list(sim_systems.LOCATION_ENEMIES.keys())
    _strong_loc_list = [l for l in loc_list if l not in _SAFE_LOCS] or loc_list
    _strong_kw = ("凶暴", "兇暴", "遠古", "深淵", "灰燼", "拾荒王", "螢光獵手",
                  "沼澤變異體", "站內巡邏無人機", "軌道站維修機械")
    for e in ALL_ENEMIES:
        if not any(e["name"] in names for names in sim_systems.LOCATION_ENEMIES.values()):
            _is_strong = any(k in e["name"] for k in _strong_kw)
            loc = _seed.choice(_strong_loc_list if _is_strong else loc_list)
            sim_systems.LOCATION_ENEMIES.setdefault(loc, []).append(e["name"])
            cnt["enemy_dist"] += 1
    
    # 正規化敵人名稱：日文漢字 → 繁體中文（與遊戲文本一致，如 鉄甲虫→鐵甲蟲）
    _JP_TW_ENEMY = {"鉄": "鐵", "亀": "龜", "猪": "豬", "黄": "黃"}
    _enemy_name_map = {}
    for _e in sim_systems.ENEMIES:
        _new = "".join(_JP_TW_ENEMY.get(c, c) for c in _e["name"])
        _enemy_name_map[_e["name"]] = _new
        _e["name"] = _new
    for _loc, _names in sim_systems.LOCATION_ENEMIES.items():
        sim_systems.LOCATION_ENEMIES[_loc] = [_enemy_name_map.get(n, n) for n in _names]
    
    # NPCs
    for name, nd in ALL_NPCS.items():
        if name not in sim_systems.NPC_SCHEDULES:
            sched = nd.get("schedule", [])
            if sched:
                sim_systems.NPC_SCHEDULES[name] = sched
                cnt["npcs"] += 1
    
    # Sync NPC metadata into NPC_METADATA (keeps NPC_SCHEDULES as list)
    if not hasattr(sim_systems, 'NPC_METADATA'):
        sim_systems.NPC_METADATA = {}
    for name, nd in ALL_NPCS.items():
        sim_systems.NPC_METADATA[name] = {
            'description': nd.get('description', ''),
            'ability_details': nd.get('ability_details', []),
            'has_abilities': nd.get('has_abilities', False),
            'home_location': nd.get('location', ''),
            'archetype': nd.get('archetype', 'default'),
            'race': nd.get('race', '\u4e0d\u660e'),
            'location': nd.get('location', ''),
            'token_categories': nd.get('token_categories', []),
            'offers': nd.get('offers', []),
            'role': nd.get('role', ''),
            'greeting': nd.get('greeting', ''),
            'schedule': nd.get('schedule', []),
            'is_merchant': nd.get('is_merchant', False),
        }
    # Quests
    existing_q = {q["id"] for q in sim_systems.QUESTS}
    for q in ALL_QUESTS:
        if q["id"] not in existing_q:
            sim_systems.QUESTS.append(q)
            existing_q.add(q["id"])
            cnt["quests"] += 1
    # Fallback: add NPC_METADATA for NPCs in NPC_SCHEDULES but not in ALL_NPCS
    for _nname in list(getattr(sim_systems, 'NPC_SCHEDULES', {}).keys()):
        if _nname not in sim_systems.NPC_METADATA:
            sim_systems.NPC_METADATA[_nname] = {
                'description': '',
                'ability_details': [],
                'has_abilities': False,
                'home_location': '聖十字校園',
                'archetype': 'default',
                'race': '\u4e0d\u660e',
                'location': '\u8056\u5341\u5b57\u6821\u5712',
                'token_categories': [],
                'offers': ['\u8349\u85e5','\u5e72\u7ce7','\u7a7a\u74f6','\u9ebb\u7e6b'],
            }
    
    
    # Vehicles
    for vn, vd in ALL_VEHICLES.items():
        if vn not in sim_systems.VEHICLES:
            sim_systems.VEHICLES[vn] = vd
            cnt["vehicles"] += 1

    # 載具能力擴充：基底 VEHICLE_ABILITIES 只定義 4 種手寫載具，
    # 擴充載具（熱氣球/飛空艇/帆船等）完全沒有能力——熱氣球描述
    # 「飛行的」卻不能飛、帆船不能渡水，與文本/常理不符。
    # 飛行載具：飛行能力（跨水域不需船）；水載具：渡水能力。
    _VEHICLE_ABILITY_EXT = {
        "漁船": {"渡水": {"name": "⚓ 渡水", "desc": "駕船可通過水域路線",
                            "cost_type": "fuel", "cost": 10, "cooldown": 0,
                            "require_riding": True, "passive": True}},
        "帆船": {"渡水": {"name": "⚓ 渡水", "desc": "駕帆船可通過水域路線",
                            "cost_type": "fuel", "cost": 10, "cooldown": 0,
                            "require_riding": True, "passive": True}},
        "大型帆船": {"渡水": {"name": "⚓ 渡水", "desc": "大型帆船可通過水域路線",
                                  "cost_type": "fuel", "cost": 10, "cooldown": 0,
                                  "require_riding": True, "passive": True}},
        "熱氣球": {"飛行": {"name": "🕊 飛行", "desc": "熱氣球飛越地形（含水域）",
                             "cost_type": "fuel", "cost": 15, "cooldown": 0,
                             "require_riding": True, "passive": True}},
        "魔法掃帚": {"飛行": {"name": "🕊 飛行", "desc": "魔女掃帚翱翔天際",
                                "cost_type": "sp", "cost": 8, "cooldown": 0,
                                "require_riding": True, "passive": True}},
        "魔法飛毯": {"飛行": {"name": "🕊 飛行", "desc": "飛毯載人飛行",
                                "cost_type": "sp", "cost": 8, "cooldown": 0,
                                "require_riding": True, "passive": True}},
        "飛空艇": {"飛行": {"name": "🕊 飛行", "desc": "魔導飛空艇長途飛行",
                              "cost_type": "fuel", "cost": 20, "cooldown": 0,
                              "require_riding": True, "passive": True}},
        "龍騎乘": {"飛行": {"name": "🕊 飛行", "desc": "乘龍翱翔天際",
                              "cost_type": "sp", "cost": 12, "cooldown": 0,
                              "require_riding": True, "passive": True}},
    }
    _VEHICLE_ABILITIES = getattr(sim_systems, "VEHICLE_ABILITIES", {})
    for _vn, _abs in _VEHICLE_ABILITY_EXT.items():
        _VEHICLE_ABILITIES.setdefault(_vn, {}).update(_abs)
    # Also sync VEHICLE_LOCATIONS for all vehicles (keyed by loc -> veh)
    # Build reverse index: every new vehicle → its primary location
    _vehicle_to_primary_loc = {
        "自行車":       "便利店",
        "登山自行車":   "森林深處",
        "駿馬":         "卡洛夫角",
        "大型馬車":     "秘密鐵工廠",
        "漁船":         "鏡湖",
        "帆船":         "鏡湖",
        "機車":         "聖十字校園",
        "重型機車":     "卡洛夫角",
        "吉普車":       "廢棄礦坑",
        "大型帆船":     "卡洛夫角",
        "熱氣球":       "聖十字校園",
        "蒸氣機車":     "秘密鐵工廠",
        "魔法掃帚":     "英靈殿",
        "魔法飛毯":     "聖十字校園",
        "飛空艇":       "卡洛夫角",
        "龍騎乘":       "森林深處",
        "雪橇":         "廢棄礦坑",
    }
    # Build VEHICLE_TO_LOCATION reverse mapping (all vehicles → their location)
    veh_to_loc = {}
    for vn in sim_systems.VEHICLES:
        if vn in _vehicle_to_primary_loc:
            veh_to_loc[vn] = _vehicle_to_primary_loc[vn]
    if not hasattr(sim_systems, 'VEHICLE_TO_LOCATION'):
        sim_systems.VEHICLE_TO_LOCATION = veh_to_loc
    else:
        sim_systems.VEHICLE_TO_LOCATION.update(veh_to_loc)
    # Also populate VEHICLE_LOCATIONS with first vehicle per unique location
    _used_locs = set(sim_systems.VEHICLE_LOCATIONS.keys())
    for veh, loc in _vehicle_to_primary_loc.items():
        if veh in sim_systems.VEHICLES and loc not in _used_locs:
            sim_systems.VEHICLE_LOCATIONS[loc] = veh
            _used_locs.add(loc)
    
    # Real estate — also sync REAL_ESTATE_KEYS
    for rn, rd in ALL_REAL_ESTATE.items():
        if rn not in sim_systems.REAL_ESTATE:
            sim_systems.REAL_ESTATE[rn] = rd
            cnt["estate"] += 1
    # Ensure all real estate entries have location field
    for _rn, _rd in list(sim_systems.REAL_ESTATE.items()):
        if 'location' not in _rd:
            _infer = None
            for _loc in sim_systems.WORLD_MAP:
                if _loc[:2] in _rn or _rn[:2] in _loc:
                    _infer = _loc; break
            _rd['location'] = _infer if _infer else list(sim_systems.WORLD_MAP.keys())[0]
    # Refresh REAL_ESTATE_KEYS to include new entries
    sim_systems.REAL_ESTATE_KEYS = list(sim_systems.REAL_ESTATE.keys())
    
    # Ensure ALL items have tags (based on type)
    _default_tags = {
        'weapon': ['weapon'], 'armor': ['armor'], 'accessory': ['accessory'],
        'consumable': ['consumable'], 'quest': ['quest'], 'junk': ['junk'],
        'material': ['material'], 'misc': ['misc'],
    }
    for _iname, _idata in list(sim_systems.ITEM_CATALOG.items()):
        if 'tags' not in _idata:
            _typ = _idata.get('type', 'misc')
            _idata['tags'] = _default_tags.get(_typ, ['misc'])
    
    # Scene objects
    for loc, objs in ALL_SCENE_OBJECTS.items():
        if loc not in sim_systems.SCENE_OBJECTS:
            sim_systems.SCENE_OBJECTS[loc] = list(objs)
            cnt["objs"] += len(objs)
        else:
            existing_ids = {o["id"] for o in sim_systems.SCENE_OBJECTS[loc]}
            for o in objs:
                if o["id"] not in existing_ids:
                    sim_systems.SCENE_OBJECTS[loc].append(o)
                    existing_ids.add(o["id"])
                    cnt["objs"] += 1    # Recipes
    existing_r = {r["recipe_id"] for r in sim_systems.RECIPES}
    for r in ALL_RECIPES:
        if r["recipe_id"] not in existing_r:
            sim_systems.RECIPES.append(r)
            existing_r.add(r["recipe_id"])
            cnt["recipes"] += 1
        # Scene card locations → merge into WORLD_MAP
    _NEW_LOCATION_VIBES = {
        "概念學術高等學校": "📚 學術氛圍濃厚的校舍",
        "學生宿舍": "🏠 寧靜的學生住所",
        "校園後方廢棄倉庫": "🏚 早已無人使用的倉庫",
        "概念戰場模擬區": "⚔ 模擬戰用廣場",
        "地下避難所": "🕳 向地下延伸的避難設施",
        "夜間巡邏路線": "🌙 夜間巡邏路線",
        "校園屋頂": "🌅 校舍屋頂，視野極佳",
        "食堂": "🍽 學生們聚集的食堂",
        "圖書館分館": "📖 小型圖書室",
        "迴廊深層夢境": "✨ 夢境迴廊，現實變得模糊",
        "綻放混成園": "🌺 繁花盛開的庭園",
        "軌道居住站大學院": "🚀 漂浮在宇宙中的學術都市",
        "銀行區": "🏛 莊嚴的銀行街",
        "珊瑚台": "🪸 珊瑚閃耀的高地",
        "黑淵台": "🌑 俯瞰深淵的懸崖",
        "彩紋礁": "🌈 色彩繽紛的珊瑚礁",
        "流光": "💫 流光溢彩的神祕之地",
        "鏡湖周邊": "💧 鏡面般寧靜的湖面",
    }
    _SCENE_TO_WORLD_CONNECTIONS = {
        "概念學術高等學校": {"south":"聖十字校園"},
        "學生宿舍": {"south":"聖十字校園"},
        "校園後方廢棄倉庫": {"enter":"聖十字校園"},
        "概念戰場模擬區": {"enter":"聖十字校園"},
        "地下避難所": {"enter":"聖十字校園"},
        "夜間巡邏路線": {"west":"聖十字校園"},
        "校園屋頂": {"enter":"聖十字校園"},
        "食堂": {"north":"聖十字校園"},
        "圖書館分館": {"south":"聖十字校園"},
        "迴廊深層夢境": {"enter":"迴廊"},
        "綻放混成園": {"enter":"迴廊"},
        "軌道居住站大學院": {"enter":"迴廊"},
        "銀行區": {"west":"聖十字校園","south":"聖十字校園"},
        "珊瑚台": {"north":"卡洛夫角"},
        "黑淵台": {"south":"卡洛夫角"},
        "彩紋礁": {"north":"珊瑚台"},
        "流光": {"enter":"鏡湖"},
        "鏡湖周邊": {"enter":"鏡湖"},
        # 星光舞台演出場景（SC-20 特戰偶像團）：玩家需能從聖十字校園
        # 進入演出——否則這些場景只有單向出口（演出場景→校園）而
        # 永遠無法到達（地圖單向死路，卡片內容不可玩）。
        "星光舞台": {"enter":"聖十字校園"},
        "演唱會模式": {"enter":"星光舞台"},
        "戰術模式": {"enter":"星光舞台"},
        "切換瞬間": {"enter":"星光舞台"},
        "首爾奧林匹克體育場": {"enter":"星光舞台"},
        "後台更衣室": {"enter":"星光舞台"},
        "直播控制室": {"enter":"星光舞台"},
        "伺服器核心室": {"enter":"星光舞台"},
        "舞台切換盲區": {"enter":"星光舞台"},
        "異常輸出時刻": {"enter":"星光舞台"},
    }
    scene_locs_added = 0
    for scene_id, sdata in ALL_LOCATIONS.items():
        sname = sdata.get("name","")
        if not sname or sname in sim_systems.WORLD_MAP:
            continue
        # Add to WORLD_MAP
        conn = _SCENE_TO_WORLD_CONNECTIONS.get(sname, {"south":"聖十字校園"})
        sim_systems.WORLD_MAP[sname] = conn
        # Add vibe
        vibe = _NEW_LOCATION_VIBES.get(sname, sdata.get("vibe", "📍 未知之地"))
        sim_systems.LOCATION_VIBES[sname] = vibe
        # Assign scene type for new locations
        loc_type = "outdoor"
        if any(kw in sname for kw in ["教室","圖書館","食堂","宿舍","倉庫","避難所","館","工場","店"]):
            loc_type = "indoor"
        elif any(kw in sname for kw in ["迷宮","遺跡","坑","地下","洞"]):
            loc_type = "dungeon"
        elif any(kw in sname for kw in ["夢境","異空間","次元"]):
            loc_type = "special"
        sim_systems.LOCATION_TYPES[sname] = loc_type
        # Add enemy distribution
        _enemy_pool = list(sim_systems.ENEMIES)
        if _enemy_pool:
            sim_systems.LOCATION_ENEMIES.setdefault(sname, []).append(
                _seed.choice(_enemy_pool)["name"])
        scene_locs_added += 1
    cnt["locations"] = scene_locs_added

    # ────────────────────────────────────────────────────────────
    # 跨線地點遭遇敵人覆寫 — 依《世界線錨定 — 補充欄位》權威表：
    #   W04 灰燼紀元 = 灰燼行者/拾荒王/螢光獵手（後末日不穩定聚合）
    #   W03 軌道站   = 下層工業港機械系（宇宙時代極低聚合）
    #   S07 熒光沼澤 = 變異兩棲生物（原人類暴露變異、食物鏈頂端）
    #   S08 玻璃荒漠 = 靈爆中心殘留（>100ppm）
    #   夢境層 S10/S11 = 概念構成（暗影/幽靈/元素）
    #   原先這些地點的遭遇敵人是隨機指派（玻璃荒漠=虎、軌道站=晞咕萊雅之影），
    #   且卡片影之敵（X之影/深淵X之影）是任務演出專用，不應出現在一般遭遇池。
    # ────────────────────────────────────────────────────────────
    _WORLD_LINE_ENEMY_OVERRIDES = {
        "熒光沼澤":         ["螢光獵手", "沼澤變異體", "暗影靈"],
        "玻璃荒漠":         ["灰燼行者", "灰燼行者長", "元素核心"],
        "鏽蝕城邦":         ["灰燼行者", "拾荒王", "廢鐵傀儡"],
        "鏽蝕城邦地下":     ["灰燼行者", "拾荒王", "廢鐵傀儡"],
        "軌道居住站大學院": ["站內巡邏無人機", "軌道站維修機械", "廢鐵傀儡"],
        "高密度大氣結晶行星": ["暗影靈", "幽靈", "元素核心"],
        "綻放混成園":       ["暗影靈", "幽靈", "元素核心"],
    }
    for _loc, _names in _WORLD_LINE_ENEMY_OVERRIDES.items():
        if _loc in sim_systems.WORLD_MAP or _loc in sim_systems.LOCATION_ENEMIES:
            sim_systems.LOCATION_ENEMIES[_loc] = list(_names)

    # 世界線敵人洩漏清理 + 影之敵排除移往 expand_game 尾部（after 統計前）：
    # 卡片整合段（珊瑚台等）在覆寫表之後才建立場景並指派敵人，
    # 清理必須在全部來源建立完成後執行才能涵蓋。
    
    # Final VEHICLE_LOCATIONS fallback: ensure ALL WORLD_MAP locations have vehicles
    _vlist = ['腳踏車','馬','馬車','小舟','自行車','登山自行車','駿馬','大型馬車','漁船',
    '機車','重型機車','吉普車','帆船','大型帆船','熱氣球','蒸氣機車','魔法掃帚','魔法飛毯','飛空艇','龍騎乘','雪橇']
    if not hasattr(sim_systems, 'VEHICLE_LOCATIONS'):
        sim_systems.VEHICLE_LOCATIONS = {}
    _occupied = set(sim_systems.VEHICLE_LOCATIONS.keys())
    for _vi, _loc in enumerate(sim_systems.WORLD_MAP):
        if _loc not in _occupied:
            sim_systems.VEHICLE_LOCATIONS[_loc] = _vlist[_vi % len(_vlist)]

    # 知名地點載具配對覆寫：fallback 任意指派可能不符常理
    # （如極北冰原配蒸氣機車、魔女學府配熱氣球），依地理/文本常理修正。
    _VEHICLE_LOCATION_OVERRIDES = {
        "極北冰原": "雪橇",          # 冰原雪橇
        "魔女學府": "魔法掃帚",      # 魔女學府的掃帚
        "農學院":   "馬車",          # 農產運輸
        "清溪河":   "小舟",          # 河流渡水
        "鏡山":     "登山自行車",    # 山路
        "鬱鬱山":   "登山自行車",    # 山林越野
        "煙雲溫泉湖": "重型機車",    # 溫泉山路
    }
    for _ov_loc, _ov_veh in _VEHICLE_LOCATION_OVERRIDES.items():
        if _ov_veh in sim_systems.VEHICLES:
            sim_systems.VEHICLE_LOCATIONS[_ov_loc] = _ov_veh

    # 載具掛載：VEHICLE_LOCATIONS 的載具（魔法掃帚/吉普車/飛空艇等）原只在地圖
    # 顯示、未掛到場景物件——玩家永遠拿不到（18 種死資料）。
    # 每個地點若無 vehicle 類型物件，就掛上該地點的載具供探索取得。
    # （VEHICLE_LOCATIONS 在此處已完整生成，故掛載放這裡。）
    _veh_desc = {"魔法掃帚": "插在石縫中的掃帚，隱隱流轉著魔力",
                 "魔法飛毯": "攤開的飛毯，邊緣繡著符文",
                 "飛空艇": "停泊的魔導飛空艇，船體刻著魔法陣",
                 "龍騎乘": "盤踞的巨龍，等待與它心意相通的人",
                 "熱氣球": "充好氣的熱氣球，吊籃裡備著燃料",
                 "吉普車": "越野吉普車，車況良好",
                 "機車": "一輛機車，鑰匙還插著",
                 "重型機車": "粗獷的重型機車",
                 "蒸氣機車": "停在軌道上的蒸氣機車，爐火尚溫",
                 "帆船": "泊在碼頭的帆船",
                 "大型帆船": "雄偉的大型帆船，船舷高聳",
                 "漁船": "作業中的漁船，漁網堆在甲板上",
                 "雪橇": "狗拉雪橇，雪橇犬已經就位",
                 "登山自行車": "齒比粗大的登山自行車",
                 "自行車": "一輛乾淨的自行車",
                 "駿馬": "一匹精神抖擻的駿馬",
                 "大型馬車": "寬敞的大型馬車，可載多人",
                 "馬車": "載貨用馬車"}
    for _vloc, _vname in list(sim_systems.VEHICLE_LOCATIONS.items()):
        if _vname not in sim_systems.VEHICLES:
            continue
        _scene_objs = sim_systems.SCENE_OBJECTS.setdefault(_vloc, [])
        if any(o.get("type") == "vehicle" for o in _scene_objs):
            continue
        _scene_objs.append({
            "id": "veh_%s" % _vloc, "name": _vname, "type": "vehicle",
            "vehicle_type": _vname,
            "desc": _veh_desc.get(_vname, "停靠在此的%s" % _vname),
            "interactable": True,
        })

    # ── NPC schedule location fallback ──
    # Some NPCs reference locations not in WORLD_MAP or scene cards
    # 世界線橋樑：W03/W04/夢境層 地點經由「迴廊」連通（文本：迴廊是連接
    # 多元宇宙各世界線的橋樑），不再直接掛在聖十字校園（W01）
    _NPC_FALLBACK_LOCATIONS = {
        "中央大圖書館": {"west":"聖十字校園", "east":"英靈殿"},
        "西翼大市集": {"east":"聖十字校園", "north":"便利店"},
        "小吉鎮": {"south":"霧海群島"},
        "大根莖村": {"west":"小吉鎮"},
        "迴廊": {"north":"聖十字校園", "enter":"軌道居住站大學院",
                   "east":"鏽蝕城邦", "deep":"玻璃荒漠"},
        "魔女學府": {"south":"聖十字校園"},
        "鏽蝕城邦": {"enter":"迴廊"},
        "熒光沼澤": {"enter":"迴廊"},
        "玻璃荒漠": {"enter":"迴廊"},
        "煙雲溫泉湖": {"enter":"迴廊"},
        "高密度大氣結晶行星": {"enter":"迴廊"},
        "綻放混成園": {"enter":"迴廊"},
    }
    for _loc, _conn in _NPC_FALLBACK_LOCATIONS.items():
        if _loc not in sim_systems.WORLD_MAP:
            sim_systems.WORLD_MAP[_loc] = _conn
            if _loc not in sim_systems.LOCATION_VIBES:
                _vibe_map = {
        '中央大圖書館': '📚 藏書豐富的巨大圖書館',
        '西翼大市集': '🏪 陳列著異世界商品的市集',
        '小吉鎮': '🍃 氛圍溫馨的鄉村小鎮',
        '大根莖村': '🌱 地下的神祕村莊',
        '迴廊': '🧩 空間扭曲的古代迴廊',
        '魔女學府': '🔮 魔法與科學交織的學府',
                }
                sim_systems.LOCATION_VIBES[_loc] = _vibe_map.get(_loc, '🌍 未知之地')
            if _loc not in sim_systems.LOCATION_TYPES:
                sim_systems.LOCATION_TYPES[_loc] = "indoor" if _loc in ("中央大圖書館","迴廊","魔女學府") else "outdoor"
    if hasattr(sim_systems, 'LOCATION_NATIONS'):
        for _loc in _NPC_FALLBACK_LOCATIONS:
            if _loc not in sim_systems.LOCATION_NATIONS:
                sim_systems.LOCATION_NATIONS[_loc] = ""
    
    # ════════════════════════════════════════════════════════════
    # 地圖連通性修正：補齊雙向邊（常理——能進就能出）
    # ════════════════════════════════════════════════════════════
    # 世界線邊強制修正：W03/W04/夢境層 地點只能經由「迴廊」進入，
    # 覆寫場景卡生成時誤掛到 W01 聖十字校園的邊（文本：跨世界線須經迴廊）
    _CORRIDOR_ONLY = {
        "軌道居住站大學院": {"enter": "迴廊"},
        "鏽蝕城邦": {"enter": "迴廊"},
        "熒光沼澤": {"enter": "迴廊"},
        "玻璃荒漠": {"enter": "迴廊"},
        "高密度大氣結晶行星": {"enter": "迴廊"},
        "綻放混成園": {"enter": "迴廊"},
        # W02 琥珀紀元村落（Ver 3.1：小吉鎮/大根莖村屬 W02）——
        # 從 W01 無法直達，需經迴廊（霧海群島的舊直連邊改連迴廊）
        "小吉鎮": {"enter": "迴廊", "east": "大根莖村"},
        "大根莖村": {"west": "小吉鎮"},
        # SL-10 界域內部：M-值工程沙盒 是魔女學府的實驗區，從學府進入
        "魔女學府 M-值工程沙盒": {"enter": "魔女學府"},
        "迴廊": {"north": "聖十字校園", "south": "鏡湖",
                   "west": "小吉鎮", "east": "霧海群島",
                   "enter": "軌道居住站大學院", "exit": "鏽蝕城邦",
                   "deep": "玻璃荒漠"},
    }
    # ════════════════════════════════════════════════════════════
    # 迴廊場景物件（依《多元宇宙與概念之橋》迴廊文本：概念、數據流、
    # 意識碎片、世界法則交織的虛無維度）——讓 Lv1-5 玩家在樞紐也有探索內容
    # type 必須對應 do_scene_search 既有處理器（decoration/container/
    # workstation/vehicle/mechanism/rest），否則物件可互動卻無效果
    _CORRIDOR_OBJS = [
        {"name": "世界法則碎片", "type": "decoration", "interactable": True,
         "desc": "一塊凝固的世界法則殘片，表面流動著各世界線的剪影。",
         "note": "碎片映出四條世界線的縮影：高靈子的 W01、無魔的 W02、軌道上的 W03、灰燼不穩的 W04——它們都被迴廊串在一起。"},
        {"name": "漂浮的數據流", "type": "container", "interactable": True,
         "desc": "概念數據流凝成的光帶，觸碰時指尖浮現不屬於任何世界的文字。",
         "contents": ["水晶碎片"]},
        {"name": "意識碎片映池", "type": "rest", "interactable": True,
         "desc": "倒映意識碎片的淺池，凝視片刻能讓思緒沉澱。",
         "rest_sp": 12},
    ]
    _exist = {o.get("name") for o in sim_systems.SCENE_OBJECTS.setdefault("迴廊", [])}
    for _o in _CORRIDOR_OBJS:
        if _o["name"] not in _exist:
            sim_systems.SCENE_OBJECTS["迴廊"].append(dict(_o))

    for _loc, _conn in _CORRIDOR_ONLY.items():
        sim_systems.WORLD_MAP[_loc] = dict(_conn)

    # 所有 WORLD_MAP 寫入完成後統一處理，避免單向死路卡死 NPC 家／任務回報。
    # ════════════════════════════════════════════════════════════
    _REVERSE_DIR = {"east": "west", "west": "east", "north": "south", "south": "north",
                     "enter": "exit", "exit": "enter", "deep": "up", "up": "deep"}
    _bidir_fixed = 0
    for _loc in list(sim_systems.WORLD_MAP.keys()):
        for _d, _dest in list(sim_systems.WORLD_MAP.get(_loc, {}).items()):
            _rev = _REVERSE_DIR.get(_d)
            if not _rev:
                continue
            _dest_conns = sim_systems.WORLD_MAP.setdefault(_dest, {})
            # 已可回到 _loc 則跳過（任意方向有通往 _loc 的邊即可）
            if any(v == _loc for v in _dest_conns.values()):
                continue
            if _rev not in _dest_conns:
                _dest_conns[_rev] = _loc
                _bidir_fixed += 1
    if _bidir_fixed:
        print(f"[game_data] 地圖雙向邊修正: +{_bidir_fixed}")

    # 霧海群島原手寫 north:小吉鎮 是 W01→W02 跨線邊——改連迴廊樞紐。
    # 放在雙向邊修正之後：north:小吉鎮 由雙向修正補上（小吉鎮 south:霧海群島），
    # 此時覆寫為迴廊，並確保迴廊→霧海群島 有回程（迴廊 east:霧海群島）。
    _wuhai = sim_systems.WORLD_MAP.get("霧海群島")
    if _wuhai:
        _wuhai["north"] = "迴廊"
        _corr_conns = sim_systems.WORLD_MAP.setdefault("迴廊", {})
        if "east" not in _corr_conns:
            _corr_conns["east"] = "霧海群島"

    # ────────────────────────────────────────────────────────────
    # 尾部清理（所有 WORLD_MAP / LOCATION_ENEMIES 來源都建立完成後）：
    # 1. 世界線洩漏清理——distribution/場景/卡片整合各段可能把 W03/W04
    #    專屬敵隨機塞進 W01 地點；覆寫表只替換跨線目標，此處把世界線
    #    敵人名從所有非目標地點移除（如珊瑚台被隨機指派站內巡邏無人機）。
    # 2. 影之敵排除——卡片影之敵（X之影/深淵X之影）是任務演出專用；
    #    普通場景不得被演出敵污染日常遭遇，演出場景刻意保留。
    # ────────────────────────────────────────────────────────────
    _WL_NAMES = set()
    for _nlist in _WORLD_LINE_ENEMY_OVERRIDES.values():
        _WL_NAMES.update(_nlist)
    for _loc, _names in list(sim_systems.LOCATION_ENEMIES.items()):
        if _loc in _WORLD_LINE_ENEMY_OVERRIDES:
            continue
        _clean = [n for n in _names if n not in _WL_NAMES]
        if len(_clean) != len(_names):
            if _clean:
                sim_systems.LOCATION_ENEMIES[_loc] = _clean
            else:
                _plain = [e for e in sim_systems.ENEMIES
                          if e["name"] not in _WL_NAMES and "之影" not in e["name"]]
                sim_systems.LOCATION_ENEMIES[_loc] = [_seed.choice(_plain)["name"]]
    # NPC 個人商店道具補齊（所有 NPC_METADATA 建立完成後）
    for _nname, _ndata in sim_systems.NPC_METADATA.items():
        for _offer in _ndata.get("offers", []):
            if _offer in sim_systems.ITEM_CATALOG:
                continue
            _def = _NPC_SHOP_ITEM_OVERRIDES.get(_offer) or _build_npc_shop_item_def(_offer)
            # reviewer 修正：規則生成的消耗品補預設治癒值（無 heal_hp/heal_sp
            # 的消耗品使用時補 0，買了等於沒用）
            if _def["type"] == "consumable" and "heal_hp" not in _def and "heal_sp" not in _def:
                if "magic" in _def.get("tags", []):
                    _def["heal_sp"] = 12
                else:
                    _def["heal_hp"] = 15
            sim_systems.ITEM_CATALOG[_offer] = dict(_def)
            cnt["items"] += 1

    _PERF_KW = ("舞台", "演唱會", "模式", "瞬間", "盲區", "更衣室", "直播",
                "控制室", "核心室", "體育場", "競技", "演出")
    # fallback 池同時排除世界線敵人（_WL_NAMES）：否則影之敵排除後
    # 補普通敵人時可能抽到 W03/W04 專屬敵（如珊瑚台被補成站內巡邏無人機）。
    _non_shadow_enemies = [e for e in sim_systems.ENEMIES
                           if "之影" not in e["name"] and e["name"] not in _WL_NAMES]
    for _loc, _names in list(sim_systems.LOCATION_ENEMIES.items()):
        if _loc in _WORLD_LINE_ENEMY_OVERRIDES:
            continue
        if any(k in _loc for k in _PERF_KW):
            continue
        if any("之影" in n for n in _names) and _non_shadow_enemies:
            sim_systems.LOCATION_ENEMIES[_loc] = [
                n for n in _names if "之影" not in n] or [_seed.choice(_non_shadow_enemies)["name"]]

    after = {
        "items": len(sim_systems.ITEM_CATALOG),
        "enemies": len(sim_systems.ENEMIES),
        "quests": len(sim_systems.QUESTS),
        "npcs": len(sim_systems.NPC_SCHEDULES),
        "vehicles": len(sim_systems.VEHICLES),
        "estate": len(sim_systems.REAL_ESTATE),
        "objs": sum(len(v) for v in sim_systems.SCENE_OBJECTS.values()),
        "recipes": len(sim_systems.RECIPES),
    }
    
    # Also count dialogues, schedule entries, locations, cards as entities
    dialogs = sum(len(v) for v in ALL_DIALOGUES.values())
    
    # Count each NPC schedule entry separately (5 per NPC)
    sched_entries = sum(len(s) for s in sim_systems.NPC_SCHEDULES.values())
    
    # Count locations: original + scene card generated
    loc_count = len(sim_systems.WORLD_MAP)
    
    # Count game cards
    card_count = len(_ALL_CARDS)
    
    enemy_dists = cnt['enemy_dist']
    
    # Expose NPC_DIALOGUES to sim_systems module
    sim_systems.NPC_DIALOGUES = ALL_DIALOGUES

    # ════════════════════════════════════════════════════════════
    # 世界線標記：每地點標記所屬世界線（依場景卡文本權威表）
    # 未列者預設 W01 主世界線；跨線地點顯示「跨世界線」標記
    sim_systems.LOCATION_WORLD_LINES = {}
    for _loc in sim_systems.WORLD_MAP:
        sim_systems.LOCATION_WORLD_LINES[_loc] = get_location_world_line(_loc)

    print(f"[game_data] Integration complete!")
    print(f"  Items: +{cnt['items']} → {after['items']}")
    print(f"  Enemies: +{cnt['enemies']} → {after['enemies']} (dists: +{enemy_dists})")
    print(f"  NPCs: +{cnt['npcs']} → {after['npcs']} (schedule entries: {sched_entries})")
    print(f"  Quests: +{cnt['quests']} → {after['quests']}")
    print(f"  Skills: {len(ALL_SKILLS)}")
    print(f"  WorldModifiers: {len(ALL_WORLD_MODIFIERS)}")
    print(f"  Vehicles: +{cnt['vehicles']} → {after['vehicles']}")
    print(f"  RealEstate: +{cnt['estate']} → {after['estate']}")
    print(f"  SceneObjs: +{cnt['objs']} → {after['objs']}")
    print(f"  Recipes: +{cnt['recipes']} → {after['recipes']}")
    print(f"  Dialogues: {dialogs} lines")
    print(f"  Locations: +{loc_count}")
    print(f"  Cards: +{card_count}")
    print(f"  EnemyDists: +{enemy_dists}")
    
    # Grand total includes all entity types
    grand = sum(after.values()) + dialogs + sched_entries + loc_count + card_count + enemy_dists
    print(f"  ★ GRAND TOTAL entities: {grand}")
