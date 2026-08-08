import json
import os

CARDS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "apps", "game-rpg", "data", "game_cards.json")
data = json.load(open(CARDS_PATH, encoding='utf-8'))
cards = data['cards']

char_cards = [c for c in cards if c.get('card_type') in ['角色卡','角色補充卡']]
print(f'Total character cards: {len(char_cards)}')
print()

for c in char_cards:
    tok_cats = {t.get('category') for t in c.get('tokens',[])}
    lore_toks = [t for t in c.get('tokens',[]) if t.get('category')=='lore']
    race = next((t.get('value','') for t in lore_toks if '種族' in t.get('name','')), '')
    role = next((t.get('value','') for t in lore_toks if '身份' in t.get('name','') or '職業' in t.get('name','')), '')
    affil = next((t.get('value','') for t in lore_toks if '隸屬' in t.get('name','') or '組織' in t.get('name','') or '所屬' in t.get('name','')), '')
    home_tok = next((t.get('value','') for t in lore_toks if '所在' in t.get('name','') or '主要場景' in t.get('name','') or '家鄉' in t.get('name','')), '')
    # Also get craft/social specific items
    craft_toks = [t for t in c.get('tokens',[]) if t.get('category') in ('craft','knowledge','social','element')]
    craft_items = [t.get('name','') for t in craft_toks if t.get('name','')]
    cid = c.get('card_id','')
    name = c.get('name','?')[:25]
    print(f"{cid:8s} | {name:25s} | race={race[:15]:15s} role={role[:25]:25s} loc={home_tok[:20]:20s} affil={affil[:20]:20s} craft={craft_items[:3]}")
