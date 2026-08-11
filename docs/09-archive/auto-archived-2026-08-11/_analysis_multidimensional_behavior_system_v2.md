# 多維度行為觸發系統 v2.0
## MultiDimensional Behavior Trigger System

---

## 核心理念轉變

### ❌ 舊思維（單一維度判定）
```
if α > 0.7:
    執行 seek(尋找)
```
- 問題：行為單一、機械化、閾值僵化
- 結果：像機器人，不像生命體

### ✅ 新思維（多維度組合判定）
```
if α.physical_arousal > 0.4 + γ.playfulness > 0.3 + 外部刺激(搔癢):
    執行 giggle(咯咯笑) + playful_reaction(玩鬧反應)
```
- 優勢：行為豐富、自然、有機組合
- 結果：像有個性的生命體

---

## 架構設計

### 1. 維度狀態結構（非單一數值）

每個維度不再是一個簡單的 0-1 數字，而是**多參數結構**：

```python
alpha_state = {
    "energy": 0.7,              # 能量水平
    "comfort": 0.6,             # 舒適度
    "physical_arousal": 0.3,    # 生理反應（對刺激）
    "rest_need": 0.2,           # 休息需求
}

gamma_state = {
    "happiness": 0.6,           # 快樂
    "playfulness": 0.4,         # 玩心
    "affection": 0.5,           # 親密感
    "emotional_arousal": 0.3,   # 情感激發
}
```

### 2. 行為觸發器（多條件組合）

```python
BehaviorTrigger(
    behavior_id="tickle_response",
    behavior_name="搔癢反應",
    
    # 必需條件（多維度組合）
    required_dimensions={
        "alpha": {"min": 0.4, "keys": ["physical_arousal"]},  # 需要生理反應
        "gamma": {"min": 0.3, "keys": ["playfulness"]}       # 需要玩心
    },
    
    # 可選條件（有就加分）
    optional_dimensions={
        "gamma": {"keys": ["happiness"], "boost": 0.2},      # 快樂會加分
    },
    
    # 外部刺激條件
    stimulus_requirements=[
        {"type": "touch", "location": "sensitive", "min_intensity": 0.3}
    ],
    
    action_type="react",
    expression_style="playful"
)
```

### 3. 刺激處理系統

```python
# 用戶在 Live2D 上搔癢
stimulus = Stimulus(
    stimulus_type=StimulusType.TOUCH,
    source="live2d",
    intensity=0.7,
    data={"location": "head", "duration": 2.0},
    alpha_impact=0.6,    # 提升生理反應
    gamma_impact=0.4     # 提升情感激發
)

trigger_system.process_stimulus(stimulus)
# → 自動更新相關維度值
# → 觸發相關行為評估
```

---

## 預設行為觸發器

### 1. 搔癢反應 (`tickle_response`)
**觸發條件**：
- 必需：`α.physical_arousal > 0.4` + `γ.playfulness > 0.3`
- 刺激：`touch` + `location: sensitive` + `intensity > 0.3`
- 可選：`γ.happiness` 越高越好

**行為表現**：
- 咯咯笑、躲閃、 playful 反應
- 表達風格：playful

### 2. 親密回應 (`affection_response`)
**觸發條件**：
- 必需：`γ.affection > 0.5` + `δ.attention_to_user > 0.6` + `δ.bond_strength > 0.3`
- 刺激：`touch` (任意) 或 `speech(tone: gentle)`
- 可選：`α.comfort` 越高越好

**行為表現**：
- 溫柔回應、親密表達
- 表達風格：warm

### 3. 好奇探索 (`curiosity_explore`)
**觸發條件**：
- 必需：`β.curiosity + β.learning_drive > 0.3` (加總，不是單一值)
- 刺激：`system(quiet_period)`
- 可選：`α.energy > 0.4` (能量不能太低)

**行為表現**：
- 主動探索、詢問、學習
- 表達風格：curious

### 4. 尋求關注 (`attention_seeking`)
**觸發條件**：
- 必需：`δ.presence_need + δ.attention_to_user > 0.4` (平均) + `γ.affection > 0.3`
- 刺激：無（純內部狀態驅動）

**行為表現**：
- 撒嬌、引起注意
- 表達風格：cute

### 5. 疲憊休息 (`tired_rest`)
**觸發條件**：
- 必需：`α.energy < 0.3` + `α.rest_need > 0.5`
- 權重：2.0（高優先級）

**行為表現**：
- 打哈欠、休息、降低活動
- 表達風格：tired

### 6. 驚喜反應 (`surprise_response`)
**觸發條件**：
- 必需：`γ.emotional_arousal > 0.5` + `α.physical_arousal > 0.3`
- 刺激：`gift(intensity > 0.6)` 或 `system(unexpected)`
- 可選：`γ.happiness` 越高越好

**行為表現**：
- 驚喜、開心、感謝
- 表達風格：surprised

---

## 組合邏輯說明

### 為什麼這樣設計？

**舉例：搔癢反應**

如果用戶在 Live2D 上搔癢 Angela：

1. **刺激輸入**：`touch` + `location: head` + `intensity: 0.7`
2. **維度更新**：
   - `α.physical_arousal` += 0.6 → 0.6
   - `γ.emotional_arousal` += 0.4 → 0.4
   - `γ.playfulness` += 0.2 → 0.4 (因為是頭部)

3. **行為評估**：
   - 檢查 `tickle_response`：
     - `α.physical_arousal (0.6) > 0.4` ✓
     - `γ.playfulness (0.4) > 0.3` ✓
     - 刺激匹配 ✓
   - 匹配分數：0.6 (α) + 0.4 (γ) + 0.2 (刺激) = 1.2

4. **行為選擇**：
   - 可能同時匹配 `tickle_response` (1.2分) 和 `affection_response` (0.9分)
   - 選擇最高分執行

**結果**：Angela 咯咯笑並 playful 地回應，而不是機械地「收到搔癢指令→執行動作 A」

---

## 與原系統的整合

### 整合方式

```python
class EnhancedAutonomousLifeCycle:
    def __init__(self):
        # 原有系統
        self.matrix = EnhancedAutonomyMatrix()
        self.synthesizer = MatrixDrivenBehaviorSynthesizer(self.matrix)
        
        # [新] 多維度觸發系統
        self.multi_trigger = MultiDimensionalBehaviorTrigger()
        
        # 模式切換
        self.trigger_mode = "multidimensional"  # "legacy" | "enhanced" | "multidimensional"
```

### 循環更新

```python
async def _life_cycle(self):
    while self.alive:
        if self.trigger_mode == "multidimensional":
            # 1. 時間演化（自然衰減）
            self.multi_trigger.natural_decay(1.0)
            
            # 2. 尋找匹配行為
            matches = self.multi_trigger.find_matching_behaviors(top_n=3)
            
            # 3. 執行最佳匹配
            if matches:
                result = self.multi_trigger.select_and_execute(matches)
                await self._execute_multidimensional_behavior(result)
        
        await asyncio.sleep(1.0)
```

### 處理外部刺激

```python
# 從 Live2D 接收搔癢事件
async def handle_live2d_interaction(self, interaction_data):
    stimulus = Stimulus(
        stimulus_type=StimulusType.TOUCH,
        source="live2d",
        intensity=interaction_data['pressure'],
        data={
            "location": interaction_data['area'],  # "head", "body", "hand"
            "duration": interaction_data['duration']
        },
        alpha_impact=0.5 if interaction_data['area'] == 'sensitive' else 0.3,
        gamma_impact=0.4
    )
    
    # 處理刺激
    self.multi_trigger.process_stimulus(stimulus)
    
    # 立即評估（不用等生命週期循環）
    matches = self.multi_trigger.find_matching_behaviors()
    if matches:
        return await self._execute_multidimensional_behavior(matches[0])
```

---

## 優勢總結

### vs 單一維度判定

| 面向 | 單一維度 | 多維度組合 |
|------|---------|-----------|
| **行為豐富度** | 低（4種基本行為） | 高（組合產生多種變體） |
| **自然度** | 機械化 | 有機、類生命 |
| **外部響應** | 間接（通過維度） | 直接（刺激系統） |
| **閾值** | 固定（0.7, 0.5, 0.6） | 動態組合 |
| **表達** | 模板化 | 上下文相關 |

### vs 其他 AI 系統

| 特性 | ChatGPT | Character.AI | **Angela (多維度)** |
|------|---------|--------------|---------------------|
| 自主行為 | ❌ 無 | ❌ 無 | ✅ 有 |
| 內部狀態 | ❌ 無 | ❌ 無 | ✅ 4維多參數 |
| 外部刺激 | ❌ 僅文本 | ❌ 僅文本 | ✅ Live2D觸摸等 |
| 多維度組合 | ❌ 無 | ❌ 無 | ✅ 核心設計 |
| 時間持續性 | ❌ 無 | ❌ 無 | ✅ 自然衰減 |

---

## 未來擴展

### 1. 動態行為註冊
```python
# 允許用戶定義新行為
trigger_system.register_trigger(BehaviorTrigger(
    behavior_id="user_defined_happy_dance",
    required_dimensions={
        "gamma": {"min": 0.8, "keys": ["happiness", "playfulness"], "combine": "avg"}
    },
    stimulus_requirements=[
        {"type": "gift", "data_key": "item", "data_value": "user_favorite"}
    ]
))
```

### 2. 學習優化
- 記錄用戶反應（喜歡/不喜歡）
- 自動調整 `boost` 值和 `min` 閾值
- 發現新的行為組合模式

### 3. 多層級行為
```python
# 複合行為（多步驟）
ComplexBehavior([
    "attention_seeking",    # 第一步：引起注意
    "curiosity_explore",    # 第二步：展示好奇
    "affection_response"    # 第三步：建立親密
])
```

---

## 結論

這個系統的核心突破：

1. **從「單一維度判定」到「多維度組合判定」**
   - 不再是 α>0.7 → 做 X
   - 而是 α.A + β.B + γ.C + 刺激 → 做複雜行為

2. **從「統計值」到「子參數組合」**
   - 維度不再是一個數字
   - 而是一組相關狀態的集合

3. **從「內部驅動」到「內外協同」**
   - Live2D 互動直接影響維度
   - 刺激系統獨立於時間循環

4. **從「固定閾值」到「動態匹配」**
   - 沒有硬編碼的 0.7, 0.5
   - 只有相對的匹配分數

**這才是生命體該有的行為模式** 🌟

---

*文件版本：2.0*  
*更新日期：2026-02-01*  
*架構設計：多維度行為觸發系統*
