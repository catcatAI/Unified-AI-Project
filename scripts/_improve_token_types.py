"""
Improve token type assignment by adding more keyword rules.
Target: reduce general from ~32% to <20% by better matching.
"""
import json
import re

CARDS_PATH = 'data/game_cards.json'

# ── Expanded type rules ─────────────────────────────────────────────
# These are ADDITIONAL patterns found in the general analysis

_ADDITIONAL_RULES = [
    ("mechanism", ["機制", "系統", "引擎", "法則", "模塊", "模組", "程序", "protocol"]),
    ("status", ["狀態", "狀況", "參數", "參數", "數值", "進度", "程度"]),
    ("identity", ["身份", "身份", "階級", "地位", "級別", "等級", "排名"]),
    ("meta", ["全稱", "簡稱", "代號", "縮寫", "版本", "代碼", "編號", "ID", "序號"]),
    ("purpose", ["核心目的", "宗旨", "目標", "使命", "任務", "意圖"]),
    ("theme", ["核心主題", "主題", "主軸", "議題"]),
    ("character", ["角色", "人物", "登場", "登場作品"]),
    ("storyline", ["故事線", "劇情", "情節", "章節", "篇章", "線索"]),
    ("event", ["事件", "事故", "事變", "活動"]),
    ("dialogue", ["對話", "台詞", "對白", "發言", "語音"]),
    ("quote", ["名言", "口頭禪", "標語", "slogan"]),
    ("item", ["物品", "道具", "持有物", "裝備", "持有", "攜帶"]),
    ("technology", ["技術", "科技", "科學", "工藝", "工程", "裝置"]),
    ("environment", ["環境", "生態", "氣候", "地形", "地理"]),
    ("group", ["組織", "團體", "隊伍", "團隊", "小隊", "部隊", "軍團"]),
    ("economy", ["經濟", "貿易", "市場", "貨幣", "物價", "價格", "價值", "金錢"]),
    ("politics", ["政治", "政府", "政策", "法律", "法規", "條約", "外交"]),
    ("culture", ["文化", "傳統", "習俗", "節日", "信仰", "宗教"]),
    ("dimension", ["維度", "次元", "空間", "領域", "界域"]),
    ("connection", ["連接", "關聯", "聯繫", "通道", "橋樑", "紐帶"]),
    ("feature", ["特色", "特點", "特徵", "特性", "屬性", "性質"]),
    ("interest", ["興趣", "愛好", "嗜好", "喜歡", "偏好"]),
    ("body", ["身體", "體型", "體重", "身高", "外貌", "外表", "外觀", "體格"]),
    ("skill", ["技能", "技巧", "手法", "手法", "熟練", "專長"]),
    ("knowledge_field", ["學科", "領域", "專業", "知識領域", "專精"]),
    ("rank", ["等級", "階級", "段位", "層級", "位階"]),
    ("alignment_value", ["善惡值", "道德", "倫理", "正義", "邪惡"]),
    ("location_type", ["總部", "基地", "據點", "根據地", "所在"]),
    ("situation", ["情境", "場景", "場合", "狀況"]),
    ("classification", ["分類", "類別", "類型", "種類", "系譜", "譜系"]),
    ("records", ["記錄", "檔案", "資料", "數據", "情報"]),
    ("attribute", ["屬性", "能力值", "基本數值", "基礎數值"]),
    ("occupation", ["業務", "職責", "分管", "負責"]),
    ("ability", ["天賦型態", "天賦", "變身", "型態", "形態"]),
    ("item", ["產品型號", "產品", "型號", "版本號"]),
    ("status", ["成員數", "人數", "數量", "總數", "合計", "總計"]),
    ("dimension", ["面向", "層面", "角度"]),
    ("location", ["舞台", "會場", "場地", "場館"]),
    ("main_character", ["主角", "主人公", "主役"]),
    ("reference", ["S0", "SL-", "EP-", "CC-", "ORG-", "WC-", "UM-"]),
]

# Also add more exact name overrides
_EXACT_TYPE_OVERRIDES = {
    "概念永恆": "immortality",
    "概念性生理反應": "physiology",
    "概念性心理狀態": "psychology",
    "概念器官的臨時改變": "physiology",
    "概念性昏迷": "physiology",
    "概念固化": "physiology",
    "概念性連續攻擊": "combat",
    "概念性防禦": "defense",
    "CC-02": "reference",
    "CC-03": "reference", 
    "CC-04": "reference",
    "身體": "body",
    "體重": "body",
    "善惡值": "alignment",
    "卡片類型": "meta",
    "卡片代碼": "meta",
    "核心主題": "theme",
    "核心目的": "purpose",
    "一條總結": "description",
    "分類系譜": "classification",
    "政治結構": "politics",
    "總部": "location",
    "總部地點": "location",
    "勢力": "faction",
    "關係": "relationship",
    "連接": "connection",
    "興趣": "interest",
    "情境": "situation",
    "參數": "status",
    "特色": "feature",
    "維度": "dimension",
    "特質": "trait",
    "特徵": "feature",
}


def improved_token_type(name: str, value: str, old_type: str) -> str:
    """Improve token type by checking additional rules."""
    # 1. Exact override
    if name in _EXACT_TYPE_OVERRIDES:
        return _EXACT_TYPE_OVERRIDES[name]
    
    text = name.lower() + " " + str(value).lower()
    
    # 2. Additional rules
    for ttype, keywords in _ADDITIONAL_RULES:
        for kw in keywords:
            if kw in text:
                return ttype
    
    # 3. Keep original if not improved
    return old_type


# ── Main ────────────────────────────────────────────────────────────

with open(CARDS_PATH, 'r', encoding='utf-8') as f:
    gc = json.load(f)

changes = {}
for card in gc['cards']:
    for t in card.get('tokens', []):
        if isinstance(t, dict):
            old_type = t.get('type', '')
            name = t.get('name', '')
            value = t.get('value', '')
            
            if old_type == 'general':
                new_type = improved_token_type(name, value, old_type)
                if new_type != 'general':
                    t['type'] = new_type
                    changes[old_type] = changes.get(old_type, 0) + 1

with open(CARDS_PATH, 'w', encoding='utf-8') as f:
    json.dump(gc, f, ensure_ascii=False, indent=2)

# Count remaining
remaining_general = 0
by_new_type = {}
for card in gc['cards']:
    for t in card.get('tokens', []):
        if isinstance(t, dict):
            ttype = t.get('type', '')
            if ttype == 'general':
                remaining_general += 1
            else:
                by_new_type[ttype] = by_new_type.get(ttype, 0) + 1

total = sum(by_new_type.values()) + remaining_general
pct = remaining_general / total * 100 if total > 0 else 0

print("=== IMPROVED TOKEN TYPE REPORT ===")
print(f"Tokens improved from 'general': {sum(changes.values())}")
print(f"Remaining 'general': {remaining_general}/{total} ({pct:.1f}%)")
print(f"Target: <20%")
print(f"Result: {'✅ PASS' if pct < 20 else '❌ FAIL'}")
print()
print("New type distribution (excluding general):")
for ttype, count in sorted(by_new_type.items(), key=lambda x: -x[1])[:30]:
    print(f"  {ttype}: {count}")
