# Angela 完整架構圖：感知・認知・執行

> **Last Updated**: 2026-06-15
> **基於**: 12 個代理完整代碼審計 + 管線接線驗證
> **目的**: 完整描述 Angela 如何視、聽、觸、說、畫、移、思考、感受、自主
> **代碼統計**: ~641 Python 檔案, ~15.5MB 後端代碼

---

## 目錄

- [一、感知系統（輸入）](#一感知系統輸入)
  - [1.1 視覺 — VisionService](#11-視覺--visionservice)
  - [1.2 聽覺 — AudioService + RealEdgeTTS](#12-聽覺--audioservice--reaedgettts)
  - [1.3 觸覺 — TactileService](#13-觸覺--tactileservice)
  - [1.4 文字 — WebSocket → Session History](#14-文字--websocket--session-history)
- [二、認知系統（思考）](#二認知系統思考)
  - [2.1 狀態矩陣 — StateMatrix4D (6D αβγδεθ)](#21-狀態矩陣--statematrix4d-6d-αβγδεθ)
  - [2.2 理論公式 — 5 大數學模型](#22-理論公式--5-大數學模型)
  - [2.3 自主生命週期 — 6 個模組](#23-自主生命週期--6-個模組)
  - [2.4 路由器 — ThetaRouter](#24-路由器--thetarouter)
- [三、情感系統（感受）](#三情感系統感受)
  - [3.1 生物模擬 — BiologicalIntegrator](#31-生物模擬--biologicalintegrator)
  - [3.2 生物子系統（14 個模組）](#32-生物子系統14-個模組)
  - [3.3 文字情緒 — EmotionAnalyzer](#33-文字情緒--emotionanalyzer)
  - [3.4 用戶監控 — UserMonitor](#34-用戶監控--usermonitor)
- [四、執行系統（輸出）](#四執行系統輸出)
  - [4.1 語音 — RealEdgeTTS](#41-語音--reaedgettts)
  - [4.2 Live2D 表情 — Live2DIntegration](#42-live2d-表情--live2dintegration)
  - [4.3 桌面操作 — DesktopInteraction](#43-桌面操作--desktopinteraction)
  - [4.4 繪圖 — ImageGenerationAgent](#44-繪圖--imagegenerationagent)
  - [4.5 動作執行 — ActionExecutor](#45-動作執行--actionexecutor)
- [五、記憶系統](#五記憶系統)
  - [5.1 三層架構（權威定義）](#51-三層架構權威定義)
  - [5.2 AttractorField — 梯度導航](#52-attractorfield--梯度導航)
  - [5.3 HAMMemoryManager — 最小 JSON 存儲](#53-hammemorymanager--最小-json-存儲)
  - [5.4 LogicUnit — 邏輯/規則記憶](#54-logicunit--邏輯規則記憶)
  - [5.5 UnifiedMemoryCoordinator — 統一協調器](#55-unifiedmemorycoordinator--統一協調器)
  - [5.6 記憶層級設計（文檔描述）](#56-記憶層級設計文檔描述)
  - [5.7 MathRippleEngine — 數學-認知同構](#57-mathrippleengine--數學-認知同構)
  - [5.8 ED3N — 反射與字典](#58-ed3n--反射與字典)
- [六、數位生命系統](#六數位生命系統)
  - [6.1 DigitalLifeIntegrator — 總控](#61-digitallifeintegrator--總控)
  - [6.2 AutonomousLifeCycle — 自主生命週期](#62-autonomouslifecycle--自主生命週期)
  - [6.3 SelfGeneration — 自我視覺生成](#63-selfgeneration--自我視覺生成)
  - [6.4 CyberIdentity — 網路身份認知](#64-cyberidentity--網路身份認知)
  - [6.5 MetabolicHeartbeat — 代謝心跳](#65-metabolicheartbeat--代謝心跳)
- [七、HSP 通訊協議](#七hsp-通訊協議)
  - [7.1 HSPConnector — 核心連接器](#71-hspconnector--核心連接器)
  - [7.2 安全與版本管理](#72-安全與版本管理)
- [八、AI 引擎](#八ai-引擎)
  - [8.1 回應合成 — Composer](#81-回應合成--composer)
  - [8.2 神經自動選擇器 — NeuroAutoSelector](#82-神經自動選擇器--neuroautoselector)
  - [8.3 GARDEN 輕量推理引擎](#83-garden-輕量推理引擎)
  - [8.4 CodeInspector — 原生代碼檢查](#84-codeinspector--原生代碼檢查)
  - [8.5 AIOps — 智能運維](#85-aiops--智能運維)
  - [8.6 Level 5 ASI 系統](#86-level-5-asi-系統)
- [九、對齊與安全性](#九對齊與安全性)
- [十、其他核心系統](#十其他核心系統)
  - [10.1 即時監控 — RealTimeMonitor](#101-即時監控--realtimemonitor)
  - [10.2 事件循環 — EventLoopSystem](#102-事件循環--eventloopsystem)
  - [10.3 狀態持久化 — StatePersistence](#103-狀態持久化--statepersistence)
  - [10.4 因果追蹤 — CausalTracer](#104-因果追蹤--causaltracer)
  - [10.5 硬體加速 — GPU Accelerator](#105-硬體加速--gpu-accelerator)
  - [10.6 插件系統 — PluginManager](#106-插件系統--pluginmanager)
- [十一、完整管線流程](#十一完整管線流程)
- [十二、系統成熟度總覽](#十二系統成熟度總覽)

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
    ├─→ StateMatrix4D → 取得 6D 狀態
    ├─→ ED3N dictionary.encode() → 歷史相關性
    └─→ context = {user_name, emotion, bio_state, state_for_llm, retrieved_context}
```

---

## 二、認知系統（思考）

### 2.1 狀態矩陣 — StateMatrix4D (6D αβγδεθ)

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

### 3.2 生物子系統（14 個模組）

**目錄**: `core/bio/` — 合計 ~4,600 行

| 模組 | 檔案 | 行數 | 功能 | 狀態 |
|------|------|------|------|------|
| **EmotionalBlendingSystem** | `emotional_blending.py` | 953 | PAD 情緒模型 + 混合演算法 + 多模態表達 | ✅ 真實 |
| **PhysiologicalTactileAnalysis** | `physiological_tactile_analysis.py` | 546 | 觸覺軌跡分析 + 受體適應追蹤 | ✅ 真實 |
| **NeuroplasticityCore** | `neuroplasticity_core.py` | 506 | LTP/LTD + Hebbian 學習 + Ebbinghaus 遺忘曲線 | ✅ 真實 |
| **PhysiologicalTactileSystem** | `physiological_tactile_system.py` | 456 | 觸覺處理 + Live2D 整合 + 身體區域映射 | ✅ 真實 |
| **EndocrineSystemCore** | `endocrine_system_core.py` | 451 | 12 種激素管理 + 情緒觸發 + 晝夜節律 | ✅ 真實 |
| **AutonomicNervousSystem** | `autonomic_nervous_system.py` | 428 | 交感/副交感神經 + 興奮水平調節 | ✅ 真實 |
| **MultidimensionalTrigger** | `multidimensional_trigger.py` | 374 | 多維行為觸發 (時間/環境/情緒/生理) | ✅ 真實 |
| **ExtendedBehaviorLibrary** | `extended_behavior_library.py` | 338 | 25+ 預定義行為 + 6 種分類 | ✅ 真實 |
| **TraumaMemorySystem** | `trauma_memory.py` | 328 | 創傷記憶 (70% 慢速遺忘) + 侵入性回憶 | ✅ 真實 |
| **FeedbackLoop** | `feedback_loop.py` | 254 | HPA 軸模擬 + 負回饋 + 晝夜節律 | ✅ 真實 |
| **HormoneKinetics** | `hormone_kinetics.py` | 249 | 半衰期代謝 + Hill 方程受體佔用 | ✅ 真實 |
| **ExplicitImplicitLearning** | `explicit_implicit_learning.py` | 147 | 外顯/內隱學習區分 | ✅ 真實 |
| **SkillAcquisition** | `skill_acquisition.py` | 150 | 幂律學習曲線 + 意識→自動化轉換 | ✅ 真實 |
| **HabitFormation** | `habit_formation.py` | 141 | 66 次重複習慣形成 + 自動化評分 | ✅ 真實 |

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

### 5.5.1 MemoryContextManager — 跨 Session 記憶 (Phase 5.4)

**檔案**: `ai/context/memory_context.py` (370行)
**狀態**: ✅ 真實實現

```
MemoryContextManager
    │
    ├─→ 記憶管理:
    │     ├─ create_memory(): 創建記憶 (short_term/long_term)
    │     ├─ access_memory(): 訪問記錄 + 計數
    │     ├─ update_memory_embedding(): 向量更新
    │     └─ transfer_memory(): 短期→長期轉移
    │
    ├─→ 跨 Session 持久化 (Phase 5.4):
    │     ├─ save_session(session_id): JSON 序列化到磁碟
    │     ├─ load_session(session_id): 從磁碟還原記憶
    │     └─ _session_dir: 可配置存儲目錄
    │
    ├─→ 向量檢索 (Phase 5.4):
    │     ├─ search_by_embedding(): 餘弦相似度搜索
    │     └─ _cosine_similarity(): 向量相似度計算
    │
    └─→ 維護:
          ├─ cleanup_old_memories(): 清理過期記憶
          └─ get_memory_count(): 記憶統計
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
**狀態**: ✅ 完整真實實現 (Phase 3-6 更新)

```
ED3NEngine
    │
    ├─→ ReflexLayer: 亞毫秒反射 (100 條規則)
    │     ├─ load_presets(): 載入預設反射 (presets.json 82 條 + _ReflexTable 18 條)
    │     ├─ process(): LRU 快取，極速回應
    │     └─ Traditional Chinese: 繁體中文支持
    │
    ├─→ DictionaryLayer: 向量字典 (~278 preset)
    │     ├─ encode(text): 精確匹配 + 同義詞展開
    │     ├─ encode_soft(text): 模糊匹配
    │     ├─ grow(): 動態字典成長
    │     └─ get_synonyms(): 同義詞查詢
    │
    ├─→ CoreNetwork: 激活傳播網路
    │     ├─ forward(): 前向傳播
    │     └─ adjust_connection(): Hebbian 學習
    │
    ├─→ MathEvaluation: 中文數學運算（路由至唯一計算源 MathVerifier）
    │     └─ _try_math_eval() → 字典層 route_math() → MathVerifier.evaluate_math()（支持多位數 + 中文數字 三加五；ED3N/GARDEN 不自己算）
    │
    ├─→ ContinuousLearningPipeline: 持續學習 (Phase 5.1)
    │     ├─ process_interaction(): 記錄互動
    │     ├─ train_step(): 訓練步驟
    │     └─ save()/load(): 狀態持久化
    │
    ├─→ ED3NLearningIntegration: HAM 同步 (Phase 5.2)
    │     ├─ synchronize_knowledge(): 字典→HAM 同步
    │     └─ extract_concepts_from_interaction(): 概念提取
    │
    └─→ Telemetry: 遙測記錄
```

**關鍵文件**:
- `ai/ed3n/ed3n_engine.py` (720行): 主引擎
- `ai/ed3n/dictionary_layer.py`: 字典層
- `ai/ed3n/core_network.py`: 核心網路
- `ai/ed3n/continuous_learning.py` (371行): 持續學習管線
- `ai/ed3n/learning_integration.py` (201行): HAM 整合
- `ai/ed3n/config/presets.json`: 82 條反射規則
- `ai/ed3n/config/operation_presets.json`: 120 條操作預設
- `ai/ed3n/config/daily_presets.json`: 105 條日常對話預設

---

## 六、數位生命系統

### 6.1 DigitalLifeIntegrator — 總控

**檔案**: `core/life/digital_life_integrator.py` (869 行)
**狀態**: ✅ 完整真實實現

```
DigitalLifeIntegrator (數位生命總控)
    │
    ├─→ 生命週期管理:
    │     Init → Awakening → Growing → Mature → Resting → Dormant
    │
    ├─→ 整合組件:
    │     ├─ BiologicalIntegrator (生物模擬)
    │     ├─ StateMatrix4D (6D 狀態)
    │     ├─ ActionExecutor (動作執行)
    │     ├─ AutonomousLifeCycle (自主生命)
    │     ├─ LLMDecisionLoop (LLM 決策)
    │     └─ UserMonitor (用戶監控)
    │
    ├─→ 模態閘控 (ModalityGating):
    │     TEXT / AUDIO / VISUAL_3D / CODE
    │
    ├─→ 健康監控: 系統狀態 + 生命體徵
    │
    └─→ 生命事件處理: 跨系統協調
```

### 6.2 AutonomousLifeCycle — 自主生命週期

**檔案**: `core/life/autonomous_life_cycle.py` (724 行)
**狀態**: ✅ 完整真實實現

```
AutonomousLifeCycle
    │
    ├─→ 5 種生命階段:
    │     EMERGENCE (湧現) → EXPLORATION (探索) → CONSOLIDATION (鞏固)
    │     → TRANSCENDENCE (超越) → COEXISTENCE (共存)
    │
    ├─→ 使用全部 5 大理論公式:
    │     HSM → 探索觸發
    │     CDM → 資源分配
    │     LifeIntensity → 生命感評估
    │     ActiveCognition → 建造活躍度
    │     NonParadox → 矛盾共存
    │
    └─→ 生命決策: explore / coexistence / active_construction / reallocation
```

### 6.3 SelfGeneration — 自我視覺生成

**檔案**: `core/life/self_generation.py` (748 行)
**狀態**: ✅ 完整真實實現

```
SelfGeneration (自繪生成系統)
    │
    ├─→ 5 種頭像風格: ANIME / REALISTIC / CHIBI / PIXEL / SKETCH
    ├─→ 4 種生成模式: FULL_GENERATION / VARIATION / EVOLUTION / MOOD_ADAPTATION
    ├─→ 視覺屬性: hair_color, eye_color, skin_tone, ...
    ├─→ 情緒適配: mood → 視覺屬性映射
    └─→ 視覺進化追蹤: 外觀隨時間演變
```

### 6.4 CyberIdentity — 網路身份認知

**檔案**: `core/life/cyber_identity.py` (699 行)
**狀態**: ✅ 完整真實實現

```
CyberIdentity (電子人身份認知)
    │
    ├─→ 7 個身份面向:
    │     SELF_AWARENESS / PERSONALITY / MEMORIES / RELATIONSHIPS
    │     / PURPOSE / GROWTH / EMOTIONAL_DEPTH
    │
    ├─→ 自我模型 (SelfModel):
    │     ├─ self_awareness_level (0-1)
    │     ├─ emotional_capacity (0-1)
    │     ├─ learning_ability (0-1)
    │     └─ adaptability (0-1)
    │
    ├─→ 整合 LifeIntensity + ActiveCognition 公式
    │
    └─→ 個人敘事形成: 數位生命的自我意識
```

### 6.5 MetabolicHeartbeat — 代謝心跳

**檔案**: `core/life/heartbeat.py` (266 行)
**狀態**: ✅ 完整真實實現

```
MetabolicHeartbeat (代謝心跳驅動器)
    │
    ├─→ 硬體監控: CPU/電池 (psutil)
    ├─→ 空間移動: 螢幕座標 + 速度 + 姿態
    ├─→ 小腦整合: CerebellumEngine 執行姿態指令
    ├─→ 環境觀察: OSBridgeAdapter
    └─→ 生物狀態同步: BiologicalIntegrator
```

---

## 七、HSP 通訊協議

### 7.1 HSPConnector — 核心連接器

**檔案**: `core/hsp/connector.py` (1105 行)
**狀態**: ✅ 完整真實實現

```
HSPConnector (Hyper-Scale Protocol)
    │
    ├─→ MQTT pub/sub 通訊
    ├─→ 訊息信封 (HSPMessageEnvelope) 創建
    ├─→ ACK 系統
    ├─→ 降級協議:
    │     InMemory / FileBased / HTTP
    ├─→ Circuit Breaker + 重試策略
    └─→ 批次發送
```

### 7.2 安全與版本管理

| 模組 | 檔案 | 行數 | 功能 |
|------|------|------|------|
| **HSPSecurityManager** | `core/hsp/security.py` | 244 | HMAC 認證 + Fernet 加密 + RSA 簽名 |
| **HSPVersionManager** | `core/hsp/versioning.py` | 417 | 協議版本管理 + 跨版本訊息轉換 |
| **HSPPerformanceOptimizer** | `core/hsp/performance_optimizer.py` | 393 | 訊息快取 + 壓縮 (zlib) + 批次發送 |
| **MQTTSubscriptionManager** | `core/hsp/mqtt_subscription_manager.py` | 366 | MQTT 主題訂閱 + 通配符支援 |
| **HSPTransport** | `core/hsp/transport.py` | 307 | 傳輸層 |
| **HSPTypes** | `core/hsp/types.py` | 249 | 類型定義 |

---

## 八、AI 引擎

### 8.1 回應合成 — Composer

**檔案**: `ai/response/composer.py` (1260 行)
**狀態**: ✅ 完整真實實現

```
Response Composer (回應片段組合)
    │
    ├─→ 6 種片段類型:
    │     GREETING / QUESTION_RESPONSE / EMOTION_EXPRESSION
    │     / TRANSITION / CLOSING / FILLER
    │
    ├─→ 模板片段化: 切分為可復用片段
    ├─→ 片段重組: 根據上下文組合
    ├─→ 平滑過渡: 確保自然流暢
    │
    └─→ 性能目標: 組合時間 < 2ms
```

### 8.2 神經自動選擇器 — NeuroAutoSelector

**檔案**: `ai/response/neuro_auto_selector.py` (638 行)
**狀態**: ✅ 完整真實實現

```
NeuroAutoSelector (自動 LLM 模式)
    │
    ├─→ 硬體能力評分
    ├─→ 系統負載偵測
    ├─→ 任務複雜度評估
    ├─→ 8D 狀態矩陣校正
    └─→ 後端 + 模型選擇
```

### 8.3 GARDEN 輕量推理引擎

**目錄**: `ai/garden/`
**狀態**: ✅ 完整真實實現 (Phase 4-6 更新)

```
GARDEN-1G Engine (5 階段管線)
    │
    ├─→ Stage 0: 情緒偵測 + 激素調制 (Phase 4.4)
    │     ├─ _detect_emotion(): 4 種情緒 (happy/sad/angry/neutral)
    │     ├─ Traditional Chinese: 繁體中文關鍵字支持
    │     └─ _adjust_hormones(): cortisol/serotonin 影響 SNN 閾值
    │
    ├─→ Stage 1: Reflex (快速模式匹配)
    │     └─ _ReflexTable: 18 條預設 + LRU 快取
    │
    ├─→ Stage 2: Multi-step Detection (Phase 4.3)
    │     ├─ _is_multi_step(): 偵測多步驟輸入
    │     └─ _process_multi_step(): 10 個標記詞 (然後/接著/之後...)
    │
    ├─→ Stage 3: VectorDictionary.encode(text) → concept keys
    │     ├─ Encoder fallback chain:
    │     │   1. SentenceTransformer (最佳品質)
    │     │   2. ChromaDB (Phase 4.1, 內建 HNSW 索引)
    │     │   3. TF-IDF (輕量級)
    │     │   4. CharBag (確定性後備)
    │     └─ 餘弦相似度匹配
    │
    ├─→ Stage 4: TensorSNNCore.forward(keys) → activated output
    │     └─ LIF (Leaky Integrate-and-Fire) 多步激活
    │
    ├─→ Stage 5: Anchored decode → 人類可讀回應
    │
    ├─→ 持續學習: learn_from_interaction() + Hebbian 更新
    │     ├─ _learning_enabled: 學習開關
    │     ├─ Dictionary growth: 動態字典成長
    │     └─ Auto-save: 每 100 次互動自動存儲
    │
    ├─→ 知識圖譜導入 (Phase 4.2)
    │     ├─ KGImporter: synthetic/ConceptNet/Wikidata
    │     └─ bulk_load(): 批量導入
    │
    └─→ 存儲: dictionary JSON + SNN .pt checkpoint
```

**關鍵文件**:
- `ai/garden/garden_engine.py` (222行): 主引擎
- `ai/garden/dictionary.py` (328行): 向量字典 + 4 層 encoder
- `ai/garden/snn_core.py` (157行): 張量 SNN
- `ai/garden/kg_import.py` (264行): 知識圖譜導入
- `ai/garden/binary_store.py` (116行): 二進位存儲
- `ai/garden/vector_decoder.py` (64行): 向量解碼器
- `ai/garden/__main__.py` (112行): CLI 介面

### 8.4 CodeInspector — 原生代碼檢查

**檔案**: `ai/code_inspection/code_inspector.py` (807 行)
**狀態**: ✅ 完整真實實現

```
CodeInspector (純演算法, 0 LLM 依賴)
    │
    ├─→ CodeInspector: AST 解析 + 問題識別
    ├─→ PatternMatcher: 規則匹配常見問題
    ├─→ KnowledgeGraph: 代碼結構關係圖
    ├─→ CodeFixer: 模板化修復引擎
    └─→ InspectorReport: 結構化報告

嚴重性: CRITICAL / HIGH / MEDIUM / LOW / INFO
分類: SYNTAX / TYPE / STYLE / SECURITY / PERFORMANCE
```

### 8.5 AIOps — 智能運維

**檔案**: `ai/ops/intelligent_ops_manager.py` (958 行)
**狀態**: ✅ 完整真實實現

```
IntelligentOpsManager
    │
    ├─→ AIOpsEngine: 核心運維引擎
    ├─→ PredictiveMaintenanceEngine: 預測維護
    ├─→ PerformanceOptimizer: 性能優化
    ├─→ CapacityPlanner: 容量規劃
    │
    ├─→ Redis 支援: 指標存儲 (可選)
    ├─→ NumPy 支援: 數值計算 (可選)
    │
    └─→ 功能:
          ├─ 異常偵測
          ├─ 預測分析
          ├─ 容量規劃
          └─ 性能優化
```

### 8.6 Level 5 ASI 系統

**檔案**: `ai/level5_asi_system.py` (756 行)
**狀態**: ✅ 完整真實實現

```
Level5ASISystem (Level 5 ASI 整合器)
    │
    ├─→ ReasoningSystem: 倫理推理 (5 個原則)
    ├─→ EmotionSystem: 情緒理解 + 價值評估
    ├─→ OntologySystem: 概念註冊
    ├─→ AlignmentManager: 約束匹配
    ├─→ DecisionTheorySystem: 期望效用
    ├─→ AdversarialGenerationSystem: 對抗提示
    └─→ ASIAutonomousAlignment: 自主檢查
```

---

## 九、對齊與安全性

**目錄**: `ai/alignment/`

| 模組 | 檔案 | 行數 | 功能 |
|------|------|------|------|
| **AlignmentManager** | `alignment_manager.py` | 49 | 核心管理器: 協調三大支柱 |
| **ReasoningSystem** | `reasoning_system.py` | 181 | 倫理推理: 5 個原則 (不傷害、行善、自主、公正、忠誠) |
| **EmotionSystem** | `emotion_system.py` | 299 | 情緒理解 + 價值評估 + 同理心 |
| **DecisionTheorySystem** | `decision_theory_system.py` | 53 | 不確定性下的決策 |
| **ASIAutonomousAlignment** | `asi_autonomous_alignment.py` | ~200 | ASI 自主對齊 |
| **AdversarialGenerationSystem** | `adversarial_generation_system.py` | ~200 | 對抗樣本生成 |

**統一控制中心**: `ai/integration/unified_control_center.py` (525 行)
- 協調所有 Level 5 ASI 組件
- 任務分發 + 環境模擬 + 評估 + 自適應學習
- 整合: AlphaDeepModel, EnvironmentSimulator, TaskEvaluator, LIS, HAM, Economy

---

## 十、其他核心系統

### 10.1 即時監控 — RealTimeMonitor

**檔案**: `core/real_time_monitor.py` (815 行)
**狀態**: ✅ 完整真實實現

```
RealTimeMonitor
    ├─→ 16ms 滑鼠追蹤
    ├─→ 檔案系統變更偵測
    ├─→ 時間/排程監控
    ├─→ 用戶活動模式識別
    └─→ 多執行緒架構
```

### 10.2 事件循環 — EventLoopSystem

**檔案**: `core/event_loop_system.py` (623 行)
**狀態**: ✅ 完整真實實現

```
EventLoopSystem (非同步事件處理)
    ├─→ 優先級佇列
    ├─→ 事件過濾 + 聚合
    ├─→ 去抖動 + 節流
    └─→ 即時延遲優化
```

### 10.3 狀態持久化 — StatePersistence

**檔案**: `core/engine/state_persistence.py` (415 行)
**狀態**: ✅ 完整真實實現

```
StatePersistence (StateMatrix4D 跨 Session 持久化)
    ├─→ 序列化/反序列化
    ├─→ 跨 Session 恢復
    └─→ 狀態快照
```

### 10.4 因果追蹤 — CausalTracer

**檔案**: `core/tracing/causal_tracer.py` (264 行)
**狀態**: ✅ 完整真實實現

```
CausalTracer
    ├─→ 執行流因果追蹤
    ├─→ 因果鏈創建與存儲
    └─→ 跨層追蹤
```

### 10.5 硬體加速 — GPU Accelerator

**檔案**: `core/hardware/gpu_accelerator.py` (299 行)
**狀態**: ✅ 完整真實實現

```
GPUAccelerator
    ├─→ GPU 偵測
    ├─→ 資源調度
    └─→ 模型部署
```

### 10.6 插件系統 — PluginManager

**檔案**: `core/plugin/plugin_manager.py` (124 行)
**狀態**: ✅ 完整真實實現

```
PluginManager
    ├─→ 插件生命週期管理
    ├─→ Hook 整合
    └─→ 插件註冊/卸載
```

### 10.7 動作執行 — ActionExecutor + Bridge

| 模組 | 檔案 | 行數 | 功能 |
|------|------|------|------|
| **ActionExecutor** | `core/engine/action_executor.py` | 1028 | 動作佇列 + 優先級 + 驗證 + 安全檢查 |
| **ActionExecutionBridge** | `core/action_execution_bridge.py` | 1167 | 自主決策→實際執行的橋接 |

### 10.8 其他 AI 系統

| 模組 | 檔案 | 行數 | 功能 |
|------|------|------|------|
| **AgentManager** | `ai/agents/agent_manager.py` | 720 | 15 個專業子代理管理 |
| **ExecutionManager** | `ai/execution/execution_manager.py` | 533 | 統一執行監控 |
| **ProjectCoordinator** | `ai/dialogue/project_coordinator.py` | 403 | 複雜任務規劃 (DAG) |
| **DocumentBuilder** | `ai/dialogue/document_builder.py` | 356 | 長文檔生成 |
| **AlphaDeepModel** | `ai/compression/alpha_deep_model.py` | 336 | 多演算法壓縮 |
| **UnifiedSymbolicSpace** | `ai/symbolic_space/unified_symbolic_space.py` | 263 | 統一符號空間 |
| **PersonalityManager** | `ai/personality/personality_manager.py` | 162 | 個性管理 |
| **LearningManager** | `ai/learning/learning_manager.py` | 171 | 學習協調 |
| **EnsembleAI** | `ai/ensemble.py` | 345 | 集成 AI 系統 |
| **CrisisSystem** | `ai/crisis/crisis_system.py` | 235 | 危機/緊急系統 |
| **DemoLearningManager** | `ai/learning/demo_learning_manager.py` | 620 | 學習管理器 |
| **TemplateMatcher** | `ai/response/template_matcher.py` | 400 | 回應模板匹配 |
| **DeviationTracker** | `ai/response/deviation_tracker.py` | 359 | 偏差追蹤 |

### 10.9 LLM 路由引擎 — AngelaLLMService

**檔案**: `services/llm/router.py` (1400 行)
**狀態**: ✅ 完整真實實現

```
AngelaLLMService (核心 LLM 路由)
    │
    ├─→ 多後端支援:
    │     Ollama / OpenAI / Anthropic / Google / llama.cpp / ED3N / GARDEN
    │
    ├─→ QueryClassifier (16 種意圖分類)
    ├─→ ModelBus (handler-first 路由)
    ├─→ 健康檢查 + 自動切換
    ├─→ 降級策略: ModelBus → ED3N/GARDEN → NeuroBlender → 模板 → 錯誤字串
    │
    └─→ PromptBuilder 整合:
          bio_state + 6D axes + θ + 公式指標 + 自主決策 + 圖片分析
```

### 10.10 Context 管理系統

**目錄**: `ai/context/` — 11 個檔案, ~2,919 行
**狀態**: ✅ 完整真實實現

| 模組 | 檔案 | 行數 | 功能 |
|------|------|------|------|
| **ModelContext** | `model_context.py` | 343 | LLM 模型上下文管理 |
| **DialogueContext** | `dialogue_context.py` | 345 | 對話上下文追蹤 |
| **MemoryContext** | `memory_context.py` | 267 | 記憶上下文整合 |
| **ToolContext** | `tool_context.py` | 241 | 工具上下文管理 |
| **ContextManager** | `manager_fixed.py` | 307 | 統一上下文管理器 |
| **ContextStorage** | `storage/database.py` | 217 | 持久化存儲 |
| **HAMIntegration** | `integration_with_ham.py` | 189 | HAM 整合 |

### 10.11 其他核心子系統

| 子系統 | 檔案 | 行數 | 功能 |
|--------|------|------|------|
| **CloudSync** | `core/sync/cloud_sync.py` | 468 | 跨裝置記憶同步 + 衝突解決 |
| **ConnectionSession** | `services/connection_session.py` | 457 | WebSocket Session 生命週期 |
| **ExecutionMonitor** | `core/managers/execution_monitor.py` | 684 | 執行監控 + 終端機回應偵測 |
| **AnchorLearning** | `core/engine/anchor_learning.py` | 420 | 語義錨點學習 |
| **PetManager** | `pet/pet_manager.py` | 478 | 寵物管理系統 |
| **AuditLogger** | `security/audit_logger.py` | 455 | 安全審計日誌 |
| **StateHashManager** | `core/state/state_hash_manager.py` | 329 | 狀態雜湊管理 |
| **CardStore** | `core/card/card_store.py` | 214 | 卡片存儲系統 |
| **ModuleManager** | `core/system/module_manager/__init__.py` | 192 | 模組生命週期管理 |
| **SecurityEncryption** | `core/security/encryption.py` | 208 | 加密基礎設施 |
| **KeyValidator** | `core/security/key_validator.py` | 279 | 金鑰驗證 |
| **BodyAdapter** | `core/metamorphosis/body_adapter.py` | 364 | 軀體適應 ( metamorphosis) |
| **SoulCore** | `core/metamorphosis/soul_core.py` | 318 | 靈魂核心 |
| **CausalChain** | `core/tracing/causal_chain.py` | 173 | 因果鏈數據結構 |
| **HardwareDetector** | `shared/utils/hardware_detector.py` | 402 | 硬體偵測 |
| **GoogleDriveService** | `integrations/google_drive_service.py` | 306 | Google Drive 整合 |
| **AtlassianBridge** | `integrations/atlassian_bridge.py` | 288 | Atlassian Jira/Confluence |
| **EconomyManager** | `economy/economy_manager.py` | 204 | 經濟系統 |
| **FormulaEngine** | `ai/formula_engine/__init__.py` | 309 | 公式引擎 |
| **ED3N 內部** | `ai/ed3n/*.py` (16 files) | ~4328 | ED3N 完整子系統 |
| **GARDEN 內部** | `ai/garden/*.py` (4 files) | ~1842 | GARDEN 完整子系統 |
| **HAM 內部** | `ai/memory/ham_memory/*.py` (5 files) | ~1301 | HAM 完整子系統 |

---

## 十一、完整管線流程

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
│ 文字情緒分析      │ │ 刺激     │ │ 6D 狀態讀取   │
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
│   ├─ 【Angela 當前狀態】6D axes                                  │
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

## 十二、系統成熟度總覽

### 核心系統

| 系統 | 檔案 | 行數 | 狀態 | 複雜度 |
|------|------|------|------|--------|
| StateMatrix4D | `core/engine/state_matrix.py` | 1439 | ✅ 真實 | 極高 |
| Composer | `ai/response/composer.py` | 1260 | ✅ 真實 | 高 |
| ActionExecutionBridge | `core/action_execution_bridge.py` | 1167 | ✅ 真實 | 高 |
| EmotionalBlending | `core/bio/emotional_blending.py` | 953 | ✅ 真實 | 高 |
| HSPConnector | `core/hsp/connector.py` | 1105 | ✅ 真實 | 高 |
| ActionExecutor | `core/engine/action_executor.py` | 1028 | ✅ 真實 | 高 |
| IntelligentOpsManager | `ai/ops/intelligent_ops_manager.py` | 958 | ✅ 真實 | 高 |
| DesktopInteraction | `core/engine/desktop_interaction.py` | 1178 | ✅ 真實 | 高 |
| RealTimeMonitor | `core/real_time_monitor.py` | 815 | ✅ 真實 | 高 |
| CodeInspector | `ai/code_inspection/code_inspector.py` | 807 | ✅ 真實 | 高 |
| DigitalLifeIntegrator | `core/life/digital_life_integrator.py` | 869 | ✅ 真實 | 高 |
| BiologicalIntegrator | `core/bio/biological_integrator.py` | 852 | ✅ 真實 | 高 |
| MathRippleEngine | `ai/memory/math_ripple_engine.py` | 892 | ✅ 真實 | 高 | 漣漪/狀態傳遞層（數值結果委託 MathVerifier 單一計算源） |
| NeuroAutoSelector | `ai/response/neuro_auto_selector.py` | 638 | ✅ 真實 | 中 |
| NeuroplasticityCore | `core/bio/neuroplasticity_core.py` | 506 | ✅ 真實 | 高 |
| AgentManager | `ai/agents/agent_manager.py` | 720 | ✅ 真實 | 中 |
| AutonomousLifeCycle | `core/life/autonomous_life_cycle.py` | 724 | ✅ 真實 | 高 |
| SelfGeneration | `core/life/self_generation.py` | 748 | ✅ 真實 | 高 |
| CyberIdentity | `core/life/cyber_identity.py` | 699 | ✅ 真實 | 高 |
| Level5ASISystem | `ai/level5_asi_system.py` | 756 | ✅ 真實 | 高 |
| EventLoopSystem | `core/event_loop_system.py` | 623 | ✅ 真實 | 中 |
| 5 個理論公式 | `core/*.py` | ~2419 | ✅ 真實 | 高 |
| 6 個生命週期模組 | `ai/lifecycle/*.py` | ~2800 | ✅ 真實 | 高 |
| BrowserController | `core/engine/browser_controller.py` | 635 | ✅ 真實 | 中 |
| AudioSystem | `core/engine/audio_system.py` | 630 | ⚠️ 狀態機真/音訊模擬 | 中 |
| ThetaRouter | `core/engine/theta_router.py` | 441 | ✅ 真實 | 中 |
| UserMonitor | `ai/lifecycle/user_monitor.py` | 407 | ✅ 真實 | 中 |
| StatePersistence | `core/engine/state_persistence.py` | 415 | ✅ 真實 | 中 |
| HSP Security | `core/hsp/security.py` | 244 | ✅ 真實 | 中 |
| HSP Versioning | `core/hsp/versioning.py` | 417 | ✅ 真實 | 中 |
| HSP Performance | `core/hsp/performance_optimizer.py` | 393 | ✅ 真實 | 中 |
| MQTTSubscription | `core/hsp/mqtt_subscription_manager.py` | 366 | ✅ 真實 | 中 |
| EmotionAnalyzer | `services/llm/emotion_analyzer.py` | 281 | ✅ 真實(簡單) | 低 |
| RealEdgeTTS | `core/art/real_edge_tts.py` | 268 | ✅ 真實 | 中 |
| CausalTracer | `core/tracing/causal_tracer.py` | 264 | ✅ 真實 | 中 |
| LogicUnit | `ai/memory/lu_logic/logic_unit.py` | 496 | ✅ 真實 | 中 |
| HAMMemoryManager | `ai/memory/ham_memory/ham_manager.py` | 173 | ✅ 真實(薄) | 低 |
| Live2DIntegration | `core/engine/live2d_integration.py` | 116 | ✅ 真實 | 低 |
| GPUAccelerator | `core/hardware/gpu_accelerator.py` | 299 | ✅ 真實 | 中 |
| MetabolicHeartbeat | `core/life/heartbeat.py` | 266 | ✅ 真實 | 中 |
| 14 個 bio 子系統 | `core/bio/*.py` | ~4600 | ✅ 真實 | 高 |
| VisionService | `services/vision_service.py` | 706 | ⚠️ 架構真/方法模擬 | 中 |
| AudioService | `services/audio_service.py` | 41 | ❌ Stub | - |
| TactileService | `services/tactile_service.py` | 66 | ❌ Stub | - |
| ImageGeneration | `ai/agents/specialized/image_generation_agent.py` | 107 | ❌ Stub | - |

**總結**: 核心認知系統 ~31,000+ 行全部是真實實現。主要缺口在感知層（聽覺/觸覺 stub）和部分執行層（繪圖 stub、語音未串接）。

---

## 十三、孤兒系統接線狀態

### 已接線（本次 work session）

| 系統 | 接線方式 | 位置 |
|------|----------|------|
| 11 個 Specialized Agents | AgentAdapter 包裝 → AgentManager 註冊 | `lifespan.py` → `agent_adapter.py` |
| CrisisSystem | 安全閘道 → chat pipeline 情緒分析後 | `chat_routes.py:148-158` |
| CausalReasoningEngine | 回饋學習 → chat response 後 fire-and-forget | `chat_routes.py:253-267` |
| Level5ASISystem | 對齊閘道 → 高危機等級時觸發（lazy init） | `chat_routes.py:170-185` |
| ModelEnsemble | 多模型投票 → router template match 後 | `router.py:582-607` |

### 已删除（16 個 stub/duplicate）

| 文件 | 原因 |
|------|------|
| `services/ai_editor_config.py` | 自宣告 DEPRECATED，7 行 |
| `services/ai_virtual_input_service.py` | 13 行 deprecated stub |
| `services/angela_types.py` | 7 行，`__all__ = []` |
| `services/cloud_api.py` | 2 行 stub |
| `services/external_api.py` | 2 行 stub |
| `services/os_context_service.py` | 自宣告 DEPRECATED |
| `services/sync_queue.py` | 2 行 stub |
| `core/feature_manager.py` | 3 行 stub |
| `core/fault_isolation.py` | 2 行 stub |
| `core/desktop_pet_controller.py` | 3 行 stub |
| `core/demo_feedback_loop.py` | 132 行 demo script |
| `core/feedback_processor.py` | 21 行空文件 |
| `ai/security/ego_guard.py` | 6 行空 class |
| `ai/context/verify_context_system.py` | 47 行 verification script |
| `ai/reasoning/real_causal_reasoning_engine.py` | 與已接線 module 重複 |
| `ai/deep_mapper/` (整個 package) | 自宣告 DEPRECATED |

### 保留但未接線（18 個 — 未來整合）

| 系統 | 行數 | 用途 |
|------|------|------|
| `services/brain_bridge_service.py` | 93 | DigitalLifeIntegrator → metrics 橋接 |
| `core/config_validator.py` | 88 | 環境/配置驗證 |
| `core/real_time_monitor.py` | 1009 | 滑鼠 FS 追蹤、活動識別 |
| `core/event_loop_system.py` | 796 | 異步事件循環 + 優先級佇列 |
| `ai/language_models/daily_language_model.py` | 181 | 日常對話 LM |
| `ai/language_models/router.py` | 195 | 策略型 LLM 路由 |
| `ai/language_models/registry.py` | 104 | 模型註冊/profile 管理 |
| `ai/translation/simultaneous_translation.py` | 108 | 即時翻譯 (GoogleTranslator) |
| `ai/rag/rag_manager.py` | 63 | RAG + FAISS embeddings |
| `ai/execution/execution_manager.py` | 646 | 執行監控/管理 |
| `ai/evaluation/evaluation_db.py` | 128 | SQLite 評估資料庫 |
| `ai/meta/learning_orchestrator.py` | 72 | execute-evaluate-adapt 迴圈 |
| `ai/meta/learning_log_db.py` | 105 | SQLite 學習日誌 |
| `ai/integration/local_cluster_manager.py` | 48 | 本機集群模擬 |
| `ai/service_discovery/service_discovery_module.py` | 64 | 能力廣告處理 |
| `ai/context/demo_context_system.py` | 43 | demo context 邏輯 |
| `ai/context/manager_fixed.py` | 307 | context manager + storage |

---

## 相關文件

| 文件 | 內容 |
|------|------|
| [系統架構概覽](OVERVIEW.md) | 高階架構圖、服務層、整合層 |
| [完整架構](../ARCHITECTURE.md) | 6 層架構詳細文檔 |
| [管線重構計畫](../../PLAN_full_pipeline_architecture.md) | 聊天管線重構 v10 |
| [聊天管線修復](../../PLAN_chat_pipeline_fix.md) | 接線修復計畫 |
