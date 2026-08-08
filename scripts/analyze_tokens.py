"""Generate token analysis from parsed card data."""
import json
import re
from collections import Counter, defaultdict

with open(r'D:\Projects\Unified-AI-Project\data\parsed_cards.json', 'r', encoding='utf-8') as f:
    cards = json.load(f)

# === Token Extraction ===
# Extract tokens from card fields and content
token_categories = {
    '天賦': [], '技能': [], '興趣': [], '體質': [], '背景': [],
    '狀態': [], '關係': [], '知識': [], '元素': [], '世界觀': []
}

# Known token keywords from the token-card-system.md
TOKEN_KEYWORDS = {
    '天賦': ['時之眼', '匠師魂', '概念共鳴', '術式', '翼膜', '龍娘', '狐娘', '貓娘', '魔女', '天空龍娘'],
    '技能': ['弓道', '機械加工', '駭客', '戰術', '格鬥', '射擊', '潛水', '飛行', '造船', '航海', '煉金', '藥學'],
    '興趣': ['手工藝', '茶道', '閱讀', '音樂', '繪畫', '競速', '收藏'],
    '體質': ['敏感體質', '高代謝', '耐寒', '夜視', '水中呼吸', '翼膜', '再生', '強化'],
    '背景': ['財閥千金', '工匠之女', '極地生存者', '軍人之後', '孤兒', '貴族', '漁夫'],
    '狀態': ['疲憊', '亢奮', '恐懼', '專注', '受傷', '中毒', '強化'],
    '關係': ['信任', '陌生', '敵對', '師徒', '同伴', '敵人', '恋人', '家人'],
    '知識': ['地質學', '靈子理論', '造船知識', '醫學', '法律', '歷史', '戰術', '外交'],
    '元素': ['火', '水', '風', '土', '雷', '冰', '光', '暗', '靈子'],
    '世界觀': ['靈子塵埃', '冷戰線', '大正線', '灰燼線', '魔女學府', '多元宇宙']
}

# Extract all field values
all_field_values = []
for card in cards:
    for k, v in card['fields'].items():
        all_field_values.append(f"{k}: {v}")

# Find tokens in field values
found_tokens = defaultdict(list)
for card in cards:
    card_text = ' '.join(card['fields'].values())
    for category, keywords in TOKEN_KEYWORDS.items():
        for kw in keywords:
            if kw in card_text:
                found_tokens[category].append((card['card_id'], kw))

# === Card Type Statistics ===
type_counts = Counter(c['card_type'] for c in cards)
world_line_counts = Counter(c['world_line'] for c in cards if c['world_line'])
history_line_counts = Counter(c['history_line'] for c in cards if c['history_line'])

# === Field Completeness ===
field_completeness = {}
for card in cards:
    t = card['card_type']
    nf = len(card['fields'])
    if t not in field_completeness:
        field_completeness[t] = {'count': 0, 'total_fields': 0}
    field_completeness[t]['count'] += 1
    field_completeness[t]['total_fields'] += nf

# === Output ===
output = {
    'summary': {
        'total_cards': len(cards),
        'by_type': dict(type_counts),
        'by_world_line': dict(world_line_counts),
        'by_history_line': dict(history_line_counts),
    },
    'token_analysis': {
        'found_tokens': {k: list(set(v for _, v in items)) for k, items in found_tokens.items()},
        'token_counts': {k: len(set(v for _, v in items)) for k, items in found_tokens.items()},
    },
    'field_completeness': field_completeness,
    'cards_with_most_fields': [
        {'card_id': c['card_id'], 'name': c['name'][:50], 'fields': len(c['fields'])}
        for c in sorted(cards, key=lambda x: -len(x['fields']))[:10]
    ],
    'cards_by_world_line': {},
}

# Group cards by world line
for card in cards:
    wl = card['world_line'] or '未分類'
    if wl not in output['cards_by_world_line']:
        output['cards_by_world_line'][wl] = []
    output['cards_by_world_line'][wl].append({
        'card_id': card['card_id'],
        'name': card['name'][:50],
        'type': card['card_type'],
        'fields': len(card['fields'])
    })

# Save
with open(r'D:\Projects\Unified-AI-Project\data\token_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

# Print summary
print("=== TOKEN ANALYSIS ===")
print(f"Total cards: {len(cards)}")
print(f"\nBy type:")
for t, c in sorted(type_counts.items()):
    print(f"  {t}: {c}")
print(f"\nBy world line:")
for wl, c in sorted(world_line_counts.items()):
    print(f"  {wl}: {c}")
print(f"\nTokens found:")
for cat, items in found_tokens.items():
    unique = set(v for _, v in items)
    print(f"  {cat}: {len(unique)} unique — {', '.join(sorted(unique)[:5])}")
print(f"\nTop cards by field count:")
for item in output['cards_with_most_fields'][:5]:
    print(f"  {item['card_id']:12s} | {item['name']:45s} | {item['fields']} fields")

print(f"\nSaved to: D:\\Projects\\Unified-AI-Project\\data\\token_analysis.json")
