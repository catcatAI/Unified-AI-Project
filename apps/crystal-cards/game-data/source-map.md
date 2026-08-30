# Crystal Cards — 資料來源對照表

> 最後更新：2026-08-31
> 目的：追蹤每筆遊戲內容的來源、整合狀態、和遺漏

---

## 資料來源一覽

| # | 來源 | 路徑 | 內容 | 數量 |
|---|------|------|------|------|
| A | **game_cards.json** | `apps/game-rpg/data/game_cards.json` | 角色卡、場景卡、國家卡、組織卡、技能卡、事件卡、規則卡、世界觀卡 | 100 張 |
| B | **sim_systems.py** | `apps/game-rpg/sim_systems.py` | 物品、敵人、配方、地圖、NPC 時間表 | ~200 項 |
| C | **game_supplement.json** | `apps/game-rpg/data/game_supplement.json` | 藥草、艦娘裝備、動物素材、元素裝備 | ~160 項 |
| D | **Google Drive txt** | `apps/game-rpg/data/gdrive_export/` | 原始卡片文本、設定集、小說 | 122 檔案 |

---

## 整合狀態：地點

### 21 個地點（全部來自 WORLD_MAP in sim_systems.py）

| 地點 | 來源 | Crystal Cards ID | 敵人分佈 | 狀態 |
|------|------|-----------------|---------|------|
| 聖十字校園 | B | loc_holy_cross | 哥布林, 盜賊, 野狼 | ✅ |
| 鏡湖 | B | loc_mirror_lake | 晶石蜘蛛, 暗影靈, 蛇妖 | ✅ |
| 卡洛夫角 | B | loc_market | 盜賊, 廢鐵傀儡, 蛇妖 | ✅ |
| 迴廊 | B | loc_corridor | 晶石蜘蛛, 暗影靈, 雷靈 | ✅ |
| 森林深處 | B | loc_forest | 巨熊, 野狼, 蛇妖, 元素核心 | ✅ |
| 廢棄礦坑 | B | loc_abandoned_mine | 巨熊, 晶石蜘蛛, 廢鐵傀儡 | ✅ |
| 英靈殿 | B | loc_hall_of_heroes | 古代守衛, 幽靈, 元素核心 | ✅ |
| 鏽蝕城邦 | B | loc_rust_city | — | ✅ |
| 軌道居住站 | C | loc_orbital_station | — | ✅ |
| 中央大圖書館 | B | loc_library | 幽靈, 暗影靈, 晶石蜘蛛 | ✅ |
| 便利店 | B | loc_convenience_store | 盜賊, 哥布林 | ✅ |
| 鬱鬱山 | B | loc_yuyu_mountain | 巨熊, 野狼, 哥布林 | ✅ |
| 霧海群島 | B | loc_fog_islands | 蛇妖, 古代守衛, 幽靈 | ✅ |
| 秘密鐵工廠 | B | loc_secret_ironworks | 廢鐵傀儡, 哥布林 | ✅ |
| 煙雲溫泉湖 | B | loc_hot_spring | 暗影靈, 晶石蜘蛛 | ✅ |
| 清溪河 | B | loc_clear_stream | 野狼, 蛇妖 | ✅ |
| 鏡山 | B | loc_mirror_mountain | 石像鬼, 幽靈, 古代守衛 | ✅ |
| 農學院 | B | loc_agriculture | 石像鬼, 廢鐵傀儡, 毒蛇 | ✅ |
| 魔女學府 | B | loc_witch_academy | 石像鬼, 暗靈, 火靈 | ✅ |
| 極北冰原 | B | loc_frozen_wastes | 大冰靈, 水馬, 猛禽 | ✅ |
| 西翼大市集 | B | loc_west_market | 盜賊, 野狼 | ✅ |

**WORLD_MAP 連結：** 完整的地圖連結系統在 `game-rpg-content.md` Part VII。

---

## 整合狀態：角色

### 7 個已整合角色（Crystal Cards → 來源驗證）

| 角色 | 來源 | 原始位置 | Crystal Cards 位置 | 原始能力 | Crystal Cards 能力 | 狀態 |
|------|------|---------|-------------------|---------|-------------------|------|
| 晞咕萊雅 | A(CC-38)+D | 中央大圖書館 | loc_library | 結構化編目, 震動感知, 低耗能認知, 古籍修復 | 結構化編目, 震動感知, 低耗能認知, 古籍修復 | ✅ |
| 紅 | A(C22)+B | **便利店** | loc_convenience_store | 談判, 情報收集, 觀察力 | 談判, 情報收集, 觀察力 | ✅ |
| 織織 | A(CC-01)+D | 迴廊 | loc_corridor | 概念共鳴, 像素化 | 概念共鳴, 像素化, 迴廊感知 | ✅ |
| 宿曉 | A(CC-37) | 聖十字校園 | loc_holy_cross | 手作, 感知, 交涉 | 手作, 感知, 交涉 | ✅ |
| 姬路 | A(C14) | 聖十字校園 | loc_holy_cross | 智慧, 領導, 治癒 | 智慧, 領導, 治癒 | ✅ |
| 吉普莉爾 | A(C11) | **天空神殿圖書館** | loc_library | 高速閱讀, 資訊仲介, 天翼防衛 | 高速閱讀, 資訊仲介, 天翼防衛 | ✅ |
| 露露 | A(C02) | **跨世界貿易** | loc_market | 交易, 情報收集, 跨世界貿易 | 交易, 情報收集, 跨世界貿易 | ✅ |

### 未整合角色（game_cards.json 有但 Crystal Cards 沒有）

**角色卡 (game_cards.json)：** 100 張中有 ~80 張未整合

關鍵缺失角色（有完整數據）：

| ID | 名稱 | 種族 | 位置 | 可用性 |
|----|------|------|------|--------|
| CC-02 | 壞壞米亞 | 貓娘 | 中央大圖書館 | ⚠️ |
| CC-03 | 星辰米亞 | 狐妖→艦娘 | — | ⚠️ |
| CC-04 | 純真米亞 | 花妖娘 | — | ⚠️ |
| CC-06 | 楓 | 秋狐神明 | — | ⚠️ |
| CC-16 | 小倉靜子 | 人類（大正） | 聖十字校園 | ⚠️ |
| CC-17 | 左間小蒼蘭 | 人類 | 秘密鐵工廠 | ⚠️ |
| CC-18 | 小狐丸 | 神話（刀劍） | 鏡湖 | ⚠️ |
| CC-20 | 冰喀啦 | 半神話龍娘 | 鏡湖 | ⚠️ |
| CC-28 | 京島伊吹 | 狐娘 | 聖十字校園 | ⚠️ |
| CC-29 | 京島楓香 | 人類（魔女） | 魔女學府 | ⚠️ |
| CC-38 | 晞咕萊雅 | 拉米雅 | 中央大圖書館 | ✅ 已整合 |
| CC-39 | 暈咔繆露 | 拉米雅 | 中央大圖書館 | ⚠️ |
| CC-40 | 髂審芬蒂 | 阿拉克涅 | 中央大圖書館 | ⚠️ |
| CC-41 | 芬喀涅 | 阿拉克涅 | 中央大圖書館 | ⚠️ |
| CC-49 | 晞吶 | 拉米雅 | 方碑丘 | ⚠️ |
| CC-50 | 翎翾 | 哈比 | — | ⚠️ |
| CC-51 | 夜鈴 | 蝙蝠娘 | — | ⚠️ |
| C01 | 霜 | 艦娘 | — | ⚠️ |
| C03 | 椿 | 狐娘 | — | ⚠️ |

---

## 整合狀態：物品

### 10 個基礎物品（Crystal Cards 手寫）

| ID | 名稱 | 來源 | 狀態 |
|----|------|------|------|
| item_flashlight | 火把 | 手寫 | ✅ |
| item_map | 地圖 | 手寫 | ✅ |
| item_knife | 小刀 | 手寫 | ✅ |
| item_crystal | 迴廊之水晶 | 手寫 | ✅ |
| item_key_corridor | 迴廊鑰匙 | 手寫 | ✅ |
| item_photo | 舊照片 | 手寫 | ✅ |
| item_memory_orb | 記憶球 | 手寫 | ✅ |
| item_courage | 勇氣液 | 手寫 | ✅ |
| item_glow_fruit | 發光果實 | 手寫 | ✅ |
| item_corridor_pearl | 迴廊之珠 | 手寫 | ✅ |

### 67 個 RPG 物品（來自 sim_systems.ITEM_CATALOG）

**已整合 ✅** — 全部 67 項（材料 14 + 消耗品 10 + 武器 7 + 防具 7 + 飾品 5 + 任務 5 + 垃圾 18 + 修復 1）

### 26 個藥草（來自 game_supplement.json herbal_items）

**已整合 ✅**

### 57 個艦娘裝備（來自 game_supplement.json naval_data）

**已整合 ✅**

### 59 個動物素材（來自 game_supplement.json animal_data）

**已整合 ✅**

### 18 個元素裝備（來自 game_supplement.json elemental_items）

**已整合 ✅**

---

## 整合狀態：敵人

### 5 個基礎敵人（Crystal Cards 手寫）

| ID | 名稱 | 狀態 |
|----|------|------|
| enemy_shadow | 暗影 | ✅ |
| enemy_echo | 迴音 | ✅ |
| enemy_crystal_golem | 水晶魔像 | ✅ |
| enemy_corridor_beast | 迴廊獸 | ✅ |
| enemy_spirit_drain | 靈子吸取者 | ⚠️ 名稱含「靈子」 |

### 22 個 RPG 敵人（來自 sim_systems.ENEMIES + elemental_enemies）

**已整合 ✅**

---

## 整合狀態：配方

### 6 個基礎配方（Crystal Cards 手寫）

| ID | 名稱 | 來源 | 狀態 |
|----|------|------|------|
| recipe_1 | 製作火把 | 手寫 | ✅ |
| recipe_2 | 調製藥水 | 手寫 | ✅ |
| recipe_3 | 合成水晶 | 手寫 | ✅ |
| recipe_4 | 鍛造工具 | 手寫 | ✅ |
| recipe_5 | 封印迴廊之力 | 手寫 | ✅ |
| recipe_6 | 培育發光果實 | 手寫 | ✅ |

### 18 個 RPG 配方（來自 sim_systems.RECIPES）

**已整合 ✅**

---

## 整合狀態：對話

### 52 個對話（Crystal Cards 手寫）

| 角色 | greeting | 子對話數 | 狀態 |
|------|----------|---------|------|
| 晞咕萊雅 | ✅ | 5 | ✅ |
| 紅 | ✅ | 3 | ✅ |
| 織織 | ✅ | 4 | ✅ |
| 宿曉 | ✅ | 4 | ✅ |
| 姬路 | ✅ | 5 | ✅ |
| 吉普莉爾 | ✅ | 4 | ✅ |
| 露露 | ✅ | 4 | ✅ |
| tutorial | ✅ | 3 | ✅ |
| corridor | ✅ | 5 | ✅ |
| ending | ✅ | 2 | ✅ |

---

## 整合狀態：商店

### 50 個商店目錄（來自 game_supplement.json NPC 商店關鍵字）

**已整合 ✅**

### 30 個 NPC 道具（來自 game_supplement.json NPC 專屬道具）

**已整合 ✅**

---

## 待整合（下一步）

### 高優先級
1. **新增角色**：冰喀啦(CC-20)、小狐丸(CC-18)、小倉靜子(CC-16)、京島伊吹(CC-28)、京島楓香(CC-29)
2. **修正**：enemy_spirit_drain 名稱（移除「靈子」）
3. **新增**：中央大圖書館其他成員（暈咔繆露、髂審芬蒂、芬喀涅）

### 中優先級
4. **新增角色**：壞壞米亞(CC-02)、星辰米亞(CC-03)、純真米亞(CC-04)
5. **新增對話**：為新角色設計對話
6. **新增地點連結**：WORLD_MAP 的方向連結系統

### 低優先級
7. **新增角色**：魔法少女系列(C17-C20)、彩虹戰隊(C22-C27)
8. **新增組織卡**：脈動工業(ORG-08)、永恆義體(ORG-09)、鐵砧防務(ORG-10)
9. **新增國家卡**：莫比迪克自由邦聯(NAT-06)、阿比薩深淵聯邦(NAT-07)
10. **新增規則卡**：骰子判定系統、蝠群規則(RC-12)
