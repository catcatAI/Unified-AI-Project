import json
import os

_GAME_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "apps", "game-rpg", "data")

def fix_json_file(path, is_final=False):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if is_final:
        cards = data
    else:
        cards = data.get("cards", [])

    mismatches = {
        "CC-12-A": "角色補充卡",
        "CCK-01": "元設定卡",
        "E000": "劇情節點卡",
        "E001": "劇情節點卡",
        "E002": "劇情節點卡",
        "RC-01": "規則卡",
        "RC-02": "規則卡",
        "RC-03": "規則卡",
        "RC-04": "規則卡",
        "W01": "世界觀核心卡",
        "W02": "世界觀核心卡",
        "W03": "世界觀核心卡",
        "W04": "世界觀核心卡"
    }

    for card in cards:
        cid = card.get("card_id")
        # Fix mismatches
        if cid in mismatches:
            card["card_type"] = mismatches[cid]
        
        # Fix NAT-01 to NAT-05 empty names
        if cid in ["NAT-01", "NAT-02", "NAT-03", "NAT-04", "NAT-05"] and not card.get("name"):
            if "fields" in card and "全稱" in card["fields"]:
                card["name"] = card["fields"]["全稱"].split("（")[0].strip()
            else:
                # Fallbacks if fields not present (e.g. in game_cards.json)
                fallbacks = {
                    "NAT-01": "聖諭同盟",
                    "NAT-02": "唯靈聯邦",
                    "NAT-03": "神聖羅馬企業帝國",
                    "NAT-04": "深淵聯盟",
                    "NAT-05": "大正軍國"
                }
                card["name"] = fallbacks.get(cid, card["name"])

    with open(path, 'w', encoding='utf-8') as f:
        if is_final:
            json.dump(cards, f, ensure_ascii=False, indent=2)
        else:
            json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    fix_json_file(os.path.join(_GAME_DATA, "all_cards_final.json"), is_final=True)
    fix_json_file(os.path.join(_GAME_DATA, "game_cards.json"), is_final=False)
    print("Fixed JSON files successfully.")
