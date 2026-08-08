import json, os, sys

CARDS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "apps", "game-rpg", "data", "game_cards.json")
data = json.load(open(CARDS_PATH, encoding='utf-8'))
cards = data['cards']

# Build: card_id -> all lore tokens (full detail), useful for understanding merchant wares
char_cards = [c for c in cards if c.get('card_type') in ['角色卡','角色補充卡']]

for c in char_cards:
    cid = c.get('card_id','')
    name = c.get('name','?')
    lore_toks = [t for t in c.get('tokens',[]) if t.get('category')=='lore']
    craft_toks = [t for t in c.get('tokens',[]) if t.get('category') in ('craft','trade','product','item')]
    print(f"\n=== {cid}: {name} ===")
    for t in lore_toks:
        n = t.get('name','')
        v = t.get('value','')
        if v and n:
            print(f"  [lore] {n}: {v[:100]}")
    for t in craft_toks:
        n = t.get('name','')
        v = t.get('value','')
        if n:
            print(f"  [craft] {n}: {v[:80]}")

# Also print all craft tokens in any card to understand what trades exist
print("\n\n=== ALL CRAFT TOKENS ACROSS ALL CARDS ===")
seen_craft = {}
for c in cards:
    for t in c.get('tokens',[]):
        if t.get('category') in ('craft','trade','product','item'):
            n = t.get('name','')
            v = t.get('value','')
            key = (c.get('card_id',''), n)
            if key not in seen_craft:
                seen_craft[key] = v
                print(f"  {c.get('card_id','')} [{t.get('category')}] {n}: {v[:60]}")
