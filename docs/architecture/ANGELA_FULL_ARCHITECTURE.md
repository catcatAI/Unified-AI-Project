# Angela 完整架構圖：感知・認知・執行

> **Last Updated**: 2026-06-15
> **基於**: 12 個代理完整代碼審計 + 管線接線驗證
> **目的**: 完整描述 Angela 如何視、聽、觸、說、畫、移、思考、感受、自主

---

## 目錄

- [一、感知系統（輸入）](#一感知系統輸入)
  - [1.1 視覺 — VisionService](#11-視覺--visionservice)
  - [1.2 聽覺 — AudioService + RealEdgeTTS](#12-聽覺--audioservice--reaedgettts)
  - [1.3 觸覺 — TactileService](#13-觸覺--tactileservice)
  - [1.4 文字 — WebSocket → Session History](#14-文字--websocket--session-history)
- [二、認知系統（思考）](#二認知系統思考)
  - [2.1 狀態矩陣 — StateMatrix4D (7D)](#21-狀態矩陣--statematrix4d-7d)
  - [2.2 理論公式 — 5 大數學模型](#22-理論公式--5-大數學模型)
  - [2.3 自主生命週期 — 6 個模組](#23-自主生命週期--6-個模組)
  - [2.4 路由器 — ThetaRouter](#24-路由器--thetarouter)
- [三、情感系統（感受）](#三情感系統感受)
  - [3.1 生物模擬 — BiologicalIntegrator](#31-生物模擬--biologicalintegrator)
  - [3.2 文字情緒 — EmotionAnalyzer](#32-文字情緒--emotionanalyzer)
  - [3.3 用戶監控 — UserMonitor](#33-用戶監控--usermonitor)
- [四、執行系統（輸出）](#四執行系統輸出)
  - [4.1 語音 — RealEdgeTTS](#41-語音--reaedgettts)
  - [4.2 Live2D 表情 — Live2DIntegration](#42-live2d-表情--live2dintegration)
  - [4.3 桌面操作 — DesktopInteraction](#43-桌面操作--desktopinteraction)
  - [4.4 繪圖 — ImageGenerationAgent](#44-繪圖--imagegenerationagent)
- [五、記憶系統](#五記憶系統)
  - [5.1 三層架構（權威定義）](#51-三層架構權威定義)
  - [5.2 AttractorField — 梯度導航](#52-attractorfield--梯度導航)
  - [5.3 HAMMemoryManager — 最小 JSON 存儲](#53-hammemorymanager--最小-json-存儲)
  - [5.4 LogicUnit — 邏輯/規則記憶](#54-logicunit--邏輯規則記憶)
  - [5.5 UnifiedMemoryCoordinator — 統一協調器](#55-unifiedmemorycoordinator--統一協調器)
  - [5.6 記憶層級設計（文檔描述）](#56-記憶層級設計文檔描述)
  - [5.7 ED3N — 反射與字典](#57-ed3n--反射與字典)
- [六、完整管線流程](#六完整管線流程)
- [七、系統成熟度總覽](#七系統成熟度總覽)

---

## 一、感知系統（輸入）

### 1.1 視覺 — VisionService

**檔案**: `services/vision_service.py` (706 行)
**狀態**: 架構完整，分析方法大部分為模擬

```
使用者上傳圖片
    │
    ▼
VisionService.analyze_image()
    │
    ├─→ VisualSampler (1000 粒子雲)
    │     └─ 4 種分佈: UNIFORM / GAUSSIAN / PARTICLE_CLOUD / GRID
    │     └─ 每個粒子有 x, y, intensity（指數衰減模擬中央/周邊視覺）
    │
    ├─→ PerceptualMemory (物體追蹤)
    │     └─ 歐氏距離匹配 (閾值 0.05)
    │     └─ LRU 淘汰 (容量 1000)
    │
    ├─→ AttentionController (注視控制)
    │     └─ 4 種模式: EXPLORE / FOCUS / TRACK / IDLE
    │
    └─→ 分析管線:
          ├─ OCR: OSBridgeAdapter (真實)
          ├─ 物體偵測: 模擬 (回傳隨機物件)
          ├─ 人臉偵測: 模擬
          ├─ 場景分析: 模擬
          ├─ 情緒偵測: 模擬
          └─ 顏色分析: 模擬
```

**關鍵方法**:
- `perceive_and_focus()` (line 316): 偵測→儲存→決定→注視→注入桌面
- `process()` (line 665): 統一入口，分派到各分析方法

### 1.2 聽覺 — AudioService + RealEdgeTTS

**AudioService** (`services/audio_service.py`, 41 行): **純 stub**
- `speech_to_text()`: 回傳硬編碼 `"transcribed text"`
- `text_to_speech()`: 回傳硬編碼 `b"audio data"`

**RealEdgeTTS** (`core/art/real_edge_tts.py`, 268 行): **真實 TTS**
- 使用 Microsoft Edge TTS (免費高品質)
- 支援: AriaNeural, XiaoxiaoNeural, NanamiNeural 等
- 情緒調制: happy → +10% 語速, sad → -5% 語速

**AudioSystem** (`core/engine/audio_system.py`, 630 行): **架構完整，音訊輸出模擬**
- `speak()`: 狀態機 + 字幕生成，但音訊輸出為 `asyncio.sleep()`
- `sing()`: 歌詞同步循環

### 1.3 觸覺 — TactileService

**檔案**: `services/tactile_service.py` (66 行)
**狀態**: Stub，唯一真實邏輯在 `simulate_touch()`

```
simulate_touch(object_id, contact_point, origin)
    │
    ├─ pressure > 0.8 → reflex = "withdrawal" (縮手反射)
    └─ pressure ≤ 0.8 → reflex = "normal"
    │
    └─ 回傳: intensity (pressure × 1.2), texture ("smooth"), temperature (36.5°C)
```

### 1.4 文字 — WebSocket → Session History

**檔案**: `services/websocket_manager.py` + `api/routes/chat_routes.py`

```
使用者輸入文字
    │
    ▼
WebSocket (/ws)
    │
    ├─→ 握手驗證 (HMAC)
    ├─→ _handle_chat_message()
    │     ├─ 取得 _session_history[session_id] (最多 30 則)
    │     └─ 呼叫 _handle_chat_request()
    │
    ▼
_handle_chat_request()
    ├─→ EmotionAnalyzer.analyze_emotion() → 情緒分析
    ├─→ BiologicalIntegrator → 生物刺激 (fire-and-forget)
    ├─→ StateMatrix4D → 取得 7D 狀態
    ├─→ ED3N dictionary.encode() → 歷史相關性
    └─→ context = {user_name, emotion, bio_state, state_for_llm, retrieved_context}
```

---

## 二、認知系統（思考）

### 2.1 狀態矩陣 — StateMatrix4D (7D)

**檔案**: `core/engine/state_matrix.py` (1439 行)
**狀態**: ✅ 完整真實實現

| 維度 | 希臘文 | 名稱 | 內部值 |
|------|--------|------|--------|
| α | alpha | 生理 | energy, comfort, arousal, rest_need |
| β | beta | 認知 | curiosity, focus, confusion, learning |
| γ | gamma | 情感 | happiness, sadness, anger, fear, disgust, surprise, trust, anticipation |
| δ | delta | 社交 | attention, bond, trust, presence |
| ε | epsilon | 數理 | logic, precision, abstraction, certainty, complexity, fatigue |
| θ | theta | 元認知 | novelty, complexity, ambiguity, dimension_fit, creation_urge, correction_urge |
| ζ | zeta | 意識流 | temporal_coherence, memory, narrative, identity |

**θ 軸特殊功能**:
- `meta_allocate()`: 根據語義向量共振自動分配資料到各軸
- `trigger_theta_negativity()`: 偵測可能的錯配
- `correct_misallocation()`: 自動校正錯配
- `create_axis()`: 動態創建新維度

**維度間動態**:
- 反平方律「認知引力」
- 影響矩陣 (α 影響 γ, 等)
- 意圖重力 (維度漂移到目標座標)
- 維度間拖曳

### 2.2 理論公式 — 5 大數學模型

| 公式 | 檔案 | 行數 | 核心概念 |
|------|------|------|----------|
| **HSM** | `core/hsm_formula_system.py` | 156 | 認知差距 × 隨機性 (0.1) → 探索觸發 |
| **LifeIntensity** | `core/life_intensity_formula.py` | 704 | 知識∞ vs 現實限制 → 生命感 |
| **ActiveCognition** | `core/active_cognition_formula.py` | 720 | 系統壓力/原生秩序 → 建造活躍度 |
| **CDM** | `core/cdm_dividend_model.py` | 586 | 認知活動消耗資源 → 生命紅利 |
| **NonParadox** | `core/non_paradox_existence.py` | 253 | 認知差距大時接受矛盾共存 |

**解釋**:
- **HSM**: `HSM = C_Gap × E_M2`，當認知差距大時觸發探索
- **LifeIntensity**: `L_s = f(C_inf, C_limit, M_f, time)`，生命存在於「你能成為什麼」與「現實允許你成為什麼」的差距中
- **ActiveCognition**: `A_c = S_stress / O_order`，< 0.5 舒適/停滯, > 1.5 掙扎/超載
- **CDM**: 7 種認知活動消耗資源，產生「生命紅利」
- **NonParadox**: 認知差距 ≥ 0.6 時，接受多種矛盾狀態同時存在

### 2.3 自主生命週期 — 6 個模組

**目錄**: `ai/lifecycle/`

| 模組 | 功能 | 循環方式 |
|------|------|----------|
| **UserMonitor** | 追蹤用戶在線/情緒/活動 | 背景循環，30 秒檢查 |
| **ProactiveInteractionSystem** | 8 種主動互動觸發 | 背景循環，機會偵測 |
| **LLMDecisionLoop** | LLM 決策 7 種行為 | 背景循環，LLM prompt |
| **BehaviorFeedbackLoop** | 行為效果學習 | 背景循環，效果評估 |
| **MemoryIntegrationLoop** | 記憶結構化 | 背景循環，模式分析 |
| **UnifiedMemoryCoordinator** | HAM+Logic+CDM 橋接 | 被呼叫時執行 |

**主動互動觸發**:
1. USER_RETURN — 用戶回來
2. LONG_IDLE — 長時間閒置
3. EMOTIONAL_CHANGE — 情緒變化
4. TIME_BASED — 時間觸發 (早8晚8問候, 23點提醒睡)
5. MEMORY_TRIGGER — 記憶觸發
6. LEARNING_SHARE — 學習分享
7. WEATHER_CHANGE — 天氣變化
8. EVENT_REMINDER — 事件提醒

### 2.4 路由器 — ThetaRouter

**檔案**: `core/engine/theta_router.py` (441 行)
**狀態**: ✅ 完整真實實現

```
資料進入
    │
    ▼
resolve_route(port)
    ├─→ 計算語義向量共振 (vs 所有軸)
    ├─→ θ novelty/complexity 更新
    │
    ├─ max_resonance ≥ 0.5 → BIND (綁定到最佳軸)
    ├─ max_resonance < 0.3 + creation_urge > 0.6 → CREATE (創建新軸)
    └─ 否則 → BIND (低信心)
```

---

## 三、情感系統（感受）

### 3.1 生物模擬 — BiologicalIntegrator

**檔案**: `core/bio/biological_integrator.py` (852 行)
**狀態**: ✅ 完整真實實現

```
BiologicalIntegrator
    │
    ├─→ EndocrineSystem (內分泌)
    │     ├─ 多巴胺 (dopamine): 學習/獎勵
    │     ├─ 血清素 (serotonin): 情緒穩定
    │     ├─ 腎上腺素 (adrenaline): 戰鬥/逃跑
    │     ├─ 皮質醇 (cortisol): 壓力
    │     └─ 催產素 (oxytocin): 社交連結
    │
    ├─→ AutonomicNervousSystem (自主神經)
    │     ├─ 交感神經: 興奮/壓力
    │     └─ 副交感神經: 放鬆/恢復
    │
    ├─→ EmotionalBlendingSystem (情緒混合)
    │     └─ PAD 模型: Pleasure-Arousal-Dominance
    │
    ├─→ NeuroplasticitySystem (神經可塑性)
    │     └─ 學習/記憶形成
    │
    └─→ CerebellumEngine (小腦)
          └─ 運動/本體感覺

跨系統交互 (8 條規則):
    ├─ 神經→內分泌: 興奮→腎上腺素 (強度 0.8)
    ├─ 內分泌→情緒: 多巴胺→快樂
    ├─ 情緒→神經: 快樂→副交感
    └─ ...

恆定調節:
    ├─ _apply_homeostasis(): 每個循環恢復平衡
    └─ _synchronize_states(): 跨系統狀態同步
```

### 3.2 文字情緒 — EmotionAnalyzer

**檔案**: `services/llm/emotion_analyzer.py` (281 行)
**狀態**: ✅ 真實實現 (簡單)

```
使用者文字
    │
    ▼
analyze_emotion(text)
    ├─→ 7 種情緒關鍵字匹配
    │     happy / sad / angry / fear / surprise / curious / calm
    ├─→ 否定詞偵測 (3 字元內): 不, 没, 別, 無...
    ├─→ 強調詞偵測 (3 字元內): 好, 很, 太, 非常...
    ├─→ 權重計算: angry×1.2, fear×1.1, surprise×0.9, calm×0.7
    └─→ 回傳: {emotion, confidence, intensity, secondary_emotions}
```

### 3.3 用戶監控 — UserMonitor

**檔案**: `ai/lifecycle/user_monitor.py` (407 行)
**狀態**: ✅ 完整真實實現

```
UserMonitor
    │
    ├─→ 追蹤項目:
    │     ├─ 在線/離線狀態 (閒置 > 300s → 離線)
    │     ├─ 活動水平: HIGH (>0.5 msg/s) / MEDIUM / LOW / IDLE
    │     ├─ 情緒估計 (8 種: happy/sad/neutral/frustrated/excited/anxious/confused/relaxed)
    │     ├─ 會話時長
    │     └─ 總互動次數
    │
    ├─→ 歷史記錄:
    │     ├─ 情緒歷史: 最近 50 筆
    │     └─ 活動歷史: 最近 100 筆
    │
    └─→ 回呼 (callbacks):
          ├─ "offline" → 離線
          ├─ "return" → 回來
          └─ "online" → 上線
```

---

## 四、執行系統（輸出）

### 4.1 語音 — RealEdgeTTS

**檔案**: `core/art/real_edge_tts.py` (268 行)
**狀態**: ✅ 真實實現

```
Angela 要說話
    │
    ▼
RealEdgeTTS
    ├─→ greet(name): "Hello {name}! I'm Angela..."
    ├─→ express_emotion(text, emotion):
    │     ├─ happy: rate +10%, pitch +5Hz
    │     ├─ sad: rate -5%, pitch -5Hz
    │     ├─ angry: rate +5%, pitch +5Hz
    │     ├─ surprised: rate +10%, pitch +10Hz
    │     └─ calm: rate -5%, pitch -2Hz
    ├─→ narration(text): 通用旁白
    └─→ list_voices(): 列出所有可用語音

支援語音:
    ├─ 英文: AriaNeural, GuyNeural, JennyNeural
    ├─ 中文: XiaoxiaoNeural, YunxiNeural, XiaoyouNeural
    └─ 日文: NanamiNeural, KeitaNeural
```

### 4.2 Live2D 表情 — Live2DIntegration

**檔案**: `core/engine/live2d_integration.py` (116 行)
**狀態**: ✅ 真實實現

```
Angela 決定表情
    │
    ▼
Live2DIntegration.set_expression("happy")
    │
    ├─→ _parameters 更新 (30+ Live2D 參數)
    ├─→ _notify_state_change() → 回呼
    └─→ WebSocket 廣播 → 前端
          │
          ▼
    Live2DManager.setExpression("happy")
          │
          ├─→ Cubism SDK 渲染 (真實 3D)
          └─→ 2D Sprite 備選 (Intel UHD)
```

**8 種情緒配置**:
neutral / happy / sad / surprised / angry / shy / love / thinking

**每個情緒映射到**:
- ParamAngleX/Y/Z (頭部角度)
- ParamEyeLOpen/REyeOpen (眼睛)
- ParamMouthForm (嘴巴)
- ParamCheek (臉紅)
- 等 30+ 參數

### 4.3 桌面操作 — DesktopInteraction

**檔案**: `core/engine/desktop_interaction.py` (1178 行)
**狀態**: ✅ 完整真實實現

```
DesktopInteraction
    │
    ├─→ organize_desktop(): 按副檔名分類
    │     ├─ documents/ → .pdf, .doc, .txt
    │     ├─ images/ → .jpg, .png, .gif
    │     ├─ code/ → .py, .js, .ts
    │     └─ ...
    │
    ├─→ set_wallpaper(): 跨平台壁紙
    │     ├─ Windows: ctypes.windll
    │     ├─ macOS: osascript
    │     └─ Linux: gsettings/qdbus
    │
    ├─→ create_file(): 檔案操作
    ├─→ cleanup_desktop(): 刪除舊暫存檔
    │
    └─→ BrowserController (635 行)
          ├─ search(): DuckDuckGo 真實搜尋
          ├─ extract_content(): BeautifulSoup 網頁提取
          └─ detect_game(): 關鍵字遊戲偵測
```

### 4.4 繪圖 — ImageGenerationAgent

**檔案**: `ai/agents/specialized/image_generation_agent.py` (107 行)
**狀態**: ❌ Stub (需要 Stable Diffusion API key)

**Live2DAvatarGenerator** (`core/engine/live2d_avatar_generator.py`, 1256 行):
- `generate_avatar()`: 6 階段管線 (初始化→底圖→圖層→綁定→配置→完成)
- 但 `_generate_layer_image()` 用 Pillow 繪製色塊占位符

---

## 五、記憶系統

### 5.1 三層架構（權威定義）

**來源**: `FULL_ARCHITECTURE_ANALYSIS.md` §5.2

```
HAM 記憶層次:
  L1 — Raw Memory (原始記憶):  sensor input, chat history
  L2 — Abstract Memory (抽象記憶):  pattern, concept, relation
  L3 — Symbolic Memory (符號記憶):  symbolic representation, formula
```

**5 種記憶類型** (`ai/memory/types.py`):

| 類型 | 說明 |
|------|------|
| `core` | 核心記憶 (身份、關鍵事實) |
| `episodic` | 事件記憶 (經驗、對話) |
| `semantic` | 語義記憶 (概念、知識) |
| `procedural` | 程序記憶 (技能、行為) |
| `working` | 工作記憶 (當前上下文) |

### 5.2 AttractorField — 梯度導航

**檔案**: `ai/memory/attractor_field.py`

```
AttractorField 算法:
  1. 每個記憶點在向量空間中有一個位置
  2. Attractor (吸引子) 是穩定點，附近的記憶被"吸引"強化
  3. Gradient descent 導航:
     新記憶位置 = 舊位置 - learning_rate × gradient(fields)
  4. 重要性評分:  relevance = cosine_similarity(query, memory) × importance_weight
```

**向量存儲**:
- ChromaDB: 持久化向量存儲
- FAISS: 快速相似性搜索
- JSON: 本地文件備份

### 5.3 HAMMemoryManager — 最小 JSON 存儲

**檔案**: `ai/memory/ham_memory/ham_manager.py` (173 行)
**狀態**: ✅ 真實實現 (薄)

```
HAMMemoryManager
    │
    ├─→ 存儲: angela_memory.json
    │     ├─ templates: 模板 + 關鍵字
    │     ├─ conversations: 對話歷史
    │     └─ experiences: 經驗 + 自動提取關鍵字
    │
    ├─→ 檢索: Bigram Jaccard 相似度
    │     ├─ 子字串匹配 (0.9 分)
    │     └─ 字符雙連音 Jaccard
    │
    └─→ 統計: 模板數/對話數
```

### 5.4 LogicUnit — 邏輯/規則記憶

**檔案**: `ai/memory/lu_logic/logic_unit.py` (496 行)
**狀態**: ✅ 真實實現

```
LogicUnit (L2 邏輯層)
    │
    ├─→ 規則管理:
    │     ├─ LogicRule: 條件 + 動作 + 優先級
    │     ├─ RulePriority: LOW / NORMAL / HIGH / CRITICAL
    │     └─ 規則匹配 + 執行
    │
    └─→ 用途: 管理和執行邏輯規則，支持條件判斷、規則匹配和推理
```

### 5.5 UnifiedMemoryCoordinator — 統一協調器

**檔案**: `ai/lifecycle/unified_memory_coordinator.py`
**狀態**: ✅ 真實實現

```
UnifiedMemoryCoordinator
    │
    ├─→ HAM: 分層關聯記憶 (存儲/檢索)
    ├─→ LogicUnit: 邏輯規則記憶
    ├─→ CDM: 認知紅利模型 (資源追蹤)
    │
    └─→ 統一介面:
          ├─ query(): 跨系統查詢
          └─ store(): 統一存儲
```

### 5.6 記憶層級設計（文檔描述）

**來源**: `HAMEMORY_INTEGRATION_SUCCESS.md`

```
記憶層級架構 (文檔):
├── working_memory (50 項位)    # 當前對話上下文
├── short_term (200 項位)      # 幾小時到幾天
├── long_term (500 項位)        # 幾週到幾月
└── episodic (100 項位)         # 重要事件和經驗

智能分類:
  - episodic: 包含 "important", "critical", "remember"
  - long_term: 長內容 (>500 字符)
  - short_term: 問題類內容
  - working_memory: 其他對話內容
```

**注意**: 此分類邏輯在文檔中描述，但 `HAMMemoryManager` 實際實現是平面 JSON 存儲，未實現分層。

### 5.7 ED3N — 反射與字典

**目錄**: `ai/ed3n/`

```
ED3NEngine
    │
    ├─→ ReflexLayer: 亞毫秒反射
    │     ├─ load_presets(): 載入預設反射
    │     └─ process(): LRU 快取，極速回應
    │
    ├─→ DictionaryLayer:
    │     ├─ encode(text): 精確匹配
    │     └─ encode_soft(text): 模糊匹配
    │
    └─→ ContinuousLearning: 持續學習 (慢)
```

---

## 六、完整管線流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    使用者輸入 (文字/圖片/語音)                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ [接入層] WebSocket + HTTP + Session                              │
│   ├─ 握手驗證 (HMAC)                                            │
│   ├─ session_history (30 則上限)                                 │
│   └─ _handle_chat_request()                                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
┌──────────────────┐ ┌──────────┐ ┌──────────────┐
│ EmotionAnalyzer  │ │ Bio      │ │ StateMatrix  │
│ 文字情緒分析      │ │ 刺激     │ │ 7D 狀態讀取   │
│ (7 種情緒)       │ │ (非同步) │ │ (αβγδεθζ)    │
└────────┬─────────┘ └──────────┘ └──────┬───────┘
         │                               │
         └───────────┬───────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ [分類層] QueryClassifier (16 種意圖)                              │
│   ├─ 9 原有: REFLEX, GREETING, MATH, LOGIC, KNOWLEDGE,         │
│   │          CREATIVE, OPINION, COMMAND, UNKNOWN                │
│   ├─ 7 新增: FILE, SEARCH, CODE, EXECUTE, TASK, VISION, AUDIO  │
│   └─ ED3N encode_soft 輔助分類 (_keys_to_intent)                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ [路由層] ModelBus                                                │
│   ├─ REFLEX/GREETING → ED3N reflex (亞毫秒)                     │
│   ├─ MATH → ED3N → GARDEN                                       │
│   ├─ FILE → FileOperationHandler → DesktopInteraction           │
│   ├─ SEARCH → WebSearchHandler → DuckDuckGo                     │
│   ├─ CODE/EXECUTE/TASK → Handlers                               │
│   ├─ VISION → VisionService                                     │
│   ├─ KNOWLEDGE → GARDEN → Cloud LLM                             │
│   ├─ CREATIVE → Cloud LLM                                       │
│   └─ 其他 → fan-out                                             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ [Prompt 層] PromptBuilder                                       │
│   ├─ System: "你是 Angela..."                                    │
│   ├─ 【生物狀態】bio_state                                      │
│   ├─ 【Angela 當前狀態】7D axes                                  │
│   ├─ 【元認知 θ】novelty, creation_urge                         │
│   ├─ 【執行 η】module_count, success_rate                       │
│   ├─ 【理論公式指標】HSM, LifeIntensity, ActiveCognition...      │
│   ├─ 【自主認知決策】phase, recent_decisions                     │
│   ├─ 【θ 路由狀態】creation_urge, negativity                    │
│   ├─ 【圖片分析結果】(如果有)                                    │
│   ├─ 歷史 (last 10)                                             │
│   └─ 相關上下文 (ED3N retrieved)                                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ [LLM 層] AngelaLLMService.generate_response()                   │
│   └─ Cloud LLM (Ollama / OpenAI / Anthropic / Google)           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
┌──────────────────┐ ┌──────────┐ ┌──────────────┐
│ 生物狀態更新      │ │ HAM      │ │ Live2D       │
│ (fire-and-forget)│ │ store_   │ │ set_expression│
│                  │ │ experience│ │ → 前端渲染    │
└──────────────────┘ └──────────┘ └──────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│ [回應層] WebSocket 回傳                                          │
│   {response_text, emotion, hit_score, route, session_id}        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 七、系統成熟度總覽

| 系統 | 檔案 | 行數 | 狀態 | 複雜度 |
|------|------|------|------|--------|
| StateMatrix4D | `core/engine/state_matrix.py` | 1439 | ✅ 真實 | 極高 |
| DesktopInteraction | `core/engine/desktop_interaction.py` | 1178 | ✅ 真實 | 高 |
| LogicUnit | `ai/memory/lu_logic/logic_unit.py` | 496 | ✅ 真實 | 中 |
| BiologicalIntegrator | `core/bio/biological_integrator.py` | 852 | ✅ 真實 | 高 |
| VisionService | `services/vision_service.py` | 706 | ⚠️ 架構真/方法模擬 | 中 |
| 5 個理論公式 | `core/*.py` | ~2419 | ✅ 真實 | 高 |
| 6 個生命週期模組 | `ai/lifecycle/*.py` | ~2800 | ✅ 真實 | 高 |
| BrowserController | `core/engine/browser_controller.py` | 635 | ✅ 真實 | 中 |
| AudioSystem | `core/engine/audio_system.py` | 630 | ⚠️ 狀態機真/音訊模擬 | 中 |
| ThetaRouter | `core/engine/theta_router.py` | 441 | ✅ 真實 | 中 |
| UserMonitor | `ai/lifecycle/user_monitor.py` | 407 | ✅ 真實 | 中 |
| EmotionAnalyzer | `services/llm/emotion_analyzer.py` | 281 | ✅ 真實(簡單) | 低 |
| RealEdgeTTS | `core/art/real_edge_tts.py` | 268 | ✅ 真實 | 中 |
| HAMMemoryManager | `ai/memory/ham_memory/ham_manager.py` | 173 | ✅ 真實(薄) | 低 |
| Live2DIntegration | `core/engine/live2d_integration.py` | 116 | ✅ 真實 | 低 |
| AudioService | `services/audio_service.py` | 41 | ❌ Stub | - |
| TactileService | `services/tactile_service.py` | 66 | ❌ Stub | - |
| ImageGeneration | `ai/agents/specialized/image_generation_agent.py` | 107 | ❌ Stub | - |

**總結**: 核心認知系統 ~10,000+ 行全部是真實實現。主要缺口在感知層（聽覺/觸覺 stub）和部分執行層（繪圖 stub、語音未串接）。

---

## 相關文件

| 文件 | 內容 |
|------|------|
| [系統架構概覽](OVERVIEW.md) | 高階架構圖、服務層、整合層 |
| [完整架構](../ARCHITECTURE.md) | 6 層架構詳細文檔 |
| [管線重構計畫](../../PLAN_full_pipeline_architecture.md) | 聊天管線重構 v10 |
| [聊天管線修復](../../PLAN_chat_pipeline_fix.md) | 接線修復計畫 |
