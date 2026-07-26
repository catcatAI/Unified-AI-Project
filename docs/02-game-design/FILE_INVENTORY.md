# 附屬遊戲檔案總覽 (File Inventory)

## 一覽表

### 根目錄遊戲檔案

| 檔案 | 類型 | 說明 |
|------|------|------|
| `game.py` | Python | 主遊戲引擎文字冒險模組，單一檔案含全部場景、定義與 CLI 呈現邏輯 |
| `run_game.py` | Python | 遊戲啟動器，import 並執行 game.py 的 run_game() |
| `ANGELA_CARD_INTEGRATION_PLAN.md` | Markdown | 卡片系統整合計劃 |

### 設計文檔

位於 `docs/02-game-design/`，以下為當前唯一有效的設計文檔：

| 檔案 | 說明 |
|------|------|
| `README.md` | 設計文件索引 |
| `GAME_OVERVIEW.md` | 遊戲總覽、定位、系統概覽 |
| `ARCHITECTURE.md` | 技術架構、模組結構、數據流向 |
| `INTERFACE_TERMINAL.md` | CLI 終端介面設計（不是 UI） |
| `WORLD_AND_STORY.md` | 世界觀、劇情、主線支線任務 |
| `CHARACTER_SYSTEM.md` | 角色系統、屬性條、立繪 |
| `ITEM_EQUIPMENT_SYSTEM.md` | 物品、裝備、背包、合成 |
| `NUMERICAL_SYSTEMS.md` | 數值計算公式與規則 |
| `MAP_AND_SCENES.md` | 地圖、場景、不動產、物件、載具 |
| `SIMULATION_SYSTEMS.md` | NPC 作息、行程、生活模擬 |
| `FILE_INVENTORY.md` | 這份文件 |

### 後端遊戲原始碼

路徑: `apps/backend/src/game/`

| 檔案 | 說明 |
|------|------|
| `__init__.py` | 模組初始化 |
| `app.py` | Textual TUI 主應用程式入口 |
| `engine.py` | 遊戲主引擎 |
| `models.py` | 資料模型 (Character, Scene, GameState, Message) |
| `npc.py` | NPC 系統（例行程為、日程表、對話） |
| `quests.py` | 任務系統（主線/支線、任務目標狀態機） |
| `i18n.py` | 多語系統 |
| `token_effects.py` | Token 效果應用 |
| `screens.py` | 遊戲畫面管理 |
| `title_screen.py` | 標題畫面 |
| `gameover_screen.py` | 遊戲結束畫面 |
| `widgets.py` | TUI 小元件 |

### 核心卡片系統原始碼

路徑: `apps/backend/src/core/card/`

| 檔案/目錄 | 說明 |
|------------|------|
| `__init__.py` | 模組初始化 |
| `card_store.py` | 卡片存儲與查詢 |
| `card_types.py` | 卡片數據結構定義 |
| `capabilities/` | 卡片能力模組 |
| `parser/` | 卡片解析器 |
| `quality/` | 品質保證 |
| `resolver/` | 解析器 |
| `export/` | 匯出模組 |
| `integration/` | 整合模組 |

### 遊戲資料（卡片堆）

路徑: `data/`

| 檔案 | 大小 | 說明 |
|------|------|------|
| `game_cards.json` | 347 KB | 主卡片資料（含角色卡、世界觀卡、物品卡、場景卡等） |
| `card_registry.json` | 93 KB | 卡片註冊表 |
| `all_cards.json` | 169 KB | 整合卡片資料 |
| `all_cards_final.json` | 381 KB | 最終整合卡片 |
| `parsed_cards.json` | 86 KB | 解析後卡片 |
| `card_deck_inventory.json` | 44 KB | 卡片堆庫存 |

#### 卡片堆說明

- 卡片堆中的設定文本多為**框架性**的（世界觀、規則、系統），而非具體角色定義
- 角色卡從卡片堆中生成的模式為：隱藏世界中的勇者、村民等角色（角色卡都是勇者+村民的生成模型）
- 卡片提取的差異是「有或沒有」的差異，不是「多或少」的差異
- 卡片堆支撐從隱藏世界觀中動態生成角色（勇者和常規村民均可由框架推算生成）

### 工具腳本

| 檔案 | 說明 |
|------|------|
| `scripts/import_card_deck.py` | 卡片堆匯入腳本 |
| `scripts/scan_card_deck.py` | 卡片堆掃描腳本 |
| `scripts/parse_correct.py` | 解析修正工具 |
| `scripts/export_remaining2.py` | 匯出剩餘工具 |

### 計算配置

| 檔案 | 說明 |
|------|------|
| `apps/backend/configs/simulated_resources.yaml` | 模擬資源配置 |

### 測試

| 檔案/目錄 | 說明 |
|------------|------|
| `tests/core/card/` | 卡片系統測試 |
| `tests/ai/meta/` | AI 元系統測試 |

### 專案整合計劃

| 檔案 | 說明 |
|------|------|
| `ANGELA_CARD_INTEGRATION_PLAN.md` | 專案根目錄的卡片整合計劃 |
| `docs/06-project-management/plans/ANGELA_CARD_INTEGRATION_PLAN.md` | 程式管理中的整合計劃 |
| `docs/06-project-management/plans/CARD_IMPORT_PIPELINE_PLAN.md` | 卡片匯入管線計劃 |
| `docs/06-project-management/plans/CARD_INTEGRATION_PLAN_REVIEW.md` | 整合計劃審查 |
