"""Add favorable/unfavorable outcome descriptions to all world events."""
import json
import os

WC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "apps", "game-rpg", "data", "world_clock.json")

with open(WC_PATH, 'r', encoding='utf-8') as f:
    wc = json.load(f)

outcomes = {
    "EVT-001": {
        "favorable_outcome": "迴廊的結構異常穩定，能量流動順暢，為後世的研究者提供了安全的實驗環境。多個世界線在早期就建立了穩定的連接通道。",
        "unfavorable_outcome": "迴廊初生時就存在結構不穩定的缺陷，部分世界線的連接通道出現裂縫，導致能量洩漏和概念污染，為後來的災難埋下伏筆。"
    },
    "EVT-002": {
        "favorable_outcome": "神靈種與物質世界的生物建立了和諧的共生關係，教導早期文明掌握靈子的基本運用。世界的規則因此而更加豐富多元。",
        "unfavorable_outcome": "神靈種的誕生引發了概念領域的震盪，部分神靈種因無法適應物質世界而墮落，成為後來概念污染的核心來源之一。"
    },
    "EVT-003": {
        "favorable_outcome": "兩殿的制衡機制運作良好，確保了概念世界的穩定發展。正面與負面概念在平衡中共同推動了文明的進步。",
        "unfavorable_outcome": "兩殿的分化導致概念世界的極化加劇，負面概念逐漸累積形成污染核。殿與殿之間的對立為日後的衝突埋下了根源。"
    },
    "EVT-004": {
        "favorable_outcome": "艾莉西亞的研究筆記完整保留，靈子技術的基礎理論得以快速傳播。煉金術與科學的結合開啟了前所未有的技術繁榮。",
        "unfavorable_outcome": "靈子發現的關鍵部分——靈子的意識敏感性——被刻意隱瞞。這導致後續的靈子工業化忽視了安全問題，最終引發了概念污染危機。"
    },
    "EVT-005": {
        "favorable_outcome": "靈子能源的普及極大改善了生活品質，醫療、交通、通訊等領域經歷了革命性進步。平民也能享受到靈子技術帶來的好處。",
        "unfavorable_outcome": "靈子革命加劇了社會不平等。掌握靈子技術的精英階層壟斷了資源，底層民眾被迫成為靈子能源的消耗品。技術進步的代價由弱者承擔。"
    },
    "EVT-006": {
        "favorable_outcome": "迴廊研究的理論框架為後世學者提供了堅實的基礎。重要的安全協議和研究倫理在這個時期被建立起來。",
        "unfavorable_outcome": "早期研究者過於急功近利，忽略了一些關鍵的警告信號。他們錯誤地認為迴廊是可控的，這種過度自信導致了日後的災難。"
    },
    "EVT-007": {
        "favorable_outcome": "衝突促進了靈子軍事技術的快速發展，同時也催生了戰時外交和衝突調解機制。戰爭雖然慘烈，但塑造了後來的國際秩序。",
        "unfavorable_outcome": "長期的戰爭消耗了大量靈子資源，導致多個地區的概念環境遭到不可逆轉的破壞。無數知識和技術在戰火中遺失。戰爭的創傷至今仍在。"
    },
    "EVT-008": {
        "favorable_outcome": "商業聯合體成為重要的中立調解力量，在戰火中保護了大量平民和知識遺產。其建立的商業網絡至今仍然是跨世界貿易的骨幹。",
        "unfavorable_outcome": "商業聯合體表面上中立，實則利用戰爭牟取暴利。他們向雙方出售武器和情報，延長了戰爭的持續時間。中立的外衣下是赤裸裸的利益。"
    },
    "EVT-009": {
        "favorable_outcome": "停戰協定為世界帶來了長達三百年的和平時期。各國將注意力轉向內部發展，文化和科技迎來了黃金時代。",
        "unfavorable_outcome": "停戰協定只是勉強凍結了衝突，並未解決根本矛盾。戰敗方的復仇情緒在暗處滋長，最終形成了像新世界集團這樣的激進組織。"
    },
    "EVT-010": {
        "favorable_outcome": "聖十字校園成為多元宇宙中最重要的知識聖地之一，培養了無數優秀的學者、研究者和守護者。其圖書館保存了最完整的迴廊研究資料。",
        "unfavorable_outcome": "校園的建立吸引了過多注意力，使其成為各方勢力滲透和爭奪的目標。校園內部出現了嚴重的派系鬥爭，部分珍貴資料在內鬥中被銷毀。"
    },
    "EVT-011": {
        "favorable_outcome": "魔女學府在靈子與概念的高階研究上取得了突破性進展。其獨特的教育理念培養出了許多能夠與迴廊直接溝通的天才。",
        "unfavorable_outcome": "魔女學府的封閉式研究和對秘密的執著導致其與主流學術界漸行漸遠。部分極端實驗引發了小規模的概念污染，被迫遷移到更深的山區。"
    },
    "EVT-012": {
        "favorable_outcome": "晞咕萊雅的前輩們完成的標準化理論體系使得迴廊研究變得系統化和可傳承。圖書館的建立保護了大量珍貴知識免於流失。",
        "unfavorable_outcome": "標準化過程中，部分非主流但可能重要的理論被刻意排除。知識的統一也意味著知識的控制，有些真相被鎖在了圖書館最深處的書架上。"
    },
    "EVT-013": {
        "favorable_outcome": "新世界集團的活動引起了各國情報機構的警覺，促使各國加強了對靈子技術的監管和安全合作。其部分極端計劃因過早暴露而失敗。",
        "unfavorable_outcome": "新世界集團成功在暗處站穩了腳跟，收集了大量靈子技術和禁忌知識。他們在各國政府中安插了棋子，擁有了足以撼動世界秩序的力量。"
    },
    "EVT-014": {
        "favorable_outcome": "概念污染事件雖然造成了影響，但也讓人類對概念安全有了更深刻的認識。污染控制技術在這個時期取得了重大突破。",
        "unfavorable_outcome": "概念污染迅速蔓延，影響了多個世界線的生態系統。受到污染的地區出現了扭曲生物和異常現象，部分區域被迫永久隔離。"
    },
    "EVT-015": {
        "favorable_outcome": "千年轉折的預言被正確解讀，各國得以提前做好準備。部分地區甚至利用概念波動開闢了新的靈子能源來源，迎來了短暫的繁榮。",
        "unfavorable_outcome": "千年轉折的能量波動引發了連鎖反應，多個休眠中的概念污染核被激活。預言中的動盪時代比預期更加猛烈地降臨了。"
    },
    "EVT-016": {
        "favorable_outcome": "鏡湖異變的早期預警系統成功運作，聖十字校園及時疏散了師生，沒有人員傷亡。異變也暴露了鏡湖迴廊入口的位置，加速了探索進程。",
        "unfavorable_outcome": "鏡湖異變導致大量概念實體在物質世界具現化，造成了廣泛的混亂和破壞。聖十字校園的師生中出現了多起概念污染案例。"
    },
    "EVT-017": {
        "favorable_outcome": "靈子工業化在唯靈聯邦推動了經濟起飛，創造了大量就業機會。新技術也應用於環境修復，部分受污染地區得到了有效治理。",
        "unfavorable_outcome": "靈子工業化以犧牲安全和環境為代價追求效率。工廠排放的靈子廢料污染了周邊地區，工人們在沒有足夠保護的情況下暴露於高濃度靈子環境中。"
    },
    "EVT-018": {
        "favorable_outcome": "迴廊共鳴促進了多個世界線之間的文化和技術交流，許多長期以來的科學難題在跨世界合作下得到解決。和平發展的新時代由此開始。",
        "unfavorable_outcome": "迴廊共鳴造成的世界線交疊導致了嚴重的身份混淆和現實認知障礙。許多人無法確定自己所屬的世界線，社會秩序一度崩潰。"
    }
}

# Update events (v2 format: events live per world line)
updated = 0
for wl_id, line in wc.get('world_lines', {}).items():
    for evt in line.get('events', []):
        eid = evt.get('id')
        if eid in outcomes:
            evt['favorable_outcome'] = outcomes[eid]['favorable_outcome']
            evt['unfavorable_outcome'] = outcomes[eid]['unfavorable_outcome']
            updated += 1

with open(WC_PATH, 'w', encoding='utf-8') as f:
    json.dump(wc, f, ensure_ascii=False, indent=2)

print(f"Updated {updated} events with outcome descriptions.")
