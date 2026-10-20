# 附屬遊戲檔案總覽 (File Inventory)

## 一覽表

### 根目錄遊戲檔案

路由已整合至 `apps/game-rpg/`（獨立 CLI RPG app）：

| 檔案                                | 類型   | 說明                                                                                                                   |
| ----------------------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------- |
| `apps/game-rpg/game.py`             | Python | 主遊戲引擎文字冒險模組，單一檔案含全部場景定義                                                                         |
| `apps/game-rpg/run_game.py`         | Python | 遊戲啟動器，完整 RPG 迴圈                                                                                              |
| `apps/game-rpg/sim_systems.py`      | Python | 模擬系統層（物品/敵/配方/地圖/任務）                                                                                   |
| `apps/game-rpg/game_data.py`        | Python | 資料展開（expand_game）                                                                                                |
| `apps/game-rpg/character_system.py` | Python | 角色生成/存檔                                                                                                          |
| `apps/game-rpg/axis_system.py`      | Python | 軸譜系統                                                                                                               |
| `apps/game-rpg/world_clock.py`      | Python | 多世界線時間引擎                                                                                                       |
| `apps/game-rpg/game_familiarity.py` | Python | 熟悉度系統                                                                                                             |
| `apps/game-rpg/backbone_bridge.py`  | Python | 主幹線接入（可選 lazy，缺時遊戲照跑）                                                                                  |
| `apps/game-rpg/analyze_cards.py`    | Python | 卡片分析工具                                                                                                           |
| `apps/game-rpg/check_content.py`    | Python | 內容一致性檢查工具                                                                                                     |
| `apps/game-rpg/conftest.py`         | Python | pytest bootstrap（game-rpg 根插入 sys.path）                                                                           |
| `apps/game-rpg/engine/`             | Python | 「萬物皆軸」M1–M9 引擎（12 檔：契約管線/量化/主時鐘/渲染橋/內容快照/精靈視圖/SoA 熱群組/常駐執行器/SkillContext 橋接） |
| `apps/game-rpg/tests/`              | pytest | 單測 306 passed（axis/backbone/craft＋engine M1–M7 七檔）                                                              |
| `apps/game-rpg/data/`               | JSON   | 遊戲資料（唯一權威來源）                                                                                               |

### 設計文檔

位於 `docs/02-game-design/`，以下為當前唯一有效的設計文檔：

| 檔案                                           | 說明                                |
| ---------------------------------------------- | ----------------------------------- |
| `README.md`                                    | 設計文件索引                        |
| `GAME_OVERVIEW.md`                             | 遊戲總覽、定位、系統概覽            |
| `ARCHITECTURE.md`                              | 技術架構、模組結構、數據流向        |
| `INTERFACE_TERMINAL.md`                        | CLI 終端介面設計（不是 UI）         |
| `WORLD_AND_STORY.md`                           | 世界觀、劇情、主線支線任務          |
| `CHARACTER_SYSTEM.md`                          | 角色系統、屬性條、立繪              |
| `ITEM_EQUIPMENT_SYSTEM.md`                     | 物品、裝備、背包、合成              |
| `NUMERICAL_SYSTEMS.md`                         | 數值計算公式與規則                  |
| `MAP_AND_SCENES.md`                            | 地圖、場景、不動產、物件、載具      |
| `SIMULATION_SYSTEMS.md`                        | NPC 作息、行程、生活模擬            |
| `GAME_FAMILIARITY_SYSTEM.md`                   | 熟悉度系統設計                      |
| `GAME_SUBSYSTEM_AUDIT_AND_AXIS_ENGINE_PLAN.md` | 12 子系統盤點與「萬物皆軸」落地計畫 |
| `FILE_INVENTORY.md`                            | 這份文件                            |

### 後端遊戲原始碼

路徑: `apps/backend/src/game/`

| 檔案                 | 說明                                            |
| -------------------- | ----------------------------------------------- |
| `__init__.py`        | 模組初始化                                      |
| `app.py`             | Textual TUI 主應用程式入口                      |
| `engine.py`          | 遊戲主引擎                                      |
| `models.py`          | 資料模型 (Character, Scene, GameState, Message) |
| `npc.py`             | NPC 系統（例行程為、日程表、對話）              |
| `quests.py`          | 任務系統（主線/支線、任務目標狀態機）           |
| `i18n.py`            | 多語系統                                        |
| `token_effects.py`   | Token 效果應用                                  |
| `screens.py`         | 遊戲畫面管理（含小元件，無獨立 widgets 模組）   |
| `title_screen.py`    | 標題畫面                                        |
| `gameover_screen.py` | 遊戲結束畫面                                    |

### 核心卡片系統原始碼

路徑: `apps/backend/src/core/card/`

| 檔案/目錄       | 說明             |
| --------------- | ---------------- |
| `__init__.py`   | 模組初始化       |
| `card_store.py` | 卡片存儲與查詢   |
| `card_types.py` | 卡片數據結構定義 |
| `capabilities/` | 卡片能力模組     |
| `parser/`       | 卡片解析器       |
| `quality/`      | 品質保證         |
| `resolver/`     | 解析器           |
| `export/`       | 匯出模組         |
| `integration/`  | 整合模組         |

### 遊戲資料（卡片堆）

路徑: `apps/game-rpg/data/`（唯一權威來源；根目錄 `data/` 的舊卡片 JSON
`game_cards.json`/`card_registry.json`/`all_cards.json`/`all_cards_final.json`/
`parsed_cards.json`/`card_deck_inventory.json` 已於技術債清理批次刪除）

| 檔案                   | 大小    | 說明                                                   | git    |
| ---------------------- | ------- | ------------------------------------------------------ | ------ |
| `game_cards.json`      | 1.6 MB  | 主卡片資料（351 卡：角色/世界觀/物品/場景/劇情節點等） | 已入庫 |
| `game_supplement.json` | 57 KB   | 補充資料（裝備/敵人/配方等模擬層）                     | 已入庫 |
| `world_clock.json`     | 21 KB   | 主時鐘/世界線/季節（`master_clock` 資料）              | 已入庫 |
| `gdrive_cards.json`    | 250 KB  | Google Drive 卡片匯入中間產物                          | 未入庫 |
| `gdrive_export/`       | 140 txt | 原始卡片目錄文字檔（axis 譜系權威來源）                | 未入庫 |

#### 卡片堆說明

- 卡片堆中的設定文本多為**框架性**的（世界觀、規則、系統），而非具體角色定義
- 角色卡從卡片堆中生成的模式為：隱藏世界中的勇者、村民等角色（角色卡都是勇者+村民的生成模型）
- 卡片提取的差異是「有或沒有」的差異，不是「多或少」的差異
- 卡片堆支撐從隱藏世界觀中動態生成角色（勇者和常規村民均可由框架推算生成）

### 工具腳本

| 檔案                           | 說明           |
| ------------------------------ | -------------- |
| `scripts/import_card_deck.py`  | 卡片堆匯入腳本 |
| `scripts/scan_card_deck.py`    | 卡片堆掃描腳本 |
| `scripts/parse_correct.py`     | 解析修正工具   |
| `scripts/export_remaining2.py` | 匯出剩餘工具   |

### 計算配置

| 檔案                                            | 說明         |
| ----------------------------------------------- | ------------ |
| `apps/backend/configs/simulated_resources.yaml` | 模擬資源配置 |

### 測試

| 檔案/目錄                                             | 說明                                                                                      |
| ----------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `tests/core/card/`                                    | 卡片系統測試                                                                              |
| `tests/ai/meta/`                                      | AI 元系統測試                                                                             |
| `apps/game-rpg/tests/`                                | game-rpg 單測 306 passed（axis/backbone/craft＋engine M1–M7 七檔）                        |
| `tests/game/`                                         | 後端遊戲子系統 29＋CLI echo 冒煙 1（共 30 tests；`test_game_cli_smoke.py` 斷言 8 關鍵幀） |
| `tests/frontend/test_game_asset_contracts.py`         | 遊戲資產契約 10（glb v2/立繪/base_sprite/圖集/卡片自述總和）                              |
| `tests/ai/multimodal/primitives/test_game_sprites.py` | 軸→視覺繪製 53（atlas/幀表/三圖層/四地形＋axis_system 同步鎖定）                          |

### 專案整合計劃

> 三份計劃文檔已於 2026-08-11 自動歸檔至
> `docs/09-archive/auto-archived-2026-08-11/`（根目錄同名檔一併歸檔）。僅作歷史紀錄，非現行計畫——現行遊戲工作以
> `docs/02-game-design/GAME_SUBSYSTEM_AUDIT_AND_AXIS_ENGINE_PLAN.md` 為準。

| 檔案                                                                       | 說明                       |
| -------------------------------------------------------------------------- | -------------------------- |
| `docs/09-archive/auto-archived-2026-08-11/ANGELA_CARD_INTEGRATION_PLAN.md` | 卡片整合計劃（已歸檔）     |
| `docs/09-archive/auto-archived-2026-08-11/CARD_IMPORT_PIPELINE_PLAN.md`    | 卡片匯入管線計劃（已歸檔） |
| `docs/09-archive/auto-archived-2026-08-11/CARD_INTEGRATION_PLAN_REVIEW.md` | 整合計劃審查（已歸檔）     |
