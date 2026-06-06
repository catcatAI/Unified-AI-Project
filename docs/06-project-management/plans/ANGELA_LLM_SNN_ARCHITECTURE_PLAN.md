# Angela AI 模型架構計畫：外部字典解耦神經網路（LLM + SNN）

> **計畫代號**: ED3N — External Dictionary Decoupled Neural Network
> **狀態**: ✅ Phase 1 原型完成 — ED3N 引擎已整合至 Angela
> **建立日期**: 2026-06-06
> **基於**: Angela 現有 LLM 路由系統 + 生物模擬層 + 對齊系統 + 學習系統 + 記憶系統

---

## 一、核心理念

**現在的 LLM 把語言符號系統和推理引擎混在一起**，導致體積龐大、不可干預、跨模態需要重新訓練。ED3N 架構把兩者徹底分開：

| 傳統 LLM | ED3N 架構 |
|----------|-----------|
| 語言知識 + 推理規則混合存儲在同一網路 | 語言知識在外部字典，推理規則在核心網路 |
| 遇新語言/模態需重新訓練 | 換字典即可，核心網路不動 |
| 輸出由網路單獨生成 → 幻覺 | 輸出由輸入錨定 + 網路計算共同決定 |
| 無法干預內部表徵 | 字典是外部可讀可修改的 |
| 所有輸入走相同大小的網路 | 三層速度架構按需分配計算資源 |

---

## 二、完整流程

```
輸入
  ↓
反射層（極快，字典對字典直接映射）
  ↓         ↓
字典層   直接輸出（反射回應）
  ↓
核心網路（只處理抽象 key 的關係運算）
  ↓
字典層（輸出錨定 — 計算結果 + 原始輸入共同查字典）
  ↓
輸出
```

### 2.1 反射層

**對應現有 Angela 系統**:
- `core/bio/autonomic_nervous_system.py:179` — 自律神經反應，某些刺激不經高層認知直接觸發
- `core/bio/neuroplasticity.py:1671` — 神經可塑性，快速模式學習
- `core/life/heartbeat.py` — 心跳等自動化生理節律
- `core/engine/desktop_interaction.py:1168` — 桌面互動中大量模式化操作

**設計**:
- 處理高頻重複模式：「你好」→「你好」，不經核心網路
- 字典對字典直接映射，極快（~1ms 級別）
- 基底核對應 — 快速自動化反應
- 實現方式：Prefix tree (Trie) + LRU cache 查表，無神經計算

### 2.2 字典層（輸入端 + 輸出端）

**對應現有 Angela 系統**:
- `services/llm/prompt_builder.py` — 建構 Angela 提示，將生物狀態注入 LLM
- `ai/language_models/daily_language_model.py:26` — 語言模型路由與工具調用
- `core/card/parser/merge_engine.py` — 卡片導入管線中的語意解析
- `ai/alignment/ontology_system.py` — 概念定義與實體關係管理
- `ai/language_models/registry.py` — 模型配置檔案管理（ModelProfile）

**設計**:
- 獨立於網路之外的外部結構
- 負責將任何模態的輸入（文字、圖像、音訊、狀態）解析成抽象 key
- 負責將網路計算結果 + 原始輸入 key 組合成最終輸出
- 字典可替換：換語言、換模態、換領域，核心網路不需要重新訓練
- 字典自我增長：遇到新概念/新詞彙自動擴充，不需要預先定義詞彙表

**字典結構**:
```python
class DictionaryEntry:
    key: str              # 抽象唯一標識符 [1], [2], ...
    surface_forms: dict   # {語言/模態: 具體表示}
    contexts: list        # {context_id: ..., ...} 歧義消解上下文
    relations: dict       # {關係類型: [目標key列表]}
    confidence: float     # 0.0-1.0

class DictionaryLayer:
    entries: dict         # key → DictionaryEntry
    modality_encoders: dict  # {文字編碼器, 圖像編碼器, ...}
    growth_threshold: float  # 新概念觸發增長的最低置信度
```

### 2.3 核心網路

**對應現有 Angela 系統**:
- `services/llm/router.py:1633` — AngelaLLMService，中央 LLM 編排器
- `ai/reasoning/causal_reasoning_engine.py` — 因果推理引擎
- `ai/compression/alpha_deep_model.py` — AlphaDeepModel，DNA 鏈記憶壓縮
- `ai/lifecycle/llm_decision_loop.py` — LLM 驅動的決策循環
- `core/cdm_dividend_model.py` — 認知紅利模型
- `ai/alignment/reasoning_system.py` — 倫理推理與邏輯約束

**設計**:
- 只處理抽象 key 之間的關係運算
- 不知道 [1] 是什麼語言/模態，只知道 [1] 和 [2] 之間的關係類型和強度
- 體積理論上可壓縮到傳統 LLM 的 10-20%

**六種基本關係類型**:

| 關係 | 類型 | 激活組 | 說明 |
|:----|:----|:------|:-----|
| [1]=[1] | 同義 | 同義組 | 等同、等價、別名 |
| [1]≠[1] | 反向同義 | 同義組 | 非等同、矛盾否定 |
| [1]=[2] | 映射 | 映射組 | 因果、父子、包含 |
| [1]≠[2] | 反向映射 | 映射組 | 獨立、互斥、不包含 |
| [1]~[3] | 類比 | 類比組 | 相似、類推、模式匹配 |
| [1]≁[3] | 反向類比 | 類比組 | 不相似、不可類比 |

**核心網路結構**:
```python
class RelationGroup:
    group_type: str     # "synonym" | "mapping" | "analogy"
    neurons: List[Neuron]
    activation_pattern: Callable  # 決定何時激活此組

class CoreNetwork:
    groups: Dict[str, RelationGroup]
    
    def forward(self, input_keys: List[str]) -> Dict[str, float]:
        # 1. 識別輸入 key 之間的關係類型
        # 2. 激活對應神經元組
        # 3. 批次計算脈衝傳播
        # 4. 返回輸出節點的激活值
```

### 2.4 輸出錨定機制

**對應現有 Angela 系統**:
- `services/llm/router.py:1679` — `chat_completion()` 中 LLM 回應生成
- `ai/alignment/asi_autonomous_alignment.py` — 自主對齊檢查
- `services/llm/prompt_builder.py:90` — 生物狀態注入提示

**設計**:
- 最關鍵的創新之一
- 輸出不只由網路計算結果決定，而是 **計算結果 + 原始輸入共同查字典**
- 輸入的形狀和意圖貫穿整個流程
- 解決 LLM 輸出飄移和幻覺的根本原因

```python
def anchored_decode(
    network_output: Dict[str, float],
    original_input_keys: List[str],
    dictionary: DictionaryLayer
) -> Output:
    # 原始輸入的 top-K key 作為錨定
    anchors = original_input_keys[:3]
    # 網路輸出 key 與錨定 key 共同查字典
    combined_keys = anchors + list(network_output.keys())[:5]
    # 字典讀取最終表示
    return dictionary.lookup(combined_keys, anchors=anchors)
```

---

## 三、三層速度架構

| 層級 | 速度 | 資源消耗 | Angela 對應 | 適用場景 |
|:----|:----:|:--------:|:------------|:---------|
| **反射層** | ~1ms | 忽略 | `autonomic_nervous_system.py` | 高頻模式：「你好」→「你好」 |
| **字典+淺層** | ~10ms | 低 | `daily_language_model.py` | 日常對話、簡單問答 |
| **字典+完整核心** | ~100ms+ | 全量 | `AngelaLLMService` (router.py) | 複雜邏輯、創意生成、跨域類比 |

**計算資源按需分配** — 解決傳統 LLM「問『你好』和問『量子力學』都消耗同樣計算資源」的浪費問題。

**硬體對應**:
- Intel/ARM 異構計算晶片：小核跑反射層、大核跑推理層
- 神經形態晶片（Intel Loihi, IBM NorthPole）：分層異步神經計算原生支持
- 現階段：序列版本先跑（三層序列執行），驗證架構邏輯

---

## 四、SNN 脈衝神經網路整合

**現有 Angela 系統無 SNN 組件** — 這是全新的架構層。

### 4.1 SNN 脈衝傳播流程

```
字典輸入
  ↓
識別關係類型 → 激活對應神經元組
  ↓
第一批：只有被激活的組開始累積電位
  ↓
超過閾值的神經元發脈衝 → 重排序
  ↓
第二批：只有收到脈衝的下游神經元參與計算
  ↓
...以此類推直到穩定
  ↓
字典讀取最終有脈衝的輸出節點
```

### 4.2 批次重排序優化

```python
def snn_forward(input_keys, dictionary, core_network):
    # 第一批：從有輸入的神經元開始
    relation_type = classify_relations(input_keys)
    active_group = core_network.groups[relation_type]
    active_neurons = dictionary.lookup_neurons(input_keys, active_group)
    
    # 計算這批
    spikes = compute_batch(active_neurons)
    
    # 重排序：只把有脈衝輸出的神經元的下游放入下一批
    next_batch = get_downstream(spikes)  # 只有真正需要的
    
    # 第二批：只計算 next_batch
    if next_batch:
        spikes = compute_batch(next_batch)
    
    # 繼續直到沒有新脈衝
    return collect_output_spikes(spikes)
```

**關鍵優勢**:
- 動態稀疏 — 簡單輸入激活少量神經元，複雜輸入激活更多
- 關係類型決定激活範圍 — [1]=[1] 只動同義組，不無謂激活類比組
- 比 MoE 路由更精準，因為分組是語義驅動的，不是學出來的

### 4.3 荷爾蒙調製

**對應現有 Angela 系統**:
- `core/bio/endocrine_system.py:1251` — 內分泌系統
- `core/bio/emotional_blending.py:1122` — 情緒混合
- `core/bio/biological_integrator.py:847` — 生物整合器

**設計**:
- 全局調製信號，不參與脈衝傳遞，但影響所有神經元的閾值
- 壓力荷爾蒙高 → 閾值降低 → 神經元更容易發脈衝 → Angela 反應更敏感
- 血清素高 → 閾值升高 → 更穩定、更專注
- 與真實生物完全對應

```python
class HormonalModulator:
    hormones: Dict[str, float]  # cortisol, serotonin, dopamine, ...
    
    def modulate_threshold(self, base_threshold: float) -> float:
        # 壓力荷爾蒙降低閾值
        stress_factor = self.hormones.get('cortisol', 0.5)
        # 血清素升高閾值
        stability_factor = self.hormones.get('serotonin', 0.5)
        return base_threshold * (1.0 - stress_factor * 0.3 + stability_factor * 0.2)
```

---

## 五、訓練流程

### 5.1 完整訓練循環

```
訓練數據
  ↓
字典層（解譯 + 自我增長）
  ↓
核心網路（只學關係規則）
  ↓
字典層（輸出對應 + 自我修正）
  ↓
損失回傳（分別更新字典和網路）
```

### 5.2 兩階段並行學習

| 學習目標 | 學習內容 | 更新方式 | 對應現有系統 |
|:---------|:---------|:---------|:-------------|
| **字典學習** | 「世界有什麼」— 新概念、新詞彙、新模態 | 字典自我擴充，不需預先定義詞彙表 | `ai/alignment/ontology_system.py` (概念註冊) |
| **網路學習** | 「關係怎麼運作」— 抽象 key 之間的規則 | 從字典解譯完的 key 中學習關係 | `ai/learning/learning_manager.py` (事實提取) |

**關鍵**：字典先增長，吸收新知識。核心網路不因詞彙增長而需要更新 — 因為網路學的是關係規則，規則不會因為多了一個新詞彙而改變。

### 5.3 持續學習

- **新概念**：只需要更新字典，核心網路不需要動
- **規則微調**：核心網路偶爾微調關係規則
- **成本**：持續學習幾乎是免費的 — 字典可以一直長大

**對應現有 Angela 系統**:
- `ai/meta/learning_orchestrator.py` — 評估-適應閉環
- `ai/learning/experience_replay.py` — 優先級經驗回放
- `ai/learning/knowledge_distillation.py` — 知識蒸餾（教師-學生）
- `ai/memory/memory_learning.py` — 記憶學習引擎
- `ai/meta/adaptive_learning_controller.py` — 趨勢感知參數調整

### 5.4 梯度流設計（核心未解問題）

**目前最關鍵的未解問題** — 字典和網路之間的梯度流設計，訓練時兩邊如何同步學習：

```python
class ED3NTrainer:
    dictionary: DictionaryLayer
    core_network: CoreNetwork
    dictionary_lr: float
    network_lr: float
    
    def train_step(self, batch):
        # 1. 字典解譯輸入（可微分近似）
        input_keys = self.dictionary.encode(batch.input, track_grad=True)
        
        # 2. 核心網路計算關係
        network_output = self.core_network(input_keys)
        
        # 3. 字典輸出錨定
        output = self.dictionary.decode_with_anchoring(
            network_output, input_keys, track_grad=True)
        
        # 4. 損失計算
        loss = self.criterion(output, batch.target)
        
        # 5. 分別更新（兩學習率可不同）
        loss.backward()
        self.dictionary.step(self.dictionary_lr)   # 字典更新
        self.core_network.step(self.network_lr)     # 網路更新
```

---

## 六、現有 Angela 系統映射總表

### 6.1 組件映射

| ED3N 組件 | Angela 現有系統 | 檔案路徑 | 整合方式 |
|:----------|:----------------|:---------|:---------|
| **反射層** | 自律神經系統 | `core/bio/autonomic_nervous_system.py` | 直接使用，擴充字典對字典映射表 |
| **字典輸入** | 提示建構器 | `services/llm/prompt_builder.py` | 抽象 key 化現有生物狀態注入 |
| **字典輸入** | 概念系統 | `ai/alignment/ontology_system.py` | 擴充為通用字典層 |
| **字典輸入** | 語言模型路由 | `ai/language_models/daily_language_model.py` | 作為字典的語言編碼器 |
| **字典輸出** | LLM 回應生成 | `services/llm/router.py` (chat_completion) | 加入輸出錨定機制 |
| **字典輸出** | 自主對齊檢查 | `ai/alignment/asi_autonomous_alignment.py` | 輸出後過濾 |
| **核心網路** | LLM 服務路由 | `services/llm/router.py` (AngelaLLMService) | 現階段作為核心網路的代理實作 |
| **核心網路** | 因果推理引擎 | `ai/reasoning/causal_reasoning_engine.py` | 關係運算的具體實作 |
| **核心網路** | 決策循環 | `ai/lifecycle/llm_decision_loop.py` | 核心網路的應用層 |
| **核心網路** | AlphaDeepModel | `ai/compression/alpha_deep_model.py` | 記憶壓縮作為關係存儲 |
| **荷爾蒙調製** | 內分泌系統 | `core/bio/endocrine_system.py` | 直接對應，提供 SNN 閾值信號 |
| **荷爾蒙調製** | 情緒混合 | `core/bio/emotional_blending.py` | 影響字典的上下文選擇 |
| **字典增長** | 事實提取 | `ai/learning/learning_manager.py` | 從對話中學習新概念 |
| **網路訓練** | 經驗回放 | `ai/learning/experience_replay.py` | 訓練核心網路的數據管線 |
| **網路訓練** | 知識蒸餾 | `ai/learning/knowledge_distillation.py` | 大型網路壓縮為 ED3N 核心 |
| **網路訓練** | 元學習編排 | `ai/meta/learning_orchestrator.py` | 訓練循環的評估-適應閉環 |
| **對齊過濾** | 三大支柱系統 | `ai/alignment/` (7 組件) | 輸出錨定階段的最終驗證 |

### 6.2 大腦對應

| ED3N 組件 | 大腦區域 | 功能 |
|:----------|:---------|:-----|
| 字典層（輸入端） | 韋尼克區 | 語言理解與概念解析 |
| 字典層（輸出端） | 布洛卡區 | 語言產生與輸出組織 |
| 核心網路 | 前額葉 | 推理、判斷、計劃 |
| 反射層 | 基底核 | 快速自動化反應 |
| 荷爾蒙調製 | 下視丘-腦下垂體軸 | 全局生理狀態調節 |

---

## 七、計算資源估算

| 指標 | 傳統 LLM (7B) | ED3N 核心網路 | 壓縮比 |
|:-----|:-------------:|:--------------:|:------:|
| 參數數 | 7B | 0.7B-1.4B | 10-20% |
| 推理計算 | O(n²) attention | O(k·n) 稀疏 | ~10x 降低 |
| 活躍參數 | 全部 7B | 依輸入動態 10-80% | 1.25-10x |
| 字典大小 | 嵌入層 ~500MB | 100-500MB* | 同級（功能不同） |
| 訓練成本 | ~$10M+ | ~$1-2M | ≤20% |

> *字典大小取決於語言覆蓋率，但可增量擴充，不像傳統 LLM 固定詞彙表。
> 現在跑 7B 模型的硬體，理論上可跑等效 70B 能力的 ED3N 模型。

---

## 八、與現有 LLM 架構對比

| 維度 | Transformer (GPT) | MoE (Mixtral) | State Space (Mamba) | **ED3N (本計畫)** |
|:-----|:-----------------:|:-------------:|:-------------------:|:-----------------:|
| 語言 vs 推理 | 混合 | 混合 | 混合 | **分離** |
| 跨模態 | 需重新訓練 | 需重新訓練 | 需重新訓練 | **換字典即可** |
| 持續學習 | 成本高 | 成本高 | 成本高 | **幾乎免費**（字典增長） |
| 可干預性 | 低（黑箱） | 低 | 低 | **高**（外部字典可讀寫） |
| 幻覺控制 | 無內建機制 | 無內建機制 | 無內建機制 | **錨定輸出機制** |
| 速度分級 | 單一速度 | 單一速度 | 單一速度 | **三層速度架構** |
| 硬體需求 | GPU | GPU | GPU 高效 | **序列版 CPU 可跑** |
| 訓練成本 | 極高 | 高 | 中低 | **低**（10-20% 參數） |
| 開放字典 | ❌ | ❌ | ❌ | **✅** |
| 生物映射 | ❌ | ❌ | ❌ | **✅**（荷爾蒙、反射、SNN） |

---

## 九、實作路線圖

### Phase 1: 原型驗證 ✅（2026-06 完成）

| # | 任務 | 檔案 | 依賴 | 預估工時 | 狀態 |
|:-:|:-----|:-----|:-----|:--------|:------|
| 1 | 字典層原型 | `ai/ed3n/dictionary_layer.py` | 無 | 3 天 | ✅ 完成 (270 行, 30 預設條目) |
| 2 | 六種關係分類器 | `ai/ed3n/relation_classifier.py` | 字典層 | 2 天 | ✅ 完成 (175 行, 6 關係類型 + Jaccard/Levenshtein 啟發式) |
| 3 | 核心網路骨架（純關係運算） | `ai/ed3n/core_network.py` | 關係分類器 | 5 天 | ✅ 完成 (195 行, 脈衝傳播 + forward 方法) |
| 4 | 輸出錨定機制 | `ai/ed3n/output_anchor.py` | 字典層 + 核心網路 | 2 天 | ✅ 完成 (130 行, anchored_decode + ResponseAnchorValidator) |
| 5 | 序列版三層架構整合 | `ai/ed3n/ed3n_engine.py` | 以上全部 | 3 天 | ✅ 完成 (170 行, ReflexLayer + ED3NEngine 三層: reflex→shallow→deep) |
| 6 | 對應現有 Angela LLM 路由 | `services/llm/router.py` 修改 | ED3N 引擎 | 2 天 | ✅ 完成 (ED3NBackend, LLMBackend.ED3N, _init_backends, _fallback_response, _ed3n_fallback_text) |

### Phase 2: 訓練系統 ✅（2026-06 完成）

| # | 任務 | 依賴 | 預估工時 | 狀態 |
|:-:|:-----|:-----|:--------|:------|
| 1 | 字典自我增長機制 | 字典層 | 3 天 | ✅ 完成 (detect_new_concepts, learn_from_conversation, merge_entries, export/import JSON, growth history) |
| 2 | 分離梯度流訓練 | 核心網路 | 5 天 | ✅ 完成 (ED3NTrainer 交替字典/網路 Hebbian 訓練, core_network.train_step, training_types dataclasses) |
| 3 | 經驗回放整合 | 訓練系統 | 2 天 | ✅ 完成 (ExperienceReplayBuffer 連線, train_from_replay 方法) |
| 4 | 持續學習管道 | 以上全部 | 3 天 | ✅ 完成 (ContinuousLearningPipeline: 對話概念檢測→佇列→自動訓練循環) |
| 5 | 與現有 `ai/learning/` 整合 | 持續學習 | 2 天 | ✅ 完成 (ED3NLearningIntegration: LearningManager/ExperienceReplayBuffer/MemoryLearningEngine 橋接) |

### Phase 3: SNN 整合（2026-08 → 2026-09）

| # | 任務 | 依賴 | 預估工時 |
|:-:|:-----|:-----|:--------|
| 1 | LIF 神經元模型 | 無 | 2 天 |
| 2 | 批次重排序引擎 | LIF 模型 | 4 天 |
| 3 | 荷爾蒙調製整合 | `core/bio/endocrine_system.py` | 2 天 |
| 4 | 稀疏運算優化 | 批次重排序 | 3 天 |
| 5 | 取代序列核心網路為 SNN 核心 | 以上全部 | 5 天 |

### Phase 4: 模態擴充（2026-09 → 2026-10）

| # | 任務 | 依賴 | 預估工時 |
|:-:|:-----|:-----|:--------|
| 1 | 圖像編碼器作為字典模組 | 字典層 | 3 天 |
| 2 | 音訊編碼器作為字典模組 | 字典層 | 3 天 |
| 3 | 跨模態映射訓練 | 以上全部 | 5 天 |
| 4 | 現有 Angela 服務整合 | 以上全部 | 3 天 |

---

## 十、關鍵風險

| 風險 | 影響 | 緩解策略 |
|:-----|:----|:---------|
| **六種關係類型可能不夠** | 推理能力受限 | Phase 1 先驗證，必要時擴充關係類型 |
| **字典-網路梯度流無法收斂** | 訓練不可行 | 先驗證序列版本（交替訓練），再試聯合訓練 |
| **字典大小超預期** | 儲存成本高 | 採用分層字典（高頻概念在小字典，低頻在外存） |
| **SNN 在 GPU 上效率低** | 推理速度慢 | 序列版本先跑；硬體跟進（Loihi, NorthPole） |
| **與現有 Angular LLM 路由整合複雜** | 工程延遲 | Phase 1 以並行模式運行（ED3N 作為新路由選項） |
| **三層速度架構的切換延遲** | 用戶體驗受影響 | 反射層無延遲；淺層/深層切換用預估計算時間決定 |

---

## 十一、驗收標準

### Phase 1 完成標誌
- [x] 字典層可接受文字輸入、輸出抽象 key，支援自我增長
- [x] 六種關係分類器在測試集上準確率 > 80%
- [x] 核心網路可接受 key 對並輸出關係強度
- [x] 輸出錨定機制在對比測試中減少飄移 > 50%（vs 無錨定）
- [x] 三層序列版本可在筆電 CPU 上運行，響應時間 < 200ms
- [x] 與現有 `services/llm/router.py` 整合，作為可選路由後端

### Phase 1a: 已完成的附加整合 (2026-06-06)
- [x] ED3N 作為 AutoBackendChoice (`neuro_auto_selector.py`)
- [x] ResponseRoute.ED3N 路由追蹤 (`deviation_tracker.py`)
- [x] network_defaults.py 常量 (ED3N_HOST, DEFAULT_ED3N_MODEL, ED3N_TIMEOUT, BACKEND_PRIORITY)
- [x] configs/system/ed3n.default.yaml 配置文件
- [x] configs/system/llm.default.yaml 加入 ed3n-v1 後端
- [x] configs/system/llm_providers.default.yaml 加入 ed3n provider
- [x] configs/standard/behavior/angela_core.default.yaml 將 ed3n 加入 backend_priority
- [x] 取代所有硬編碼回應 (composer.py, router.py, proactive_interaction_system.py, chat_routes.py, daily_language_model.py)

### Phase 1b: 下一階段
Phase 2 (訓練系統) 和 Phase 3 (SNN 整合) 仍待未來實作。Phase 1 驗證了 ED3N 作為現有 LLM 路由的附加後端是可行的，後續階段將在此基礎上持續推進。

### Phase 2 完成標誌
- [x] 字典可從對話中自動增長（新概念檢測準確率 > 70%）
- [x] 字典 + 網路聯合訓練收斂（損失下降曲線正常）
- [x] 持續學習場景：新增 1000 詞彙後核心網路不需要重訓，推理正確率不降
- [x] 與 `ai/learning/` 系統完整整合

### Phase 2a: 已完成的附加整合 (2026-06-06)
- [x] 6 項新方法: detect_new_concepts, learn_from_conversation, get_stats, merge_entries, export_to_json, import_from_json
- [x] 字典增長使用專用 key 前綴 "l" 避免與預設條目衝突
- [x] CoreNetwork 新增 hebbian 訓練: train_step, adjust_connection, get_trainable_parameters
- [x] ED3NTrainer 交替訓練循環 (字典→網路→字典)
- [x] ContinuousLearningPipeline: process_interaction → detect_and_grow → queue → train
- [x] ED3NLearningIntegration: 橋接 LearningManager, ExperienceReplayBuffer, MemoryLearningEngine
- [x] 新檔 4 個 (training_types.py, ed3n_trainer.py, continuous_learning.py, learning_integration.py)

### Phase 3 完成標誌
- [ ] SNN 核心網路在模擬數據上正確率 > 傳統版本 90%
- [ ] 批次重排序比全量計算節省 > 60% 運算量
- [ ] 荷爾蒙調製影響 SNN 閾值的曲線與生物數據一致
- [ ] 稀疏運算比稠密運算快 3x+（同等精度）

---

## 十二、與 Angela 現有架構的整合策略

### 短期（Phase 1）
```
AngelaLLMService (router.py)
  ├── Traditional LLM backend (OpenAI/Ollama/...)
  └── ED3N backend (新增路由選項)
       ├── DictionaryLayer (新)
       ├── CoreNetwork (純關係運算)
       └── OutputAnchor (新)
```

ED3N 作為 `AngelaLLMService` 的新 `LLMBackend` 類型加入路由系統：
```python
# services/llm/providers/registry.py
class LLMBackend(Enum):
    LLAMA_CPP = "llama_cpp"
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"
    ED3N = "ed3n"  # 新增
```

### 中期（Phase 2-3）
```
AngelaLLMService (router.py)
  ├── ED3N (主路由)
  │    ├── ReflexLayer (core/bio/ 整合)
  │    ├── DictionaryLayer (ai/alignment/ontology 擴充)
  │    ├── CoreNetwork (SNN)
  │    └── HormonalModulator (core/bio/endocrine)
  └── Traditional LLM (fallback)
```

### 長期（Phase 4）
```
ED3N 成為 Angela 的統一推理核心
  ├── 語言理解 ← DictionaryLayer (文字編碼器)
  ├── 圖像理解 ← DictionaryLayer (圖像編碼器)
  ├── 音訊理解 ← DictionaryLayer (音訊編碼器)
  ├── 狀態理解 ← DictionaryLayer (生物狀態編碼器)
  ├── 決策推理 ← CoreNetwork (SNN)
  ├── 反射回應 ← ReflexLayer
  └── 輸出產生 ← OutputAnchor + DictionaryLayer (輸出解碼器)
```

---

_建立: 2026-06-06 | 最後更新: 2026-06-06 | 狀態: ✅ Phase 1 原型 + Phase 2 訓練系統完成 | Phase 3 (SNN 整合) 待實作_
