#!/usr/bin/env python3
"""
_fix_ability_types.py — Fix missing ability type fields and short descriptions.

Issues fixed:
1. 161 abilities missing 'type' field → auto-assign based on name keywords
2. 16 character cards with descriptions <100 chars → enrich from available data
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend', 'src'))

CARD_PATH = "data/game_cards.json"

# =============================================================================
# Ability type inference rules
# =============================================================================

# Rule priority: first match wins
_ABILITY_TYPE_RULES = [
    # Combat / attack
    (["戰鬥", "攻擊", "戰技", "格鬥", "劍術", "刀術", "射擊", "破壞", "殲滅",
      "鋼鐵破砕", "暗殺", "獵殺", "暴擊"], "combat"),
    # Passive / inherent
    (["天生特質", "核心能力", "核心矛盾", "核心優勢", "特殊設定", "概念永恆",
      "概念性", "不屈意志", "被動", "痛覺遲鈍", "特殊能力", "能力環境",
      "使命", "世界建構"], "passive"),
    # Knowledge / intelligence
    (["推理", "知識", "研究", "解析", "情報", "AI公式", "數據處理", "感知",
      "時之眼", "共鳴", "核心目的"], "knowledge"),
    # Magic / element
    (["魔法", "魔", "元素", "咒", "術式", "符文", "龍鱗", "天賦型態",
      "能量感知"], "magic"),
    # Support / healing
    (["輔助", "治癒", "恢復", "護盾", "支援", "手作", "交涉"], "輔助"),
    # Special / unique
    (["特殊技能", "事件觸發", "機制", "角色定位", "創作輔助", "特殊"], "special"),
    # Craft
    (["製作", "工匠", "鍛造", "工藝", "料理", "烹飪", "採集", "合成",
      "修理", "手作"], "craft"),
    # Social
    (["社交", "交易", "交涉", "表演", "歌唱", "音樂", "說服", "服務"], "social"),
    # Tech
    (["技術", "科技", "機械", "程式", "數據", "系統", "網路"], "tech"),
]

# =============================================================================
# Short description enrichment (for C-series and template-like cards)
# =============================================================================

_DESCRIPTION_ENRICHMENTS = {
    "C09": "【灰燼行者】\n種族：人類（實證主義·廢土）\n\n在輻射廢土中生存的灰燼行者，擁有敏銳的直感和頑強的生命力。雖然生活在W04的惡劣環境中，但從未放棄對知識的渴望和對世界的探索。以推理能力見長，能在有限的線索中找出真相。",
    "C12": "【螢光獵手】\n種族：精靈（實證主義·螢光）\n\nW04變異兩棲掠奪者，在螢光沼澤中以獨特的適應能力生存。精靈血脈使其擁有超凡的感知力，能在黑暗中精準判斷敵人的位置。戰鬥風格靈活多變，擅長利用環境優勢。",
    "C17": "【春】\n種族：人類（實證主義·春）\n\n魔法少女（春），同時也是小說作家。性格溫柔細膩，善於觀察日常生活中的細節，將其轉化為創作靈感。在實證主義世界中，用文字記錄下這個時代的每一個重要瞬間。",
    "C18": "【夏】\n種族：人類（實證主義·夏）\n\n魔法少女（夏），本職是小學男生，但擁有超乎年齡的成熟與戰鬥天賦。陽光開朗的性格下隱藏著敏銳的洞察力，是團隊中不可或缺的活力來源與戰鬥主力。",
    "C19": "【秋】\n種族：精靈（實證主義·秋）\n\n魔法少女（秋），作為編輯工作，擁有精靈族的長壽與智慧。擅長從繁雜的資訊中提煉出有價值的內容，對世界運行的規律有著獨特的理解。",
    "C20": "【冬】\n種族：人類（實證主義·冬）\n\n魔法少女（冬），中學女生，看似柔弱的外表下有著堅定的意志。在極地環境中成長，培養出超強的適應能力和生存技巧。擅長在嚴酷的條件下保持冷靜思考。",
    "C21": "【紅】\n種族：人類（實證主義·赤）\n\n彩虹戰隊·紅，白天是普通便利店員，夜晚則是守護城市的戰士。熱情如火，正義感強烈，總是第一個衝向危險。擅長近距離戰鬥，以壓倒性的氣勢壓制敵人。",
    "C22": "【橙】\n種族：人類（實證主義·橙）\n\n彩虹戰隊·橙，本職獸醫，擁有溫柔的性格和精湛的手術技巧。在戰場上是可靠的後勤支援，能迅速判斷夥伴的傷勢並進行急救處理。對所有生命都懷有敬意。",
    "C23": "【黃】\n種族：人類（實證主義·黃）\n\n彩虹戰隊·黃，物理教師出身，擅長用科學思維分析戰場局勢。總能在混亂中找到規律，制定出最優的戰鬥策略。冷靜理性的性格使其成為團隊的智囊。",
    "C24": "【綠】\n種族：精靈（實證主義·綠）\n\n彩虹戰隊·綠，在植物店打工的同時守護自然。與植物有著特殊的共鳴能力，能感知環境的細微變化。性格溫和但意志堅定，為了保護生態環境可以奮不顧身。",
    "C25": "【藍】\n種族：人類（實證主義·藍）\n\n彩虹戰隊·藍，客服接線生，練就了超強的多任務處理能力和耐心傾聽的技巧。在戰鬥中擅長協調團隊配合，是最佳的溝通橋樑和戰場調度者。",
    "C26": "【靛】\n種族：人類（實證主義·靛）\n\n彩虹戰隊·靛，油漆師傅出身，對色彩和細節有著敏銳的感知力。擅長設置陷阱和利用環境偽裝，在戰鬥中常以出其不意的方式取得優勢。",
    "C27": "【紫】\n種族：精靈（實證主義·紫）\n\n彩虹戰隊·紫，糕點師兼紫之水晶守護者。優雅從容的舉止下隱藏著強大的魔法天賦。能運用紫色水晶的力量創造防護結界，是團隊最可靠的防禦者。",
    "CC-13": "【希格諾／碧翠絲·海瑟薇】\n種族：人類\n\n魔女學徒同時也是海洋研究者的雙重身份，使希格諾擁有獨特的視角——既能理解科學的邏輯，也能掌握魔法的奧秘。在魔女學府中努力尋找魔法與科學之間的平衡點，並用推理能力解決層層謎團。",
    "CC-14": "【翠森】\n種族：妖精\n\n來自森林深處的妖精，擁有與自然溝通的能力。雖然外表嬌小，但擁有豐富的自然知識和敏銳的直覺。在人類世界中保持著對一切事物的好奇心，常以純真的視角發現被忽略的細節。",
    "CC-15": "【米斯蒂】\n種族：人類\n\n魔女學府見習生，正處於魔法學習的關鍵階段。天賦出眾但略顯青澀，需要通過各種考驗來證明自己的實力。擅長初級魔法和基礎藥劑製作，潛力巨大。",
}

# =============================================================================
# Main fix logic
# =============================================================================

def _infer_ability_type(name: str) -> str:
    """Infer ability type from name using keyword rules."""
    text = name.lower()
    for keywords, atype in _ABILITY_TYPE_RULES:
        for kw in keywords:
            if kw.lower() in text:
                return atype
    return "passive"  # Default fallback

def main():
    print("=== Ability Type & Description Fix ===")
    print()
    
    with open(CARD_PATH, "r", encoding="utf-8") as f:
        gc = json.load(f)
    
    # ---------------------------------------------------------------
    # Fix 1: Missing ability types
    # ---------------------------------------------------------------
    fixed_types = 0
    still_missing = 0
    
    for c in gc["cards"]:
        cid = c.get("card_id", "?")
        for a in c.get("abilities", []):
            if isinstance(a, dict):
                atype = a.get("type", "")
                if not atype or atype == "?":
                    inferred = _infer_ability_type(a.get("name", ""))
                    a["type"] = inferred
                    fixed_types += 1
    
    print(f"Fixed ability types: {fixed_types}")
    
    # Verify no remaining missing
    for c in gc["cards"]:
        for a in c.get("abilities", []):
            if isinstance(a, dict):
                if not a.get("type", "") or a.get("type") == "?":
                    still_missing += 1
    
    print(f"Still missing: {still_missing}")
    print()
    
    # ---------------------------------------------------------------
    # Fix 2: Short card descriptions
    # ---------------------------------------------------------------
    fixed_descs = 0
    still_short = 0
    
    for c in gc["cards"]:
        cid = c.get("card_id", "?")
        desc = c.get("description", "")
        
        if len(desc) < 100 and c.get("card_type") == "角色卡":
            if cid in _DESCRIPTION_ENRICHMENTS:
                c["description"] = _DESCRIPTION_ENRICHMENTS[cid]
                fixed_descs += 1
                print(f"  Enriched: {cid} {c.get('name','?')[:20]} ({len(desc)} → {len(_DESCRIPTION_ENRICHMENTS[cid])} chars)")
            else:
                still_short += 1
    
    print()
    print(f"Enriched descriptions: {fixed_descs}")
    print(f"Still short (<100 chars): {still_short}")
    print()
    
    # ---------------------------------------------------------------
    # Save
    # ---------------------------------------------------------------
    with open(CARD_PATH, "w", encoding="utf-8") as f:
        json.dump(gc, f, ensure_ascii=False, indent=2)
    
    print("Saved to game_cards.json")
    
    # Summary
    print()
    print("=== Summary ===")
    print(f"  Ability types fixed: {fixed_types}")
    print(f"  Descriptions enriched: {fixed_descs}")

if __name__ == "__main__":
    main()
