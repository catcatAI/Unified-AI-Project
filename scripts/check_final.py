import json
with open('data/all_cards_final.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('Total:', len(data))
by_type = {}
for c in data:
    t = c.get('card_type', 'unknown')
    by_type[t] = by_type.get(t, 0) + 1
for t, cnt in sorted(by_type.items()):
    print(f'  {t}: {cnt}')

missing = [c for c in data if c.get('card_type') in ['故事線卡', '國家卡', '組織卡', '規則卡', '世界觀核心卡', '元設定卡', '專案管理卡']]
print(f'Total missing types: {len(missing)}')
for c in missing[:20]:
    cid = c.get('card_id', '?')
    ctype = c.get('card_type', '?')
    name = c.get('name', '(no name)')[:50]
    print(f'    {cid} [{ctype}]: {name}')