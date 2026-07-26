# 技術架構 (Architecture)

## 附屬遊戲：角色扮演模擬 — 技術架構

### 資料夾結構

`
D:\\Projects\\Unified-AI-Project\\
│
├── game.py                          # 主遊戲引擎文字冒險模組（單一檔案）
│                                    # 含全部場景、定義、角色狀態、CLI 呈現邏輯
│
├── run_game.py                      # 遊戲啟動器（import 並執行 game.py）
│
├── apps/backend/src/game/           # 遊戲後端模組（正式原始碼區）
│   ├── __init__.py                  # 模組初始化
│   ├── app.py                       # Textual TUI 主應用程式入口
│   ├── engine.py                    # 遊戲主引擎（主循環、輸入處理、NPC 互動、戰鬥）
│   ├── models.py                    # 資料模型
│   ├── npc.py                       # NPC 系統（例行程為、日程表、對話）
│   ├── quests.py                    # 任務系統（主線/支線、任務目標狀態機）
│   ├── i18n.py                      # 多語系統（zh/en/ja）
│   ├── token_effects.py             # Token 效果應用（HP/靈力/技能加成）
│   ├── screens.py                   # 遊戲畫面管理
│   ├── title_screen.py              # 標題畫面
│   ├── gameover_screen.py           # 遊戲結束畫面
│   └── widgets.py                   # TUI 小元件
│
├── apps/backend/src/core/card/      # 卡片系統（遊戲資料來源）
│   ├── __init__.py                  # 模組初始化
│   ├── card_store.py                # 卡片存儲與查詢
│   ├── card_types.py                # 卡片數據結構定義
│   ├── capabilities/                # 卡片能力模組
│   │   ├── __init__.py
│   │   ├── roleplay_engine.py       # 角色扮演引擎
│   │   ├── scene_interpreter.py     # 場景解釋器
│   │   └── story_writer.py          # 故事生成器
│   ├── parser/                      # 卡片解析器
│   │   ├── __init__.py
│   │   ├── deterministic_parser.py  # 確定性解析
│   │   ├── conflict_detector.py     # 衝突檢測
│   │   ├── gdoc_reader.py           # Google 讀取器
│   │   ├── merge_engine.py          # 合併引擎
│   │   └── timeline_resolver.py     # 時間線解析
│   ├── quality/                     # 品質保證
│   │   ├── __init__.py
│   │   ├── gravity_calibration.py   # 重力校準
│   │   └── import_quality_checker.py# 匯入品質檢查
│   ├── resolver/                    # 解析器（多階段處理）
│   │   ├── __init__.py
│   │   ├── llm_fallback.py          # LLM 降級處理
│   │   ├── pipeline_orchestrator.py # 管線編排
│   │   ├── text_gravity.py          # 文字重力系統
│   │   ├── token_extractor.py       # Token 提取
│   └── export/                      # 匯出模組
│       ├── __init__.py
│       ├── html_viewer.py           # HTML 預覽
│       ├── json_exporter.py         # JSON 匯出
│       └── pdf_exporter.py          # PDF 匯出
│
├── data/                            # 遊戲資料
│   ├── game_cards.json              # 主卡片資料（347KB）
│   ├── card_registry.json           # 卡片註冊表（93KB）
│   ├── all_cards.json               # 整合卡片資料（169KB）
│   ├── all_cards_final.json         # 最終整合卡片（381KB）
│   ├── parsed_cards.json            # 解析後卡片（86KB）
│   ├── card_deck_inventory.json     # 卡片堆庫存（44KB）
│   └── npcs.json                    # NPC 資料（若存在）
│
├── scripts/                         # 工具腳本
│   ├── import_card_deck.py          # 卡片堆匯入腳本
│   ├── scan_card_deck.py            # 卡片堆掃描腳本
│   ├── parse_correct.py             # 解析修正工具
│   ├── export_remaining2.py         # 匯出剩餘工具
│   └── ...                          # 其餘工具
│
├── docs/02-game-design/             # 遊戲設計文檔
│   ├── GAME_OVERVIEW.md             ← 遊戲總覽與定位（本文）
│   ├── ARCHITECTURE.md              ← 技術架構（本文）
│   ├── INTERFACE_TERMINAL.md        ← CLI 終端介面（中文）
│   ├── WORLD_AND_STORY.md           ← 世界觀與劇情
│   ├── CHARACTER_SYSTEM.md          ← 角色系統
│   ├── ITEM_EQUIPMENT_SYSTEM.md     ← 物品與裝備
│   ├── NUMERICAL_SYSTEMS.md         ← 數值系統
│   ├── MAP_AND_SCENES.md            ← 地圖與場景
│   ├── SIMULATION_SYSTEMS.md        ← 模擬系統
│   └── FILE_INVENTORY.md            ← 檔案總覽（本文）
│
├── apps/backend/configs/simulated_resources.yaml  # 模擬資源配置
│
├── apps/backend/data/game_data/     # 遊戲資料
│   ├── npcs.json                    # NPC 資料
│   └── knowledge_graph_mapping.json # 知識圖譜映射
│
├── tests/                           # 測試
│   ├── core/card/                   # 卡片系統測試
│   └── ai/meta/                     # AI 元系統測試
│
└── ANGELA_CARD_INTEGRATION_PLAN.md  # 卡片整合計劃（專案根目錄）
`

### 數據流向

`
卡片資料 (data/*.json)
    │
    ▼
CardRegistry (apps/backend/src/core/card/card_store.py)
    │
    ▼
角色生成: Card → GameCharacter (models.py)
場景生成: Card → Scene (models.py)
物品生成: Card → Item (models.py)
任務生成: Card → Quest (quests.py)
NPC 生成: Card → NPC (npc.py)
    │
    ▼
GameEngine (engine.py) — 主循環
    │
    ├── 處理玩家輸入 (process_input)
    ├── 更新 NPC 狀態 (NPC 例行公事)
    ├── 檢查任務進度 (QuestLog)
    ├── 觸發事件 (EventTrigger)
    ├── 計算戰鬥 ( Combat)
    ├── 更新屬性 (TokenEffects)
    └── 輸出 CLI 呈現 (UI/terminal)
`

### 關鍵模組說明

| 模組 | 檔案 | 職責 |
|------|------|------|
| 遊戲引擎 | engine.py | 主循環、輸入處理、NPC 互動、戰鬥、任務追蹤 |
| 資料模型 | models.py | Character, Scene, GameState, Message 資料結構 |
| NPC 系統 | 
pc.py | NPC 類別、例行公事、日程表、對話、好感度 |
| 任務系統 | quests.py | Quest, QuestObjective, QuestLog — 狀態機 |
| 卡片存儲 | card_store.py | 卡片載入、查詢、註冊 |
| 卡片類型 | card_types.py | Card, Token, Relation 等數據結構 |
| 多語系統 | i18n.py | zh/en/ja 三語系統切換 |
| Token 效果 | 	oken_effects.py | Token → HP/靈力/技能加成計算 |

### 與其他專案模組的整合點

| 專案模組 | 整合方式 |
|----------|----------|
| core/card/ | 讀取 CardRegistry 獲取卡片數據 |
| core/life/digital_life_integrator.py | Angela 角色的自主行為 |
| i/memory/ham_memory/ | NPC 記憶和玩家經歷存儲 |
| i/alignment/emotion_system.py | NPC 情緒狀態影響行為 |
| i/meta/meta_controller.py | 動態難度調整 |
| services/angela_llm_service.py | GM 敘事生成 |
| services/llm/ | LLM 後端支援 |
