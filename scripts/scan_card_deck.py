"""Scan card deck files and extract card information from filenames."""
import os
import re
import json

base = r'G:\我的雲端硬碟\卡片堆'
cards = []

for root, dirs, files in os.walk(base):
    for f in files:
        if f.endswith('.gdoc') and f != 'desktop.ini':
            rel_path = os.path.relpath(os.path.join(root, f), base)
            cards.append(rel_path)

# Categorize
results = []
for card in sorted(cards):
    name = card.replace('.gdoc', '')
    
    # Match card ID patterns
    patterns = [
        (r'CC[-\s]?(\d+)', 'CC'),
        (r'RC[-\s]?(\d+)', 'RC'),
        (r'NAT[-\s]?(\d+)', 'NAT'),
        (r'ORG[-\s]?(\d+)', 'ORG'),
        (r'EP[-\s]?(\d+)', 'E'),
        (r'SL[-\s]?(\d+)', 'SL'),
        (r'SC[-\s]?(\d+)', 'SC'),
        (r'WC[-\s]?(\d+)', 'WC'),
        (r'SK[-\s]?(\d+)', 'SK'),
        (r'IT[-\s]?(\d+)', 'IT'),
    ]
    
    card_id = None
    card_type = 'OTHER'
    for pattern, ctype in patterns:
        m = re.search(pattern, name)
        if m:
            card_id = f'{ctype}-{m.group(1)}'
            card_type = ctype
            break
    
    # Detect type from Chinese keywords
    if card_type == 'OTHER':
        if '角色卡' in name or '角色' in name:
            card_type = 'CHARACTER'
        elif '場景卡' in name or '場景' in name:
            card_type = 'SCENE'
        elif '規則卡' in name or '規則' in name:
            card_type = 'RULE'
        elif '國家卡' in name or '國家' in name:
            card_type = 'NATION'
        elif '組織卡' in name or '組織' in name:
            card_type = 'ORGANIZATION'
        elif '設定卡' in name or '設定' in name:
            card_type = 'SETTING'
        elif '劇情' in name or '事件' in name:
            card_type = 'EVENT'
        elif '卡組' in name or '卡組' in name:
            card_type = 'CARD_SET'
        elif '目錄' in name or '統計' in name:
            card_type = 'INDEX'
        elif 'token' in name.lower() or 'Token' in name:
            card_type = 'TOKEN_DEF'
    
    results.append({
        'card_id': card_id,
        'name': name,
        'type': card_type,
        'path': card,
        'world_line': 'W01' if '迴廊' in name or '多元宇宙' in name else ('W02' if '艦娘' in name else ''),
    })

# Print summary
print(f'=== Card Deck Summary ===')
print(f'Total .gdoc files: {len(cards)}')
print()

# Group by type
by_type = {}
for r in results:
    t = r['type']
    if t not in by_type:
        by_type[t] = []
    by_type[t].append(r)

for t in sorted(by_type.keys()):
    items = by_type[t]
    print(f'--- {t} ({len(items)}) ---')
    for item in items:
        cid = item['card_id'] or '[?]'
        print(f'  {cid}: {item["name"]}')
    print()

# Save as JSON
output_path = r'D:\Projects\Unified-AI-Project\data\card_deck_inventory.json'
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f'Saved inventory to {output_path}')
