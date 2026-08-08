import json
import os

CARDS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "apps", "game-rpg", "data", "game_cards.json")
data = json.load(open(CARDS_PATH, encoding='utf-8'))
cards = data['cards']

# ORG cards
org_cards = [c for c in cards if c.get('card_type') == '組織卡']
print(f'ORG cards: {len(org_cards)}')
for c in org_cards:
    tok_cats = {t.get('category') for t in c.get('tokens',[])}
    lore_toks = [t for t in c.get('tokens',[]) if t.get('category') in ('lore','craft','trade','product')]
    cid = c.get('card_id','')
    name = c.get('name','')[:30]
    print(f'  {cid:8s} | {name:30s} | cats={str(tok_cats)[:50]}')
    for t in lore_toks[:5]:
        print(f'          tok: {t.get("name","")[:20]} = {t.get("value","")[:50]}')

print()

# Also check SC (scene) cards - they define important locations
scene_cards = [c for c in cards if c.get('card_type') == '場景卡']
print(f'SCENE cards: {len(scene_cards)}')
for c in scene_cards:
    tok_cats = {t.get('category') for t in c.get('tokens',[])}
    cid = c.get('card_id','')
    name = c.get('name','')[:40]
    print(f'  {cid:8s} | {name:40s} | cats={str(tok_cats)[:50]}')
