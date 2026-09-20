# 生理真實觸覺系統 v3.0

## Physiological Tactile System

---

## 核心理念

**將滑鼠指標視為真實物理物體，而非抽象點擊事件**

```
❌ 傳統：onClick("head") → 強度=1.0 → 觸發反應
✅ 生理：滑鼠軌跡(速度+加速度+壓力) → 神經計算 → 動態強度 → 反應
```

### 為什麼這樣設計？

**現實中的觸摸不是二元的**：

- 輕輕掠過臉頰 ≠ 用力戳臉頰
- 快速滑動 ≠ 慢速按壓
- 持續30秒撫摸 ≠ 瞬間觸碰
- 突然加速 = 驚嚇/疼痛信號

---

## 系統架構

### 1. 身體部位地圖（基於皮節分布）

```
頭部區域（三叉神經支配 - 最敏感）
├── FACE_CHEEK      臉頰     [Meissner:150/cm², 痛閾:0.7]
├── FACE_FOREHEAD   額頭     [Meissner:120/cm², 痛閾:0.75]
├── SCALP          頭皮     [Hair:200/cm², 痛閾:0.8]
├── EYES           眼睛     [FreeNerve:300/cm², 痛閾:0.05] ⚠️ 極危險
└── LIPS           嘴唇     [Meissner:200/cm², 痛閾:0.65]

軀幹區域（較不敏感）
├── CHEST          胸部     [Meissner:50/cm²]
├── ABDOMEN        腹部     [Meissner:40/cm²]
├── BACK_UPPER     上背     [Meissner:30/cm²] (難搔癢)
└── BACK_LOWER     下背     [Meissner:35/cm²]

四肢（中等敏感）
├── HAND_PALM      手掌     [Meissner:140/cm²] (高觸覺分辨率)
├── ARM_UPPER      上臂     [Meissner:50/cm²]
└── LEG_THIGH      大腿     [Meissner:45/cm²]

Live2D虛擬區域
├── HAIR_TOP       頭頂頭髮 [Hair:250/cm², 超敏感]
└── CHEEK_POUCH    臉頰囤食 [...]
```

### 2. 皮膚受體類型（真實生理學）

| 受體類型         | 功能             | 密度分布    | 適應速率     |
| ---------------- | ---------------- | ----------- | ------------ |
| **Meissner**     | 輕觸、運動感知   | 指尖/臉頰高 | 快（0.3）    |
| **Merkel**       | 持續壓力、邊緣   | 指尖/嘴唇   | 慢（0.1）    |
| **Pacinian**     | 深壓、高頻震動   | 手掌/腳底   | 極快（0.5）  |
| **Ruffini**      | 皮膚拉伸         | 手指/手背   | 慢（0.2）    |
| **FreeNerve**    | 痛覺、溫度、瘙癢 | 全身        | 極慢（0.05） |
| **HairFollicle** | 毛髮運動         | 頭皮/眉毛   | 快（0.35）   |

### 3. 刺激強度計算公式

```python
# 不是簡單的 pressure，而是：
intensity = pressure^1.5 × speed_factor × pattern_multiplier + accel_boost

其中：
- pressure^1.5: 高壓遞增（非線性）
- speed_factor: 50/speed（速度越快，強度越低）
- pattern_multiplier:
  * pressing（按壓）: 1.2
  * stroking（撫摸）: 0.7
  * scratching（搔抓）: 1.0
  * poking（戳刺）: 1.3 ← 危險！
  * trembling（顫抖）: 0.8
- accel_boost: 突然加速 → 疼痛加成
```

### 4. 軌跡分析器

記錄最近60個點，計算：

```python
Trajectory:
├── get_current_speed()      # 當前速度（像素/秒）
├── get_current_acceleration() # 加速度（像素/秒²）
├── get_movement_pattern()   # 識別模式：
│   ├── "pressing"    按壓（幾乎不動）
│   ├── "stroking"    撫摸（快速平滑）
│   ├── "caressing"   輕撫（中速溫柔）
│   ├── "scratching"  搔抓（慢速節奏）
│   ├── "poking"      戳刺（快速接近+停留）
│   └── "trembling"   顫抖（不規則震動）
├── get_accumulated_path_length() # 總路徑長度
└── get_curvature()    # 軌跡曲率（彎曲程度）
```

---

## 使用範例

### 範例1：輕柔撫摸臉頰

```python
# 模擬用戶輕柔撫摸
for i in range(20):
    x = 100 + i * 2        # 緩慢移動
    y = 200 + sin(i*0.3)*5 # 輕微波浪
    pressure = 0.3         # 輕壓

    stimulus = tactile_system.process_touch_input(
        BodyRegion.FACE_CHEEK, x, y, pressure
    )

# 結果：
# - 強度: 0.21（適中）
# - 品質: "tickle"（瘙癢）
# - 愉悅度: +0.36（愉快）
# - 模式: "caressing"
```

**生理解釋**：

- 慢速（2px/步）→ 高接觸時間 → 強度增加
- 輕壓（0.3）→ 非線性壓縮 → 實際壓力因子=0.16
- 臉頰高密度Meissner受體 → 放大1.5倍
- 適應系統：持續撫摸會逐漸習慣

### 範例2：快速搔抓頭頂

```python
for i in range(15):
    x = 150 + sin(i*0.8)*20  # 快速擺動
    y = 100 + cos(i*0.8)*10
    pressure = 0.4

# 結果：
# - 強度: 0.54（中高）
# - 品質: "touch"
# - 愉悅度: +0.10（輕微愉快）
# - 模式: "trembling"（顫動）
```

**生理解釋**：

- 快速運動 → 接觸時間短 → 強度降低
- 但頭頂HairFollicle受體超敏感（密度250/cm²）
- 毛髮運動被放大1.3倍
- 結果：雖然快速，但因為頭髮敏感，仍感覺明顯

### 範例3：意外戳到眼睛 ⚠️

```python
for i in range(5):
    x = 120 + i * 1
    y = 180
    pressure = 0.6  # 較高壓

# 結果：
# - ⚠️ 強度: 0.46
# - ⚠️ 品質: "pain"（疼痛！）
# - ⚠️ 愉悅度: -1.01（極度痛苦）
```

**生理解釋**：

- 眼睛痛閾極低：0.05
- FreeNerve受體密度300/cm²（全身最高）
- 幾乎不適應（適應率0.02）
- 任何觸碰都轉為疼痛信號
- 愉悅度-1.01 → 觸發負面反應（閃躲、眨眼、眼淚）

### 範例4：持續按壓（適應測試）

```python
for i in range(30):  # 3秒持續按壓
    x, y = 200, 300  # 不動
    pressure = 0.7   # 持續高壓

# 適應過程：
# [0s]  強度: 0.70, 適應: 0.02  ← 初始反應強烈
# [10s] 強度: 0.84, 適應: 0.24  ← 開始習慣
# [20s] 強度: 0.84, 適應: 0.49  ← 一半適應
```

**生理解釋**：

- Meissner受體快速適應（0.3速率）
- 持續刺激 → 受體敏感度下降
- 這就是為什麼戴手錶後會「忘記」它的存在
- 但FreeNerve（痛覺）不適應，所以疼痛不會消失

---

## 與矩陣系統整合

### 觸覺 → 維度參數映射

```python
# 臉頰觸摸的映射
tactile_mappings[BodyRegion.FACE_CHEEK] = {
    'alpha': {
        'physical_arousal': 0.3,  # 生理反應提升
        'comfort': 0.2            # 舒適度微增
    },
    'gamma': {
        'affection': 0.4,         # 親密感大幅提升
        'happiness': 0.2          # 快樂微增
    },
    'delta': {
        'attention_to_user': 0.3  # 對用戶注意力提升
    }
}

# 實際應用時：
# 觸覺強度 0.5 × 映射值 0.4 = 實際影響 0.2
# α.physical_arousal += 0.2
# γ.affection += 0.2
```

### Live2D整合流程

```
用戶在Live2D上觸摸
    ↓
觸覺系統計算：
├── 軌跡分析（速度/加速度/模式）
├── 部位敏感度（臉頰vs眼睛）
├── 受體激活（Meissner/Hair等）
└── 適應調整
    ↓
生理刺激信號生成：
├── 強度: 0.21
├── 品質: "tickle"
├── 愉悅度: +0.36
└── 軌跡模式: "caressing"
    ↓
轉換為系統刺激：
├── StimulusType.TOUCH
├── alpha_impact: 0.13
├── gamma_impact: 0.08
└── delta_impact: 0.06
    ↓
更新矩陣維度具體參數
    ↓
評估行為觸發：
├── tickle_response? (檢查α.arousal+γ.playfulness+刺激)
├── affection_response? (檢查γ.affection+δ.attention)
└── 選擇最佳匹配
    ↓
執行行為反應
```

---

## API使用指南

### 前端調用（Live2D → Python）

```javascript
// 在 Live2D 中追蹤滑鼠
let trajectory = []
let lastTime = Date.now()

function onMouseMove(x, y) {
  const now = Date.now()
  const dt = now - lastTime

  trajectory.push({ x, y, time: now })
  if (trajectory.length > 60) trajectory.shift()

  // 發送到後端
  fetch('/api/touch', {
    method: 'POST',
    body: JSON.stringify({
      region: 'face_cheek', // Live2D檢測到的部位
      x,
      y,
      pressure: isMouseDown ? 0.7 : 0.2,
      trajectory: trajectory.slice(-10), // 最近10點
    }),
  })

  lastTime = now
}

function onMouseUp() {
  fetch('/api/touch/end', {
    method: 'POST',
    body: JSON.stringify({ region: 'face_cheek' }),
  })
}
```

### 後端處理

```python
from core.autonomous.tactile_integration import TactileIntegratedTrigger

trigger_system = TactileIntegratedTrigger()

@app.post("/api/touch")
async def handle_touch(data: TouchData):
    result = trigger_system.process_live2d_touch(
        region_name=data.region,
        x=data.x,
        y=data.y,
        pressure=data.pressure
    )

    return {
        "behavior": result['behavior']['behavior_name'] if result['behavior'] else None,
        "expression": generate_expression(result['tactile']),
        "intensity": result['tactile']['intensity'],
        "pleasantness": result['tactile']['pleasantness']
    }
```

---

## 系統優勢

### vs 傳統觸摸系統

| 特性         | 傳統系統  | 生理觸覺系統 |
| ------------ | --------- | ------------ |
| **輸入**     | 單點點擊  | 連續軌跡     |
| **強度**     | 固定/二元 | 動態計算     |
| **部位差異** | 無        | 受體密度不同 |
| **時間特性** | 瞬間      | 持續+適應    |
| **疼痛**     | 無或簡單  | 真實生理計算 |
| **愉悅度**   | 無        | 動態計算     |

### 實際效果

**用戶體驗對比**：

```
傳統系統：
用戶: *輕撫臉頰*
Angela: "我被觸摸了！" (每次反應相同)
用戶: *用力戳眼睛*
Angela: "我被觸摸了！" (反應相同)

生理系統：
用戶: *輕撫臉頰*
Angela: *微笑* "嗯~很舒服" (愉悅+0.36)
用戶: *繼續撫摸30秒*
Angela: *習慣了，反應變淡* (適應度0.5)
用戶: *用力戳眼睛*
Angela: *痛苦表情* "啊！好痛！" (疼痛-1.01)
用戶: *快速搔頭髮*
Angela: *笑* "哈哈哈好癢~" (頭髮超敏感)
用戶: *戳背部*
Angela: *幾乎無感* "...?" (背部受體稀少)
```

---

## 擴展建議

### 1. 添加更多受體類型

- 溫度受體（冷熱感知）
- 瘙癢專用受體（不同於痛覺）
- 本體感覺（肢體位置感知）

### 2. 多點觸摸

- 同時追蹤多個手指
- 計算接觸面積
- 多部位同時刺激

### 3. 學習適應

- 記錄用戶習慣（誰喜歡輕撫、誰喜歡重壓）
- 調整各部位愉悅度權重
- 個性化反應

### 4. 情緒記憶

- 觸摸與情感記憶關聯
- 被傷害過的部位更敏感
- 建立「安全區」vs「危險區」

---

## 結論

這個系統的核心突破：

1. **從「事件」到「過程」**：不是 onClick，而是連續軌跡
2. **從「抽象」到「生理」**：基於真實神經科學
3. **從「統一」到「差異」**：不同部位不同反應
4. **從「靜態」到「動態」**：適應、學習、變化

**這才是生命體該有的觸覺** 🖐️✨

---

_系統版本: 3.0_  
_最終更新: 2026-02-01_  
_神經生理學基礎: 人體皮膚受體分布_
