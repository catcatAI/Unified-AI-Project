"""
Fix all 3871 token type fields.
Every token has type='?' — this script assigns meaningful types
based on token name and value keyword matching.
"""
import json

CARDS_PATH = 'data/game_cards.json'

# ── Type assignment rules ──────────────────────────────────────────────
# Rules: (type, [list of keywords to match in token name], [extra keywords in value])
# Priority: first match wins

_TYPE_RULES = [
    # Identity / Bio
    ("race", ["種族", "race", "種族特徵", "物種"]),
    ("gender", ["性別", "gender", "sex"]),
    ("age", ["年齡", "age", "歲", "年紀"]),
    ("name", ["姓名", "名稱", "名字", "name", "稱號", "暱稱", "化名", "代號"]),
    ("origin", ["起源", "出身", "出生", "origin", "來歷", "來源", "故鄉", "原生"]),
    ("identity", ["身份", "identity", "身分", "地位", "頭銜", "階級"]),
    ("occupation", ["職業", "職位", "職務", "工作", "occupation", "job", "任職", "打工"]),
    ("role", ["角色定位", "定位", "role", "擔當", "位置", "崗位"]),
    
    # Combat & Survival
    ("combat", ["戰鬥", "戰", "武", "兵", "劍", "刀", "槍", "弓", "attack", "combat",
                 "戰術", "攻擊", "格鬥", "近戰", "遠程", "射擊", "戰鬥力",
                 "身法", "步法", "戰技", "實戰", "獵殺", "追獵", "暗殺"]),
    ("survival", ["生存", "survival", "生活", "起居", "日常", "作息"]),
    ("defense", ["防禦", "defense", "護甲", "護盾", "裝甲", "防護"]),
    
    # World & Setting
    ("worldline", ["世界線", "world", "世界", "宇宙", "位面", "次元"]),
    ("location", ["住址", "住所", "地址", "住處", "家", "居住", "定居", "常駐",
                   "據點", "基地", "藏身", "位置", "地點", "location", "home",
                   "宿舍", "房間", "辦公室", "公寓", "塔樓"]),
    ("time_anchor", ["時間錨點", "時間", "時代", "紀元", "epoch"]),
    ("history", ["歷史", "history", "歷史線", "過去", "往事", "背景故事",
                  "經歷", "履歷", "年表", "事件"]),
    
    # Personality & Traits
    ("personality", ["性格", "個性", "personality", "人格", "氣質", "性情"]),
    ("tone", ["基調", "tone", "風格", "氣氛", "氛圍", "色調"]),
    ("trait", ["特質", "trait", "特徵", "標籤", "tag", "特點", "屬性"]),
    ("weakness", ["弱點", "weakness", "缺點", "弱項", "短板", "缺陷"]),
    ("alignment", ["陣營", "alignment", "立場", "傾向", "取向"]),
    
    # Abilities & Powers
    ("ability", ["能力", "技能", "skill", "ability", "招式", "必殺", "絕招",
                  "本領", "手段", "法術", "術式"]),
    ("element", ["元素", "element", "屬性", "火", "水", "風", "雷", "土", "光", "闇",
                  "神性", "神力", "信仰", "自然"]),
    ("energy", ["能量", "energy", "魔力", "mana", "靈力", "內力", "法力",
                 "動力", "電力", "靈子"]),
    
    # Social & Relationships
    ("relationship", ["關係", "relationship", "羈絆", "連結", "connection",
                       "人際", "社交", "交情", "互動", "相處"]),
    ("faction", ["組織", "faction", "勢力", "陣營", "派系", "集團", "團體", "公會"]),
    ("social", ["社交", "社會", "人脈", "聲望", "名聲", "信譽"]),
    
    # Knowledge & Lore
    ("knowledge", ["知識", "knowledge", "情報", "資訊", "理論", "學問",
                    "研究", "調查", "解析", "實驗"]),
    ("lore", ["設定", "lore", "傳說", "神話", "典故", "軼事"]),
    
    # Meta / Card data
    ("card_id", ["卡片代碼", "card_id", "card id", "卡號", "ID"]),
    ("description", ["描述", "description", "說明", "介紹", "摘要", "總結",
                      "一條總結", "概述", "簡介"]),
    ("status", ["狀態", "status", "情況", "狀況", "現狀"]),
    
    # Game mechanics
    ("mechanism", ["機制", "mechanism", "規則", "rule", "法則", "系統", "引擎"]),
    ("condition", ["條件", "條件", "condition", "前提", "要求"]),
    ("effect", ["效果", "effect", "影響", "作用", "功用", "功能"]),
    
    # Items & Equipment
    ("item", ["物品", "道具", "裝備", "item", "equipment", "持有", "擁有", "攜帶"]),
    
    # Speech & Communication
    ("speech", ["對話", "台詞", "說話", "speech", "口頭禪", "名言", "發言",
                 "語氣", "語調"]),
    
    # Appearance
    ("appearance", ["外觀", "外表", "appearance", "長相", "容貌", "服裝", "衣著",
                     "造型", "形象", "體型", "身高"]),
    
    # Story & Plot
    ("storyline", ["故事線", "主線", "支線", "story", "劇情", "情節"]),
    ("event", ["事件", "event", "事故", "異變", "變故", "活動"]),
]

# Special exact-name overrides for precise matching
_EXACT_TYPE_OVERRIDES = {
    "種族": "race",
    "性別": "gender",
    "年齡": "age",
    "姓名": "name",
    "名稱": "name",
    "基調": "tone",
    "世界線": "worldline",
    "身份": "identity",
    "生存": "survival",
    "戰鬥": "combat",
    "起源": "origin",
    "歷史": "history",
    "歷史線": "history",
    "角色定位": "role",
    "職業": "occupation",
    "卡片代碼": "card_id",
    "時間錨點": "time_anchor",
    "住址": "location",
    "跨線相容性": "meta",
    "法則版本": "meta",
    "一條總結": "description",
    "事件描述": "description",
    "類型": "type",
    "技能效果": "effect",
    "核心目的": "purpose",
    "特質": "trait",
    "能力": "ability",
    "對象": "target",
}


def determine_token_type(name: str, value: str) -> str:
    """Determine token type from name and value."""
    # 1. Check exact name override
    if name in _EXACT_TYPE_OVERRIDES:
        return _EXACT_TYPE_OVERRIDES[name]
    
    # Also check if the name starts with a known pattern
    for sep in ['_', '：', ':']:
        if sep in name:
            prefix = name.split(sep)[0]
            if prefix in _EXACT_TYPE_OVERRIDES:
                return _EXACT_TYPE_OVERRIDES[prefix]
    
    # 2. Match against keyword rules
    value_str = str(value) if value is not None else ''
    text = name.lower() + " " + value_str.lower()
    for ttype, keywords in _TYPE_RULES:
        for kw in keywords:
            if kw.lower() in text:
                return ttype
    
    # 3. Fallback: use category if available
    return "general"


# ── Main ────────────────────────────────────────────────────────────────

with open(CARDS_PATH, 'r', encoding='utf-8') as f:
    gc = json.load(f)

type_counts = {}
fixed_count = 0
no_change = 0

for card in gc['cards']:
    for t in card.get('tokens', []):
        if isinstance(t, dict):
            old_type = t.get('type', '')
            name = t.get('name', t.get('id', ''))
            value = t.get('value', '')
            
            if not old_type or old_type == 'unknown' or old_type == '?':
                new_type = determine_token_type(name, value)
                t['type'] = new_type
                type_counts[new_type] = type_counts.get(new_type, 0) + 1
                fixed_count += 1
            else:
                no_change += 1

with open(CARDS_PATH, 'w', encoding='utf-8') as f:
    json.dump(gc, f, ensure_ascii=False, indent=2)

print("=== TOKEN TYPE FIX REPORT ===")
print(f"Total tokens processed: {fixed_count + no_change}")
print(f"Tokens with type added: {fixed_count}")
print(f"Tokens already had type: {no_change}")
print()
print("Type distribution:")
for ttype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
    print(f"  {ttype}: {count}")

# Verify no remaining empty types
print()
remaining_empty = 0
for card in gc['cards']:
    for t in card.get('tokens', []):
        if isinstance(t, dict) and not t.get('type'):
            remaining_empty += 1
print(f"Remaining empty types: {remaining_empty}")
if remaining_empty == 0:
    print("✅ ALL TOKENS HAVE TYPE!")
