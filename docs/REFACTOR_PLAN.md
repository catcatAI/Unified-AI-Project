# Angela AI — 架構整合與开箱即用改造計劃

> Version: 1.1 — 2026-08-12
> Status: IN PROGRESS — Phase 1-4 done, Phase 5-10 pending
> 目標：去重、配置驅動、一鍵啟動、開箱即用

---

> **執行紀錄 (2026-08-13)**：本計畫的「去重」目標已在主幹執行 — 錯誤體系統一至
> `core.angela_error`（移除 `core/error/error_handler.py`）、跨檔重複類別合併
> （error dataclasses / `TrainingExample` / `BaseAgent` 等）。詳見根 `README.md`
> §2026-08-13 Internal Consolidation。測試數已同步至 **4,499**（0 errors）。
> `ANGELA_FULL_ARCHITECTURE.md` 的已刪子系統標記已校正。`core_ai/` 舊結構已不存在，
> 相關規劃文檔已歸檔至 `docs/09-archive/planning-2026-08-13/`（原 `docs/06-project-management/planning/`，描述舊 `core_ai/` 結構）。

## 1. 現狀診斷

### 1.1 重複實作清單

| 功能 | 重複數 | 檔案 | 問題 |
|------|--------|------|------|
| **意圖分類** | 3 | query_classifier.py (795L), dictionary_classifier.py (473L), intent_model.py (280L) | 三個系統做類似的事 |
| **SNN 核心** | 3 | core_network.py (623L), snn_core.py (205L), garden/snn_core.py (738L) | SNNCore 聲稱替代 CoreNetwork 但兩者共存 |
| **知識圖譜** | 1（僅剩 kg_import.py） | unified_knowledge_graph_impl.py、knowledge_graph_agent.py 已於 Phase 11b 刪除；kg_import.py (726L) 保留 | stub + 完整實作 + agent 包裝 |
| **推理引擎** | 5 | reasoning_engines.py, causal_reasoning_engine.py, symbolic_reasoner.py, relational_chain.py, reasoning_system.py | 部分功能重疊 |
| **情緒系統** | 4 | emotion_system.py (572L), emotional_blending.py (1141L), emotion_analyzer.py (549L), user_monitor.py (408L) | PAD 模型重複 |
| **記憶系統** | 8+ | ham_manager.py, ham_core_storage.py, vector_store.py, multimodal_memory.py, perceptual_memory.py, trauma_memory.py 等 | HAM 有 4+ 獨立實例 |
| **訓練器** | 3+ | ed3n_trainer.py, training_pipeline.py, cross_modal_trainer.py | 不同領域但界面不統一 |
| **響應生成** | 5+ | composer.py, template_matcher.py, vision_response_generator.py, vector_decoder.py 等 | TemplateMatcher 與 Composer 重疊 |
| **規劃** | 3 | planning_engine.py, planning_agent.py, proactive_interaction_system.py | PlanningAgent 只是薄包裝 |
| **StateMatrix** | 2+1 stub | state_matrix.py (1664L), adapter.py (370L), autonomous/state_matrix.py (12L stub) | 有 stub |

### 1.2 架構缺失

| 缺失組件 | 影響 | 來源 |
|----------|------|------|
| **Backbone 層** | ~130 個散落的單例工廠 | ✅ 已實現（`core/backbone/backbone.py` + `hardware.py`，見 ARCHITECTURE_BACKBONE.md） |
| **統一配置切換** | 無法根據硬體自動選擇最佳實現 | 系統中沒有 |
| **一鍵安裝/訓練** | 用戶需手動下載數據、訓練、配置 | 沒有統一入口 |
| **自動硬體檢測** | 無法根據 GPU/CPU/記憶體自動調整 | 僅有 hardware_profile.py 但未被組件使用 |

---

## 2. 目標架構

### 2.1 分層設計

```
┌─────────────────────────────────────────────────────────┐
│  Layer 6: Presentation (Desktop/Web/CLI/Pixel)         │
├─────────────────────────────────────────────────────────┤
│  Layer 5: API (FastAPI/WebSocket/SSE)                  │
├─────────────────────────────────────────────────────────┤
│  Layer 4: Application (Chat/LLM/Vision/Audio)          │
├─────────────────────────────────────────────────────────┤
│  Layer 3: Backbone (統一註冊/路由/配置/開關)  ← 新建   │
├─────────────────────────────────────────────────────────┤
│  Layer 2: AI Core                                      │
│    ├── IntentEngine (統一意圖分類)                      │
│    ├── NeuralEngine (SNN/推理/學習)                     │
│    ├── KnowledgeEngine (知識圖譜/字典/記憶)             │
│    ├── EmotionEngine (情緒/狀態)                        │
│    └── PlanningEngine (規劃/步驟)                       │
├─────────────────────────────────────────────────────────┤
│  Layer 1: Foundation (硬體/數學/物理)                   │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Backbone 層核心職責

```python
# core/backbone/backbone.py
class Backbone:
    """統一註冊、路由、配置、生命週期管理"""
    
    # 註冊表（每個功能只有一個實現）
    engines: Dict[str, EngineInterface]
    config: AngelaConfig
    hardware: HardwareProfile
    
    # 統一工廠（取代 ~130 個散落工廠）
    def get_engine(name: str) -> EngineInterface
    def get_config(section: str) -> dict
    def get_memory() -> MemoryInterface  # 單例
    def get_state_matrix() -> StateMatrix  # 單例
    def get_emotion_system() -> EmotionInterface  # 單例
    
    # 自動切換
    def auto_select_backend(engine_name: str) -> str  # 根據硬體選擇
```

### 2.3 配置驅動的引擎切換

```yaml
# configs/standard/backbone.default.yaml
backbone:
  intent_engine: auto  # auto | query_classifier | dictionary_classifier
  neural_backend: auto  # auto | torch | numpy | snn_lif
  knowledge_backend: auto  # auto | symbolic | vector | hybrid
  emotion_model: auto  # auto | pad_basic | pad_blending
  memory_backend: auto  # auto | ham | vector | hybrid
  
  # 自動切換規則
  auto_select:
    torch: "gpu_memory >= 4GB"
    snn_lif: "cpu_cores >= 8"
    vector_backend: "has_chromadb"
    ham_only: "memory <= 2GB"
```

---

## 3. 去重整合計劃

### 3.1 第一階段：高優先（刪除/合併明顯的重复）

| 動作 | 檔案 | 結果 |
|------|------|------|
| **刪除** stub | `unified_knowledge_graph_impl.py` (28L) | 刪除，使用 kg_import.py |
| **刪除** 薄包裝 | `planning_agent.py` (90L) | 合併到 PlanningEngine |
| **合併** | `dictionary_classifier.py` (473L) → `query_classifier.py` | 統一看為字典路徑 |
| **刪除** stub | `autonomous/state_matrix.py` (12L) | 刪除 |
| **刪除** 重複 wrapper | `ham_query_engine.py` (43L) | 用 ham_memory/ham_query_engine.py |
| **刪除** 重複 scorer | `importance_scorer.py` (95L) | 用 ham_importance_scorer.py |
| **合併** | `template_matcher.py` (401L) → `composer.py` | Composer 已有模板邏輯 |
| **合併** | `emotion_analyzer.py` (549L) → `emotion_system.py` | 作為文本輸入路徑 |

### 3.2 第二階段：中優先（統一接口但保留實現）

| 功能 | 現有實現 | 統一接口 | 自動切換 |
|------|----------|----------|----------|
| **SNN** | CoreNetwork, SNNCore, TensorSNNCore | `NeuralInterface.forward()` | 根據硬體選最佳 |
| **推理** | symbolic, causal, chain | `ReasonInterface.reason()` | 根據查詢類型選 |
| **情緒** | EmotionSystem, EmotionalBlending | `EmotionInterface.get_state()` | 根據配置選 |
| **記憶** | HAM, VectorStore, Multimodal | `MemoryInterface.store/query()` | 統一協調器 |

### 3.3 第三階段：建立 Backbone

| 步驟 | 內容 |
|------|------|
| 1 | 創建 `core/backbone/backbone.py` — 統一註冊表 + 工廠 |
| 2 | 創建 `core/backbone/config.py` — 統一配置加載 |
| 3 | 將 ~130 個 `get_*` 工廠移到 `Backbone` |
| 4 | 實現 `auto_select_backend()` — 根據硬體自動選擇 |
| 5 | 實現單例管理 — HAM/StateMatrix/Emotion 統一實例 |

---

## 4. 一鍵啟動系統

### 4.1 總命令

```bash
python scripts/setup.py
```

這個腳本自動完成：
1. 檢測硬體（GPU/CPU/記憶體/OS）
2. 選擇最佳配置
3. 下載所需數據集
4. 訓練模型
5. 保存配置
6. 驗證安裝

### 4.2 setup.py 流程

```
1. Hardware Detection
   ├── GPU? → torch backend
   ├── RAM? → model size
   ├── Disk? → dataset selection
   └── OS? → path config

2. Dependency Installation
   ├── Base deps (always)
   ├── ML deps (if GPU or >8GB RAM)
   └── Optional deps (chromadb, redis)

3. Data Download
   ├── Dictionaries (cedict/wordnet/jmdict) — 467MB
   ├── Training data (arithmetic/logic) — 2.8MB
   ├── Knowledge graph seeds — small
   └── Multimodal (optional, 2GB+)

4. Training
   ├── ED3N reflex + dictionary (fast, ~2min)
   ├── ED3N SNN weights (medium, ~10min)
   ├── GARDEN convergence (fast, ~5min)
   └── Multimodal encoders (optional, ~30min)

5. Configuration
   ├── Generate configs/standard/backbone.local.yaml
   ├── Set backend paths
   └── Verify all engines load

6. Verification
   ├── Math: 3+5*2 = 13
   ├── Knowledge: sky color = blue
   ├── Dictionary: france = 法国
   └── All engines report healthy
```

### 4.3 硬體自適應配置

```python
# scripts/setup.py — 自動檢測
def detect_hardware():
    return {
        "gpu": detect_gpu(),           # nvidia/intel/none
        "gpu_memory": get_gpu_mem(),   # GB
        "cpu_cores": os.cpu_count(),
        "ram_gb": get_system_ram(),
        "disk_free": get_free_space(),
        "os": platform.system(),
        "has_torch": importlib.util.find_spec("torch") is not None,
        "has_chromadb": importlib.util.find_spec("chromadb") is not None,
    }

def select_config(hw):
    if hw["gpu"] and hw["gpu_memory"] >= 4:
        return "high_performance_gpu"
    elif hw["ram_gb"] >= 16:
        return "high_performance_desktop"
    elif hw["ram_gb"] >= 8:
        return "laptop_normal"
    elif hw["ram_gb"] >= 4:
        return "laptop_power_saver"
    else:
        return "low_power_device"
```

---

## 5. 訓練系統

### 5.1 統一訓練入口

> ⚠️ 計畫中的 `scripts/train.py` **不存在**（已確認全倉無此檔）。實際的統一訓練入口是 `scripts/train_pipeline.py`，但**尚未接線成一鍵流程**，也未在 `setup.py` 中自動呼叫。下載資料集（`scripts/download_datasets.py`）+ 訓練（`scripts/train_pipeline.py` 等）的能力存在，但需手動執行。

```bash
# 實際可用（手動）：
python scripts/download_datasets.py      # 下載 CC-CEDICT/JMdict/WordNet 等
python scripts/train_pipeline.py          # 統一訓練管線（確切引數請見該檔 main()）
```

### 5.2 訓練優先級

| 組件 | 數據 | 時間 | 優先級 |
|------|------|------|--------|
| ED3N reflex | presets.json | 30s | P0 |
| ED3N dictionary | cedict+wordnet | 2min | P0 |
| ED3N SNN weights | arithmetic+logic | 10min | P1 |
| GARDEN convergence | knowledge_base | 5min | P1 |
| Knowledge Graph | conceptnet/wikidata | 5min | P2 |
| Multimodal encoders | CIFAR-10+ESC-50 | 30min | P3 |

### 5.3 訓練驗證

每個組件訓練後自動驗證：
```python
def verify_training(component):
    tests = component.get_verification_tests()
    results = [t() for t in tests]
    success_rate = sum(results) / len(results)
    assert success_rate >= 0.8, f"{component} verification failed"
```

---

## 6. 配置系統

### 6.1 配置層次

```
configs/
├── system/           # 系統級（不常改）
│   ├── bootstrap/
│   ├── compute/
│   └── hardware_profile.json
├── standard/         # 標準配置（隨版本更新）
│   ├── backbone.default.yaml  ← 新增
│   ├── engine.default.yaml     ← 新增
│   └── training.default.yaml   ← 新增
├── local/            # 本地覆蓋（手動調整）
│   └── backbone.local.yaml    ← 新增
└── mods/             # MOD 擴展
    └── *.yaml
```

### 6.2 引擎配置範例

```yaml
# configs/standard/engine.default.yaml
engines:
  intent:
    backend: auto  # auto → 根據 query 類型自動選擇
    fallback: query_classifier
    
  neural:
    backend: auto  # auto → torch > numpy > snn_lif
    device: auto   # auto > cuda > cpu
    batch_size: auto  # 根據 RAM 自動
    
  knowledge:
    backend: hybrid  # symbolic + vector + dictionary
    cache_size: auto  # 根據 RAM
    
  emotion:
    model: pad_blending
    persistence: true
    
  memory:
    backend: hybrid  # ham + vector
    max_entries: auto  # 根據 RAM
```

---

## 7. 向後兼容

### 7.1 現有 API 保持不變

```python
# 舊代碼仍然工作
from ai.core.query_classifier import QueryClassifier
qc = QueryClassifier()

# 新代碼用 Backbone
from core.backbone import get_backbone
bb = get_backbone()
intent = bb.get_engine("intent")
```

### 7.2 MOD 支持

```yaml
# configs/mods/my_custom_engine.yaml
mod:
  name: "my_custom_intent"
  replaces: "intent"
  module: "mods.my_custom.intent_engine"
  class: "CustomIntentEngine"
  priority: 10  # > 0 means override default
```

---

## 8. 執行計畫

| 階段 | 任務 | 預計時間 | 完成後會是啥樣（端到端樣貌） |
|------|------|----------|--------------------------------|
| 1 | 刪除明顯的重复/stub | 2h | 程式碼減少 ~300 行、無空殼封裝 |
| 2 | 合併 DictionaryClassifier → QueryClassifier | 1h | 單一意圖分類入口，不再雙套邏輯 |
| 3 | 合併 TemplateMatcher → Composer | 1h | 單一生器，模板與組合統一 |
| 4 | 合併 EmotionAnalyzer → EmotionSystem | 1h | 單一情緒輸入來源 |
| 5 | 合併 PlanningAgent → PlanningEngine | 0.5h | 統一規劃引擎 |
| 6 | 建立 Backbone 骨架 | 4h | 共享單例工廠，模組統一取得 |
| 7 | 實現自動硬體檢測 + 配置選擇 | 2h | 依硬體自動選配置，免手動調 |
| 8 | 建立 setup.py 一鍵啟動 | 3h | 一條指令即開箱可用 |
| 9 | 建立統一訓練入口 | 2h | 一鍵訓練，入口統一 |
| 10 | 測試 + 驗證 + 文檔 | 3h | 全計畫可驗收 |
| 11 | 字典概念身分層：佔位 / 生造 / 回填 / 批配 不衝突（詳 §10–§12） | — | 詞彙可成長、回應零外漏、跨重啟不撞號 |
| 11.1 | P3 修正驗證契約（解除 C4：SNN 貢獻不再被丟棄） | 1h | SNN 生成內容不再被丟棄，`process_deep` 正常回傳 |
| 11.2 | P1 概念收斂 `resolve_concepts`（解除 C2：同概念不重複） | 2h | 同概念輸入+字典合併去重，不再重複佔位 |
| 11.3 | §10 Token Ontogenesis：`grow` 佔位標記 + grow 側去重（§10.6 呼叫點）/ `TokenComposer` / `backfill_placeholder` / 字典單例化 | 4h | 四階段管線完整、寫入即去重、佔位有標記 |
| 11.4 | P2 佔位永不外漏 + P5 key 持久化/內容定址（解除 C1/C5） | 2h | 回應無 raw key 外漏、跨重啟 key 穩定 |
| 11.5 | 補 `tests/ai/ed3n/test_dict_ontogenesis.py`（量化 §11.4 指標） | 2h | 量化指標有測試守護，避免回退 |
| 13 | 主幹線自適應派遣層：輸入依內容判定去向（學習/訓練排序/傳遞） | — | 僅 `text`+`time` 的 mod 輸入也能正常處理並回應 |
| 13.1 | D1 輸入標準化 + time 綁定（InputEnvelope；對齊 `/chat/unified`、`/session/{id}/send`） | 1h | `time` 成為可傳遞中繼資料，供學習/訓練排序 |
| 13.2 | D2 內容驅動任務分類：擴充 `QueryClassifier`/新增 `DispatchIntent`（GENERATE/LEARN/TRAIN + 信心） | 2h | 創作類輸入被判 GENERATE 而非掉 fallback |
| 13.3 | D3 派遣策略：依 (intent, 信心, 狀態) → 動作集 {LEARN, TRAIN(queue), FORWARD} | 2h | 一輸入可同時學習+生成（多動作集） |
| 13.4 | D4 訓練排序執行：接 `TrainingCoordinator` 佇列 + 優先級（排序執行，不阻塞主線） | 2h | 訓練按優先級排隊，不阻塞主線 |
| 13.5 | D5 FORWARD 保證正常輸出：接 §11 管線，創作類不塌縮 fallback | 2h | 僅 text+time 的 mod 輸入回正常生成 |

**總計: ~19.5 + 10 + 9 = ~38.5 小時**

---

## 9. 預期結果

### 改造前
```bash
# 用戶需要手動做的事：
pip install -e ".[standard]"
python scripts/import_dictionaries.py
python scripts/download_datasets.py
python scripts/train_pipeline.py
# 手動編輯 5+ 個 yaml 文件
# 手動解決依賴衝突
# 手動調整硬體配置
python -m uvicorn ... # 啟動
```

### 改造後（目前實際可達成的流程）

> ✅ `start.py` 啟動器**已實作**（`python start.py` 一鍵啟動後端 + Web Viewer）。
> ✅ `setup.py` 一鍵流程**已實作**的子集：自動檢測 + Backbone 初始化 + 知識系統初始化 + 知識圖譜 + 驗證（3 項測試）。
> ⚠️ 計畫中的「`setup.py` 自動**下載** + 自動**訓練**」仍**尚未實作**（Phase 5-10）；`setup.py` 目前僅載入已訓練模型，不會下載/訓練。
> 目前真實的一鍵流程如下：

```bash
# 1) 安裝依賴（二選一）：
python setup.py                        # 一鍵：硬體偵測 → Backbone 初始化 → 知識系統 + 知識圖譜 → 驗證（不會自動下載/訓練）
#   或：pip install -e "apps/backend"  # 套件化安裝（推薦，見 README）
# 2) 啟動（主要入口 scripts/run_angela.py；或 python start.py 一鍵啟動前後端）：
python scripts/run_angela.py              # 啟動前後端
python scripts/run_angela.py --api-only    # 只啟動後端
python scripts/run_angela.py --health-check
# 完成！Angela 已可用（後端依偵測到的硬體自動配置；訓練為選用，見 docs/usage/SCENARIOS.md）
```

> 終極目標中的「自動檢測 + 配置 + 驗證 → 一鍵啟動」**已在 caaf9f8e 實作**（`setup.py` + `start.py`）；僅「自動下載 + 自動訓練」仍屬 Phase 5-10 規劃，**尚未實作**。

### 代碼改善

> 下列為計畫目標值（設計對照），非全部已落地：其中「啟動步驟→1 命令」「硬體適配→自動」已由 `scripts/run_angela.py` + `hardware_profile.py` 實現；`start.py` 亦提供一鍵啟動；「`setup.py` 自動下載/訓練」尚未實作（見上方 ⚠️）。

| 指標 | 改造前 | 改造後 |
|------|--------|--------|
| 重複程式碼 | ~5000 行 | ~0 行 |
| 散落工廠 | ~130 個 | 1 個 Backbone |
| 配置檔案 | 50+ 個分散 | 統一 3 層 |
| 啟動步驟 | 10+ 手動 | 1 個命令 |
| 硬體適配 | 手動 | 自動 |
| MOD 支持 | 無 | 宣告式 |

---

## 10. 智能上限提升：Token 佔位 / 生造 / 回填 管線（Token Ontogenesis）

> 研究日期：2026-08-12
> 目的：把「SNN 算出語意 → 先佔字典槽位 → 以語意組合/拼接/生造 token → 學到具體字形後回填 → 解決新增與佔位的衝突」這條管線的研究結果整合進重構計畫，作為「開箱即用」之外的**智能成長上限**主軸。

### 10.1 現狀研究（既有實作，已核對原始碼）

專案中已存在「佔位 token」的核心雛形，但不是使用者描述的那條完整四階段管線：

1. **槽位分配**：`DictionaryLayer._assign_key(prefix)` — `apps/backend/src/ai/ed3n/dictionary_layer.py:72`
   - 以 `f"{prefix}{self._next_key_id}"` 形式分配（預設 `c`，`grow` 用 `l`），並以 `while ... in self.entries` 遞增避免當次會話碰撞。
   - `_next_key_id` 初值為 `1`（`dictionary_layer.py:58`），**未持久化**。
2. **語意 → 槽位**：`DictionaryLayer.grow(text, surface_form, confidence)` — `dictionary_layer.py:340`
   - 直接建立 `DictionaryEntry(key, surface_forms={"zh": surface_form, "en": text}, confidence)`，即**建立當下就要求有 surface_form**，不存在「先佔位、後回填」的區隔。
   - 呼叫點：`ai/response/learning_loop.py:139`、`ai/document/learner.py:90`、`ai/ed3n/ed3n_trainer.py:128`、`ai/ed3n/continuous_learning.py:163`、`ai/garden/garden_engine.py:1163` 與 `:1280`、`dictionary_layer.py:586`（learn_new_concepts）。
3. **解碼兜底（外漏來源）**：`anchored_decode` / `decode` — `apps/backend/src/ai/ed3n/output_anchor.py:102`、`dictionary_layer.py:280`
   - `surface = zh or en or key`：若某 key 沒有 surface_forms，會直接把原始 key（如 `l42`）當作 token 輸出 → **佔位未回填時的 token 外漏**。
4. **去重合併（僅手動）**：`DictionaryLayer.merge_entries()` — `dictionary_layer.py:598`
   - 可把 source 合併進 target，但**沒有自動把「佔位」連結到「後來學到的真詞」的邏輯**，需外部顯式呼叫。

**結論**：現有機制具備「語意/文字 → 字典槽位」與「手動合併」，但使用者構想中的**佔位 → 生造 → 回填 → 衝突解決**四階段並不完整，屬於「部分實作」。

### 10.2 設計：四階段管線（對應使用者構想）

| 階段 | 目標 | 現狀 | 需新增 |
|------|------|------|--------|
| **① 佔位 (Placeholder)** | SNN/encoding 算出語意 → 立即佔用字典槽位，surface_forms 留空並標記 `is_placeholder=True` | `grow` 強制要有 surface_form | 支援 `grow(text, surface_forms={}, placeholder=True)` |
| **② 生造 (Compose/Splice)** | 根據語意嘗試組合、拼接已知語素/字形來「生造」一個近似 token | 無（decode 只拼接既有 surface） | 新增 `TokenComposer`/`OntogenyEngine`：以語意向量檢索相近詞根 → 拼接/變形生成候選字形 |
| **③ 回填 (Backfill)** | 學到具體字形/真詞 → 填入佔位 token 的 surface_forms，清除 `is_placeholder` | 僅 `merge_entries` 手動 | `backfill_placeholder(key, real_surface)`：回填 + 建立 `mapping`/`synonym` 關聯 |
| **④ 衝突解決 (Resolve)** | 檢查「新學到的真詞」與「既有佔位」是否衝突並解決 | `add_entry` 僅 `logger.warning` 覆寫（`:307`） | `resolve_placeholder_conflict()`：偵測同名/同義 → 自動回填或合併，避免重複概念與資料遺失 |

### 10.3 衝突分析（既有修復是否完美 → 結論：不完美）

逐一核對使用者特別關心的「新增與佔位的衝突」：

1. **`add_entry` 靜默覆寫**（`dictionary_layer.py:306-307`）：key 已存在只 `logger.warning("Overwriting existing entry...")` 後直接覆寫 → **既有的「修復」只是警告，資料仍會遺失**，不完美。
2. **`_next_key_id` 未持久化**（`export_to_json` 只存 `entries`/`growth_history`，`dictionary_layer.py:627-644`）：重新載入後 `_next_key_id` 重置為 `1`。當次會話靠 `while ... in self.entries` 避開，但**跨部分載入 / 不同 prefix 重疊時脆弱**，且無法保證全局唯一。
3. **無純佔位建立**：`grow` 要求 `surface_form`，所以無法產生「語意已知、字形未知」的純佔位；decode 退化為輸出原始 key（外漏）。
4. **無佔位↔真詞自動連結**：`grow` 與 `add_entry` 各自檢查，但沒有把「後來學到的真詞」自動回填到「先前佔位」的機制；結果是同一概念可能同時存在「佔位 `l42`（外漏）」與「真詞新 key」→ 重複概念。
5. **camelCase / 概念編碼**（`continuous_learning.py:163` 等以 `l` prefix grow）與 `grow` 共用 `l` prefix，若未來有手動 key 採同 prefix+數字，會落入 `_assign_key` 的碰撞檢查邊界。

**小結**：既有修復屬「部分防護」，並未實現使用者構想中的四階段自洽迴圈；衝突點主要在第 ①/③/④ 與 `_next_key_id` 持久化。

### 10.4 實作建議（可併入 REFACTOR 階段 6–10 / Backbone）

- **`DictionaryEntry` 擴充**：增加 `is_placeholder: bool = False` 與 `placeholder_for: Optional[str]` 欄位（`dictionary_layer.py:28` 的 `__slots__`）。
- **`grow()` 支援純佔位**：`surface_forms` 可為 `{}`，`placeholder=True` 時建立標記佔位；decode 對 `is_placeholder` 不輸出原始 key，改輸出「語意暫譯」或空（避免外漏）。
- **`TokenComposer` / `OntogenyEngine`**（建議落在 `ai/ed3n/` 或 Backbone 的 `ai` 層）：
  - 輸入：語意向量 / encode 結果。
  - 檢索相近詞根 → 依構詞規則拼接/變形（中文偏語素組合，英文偏詞綴拼接）生成候選字形。
  - 輸出候選 token 供 ③ 回填或供 LLM/使用者確認。
- **`backfill_placeholder(key, real_surface)`**：回填 surface_forms、清 `is_placeholder`、建立 `mapping`/`synonym` 關聯（可複用 `merge_entries` 的關聯邏輯）。
- **`resolve_placeholder_conflict()`**：
  - 新詞入庫前，先以 `encode_soft` + 語意相似度比對現有 `is_placeholder` 條目；
  - 命中 → 直接回填該佔位（而非新建 key）；
  - 未命中但有同義 → 走 `merge_entries`；
  - 替換 `add_entry` 的「警告後覆寫」為「衝突解決後寫入」。
- **持久化 `_next_key_id`**：`export_to_json` / `import_from_json` 增加 `_next_key_id` 欄位；或在載入後以 `max(現有數字 key)` +1 重新計算，確保跨重啟唯一。

### 10.5 預期效益

- **智能上限提升**：未知概念在 SNN 算出語意當下即獲**穩定、不外露的槽位**；先以語意組合「生造」近似字形維持表達力，待真詞學到再**回填**；全程自動偵測並解決新增/佔位衝突 → 詞彙可持續成長、零 token 外漏、概念不自動重複。
- **與現有架構相容**：沿用 `DictionaryLayer` / `output_anchor` / `continuous_learning` 的既有介面，建議掛在 Backbone 的統一字典/知識引擎之下（見第 3 節 `KnowledgeEngine`），不破壞現有 API。
- **誠實備註**：此為「上限提升」設計，非當前可驗證指標；需在 ② 生造品質與 ④ 衝突召回率上以測試量化（建議補 `tests/ai/ed3n/test_dict_ontogenesis.py`）。

### 10.6 學習期寫入側範圍：grow 呼叫點清單與去重缺口（實證補充）

> 2026-08-12 經 `grep "\.grow("` 全專案掃描確認：衝突不只在解碼期（§11），**寫入期就是源頭**。

- 全專案 `grow()` 呼叫點（7 處）：
  - `ai/response/learning_loop.py:139`
  - `ai/document/learner.py:90` → `grow(token, token)`（**garden 字典**）
  - `ai/ed3n/ed3n_trainer.py:128`
  - `ai/ed3n/dictionary_layer.py:586`（經 `learn_from_conversation` → `detect_new_concepts`，已有 **surface 字串級**去重）
  - `ai/ed3n/continuous_learning.py:163` → `grow(text, token)`（僅 per-call `token in known_surfaces` 檢查）
  - `ai/garden/garden_engine.py:1163`、`:1280` → `grow(token, token)`（**garden 字典**）
- 關鍵缺口：
  1. **`grow()` 本身無概念級去重**（`dictionary_layer.py:340-371`）：永遠 `_assign_key` 新 key，不檢查同概念是否已存在。除 `learn_from_conversation`（走 `detect_new_concepts` 的 surface 字串去重）外，其餘呼叫點直接呼叫 `grow`，同一概念跨文字/跨呼叫者會產生多個 `l##` 條目 → 正是「新增與佔位衝突」的**寫入側源頭**。
  2. **`grow(text, token)` / `grow(token, token)` 把原始 token 當作 surface** → 即使用者描述的「佔位」：語意算出後先佔槽、以原始 token 充當 surface，待日後回填真詞。故這些條目建檔時即應標 `is_placeholder=True`。
  3. **字典非單例**：garden（`self.garden.dictionary`）與 ed3n（`self.dictionary`）各有獨立 `DictionaryLayer` 實例，跨實例無法去重/回填；與 §3 Backbone 統一 `KnowledgeEngine` 目標衝突，須先收斂為共享實例。
- **修正歸屬**：§10.4 的 `resolve_placeholder_conflict()` / `backfill_placeholder()` 必須**掛進 `grow()` 與 `add_entry()` 本身**（寫入即去重 + 標佔位），而非只於解碼期（§11 P1）處理；否則多呼叫點會持續產生重複佔位。納入 §8 Phase 11.3 執行（含 grow 側去重 + 佔位標記 + 字典單例化）。

---

## 11. 管線衝突根治：輸入 → 字典 → SNN → 輸入+字典 → 輸出

> 研究日期：2026-08-12
> 目的：使用者指出既有管線 `輸入 > 字典 > SNN > 輸入+字典 > 輸出`「又衝突了」。本節對照原始碼精確定位衝突點，並給出**完美解決方案**（統一概念身分層 + 修正驗證契約），與 §10 的 Token 佔位/回填互補。

### 11.1 流程現況（對照原始碼，已核對）

| 階段 | 使用者稱呼 | 實際程式碼 | 位置 |
|------|-----------|-----------|------|
| ① 輸入 | 輸入 | `process()` / `process_deep()` 接收 `input_text` | `ed3n_engine.py:247`、`:790` |
| ② 字典（編碼） | 字典 | `dictionary.encode(input_text)` → `keys` | `_stage_encode` `ed3n_engine.py:614`；`dictionary_layer.py:104`、`:234` |
| ③ SNN（語意） | SNN | `network.forward(keys)` / `snn_network.forward(keys)` → `network_output` | `_stage_network_forward` `ed3n_engine.py:705`；`_snn_process` `:358` |
| ④ 輸入+字典（合併解碼） | 輸入+字典 | `anchored_decode(network_output, original_input_keys=keys, enriched)` 把**輸入 keys** 與 **SNN 激發的 dict keys** 合併 | `_stage_anchored_decode` `ed3n_engine.py:711`；`output_anchor.py:17` |
| ⑤ 輸出 | 輸出 | `response` → `validator.validate(...)` → 回傳 | `_stage_validate` `ed3n_engine.py:717`；`process_deep:813` |

**④「輸入+字典」合併的內部建池邏輯**（`output_anchor.py:29-72`）：
- `anchor_pool` 由三類 key 組成：
  1. `original_input_keys`（輸入錨，`output_anchor.py:32`）
  2. `enriched.text_variants` 重新 `encode` 出的 variant keys（`output_anchor.py:44-62`）
  3. `network_output`（SNN 激發的 dict keys，`output_anchor.py:64-72`）
- 解碼兜底：`surface = zh or en or key`（`output_anchor.py:100-102`）——**無 surface 時直接輸出原始 key**。

### 11.2 衝突點精確定位

**C4（核心衝突 · 結構性塌縮）— 驗證契約與解碼來源不一致**
- `process_deep` 呼叫 `self.validator.validate(response, anchored_keys=keys)`（`ed3n_engine.py:813`），**未傳 `response_keys`**（預設 `None`）。
- `ResponseAnchorValidator.measure_drift(anchored_keys, response_keys=None)` 在 `response_keys is None` 時直接 `return 1.0`（`output_anchor.py:167`）。
- `validate` 判定 `drift(=1.0) > max_drift(0.5)` → **永遠回傳 False**（`output_anchor.py:151-158`）。
- 結果：`process_deep` 永遠走 fallback `dictionary.decode(keys)`（`ed3n_engine.py:814`）——**SNN 的語意貢獻被系統性丟棄**，④「輸入+字典」塌縮回純「輸入」。這正是使用者說的「又衝突了」：SNN 算出來的東西在 輸出 關卡被擋掉。
- `process` 自動路徑（`_process_unlocked`）在 `depth=="auto"` 且無 context 時只走 `_stage_shallow_decode`（`:466-480`），根本不經過 SNN 深解碼，同樣繞過了 ③。

**C1（佔位 token 外漏）— §10 的延伸**
- SNN 激發的 key 可能是 `grow()` 產生的佔位 `l42`（無 surface_forms），`anchored_decode` 兜底輸出 `l42` 原始 key（`output_anchor.py:102`）→ 回應出現機器碼。

**C2（新增與佔位的衝突 · 同概念雙 key）**
- 輸入編碼出真詞 key `K`（有 surface），SNN 同時激發同概念的佔位 `l42`。兩者都進 `anchor_pool`；去重只在 `output_anchor.py:103` 的 `seen_surfaces` 按「surface 字串」做——佔位無 surface → 原 key 穿過 → 輸出同概念出現「真詞 + 原始 key」矛盾。

**C3（variant key 爆炸）**
- `enriched.text_variants` 再次 `encode` 塞入額外 keys（`output_anchor.py:44-62`），可能也是佔位或與輸入 key 撞 → 放大 C1/C2。

**C5（key 跨重啟碰撞）**
- `_next_key_id` 初值 `1` 且不持久化（`dictionary_layer.py:58`、`:627` `export_to_json` 只存 `entries`）；重啟後 `_assign_key` 重新從 `l1` 計，兩個 session 可能把不同概念都分配到 `l42` → `anchor_pool` 取到錯 entry，無法靠 §10 的衝突邏輯還原。

### 11.3 完美解決方案（Concept Identity Layer + 修正驗證契約）

原則：**字典同時是編碼表與解碼表，但「key」與「概念」不是一對一**。在 ④ 之前插入「概念身分解析層」，把 輸入/SNN/variant 三類 key 先收斂成「概念集合」再解碼；同時修正 ⑤ 的驗證契約。

1. **P1 · 概念收斂 `resolve_concepts(keys) -> canonical_keys`（插入 `anchored_decode` 建池後、解碼前，`output_anchor.py:73` 之前）**
   - 以 `mapping`/`synonym`/`same-encode` 關係把多 key 折疊成**同一概念的一個 canonical key**（取有 surface 者；皆無 surface 取 confidence 最高者）。
   - 直接解決 C2：輸入真詞 `K` 與 SNN 佔位 `l42` 若同概念 → 折疊為 `K`，`l42` 不再單獨進池。
   - 由 §10.4 的 `resolve_placeholder_conflict()` 提供概念對齊能力，二者共用。

2. **P2 · 佔位永不外漏（解碼兜底改造，`output_anchor.py:100-106`）**
   - `if entry.is_placeholder:` 不輸出 `key`，改輸出其鄰接（relations）中最接近的 surface 做「語意暫譯」，或略過；絕不出現 `l42`。解決 C1。

3. **P3 · 修正驗證契約（核心修復，`ed3n_engine.py:813` 與 `output_anchor.py:162-191`）**
   - `process_deep` 改傳 `response_keys=resolved_concept_keys`（即 P1 輸出），並把 `anchored_keys` 改為 `resolved_concept_keys`（而非原始 `keys`）。
   - `measure_drift` 改測「輸入概念」與「輸出概念」的**語意連通性**（經 relations 擴散，已現成於 `output_anchor.py:175-185` 的 synonym/mapping 擴散），而非原始 key 重疊。
   - 效果：SNN 合法新增的概念（在 resolved 集合內）drift 低 → 通過驗證；佔位外漏（P2 已擋）→ 不存在。SNN 貢獻不再被丟棄，④「輸入+字典」真正生效。解決 C4（根因）。

4. **P4 · variant key 計入同一概念解析（C3）**
   - `enriched.text_variants` 產生的 keys 在 P1 與輸入/SNN keys 一起折疊，避免重複；`top_k_anchors`/`top_k_network` 改在 resolved 集合上取，而非原始池。

5. **P5 · 確定性且持久的 key 分配（C5）**
   - 持久化 `_next_key_id`（`export_to_json`/`import_from_json` 增欄，或載入後以 `max(現有數字 key)+1` 重算）。
   - 長期改用 **內容定址 key**（canonical surface 的穩定雜湊）或 `namespace`（真詞 `w:...` / 佔位 `ph:...` 分開），使同一概念跨重啟必得同一 key，根除跨 session 碰撞。

6. **P6 · 學習期回填與解碼期解析雙向閉環（與 §10 銜接）**
   - 學習期（`grow`/`continuous_learning`）產生佔位時即建立 `is_placeholder` 與 `placeholder_for` 指標（§10.4）。
   - 解碼期 P1/P3 發現同概念有「真詞 + 佔位」時，除折疊外，觸發 §10.4 的 `backfill_placeholder()` 把 surface 回填進佔位，使下一次 ② 編碼直接命中真詞，形成「佔位→生造→回填→去佔位」閉環。

### 11.4 驗收指標（量化，避免空泛）

| 指標 | 現況（推論） | 目標（P1–P6 後） |
|------|------------|----------------|
| `process_deep` 中 SNN 輸出被 fallback 覆寫比率 | ≈100%（C4 恆 False） | 0%（P3） |
| 回應含原始 `l##` key 比率 | >0（C1） | 0%（P2） |
| 同概念重複 surface 出現率 | >0（C2） | 0%（P1） |
| 跨重啟同概念 key 穩定率 | <100%（C5） | 100%（P5） |
| 對「輸入未含但語意相關」的正確回答率 | 0（SNN 被丟） | >0（P3 修復後） |

### 11.5 與 §10 的關係

- §10 = **學習期**的「佔位產生 / 生造 / 回填」管線（字典寫入側）。
- §11 = **推論期**的「輸入+字典→輸出」衝突根治（字典讀出側）。
- 兩者經由 `is_placeholder` / `resolve_placeholder_conflict()` / `backfill_placeholder()` 共用同一概念身分契約，構成「寫入佔位、讀出收斂、學到回填」的完整智能成長迴圈。
- 實作建議掛在 Backbone 的統一字典/知識引擎（`KnowledgeEngine`，見第 3 節）之下，不破壞現有 API；先落地 P3（驗證契約）與 P1（概念收斂）即可解除最致命的 C4/C2，其餘 P2/P4/P5/P6 為增強。

---

## 12. 實證驗證（2026-08-12，作為 §8 Phase 11 的依據）

> 目的：以獨立腳本直接對 `DictionaryLayer` / `anchored_decode` / `ResponseAnchorValidator` 跑最小重現，確認 §10/§11 描述的衝突**真實存在**，而非推測；驗證通過後，§10/§11 才正式納入 §8 執行計畫的 Phase 11（不再是補充章節）。

### 12.1 驗證方法

- 環境：Python 3.12.3，`apps/backend/src` 加入 `sys.path`，不啟動服務、不載入 torch。
- 腳本：`/tmp/verify_dict.py`（獨立於倉庫，不污染專案）。
- 對象：`ai.ed3n.dictionary_layer.DictionaryLayer`、`ai.ed3n.output_anchor.anchored_decode` / `ResponseAnchorValidator`。

### 12.2 驗證結果（逐項重現）

| 編號 | 聲稱的衝突 | 重現操作 | 實際輸出 | 結論 |
|------|-----------|---------|---------|------|
| C1 | 佔位無 surface → 解碼外漏原始 key | `add_entry("l42", surface_forms={})` → `decode(["l42"])` / `anchored_decode({"l42":1.0},["l42"],dl)` | `'l42'` / `'l42'` | ✅ 重現 |
| C4（根因） | 驗證契約：未傳 `response_keys` → `measure_drift` 恆 1.0 → `validate` 恆 False | `ResponseAnchorValidator.measure_drift(["l42"], None)` | `1.0`（→ validate 永遠 False → `process_deep` 走 fallback） | ✅ 重現 |
| C5 | `_next_key_id` 不持久化 | `export_to_json` 後檢查 top keys | `['version','exported_at','entries','growth_history']`，**無 `_next_key_id`** | ✅ 重現 |
| 衝突 | `add_entry` 重複 key 僅警告後靜默覆寫 | 二次 `add_entry("l42", {"en":"dog"})` | 印 `Overwriting existing entry with key=l42`，條目變 `{'en':'dog'}` | ✅ 重現 |
| — | 對照：正常 `grow` 可用 | `grow("cat","貓",0.6)` | key=`l1`，surface=`{'zh':'貓','en':'cat'}` | ✅ 正常 |

### 12.3 結論

四項衝突（C1 外漏、C4 驗證塌縮、C5 key 不持久、add_entry 靜默覆寫）**均經實證重現**；`grow` 基礎功能正常。因此 §10（學習期佔位/生造/回填）+ §11（推論期 輸入+字典 衝突根治）不是假想問題，而對應可重現的缺陷，正式列為 **§8 Phase 11** 的執行內容，並以 §11.4 的量化指標（SNN 輸出被覆寫率、raw key 外漏率、跨重啟 key 穩定率）作為完成驗收標準。

### 12.4 下一步

按 §8 Phase 11.1→11.5 順序落地；每步以 `tests/ai/ed3n/test_dict_ontogenesis.py` 鎖定對應指標，避免回退。

---

## 13. 主幹線自適應派遣層（輸入依內容判定去向）

> 來源：2026-08-12 用戶需求——主幹線應「依據實際內容」自適應判定輸入去向：**學習 / 訓練(排序執行) / 傳遞**，使僅給 `text`+`time` 的 mod 輸入也能被適當處理並回傳正常輸出。本節為設計章（執行項見 §8 Phase 13 / §13.6）。

### 13.1 現狀與缺口（實證）

- 輸入入口已支援 `text`：`chat_routes.py:1763 unified_chat` 與 `chat_routes.py:1750 send_message` 皆 `request.get("message", request.get("text", ""))`。但 **`time` 欄位被完全忽略**（`_run_chat_pipeline` 不讀 `time`）。
- 核心管線 `chat_routes.py:1410 _run_chat_pipeline` 固定流程：驗證→數學→情境→情緒/危機→執行閘→代理路由（`_try_agent_routing` `chat_routes.py:771`）→LLM。流程**假設輸入都是「要產生回應的對話」**，沒有「這是訓練資料 / 學習信號」的分支。
- 分類器 `query_classifier.py:25 QueryType` 已有 `CREATIVE/KNOWLEDGE/...`，且在 `chat_routes.py:686` 與 `router.py:1235` 被呼叫——但**只拿來選模型/選代理**，不決定「要不要學習 / 要不要訓練 / 要不要只轉發」。
- `ExecutionGate`（`execution_gate.py`）處理「可否執行動作（工具）」，不涵蓋 learn/train。
- `TrainingCoordinator`（`training_coordinator.py:45`）已具 `asyncio.Lock` + `record_training`/`should_skip`/`assign_domain` + 記憶體上限，是「排序執行」的良好基座，但**尚無優先級排隊**，也未被主幹線在 ingest 時呼叫。

**結論**：組件都在，但缺一個 **ingest-time 的統一派遣決策點**——輸入一進來先依內容判 `GENERATE/LEARN/TRAIN` 並決定動作集，而非直接灌進「產生回應」單一路徑。

### 13.2 使用者範例（驅動需求）

某 mod 只傳：

```text
text: [("你作為例中的用戶來編寫，寫一段故事")]
time: ["xx/xx,xx:xx"]
```

期望：主幹線判斷這是**創作生成**（非問答/工具），走 FORWARD→生成管線，回傳正常故事；同時 `time` 可作為學習/訓練排序的時間序依據。若無法依內容判斷，就會掉進 fallback（"抱歉我沒理解"）或被迫走錯路徑。

### 13.3 設計：MainLineDispatcher（主幹線派遣層）

新增 `services/mainline_dispatcher.py`：

- `InputEnvelope`：`{text, time, origin, metadata, raw}`，標準化所有入口（`unified_chat` / `send_message` / 未來 mod 介面）。
- `DispatchIntent`：`GENERATE` / `LEARN` / `TRAIN`。
- `classify_dispatch(text) -> DispatchDecision(intent, confidence, sub_type)`：
  - 複用並擴充 `QueryClassifier`（creative/knowledge/opinion → `GENERATE`；command/execute/file → 仍走 `ExecutionGate` 動作）；
  - 新增啟發式：含「學習/訓練/請記住/請學」等詞或結構化批次 → `LEARN`/`TRAIN`；
  - 低信心或混合 → 多動作（如 `GENERATE`+`LEARN`）。
- `dispatch(envelope) -> List[Action]`：
  - `FORWARD` → 呼叫 `_run_chat_pipeline`（生成回應）；**接 §11 管線**，確保創作類不塌縮 fallback（P3 已解 C4 根因）。
  - `LEARN` → 寫入連續學習 / HAM 記憶（帶 `time` 時間序）。
  - `TRAIN` → `TrainingCoordinator.enqueue(domain, sample, priority=...)`（排序執行，不阻塞主線）。

整合點：`_run_chat_pipeline` 開頭建 `InputEnvelope` 並 `dispatch`；`GENERATE` 續行既有流程，`LEARN`/`TRAIN` 附加於回應之前/之後非阻塞執行。

### 13.4 排序執行（D4）

`TrainingCoordinator` 增加優先級佇列（`heapq` 或有序插入），`enqueue(domain, sample, priority)` 依 priority 排序；主幹線呼叫非阻塞（`asyncio.create_task`）。與 §X #111 的 async + 記憶體上限相容。

### 13.5 與 §10/§11 的銜接

- FORWARD 路徑即 §11 的「輸入→字典→SNN→輸出」推論鏈；§10 的概念身分層提供 `LEARN`/`TRAIN` 的去重與回填依據（同一概念不重複佔位）。
- 依賴：§13 的 FORWARD 正常輸出**依賴 §11 完成**（尤其 P3 已落地；P1/P2 提升去重與零外漏）。故執行順序：**先完成 Phase 11，再 Phase 13**。

### 13.6 執行項（D1–D5，對應 §8 Phase 13）

| 項 | 任務 | 依賴 |
|----|------|------|
| D1 | 輸入標準化 + time 綁定（InputEnvelope；text/time 對齊入口） | — |
| D2 | 內容驅動任務分類：擴充 QueryClassifier / 新增 DispatchIntent（GENERATE/LEARN/TRAIN） | — |
| D3 | 派遣策略：依 (intent, 信心, 狀態) → 動作集 {LEARN, TRAIN(queue), FORWARD} | D1,D2 |
| D4 | 訓練排序執行：TrainingCoordinator 優先級佇列（排序執行） | D3 |
| D5 | FORWARD 保證正常輸出：接 §11 管線，創作類不塌縮 | §11 完成 |

### 13.7 驗收指標（可測）

- 給 `text=["你作為例中的用戶來編寫，寫一段故事"]`+`time`，`classify_dispatch` 判為 `GENERATE`/`CREATIVE`，且 `dispatch` 產生 `FORWARD`（不 fallback）。
- `time` 欄位被 `InputEnvelope` 綁定且傳遞至 LEARN/TRAIN。
- 訓練請求依 priority 排序執行（單元測試驗證排序）。
- 混合輸入（生成+學習）產生多動作集。

### 13.8 下一步

與 Phase 11 銜接：先以 `tests/ai/ed3n/test_dict_ontogenesis.py` 鎖定 §11，再於 `tests/` 新增 `test_mainline_dispatch.py` 鎖定 §13。
