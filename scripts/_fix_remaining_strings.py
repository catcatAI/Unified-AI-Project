"""Fix 4 cards with string abilities — convert to dict format."""
import json

CARDS_PATH = 'data/game_cards.json'

with open(CARDS_PATH, 'r', encoding='utf-8') as f:
    gc = json.load(f)

fixed = 0
for card in gc['cards']:
    abilities = card.get('abilities', [])
    new_abilities = []
    has_strings = False
    for a in abilities:
        if isinstance(a, str):
            has_strings = True
            new_abilities.append({"name": a[:30], "description": a, "category": "general"})
        else:
            new_abilities.append(a)
    if has_strings:
        card['abilities'] = new_abilities
        fixed += 1
        print(f"Fixed: {card['card_id']} {card.get('name','?')[:20]} ({len(abilities)} strings→dicts)")

with open(CARDS_PATH, 'w', encoding='utf-8') as f:
    json.dump(gc, f, ensure_ascii=False, indent=2)

print(f"\nTotal cards fixed: {fixed}")
