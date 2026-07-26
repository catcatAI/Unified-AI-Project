"""
CORRECT APPROACH: 
1. Find ALL 510 "項目 內容" blocks
2. For each block, find the card ID it belongs to by scanning backwards
3. A block belongs to a card ID if the ID appears BEFORE the block (within 5000 chars)
4. Use the NEAREST card ID to the block
5. If multiple blocks map to the same card ID, keep the one with most fields
"""
import json
import re
import os
from collections import Counter

EXPORT_DIR = 'D:/Projects/Unified-AI-Project/data/gdrive_export'

all_files = {}
for fname in os.listdir(EXPORT_DIR):
    if not fname.endswith('.txt'):
        continue
    with open(os.path.join(EXPORT_DIR, fname), 'r', encoding='utf-8') as f:
        all_files[fname] = f.read()

TYPE_MAP = {
    'CC': '角色卡', 'RC': '規則卡', 'ORG': '組織卡', 'NAT': '國家卡',
    'EP': '劇情節點卡', 'SL': '故事線卡', 'SC': '場景卡', 'WC': '世界觀核心卡',
    'UM': '通用機制卡', 'WT': '創作工具卡', 'PM': '專案管理卡', 'MF': '元公式卡',
    'SLex': '安全詞庫卡', 'WL': '元設定卡', 'CCK': '卡片衝突檢查',
}

def detect_type(cid):
    for prefix, ct in TYPE_MAP.items():
        if cid.startswith(prefix):
            return ct
    if re.match(r'S\d{2}', cid):
        return '場景卡'
    return '未知'

def extract_fields(text):
    fields = {}
    header = re.search(r'項目\s+內容|項目\t內容', text)
    if not header:
        return fields
    after = text[header.end():]
    for line in after.split('\n'):
        line = line.strip()
        if not line or line in ('項目', '內容', '---'):
            continue
        if re.match(r'^(---+|📇|#+\s)', line):
            break
        if '\t' in line:
            parts = line.split('\t', 1)
            if len(parts) == 2 and len(parts[0].strip()) <= 30:
                k, v = parts[0].strip(), parts[1].strip()
                if k and v and k not in ('項目', '內容'):
                    fields[k] = v
        else:
            # Match: key (1-30 chars, no spaces) + space(s) + value
            m = re.match(r'^([^\s]{1,30})\s+(.+)$', line)
            if m:
                k, v = m.group(1).strip(), m.group(2).strip()
                if k and v and k not in ('項目', '內容'):
                    fields[k] = v
    return fields

# Step 1: Find ALL field blocks and their nearest card IDs
all_blocks = []  # (card_id, fields, fname, block_pos)

for fname, text in all_files.items():
    blocks = list(re.finditer(r'項目\s+內容|項目\t內容', text))
    
    for block in blocks:
        block_pos = block.start()
        
        # Find ALL card IDs within 5000 chars BEFORE this block
        search_start = max(0, block_pos - 5000)
        search = text[search_start:block_pos]
        
        ids_before = list(re.finditer(
            r'(?:CC|RC|ORG|NAT|EP|SL|SC|WC|UM|WT|PM|MF|SLex|WL|CCK)-\d{1,3}[A-Z]?|\bS(?:0[1-9]|1[0-7])\b',
            search
        ))
        
        if not ids_before:
            continue
        
        # Use the NEAREST (last) card ID
        cid = ids_before[-1].group()
        
        # Extract fields from block to next block or 3000 chars
        next_pos = block_pos + 3000
        for b in blocks:
            if b.start() > block_pos:
                next_pos = b.start()
                break
        
        fields = extract_fields(text[block_pos:next_pos])
        if not fields:
            continue
        
        all_blocks.append((cid, fields, fname, block_pos))

print(f"Total field blocks with card IDs: {len(all_blocks)}")

# Step 2: For each card ID, keep the block with most fields
best_blocks = {}
for cid, fields, fname, pos in all_blocks:
    if cid not in best_blocks or len(fields) > len(best_blocks[cid]['fields']):
        best_blocks[cid] = {
            'fields': fields,
            'source_file': fname,
        }

print(f"Unique card IDs with field blocks: {len(best_blocks)}")

# Step 3: Build card list
cards_list = []
for cid, data in sorted(best_blocks.items()):
    name = data['fields'].get('姓名', data['fields'].get('卡片名稱', data['fields'].get('組織名稱', data['fields'].get('名稱', ''))))
    cards_list.append({
        'card_id': cid,
        'card_type': detect_type(cid),
        'name': name,
        'fields': data['fields'],
        'source_file': data['source_file'],
    })

# Step 4: Add narrative cards (EP-xxA/B/C) without field blocks
for fname, text in all_files.items():
    for m in re.finditer(r'(EP-\d{1,2}[A-D])\s+(.+?)(?:\n|$)', text):
        cid, desc = m.group(1), m.group(2).strip()
        if len(desc) > 5 and cid not in best_blocks:
            cards_list.append({
                'card_id': cid, 'card_type': detect_type(cid),
                'name': desc[:100], 'fields': {'description': desc},
                'source_file': fname,
            })

cards_list.sort(key=lambda c: c['card_id'])
total_fields = sum(len(c['fields']) for c in cards_list)
structured = [c for c in cards_list if len(c['fields']) >= 2]

print(f"\n=== FINAL RESULTS ===")
print(f"Total cards: {len(cards_list)}")
print(f"Structured (2+ fields): {len(structured)}")
print(f"Total fields: {total_fields}")

with open('D:/Projects/Unified-AI-Project/data/all_cards_final.json', 'w', encoding='utf-8') as f:
    json.dump(cards_list, f, ensure_ascii=False, indent=2)

# Coverage
all_ids = set()
for fname, text in all_files.items():
    for m in re.finditer(r'(?:CC|RC|ORG|NAT|EP|SL|SC|WC|UM|WT|PM|MF|SLex|WL|CCK)-\d{1,3}[A-Z]?|\bS(?:0[1-9]|1[0-7])\b', text):
        all_ids.add(m.group())

parsed_ids = set(c['card_id'] for c in cards_list)
missing = all_ids - parsed_ids
print(f"\nCoverage: {len(parsed_ids)}/{len(all_ids)} ({100*len(parsed_ids)/len(all_ids):.1f}%)")
if missing:
    print(f"Missing ({len(missing)}): {sorted(missing)[:30]}")

fc = Counter(len(c['fields']) for c in cards_list)
print(f"\nField distribution:")
for k in sorted(fc.keys()):
    print(f"  {k} fields: {fc[k]} cards")

print(f"\nTop cards:")
for c in sorted(cards_list, key=lambda c: len(c['fields']), reverse=True)[:20]:
    print(f"  {c['card_id']}: {len(c['fields'])} fields - {c.get('name','?')[:45]}")
