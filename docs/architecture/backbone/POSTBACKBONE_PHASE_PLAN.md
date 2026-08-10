<!--
  =============================================================================
  FILE_HASH: TBD
  FILE_PATH: docs/architecture/backbone/POSTBACKBONE_PHASE_PLAN.md
  FILE_TYPE: execution-plan
  PURPOSE: 主幹線完成後的後續執行計畫 — 自由矩陣、多模態字典、座標軸、
          設置與配置、數據集、遊戲接入 六大主題的增量演進藍圖。
  VERSION: 7.5.0-dev
  STATUS: active (draft — to be executed)
  LANGUAGE: zh-TW
  LAST_MODIFIED: 2026-08-10
  AUDIENCE: architects, developers, agents
  =============================================================================
-->

# 主幹線後續執行計畫（六大主題）

> **狀態**: 執行藍圖。主幹線步驟 A（`417d188f`）、B1-B11（`35e17ff5`…`0efc32b9`）、
> C1-C5（`2ee25a66`/`36da6992`/`2b2f87b6`/`37345518`/C5 commit）已提交，里程碑達成
> （`pytest tests/` 全綠：**5,085 passed, 82 skipped**）。
> 本文件定義接下來的六大主題方向，每主題獨立推進、可合併、不互相阻塞。

---

## 0. 背景

主幹線（`core/backbone/`）已建立統一接線層：元件註冊、字典統一協定、訓練掛載、
安全層掛載。但**自由矩陣的深度應用、多模態字典的語義化、座標軸的統一、設置與配置
的可分級、數據集的供給、遊戲的正式接入** 仍是開放議題。本計畫依用戶指定六主題
各立執行章節，每章節含：現況、目標、增量步驟、驗收。

---

## 1. 自由矩陣（Free Matrix）深化

### 現況
- `SharedLatentSpace` 已接 `Mountable`（C1）：`save_weights`/`load_weights`（.npz）、
  `register_mountable` 惰性 factory、`get_backbone()` 自動註冊進程單例。
- `mountable.py` 的 `MountableWrapper` 支援 lazy factory（mount 時才實例化）。
- 尚未做到：**多實例自由矩陣**（不同任務各自矩陣）、**mounted 統計**（現存幾份）、
  **權重版本化**。

### 目標
自由矩陣按需掛載/釋放（memory ↔ disk），多任務並行不互相污染。

### 增量步驟
1. `SharedLatentSpace` 加 `version` / `created_at` 欄位；`save_weights` 支援版本 tag。
2. backbone 加 `free_matrices()` 列出所有已掛載自由矩陣實例與狀態（is_mounted/size）。
3. 遊戲接入（§6）以遊戲專屬自由矩陣實例掛載，與對話主矩陣隔離。

### 驗收
- 新增測試：權重版本 roundtrip、多實例隔離、`free_matrices()` 列出正確。

---

## 2. 多模態字典（Multimodal Dictionaries）語義化

### 現況
- `MultimodalDictionary` 協定（C2）+ 5 實作：`Ed3nDictionaryAdapter`、`GardenDictionaryAdapter`、
  `InMemoryDictionary`、`KeyValueDictionary`（object/space）、`SemanticKeyMapperAdapter`（C4）。
- `DictionaryRegistry.query` 跨字典合併 top_k；`backbone.query_dictionary` 門面。

### 目標
字典查詢有**語義得分**、跨字典結果可比較、可為遊戲卡片（§6）供查。

### 增量步驟
1. `_normalize_hit` 已正規化 tuple/dict → 統一 `{key, score, source}`；加 `score` 標準化
   （各字典自帶 confidence 差異，統一 scale 到 0..1）。
2. 增加 `DictionaryRegistry.sources()`：列出已註冊字典及其 modality。
3. 遊戲卡片文本（`apps/game-rpg/data/game_cards.json`）以 `InMemoryDictionary` 或
   `KeyValueDictionary` 掛載為「遊戲字典」，供 `backbone.query_dictionary("card")` 查詢。

### 驗收
- 新增測試：跨字典 score 標準化、`sources()` 列出遊戲字典、遊戲卡片查詢回傳正確。

---

## 3. 座標軸（Coordinate Axes）統一

### 現況
- 後端核心座標軸分裂在 4 檔案（`core/state/axis.py`、`axis_field.py`、`eta_axis.py`、
  `axis_port_registry.py`）——§1 盤點 #4，主幹線設計記為「待統一 🔧」。
- 遊戲自有 `apps/game-rpg/axis_system.py`（四系譜軸譜：物種/AI/義體人/神話種，各 3 軸，
  五維度親和力 0..1）——與後端核心軸**無關聯**。

### 目標
統一**座標軸介面**（不重寫各自軸語意），讓後端軸與遊戲軸透過同一
`AxesRegistry` 註冊/讀取。

### 增量步驟
1. 新增 `core/backbone/axes.py`：`AxesRegistry`（`register_axis`/`axis`/`list_axes`），
   每軸含 `name`/`dimensions`/`positions`。
2. 遊戲 `axis_system.AXIS_SYSTEMS` 轉譯為 `AxesRegistry` 註冊（不改遊戲本身邏輯，
   只做讀取層）。
3. 後端 4 檔軸核心以 adapter 註冊（不併檔）。

### 驗收
- `backbone.axes("遊戲").axis("物種")` 讀到軸位；後端軸也能列出。新增測試。

---

## 4. 設置與配置（Config & Settings）可分級

### 現況
- 配置分級已存在：`configs/system/*.default.yaml`（bootstrap/core/ed3n/keys/llm/timing/
  capacity/compute）+ `configs/standard/{behavior,matrix,narrative,science,state}/`。
- `magic_numbers.py` 的 `compute_bool/int/float` 已是 profile-aware（§X #263）。

### 目標
遊戲配置（§6）與多模態字典配置納入同一分級體系，`ANGELA_HARDWARE_PROFILE` 可控制。

### 增量步驟
1. 新增 `configs/system/game.default.yaml`（遊戲開關：enabled/mount dictionary/max cards）。
2. `compute_bool("game")` 讀取；`magic_numbers.py` 補 `game` feature 鍵。
3. 配置可被 `setup` 時讀取並寫入 backbone（game dict 掛載）。

### 驗收
- 有 `game.default.yaml`；`compute_bool("game", True)` 讀到正確值。

---

## 5. 數據集（Datasets）供給

### 現況
- `scripts/download_datasets.py` + `scripts/import_dictionaries.py` 已建（CC-CEDICT/JMdict/
  WordNet 460k 條目）。
- 遊戲卡片：`apps/game-rpg/data/game_cards.json`（351 卡，含 relationships/abilities）、
  `game_supplement.json`、`world_clock.json`。

### 目標
遊戲卡片 + 外部字典皆可經由統一數據集入口供給 backbone（查詢/訓練來源）。

### 增量步驟
1. 新增 `apps/backend/src/core/backbone/datasets.py`：`DatasetRegistry`（註冊資料集、
   列出、載入）。
2. 遊戲卡片 JSON 註冊為 `datasets:game_cards`；外部字典維持既有 import 流程。
3. `scripts/` 提供 `python -m` 入口重新生成遊戲字典快取。

### 驗收
- `DatasetRegistry` 列出遊戲卡片資料集、可載入 351 卡。

---

## 6. 遊戲正式接入（矩陣/字典/座標軸）

### 現況
- 遊戲為獨立 CLI（`apps/game-rpg/`），自有軸譜與數值，132 tests 全綠，**未接 backbone**。
- 卡片文本源：`data/gdrive_export/`（雲端硬碟匯出，目前空）→ 各用戶自有 Google Drive
  抽卡片內容，不共享帳戶（安全性已審查：token 未追蹤）。

### 目標
遊戲以 backbone 為中介讀取：矩陣（自由矩陣掛載遊戲專屬空間）、字典（卡片查詢）、
座標軸（AxesRegistry 讀取軸譜），不改變遊戲 CLI 玩法。

### 增量步驟
1. **接入層**：`apps/game-rpg/` 新增 `backbone_bridge.py`——`get_backbone()` 掛載
   遊戲自由矩陣 + 卡片字典 + 軸譜 registry，遊戲 `run_game.py` 惰性讀取。
2. **卡片查詢**：角色卡經 `backbone.query_dictionary("card")` 檢索對應卡。
3. **實際遊玩/對話測試**：跑 `run_game.py` 典型流程找 bug（§風險 3）。
4. **MD 盤點**：`docs/02-game-design/` 12 檔對照實際代碼，脫離者歸檔。

### 驗收
- 遊戲開機能經 backbone 讀到卡片與軸譜；`pytest apps/game-rpg/tests/` 全綠不倒退。

---

## 7. 非目標 / 風險

- ❌ 不重寫遊戲 CLI 玩法、不圖形化。
- ❌ 不強制遊戲依賴後端啟動（backbone_bridge 惰性，缺 backbone 時遊戲照跑）。
- 風險 1：遊戲接 backbone 後啟動變慢 → 只 lazy 掛載卡片字典。
- 風險 2：軸譜雙源（遊戲 + registry）漂移 → 軸譜以 `axis_system.py` 為權威，
  registry 只讀取層。
- 風險 3：實際遊玩找 bug 可能擴散 → 只修影響既有測試者。

---

## 8. 執行順序建議

每主題獨立 commit，順序建議：

| 序 | 主題 | 依賴 |
|---|---|---|
| 1 | §4 設置配置（game.default.yaml 先立） | 無 |
| 2 | §3 座標軸 AxesRegistry | 無 |
| 3 | §1 自由矩陣深化 | C1 已備 |
| 4 | §2 多模態字典語義化 | C2/C4 已備 |
| 5 | §5 數據集供給 | 無 |
| 6 | §6 遊戲接入（用 1-5 成果） | 全部 |
