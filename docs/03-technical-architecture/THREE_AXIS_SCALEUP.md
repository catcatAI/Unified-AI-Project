# 三軸系統擴展藍圖 (Three-Axis Scale-Up) — 大語言 × 多模態 × 數理化學

> 本文件回答用戶 2026-08-18 的指令：**把大語言、多模態、數理化學都加上，
> 能對位就能對齊多模態、段落；能滑動就能讓上下文上限接近硬碟容量、調記憶**。
> 內容是**設計**層級 — 指明「該如何正確地實作出來」，每一步都標出既有事實
> （`file:line`）與誠實限制。基礎引擎見
> `THREE_AXIS_SYSTEM.md`（三軸定義、錨點對位、實作狀態）。

---

## 0. 核心命題 (Core Thesis)

已實作的三軸引擎有兩個已驗證的自由度（`THREE_AXIS_SYSTEM.md §8.2/§8.5`）：

```
對位 (alignment)  = AnchorLearner 以 EM 從語料學出「終端分隔」錨點
                   → 語料事實: {=, -, .} (2 輪收斂, = 分數 0.856)
滑動 (sliding)    = 位置軸從「字串開頭絕對座標」變成「相對錨點」
                   → 178+101=? / what is 178 + 101=? / 178  +  101=? → 279
```

**擴展命題**：這兩個自由度不是算術域的獨門技巧，而是**通式** —

| 自由度 | 算術域的實例 | 擴展域的實例 |
|---|---|---|
| **對位** | `=` 分隔 問題\|答案 | 段落標題/換行分隔 內容\|回應；模態邊界分隔 視覺\|聽覺\|文字；欄位分隔符分隔 數理變數 |
| **滑動** | 空白/前置詞/長度偏移 → 同鍵 | 上下文窗在長語料上滑動；模態流互相對齊；公式與求解器對位 |

**正確的實作方式 = 不新增手寫規則，重複使用已驗證的 EM 錨點學習機制**：

1. **對位 → 對齊**：換「錨點語料」就重新學出對應域的錨點集。段落對齊、
   跨模態對齊、數理公式對齊都是同一個 `AnchorLearner`，只是輸入語料不同。
2. **滑動 → 上下文上界 → 硬碟容量**：一旦位置是「相對錨點」，熱層索引不再
   需要把整個上下文塞進 RAM — 冷語料留在磁碟，熱窗在 RAM 滑動 → 上界從
   RAM（2 GiB 預設）放寬到磁碟預算（`disk.max_percent: 0.80`）。
3. **誠實邊界不變**：三軸是**語料召回**，不是泛化（§1.3）。數理化學的
   「計算」由既有確定性引擎做，三軸只做「結構召回 + 對位」—「矩陣學結構、
   函數算結果」的分工不變。

### 0.1 垂直短軸正式化（Short-Axis Formalization）

> 2026-08-18 用戶提出視角轉換：把三軸「互相平行」再填充「垂直短軸/變體軸」
> （確定性引擎、記憶等），再「折回垂直」。結論（見審議記錄）：垂直/平行是
> **溝通隱喻**，代碼裡沒有「旋轉軸」可實作；真正可落地的是**把引擎內部
> 已記錄但未進輸出坐標的來源/置信度，提升為正式正交短軸**。

**現況的半成品**（`three_axis_engine.py`）：`_last_confidence`（:133）與
`_last_route`（:134）引擎內部有記，但 `process` 返回純 `str`（:379, :398）—
**來源與置信度是「斜軸」：引擎記得，下游拿不到**。

**正式化後的輸出坐標**（`str` → 坐標元組）：

| 短軸（垂直） | 值域 | 誰填充 | 落點 |
|---|---|---|---|
| **域軸** | math/logic/chem/physics/knowledge | 確定性引擎委派（`_try_math` 等） | `_last_route` → 正式字段 |
| **置信度軸** | 0..1 | 解析優先序給分（anchor 0.95 / position 0.60 …） | `_last_confidence` → 正式字段 |
| **時間/會話軸** | session id / 序號 | 記憶層（HAM 跨會話） | chat_routes 現有 session，補進引擎 |

**關鍵原則：確定性引擎是「域軸上的值」，不是獨立軸** — 三軸核心優勢是
封閉基數（256/位置/確定性），若每個引擎開一個垂直維度，坐標空間膨脹成
任意特徵空間，失去三軸存在的理由。正解：域軸是枚舉維度，引擎是該維度上的
**處理函數** — 三軸召回命中則三軸填值，miss 則在域軸上委派 `math_verifier`
計算（與 §4「矩陣學結構、函數算結果」一致）。

---

## 1. 現況基石（回顧）

### 1.1 引擎資料結構（`three_axis_engine.py`）

| 結構 | 位置 | 規模 | 內容 |
|---|---|---|---|
| `_position_content` | :113 | 位置 × 256 稀疏 | 該位置出現過的 UTF-8 值統計 |
| `_transitions` | :115 | ≤ 65,536 | (左值,右值) bigram |
| `_prefix_recall` | :119 | ≤ 2×65,536 | 有界左文脈（≤6 字符）→ 下一值 |
| `_exact_completions` | :123 | ≤ 1,000,000 | **完整前綴** → 下一值 |
| `_anchor_problems` | :127 | 語料問題數 | 錨點切分後的正規化問題 → 答案 |
| `_anchor_suffixes` | :130 | 語料後綴數 | 問題後綴 → 答案（滑動查找） |

解析優先序（`process` :358-398）：`anchor-aligned`(0.95) →
`exact-completion`(0.95) → `prefix-recall` → `position-exact` →
`position-majority`(0.60) → `bigram-transition`(0.55) → `global`(0.50)。

### 1.2 錨點學習（`anchor_learner.py`）

- EM 循環 :68-97：E-step `terminal_split`（最右側、右區無錨點的分隔）→
  M-step 評分 `0.8×terminality + 0.2×coverage` → top-K(=6) → 迭代 ≤8 輪。
- 錨點集是**資料驅動**的，非手寫（:20-22）；`align` :99-108 切
  `problem | delimiter | answer`；`normalize` :110-113 空白摺疊。
- 實證：算術語料收斂 `{=, -, .}`，`=` 分數 0.856。

### 1.3 誠實邊界（不變）

- **召回非計算**（`three_axis_engine.py:33-37`）：未見問題退統計回退。
- **形式自由度 ≠ 語義泛化**（`THREE_AXIS_SYSTEM.md §8.5`）：
  `calculate 178 plus 101=?` 的 `plus` 不在錨點學習範圍。
- 本擴展藍圖**不改此邊界** — 它擴張「召回能覆蓋的範圍」，不宣稱引擎會算。

---

## 2. 大語言擴展（Large Language）

### 2.1 現況：上下文上界 = RAM

| 層 | 現況 | 位置 |
|---|---|---|
| 對話 session | 綁定最後 80 條訊息 = 40 輪 | `chat_routes.py:1463-1465` |
| prompt | 取最後 10 條 | `prompt_builder.py:539` |
| 每條截斷 | 150-500 字符 | `prompt_builder.py:549,593-596` |
| 記憶體 cap | `memory.default_mb: 2048`（dynamic 8192） | `capacity.default.yaml:41-43` |
| 磁碟 cap | `disk.max_percent: 0.80`（=「真正的硬上限」） | `capacity.default.yaml:49-50` |

**瓶頸**：`MAX_SEQ_LEN`（三軸預設 512 字符，`three_axis_engine.py:87`）
是「單樣本學習長度」，但真正的對話上下文上界是 **RAM** — 因為熱索引
（`_exact_completions`/`_anchor_problems`/`_anchor_suffixes`）全在記憶體。

### 2.2 擴展設計：滑動上下文窗（sliding context window）

**關鍵洞察**：錨點對位已證明「位置是相對錨點的」。因此對話上下文可以
用**錨點切段落**，而不是「整段 session 塞進一個記憶體結構」：

```
熱層 (RAM)    : 當前段落窗（anchor-problem 表 + exact-completions 子集）
溫層 (磁碟)   : 全語料 suffix 索引（SQLite 或 binary_store, 見 §6.3）
冷層 (磁碟)   : 原始語料文件
```

滑動機制：

1. 對話歷史用**段落錨點**切分（新錨點集由語料學出，見 §2.3）。
2. 當前問題先查熱層 `_anchor_problems`；miss 則查溫層 suffix 索引
   （唯一答案才接受，`three_axis_engine.py:346-352` 的歧義拒絕策略保留）。
3. 命中後把該段落**升溫**回熱層（最近使用，LRU 式，與 `_enforce_memory_cap`
   :170-186 一致 — 超 cap 逐出最舊）。

**效果**：單一對話可跨越**整個磁碟語料**（wiki_zh 927MB、alpaca、算術/邏輯
集等），上下文上界從 RAM（2 GiB）變成磁碟預算（`disk.max_percent: 0.80`）。

### 2.3 段落對位（paragraph alignment）

AnchorLearner 的輸入換成「含段落標記的語料」，EM 會自動學出**段落錨點**
（換行、標題符、列表符等）取代算術的 `=`。正確做法：

- **輸入語料格式**：把 `wiki_zh`/`alpaca` 樣本序列化成
  `<段落內容>\n<回應>`（與現有 `<問題>=<答案>` 序列化同構，
  `THREE_AXIS_SYSTEM.md §8.2`）。
- **驗證標準**：錨點集是否收斂、`terminality` 最高的分隔符是否為換行/句點；
  比照算術域 `=` 0.856 的碾壓程度。
- **誠實預期**：自然語言錨點會比算術**更多元**（句點、問號、換行都可能是
  終端分隔），歧義後綴拒絕策略（`three_axis_engine.py:346-352`）會更常觸發
  → 正確率比算術域低，這是**語料性質**不是實作缺陷。

### 2.4 與 LLM 的分工

| 任務 | 誰做 | 原因 |
|---|---|---|
| 語料內已見的「問→答」 | 三軸（anchor-aligned, conf 0.95） | 零成本、確定性、可重現 |
| 未見的組合/語義推理 | LLM fallback（既有三層鏈） | 三軸誠實「不知道」就退 |
| 長文跨段召回 | 三軸滑動窗 | 上界接近硬碟，不截斷 |

---

## 3. 多模態擴展（Multimodal）

### 3.1 現況盤點（`ai/multimodal/`，26 個 py）

| 元件 | 角色 |
|---|---|
| `SharedLatentSpace` | LATENT_DIM=64 共享潛空間：`register_modality` / `project` / `similarity` / `cross_modal_attention` / contrastive train |
| `visual_encoder.py` / `audio_encoder_spectral.py` | 視覺/聽覺特徵編碼 |
| `three_layer_visual.py` / `semantic_visual.py` | 視覺語義 |
| `dual_encoder_router.py` | 雙編碼器路由 |
| `multimodal_memory.py` / `multimodal_retriever.py` | 模態記憶/檢索 |
| `primitives/` | 組合式影像生成 |

### 3.2 統一編碼：一切皆位元組

**命題**：三軸的 UTF-8 軸對所有模態都成立 — 只要模態先被**編碼為位元組流**
（既有編碼器已做這一步）。跨模態對位因此是**同一個 AnchorLearner 在不同
位元組流上的應用**：

| 模態 | 位元組流來源 | 錨點（EM 學出） |
|---|---|---|
| 文字 | UTF-8 直用 | `=` / 換行 / 句點 |
| 視覺 | `visual_encoder` 特徵 → 位元組 | 幀邊界、場景分隔 |
| 聽覺 | `audio_encoder_spectral` 特徵 → 位元組 | 時間戳、語音段界 |
| 語義 | `semantic_visual` / 潛空間向量 → 位元組 | 語義概念邊界 |

### 3.3 跨模態對位（cross-modal alignment）

**命題**：多模態對齊 = 在「同一事件的多模態位元組流」上學習**共同錨點**。
例如影像+字幕：`<幀位元組流> | <時間戳> | <文字> | <時間戳> | <幀...>` —
`|` 分隔符由 EM 學出後，任一模態的查詢（「這個畫面在講什麼」）對位到
文字段；反之亦然。

正確做法（承接現有架構，不另起爐灶）：

1. 用 `multimodal_memory.py`/`multimodal_retriever.py` 已建好的模態配對樣本，
   序列化成多模態位元組流，餵 `AnchorLearner`。
2. 學出的錨點集即為「模態切換符」；`SharedLatentSpace.cross_modal_attention`
   提供語義相似度，三軸提供**位置/結構對位** — 兩者正交互補。
3. 查詢解析：三軸先對位（找到對應模態段），再交由 `SharedLatentSpace`
   `similarity` 做語義確認 → 既拿到確定性的位置對位，又保留語義彈性。

### 3.4 誠實限制

- **三軸不學語義**：位元組流上的錨點只能對齊「結構位置」，不能保證
  「這個畫面 = 這句話」的語義。語義判定仍是 `SharedLatentSpace` 的職責。
- **原始像素不適合直接入三軸**：64-dim 潛向量已濃縮語義，直接餵原始
  位元組會把錨點學習淹沒在雜訊 — 用編碼器輸出，不用 raw data。

---

## 4. 數理化學擴展（Math / Physics / Chemistry）

### 4.1 現況盤點（誠實）

| 域 | 現況 | 位置 |
|---|---|---|
| 算術 | **唯一真相源** `evaluate_math`/`compute_arithmetic`（AST 安全求值、DoS 守衛、三角/log、中文數字、數論） | `services/math_verifier.py:482-549,215-223` |
| 布林 | `evaluate_logic`（無 XNOR — 由學習器補） | `services/math_verifier.py:403-479` |
| 數論 | 質數/GCD/LCM | `services/math_verifier.py:514-528` |
| 符號推理 | 雞兔同籠、傳遞關係、日曆、質量陷阱 | `ai/symbolic_reasoner.py:600-629,495-597` |
| 比較鏈 | 傳遞閉包求解 | `ai/reasoning/relational_chain.py:130-207` |
| 知識查表 | 顏色/動物腿數/單位換算 | `ai/knowledge_base.py:247-358` |
| 化學 | **查表** `_CHEMICAL_FORMULAS`（`knowledge_base.py:150-173,351-356`）+ **真實計量引擎** `ChemistryDomainEngine`（分子量 + 理想氣體，`_parse_formula` :565、`_molar_mass` :573） | `ai/memory/domain_ripple.py:558` |
| 物理 | **數量分類引擎** `PhysicsDomainEngine`（關鍵字+數字偵測，`compute` 委派 `math_verifier.compute_arithmetic`） | `ai/memory/domain_ripple.py:459,478` |
| 域路由 | `DOMAIN_REGISTRY` + `route_domain(text)` — 已存在的「域軸處理函數」選擇器 | `ai/memory/domain_ripple.py:609,638` |
| 學習器 | 位元級 MLP cell（carry/borrow/mul），僅在確定性引擎雙雙 None 時 fallback | `ai/arithmetic/arithmetic_learner.py`, `ai/arithmetic/gate_router.py:4-23,53-85` |

**關鍵事實**：`math_verifier.py:215-223` 註明它是**唯一算術引擎** —
ED3N/GARDEN 的 `route_math`（`dictionary_layer.py:452-472`,
`dictionary.py:1069-1085`）都委派給它。這是擴展數理化學的**正確模式**。

### 4.2 正確的分工：三軸召回 × 確定性計算

沿用「矩陣學結構、函數算結果」（`THREE_AXIS_SYSTEM.md §4.1 結論`）：

| 層 | 角色 | 正確率/信心 |
|---|---|---|
| 三軸 anchor-aligned | 語料內已見的「問題→答案」召回（含滑動變異） | conf 0.95 |
| 確定性引擎 | 未見問題的**計算**（`math_verifier` 等） | 100% 當域 |
| 學習器 | 確定性引擎的**空窗**（如 XNOR、位元形式） | 訓練收斂後 |

> ⚠️ **三軸永不計算**：`evaluate_math` 不會被三軸取代。三軸的答案是
> 「查回」的，不是「算」的；未見組合的真相只能來自 `math_verifier`。

### 4.3 物理/化學的正確接入（greenfield，遵循現有模式）

物理/化學已有**最小 Q&A 引擎**（`domain_ripple.py`：分子量/理想氣體/數量分類，
見 §4.1 修正）— 接入 = 擴充既有引擎 + route 鉤子，三軸只做語料對位。遵循
`math_verifier` 的「單一真相源」模式：

1. **新增 `physics_formulas.py` / `chem_verifier.py`**（或擴充
   `math_verifier` 的 SAFE_OPS/_SAFE_FUNCTIONS，`math_verifier.py:33-43,
   254-276`）：
   - 物理：F=ma、`E=½mv²`、`v=at`、重力、功/功率 — 全走
     `_safe_eval` 的 AST 白名單 + DoS 守衛（`:48-50` MAX_POW_EXPONENT 等）。
   - 化學：`_CHEMICAL_FORMULAS` 查表擴充為**計量驗證器**（分子量、摩爾數、
     平衡係數），保持「驗證結果」而非「生成結果」。
2. **新增 route 鉤子**：比照 `_try_math`（`garden_engine.py:309-317`）加
   `_try_physics` / `_try_chem`，並在 `garden_engine._process` 的 Stage 1
   （`:1092-1102`）與 ED3N 同序加入。
3. **三軸只存語料對位**：把「問題→答案」樣本（含未知變數）餵
   `AnchorLearner`，學出**公式分隔錨點**（`=`、未知數符號、單位符號），
   讓 `已知量 = ?` 的變異形式對位到同一條公式 → 再交給確定性引擎算。

### 4.4 誠實限制

- **物理/化學 Q&A 是部分既有**：`domain_ripple.py` 已有分子量/理想氣體/數量分類
  （`PhysicsDomainEngine` :459、`ChemistryDomainEngine` :558），但**公式求解器**
  （F=ma、動能、單位換算進階）仍缺。任何「引擎已能算公式」的宣稱都需先有
  `math_verifier` 同級測試（`level5_asi_system.py` 也無此能力 — 純對齊協調器）。
- **單位系統是硬骨頭**：`knowledge_base._UNIT_CONVERSIONS`（`:106-147`）只做
  長度/重量/體積/時間；溫度、複合單位需先補齊才能正確驗證。
- **三軸的錨點不含單位推理**：`1kg 羽毛 vs 1kg 鋼鐵` 的質量陷阱是
  `symbolic_reasoner._solve_mass_trick`（`:409-435`）的職責，三軸不該搶。

---

## 5. 記憶體調度與滑動索引（Memory Tiering & Disk-Backed Index）

### 5.1 現有容量模型

| 機制 | 現況 | 位置 |
|---|---|---|
| 容量級聯 | 每項 `[max_bytes, max_percent]`；`effective_capacity_bytes` = `min(numeric, total×percent)` | `magic_numbers.py:264-313` |
| 記憶體預設 | `memory.default_mb: 2048`（dynamic 8192, max_percent 0.80） | `capacity.default.yaml:41-43` |
| 磁碟硬上限 | `disk.max_percent: 0.80`（critical 0.90） | `capacity.default.yaml:49-50` |
| 精確度策略 | `precision`（LRU 逐出）vs `truncate`（硬切，僅 dataset） | `capacity.default.yaml:6-9` |
| 硬體設定檔 | 5 層自動偵測 + `ANGELA_HARDWARE_PROFILE` 覆寫 | `magic_numbers.py:338-422` |
| HAM 持久化 | JSON 檔案、磁碟滿時**跳過儲存**（不截斷） | `ai/memory/ham_memory/ham_core_storage.py:74-121` |
| 向量記憶體 | numpy+JSON 或 chromadb 雙後端，`VECTOR_STORE_PATH` | `ai/memory/vector_store.py:5,26` |

### 5.2 熱/溫/冷三層設計

| 層 | 載體 | 內容 | 觸發 |
|---|---|---|---|
| 熱 | RAM（`_anchor_problems`/`_exact_completions`） | 當前對話窗、高頻錨點問題 | 每次查詢 |
| 溫 | 磁碟索引（§5.3） | 全語料 suffix/前綴表 | 熱層 miss |
| 冷 | 磁碟原始檔 | 完整語料 | 溫層建索引時 |

**調度規則**：命中升溫（LRU），`_enforce_memory_cap`（`three_axis_engine.py:
170-186`）逐出最舊；溫層 miss 才讀冷層。與 HAM「磁碟滿跳過儲存」策略一致 —
**永不截斷、永不 OOM**，只降溫。

### 5.3 溫層實作選擇（正確做法）

現有可用的磁碟持久化技術：

| 選項 | 既有範例 | 適用 |
|---|---|---|
| **SQLite** | `ai/meta/learning_log_db.py`（唯一 sqlite 使用處） | suffix 索引、`VARCHAR` 鍵 + `INTEGER` 值 |
| **binary_store** | `ai/garden/binary_store.py` | 稠密表（前綴/後綴）最快 |
| **numpy+JSON** | `ai/memory/vector_store.py:158-179` | 向量/統計表 |

**建議**：suffix 索引走 SQLite（B-tree 原生支援前綴/後綴查詢、磁碟預算由
`effective_capacity_bytes("disk", ...)` 控制），稠密統計走 binary_store。
`AnchorLearner.normalize` 的空白摺疊鍵直接當 SQLite 主鍵 — 與 RAM 版
`_anchor_problems` 完全同構，熱層只是溫層的 LRU 快取。

### 5.4 記憶體計算範例（上界 = 硬碟）

以 wiki_zh（927MB）+ alpaca + 算術/邏輯集 ≈ 1GB 語料為例：

| 層 | 規模估算 | 落在 |
|---|---|---|
| 熱（RAM 快取） | 維持 `memory.default_mb: 2048` 內 | RAM |
| 溫（SQLite 索引） | 語料 × ~2-3（鍵+值+後綴）≈ 2-3GB | 磁碟（0.80×可用） |
| 冷（原始檔） | ~1GB | 磁碟 |

上下文上界 = **溫+冷層**，即**磁碟容量**；RAM 只是可調的快取層
（`dynamic_mb: 8192` 上限，`compute_int` 依硬體設定檔調整）。

---

## 6. 實作路線圖（Roadmap）

| 階段 | 內容 | 驗證標準 | 涉及 |
|---|---|---|---|
| **A. 段落錨點** | AnchorLearner 餵 wiki/alpaca 序列化樣本，學自然語言錨點 | 錨點收斂、換行/句點 terminality 碾壓；測試 `test_paragraph_alignment` | `anchor_learner.py`, `tests/` |
| **B. 磁碟溫層** | SQLite suffix 索引取代 RAM `_anchor_suffixes`；熱層改為 LRU 快取 | 2GB 語料載入 < RAM cap；查詢命中率 > 90% | `three_axis_engine.py`, 新 `disk_index.py` |
| **C. 模態對位** | `multimodal_memory` 樣本序列化 → 跨模態錨點；三軸對位 + `SharedLatentSpace` 語義確認 | 圖↔文、音↔文對位 probe | `AnchorLearner` 重用, `multimodal/` |
| **D. 物理/化學** | 擴充 `domain_ripple.py` 既有引擎（`PhysicsDomainEngine`/`ChemistryDomainEngine`）→ `route_domain` 進 GARDEN Stage 1（`garden_engine.py:1092`）；公式求解器（F=ma、動能）已實作於 `ai/memory/formula_solver.py`；`knowledge_base` 單位擴充仍缺 | F=ma、分子量 probe；`math_verifier` 同級測試 | `domain_ripple.py`, `garden_engine.py:1092-1102` |
| **E. 上界測試** | 滑動窗跨全語料召回 | 上下文上界 ≈ 磁碟預算；記憶體穩定 | §5 全 |

---

## 7. 風險與誠實評估

1. **三軸仍不泛化**（§1.3）：擴展只加大召回覆蓋，未見組合仍退統計回退 —
   別因「上下文變大」就宣稱變聰明。
2. **錨點多義**：自然語言/多模態的錨點集比算術多元，`_lookup_anchor` 的
   歧義拒絕（`three_axis_engine.py:346-352`）會更常拒絕 → 正確率較低、
   但**不會瞎答**（這是優點）。
3. **磁碟 I/O 延遲**：溫層 miss 讀冷層會慢 — 需要 LRU 命中率監控
   （比照 `performance_optimizer.py` 的 real hit/miss 追蹤）。
4. **物理/化學公式求解器（已實作 2026-08-19）**：`ai/memory/formula_solver.py`
   求解單未知物理文字題 — F=ma、動能 `½mv²`、`v=at`、動量、功、功率、重量
   `F=mg`，已接入 `PhysicsDomainEngine.compute`（domain_ripple.py）。20 測試。
   複合單位換算仍缺；任何「已能做物理公式」的宣稱必須有 `math_verifier`
   同級測試（`tests/ai/test_formula_solver.py` 為此存在）。
5. **模態位元組流需編碼器**：原始像素/波形不直接入三軸（§3.4）。

---

## 8. 與現有文件的一致性

- 本藍圖擴充 `THREE_AXIS_SYSTEM.md` §8（已實作引擎）— 不推翻任何已驗證事實。
- 分工遵循 `DETERMINISM_CLASSIFICATION.md`（確定性/半定性/非定性）與
  `FRAMEWORK_OVERVIEW.md`（LLM→ED3N→GARDEN 三層 fallback）：三軸屬半定性層
  的確定性對位，計算仍在確定性層，泛化/語義仍在 LLM 層。
- 磁碟/記憶體預算全走 `magic_numbers.py` 容量級聯與 `capacity.default.yaml` —
  不新增平行容量系統。

### 8.1 專案內既有「該加進來」的元件（Integration Audit）

> 2026-08-18 全專案審計（對照本藍圖 §2-§6 各階段）— 找到**現成可重用的既有
> 元件**，比藍圖「自己造」更省事，並修正一處事實錯誤（§4.1 物理/化學）。

| 藍圖階段 | 既有元件（可直接用） | 位置 | 比藍圖原案省什麼 |
|---|---|---|---|
| A. 段落錨點 | `DocumentChunker.chunk()`（Section/Paragraph/Sentence 邊界） | `ai/document/chunker.py:55-66` | 不用自建段落切分，序列化即餵 AnchorLearner |
| B. 磁碟溫層 | `context/storage/` 三後端（`MemoryStorage` LRU :30-60 / `DiskStorage` JSON :15-42）+ `VECTOR_STORE_PATH` 雙後端 | `ai/context/storage/`, `ai/memory/vector_store.py:26` | RAM↔磁碟分層抽象已存在，SQLite 只補 suffix 索引 |
| C. 模態對位 | `SharedLatentSpace` + `cross_modal_router` + `multimodal_memory/retriever` | `ai/multimodal/` | 模態配對樣本已內建，序列化即餵錨點學習 |
| D. 物理/化學 | `PhysicsDomainEngine` :459 / `ChemistryDomainEngine` :558 / `route_domain` :638 | `ai/memory/domain_ripple.py` | 引擎+路由已存在，只補公式求解器 |
| 短軸(域軸) | `DOMAIN_REGISTRY`（math/chemistry/physics）| `ai/memory/domain_ripple.py:609` | §0.1 域軸的現成值域 |
| 熱/冷分層 | `memory_integration_loop._promote_memories`（short→long-term 升溫） | `ai/lifecycle/memory_integration_loop.py:424-447` | §5.2「命中升溫」已實作 |
| 一致性 | `ham_core_storage` 磁碟滿**跳過儲存不截斷**（與 §5.2 同策略） | `ai/memory/ham_memory/ham_core_storage.py:74-121` | 冷層策略複用 |
| 對齊鉤子 | `core/hsp/bridge/data_aligner.py`（stub） | `connector.py:221-225` | 「align」名稱衝突處可掛真實錨點對位 |

**審計結論**：藍圖各階段幾乎都有既有對應 — 實作優先序 = **先用現成的
（`domain_ripple`、`document/chunker`、`context/storage`），再補缺口**
（SQLite suffix 索引、公式求解器、段落錨點驗證）。公式求解器缺口已閉合
（`formula_solver.py`，2026-08-19）；剩餘缺口 = SQLite suffix 索引
（Phase B）與段落錨點驗證（Phase A）。這符合 ASI 工程標準
「surgical / 不重造輪子」。

---

*版本: 擴展設計藍圖（§0.1 短軸 + §8.1 審計為實作層級，其餘階段仍為設計層級）·
基於 2026-08-18 `ThreeAxisEngine` 與 `AnchorLearner` 實作 + 同日多模態/數理
化學/記憶體子系統研究報告 · 2026-08-19 訓練流程實作：`prepare_three_axis_datasets.py`
（自動下載/自動決策）+ `train_three_axis.py --prepare`（一鍵訓練），指令見
`THREE_AXIS_SYSTEM.md §8.6`*