# 附屬遊戲檔案總覽 (File Inventory)

## 一覽表

### 根目錄遊戲檔案

| 檔案 | 類型 | 說明 |
|------|------|------|
| `game.py` | Python | 主遊戲引擎文字冒險模組，單一檔案含全部場景、定義與 CLI 呈現邏輯 |
| `run_game.py` | Python | 遊戲啟動器，import 並執行 game.py 的 run_game() |
| `ANGELA_CARD_INTEGRATION_PLAN.md` | Markdown | 卡片系統整合計劃 |

### 設計文檔

位於 `docs/02-game-design/`，以下為當前遊戲設計文檼：

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

### 已存在的舊設計文檼

以下舊文檼屬於之前的遊戲概念，已被新的 RPG 模擬設計取代但保留供參考：

| 檔案 | 說明 | 狀態 |
|------|------|------|
| `angela-design.md` | Angela 角色設計 | 舊概念 |
| `angela-game-entity.md` | Angela 遊戲實體 | 舊概念 |
| `art-asset-specification.md` | 美術資源規範 | 舊概念（本遊戲無圖片） |
| `characters.md` | 角色設計 | 舊概念 |
| `game-main.md` | 主模組設計 | 舊設計參考 |
| `game-systems-overview.md` | 系統總覽 | 舊概念 |
| `game-systems.md` | 遊戲系統統計設計 | 舊設計參考 |
| `game-utils.md` | 遊戲工具 | 舊概念 |
| `inventory.md` | 物品欄設計 | 舊設計 |
| `items-and-inventory.md` | 物品與物品欄 | 舊設計 |
| `items.md` | 物品定義 | 舊概念 |
| `main-design.md` | 主設計 | 舊設計參考 |
| `map-design.md` | 地圖設計 | 舊設計 |
| `minigames.md` | 小遊戲 | 舊概念 |
| `npcs.md` | NPC 系統設計 | 舊設計 |
| `player.md` | 玩家設計 | 舊概念 |
| `scenes.md` | 場景設計 | 舊設計 |
| `success-criteria.md` | 成功標準 | 舊設計 |
| `text-adventure-game-design.md` | 文字冒險遊戲詳細設計 | 舊概念（60KB 完整文本冒險） |
| `tiles.md` | 圖塊設計 | 舊概念 |
| `token-card-system.md` | Token 卡片系統 | 舊系統 |
| `ui.md` | UI 設計 | 已移除（本遊戲無 UI） |
| `world-and-scenes.md` | 世界與場景 | 舊設計 |
| `tiles.md` | 地圖磚設計 | 舊概念 |

### 子目錄舊設計文檼

| 檔案 | 說明 |
|------|------|
| `character-design/angela-design.md` | Angela 角色設計 |
| `character-design/general-characters.md` | 通用角色設計 |
| `scenes/village.md` | 村莊場景設計 |
| `workflow/FLOW_DEMONSTRATION.md` | 工作流程演示 |
| `workflow/STANDARD_PROCESS.md` | 標準流程 |

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

### 遊戲資料

路徑: `data/`

| 檔案 | 大小 | 說明 |
|------|------|------|
| `game_cards.json` | 347 KB | 主卡片資料 |
| `card_registry.json` | 93 KB | 卡片註冊表 |
| `all_cards.json` | 169 KB | 整合卡片資料 |
| `all_cards_final.json` | 381 KB | 最終整合卡片 |
| `parsed_cards.json` | 86 KB | 解析後卡片 |
| `card_deck_inventory.json` | 44 KB | 卡片堆庫存 |

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
