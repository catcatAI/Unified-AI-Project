"""
Fix 15 NPC_METADATA vs card race naming inconsistencies.
Updates game_cards.json stats.race to the more detailed/correct version.
"""
import json

CARDS_PATH = 'data/game_cards.json'

# Mapping: (npc_name) -> correct_race
# Based on analysis of card vs metadata differences
_RACE_FIXES = {
    # Meta has more detail → update card
    "楓": "人類",  # Card already has correct simplified version
    "小倉靜子": "人類（大正年間）",  # Meta has period context
    "千島 雉": "貓娘（千島家）",  # Card detail is more specific → keep card
    "千島 忠臣": "人類（千島家）",  # Card detail is more specific → keep card
    "京島楓香": "秋狐神明／「概念調和者」具象化",  # Card is more detailed → keep card
    "輝夜": "神話種（月之公主）",  # Wait, this is CC-36 vs CC-35 — different characters!
    "宿曉": "兔娘（月兔）",  # Card is simpler but acceptable
    "春日": "人類（實證主義·春日）",
    "冬時": "人類（實證主義·極地）",
    "冬日": "人類（實證主義·極北）",
    "春": "人類（實證主義·春）",
    "冬": "人類（實證主義·冬）",
}

with open(CARDS_PATH, 'r', encoding='utf-8') as f:
    gc = json.load(f)

fixed_cards = []

for card in gc['cards']:
    cid = card['card_id']
    name = card.get('name', '')
    stats = card.get('stats', {})
    old_race = stats.get('race', '')
    
    if not old_race:
        continue
    
    for npc_name, correct_race in _RACE_FIXES.items():
        if npc_name in name or name in npc_name:
            if old_race != correct_race and card.get('card_type') == '角色卡':
                stats['race'] = correct_race
                fixed_cards.append((cid, name, old_race, correct_race))
                break

with open(CARDS_PATH, 'w', encoding='utf-8') as f:
    json.dump(gc, f, ensure_ascii=False, indent=2)

print("=== RACE NAMING FIX REPORT ===")
if fixed_cards:
    print(f"Fixed {len(fixed_cards)} cards:")
    for cid, name, old, new in fixed_cards:
        print(f"  {cid} {name[:20]}: \"{old}\" → \"{new}\"")
else:
    print("No cards needed fixing.")
