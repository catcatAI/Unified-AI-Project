"""
Fix game_cards.json token issues:

1. All token dicts are missing 'category' field — game code (character_system.py:274-286)
   uses t.get("category") to calculate character stats (HP, SP, ATK, DEF, etc.),
   but all 1598 tokens default to category "unknown" or empty.

2. 45 cards have string tokens (e.g., ["人類", "維護員", "經驗", "調査者"])
   instead of dict tokens — t.get("category") on a string crashes.

Token categories expected by game code:
  vitality     — HP/life/body/health related
  combat       — combat/fighting/battle related
  craft        — crafting/making/building related
  knowledge    — knowledge/learning/study related
  social       — social/interaction/relationship related
  element      — elements/magic/energy related
  energy       — energy/power/force related
  exploration  — exploration/adventure/discovery related
  general      — default fallback
"""
import json
import os
import re

CARDS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "apps", "game-rpg", "data", "game_cards.json")

# ── Category keyword rules ──────────────────────────────────────────────
# Rules: (category, [list of keywords to match in token name or value])
# Priority: first match wins
_CATEGORY_RULES = [
    ("vitality", [
        "體力", "生命", "生命力", "活力", "體質", "耐久", "HP", "恢復",
        "耐力", "血量", "生存", "健康", "治癒", "復活", "護盾", "防護",
        "防禦力", "defense", "vitality", "stamina", "heal", "shield",
        "傷", "痛", "疲勞", "fatigue", "pain", "流血", "bleed",
        "身體", "感官", "器官", "代謝", "生理", "體能", "肌肉",
    ]),
    ("combat", [
        "戰鬥", "攻", "戰", "鬥", "武", "兵", "劍", "刀", "槍", "弓",
        "戰術", "攻擊", "atk", "attack", "combat", "武器", "盾",
        "格鬥", "近戰", "遠程", "射擊", "炮", "彈", "爆",
        "暗殺", "刺殺", "殺", "殲滅", "破壞", "毀滅", "傷害",
        "身法", "步法", "連擊", "重擊", "暴擊", "crit",
        "戰技", "軍", "隊", "傭兵", "護衛", "警", "士兵",
        "實戰", "獵殺", "狩獵", "獵人", "追獵",
    ]),
    ("craft", [
        "製作", "工匠", "鍛造", "工藝", "craft", "製造", "合成",
        "煉金", "調和", "料理", "烹飪", "裁縫", "木工", "石工",
        "修理", "修復", "改造", "加工", "組裝", "分解",
        "材料", "素材", "工具", "設備", "裝置", "機關",
        "採集", "挖礦", "採礦", "釣魚", "收穫", "農業", "種植",
        "建築", "建設", "設計", "圖紙", "藍圖", "零件",
        "手工", "創作", "編織", "雕刻", "繪畫",
    ]),
    ("knowledge", [
        "知識", "知識", "學識", "學問", "研究", "學習", "閱讀",
        "書", "圖書", "文獻", "資料", "情報", "資訊", "理論",
        "教學", "教育", "指導", "講師", "教師", "老師", "學生",
        "魔法", "術式", "咒", "符文", "符號", "文字", "語言",
        "歷史", "考古", "古代", "傳說", "文獻",
        "解析", "分析", "調查", "探索", "實驗", "驗證",
        "記錄", "記憶", "回憶", "筆記", "日記", "檔案",
        "科學", "技術", "數學", "物理", "化學", "天文", "地理",
        "knowledge", "study", "research", "learn", "wisdom",
    ]),
    ("social", [
        "社交", "社會", "人際", "溝通", "交流", "對話", "說服",
        "交易", "商", "買賣", "貿易", "商業", "市場", "店鋪",
        "交涉", "談判", "協商", "外交", "聯盟", "合作",
        "魅力", "領袖", "領導", "管理", "組織", "團隊",
        "聲望", "名聲", "信譽", "信用", "關係", "好感",
        "表演", "歌唱", "音樂", "舞蹈", "藝術", "娛樂",
        "服務", "接待", "照顧", "幫助", "支援", "支持",
        "情感", "情緒", "心情", "態度", "脾氣",
        "social", "charisma", "trade", "bargain",
    ]),
    ("element", [
        "元素", "元素", "屬性", "火", "炎", "水", "冰", "風", "雷",
        "電", "土", "地", "光", "闇", "暗", "無", "時", "空",
        "概念", "靈子", "魔法", "魔力", "mana", "element",
        "神性", "神力", "信仰", "祈禱", "祝福", "詛咒",
        "自然", "森林", "海洋", "天空", "大地", "星辰",
        "龍", "竜", "神", "精靈", "惡魔", "天使",
        "核", "核心", "結晶", "晶", "光輝",
    ]),
    ("energy", [
        "能量", "能源", "動力", "電力", "靈力", "氣", "內力", "法力",
        "體力", "活力", "精力", "energy", "power", "force",
        "電池", "燃料", "消耗", "充能", "充電", "續航",
        "熱", "冷", "電", "磁", "輻射", "波動", "頻率",
        "靈", "魂", "精神", "意志", "意識", "念",
        "蒸氣", "steam", "機械", "機關",
        "共鳴", "共振", "迴廊",
    ]),
    ("exploration", [
        "探索", "探險", "冒險", "旅行", "移動", "通行", "道路",
        "地圖", "導航", "方向", "座標", "位置", "路線",
        "發現", "尋", "找", "搜索", "偵察", "探測",
        "野外", "荒野", "森林", "山", "洞穴", "地下",
        "速度", "敏捷", "spd", "speed", "靈巧", "輕盈",
        "飛行", "奔跑", "跳躍", "游泳", "攀爬", "騎乘",
        "運輸", "交通", "車輛", "載具", "船", "車", "馬",
        "exploration", "explore", "adventure", "travel",
        "隱匿", "潛行", "躲藏", "stealth", "偵查",
    ]),
]

def categorize_token(name: str, value: str) -> str:
    """Determine token category by matching name/value against keyword rules."""
    text = (name + " " + value).lower()
    for category, keywords in _CATEGORY_RULES:
        for kw in keywords:
            if kw.lower() in text:
                return category
    return "general"

def fix_tokens(tokens):
    """Fix a token list: add category to dicts, convert strings to dicts."""
    fixed = []
    for t in tokens:
        if isinstance(t, str):
            # Convert string token to dict
            name = t[:20] if len(t) > 20 else t
            cat = categorize_token(t, t)
            fixed.append({"category": cat, "name": name, "value": t})
        elif isinstance(t, dict):
            # Add category if missing
            if not t.get("category"):
                tname = t.get("name", t.get("id", ""))
                tval = t.get("value", "")
                t["category"] = categorize_token(tname, tval)
            # Ensure name field exists
            if not t.get("name") and t.get("id"):
                t["name"] = t["id"]
            fixed.append(t)
        else:
            fixed.append(t)
    return fixed

# ── Main ────────────────────────────────────────────────────────────────

with open(CARDS_PATH, 'r', encoding='utf-8') as f:
    gc = json.load(f)

total_cards = len(gc['cards'])
total_fixed = 0
string_fixed = 0
category_added = 0

for card in gc['cards']:
    tokens = card.get('tokens', [])
    if not tokens:
        continue
    
    # Check for string tokens before fix
    has_strings = any(isinstance(t, str) for t in tokens)
    no_cat_dicts = sum(1 for t in tokens if isinstance(t, dict) and not t.get('category'))
    
    if has_strings or no_cat_dicts > 0:
        old_tokens = list(tokens)
        card['tokens'] = fix_tokens(tokens)
        total_fixed += 1
        if has_strings:
            string_fixed += 1
        if no_cat_dicts > 0:
            category_added += no_cat_dicts

with open(CARDS_PATH, 'w', encoding='utf-8') as f:
    json.dump(gc, f, ensure_ascii=False, indent=2)

print("=== TOKEN FIX REPORT ===")
print(f"Total cards processed: {total_cards}")
print(f"Cards with fixes applied: {total_fixed}")
print(f"Cards with string→dict fixes: {string_fixed}")
print(f"Token dicts with category added: {category_added}")

# Verify
print()
print("=== VERIFICATION ===")
all_cats = set()
missing_cat_count = 0
string_count = 0
for card in gc['cards']:
    for t in card.get('tokens', []):
        if isinstance(t, str):
            string_count += 1
        elif isinstance(t, dict):
            cat = t.get('category', '')
            all_cats.add(cat)
            if not cat:
                missing_cat_count += 1

print(f"Remaining string tokens: {string_count}")
print(f"Remaining missing category: {missing_cat_count}")
print(f"Categories used: {sorted(all_cats)}")
print()
if string_count == 0 and missing_cat_count == 0:
    print("✅ ALL TOKENS FIXED SUCCESSFULLY!")
else:
    print("⚠️ Some issues remain — see above.")
