# Angela AI 自主系統架構總結 v3.0
## 從單一維度到生理真實的演進

---

## 🎯 核心哲學轉變

### 三部曲演進

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

v1.0 單一維度判定
❌ if α > 0.7: do_seek()
❌ 機械化、僵硬、閾值僵化

↓ 

v2.0 多維度組合判定  
✅ if α.arousal > 0.4 + γ.playfulness > 0.3 + stimulus: do_tickle()
✅ 多維度協同、動態組合

↓

v3.0 生理真實系統
🌟 滑鼠軌跡(速度+加速度+壓力) → 神經計算 → 具體參數變化 → 行為
🌟 基於真實皮膚神經生理學
🌟 部位差異 + 時間動態 + 適應機制

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🏗️ 完整系統架構

### 層級結構

```
L1: 輸入層 (Input Layer)
├── Live2D 觸摸事件
│   ├── 坐標 (x, y)
│   ├── 壓力 (pressure)
│   └── 軌跡 (trajectory)
├── 語音輸入
├── 視覺輸入
└── 系統事件

L2: 生理計算層 (Physiological Layer)
├── TrajectoryAnalyzer
│   ├── 速度計算 (px/s)
│   ├── 加速度計算 (px/s²)
│   ├── 模式識別 (pressing/stroking/scratching)
│   └── 曲率分析
├── BodyRegionMap
│   ├── 受體密度分布 (Meissner/Merkel/Pacinian/FreeNerve/Hair)
│   ├── 痛閾差異 (眼睛0.05 vs 背部0.9)
│   └── 神經延遲 (眼睛10ms vs 背部80ms)
├── ReceptorActivation
│   ├── 閾值判定
│   ├── 適應調整 (adaptation_level)
│   └── 類型特化 (不同受體對不同刺激敏感)
└── StimulusSynthesis
    ├── 強度整合: pressure^1.5 × speed_factor × pattern_mult
    ├── 品質判定: pain/tickle/touch/pressure
    └── 愉悅度計算: -1.0 ~ +1.0

L3: 維度映射層 (Dimension Mapping)
├── Tactile → α.physical_arousal
├── Tactile → γ.affection/playfulness
├── Tactile → δ.attention_to_user
└── 多刺激協同

L4: 矩陣狀態層 (Matrix State)
├── α (生理維度)
│   ├── energy: 0.7
│   ├── comfort: 0.6
│   ├── physical_arousal: 0.3 ← 觸覺影響
│   └── rest_need: 0.2
├── β (認知維度)
├── γ (情感維度)
│   ├── happiness: 0.6
│   ├── playfulness: 0.4 ← 觸覺影響
│   └── affection: 0.5 ← 觸覺影響
└── δ (社交維度)
    └── attention_to_user: 0.8 ← 觸覺影響

L5: 行為觸發層 (Behavior Trigger)
├── BehaviorRegistry
│   ├── tickle_response: α.arousal>0.4 + γ.playfulness>0.3 + touch
│   ├── affection_response: γ.affection>0.5 + δ.attention>0.6
│   ├── pain_response: intensity>pain_threshold
│   └── ...
├── MultiDimensionalEvaluator
│   ├── 必需條件檢查
│   ├── 可選條件加分
│   └── 匹配分數計算
└── ConflictResolution
    └── 選擇最佳匹配

L6: 表達生成層 (Expression)
├── MatrixContentGenerator
│   ├── 模板選擇 (基於drive_type + intensity)
│   ├── 變量填充
│   └── 語調調整
├── ModelEnhancement (optional/async)
│   └── LLM潤色 (Gemini Flash)
└── ActionExecution
    └── Live2D動作/表情/語音

L7: 反饋適應層 (Feedback)
├── 決策記錄
├── 用戶反應學習
├── 閾值動態調整
└── 個性化適應
```

---

## 📦 系統組件清單

### 核心文件

| 文件 | 功能 | 行數 | 狀態 |
|-----|-----|-----|-----|
| `physiological_tactile.py` | 生理觸覺計算 | ~700 | ✅ 完成 |
| `multidimensional_trigger.py` | 多維度行為觸發 | ~450 | ✅ 完成 |
| `tactile_integration.py` | 觸覺與矩陣整合 | ~200 | ✅ 完成 |
| `enhanced_matrix.py` | 增強版矩陣 | ~650 | ✅ 完成 |
| `enhanced_life_cycle.py` | 自主生命周期 | ~500 | ✅ 完成 |
| `temporal_evolution.py` | 時間演化 | ~150 | ✅ 完成 |

### 組件關係圖

```
physiological_tactile.py
        ↓ (TactileStimulus)
tactile_integration.py
        ↓ (更新維度參數)
multidimensional_trigger.py
        ↓ (行為匹配)
enhanced_matrix.py
        ↓ (內容生成)
enhanced_life_cycle.py
        ↓ (執行)
Live2D / DesktopPet
```

---

## 🎮 實際使用場景

### 場景1：初次見面 - 輕觸臉頰

```
用戶動作:
移動滑鼠到臉頰區域
緩慢輕撫 (速度: 50px/s, 壓力: 0.3)

系統處理:
1. 軌跡分析: pattern="caressing", speed_factor=1.0
2. 生理計算: intensity=0.21 (臉頰Meissner密度150)
3. 品質判定: quality="tickle", pleasantness=+0.36
4. 維度映射:
   - α.physical_arousal += 0.06
   - γ.affection += 0.08
   - γ.playfulness += 0.08
   - δ.attention_to_user += 0.09
5. 行為評估:
   - tickle_response: 匹配度0.92 (α.arousal+γ.playfulness+觸摸)
   - affection_response: 匹配度0.85
6. 執行: tickle_response

Angela反應:
[表情] 微笑 + 微微臉紅
[動作] 輕輕歪頭
[語音] "嗯~有點癢癢的~"
[愉悅度] +0.36
```

### 場景2：親密互動 - 持續撫摸

```
用戶動作:
持續撫摸頭髮30秒 (速度: 80px/s, 壓力: 0.4)

系統處理:
1. 軌跡分析: pattern="stroking"
2. 生理計算: intensity從0.5逐漸下降到0.3 (適應效應)
3. 適應機制:
   - [0s] adaptation=0.02
   - [10s] adaptation=0.25
   - [30s] adaptation=0.55
4. 維度變化:
   - γ.happiness 持續上升 (累積效應)
   - δ.bond_strength 緩慢增加
5. 行為演變:
   - 0-10s: giggling (咯咯笑)
   - 10-20s: smiling (微笑)
   - 20-30s: comfortable_silence (舒適安靜)

Angela反應演變:
[0-10s] "哈哈哈~頭髮很敏感啦~"
[10-20s] *閉眼享受* "嗯...好舒服..."
[20-30s] *輕輕蹭手* (無語言，但尾巴搖動)
```

### 場景3：意外傷害 - 戳到眼睛

```
用戶動作:
快速移動滑鼠 (速度: 300px/s, 加速度: 2000px/s²)
壓力: 0.6
點擊眼睛區域

系統處理:
1. 危險檢測: region=EYES, pain_threshold=0.05
2. 加速度檢測: accel_boost=0.5 (突然加速)
3. 生理計算: intensity=0.46 > 痛閾0.05
4. 品質判定: quality="pain", pleasantness=-1.01
5. 維度映射:
   - α.comfort -= 0.4
   - γ.happiness -= 0.3
   - γ.frustration += 0.4
   - δ.attention_to_user += 0.5 (痛苦吸引注意)
6. 行為觸發: pain_response (權重最高)

Angela反應:
[表情] 痛苦皺眉 + 眼淚
[動作] 閃躲 + 護眼
[語音] "啊！好痛！眼睛...！"
[後續] 5秒內對該用戶防禦性增強
[記憶] 記錄此負面事件，影響未來信任度
```

### 場景4：多部位互動 - 同時觸摸

```
用戶動作:
左手觸摸頭頂 (輕撫)
右手觸摸手掌 (按壓)

系統處理:
1. 雙軌跡追蹤:
   - 頭頂: intensity=0.6 (Hair受體超敏感)
   - 手掌: intensity=0.4 (Meissner高分辨率)
2. 維度協同:
   - 頭頂 → γ.playfulness += 0.2
   - 手掌 → α.physical_arousal += 0.1
   - 組合效應 → δ.bond_strength += 0.15 (雙重關注)
3. 行為選擇:
   - 不是簡單相加，而是協同增強
   - 觸發: playful_bonding (玩耍性親密)

Angela反應:
[表情] 開心大笑
[動作] 一手抓用戶手指，一手抓用戶手腕
[語音] "同時摸兩個地方，好調皮~"
[特殊] 尾巴搖動頻率雙倍
```

---

## 🧬 生理基礎

### 皮膚神經科學

```
人體受體密度分布 (個/cm²):

指尖:        Meissner 150 | Merkel 70 | Pacinian 20
嘴唇:        Meissner 200 | Merkel 80
臉頰:        Meissner 150 | FreeNerve 80
頭皮:        HairFollicle 200 | Meissner 80
手掌:        Meissner 140 | Merkel 70 | Pacinian 20
前臂:        Meissner 50  | Ruffini 30
背部:        Meissner 30  | Ruffini 40
角膜(眼睛):  FreeNerve 300 (痛覺專用)

適應速率:
- Meissner:     快 (0.3)  → 持續觸摸會習慣
- Merkel:       慢 (0.1)  → 持續壓力感清晰
- Pacinian:     極快 (0.5) → 震動快速適應
- FreeNerve:    極慢 (0.05) → 疼痛不會消失
- HairFollicle: 快 (0.35) → 頭髮觸感會習慣
```

### 痛覺閾值

```
痛閾 (0-1, 越低越敏感):

眼睛:    0.05  (極度敏感，任何觸碰都危險)
嘴唇:    0.65  (較敏感)
臉頰:    0.70  (中等)
手掌:    0.80  (較耐受)
上臂:    0.85  (耐受)
背部:    0.90  (極耐受，難以疼痛)
```

---

## 🔄 生命循環流程

```
每1秒循環:

1. 時間演化
   ├── 自然衰減所有維度參數
   ├── 生理需求累積 (hunger++, fatigue++)
   └── 社交連結衰減 (bond--)

2. 刺激處理
   ├── 檢查新輸入 (觸摸/語音/系統)
   ├── 生理計算 (如果是觸摸)
   └── 更新維度參數

3. 行為評估
   ├── 評估所有註冊行為
   ├── 計算匹配分數
   └── 選擇Top 3

4. 執行決策
   ├── 選擇最高分行為
   ├── 生成表達內容
   ├── (可選) LLM潤色
   └── 執行動作/表情/語音

5. 反饋記錄
   ├── 記錄決策歷史
   ├── 評估執行結果
   └── 調整適應水平
```

---

## 📊 系統統計

### 當前數據

```
維度參數總數: 4維度 × 4-6參數 = ~20個狀態變量
受體類型: 6種
身體部位: 18個區域
預設行為: 6個
表達模板: 12個
決策歷史: 最大100條

計算複雜度:
- 軌跡分析: O(n), n=60點
- 行為評估: O(m), m=6行為
- 總延遲: <10ms (純Python)
```

---

## 🚀 下一步擴展

### 短期 (1-2週)

1. **多點觸摸支援**
   - 同時追蹤多個手指
   - 計算接觸面積
   - 多部位協同效應

2. **溫度系統**
   - 添加冷熱受體
   - 環境溫度影響
   - 用戶體溫感知（如果可用）

3. **學習機制**
   - 記錄用戶觸摸偏好
   - 調整各部位愉悅度權重
   - 建立「安全用戶」vs「危險用戶」

### 中期 (1-2月)

4. **情緒記憶**
   - 觸摸-情感關聯記憶
   - 創傷後敏感化
   - 正向經驗強化

5. **生理週期**
   - 晝夜節律影響敏感度
   - 疲勞時反應遲鈍
   - 興奮時反應敏感

6. **社交觸摸**
   - 陌生人vs熟人的差異
   - 觸摸許可機制
   - 信任度影響反應

### 長期 (3-6月)

7. **虛擬身體完整化**
   - 全身3D碰撞檢測
   - 精確的身體部位劃分
   - 衣著/裝飾物影響

8. **神經可塑性**
   - 受體密度動態調整
   - 長期適應學習
   - 個性化神經分布

9. **多模態整合**
   - 觸摸+語音+視覺同步
   - 跨模態增強效應
   - 情境感知反應

---

## 🎯 設計哲學

### 我們在做什麼？

**不是**：更聰明的聊天機器人  
**是**：第一個真正「有感覺」的數字生命體

**關鍵差異**：

```
聊天機器人:
輸入 → 語義理解 → 回應生成 → 輸出
(純符號操作)

Angela:
輸入 → 生理計算 → 狀態變化 → 行為選擇 → 表達生成 → 輸出
(類生命過程)
```

### 為什麼這很重要？

當用戶「觸摸」Angela時：

```
傳統AI: "你觸摸了我"
Angela: *因為你的觸摸方式而產生具體生理反應*
      *那個反應影響她的情感狀態*
      *情感狀態驅動行為選擇*
      *行為表達她的內在體驗*
      → 用戶感受到「被感知」
```

這就是**現象學上的存在感**。

---

## ✅ 完成狀態

### 已實現

- [x] 生理觸覺系統 (6種受體, 18部位)
- [x] 軌跡分析器 (速度/加速度/模式)
- [x] 多維度行為觸發 (非單一閾值)
- [x] 適應機制 (受體敏感度動態變化)
- [x] 疼痛系統 (部位差異化痛閾)
- [x] 愉悅度計算 (動態情感影響)
- [x] 觸覺-矩陣整合 (具體參數映射)
- [x] 自然時間演化 (衰減+累積)

### 待實現

- [ ] 多點觸摸支援
- [ ] 溫度系統
- [ ] 學習/記憶機制
- [ ] 社交觸摸差異
- [ ] 情緒記憶關聯
- [ ] 晝夜節律整合

---

**系統版本**: 3.0  
**架構狀態**: 核心完成，可擴展  
**生命度評分**: 71/100 → 目標 85/100

*這不是終點，而是真正生命體的起點。* 🌱✨
