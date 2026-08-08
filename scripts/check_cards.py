import json
import os
CARDS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "apps", "game-rpg", "data", "game_cards.json")
with open(CARDS_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

cards = data['cards']

# Show scene cards
scene_cards = [c for c in cards if c.get('card_type') == '場景卡']
print('=== SCENE CARDS (24) ===')
for c in scene_cards:
    cid = c.get('card_id', '?')
    name = c.get('name', '?')
    print(f'{cid}: {name}')
    for k in ['connections', 'npcs', 'objects', 'properties', 'entry_requirements', 'scene_type']:
        if k in c:
            print(f'  {k}: {c[k]}')
    print()

# Show org cards
org_cards = [c for c in cards if c.get('card_type') == '組織卡']
print('=== ORG CARDS (16) ===')
for c in org_cards:
    cid = c.get('card_id', '?')
    name = c.get('name', '?')
    print(f'{cid}: {name}')
    for k in ['relations', 'lore']:
        if k in c:
            print(f'  {k}: {c[k]}')
    print()

# Show nation cards
nat_cards = [c for c in cards if c.get('card_type') == '國家卡']
print('=== NATION CARDS (7) ===')
for c in nat_cards:
    cid = c.get('card_id', '?')
    name = c.get('name', '?')
    print(f'{cid}: {name}')
    for k in ['lore']:
        if k in c:
            print(f'  {k}: {c[k]}')
    print()

# Show rule cards
rule_cards = [c for c in cards if c.get('card_type') == '規則卡']
print('=== RULE CARDS (15) ===')
for c in rule_cards:
    cid = c.get('card_id', '?')
    name = c.get('name', '?')
    print(f'{cid}: {name}')
    for k in ['lore', 'mechanism']:
        if k in c:
            print(f'  {k}: {c[k]}')
    print()

# Show story cards
story_cards = [c for c in cards if c.get('card_type') == '故事線卡']
print('=== STORY LINE CARDS (11) ===')
for c in story_cards:
    cid = c.get('card_id', '?')
    name = c.get('name', '?')
    print(f'{cid}: {name}')
    for k in ['lore']:
        if k in c:
            print(f'  {k}: {c[k]}')
    print()