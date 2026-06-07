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

- [ ] `StepDecoder` 實作 + 測試
- [ ] 序列數據格式定義
- [ ] 在簡單序列（0-9 數字序列）上驗證生成
- [ ] P(2\|1,+) > P(5\|1,+) 之類的條件機率合理
- [ ] 57 現有測試仍全部通過

---

### Phase 2: 核心網路升級 — 序列感知

目前 CoreNetwork 將輸入視為**無序 key 集合**。生成需要**有序 token 序列**。

#### 2a. 位置編碼

在 key 進入網路前附加位置資訊：

```python
def forward_with_positions(self, input_key_sequence):
    # 每個 key 附加其在序列中的位置編碼
    encoded = []
    for i, key in enumerate(input_key_sequence):
        pos_vec = self.position_encoding(i, dim=16)
        encoded.append((key, pos_vec))
    # 網路同時看到 "什麼(key)" 和 "位置=第3個"
    return self.forward(encoded)
```

#### 2b. 因果遮罩（Causal Masking）

生成時，每個 key 只能看到自己之前的 key：

```python
def generate_step(self, context_keys, target_position):
    # target_position 之前的 key 可見
    mask = [i < target_position for i in range(len(context_keys))]
    return self.forward(context_keys, attention_mask=mask)
```

#### 2c. 上下文滑窗

當前 `compute_spike_propagation` 用 3 hops 固定深度。替換為可配置滑窗：

```python
max_context = 8  # 或 16, 32
context = context[-(max_context):]  # 只保留最近 N 個 key
```

#### 里程碑 2

- [ ] 位置編碼實作
- [ ] 因果遮罩集成到 CoreNetwork.forward()
- [ ] 滑窗上下文替代固定 hop
- [ ] 驗證：重複序列識別（ABAB → 預測下一個是 A 還是 B）

---

### Phase 3: 訓練系統升級

當前 `ED3NTrainer` 無法訓練序列生成。需要新增：

#### 3a. 序列 Trainer

```python
class SequenceTrainer:
    def train_step(self, batch: List[Tuple[List[str], List[str]]]):
        # batch: [(input_key_seq, target_key_seq), ...]
        total_loss = 0
        for input_seq, target_seq in batch:
            # Teacher forcing
            network.reset()
            context = input_seq[:]
            for step, target_key in enumerate(target_seq):
                logits = network.forward(context)
                loss = F.cross_entropy(logits, target_key)
                total_loss += loss
                # Teacher forcing: 用真實 target 而非網路預測
                context.append(target_key)
                context = context[-self.max_context:]
        return total_loss / len(batch)
```

#### 3b. 從現有數據生成序列訓練對

利用現有 43K 樣本：

```
# 當前格式 (key 集合):
input_keys = ["178", "+", "101"]
output_keys = ["279"]

# 需要轉換為序列:
input_seq = ["178", "+", "101"]
target_seq = ["279"]
```

對知識問答，需要分詞器將長 response 拆成多個 key：

```
input_seq = ["what", "is", "AI"]
target_seq = ["Artificial", "Intelligence", "is", "the", "simulation", ...]
```

#### 3c. 教師強迫 → 排練（Scheduled Sampling）

逐步從教師強迫過渡到模型自生成：

```python
def train_step(self, batch, epoch):
    use_teacher = max(0, 1.0 - epoch * 0.1)  # 衰減
    for input_seq, target_seq in batch:
        context = input_seq[:]
        for step, target_key in enumerate(target_seq):
            if random.random() < use_teacher:
                context.append(target_key)  # 教師強迫
            else:
                pred = network.forward(context)
                context.append(pred)  # 模型自己的預測
```

#### 里程碑 3

- [ ] SequenceTrainer 實作
- [ ] 從現有數據集（43K 樣本）提取序列對
- [ ] 教師強迫訓練收斂
- [ ] 排練訓練後模型能自己生成短序列
- [ ] 簡單加法泛化：訓練 1+1~50+50，測試 51+49

---

### Phase 4: 端到端梯度流（原設計中未解的核心問題）

這是 ANGELA_LLM_SNN_ARCHITECTURE_PLAN §5.4 標記的**當前最關鍵的未解問題**。

#### 4a. 字典編碼可微分近似

當前 `DictionaryLayer.encode()` 是離散的（key 存在/不存在）。需要近似：

```python
def encode_soft(self, text):
    # 對所有 key 輸出 soft 歸屬度，而非硬匹配
    # 每個 key: similarity(text, key.surface_forms)
    # 返回: {key: soft_score} 分布
    scores = {}
    for key, entry in self.entries.items():
        max_sim = max(
            self.text_similarity(text, sf)
            for sf in entry.surface_forms.values()
        )
        if max_sim > self.threshold:
            scores[key] = max_sim * entry.confidence
    return softmax(scores, temperature=0.5)
```

#### 4b. 聯合損失

```python
# 字典損失: 新概念檢測 + 置信度調整
loss_dict = self.dictionary.criterion(input, output_keys)

# 網路損失: 序列預測交叉熵
loss_net = self.network.criterion(input_keys, target_seq)

# 錨定損失: 輸出不能偏離輸入太遠
loss_anchor = self.anchor.criterion(output, input_keys)

# 聯合
total_loss = (loss_dict * dict_lr + loss_net * net_lr + loss_anchor * anchor_lr)
total_loss.backward()
```

#### 里程碑 4

- [ ] 字典 soft encoding 實作
- [ ] 字典 + 網路 + 錨定三損失聯合訓練
- [ ] 梯度流通過字典回傳到編碼器
- [ ] 驗證：新詞彙出現後，網路自動調整（不需重訓）
- [ ] 端到端訓練損失曲線正常下降

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
☐ 所有現有 57 測試仍通過
```

---

## 八、檔案變更索引

| 檔案 | 預估變更 | Phase |
|:-----|:---------|:-----:|
| `apps/backend/src/ai/ed3n/ed3n_engine.py` | 新增 generate() 方法 | 1 |
| `apps/backend/src/ai/ed3n/step_decoder.py` | **NEW** — StepDecoder 類 | 1 |
| `apps/backend/src/ai/ed3n/output_anchor.py` | 擴充 anchored_decode → anchored_generate | 1 |
| `apps/backend/src/ai/ed3n/core_network.py` | 新增位置編碼 + 因果遮罩 | 2 |
| `apps/backend/src/ai/ed3n/ed3n_trainer.py` | 新增 SequenceTrainer | 3 |
| `apps/backend/src/ai/ed3n/training_types.py` | 新增 SequenceExample, SeqBatch | 3 |
| `scripts/generate_training_data.py` | 新增序列格式輸出 | 3 |
| `apps/backend/src/ai/ed3n/dictionary_layer.py` | 新增 soft_encode() 可微分近似 | 4 |
| `apps/backend/src/ai/garden/garden_engine.py` | 新增 VectorDecoder 整合 | 5 |
| `apps/backend/src/ai/garden/vector_decoder.py` | **NEW** — 向量解碼器 | 5 |
| `tests/ai/ed3n/test_generation.py` | **NEW** — 生成能力測試套件 | 1-5 |
| `docs/06-project-management/plans/COMPREHENSIVE_AUDIT_V3.md` | 更新 Phase 5 狀態 | 全 |

---

## 九、一句話總結

> **ED3N 的字典外部化+關係網路+錨定輸出在理論上是生成架構，但當前實作只做到路由和檢索。生成能力需要補上 StepDecoder（序列解碼）、CoreNetwork 位置感知、SequenceTrainer（序列訓練），以及最終的端到端梯度流。這四個補完後，ED3N 才真正驗證了當初設計的核心假設：一個外部字典+關係網路能不能自己產出有意義的輸出。**

---

*建立: 2026-06-07 | 基於: ED3N_MATURITY_PLAN.md + GARDEN_MODEL_PLAN.md + ANGELA_LLM_SNN_ARCHITECTURE_PLAN.md | 狀態: ⚠️ 設計驗證未開始*
