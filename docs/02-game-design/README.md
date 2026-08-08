# 遊戲設計文件索引 (Game Design Index)

## 附屬遊戲：角色扮演模擬

本專案的附屬遊戲是一個 **CLI 命令列角色扮演模擬**，不包含圖形化 UI，所有互動透過終端文字完成。

---

## 核心文檔

| 文件 | 內容 | 定位 |
|------|------|------|
| [GAME_OVERVIEW.md](GAME_OVERVIEW.md) | 遊戲總覽、定位、系統概覽 | 入門必讀 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 技術架構、模組結構、數據流向 | 開發者必讀 |
| [INTERFACE_TERMINAL.md](INTERFACE_TERMINAL.md) | CLI 終端呈現方式（不是 UI） | 所有文件 |
| [WORLD_AND_STORY.md](WORLD_AND_STORY.md) | 世界觀、劇情、主線支線 | 設計者參考 |
| [CHARACTER_SYSTEM.md](CHARACTER_SYSTEM.md) | 角色系統、屬性條、立繪 | 所有文件 |
| [ITEM_EQUIPMENT_SYSTEM.md](ITEM_EQUIPMENT_SYSTEM.md) | 物品、裝備、背包、合成 | 所有文件 |
| [NUMERICAL_SYSTEMS.md](NUMERICAL_SYSTEMS.md) | 數值計算公式與規則 | 開發者必讀 |
| [MAP_AND_SCENES.md](MAP_AND_SCENES.md) | 地圖、場景、不動產、物件 | 設計者參考 |
| [SIMULATION_SYSTEMS.md](SIMULATION_SYSTEMS.md) | NPC 作息、行程、生活模擬 | 設計者參考 |
| [FILE_INVENTORY.md](FILE_INVENTORY.md) | 所有遊戲檔案總覽 | 管理必讀 |

---

## 系統概覽

### 角色
- **PC (玩家角色)**: 可選擇現有 NPC 或新建角色卡
- **NPC**: AI 驅動，有獨立作息和生活圈
- **GM**: Angela AI 負責敘事和演算法则

### 三色屬性條
- 🔴 紅條 (身體): HP, 身體, 肢體
- 🔵 藍條 (靈): 靈活躍度, 體力, 魔力
- 🟢 綠條 (經歷): 經驗, 級別, 技能

### 系統結構
```
卡片資料 → CardRegistry → 角色/場景/物品生成 → GameEngine
                                                        ↓
                                              CLI 終端呈現
```

---

## 檔案位置

```
D:\Projects\Unified-AI-Project\
├── apps/game-rpg/                   # 附屬 CLI RPG 遊戲（自洽 app）
│   ├── game.py                      # 主遊戲引擎
│   ├── run_game.py                  # 遊戲啟動器
│   ├── data/                        # 遊戲資料（唯一權威來源）
│   └── tests/                       # 遊戲單元測試
├── apps/backend/src/game/           # Textual TUI 遊戲模組
├── docs/02-game-design/            # 設計文檔 (本文索引所在目錄)
│   ├── README.md                    # ← 這份文件
│   ├── GAME_OVERVIEW.md
│   ├── ARCHITECTURE.md
│   ├── INTERFACE_TERMINAL.md
│   ├── WORLD_AND_STORY.md
│   ├── CHARACTER_SYSTEM.md
│   ├── ITEM_EQUIPMENT_SYSTEM.md
│   ├── NUMERICAL_SYSTEMS.md
│   ├── MAP_AND_SCENES.md
│   ├── SIMULATION_SYSTEMS.md
│   └── FILE_INVENTORY.md
├── apps/backend/src/core/card/     # 卡片系統
├── apps/game-rpg/data/             # 遊戲資料（唯一權威來源）
├── scripts/                         # 工具腳本
└── ANGELA_CARD_INTEGRATION_PLAN.md  # 整合計劃
```

---

## 設計原則

1. **CLI 優先**: 所有交互透過終端文字完成，無 GUI
2. **符號立繪**: 角色立繪由 ASCII/Unicode 符號組成，非圖片
3. **模擬導向**: NPC 有完整生活圈、作息與社交系統
4. **數據驅動**: 卡片系統作為遊戲內容主要來源
5. **三色條系統**: 紅藍綠三色屬性條構成角色核心狀態
