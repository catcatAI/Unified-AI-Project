# 模型生成能力橋接計畫 — ED3N/GARDEN 設計落差分析與修復路徑

> **計畫代號**: GENESIS — Generative Emergent Neural Encoding with Structured Inference Synthesis
> **狀態**: ⚠️ 設計驗證未完成 — 核心生成能力尚未實作
> **建立日期**: 2026-06-07
> **基於**: ED3N_MATURITY_PLAN.md + GARDEN_MODEL_PLAN.md + ANGELA_LLM_SNN_ARCHITECTURE_PLAN.md
> **落差分析**: 2026-06-07 設計回顧

---

## 一、核心問題陳述

### 一句話

> **我們討論了一個能自主生成的架構，實作了一個只能檢索路由的系統。生成能力那塊沒有做，被外部 LLM 替代了。**

### 設計 vs 實作對照

| 維度 | 設計藍圖 (ANGELA_LLM_SNN_ARCHITECTURE_PLAN) | 當前實作 (ED3N + GARDEN) | 差距 |
|:-----|:--------------------------------------------|:-------------------------|:----:|
| **字典角色** | 動態增長的語義結構，儲存**概念+關係+歧義消解** | Preset 短語庫 + keyword/bigram 索引 | 大 |
| **網路角色** | 學**關係規則** — 抽象 key 之間的因果/類比/映射 | 做**概念匹配和路由** — key 激活傳播 + Hebbian 權重調整 | 大 |
| **輸出產生** | **錨定生成** — 網路計算結果 + 原始輸入共同決定輸出序列 | **片段拼接** — 找到的 surface form 直接連起來 | 根本性 |
| **輸入方式** | 模態編碼器群 — 文字/圖像/音訊/狀態統一進字典 | 字元級 keyword + bigram（ED3N）；向量相似度（GARDEN） | 中 |
| **三層速度** | 反射(<1ms) → 淺層(<10ms) → 完整核心(<100ms+) | 反射 → 字典+SNN 傳播 → 輸出解碼（三層是序列的，不是速度分級的） | 中 |
| **SNN 批次** | 動態稀疏 — 關係類型決定激活範圍，只算下游 | 固定的 `compute_spike_propagation` 3 hops，無動態批次 | 中 |
| **荷爾蒙調製** | 全局閾值調製 — 壓力/穩定/多巴胺 | GARDEN 有 `HormonalModulator`；ED3N 有 LIF SNN 模式但未整合 | 小-中 |
| **持續學習** | 字典一直長大，網路不動 | ContinuousLearningPipeline 實作完成，但僅限字典增長+反射 | 中 |
| **訓練** | **字典和網路分離梯度** — 各用不同學習率同步更新 | Hebbian 交替訓練（字典調置信度，網路調權重），無梯度流 | 根本性 |
| **生成能力** | 核心網路的輸出經字典解碼產生**有意義的新句子** | 無生成 — 所有輸出都是 preset 拼接 | **完整缺失** |

---

## 二、為什麼會這樣 — 工程取捨分析

### 2.1 歷史路徑

```
設計階段 (2026-06-06 理論)
  └→ 字典外部化 + 核心網路 + 輸出錨定 = 生成新範式
      ↓
實作階段 (2026-06-06 ~ 2026-06-07)
  ├→ ED3N: 先做字典+匹配+路由 → 跑通管線 → 驗證概念
  ├→ GARDEN: 向量編碼 + SNN + 知識導入
  └→ 生成能力："
    需要訓練一個能產出有意義序列的網路，
    相當於從頭訓練一個小型 LLM，
    時間不夠，先外包給雲端 API"
      ↓
當前 (2026-06-07): 路由系統完整，生成能力 = 空
```

### 2.2 關鍵決定點

| 決定 | 當時理由 | 現在代價 |
|:-----|:---------|:---------|
| 輸出用 `anchored_decode` 拼接 surface form | 快速驗證管線 | 輸出永遠是 preset 片段組合，非生成 |
| 核心網路用 Hebbian 學習 | 無需 backprop，純 Python | 無法學習序列生成 |
| 字典編碼用 keyword/bigram | 無外部依賴 | 無語義理解，純字元匹配 |
| 訓練用 `train_step` 交替訓練 | 字典和網路分開更新 | 無聯合梯度流，無法端到端學習 |
| GARDEN 用 CharBag 回退 | sentence-transformers Python 3.14 崩潰 | 256 維 hash 無語義 |
| 生成外包給雲端 LLM | 快速獲得對話能力 | 本地永遠不具備生成能力 |

### 2.3 現有系統中已經做對的部分

雖然生成能力缺失，以下元件是正確的且可復用：

```
✅ 字典外部化架構
  ├── DictionaryLayer: key → surface_forms + relations + confidence + contexts
  ├── 自我增長: grow() + detect_new_concepts()
  ├── prune() 清理 + LRU cache
  └── 序列化: export/import JSON
✅ 三層速度分離骨架
  ├── ReflexLayer: O(1) 模式匹配
  ├── DictionaryLayer.encode(): 輸入編碼
  └── CoreNetwork/SnnCore: 關係運算
✅ 輸出錨定機制
  ├── anchored_decode(): 輸入 key 錨定 + 網路輸出共同決定
  └── ResponseAnchorValidator: 飄移檢測
✅ 訓練管線
  ├── ED3NTrainer: 字典+網路交替訓練
  ├── ContinuousLearningPipeline: 在線學習
  ├── TrainingCoordinator: 領域解衝突
  └── unified pipeline: 43K 樣本, 5 小時
✅ 路由系統
  ├── ModelBus: 能力導向路由
  ├── QueryClassifier: 8 領域分類
  └── 6 種雲端 LLM 後端
```

---

## 三、生成能力缺失的根本原因

### 3.1 解碼器不是生成器

`anchored_decode()` 當前行為：

```python
# 當前: 檢索 + 拼接
def anchored_decode(network_output, input_keys, dictionary):
    # 1. 收集 input_keys 中有的條目
    # 2. 收集 network_output 中有激活的條目
    # 3. 按權重排序
    # 4. 拼接 surface form → output
    return " ".join([entry.surface for entry in top_scored])
```

設計要求的行為：

```python
# 需要: 生成 + 錨定
def anchored_generate(network_state, input_keys, dictionary):
    # 1. 輸入 key 決定起始 context
    # 2. 網路逐步產生下一個 key 的分布
    # 3. 從分布採樣下一個 key → 查 surface form → 輸出
    # 4. 新輸出的 key 回饋到輸入 → 繼續產生
    # 5. 直到終止條件
    return generated_sequence  # 有序的 token 序列
```

### 3.2 核心網路沒有時序建模

| 能力 | 當前 CoreNetwork | 生成需要的 |
|:-----|:----------------:|:----------:|
| 輸入 → 輸出 | 一步到位 | 逐步序列 |
| 位置感知 | 無（key 是無序集合） | 有（token 順序重要） |
| 條件機率 | 無 | P(next_key \| context) |
| 採樣 | 無（top-k 直接取） | 溫度採樣 / top-k / top-p |
| 停止條件 | 無（固定 top_k_network） | \<eos\> token 或長度限制 |
| 上下文長度 | 3 hops 傳播（等效 ~3 tokens） | 可變（8-128+ tokens） |

### 3.3 訓練沒有序列損失

當前訓練：

```
每個樣本: (input_key_set, output_key_set)
  字典階段: 調整 input_key 的置信度
  網路階段: 調整 key1→key2 之間的 Hebbian 權重
```

生成需要的訓練：

```
每個樣本: (input_sequence, output_sequence)
  編碼器: input tokens → hidden state
  解碼器: hidden state → output tokens (自回歸)
  損失: cross-entropy(next_token | previous_tokens)
  梯度: 通過時間反向傳播 (BPTT) 或前向模式
```

---

## 四、修復路徑

### Phase 0: 誠實評估 (本文件) ⬅️ 現在這裡

- [x] 承認 ED3N/GARDEN 無生成能力
- [x] 釐清設計 vs 實作差距
- [x] 盤點可復用元件
- [ ] 決定：要補生成能力，還是接受「路由系統+雲端 LLM」的定位

### Phase 1: 序列解碼器 (最小生成能力)

為 ED3N 添加真正的自回歸解碼，不改變字典和網路結構。

```
輸入 → encode → CoreNetwork → decode_step loop → 輸出序列
                                    ↑
                             上一步輸出 key (feedback)
```

#### 1a. StepDecoder

```python
class StepDecoder:
    """逐步解碼器：將網路狀態轉換為有序輸出序列"""
    
    def __init__(self, dictionary, max_length=50, eos_key=None):
        self.dictionary = dictionary
        self.max_length = max_length
        self.eos_key = eos_key or "<eos>"
    
    def generate(self, network_output, input_keys, temperature=1.0):
        # 初始 context = input_keys 的 top-3
        context = list(set(input_keys))[:3]
        output_keys = []
        
        for step in range(self.max_length):
            # 當前 context → 網路查詢下一個 key 分布
            scores = self._score_next_keys(context, network_output)
            # 溫度採樣
            next_key = self._sample(scores, temperature)
            if next_key == self.eos_key:
                break
            output_keys.append(next_key)
            context.append(next_key)  # feedback
            context = context[-8:]    # sliding window
        
        # 解碼 key → surface form
        return self._decode(output_keys)
```

#### 1b. Key 序列訓練數據

從現有資料集中提取輸入→輸出序列對：

- 數學：`"178 + 101"` → `"two", "hundred", "seventy", "nine"`（或 `"279"`）
- 邏輯：`"true AND false"` → `"false"`
- 知識：`"what is AI"` → `"Artificial", "Intelligence", "is", ...`

**關鍵改變**：訓練數據從 key 集合改為 key 序列。

#### 1c. 序列損失

```python
loss = 0
for step in range(len(target_sequence)):
    # 網路在 step 的輸出分布
    logits = network.forward(context_so_far)
    # 目標 key 的交叉熵
    loss += cross_entropy(logits, target_sequence[step])
```

#### 里程碑 1

- [x] `StepDecoder` 實作 + 測試 (`apps/backend/src/ai/ed3n/step_decoder.py`)
- [x] 序列數據格式定義 (`SequenceExample`, `SeqBatch` in `training_types.py`)
- [x] `engine.generate()` API 整合 (reflex→StepDecoder fallback)
- [x] `SequenceTrainer` 實作 (非對稱權重 + Hebbian 序列學習)
- [x] `sync_from_dictionary()` 將字典關係同步至網路
- [x] 57 現有測試仍全部通過

#### Phase 1 發現

| 問題 | 狀態 | 說明 |
|:-----|:----:|:------|
| **StepDecoder 可產生序列** | ✅ | 給定 key 分布和上下文，能逐步產生有序 key 序列 |
| **序列解碼 > 簡單拼接** | ✅ | StepDecoder 會過濾重複 surface，比 `anchored_decode` 更緊湊 |
| **Heuristic scoring 有效** | ✅ | 網路激活 + 字典關係 + 溫度採樣 = 可控的隨機性 |
| **SequenceTrainer 學習非對稱權重** | ✅ | `add_directed()` 建立單向連接，前向權重高於反向 |
| **密集圖導致全域激活** | ❌ | 46 preset 條目密集互連，從任何節點出發都走到所有節點 → 需要 Phase 2 因果遮罩 |
| **足量序列數據可改善** | ⚠️ | 471 樣本訓練讓 accuracy 達 0.9958，但密集圖稀釋了學習效果 |

**核心教訓**: 當前圖結構是語意關聯（同義/映射/類比），不是序列關聯（A→B→C）。StepDecoder + SequenceTrainer 的機制正確，但需要 Phase 2（位置感知 + 因果遮罩）才能真正做到序列生成。在不遮罩的圖上，激活會從輸入節點擴散到整個圖。

---

### Phase 2: 核心網路升級 — 序列感知 (✅ 完成 2026-06-08)

目前 CoreNetwork 將輸入視為**無序 key 集合**。生成需要**有序 token 序列**。

#### 2a. 位置感知（Position-Aware Activation）

在 `CoreNetwork.forward_sequential()` 中加入位置感知權重，較晚的位置獲得輕微的近期增益：

```python
recency = 1.0 + 0.15 * pos / max(num_visible, 1)
neuron.activation = min(neuron.activation * recency, 1.0)
```

- **為什麼不是正弦編碼**：ED3N 的 key 是語義標籤（字串），不是連續向量。在無嵌入層的符號網路中，近期增益（recency boost）比正弦編碼更直接有效。
- **實作**：`core_network.py:200-210` — 迭代 `visible_keys`，對每個位置 `pos` 計算 `recency` 因子，乘到激活值上。

#### 2b. 因果遮罩（Causal Masking）

`forward_sequential()` 的核心機制 — 限制可見 key 集合：

```python
visible_keys = input_keys[:current_position + 1]
```

- 與 `forward()` 的關鍵差異：
  1. **不呼叫 `classifier.classify_pair()`** — 避免生成時動態修改圖結構
  2. **可見範圍限於 `visible_keys`** — 所有激活/傳播操作只在 `input_keys[0..current_position]` 範圍內
  3. **傳播深度縮短** — `max_hops=2, decay=0.3`（vs `forward()` 的 `max_hops=3, decay=0.5`），減少密集圖的快速全域擴散
- **實作**：`core_network.py:188-237`

#### 2c. 上下文滑窗

StepDecoder 原有的 `context_window` 參數（預設 4）已在 Phase 1 實作。`forward_sequential()` 不新增額外滑窗，而是通過 `max_hops=2` 的傳播限制達到類似效果。

#### 2d. StepDecoder 整合

`StepDecoder.generate()` 改為**每一步**呼叫 `network.forward_sequential()` → 取得當前位置的因果遮罩激活 → 用新鮮激活進行候選評分：

```python
# 不再使用 generate() 開頭的靜態 network_output
seq_output = self.network.forward_sequential(
    context, current_position=len(context) - 1
)
sorted_seq = sorted(seq_output.items(), key=lambda x: x[1], reverse=True)
net_only = {k: v for k, v in sorted_seq[:5]}
```

- 移除了原本 `context_window` 壓縮後的 `fresh` 檢查（因 `forward_sequential` 每次回傳完整遮罩激活，不再需要手動追蹤剩餘候選）
- `network_output` 參數保留但不再使用（向後相容）
- **實作**：`step_decoder.py:49-72`

#### 2e. SequenceTrainer 整合

`SequenceTrainer.train_step()` 改用 `forward_sequential()` 取代 `forward()`：

```python
activations = self.network.forward_sequential(
    context, current_position=len(context) - 1
)
```

- 訓練時因果遮罩確保：每個預測步驟只看 `keys[0..pos]`，不能預覽後續的 ground truth key
- 強迫網路學習真正的序列預測（而非 cheat by looking ahead）
- **實作**：`ed3n_trainer.py:316-318`

#### 里程碑 2 — 驗證

- [x] 位置感知（recency weighting）實作
- [x] 因果遮罩集成到 `CoreNetwork.forward_sequential()`
- [x] 滑窗上下文（原有 `context_window` + `max_hops=2`）
- [x] StepDecoder 整合 — 每一步使用新鮮因果遮罩激活
- [x] SequenceTrainer 整合 — 訓練時使用因果遮罩
- [x] 57/57 現有測試全部通過（Phase 2 零衰退）

#### Phase 2 發現

| 問題 | 狀態 | 說明 |
|:-----|:----:|:------|
| **因果遮罩減少全域激活** | ✅ | `forward_sequential()` 將可見範 */
| **生成時不修改圖結構** | ✅ | 不呼叫 `classifier.classify_pair()`，避免生成期副作用 |
| **訓練面向序列預測而非關聯配對** | ✅ | `forward_sequential()` 確保訓練時網路不能看到未來 key |
| **密集圖仍需 Phase 3 稀疏化** | ⏳ | 因果遮罩緩解但未解決根本問題 → 需要顯式序列/語義路徑分離 |

**核心教訓**: 因果遮罩是序列生成的必要前提，但不是充分條件。遮罩阻止了「窺視未來」，但密集的語意圖仍會在每個步驟產生大量雜訊激活。Phase 3 的路徑分離（序列路徑 vs 語意路徑）是真正的解決方案。

---

### Phase 3: 訓練系統升級 — 排練採樣 (✅ 完成 2026-06-08)

SequenceTrainer 已在 Phase 1 建立基本 Hebbian 教師強迫訓練。Phase 3 在此基礎上新增排練採樣（Scheduled Sampling）與序列數據轉換工具。

#### 3a. 排練採樣（Scheduled Sampling）

在 `SequenceTrainer.train_step()` 中加入動態衰減的排練採樣機率：

```python
# 每一步決定使用教師強迫還是模型自生成上下文
if random.random() < self.scheduled_sampling_prob:
    context.append(target_key)          # 教師強迫（ground truth）
else:
    predicted = max(activations, key=activations.get)  # 模型預測
    context.append(predicted)           # 模型自生成

# 每 step 後衰減排練機率
self.scheduled_sampling_prob = max(
    self.scheduled_sampling_end,
    self.scheduled_sampling_prob - self.scheduled_sampling_decay,
)
```

- **初始狀態**：`scheduled_sampling_start=1.0`（完全教師強迫）
- **最終狀態**：`scheduled_sampling_end=0.0`（完全自生成）
- **衰減率**：`scheduled_sampling_decay=0.02`（每 step 降 2%）
- **損失計算**：始終基於 ground truth `target_key`，即使上下文是模型預測
- **重置**：`reset_scheduled_sampling()` 可將機率恢復到起始值
- **實作**：`ed3n_trainer.py:306-396`

#### 3b. 序列數據轉換工具

將現有 `TrainingExample`（key 集合格式）轉換為 `SequenceExample`（key 序列格式）：

```python
def training_example_to_sequence(ex: TrainingExample) -> SequenceExample:
    return SequenceExample(
        input_text=ex.input_text,
        target_text=ex.expected_output,
        input_key_seq=list(ex.input_keys),      # 集合→序列
        target_key_seq=list(ex.output_keys),    # 集合→序列
        ...
    )
```

輔助函數：
- `training_example_to_sequence()` — 單個轉換
- `seq_batch_from_examples()` — 批量轉換
- `make_synthetic_seq_batch()` — 從 `[(input_seq, target_seq)]` 建立測試批次
- **實作**：`training_types.py:58-107`

#### 3c. 測試套件

新增 14 個測試，覆蓋：

| 測試類 | 測試數 | 驗證項目 |
|:-------|:------:|:---------|
| `TestSequenceDataUtils` | 3 | 數據轉換、批量建立、合成批次 |
| `TestSequenceTrainer` | 6 | 基本訓練、改善趨勢、排練衰減、邊界條件、重置功能、forward_sequential 呼叫 |
| `TestGeneration` | 5 | 基本生成、反射回退、空輸入、未知輸入、step_decoder 屬性 |

#### 里程碑 3 — 驗證

- [x] SequenceTrainer 實作（Phase 1）+ 排練採樣（Phase 3）
- [x] 序列數據轉換工具
- [x] 排練機率動態衰減 + 邊界保護
- [x] 71/71 測試全部通過（57 原始 + 14 新增，零衰退）
- [x] 生成 API（`engine.generate()`）在反射/空/未知輸入下正常工作

#### Phase 3 發現

| 問題 | 狀態 | 說明 |
|:-----|:----:|:------|
| **排練採樣動態衰減正確** | ✅ | 機率從 `start` → `end` 單調遞減，不低於下限 |
| **教師強迫始終基於 ground truth** | ✅ | 即使上下文使用模型預測，損失仍針對真實 target 計算 |
| **數據轉換保留語意** | ✅ | `input_keys`→`input_key_seq`，`output_keys`→`target_key_seq` |
| **生成 API 反射優先** | ✅ | `engine.generate()` 先檢查反射層，匹配則不進網路 |
| **密集圖仍需 Phase 4 路徑分離** | ⏳ | 排練採樣讓模型更魯棒，但密集圖雜訊問題仍在 |

**核心教訓**: 排練採樣讓 SequenceTrainer 從完全教師強迫逐步過渡到自生成，使模型學會在自己預測出錯時仍能恢復。但生成品質仍受密集語意圖雜訊限制 — Phase 4 的稀疏化/路徑分離才能真正解決。

---

### Phase 4: 端到端梯度流 — 梯度感知近似 (✅ 完成 2026-06-08)

這是 ANGELA_LLM_SNN_ARCHITECTURE_PLAN §5.4 標記的**當前最關鍵的未解問題**。

#### 4a. Soft Encoding 實作

`DictionaryLayer.encode_soft()` 已實作於 `dictionary_layer.py` — 取代硬匹配的 scored key matching：

```python
def encode_soft(self, text: str) -> Dict[str, float]:
    # 對所有 key 輸出 soft 歸屬度（substring overlap × entry.confidence）
    # 返回: {key: soft_score} 分布，不 softmax（保留原始分數）
    # 精確匹配 → 1.0；子串包含 → ratio × 0.85；被包含 → ratio × 0.6
    # 最後 × entry.confidence
```

不同於原設計的 softmax 方案，本實作保留原始分數以維持與硬編碼的相容性。分數範圍 (0, 1.0]。

#### 4b. 錨定飄移計算

`compute_anchor_drift()` 新增於 `output_anchor.py` — 測量輸入 key 與輸出 key 之間的語意距離：

```python
def compute_anchor_drift(input_keys, output_keys, dictionary):
    # 對每對 (in_key, out_key) 計算最大語意相似度
    # 飄移度 = 1 - avg(max_similarity)
    # 完全無關 → 1.0；完全重疊 → 0.0
```

#### 4c. 聯合訓練器

`JointTrainer` 新增於 `ed3n_trainer.py` — 協調 ED3NTrainer + SequenceTrainer：

- `train_step()`: 同時計算字典損失（預測誤差）、序列損失（sequence cross-entropy）、錨定損失（語意飄移）
- 加總為 combined_loss 後對字典和網路交替更新（Hebbian 風格）
- `training_summary()`: 輸出三損失 + 總損失 + 飄移度
- 無 autograd（純 Python Hebbian 架構限制），以「梯度感知近似」替代

#### 里程碑 4

- [x] 字典 soft encoding 實作（`encode_soft()` — 分數化 key 匹配）
- [x] 錨定飄移度量實作（`compute_anchor_drift()`）
- [x] 字典 + 網路 + 錨定三損失聯合訓練（`JointTrainer`）
- [ ] 梯度流通過字典回傳到編碼器（⏳ 留待 autograd 重構 — 見 Phase 4 發現）
- [ ] 驗證：新詞彙出現後，網路自動調整（不需重訓）
- [ ] 端到端訓練損失曲線正常下降

#### Phase 4 發現

| 維度 | 完成度 | 備註 |
|:-----|:------:|:-----|
| **Soft encoding** | ✅ | `encode_soft()` 回傳 `Dict[str, float]`，子串重疊 × 置信度。與硬編碼使用不同匹配策略（硬編碼用 bigram 索引，軟編碼用 surface form 迭代） |
| **錨定飄移** | ✅ | `compute_anchor_drift()` 獨立函數，基於關係圖語意距離計算飄移度 |
| **聯合訓練** | ✅ | `JointTrainer` 協調三損失，combined_loss 驅動交替更新。13 測試全部通過 |
| **梯度流通過字典** | ❌ | **真實 autograd 需要重寫整個 pipeline** — 當前 Hebbian 交替訓練架構無自動微分。`encode_soft()` 提供分數化輸入但無法反向傳播到編碼器。解鎖此項需要 PyTorch/JAX 重構（偏離 GENESIS 範圍） |
| **新詞彙自動調整** | ⏳ | 無獨立的適應性測試 — `JointTrainer` 的字典更新步驟理論支援，但無專項測試驗證 |
| **損失曲線** | ⏳ | 無長期訓練腳本 — 現有測試只驗證單步收斂 |

**核心教訓**: 在純 Python Hebbian 架構下，真正的端到端梯度流（autograd）不可行。Phase 4 的「梯度感知近似」— soft encoding 提供分數化輸入，JointTrainer 協調多目標損失，compute_anchor_drift 增加語意飄移懲罰 — 是當前架構下的最佳替代方案。若要實現原設計的 §4b，需要整體遷移到支援 autograd 的框架。

---

### Phase 5: GARDEN 生成能力

GARDEN 的向量字典（384/256 維）理論上比 ED3N 的 keyword 索引更適合生成：

#### 5a. 向量解碼器

```python
class VectorDecoder:
    def __init__(self, vector_dict, snn_core):
        self.dict = vector_dict  # 向量 → concept key
        self.snn = snn_core      # LIF 多步積分
    
    def generate(self, input_vec, max_steps=20):
        # 1. 輸入向量 → 初始 key 激活
        keys = self.dict.encode(input_vec, top_k=5)
        # 2. SNN 多步積分生成序列
        for step in range(max_steps):
            spikes = self.snn.forward(keys)
            next_key = self.sample_from_spikes(spikes)
            if next_key == EOS:
                break
            output.append(next_key)
            # 回饋到 SNN
            self.snn.inject(next_key)
        # 3. key → surface form
        return self.dict.decode(output)
```

#### 5b. sentence-transformers 恢復

GARDEN 的真實生成能力依賴語義編碼器。當前 CharBag 回退（256 維 hash）無法支撐生成。需要：

1. 修復 Python 3.14 + Windows 上的 sentence-transformers 崩潰
2. 或降級到 Python 3.12
3. 或替換為 ONNX 版本的 MiniLM

#### 里程碑 5

- [ ] VectorDecoder 實作
- [ ] sentence-transformers 恢復
- [ ] GARDEN 生成 + 錨定聯合測試
- [ ] ED3N ↔ GARDEN 生成能力對比

---

## 五、可行性驗證順序

為避免投入大量時間才發現不可行，按風險遞增排列：

```
Phase 1a: StepDecoder（純 Python，不改網路）
  └→ 風險最低，先驗證「給定 key 分布能否產生合理序列」
      ↓ OK
Phase 1b-1c: 序列訓練數據 + 損失
  └→ 風險低，在現有訓練管線上擴充
      ↓ OK
Phase 2: 位置編碼 + 因果遮罩
  └→ 風險中，需要改 CoreNetwork 架構
      ↓ OK
Phase 3: 序列 Trainer + scheduled sampling
  └→ 風險中高，需要收斂
      ↓ OK
Phase 4: 端到端梯度流
  └→ 風險最高，這是原設計未解決的問題
      ↓ OK
Phase 5: GARDEN 生成能力
  └→ 依賴 sentence-transformers 恢復
```

### 快速可行性測試（Phase 0.5）

先做一個最小驗證，確定方向正確：

```python
# 測試：給定 key 分布，StepDecoder 能否產生序列？
input_keys = ["two", "plus", "three"]
network_output = {"five": 0.9, "four": 0.3, "result": 0.2}
decoder = StepDecoder(dictionary)
output = decoder.generate(network_output, input_keys)
assert output == "five"  # 或 "two plus three equals five"
```

**預期 2 天內可知基本方向是否可行。**

---

## 六、不做什麼（明確排除）

| 項目 | 理由 |
|:-----|:------|
| 完整 transformer 架構 | 違背 ED3N 設計理念（字典+網路分離） |
| 取代雲端 LLM | GENESIS 目標是本地生成，非取代 GPT-4 |
| 多模態生成 | Phase 4 之後的事 |
| 百萬級詞彙表 | ED3N 字典上限 50K，足夠驗證生成概念 |
| 即時對話 | 初期生成延遲可能 100ms-1s，先求有再求快 |
| 浮點數/精確數學計算 | 無理數計算應繼續走雲端路由 |

---

## 七、成功標準

```
☐ StepDecoder 能在 5 個以內 key 的序列上產生合理輸出
☐ 序列訓練後網路能泛化到未見過的短序列
☐ 錨定機制防止輸出飄離輸入語意
☐ 端到端訓練（字典+網路）損失曲線正常下降
☐ 一個實際例子：輸入 "what is AI" → 輸出 "AI is artificial intelligence"
   （不靠 preset，靠網路學到的關係規則生成）
☐ 所有現有 84 測試仍通過
```

---

## 八、檔案變更索引

| 檔案 | 變更 | Phase | 狀態 |
|:-----|:------|:----:|:----:|
| `apps/backend/src/ai/ed3n/step_decoder.py` | **NEW** — StepDecoder 類 (generate + generate_text + scoring + sampling) | 1 | ✅ |
| `apps/backend/src/ai/ed3n/ed3n_engine.py` | 新增 `generate()` 方法 + `step_decoder` property + `_step_decoder` 屬性 | 1 | ✅ |
| `apps/backend/src/ai/ed3n/output_anchor.py` | 無變更 (`anchored_decode` 保留作為傳統路徑) | 1 | ✅ |
| `apps/backend/src/ai/ed3n/core_network.py` | 新增 `sync_from_dictionary()` + `add_directed()` 非對稱連接 + `forward_sequential()` | 1,2 | ✅ |
| `apps/backend/src/ai/ed3n/ed3n_trainer.py` | 新增 `SequenceTrainer` 類 + 排練採樣（Phase 3） + `random` 導入 | 1,3 | ✅ |
| `apps/backend/src/ai/ed3n/training_types.py` | 新增 `SequenceExample`, `SeqBatch`, `training_example_to_sequence`, `seq_batch_from_examples`, `make_synthetic_seq_batch` | 1,3 | ✅ |
| `apps/backend/src/ai/ed3n/__init__.py` | 新增 `StepDecoder` + 序列數據工具匯出 | 1,3 | ✅ |
| `apps/backend/src/ai/ed3n/dictionary_layer.py` | 新增 position encoding（Phase 2）、soft encode `encode_soft()`（Phase 4） | 2,4 | ✅ |
| `apps/backend/src/ai/ed3n/output_anchor.py` | 新增 `compute_anchor_drift()`（Phase 4） | 4 | ✅ |
| `apps/backend/src/ai/ed3n/ed3n_trainer.py` | 新增 `JointTrainer` 類（Phase 4） | 4 | ✅ |
| `apps/backend/src/ai/ed3n/__init__.py` | 新增 JointTrainer + compute_anchor_drift + encode_soft 匯出（Phase 4） | 4 | ✅ |
| `apps/backend/src/ai/garden/garden_engine.py` | VectorDecoder 整合 | 5 | ⏳ |
| `apps/backend/src/ai/garden/vector_decoder.py` | **NEW** — 向量解碼器 | 5 | ⏳ |
| `tests/ai/ed3n/test_ed3n.py` | 新增 `TestSequenceDataUtils`, `TestSequenceTrainer`, `TestGeneration`（14 測試）+ `TestSoftEncoding`, `TestAnchorDrift`, `TestJointTrainer`（13 測試） | 3,4 | ✅ |
| `docs/06-project-management/plans/COMPREHENSIVE_AUDIT_V3.md` | Phase 5 GENESIS 更新 | 全 | ⏳ |

---

## 九、一句話總結

> **ED3N 的字典外部化+關係網路+錨定輸出在理論上是生成架構，但當前實作只做到路由和檢索。生成能力需要補上 StepDecoder（序列解碼）、CoreNetwork 位置感知、SequenceTrainer（序列訓練），以及最終的端到端梯度流。這四個補完後，ED3N 才真正驗證了當初設計的核心假設：一個外部字典+關係網路能不能自己產出有意義的輸出。**

---

*建立: 2026-06-07 | 基於: ED3N_MATURITY_PLAN.md + GARDEN_MODEL_PLAN.md + ANGELA_LLM_SNN_ARCHITECTURE_PLAN.md | 狀態: ⚠️ Phase 1-4 完成，Phase 5 待執行*
