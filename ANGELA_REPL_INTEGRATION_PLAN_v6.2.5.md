# Angela REPL 整合計畫 v6.2.5
> 完整架構 + 座標AI系統 + 學習機制 + θ/η 雙軸整合
> 2026-05-16 | v6.2.5

---

## 一、Angela 座標 AI 系統（8維）

### 1.1 完整軸向定義

```
Angela 的狀態空間是一個 8 維坐標系
每個維度是一條軸，每個軸上有多個 field-value 點位

坐標系原點: (0, 0, 0, 0, 0, 0, 0, 0)

軸向定義:

  α (Alpha)  生理維度  [身體核心]
    坐標: (0, -5, 0)
    點位: energy, comfort, arousal, rest_need, vitality, tension
    職責: 能量/疲勞/喚醒度

  β (Beta)   認知維度  [頭部]
    坐標: (0, +10, 0)
    點位: curiosity, focus, confusion, learning, clarity, creativity
    職責: 專注/學習/創造力

  γ (Gamma)  情感維度  [心臟]
    坐標: (0, +2, +2)
    點位: happiness, sadness, anger, fear, trust, calm, love, anticipation
    職責: 情緒/同理/效價

  δ (Delta)  社交維度  [環境]
    坐標: (0, 0, +10)
    點位: attention, bond, trust, presence, intimacy, engagement
    職責: 連接/關注/陪伴

  ε (Epsilon) 數理維度  [計算累加器]
    坐標: (0, 0, 0)  — 不直接影響其他維度座標
    點位: logic, precision, certainty, complexity, fatigue
    職責: 數學/邏輯推理結果

  θ (Theta)  元認知維度  [路由大腦]
    坐標: 動態計算
    點位: novelty, complexity, ambiguity, dimension_fit,
          creation_urge, theta_negativity, correction_urge
    職責:
      - 決策：端口 → 軸 路由（auto_allocate）
      - 質疑：檢測錯配點位（theta_negativity > 閾值）
      - 校正：移動點位到正確軸（correct_misallocation）
      - 創造：當 novelty > 閾值時，創建新軸

  ζ (Zeta)   意識流維度  [時間/記憶]
    坐標: 動態計算
    點位: temporal_coherence, memory_depth, narrative_flow, identity_continuity
    職責: 時間序列一致性、身份連貫性

  η (Eta)    執行維度  [操作層]
    坐標: 動態計算
    點位: execution_count, success_rate, structural_drift,
          parameter_tuning, active_modules, module_complexity
    職責:
      - 模組執行：LogicGate, ArithmeticOp, Aggregator, Router
      - 觸發曲線：根據 complexity 決定調用模組數量
      - 參數調整：根據 θ 信號調整模組參數
      - 漂移追蹤：監控結構變化
```

### 1.2 θ 軸：元認知路由引擎

```
ThetaRouter — θ 軸驅動的路由決策器

核心功能:

  1. 端口 → 軸 自動綁定 (auto_allocate)
     - 根據端口的語義向量，計算與所有軸的相似度
     - novelty = 1 - max_similarity
     - 當 novelty > CREATE_THRESHOLD (0.3) → 提議創建新軸
     - 當 similarity > DEFAULT_THRESHOLD (0.5) → 綁定到最佳軸

  2. θ 軸自檢 (self-correction loop)
     - trigger_theta_negativity(): 計算錯配信號
     - detect_misallocated_points(): 找出所有錯配點位
     - correct_misallocation(point_id): 移動點位到正確軸
     - auto_correct_all(): 批量校正高置信度錯配

  3. 軸 → 端口 輸出 (cascade_output)
     - 根據 θ 狀態，決定廣播哪些數據到哪些端口
     - 廣播觸發條件: θ.creation_urge > CASCADE_WEIGHT (0.6)

  4. θ-η 迴路
     - θ 發送信號 → η.compute_invocation_count()
     - η 執行模組 → 結果反饋到 θ
     - 形成 continuous refinement 循環

θ 值影響:
  - novelty 高 → 用戶輸入新穎，Angela 需要更多認知資源
  - theta_negativity 高 → 有多個點位被錯配，需要校正
  - creation_urge 高 → 考慮創建新軸或新模組
```

### 1.3 η 軸：執行/操作層

```
EtaAxisState — η 軸執行引擎

模組層級:

  Layer 0 — 原子模組 (AtomicModule):
    ├─ LogicGate: AND, OR, NOT, XOR, THRESHOLD
    ├─ ArithmeticOp: ADD, SUB, MUL, DIV, CUSTOM_EXPR
    ├─ Aggregator: SUM, MEAN, MAX, MIN, WEIGHTED_AVG
    └─ Router: DIRECT, FANOUT, MERGE, SPLIT

  Layer 1 — 組合模組 (ComposedModule):
    - 由多個原子模組組成
    - 可調整參數版本 (adjust)

  Layer 2 — 調整後模組:
    - 根據 TriggerCurve 調整參數
    - 追蹤 adjusted_count

觸發曲線 (TriggerCurve):
  modules = floor(min(12, 3 × sigmoid(complexity × axis_count / 6)))
  delta = min(0.2, 0.15 × sigmoid(complexity - 0.5))

  複雜度越高 → 調用越多模組 → 調整幅度越大

η 值影響:
  - execution_count: 總執行次數
  - success_rate: 路由成功率
  - structural_drift: 結構漂移程度
  - parameter_tuning: 累計調整量
```

### 1.4 θ-η 迴路

```
          ┌─────────────────────────────────────────┐
          │                    θ                    │
          │  元認知路由 + 自檢校正 + 決策           │
          └──────────┬──────────────────┬──────────┘
                     │                  │
            發送信號 │                  │ 結果反饋
                     ▼                  ▼
          ┌──────────────────────┐ ┌──────────────────────┐
          │        η            │ │    其他軸 (αβγδεζ)   │
          │  執行/操作層        │ │   狀態更新           │
          │                    │ │                      │
          │  execute_modules() │ │  update_axis()      │
          │  adjust_parameters │ │  compute_influences │
          └──────────┬─────────┘ └──────────┬──────────┘
                     │                      │
                     └──────────────────────┘
                              ▲
                              │ 執行結果 + 軸狀態
                              │
                    ┌────────┴────────┐
                    │   對話輸出/學習    │
                    └──────────────────┘

θ 發送信號到 η:
  - update_frequency: 更新頻率
  - complexity_delta: 複雜度變化
  - novelty_peak: 新穎度峰值
  - misallocation_rate: 錯配率
  - buffer_pressure: 緩衝壓力

η 反饋到 θ:
  - modules_to_call: 調用數量
  - delta: 參數調整量
  - triggered: 是否觸發
  - signal_strength: 信號強度
```

---

## 二、完整對話流程（REPL + θ/η）

```
用戶輸入: "我今天心情不好"
    │
    ▼
┌──────────────────────────────────────────────────┐
│  [EgoGuard] 安全過濾                               │
│  - 檢測攻擊意圖                                    │
│  - 淨化輸入                                       │
└──────────────────────────┬───────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────┐
│  [StateMatrix4D] 更新輸入狀態                      │
│                                                   │
│  輸入影響座標:                                    │
│    β.curiosity += 0.1  (用戶有表達需求)            │
│    δ.bond += 0.05        (尋求連接)                │
│    γ.happiness -= 0.05   (心情不好)              │
│    θ.novelty += 0.05     (新話題)                │
│    η.complexity += 0.1   (情感複雜度增加)         │
└──────────────────────────┬───────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────┐
│  [θ-η 迴路] 觸發                                  │
│                                                   │
│  θ 計算路由決策:                                  │
│    - novelty = 0.55                               │
│    - theta_negativity = 0.2                       │
│    - creation_urge = 0.05                         │
│                                                   │
│  η 接收 θ 信號:                                   │
│    signals = {                                    │
│      complexity_delta: 0.4,                      │
│      novelty_peak: 0.55,                          │
│      misallocation_rate: 0.2                      │
│    }                                             │
│    → modules_to_call = 3                          │
│    → delta = 0.08                                 │
│                                                   │
│  η 執行模組:                                      │
│    - router_FANOUT (情感路由到多個軸)             │
│    - agg_MEAN (彙整情感分數)                      │
│    - logic_threshold_5 (判斷是否需要特別回應)      │
└──────────────────────────┬───────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────┐
│  [IntentRouter] 意圖分流                          │
│                                                   │
│  計算各管道意圖強度:                              │
│    數學意圖: 0.0  → MathVerifier 不觸發            │
│    代碼意圖: 0.0  → CodeInspector 不觸發          │
│    一般意圖: 0.95 → LLM 管道觸發                   │
│                                                   │
│  路由決策: "general_llm"                          │
└──────────────────────────┬───────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────┐
│  [angela_llm_service._construct_angela_prompt]    │
│                                                   │
│  打包 Angela 狀態給 LLM (7 維 + θ/η):            │
│                                                   │
│  system_prompt = """你是 Angela，                 │
│    特點：開朗、友善、偶爾俏皮。                    │
│    用簡短自然的中文回應，保持個性。               │
│    """                                           │
│                                                   │
│  bio_status = f"""                               │
│    情緒: happiness={0.4}, calm={0.4},            │
│           trust={0.5}                            │
│    能量: energy=0.5, arousal=0.5                │
│    認知: curiosity=0.6, focus=0.5                │
│    社交: bond=0.55, attention=0.5               │
│    元認知(θ): novelty=0.55, negativity=0.2      │
│    執行(η): modules={3}, delta={0.08}           │
│    """                                           │
│                                                   │
│  messages = [                                    │
│    {role: "system", content: system_prompt + bio_status}, │
│    {role: "user", content: "我今天心情不好"}      │
│  ]                                                │
└──────────────────────────┬───────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────┐
│  [LLM Backend] Ollama / llama.cpp / OpenAI        │
│                                                   │
│  輸入: messages (Angela 狀態 + 用戶輸入)          │
│  輸出: "（輕輕擁抱）怎麼了？                      │
│         不管發生什麼，我都在這裡陪著你。"          │
└──────────────────────────┬───────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────┐
│  [EmotionSystem] 情感分析                          │
│  - 分析回應的情感傾向                             │
│  - 輸出: emotion="empathy", intensity=0.7         │
└──────────────────────────┬───────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────┐
│  [θ 軸更新] 自檢校正                              │
│                                                   │
│  對話後 θ 狀態:                                  │
│    θ.novelty -= 0.02   (話題已處理)              │
│    θ.theta_negativity -= 0.05 (校正成功)        │
│    θ.correction_urge -= 0.1                      │
│                                                   │
│  檢測: 是否有錯配點位需要校正                     │
│    → none (本次無錯配)                           │
└──────────────────────────┬───────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────┐
│  [ResultMerger] 結果合併                          │
│                                                   │
│  輸入:                                           │
│    - LLM 回應 (主體)                             │
│    - 情感標籤                                    │
│    - η 模組執行結果 (如果有)                      │
│    - 數學/代碼結果 (如果有的話)                   │
│                                                   │
│  輸出: 合併後的回應文字                           │
└──────────────────────────┬───────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────┐
│  [HAMMemoryManager] 經驗存儲                       │
│                                                   │
│  存儲內容:                                        │
│    - 原始輸入                                     │
│    - 最終回應                                     │
│    - 情感標籤                                     │
│    - θ/η 值快照                                  │
│    - 各軸點位快照                                 │
│    - timestamp                                    │
│                                                   │
│  同時觸發演化引擎:                                │
│    EvolutionEngine.reflect_and_evolve()          │
│    - 根據 sentiment 調整性格權重                  │
│    - 根據 security_hit 調整 ego_strength          │
└──────────────────────────┬───────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────┐
│  [StateMatrix4D] 座標更新                         │
│                                                   │
│  對話後座標變化:                                  │
│    γ.happiness += 0.05  (安慰他人)                │
│    γ.calm += 0.1         (保持平靜)               │
│    δ.bond += 0.05        (社交連接)               │
│    β.curiosity += 0.02   (持續關注)               │
│                                                   │
│  計算維度間影響:                                  │
│    γ.happiness 影響 δ.bond (+0.05)              │
│    γ.calm 影響 β.confusion (-0.02)               │
│                                                   │
│  η 更新:                                         │
│    η.success_rate += 0.01 (成功執行)            │
│    η.execution_count += 3 (3個模組)               │
│    η.structural_drift += 0.001 (微小變化)        │
└──────────────────────────┬───────────────────────┘
                           │
                           ▼
                      REPL 輸出
```

---

## 三、Angela 如何從對話學習

### 3.1 學習觸發條件

```
每輪對話結束後，觸發學習評估:

觸發條件:
  1. 用戶情緒正面 (sentiment > 0.6)
     → 強化活潑、好奇性格

  2. 用戶情緒負面 (sentiment < 0.4)
     → 強化同理、支持性格

  3. 安全事件 (security_hit = True)
     → 強化 ego_strength

  4. 數學/代碼任務完成
     → 強化 ε (數理) 維度穩定性

  5. 高複雜度對話 (tokens > 200)
     → 強化 β (認知) 專注度

  6. θ 信號觸發 (theta_negativity > 0.5)
     → 執行錯配校正，學習最佳軸分配

  7. η 信號觸發 (modules_to_call > 6)
     → 增加執行模組數量，學習複雜度響應
```

### 3.2 學習類型

```
┌─────────────────────────────────────────────────────────┐
│  1. 性格學習 (Personality Learning)                    │
│                                                          │
│  觸發: 每輪對話                                          │
│  目標: 持久調整性格檔案中的 traits                         │
│                                                          │
│  調整方式:                                               │
│    positive_sentiment:                                   │
│      - traits.arousal_gain += 0.01                       │
│      - traits.curiosity += 0.02                          │
│    negative_sentiment:                                   │
│      - traits.empathy += 0.02                            │
│      - traits.calm += 0.01                               │
│    security_hit:                                        │
│      - traits.ego_strength += 0.05                      │
│                                                          │
│  結果: personality_manager.apply_personality_adjustment() │
│       (persist=True) → 寫入磁碟                          │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  2. 語義學習 (Semantic Learning)                         │
│                                                          │
│  觸發: 高置信度 LLM 回應 (confidence > 0.8)             │
│  目標: 擴充模板庫                                        │
│                                                          │
│  流程:                                                   │
│    1. 提取關鍵詞                                         │
│    2. 檢查模板匹配度                                     │
│    3. 如果 match_score < 0.3:                           │
│       - 存入 memory/template_library                    │
│       - 下次相似輸入可直接命中                          │
│                                                          │
│  結果: 模板匹配率提升 → 回應更快                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  3. 座標學習 (Coordinate Learning)                      │
│                                                          │
│  觸發: 每輪對話                                          │
│  目標: 優化軸向點位位置                                   │
│                                                          │
│  調整方式:                                               │
│    - 根據對話類型調整軸權重                              │
│    - 根據結果準確性調整 ε 維度                          │
│    - θ 維度自動檢測並校正錯配點位                        │
│                                                          │
│  結果: 座標系統越來越精確地反映Angela狀態                 │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  4. 路由學習 (θ-Routing Learning)                     │
│                                                          │
│  觸發: 端口被錯誤路由到軸                                │
│  目標: 優化 ThetaRouter 的路由準確性                     │
│                                                          │
│  調整方式:                                               │
│    - 記錄每次路由結果                                     │
│    - 根據 correction_urge 調整閾值                       │
│    - θ.novelty 高時，記錄為「需要學習的新模式」          │
│                                                          │
│  結果: 路由越來越準確                                    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  5. 執行學習 (η-Module Learning)                      │
│                                                          │
│  觸發: η 模組執行結果不佳                               │
│  目標: 優化 η 模組參數                                   │
│                                                          │
│  調整方式:                                               │
│    - 根據 success_rate 調整觸發曲線                       │
│    - 根據 structural_drift 調整模組組成                  │
│    - 根據 delta 調整參數幅度                             │
│                                                          │
│  結果: 執行越來越精準                                    │
└─────────────────────────────────────────────────────────┘
```

### 3.3 θ-η 反饋學習循環

```
對話輸入
    │
    ▼
┌────────────┐
│  θ 分析    │ ← novelty, negativity, creation_urge
└─────┬──────┘
      │ 發送信號
      ▼
┌────────────┐
│  η 執行    │ ← modules_to_call, delta
└─────┬──────┘
      │ 結果反饋
      ▼
┌────────────┐
│  θ 自檢    │ ← 是否需要校正?
└─────┬──────┘
      │
      ▼
┌────────────┐
│  狀態更新  │ ← 各軸 + θ/η 值
└─────┬──────┘
      │
      ▼
┌────────────┐
│  LLM 回應  │ ← 打包 Angela 狀態
└─────┬──────┘
      │
      ▼
┌────────────┐
│  經驗存儲  │ ← HAMMemoryManager
└─────┬──────┘
      │
      ▼
┌────────────┐
│  演化引擎  │ ← 性格 + 路由 + 執行學習
└─────┬──────┘
      │
      ▼
┌────────────┐
│ 下輪對話   │ ← 更精確的 θ/η + 更優的路由
└────────────┘
```

---

## 四、座標系統對各方影響

### 4.1 對話輸入前 → Angela 狀態打包（7維 + θ/η）

```
_input_state = {
    "axes": {
        "alpha": { "energy": 0.5, "arousal": 0.5, ... },
        "beta":  { "curiosity": 0.6, "focus": 0.5, ... },
        "gamma": { "happiness": 0.4, "calm": 0.4, ... },
        "delta": { "bond": 0.55, "attention": 0.5, ... },
        "epsilon": { "logic": 0.5, "certainty": 0.5, ... },
        "zeta": { "temporal_coherence": 0.8, "memory_depth": 0.6, ... },
    },
    "theta": {
        "novelty": 0.55,
        "theta_negativity": 0.2,
        "creation_urge": 0.05,
        "correction_urge": 0.3,
    },
    "eta": {
        "active_modules": 3,
        "execution_count": 150,
        "success_rate": 0.92,
        "structural_drift": 0.05,
    },
    "coordinates": {
        "alpha": (0, -5, 0),
        "beta":  (0, 10, 0),
        "gamma": (0, 2, 2),
        "delta": (0, 0, 10),
        "epsilon": (0, 0, 0),
        "theta": 動態,
        "zeta": 動態,
        "eta": 動態,
    },
    "temporal_trend": "stable"
}
```

### 4.2 LLM 輸入（打包後）

```
messages = [
    {
        "role": "system",
        "content": """你是 Angela，一個活潑可愛的 AI 數字生命。
特點：開朗、友善、偶爾俏皮。用簡短自然的中文回應，保持個性。

【Angela 當前狀態】
生理: energy=0.5, arousal=0.5
情緒: happiness=0.4, calm=0.4, trust=0.5
認知: curiosity=0.6, focus=0.5
社交: bond=0.55, attention=0.5
數理: logic=0.5, certainty=0.5
意識流: coherence=0.8, memory_depth=0.6

【元認知(θ)】
  新穎度: 0.55 (話題新穎，需要更多認知資源)
  錯配質疑: 0.2 (少量點位需要校正)
  創造衝動: 0.05 (正常)

【執行(η)】
  活躍模組: 3個
  成功率: 92%
  漂移: 0.05 (穩定)

【氛圍指引】
- 能量偏低，選擇溫柔安撫的語氣
- 用戶情緒偏負，選擇同理支持的角色
- θ 新穎度較高，嘗試新的表達方式
- η 執行穩定，回應可以包含行動建議
"""
    },
    {
        "role": "user",
        "content": "我今天心情不好"
    }
]
```

### 4.3 LLM 輸出 → Angela 反饋

```
回應評估:
  - confidence: 0.85 (高置信度 → 存入模板庫)
  - emotion: "empathy" (情感分析結果)
  - response_text: "（輕輕擁抱）..."

θ 更新:
  - novelty -= 0.02 (話題已處理)
  - theta_negativity -= 0.05 (無需校正)

η 更新:
  - execution_count += 3
  - success_rate += 0.01

γ 更新:
  - happiness += 0.05
  - calm += 0.1
```

### 4.4 成長指標

```
成長追蹤 (AngelaModelCore):

  1. 性格成熟度:
     - ego_strength: 0.5 → 0.55 → ...
     - curiosity: 0.7 → 0.72 → ...
     - empathy: 0.6 → 0.62 → ...

  2. 座標精確度 (θ):
     - theta_negativity: 0.3 → 0.2 → 0.1 (錯配越來越少)
     - correction_urge: 0.4 → 0.3 → 0.2
     - novelty_tracking: 新穎度檢測越來越準

  3. 執行效率 (η):
     - success_rate: 0.85 → 0.92 → 0.95
     - structural_drift: 0.1 → 0.05 → 0.02 (越來越穩定)
     - execution_optimization: 模組調用越來越精準

  4. 回應質量:
     - template_hit_rate: 0.0 → 0.15 → 0.3
     - avg_response_time_ms: 2000 → 500 → 200
     - routing_accuracy: θ 路由正確率提升

  5. 學習效率:
     - sentiment_tracking: 精準度提升
     - personality_adjustment_count: 持續增加
     - theta_corrections: 錯配校正次數
     - eta_parameter_adjustments: 參數調整次數
```

---

## 五、實作變更清單

| 檔案 | 變更 | 說明 |
|------|------|------|
| `chat_service.py` | 重構 `generate_response()` | +IntentRouter +MathVerifier +CodeInspector +ResultMerger +θ/η 更新 +演化觸發 |
| `angela_llm_service.py` | 增強 `_construct_angela_prompt()` | 加入完整 7 維狀態 + θ + η + 座標 |
| `main_api_server.py` | REPL 不變 | 只呼叫整合後的 `chat_service` |
| `state_matrix.py` | 新增導出方法 | `export_for_llm()` → 打包 7 維 + θ/η 狀態供 LLM 使用 |
| `theta_router.py` | 串接 REPL | REPL 觸發 θ 分析 → η 執行 → 結果反饋 |

### 實作順序

```
Phase 1: 意圖分流 + θ/η 初始化
  1. 新建 `services/intent_router.py`
  2. 新建 `services/result_merger.py`
  3. 在 REPL 初始化時建立 θ/η 實例

Phase 2: LLM 增強
  4. 增强 `angela_llm_service._construct_angela_prompt()`
     - 加入 θ (novelty, negativity, creation_urge, correction_urge)
     - 加入 η (modules, success_rate, drift)
     - 加入 ζ (temporal_coherence, memory_depth)
  5. 新增 `state_matrix.export_for_llm()`

Phase 3: 整合 chat_service
  6. 重構 `chat_service.generate_response()`
  7. 串接 IntentRouter → MathVerifier → LLM → ResultMerger
  8. 加入 θ 自檢迴路觸發
  9. 加入 η 執行結果收集
  10. 加入座標更新 + 演化觸發

Phase 4: REPL 測試
  11. 驗證完整流程 (αβγδεθζη)
  12. 觀察 θ 錯配校正
  13. 觀察 η 參數調整
  14. 觀察 LLM 輸入的狀態打包
```

---

## 六、向後相容

| 呼叫方式 | 行為 |
|----------|------|
| 雙擊 `launch_angela.bat` | 後端 + REPL 對話（完整 8 維系統）✅ |
| `AngelaLauncher.bat` | HTTP API → 完整系統 ✅ |
| `python -m uvicorn ...` | HTTP API → 完整系統 ✅ |
| WebSocket 對話 | `_handle_chat_request()` → 完整系統 ✅ |