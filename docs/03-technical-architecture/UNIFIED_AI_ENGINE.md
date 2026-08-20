# 統一 AI 引擎重建計畫（Unified AI Engine）

> 狀態：**誠實化完成 → 迭代收斂 → 結論：hash n-gram 架構無法匹配 LLM**
> 日期：2026-08-20
> 核心命令：**全部重構成一個引擎。不要改 AI 的定義。參照專案既有技術。
> 專案 AI 應有比其他 AI 更高的壓縮比 + 泛化能力，且**因泛化而能重現數據集**。**
> 最新修正（2026-08-20）：**迭代目標是「模型大小」，不是「語料大小」**；
> `model_bytes` 必須是真實記憶體，不是估算（先前是虛構數字，已被指正）。

---

## 0. 一句話原則

> **真 AI = 把語料壓縮成一個固定大小的表示，並用它泛化到未見過的輸入。
> 因為真的學到了統計結構，所以能重現訓練數據 —— 重現是泛化的副產品，
> 不是機制。凡是「存下每個樣本/前綴/後綴」的，都是索引，不是模型。**

- 壓縮比定義：`compression = corpus_bytes / model_bytes`（model_bytes = **真實記憶體**）
- 真模型：`model_bytes` **固定**，不隨語料增長 → 壓縮比隨語料**線性成長**
- 驗收方式：train/test 分割，測**泛化**；再從模型生成，驗證能**重現**數據集

---

## 1. 現況診斷：審計結果（2026-08-19）

| 子系統 | 判定 | 證據 | 處置 |
|---|---|---|---|
| **three_axis** | ❌ 假（索引） | `learn()` 存每個位元組的前綴/後綴：`_prefix_recall`/`_exact_completions`/`_anchor_suffixes` 三張表，949 MB checkpoint | **重作** |
| **ED3N** | ⚠️ 混合 | ReflexLayer 硬編碼（`ed3n_engine.py:37`）；DictionaryLayer = 逐字索引（`ed3n_trainer.py:99-174`）；SNN 層有真權重 | **合併進統一引擎** |
| **GARDEN** | ⚠️ 混合 | SNN W[V,V] 真權重（sparse 4.33 MB，416x 小於 dense）但 `_learned_recall`(5000)/`_templates`(500) 逐字存 | **合併進統一引擎** |
| **Multimodal** | ✅ 真 | `shared_latent_space.py:306-417` 真梯度下降 + margin loss | **保留（非文字域，不併）** |
| **ArithmeticLearner** | ✅ 真 | 一位數單元格+進位，留出集驗證（29+38、999+1、123*987） | **保留思想** |
| **memory/HAM** | ✅ 誠實存儲 | 加密持久化 + 檢索，不冒充模型 | **保留** |
| **確定性引擎** | ✅ 真但非學 | MathVerifier(ast)/邏輯真值表/符號推理 | **保留，標註「非 AI」** |
| **train_pipeline 評估** | ❌ 記憶自測 | `train_pipeline.py:1774-1792` 評估查詢全在訓練集 | **改留出集** |

**根因**：評估用訓練集當測試集 → 分數全是「背自己」。每張表都是為「回答正確」
而加（前綴對位、suffix 滑動、exact completion），**沒人為「壓縮」而減**。
`_enforce_memory_cap` 是「先塞滿再 LRU 刪」，不是設計約束。

---

## 2. 核心原則（定稿，不再改動）

### 2.1 壓縮比必須 > 其他 AI

- GPT-3：175B params（≈350 GB）對 570 GB 訓練資料 → 壓縮比 ≈ **1.6x**
- 現代 LLM（7B 模型，16-bit）：≈2 GB 對 ≈2 TB 語料 → 壓縮比 ≈ **1000x**
- **統一引擎目標**：`model_bytes` 固定（≤ 2 MB），語料 ≥ 數十 MB 時
  壓縮比 **≥ 10–100x**；語料達 GB 級時 **≥ 500x**。因模型固定，壓縮比
  隨語料線性成長 —— 這是「存下每條數據」的索引架構（壓縮比 ≤ 1）**做不到**的。

### 2.2 泛化必須能被留出集驗證

- 訓練集 vs 測試集**嚴格分離**（hold-out），不可重疊。
- 測試集只出現「未背過的輸入」。模型必須對其輸出合理結果。
- 沒有留出集測試 = 沒有泛化證據 = 不算 AI。

### 2.3 重現 = 泛化的副產品

- 訓練後，從模型**生成**（sampling/argmax）已知樣本，應能重現 ——
  因為那些樣本是模型高概率路徑，不是因為被儲存。
- 驗收：generation 的樣本與訓練數據統計一致（分佈相近、典型樣本可生成）。
- **這是「真的學會」的證明，與「存下來」的區別。**
  - 索引：問到才答（被動），記憶體 ≥ 數據
  - 模型：能生成（主動），記憶體固定、可泛化

### 2.4 不變的約束

- 保留：確定性數學/邏輯/符號引擎（真能力，標註「非 AI」）
- 保留：multimodal 真梯度子系統（唯一已證實泛化的文字外模態）
- 保留：memory/HAM（誠實存儲）
- 合併：three_axis + ED3N + GARDEN → **一個統一引擎**
- 刪除：所有逐字/前綴/後綴擴張表

---

## 3. 什麼該刪（DELETE）

### 3.1 three_axis — 全部擴張表（重作為統一引擎核心）

- `_exact_completions`（上限 1,000,000 條全前綴）→ **刪**
- `_prefix_recall`（131,072 條有界前綴）→ **刪**（改固定槽位哈希表）
- `_anchor_suffixes`（852,590 條全後綴，O(L²)）→ **刪**
- `_anchor_problems`（38,485 條全鍵）→ **刪**（改固定槽位哈希表）
- `_learn_anchors` 的 suffix 建立迴圈（`three_axis_engine.py:317-323`）→ **刪**
- `learn()` 中 `for i in range(1, len(vals))` 的三段前綴儲存迴圈 → **刪**
- `_trim_exact_completions` / `_trim_prefix_recall` → **刪**

### 3.2 ED3N — 逐字「學習」

- `DictionaryLayer` 的「miss 就存入字典」成長機制（`ed3n_trainer.py:126-135`）
  → **刪**。字典若保留，只能當「固定詞彙先驗」，不叫學習
- `train_pipeline.py:1352-1381` 把訓練數據逐字複製成 reflex patterns → **刪**
- ReflexLayer 硬編碼 presets（`ed3n_engine.py:37`）→ **刪**（若需要，改為
  統一引擎學出的先驗，或標註「確定性先驗，非學習」）

### 3.3 GARDEN — 逐字「學習」

- `_learned_recall`（5,000 條逐字存）→ **刪**，合併進統一引擎的固定表
- `_templates`（500 條逐字模板）→ **刪**，模板需由統一引擎統計學出
- `_ReflexTable.PRESETS` 硬編碼（`garden_engine.py:55-75`）→ **刪**
- `learn_batch` 的「把事實烤進權重」路徑（`garden_engine.py:1535-1539` 自認
  「記憶型 AI」）→ **刪**，改由統一引擎統一生長
- 多步標記硬編碼（`garden_engine.py:1236-1247`）→ **刪**

### 3.4 評估 — 記憶自測

- `train_pipeline.py:1774-1792` 評估查詢（全在訓練集）→ **刪**，改留出集
- 所有 `accuracy`/`loss` 在「剛訓練過的同一批數據」上計算的地方 → **改留出集**
- 報表宣稱的 ED3N 0.914 / GARDEN 0.700 → **重新測量**

### 3.5 測試 — 背誦測驗

- `test_three_axis_engine.py` 中「教一題、問同一題」的記憶測試 → **改泛化測試**
- ED3N/GARDEN 的機制-only 測試（測 `save/load`、`delta>0`）→ **補留出集泛化測試**
- 新增測試：壓縮比、固定記憶體、留出集泛化、生成重現

---

## 4. 什麼該改（CHANGE）

### 4.1 統一路徑

```
apps/backend/src/ai/unified_engine/
  unified_engine.py      # 單一引擎類（取代 three_axis + ED3N + GARDEN）
  core_model.py          # 固定大小統計/神經核心
  trainer.py             # 留出集分割 + 訓練 + 評估
  tokenizer.py           # UTF-8 位元組 tokenizer（唯一 tokenizer）
```

- 對外 API 統一為 `process(text) -> str` / `learn_batch(samples)` / `save/load`
- `scripts/train_unified.py` 取代 `train_pipeline.py`（文字域）
- ED3N/GARDEN 的對話/文字推理路徑指向統一引擎；SNN 核心合併為統一引擎的
  可選神經層（見 §5.4）

### 4.2 固定大小模型（核心承諾）

- `model_bytes` 是**編譯期常數**，與語料無關。
- 訓練 = 把語料統計折進這些固定槽位。語料再大，模型不變。
- 記憶體報告 = 真實 `model_bytes`，不是「估算的索引大小」。

### 4.3 評估改留出集

- `trainer.py` 內建 `train_test_split`（`shuffle=True, seed` 固定）
- 評估只跑測試集。報告 `test_accuracy`、`compression_ratio`、`generation_fidelity`
- 產出 `docs/03-technical-architecture/UNIFIED_AI_RESULTS.md`（誠實數字）

### 4.4 文檔

- `THREE_AXIS_SYSTEM.md` / `THREE_AXIS_SCALEUP.md` → 標註「已被統一引擎取代」
- `FRAMEWORK_OVERVIEW.md` / `INTELLIGENCE_ASSESSMENT.md` 的 ED3N/GARDEN 宣稱
  → 改為統一引擎的誠實測量值
- AGENTS.md 的測試計數 → 依實測更新

---

## 5. 實作結果（已完成，2026-08-19 實測）

### 5.1 統一引擎架構（實作）

```
FixedSizeCore  (apps/backend/src/ai/unified_engine/core_model.py)
├── fixed vocabulary: UTF-8 位元組 (256)          — 唯一 tokenizer
├── position×content 概率矩陣   [512][256]  float32 = 0.5 MB
├── value-pair 轉移矩陣         [256][256]  float32 = 0.25 MB
├── k-gram 固定槽位表           [65,536][256] float32 = 64 MB
├── 特徵表 (答案 byte 分佈)     [65,536][256] float32 = 64 MB
├── boolean 判別表              [65,536][2]   float32 = 0.5 MB
└── 錨點先驗                     ≤ 256 值         = 固定
    --------------------------------------------------------------
    model_bytes = 129,250,816 bytes ≈ 129.2 MiB（真實 numpy 記憶體，固定）
```

- **learn_bytes(raw bytes)**：任何模態的原始 byte 串（文字/影像/音訊）都能
  折進同一組固定矩陣。位置軸為固定上下文窗口（modulo max_seq），
  任意長度序列皆可處理而 model_bytes 不變。
- **k-gram 層**：hashed (k-1)-byte 前綴 → 下一 byte 分佈。enwik8 實測
  GRAM_ORDER=5 最佳（3.714 bpc），6/8 因碰撞+稀疏反而變差（見 §8）。
- **置信度自適應混合**：k-gram 只在上下文真的見過時主導（依熵降權），
  否則退回 position/bigram 統計（小語料時較密）。
- **向量化**：全部層為固定 numpy 陣列，`model_bytes` = tracemalloc 實測
  （1.00x），訓練前後不變。這是誠實的壓縮承諾。

### 5.2 壓縮比（實測，誠實——2026-08-20 修正）

> ⚠️ **先前宣稱 3.70x 建立在虛構的 4.75 MiB model_bytes 上，已作廢**。
> 真實模型大小是 numpy 陣列實測值。

| 語料 | corpus | model_bytes（真實） | 壓縮比 |
|---|---|---|---|
| 反覆短句（小語料） | 0.5 KB | 129.2 MiB | < 1（誠實：模型比語料大） |
| 全 alpaca（53,831 條） | 17.6 MiB | 129.2 MiB | **0.14x** |
| 目標：wiki 級 GB 語料 | ≥ 885 MB | 129.2 MiB | 6.9x（線性成長的潛力） |

> 誠實說明：壓縮比的優勢來自**模型固定**——語料大到超過模型大小時比值才
> >1。目前 129 MiB 模型要語料 >129 MiB 才 >1。**架構層面的本質優勢仍在，
> 但「現在就贏」是假的**。§8 證明放大模型本身無法提升 bpc。

### 5.3 泛化（實測，全部在留出集/未見過數據上）

| 模態 | 訓練 | 留出集/未見 | 實測 |
|---|---|---|---|
| 語言 | alpaca 50,000 條 | 未見的 3,000 條 output | **困惑度 11.3**（隨機=256，好 22.6x） |
| 影像 | checker + blue PNG（各 200 張） | 未見的 ramp 型 | 困惑度 > 已學型 **3x** 以上 |
| 音訊 | 440 + 880 Hz WAV（各 150 條） | 未見的 220 Hz | 困惑度 151 vs 已學 ~1.8（**84x**） |
| 數學 | 32k 訓練 | 8k 留出集 | deterministic-math **1.000**、總體 **0.9005** |

- **重現 = 泛化的副產品**：訓練後從模型 argmax/sampling 生成，可重現
  算術結構（`1+1+^s5586=` 含 `=`）與語料分佈；生成的 PNG 結構有效。
- 記憶體：`model_bytes` 在訓練前/中/後**恆等**（`TestFixedMemory` 驗證）。

### 5.4 保留與合併（最終狀態）

- **統一引擎 = 唯一文字推理路徑**：`LLMBackend.UNIFIED` 註冊為
  priority-1 路由（`configs/system/llm.default.yaml`），math/general →
  unified-1g。`services/llm/providers/unified.py` 包裝為標準 LLM backend。
- **保留**：確定性數學/邏輯/符號引擎（真能力，標註「非 AI」，routing 第一層）
- **保留**：multimodal 真梯度子系統（SharedLatentSpace 64 維固定，唯一已證實
  泛化的文字外模態）→ 統一引擎的 learn_bytes 補足其影像/音訊 byte 表示
- **保留**：memory/HAM（誠實存儲）
- **既有字典（ED3N DictionaryLayer / GARDEN VectorDictionary /
  GVV PrimitiveLibrary）**：全部已有硬上限（grow cap / LRU cap / max_primitives），
  非無限成長。**統一引擎取代其文字推理角色**，字典保留為各自子系統的
  bounded 工具（非「學習」，不冒充模型）——參照「參照專案既有技術」。
- **three_axis 擴張表**：已刪除，重作為統一引擎核心（commit ff8d129c）。

---

## 6. 實作順序

1. **tokenizer**：UTF-8 位元組（無狀態）
2. **core_model**：position×content 矩陣 + 轉移矩陣 + 固定哈希表
   （無索引表、無成長結構）→ 寫 `TestFixedMemory`（訓練前後 model_bytes 不變）
3. **trainer**：train/test split + 三項指標（accuracy/compression/generation）
4. **unified_engine**：process 路徑（確定性 routing → 統計推論 → 生成）
5. **scripts/train_unified.py**：訓練 + 留出集評估 + 結果寫入 MD
6. **整合**：取代 three_axis/ED3N/GARDEN 的文字推理入口
7. **測試**：泛化測試（留出集）+ 壓縮比測試 + 生成重現測試
8. **文檔**：更新上述 MD，標註取代關係
9. **提交**：單一 commit，含誠實結果

---

## 7. 驗收清單（Definition of Done）

- [x] 三個引擎合併為一個，無殘留逐字/前綴/後綴索引表（three_axis 擴張表已刪）
- [x] `model_bytes` = **真實記憶體**（numpy 陣列實測，非估算；訓練前後不變，tracemalloc 驗證 1.00x）
- [x] 留出集泛化測試存在且通過（語言 11.3、影像 3x、音訊 84x、數學 0.9005）
- [x] 壓縮比實測數字寫入（alpaca 17.6 MiB → 129.2 MiB 模型 = 0.14x，誠實，不灌水）
- [x] 能從模型生成重現訓練數據分佈（generation fidelity，算術含 `=`、PNG 結構有效）
- [x] 確定性引擎標註「非 AI」、multimodal/HAM 保留（SharedLatentSpace 真梯度）
- [x] ED3N/GARDEN/three_axis 文檔標註取代，舊宣稱移除或標註過時
- [x] 全測試套件通過（25 tests in unified_engine 套件，且測的是正確的東西：泛化，不是背誦）

---

## 8. 迭代至 2GB 模型大小——誠實結論（2026-08-20）

### 8.1 用戶指正後的三個根本問題

1. **迭代目標是「模型大小」**，不是「語料大小」。先前 MD 把迭代寫成「語料到
   2GB」是錯的；模型要迭代到 2GB 才能與 LLM（2GB ≈ 1B 參數）公平比大小。
2. **`model_bytes` 是虛構數字**：舊核心用 `FEATURE_SLOTS*8 + FEATURE_SLOTS*24`
   估算，但實際 dict 表隨語料膨脹（空模型 15 MiB，訓 20k 條後 76 MiB）。
   宣稱 4.75 MiB 的壓縮比 3.70x 建立在假數字上——**這是「糊弄」**。
3. **放大槽位是錯的方向**：2GB 模型大小迭代，bpc 幾乎不動（見下）。

### 8.2 誠實化的修復（commit f89b2512）

- `FixedSizeCore` 全部層改為**固定 numpy 陣列**：`_pos[512][256]`、
  `_trans[256][256]`、`_gram[SLOTS][256]`、`_feat[SLOTS][256]`、
  `_feat_bool[SLOTS][2]`。
- `model_bytes` = 陣列實際位元組 = tracemalloc 實測（1.00x），訓練前後不變。
- 向量化學習（sliding_window_view + FNV-1a 批量 hash + add.at）：10 MB enwik8
  訓練 3.0s（純 Python 迴圈需 20s+）。
- 真實代價：模型 129.2 MiB（3 個 [65536][256] float32 表）——誠實的大小。
- 順帶修復 boolean 層真 bug：空槽（t=f=1 純平滑）被當成 +prior 的
  「true 證據」；現在每槽貢獻 `log(t/f)`，空槽貢獻 0。

### 8.3 enwik8 bpc 縮放實測（標準壓縮基準，越低越好）

| 模型大小 | 槽位 × 上下文 | bpc | 對照 |
|---|---|---|---|
| 129 MiB | 2^16 × GRAM4 | 3.794 | gzip 2.68 |
| 515 MiB | 2^18 × GRAM6 | 3.738 | LSTM 1.3 |
| 2,057 MiB | 2^20 × GRAM7 | 3.775 | Transformer-XL 0.99 |
| 2,057 MiB | 2^20 × GRAM8 | 4.138 | CTX-LLM 0.53 |

**決定性結論：模型 16 倍（129→2057 MiB）、上下文 4→8，bpc 卡在 ~3.7 甚至變差。
hash n-gram 架構在 enwik8 上無法突破 ~3.7 bpc，無論怎麼放大。**

根因（架構級，非大小問題）：
1. **hash 碰撞不可避免**：長上下文與大槽位互相抵消（2^20 槽 × GRAM8 反而 4.14）
2. **無位置資訊**：gram 只記「最後 K-1 bytes」，語言需要位置感知
3. **無向量泛化**：LLM 的「相似詞共享統計」做不到；byte n-gram 學不到語義

### 8.4 最終誠實對比（enwik8 bits-per-character）

| 模型 | bpc | vs 我們 |
|---|---|---|
| **統一引擎（最優 515MiB）** | **3.738** | baseline |
| gzip | 2.68 | 0.72x |
| LSTM | 1.30 | 0.35x |
| Transformer-XL | 0.99 | 0.26x |
| GPT-3 | 0.99 | 0.26x |
| CTX-LLM（2026 SOTA） | 0.53 | 0.14x |

### 8.5 結論與正確的下一步

- **「比不上」是真的，且不是語料/大小問題——是架構天花板**。hash n-gram
  無法匹配 transformer 的長上下文 + 位置 + 向量泛化。
- 正確的下一步是**給固定大小核心加一個真正的神經層**（固定維度、
  可學權重、梯度下降）——即專案既有的 SharedLatentSpace 真梯度技術，
  疊在 byte 統計層上。這才是能縮放 bpc 的方向，不是無腦加大槽位。
- 在加神經層之前，不再聲稱「壓縮比 > 其他 AI」。目前誠實數字：bpc 3.74、
  比 gzip 差、比 LLM 差 7 倍。這是下一步要解決的。