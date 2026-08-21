# 統一重構總綱（UNIFIED_REFACTOR_PLAN）

> 狀態：**設計定稿 · 未開工** — 只寫 MD，不改代碼
> 日期：2026-08-21
> 目標：把專案裡「什麼都有、多種版本」的狀態收斂為**一個整體且模組化**的實現；
> 保留所有設計與原理，但**每種原理只留一個正典實現**，其餘標為刪除/委派。
> 基準：`UNIFIED_AI_ENGINE.md §8` + `UNIFIED_AI_RESULTS.md` + `UNIFIED_AI_NEXT.md` 的誠實測量；
> `zzz` 三輪推演（哈希有損 → 遞迴複用 → ACT 熵停 → 三軸碼本）的結論。

---

## 0. 一句話原則

> **輸入是位元組流；模型是固定大小的張量；智能是張量上的對位與計算，再由認知×記憶驅動。**
> 重現是泛化的副產品（`§2.3`），索引不是模型（`§3 DELETE`）。

---

## 1. 你那條鏈，每個「×」是什麼

```
輸入 > UTF-8軸 > [內容軸 × 位置軸 × 位寬] > [對位器 × 計算單元] > [自主認知 × 記憶 × …]
  ──感知──    ──固定張量──          ──對位與計算──            ──主體──
```

### 1.1 `>` = 流水線階段（有向），`×` = 正交積（笛卡爾積，但實現必做因子分解）

- `>`：前一階段的輸出是後一階段的輸入，不可跳級。
- `×`：兩軸正交、可獨立取值，其組合形成一個格子。**若樸素做笛卡爾積，格子數 = 各軸大小之積，必爆炸**；實現必須用**哈希/低秩/稀疏**做有損壓縮（`zzz:4-10` 的固定容器思想）。

### 1.2 逐段定義

| 段 | 名稱 | 形式定義 | 取值範圍（重構後正典值） | 作用 |
|---|---|---|---|---|
| ① | **輸入** | `bytes` — 任何模態序列化後的位元組流 | `len ∈ [0,∞)` | 統一入口，不分文字/圖/音 |
| ② | **UTF-8軸** | `token = byte ∈ [0,255]`，`text.encode("utf-8") → np.uint8` | `VOCAB=256` 固定 | 唯一 tokenizer（`UNIFIED_AI_ENGINE.md §4.1` 的計劃與現實統一：沒有 `tokenizer.py`，就是 `np.frombuffer`） |
| ③ | **內容軸 × 位置軸 × 位寬** | 固定張量 `T[P][C][W]`，`P` 位置、`C` 內容碼本、`W` 位寬/通道 | `P=512, C=256→1024(碼本化後), W=8`（見下） | 感知的固定容器；`learn_bytes` 折進此張量，`gram_dist` 從此張量讀 |
| ④ | **對位器 × 計算單元** | 對位器：`T` 上的**連續/統計對位**（把 `C×P×W` 對到典範座標）；計算單元：**離散/短小**的確定性函式（`ast`/`真值表`/`符號推理`） | 對位器：熵/分佈峰值作 halting 訊號；計算單元：`≤10` 步，無狀態 | 對位器解決 `zzz:141-145` 的「全有或全無」跌落；計算單元是 `deterministic, not learned` 的短路徑 |
| ⑤ | **自主認知 × 記憶 × …** | 認知：`lifecycle/emotion/intent` 狀態機；記憶：`HAM + VectorStore` 誠實存儲；`…` = `response/meta/reasoning` 等 | 認知：狀態 `S`；記憶：`M`（可增長但**不叫模型**） | 主體層：`S×M` 決定路由與行為，與統計核解耦 |

#### 為什麼位寬是 `×` 而不是 `+`

- 若 `W` 是「語言/模態通道」，`C×P×W` 的樸素格子數 = `P·C·W`。
- 實測：`P=512, C=1024, W=8 → 4M格 ×4B=16MB` 可承受；`W=256 → 512M格=2GB` 不可承受。
- 結論：**`W` 必須小（4-16），且是 `C` 的位平面/通道因子，不是獨立大軸**。多語言/多模態不靠 `W` 線性擴，而靠 `C` 碼本的語意容量 + `T` 的哈希共享。

#### 為什麼對位器 × 計算單元是 `×` 而不是 `>`

- 對位器與計算單元**正交**：對位器管「像不像」（連續相似度），計算單元管「對不對」（離散真值）。
- 現狀 `unified_engine.py: _try_math → _try_logic → _infer_from_core` 已是此 `×` 的雛形：三條正交路徑，誰先命中誰短路。
- 重構後：對位器輸出 `分布/熵`，計算單元輸出 `符號解`，兩者在 `×` 上做**優先級路由**（`deterministic > statistical`），而非串聯。

#### 為什麼認知 × 記憶是 `×` 而不是 `+`

- 認知 `S` 條件化記憶檢索 `M`，記憶 `M` 條件化認知轉移 `S`，是**雙條件積**，不是相加。
- `UNIFIED_AI_NEXT.md §6` 的「快+好+強不可兼於單一固定模型」在此解：統計核管快+好，認知×記憶管強，兩層並行。

---

## 2. 現狀審計（要收斂什麼）

### 2.1 固定 vs 膨脹（實測）

| 模組 | 存儲模型 | 大小 | 判定 |
|---|---|---|---|
| `unified_engine/core_model.py` `FixedSizeCore` | **固定** `T[P][C][W]` + 3張 gram + feat/bool | **257 MiB** 恆等（`TestFixedMemory`） | ✅ 正典 |
| `multimodal/shared_latent_space.py` | 固定 `64d` | 數 MB | ✅ 正典（文字外唯一真泛化） |
| `memory/HAM + VectorStore` | 可增長但**誠實存儲**，不冒充模型 | 取決於資料 | ✅ 保留 |
| `three_axis` 6張表 | 膨脹 `O(L²)` 後綴 + LRU 補丁 | 949 MB checkpoint | ❌ 刪除 |
| `ed3n/DictionaryLayer` | 膨脹 `500k` cap + 外置 460k 字典 | 242 MB JSON | ❌ 收斂進 `FixedSizeCore` |
| `garden/VectorDictionary` | 膨脹 `10k + 5k recall + 500 templates` | `W[V,V] 4.33MB` 稀疏但 `V²` | ❌ 收斂進 `FixedSizeCore` |

### 2.2 多版本重複（每種原理只留一個）

| 原理 | 重複實現 | 正典 | 其餘處置 |
|---|---|---|---|
| 字典/嵌入 | `DictionaryLayer` / `VectorDictionary` / `FixedSizeCore._feat` / `three_axis anchors` | `FixedSizeCore` | 其餘委派或刪除（`§3.1-3.3`） |
| 問候/預設 | 4處 `ReflexLayer/_ReflexTable` 各自 `g1-p4` 30條 | `ai/data_eng/presets.py`（新建單一來源） | 刪除重複 builder |
| SNN | `ed3n/snn` + `garden/snn_core` 雙份 LIF | `ai/snn/`（新建統一） | 合併，`compute_bool` 單一門控 |
| 確定性路由 | `route_math/logic/knowledge/reasoning/chain` 三處拷貝 | `ai/arithmetic/deterministic_router.py` | 委派 |
| 錨定解碼 | `ed3n/output_anchor` + `garden/_anchored_decode` + `L0 []` | `ai/bridge/decoder.py` | 合併 |
| Checkpoint | `three_axis/2` / `unified/1` / `garden-1.0` | `unified/1` | 其餘標 deprecated |
| LLM Provider | `unified/ed3n/garden/ollama/...` 8 個 | `unified` + `ollama` + 雲端 | `ed3n/garden` provider 刪除（路由已指 `unified-1g` priority 1） |

---

## 3. 目標架構（一個整體，模組化）

```
                    ┌─────────────────────────────────────┐
     bytes ────────▶│  感知層 Perception                    │
                    │  UTF-8軸(256) → 內容碼本(C=1024)     │
                    │  × 位置軸(P=512) × 位寬(W=8)         │
                    │  T[P][C][W] 固定張量 + gram3/5/uni  │  257 MiB 固定
                    │  learn_bytes / gram_dist / bpc      │
                    └──────────────┬──────────────────────┘
                                   │ 分布/熵
                    ┌──────────────▼──────────────────────┐
                    │  對位與計算 Alignment × Compute      │
                    │  對位器: 熵 halting (ACT, zzz:43)   │  同一套表遞迴復用
                    │  計算單元: math/logic/symbolic 路由 │  短小離散 ≤10步
                    └──────────────┬──────────────────────┘
                                   │ 符號解 / 統計分布
                    ┌──────────────▼──────────────────────┐
                    │  主體層 Cognition × Memory           │
                    │  認知: lifecycle/emotion/intent     │  狀態機
                    │  記憶: HAM + VectorStore            │  誠實存儲
                    │  響應: response/meta/reasoning      │
                    └─────────────────────────────────────┘
```

**不變式**：
- `T` 大小編譯期常數，`model_bytes` 恆等（`tracemalloc 1.00x`）。
- 對位器與計算單元**復用同一套 `T`**，深度由熵動態決定，不預設層數（`zzz:84-99` 的版本B）。
- 認知×記憶不污染 `T` 的統計，`T` 只輸出 `P(next byte)`，認知層做策略。

---

## 4. 重構操作（保留設計、消滅版本）

### 4.1 感知層：`ai/unified_engine` 為正典

- **保留**：`core_model.py` / `unified_engine.py` / `trainer.py`（唯一誠實評測）。
- **改**：`content` 軸碼本化 `256→1024`（`zzz:101-110` 的 4MB 方案），`W=8` 位平面；`tokenizer.py` 不新建——就是 `np.frombuffer`，文檔與實現統一。
- **刪**：`ai/three_axis/*` 全部 6張膨脹表（`§3.1` 已列），`ai/ed3n/dictionary_layer.grow` 的無界增長，`ai/garden/dictionary grow + learned_recall + templates`。

### 4.2 對位與計算：`ai/arithmetic` + `ai/bridge` 為正典

- **新建**：`ai/arithmetic/deterministic_router.py`（單一路由）、`ai/bridge/decoder.py`（單一錨定解碼）、`ai/snn/`（統一 LIF）、`ai/data_eng/presets.py`（單一問候預設）。
- **改**：`gram_dist` 的 `5→4→3→2→1` hard backoff 保留（`UNIFIED_AI_NEXT.md` 證最優），對位器在 `hard` 之外加**熵 halting 的遞迴復用**（同一張表再查一次，直到熵降或達 `max_iters`），不新增參數。
- **刪**：`ed3n/garden` 各自的 `route_*` 拷貝、`_ReflexTable`、`_TEMPLATES L0`。

### 4.3 主體層：`ai/lifecycle + ai/memory + ai/meta` 保留並解耦

- **保留**：`lifecycle` / `memory/HAM` / `multimodal/SharedLatentSpace`（已是固定 64d）。
- **改**：`memory` 明確標「存儲非模型」，不參與 `compression_ratio` 計算；`cognition × memory` 的 `×` 顯式化為 `S×M` 條件積（狀態條件檢索，檢索條件轉移）。

### 4.4 配置與路由

- **保留**：`configs/system/llm.default.yaml` 單一來源（`unified-1g priority 1`）。
- **合併**：`magic_numbers.py` + `compute.default.yaml` + `backbone.default.yaml` 的三處分散 → 單一 `compute.default.yaml` 門控。

---

## 5. 驗收（沿用既有，不新增花樣）

- `TestFixedMemory`：`model_bytes` 恆等 + `shape == (P,C,W)` 固定。
- `TestCompression`：`ratios[500]<ratios[2000]<ratios[8000]` 線性成長（`T` 固定故必成立）。
- `TestGeneralisation`：留出集 `math>0.7` / `logic>0.5` / `bpc 2.33` / 影像/音訊 `>3x`。
- `TestGeneration`：`bigram overlap>0.3` 且 `最長逐字匹配 ≤13 bytes`（非過擬合，`UNIFIED_AI_NEXT.md §2.3`）。
- 全量 `tests/ai/unified_engine/` 34 項通過（`328s` 基準）。

---

## 6. 風險與不做什麼

- **不做**：把 `ed3n/garden/three_axis` 的膨脹表「遷移」進新核心——直接刪，不遷移。
- **不做**：為 `W` 引入大詞表/BPE——`W` 保持 4-16，語意容量由 `C` 碼本承擔。
- **不做**：在固定核內堆神經層——`UNIFIED_AI_NEXT.md` 已證 `proto_ffn 4.70` 慘敗，神經層屬 `SharedLatentSpace` 正交模組。
- **風險**：熵 halting 的 `ponder cost` 需調（`zzz:54`），否則「永遠多算一輪」；`C=1024` 的碼本需訓練/量化，否則退化為固定映射。

---

## 7. 文件處置

- 本 MD 為重構**唯一總綱**；`THREE_AXIS_SYSTEM.md` / `THREE_AXIS_SCALEUP.md` 已標「被取代」不再更新。
- `UNIFIED_AI_ENGINE.md` / `UNIFIED_AI_RESULTS.md` / `UNIFIED_AI_NEXT.md` 保留為誠實測量底座，本 MD 不重複數據，只定義結構與操作。
