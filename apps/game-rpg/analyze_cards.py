import json, re
import os

_GAME_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# ============================================================
# 1. Parse the catalog from 完整卡片目錄V1.0.txt
# ============================================================
cat_path = os.path.join(_GAME_DATA_DIR, "gdrive_export", "完整卡片目錄V1.0.txt")
with open(cat_path, 'r', encoding='utf-8') as f:
    catalog_text = f.read()

catalog_list = {}

# MULTI-VERSE cards
sl_names = {
    'SL-01': '艦娘：三戰餘暉', 'SL-02': '迴廊物語：像素貓娘與修正者',
    'SL-03': '米亞們：平行世界與感官探險', 'SL-04': '墮落之城的微光',
    'SL-05': '秋狐神明：概念調和者', 'SL-06': '獨立故事線：大正浪漫與鋼鐵殉葬',
    'SL-07': '貓娘的秘密', 'SL-07-A': '貓娘的秘密真相篇（補充）',
    'SL-08': '小說集合', 'SL-09': '農學院（舊版，已廢止）',
    'SL-10': '魔女學府', 'SL-10-A': '魔女學府初始學徒篇（補充）',
    'SL-11': '農學院（新版完整GDD）'
}
for cid, name in sl_names.items():
    t = '故事線補充卡' if cid.endswith('-A') else '故事線卡'
    catalog_list[cid] = {'name': name, 'type': t}

cc_names = {
    'CC-01': '織織', 'CC-02': '壞壞米亞', 'CC-03': '星辰米亞', 'CC-04': '純真米亞／依月',
    'CC-05': '惡意精靈', 'CC-06': '楓', 'CC-07': '亞瑟', 'CC-08': '概念調味師',
    'CC-09': '學徒A', 'CC-10': '學徒B', 'CC-11': '學徒C', 'CC-12': '艾比',
    'CC-12-A': '農學院主角 GSI-4受試者', 'CC-16': '小倉靜子', 'CC-17': '左間小蒼蘭',
    'CC-18': '小狐丸', 'CC-19': '左間カチッ', 'CC-20': '冰喀啦', 'CC-21': '千島雉',
    'CC-22': '千島忠臣', 'CC-23': '千島鐵之介', 'CC-28': '京島伊吹', 'CC-29': '京島楓香',
    'CC-30': '特戰偶像團', 'CC-31': '台灣AI小N', 'CC-32': '雲龍院晴空', 'CC-33': '東雲',
    'CC-34': '萊姆'
}
for cid, name in cc_names.items():
    catalog_list[cid] = {'name': name, 'type': '角色卡'}

rc_names = {f'RC-{i:02d}': n for i,n in enumerate(['迴廊（The Corridor）','迴廊核心區域（核）','迴廊原住民','迴廊異象'],1)}
for cid, name in rc_names.items():
    catalog_list[cid] = {'name': name, 'type': '場域卡'}

wc_names = ['多元宇宙本質','概念的本質與表現','善惡能量平衡','宇宙熵增與失諧','生命進化與惡墮模式',
            '時間與生命哲學','概念能量循環','存在層級與維度','AetherGenesis星神生態圈']
for i,n in enumerate(wc_names,1):
    catalog_list[f'WC-{i:02d}'] = {'name': n, 'type': '世界觀核心卡'}

um_names = ['概念連結網絡','泛用機械與科技','概念污染與淨化','修正者組織/體系','惡意勢力/熵增實體','多元生物圈現象','共鳴點與錨點']
for i,n in enumerate(um_names,1):
    catalog_list[f'UM-{i:02d}'] = {'name': n, 'type': '通用機制卡'}

catalog_list['WT-01'] = {'name': '極致感官描寫風格指南', 'type': '創作工具卡'}
catalog_list['WT-02'] = {'name': '特殊機制與道具描寫指南', 'type': '創作工具卡'}

for i,n in enumerate(['創作狀態追蹤','出版稿件狀態','版本存檔記錄'],1):
    catalog_list[f'PM-{i:02d}'] = {'name': n, 'type': '專案管理卡'}

for i in range(1,19):
    catalog_list[f'MF-{i:02d}'] = {'name': f'元公式 MF-{i:02d}', 'type': '元公式卡'}

catalog_list['SLex-01'] = {'name': '白灰黑名單系統', 'type': '安全詞庫卡'}
catalog_list['WL-01'] = {'name': '世界線錨定框架', 'type': '元設定卡'}
catalog_list['CCK-01'] = {'name': '卡片衝突檢查表', 'type': '元設定卡'}
catalog_list['SC-01'] = {'name': '農學院（The Institute）', 'type': '場景卡'}
catalog_list['SC-02'] = {'name': '魔女學府 M-值工程沙盒', 'type': '場景卡'}

ep_names = ['鋼鐵的遺產 — 防空砲靜子號列裝事件','城主米米與解放','迴廊中的短暫相遇','（未命名）','水晶的覺醒']
for i,n in enumerate(ep_names,1):
    catalog_list[f'EP-{i:02d}'] = {'name': n, 'type': '劇情節點卡'}

catalog_list['ORG-04'] = {'name': '失戀集團', 'type': '組織卡'}
catalog_list['ORG-05'] = {'name': '終末燭光', 'type': '組織卡'}
catalog_list['ORG-06'] = {'name': '新世界集團', 'type': '組織卡'}

# EMPIRICISM CARDS
w_names = ['靈子塵埃（冷戰線/大正線/灰燼未來線）','琥珀紀元（絕對無魔）','軌道居住站大學院','灰燼紀元（後末日）']
for i,n in enumerate(w_names,1):
    catalog_list[f'W{i:02d}'] = {'name': n, 'type': '世界卡'}

s_names = ['聖十字環形堡壘校園','鬱鬱山','煙雲溫泉湖','春日微縮立方','清溪河','鏽蝕城邦（W04）',
           '熒光沼澤（W04）','玻璃荒漠（W04）','極北冰原','高密度大氣結晶行星（夢境層）',
           '綻放混成園（花園茶話會夢境層）','軌道居住站大學院（三層區劃）','鏡山',
           '卡洛夫山脈','鏡湖','卡洛夫角','霧海北海峽','霧海群島','霧海南岸（沙灘與平原）']
for i,n in enumerate(s_names,1):
    catalog_list[f'S{i:02d}'] = {'name': n, 'type': '場景卡'}

c_names_basic = ['霜','露露','椿','春日','冬時','希雅','櫻','冬日','灰燼行者','拾荒王',
                 '吉普莉爾','螢光獵手','磷','姬路','艾菈','愛麗絲']
for i,n in enumerate(c_names_basic,1):
    catalog_list[f'C{i:02d}'] = {'name': n, 'type': '角色卡'}
c_names_ext = ['春','夏','秋','冬','紅','橙','黃','綠','藍','靛','紫']
for i,n in enumerate(c_names_ext,17):
    catalog_list[f'C{i:02d}'] = {'name': n, 'type': '角色卡'}

for i,n in enumerate(['溫泉湖初始態','鬱鬱山側向噴發態','能量枯竭態（Path A/B）']):
    catalog_list[f'E{i:03d}'] = {'name': n, 'type': '事件卡'}

for i,n in enumerate(['聖諭同盟','唯靈聯邦','永久中立地帶','緩衝商業聯合體','武裝中立聯合'],1):
    catalog_list[f'NAT-{i:02d}'] = {'name': n, 'type': '國家卡'}

catalog_list['ORG-01'] = {'name': '彩虹戰隊（正派）', 'type': '組織卡'}
catalog_list['ORG-02'] = {'name': '魔法少女聯合體', 'type': '組織卡'}
catalog_list['ORG-03'] = {'name': '魔法少女溝通部門', 'type': '組織卡'}
catalog_list['ORG-07'] = {'name': '灰衣特勤隊', 'type': '組織卡'}
catalog_list['ORG-08'] = {'name': '迴聲站（情報部門）', 'type': '組織卡'}
catalog_list['ORG-09'] = {'name': '彩虹機甲相關企業', 'type': '組織卡'}

catalog_list['W02-小吉'] = {'name': '小吉 天翼種幼年', 'type': '角色卡'}
catalog_list['W02-雞頭四'] = {'name': '雞頭四 大根莖村祭典執行者', 'type': '角色卡'}

total_catalog = len(catalog_list)
print(f"Catalog total: {total_catalog} cards")

# ============================================================
# 2. Parse game_cards.json
# ============================================================
game_path = os.path.join(_GAME_DATA_DIR, "game_cards.json")
with open(game_path, 'r', encoding='utf-8') as f:
    game_data = json.load(f)

game_cards = {}
for card in game_data['cards']:
    cid = card['card_id']
    game_cards[cid] = {'name': card['name'], 'type': card['card_type']}

total_game = len(game_cards)
print(f"game_cards.json total: {total_game} cards")

# ============================================================
# 3. Cross-reference
# ============================================================
missing = {cid:info for cid,info in catalog_list.items() if cid not in game_cards}
extras = {cid:info for cid,info in game_cards.items() if cid not in catalog_list}

mismatches = {}
for cid, cinfo in catalog_list.items():
    if cid in game_cards:
        ginfo = game_cards[cid]
        if cinfo['type'] != ginfo['type']:
            mismatches[cid] = {'cat_type': cinfo['type'], 'cat_name': cinfo['name'],
                               'game_type': ginfo['type'], 'game_name': ginfo['name']}

print(f"\n=== MISSING CARDS (in catalog but NOT in game_cards): {len(missing)} ===")
missing_by_type = {}
for cid, info in sorted(missing.items()):
    t = info['type']
    missing_by_type.setdefault(t, []).append((cid, info['name']))
for t, items in sorted(missing_by_type.items()):
    print(f"\n  [{t}] ({len(items)})")
    for cid, name in items:
        print(f"    {cid}: {name}")

print(f"\n\n=== EXTRA CARDS (in game_cards but NOT in catalog): {len(extras)} ===")
extra_by_type = {}
for cid, info in sorted(extras.items()):
    extra_by_type.setdefault(info['type'], []).append((cid, info['name']))
for t, items in sorted(extra_by_type.items()):
    print(f"\n  [{t}] ({len(items)})")
    for cid, name in items:
        print(f"    {cid}: {name}")

print(f"\n\n=== TYPE/NAME MISMATCHES: {len(mismatches)} ===")
for cid, info in sorted(mismatches.items()):
    print(f"  {cid}: cat=({info['cat_type']}){info['cat_name']} vs game=({info['game_type']}){info['game_name']}")

# ============================================================
# 4. game_data.py analysis
# ============================================================
print(f"\n\n=== game_data.py PROCESSING ===")
game_types = set(g['type'] for g in game_cards.values())
print(f"Card types in game_cards.json: {sorted(game_types)}")
processed_types = {'角色卡', '場景卡', '劇情節點卡', '組織卡', '國家卡', '規則卡', '技能卡', '故事線卡', '故事線補充卡', '世界觀核心卡', '通用機制卡'}
unprocessed = game_types - processed_types
print(f"Types NOT processed by game_data.py: {len(unprocessed)} {sorted(unprocessed)}")
for t in sorted(unprocessed):
    cnt = sum(1 for g in game_cards.values() if g['type']==t)
    print(f"  [{t}] ({cnt} cards)")

# ============================================================
# 5. Summary
# ============================================================
print(f"\n\n=== SUMMARY ===")
print(f"Catalog cards: {total_catalog}")
covered = sum(1 for c in catalog_list if c in game_cards)
print(f"Covered in JSON: {covered}")
print(f"Missing from JSON: {total_catalog - covered}")
print(f"Coverage: {covered/total_catalog*100:.1f}%")
print(f"Extra (JSON only): {len(extras)}")
print(f"Type mismatches: {len(mismatches)}")
print(f"Total types in JSON: {len(game_types)}")
print(f"Types processed by game_data.py: 6 ({sorted(processed_types)})")
print(f"Types UNPROCESSED: {len(unprocessed)} ({sorted(unprocessed)})")