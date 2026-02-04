# Angela AI - 觸覺系統架構指南

## 📋 觸覺流程概覽

```
滑鼠輸入 (點擊、拖拽)
    ↓
Input Handler (input-handler.js)
    ↓
判定點擊部位 (Live2D 模型區域)
    ↓
Haptic Handler (haptic-handler.js)
    ↓
觸發生理觸覺事件 (PhysiologicalTactileSystem)
    ↓
更新 Angela 生理矩陣 (StateMatrix4D)
    ↓
Live2D Integration (live2d-integration.py)
    ↓
BODY_TO_LIVE2D_MAPPING (參數映射)
    ↓
更新 Live2D 模型參數
    ↓
Angela 視覺反應 (表情、動作)
```

---

## 🧬 觸覺系統架構

### 1. 滑鼠輸入層 (Mouse Input Layer)

**位置**: `apps/desktop-app/electron_app/js/input-handler.js`

**功能**:
- 滑鼠位置追蹤
- 點擊檢測 (mousedown/mouseup)
- 拖拽手勢識別
- 多點觸控支援

**輸出事件**:
```javascript
{
    type: 'click',  // 或 'drag', 'hover'
    bodyPart: 'head',  // 判定的身體部位
    position: { x: 100, y: 200 },  // 滑鼠坐標
    intensity: 0.8,  // 點擊強度
    touchType: 'pat',  // 觸覺類型
    timestamp: '2026-02-04T12:00:00Z'
}
```

---

### 2. 觸覺處理層 (Haptic Processing Layer)

**位置**: `apps/desktop-app/electron_app/js/haptic-handler.js`

**功能**:
- 接收滑鼠輸入事件
- 觸發觸覺回饋 (振動)
- 向後端發送觸覺事件
- 管理觸覺設備

**觸覺模式**:
```javascript
const hapticPatterns = {
    'click': { duration: 10, intensity: 0.5 },
    'hover': { duration: 5, intensity: 0.3 },
    'touch': { duration: 50, intensity: 1.0 },
    'pat': { duration: 30, intensity: 0.8 },
    'stroke': { duration: 40, intensity: 0.6 },
    'poke': { duration: 20, intensity: 0.9 },
    'pinch': { duration: 15, intensity: 0.7 },
    'tickle': { duration: 35, intensity: 0.4 }
};
```

**向後端發送**:
```javascript
// 通過 WebSocket 發送到後端
websocket.send({
    type: 'tactile_event',
    data: {
        bodyPart: 'head',
        touchType: 'pat',
        intensity: 0.8,
        timestamp: Date.now()
    }
});
```

---

### 3. 生理觸覺系統 (Physiological Tactile System)

**位置**: `apps/backend/src/core/autonomous/physiological_tactile.py`

**核心組件**:

#### 3.1 6 種皮膚受體 (Skin Receptors)
```python
class ReceptorType(Enum):
    MEISSNER = auto()    # 邁斯納小體 - 輕觸、快速適應
    MERKEL = auto()      # 默克爾細胞 - 壓力、持續刺激
    PACINIAN = auto()    # 帕西尼小體 - 震動、深層壓力
    RUFFINI = auto()     # 魯菲尼小體 - 皮膚拉伸
    FREE_NERVE = auto()  # 游離神經末梢 - 痛覺、溫度
    HAIR_FOLLICLE = auto() # 毛囊感受器 - 毛髮運動
```

#### 3.2 18 個身體部位 (Body Parts)
```python
class BodyPart(Enum):
    # 頭部
    TOP_OF_HEAD = ("頂頭", BodyRegion.HEAD, 0.7)
    FOREHEAD = ("額頭", BodyRegion.HEAD, 0.8)
    FACE = ("面部", BodyRegion.HEAD, 0.9)
    NECK = ("頸部", BodyRegion.HEAD, 0.6)
    
    # 上身
    CHEST = ("胸部", BodyRegion.UPPER_BODY, 0.5)
    BACK = ("背部", BodyRegion.UPPER_BODY, 0.4)
    ABDOMEN = ("腹部", BodyRegion.UPPER_BODY, 0.5)
    WAIST = ("腰部", BodyRegion.UPPER_BODY, 0.5)
    
    # 下身
    HIPS = ("臀部", BodyRegion.LOWER_BODY, 0.4)
    THIGHS = ("大腿", BodyRegion.LOWER_BODY, 0.4)
    
    # 上肢
    SHOULDERS = ("肩膀", BodyRegion.UPPER_LIMBS, 0.6)
    UPPER_ARMS = ("上臂", BodyRegion.UPPER_LIMBS, 0.5)
    FOREARMS = ("前臂", BodyRegion.UPPER_LIMBS, 0.6)
    HANDS = ("手掌", BodyRegion.UPPER_LIMBS, 1.0)
    FINGERS = ("手指", BodyRegion.UPPER_LIMBS, 1.0)
    
    # 下肢
    KNEES = ("膝蓋", BodyRegion.LOWER_LIMBS, 0.6)
    CALVES = ("小腿", BodyRegion.LOWER_LIMBS, 0.5)
    FEET = ("腳底", BodyRegion.LOWER_LIMBS, 0.8)
```

#### 3.3 6 種觸覺類型 (Tactile Types)
```python
class TactileType(Enum):
    LIGHT_TOUCH = auto()  # 輕觸
    PRESSURE = auto()    # 壓力
    TEMPERATURE = auto() # 溫度
    VIBRATION = auto()   # 震動
    PAIN = auto()        # 痛覺
    ITCH = auto()        # 痒癢
```

---

### 4. Live2D 參數映射 (Body-to-Live2D Mapping)

**位置**: `apps/backend/src/core/autonomous/physiological_tactile.py:692-769`

**結構**:
```python
BODY_TO_LIVE2D_MAPPING = {
    "top_of_head": {
        "pat": {
            "ParamAngleX": (-15, 15),    # 左右轉頭
            "ParamAngleY": (-10, 10),    # 上下轉頭
            "ParamHairSwing": (0, 0.8)    # 頭髮擺動
        },
        "stroke": {
            "ParamHairSwing": (0, 0.5),   # 輕微擺動
            "ParamHairFront": (-0.3, 0.3) # 前髮動
        },
        "rub": {
            "ParamAngleX": (-8, 8),       # 輕微晃動
            "ParamHairSwing": (0, 0.3)    # 擺動
        }
    },
    
    "face": {
        "pat": {
            "ParamCheek": (0.2, 0.8),      # 臉頰紅暈
            "ParamFaceColor": (0.1, 0.5),   # 臉色變化
            "ParamEyeScale": (1, 1.2)       # 眼睛稍微放大
        },
        "stroke": {
            "ParamCheek": (0.1, 0.4),      # 輕微紅暈
            "ParamFaceColor": (0.05, 0.2)   # 輕微變色
        },
        "poke": {
            "ParamEyeLOpen": (0.5, 0.8),     # 驚訝閉眼
            "ParamEyeROpen": (0.5, 0.8),     # 驚訝閉眼
            "ParamCheek": (0.3, 0.6)       # 紅暈
        },
        "pinch": {
            "ParamMouthForm": (-0.6, 0.6),   # 嘴型變化
            "ParamCheek": (0.5, 0.9)       # 明顯紅暈
        }
    },
    
    "chest": {
        "pat": {
            "ParamBodyAngleX": (-8, 8),      # 身體左右晃動
            "ParamBreath": (0.1, 0.4)       # 呼吸變化
        },
        "press": {
            "ParamBreath": (0.2, 0.6)        # 明顯呼吸
        }
    },
    
    # ... 其他身體部位
}
```

**參數格式**:
```python
{
    "ParamAngleX": (-15, 15),  # (最小值, 最大值)
    "ParamCheek": (0.2, 0.8),     # (最小值, 最大值)
    "ParamBreath": (0.1, 0.4)       # (最小值, 最大值)
}
```

---

### 5. 觸覺到生理矩陣的連接 (Tactile to StateMatrix4D Connection)

**位置**: `apps/backend/src/core/autonomous/physiological_tactile.py:300-500`

**處理流程**:
```python
async def process_stimulus(self, stimulus: TactileStimulus):
    """處理觸覺刺激並更新生理狀態"""
    
    # 1. 更新相應部位的受體激活
    for receptor in self.receptors[stimulus.location]:
        activation = self._calculate_receptor_activation(
            receptor, stimulus
        )
        receptor.current_activation = activation
    
    # 2. 更新生理狀態
    self._update_physiological_state()
    
    # 3. 更新情感狀態
    self._update_emotional_state(stimulus)
    
    # 4. 觸發回調
    for callback in self._on_stimulus_callbacks:
        callback(stimulus)
```

**生理狀態更新**:
```python
def _update_physiological_state(self):
    """更新生理狀態"""
    
    # 計算總體激發水平 (arousal level)
    total_activation = sum(
        r.current_activation for receptor in all_receptors
    )
    self.arousal_level = min(100, total_activation)
    
    # 更新神經系統狀態
    self._update_nervous_system()
    
    # 更新內分泌系統
    self._update_endocrine_system()
```

---

### 6. 完整觸覺流程圖

```
┌─────────────────────────────────────────────────────────────┐
│                   用戶操作 (User Action)                   │
│                   滑鼠點擊/拖拽 Angela                      │
└─────────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│            Input Handler (input-handler.js)               │
│                                                             │
│  1. 檢測滑鼠位置                                            │
│  2. 判定點擊的 Live2D 部位 (head, face, chest, arm...)     │
│  3. 判定觸覺類型 (pat, stroke, poke, tickle...)         │
│  4. 計算觸覺強度 (0-1)                                  │
│  5. 觸發本地觸覺回饋 (振動)                            │
│  6. 發送觸覺事件到後端                                   │
└─────────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│         WebSocket 通訊 (Electron → Backend)                │
│                                                             │
│  發送: {                                                   │
│    type: 'tactile_event',                                    │
│    bodyPart: 'head',                                         │
│    touchType: 'pat',                                         │
│    intensity: 0.8                                            │
│  }                                                          │
└─────────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│     PhysiologicalTactileSystem (backend)                     │
│                                                             │
│  1. 接收觸覺事件                                          │
│  2. 激活相應部位的 6 種受體                                │
│  3. 更新生理矩陣 (StateMatrix4D):                            │
│     - α (生理): arousal, hormones, nervous system                │
│     - β (情感): joy, sadness, anger, surprise                 │
│     - γ (認知): 觸覺記憶, 學習模式                     │
│     - δ (社交): 關係更新, 信任度變化                      │
│  4. 觸發情緒響應                                           │
└─────────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│        Live2D Integration (live2d-integration.py)            │
│                                                             │
│  1. 接收生理狀態更新                                      │
│  2. 通過 BODY_TO_LIVE2D_MAPPING 查找參數變化                │
│  3. 計算參數值:                                          │
│     value = min + (max - min) × intensity                       │
│  4. 更新 Live2D 模型參數:                                   │
│     - ParamAngleX, ParamAngleY, ParamAngleZ                   │
│     - ParamEyeLOpen, ParamEyeROpen                             │
│     - ParamCheek, ParamFaceColor                               │
│     - ParamBodyAngleX, ParamBodyAngleY                          │
│     - ParamBreath                                            │
│  5. 設置表情 (set_expression)                               │
│  6. 播放動作 (play_motion)                                 │
└─────────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│           Live2D Model (Miara Pro)                          │
│                                                             │
│  視覺反應:                                                  │
│  - 頭部轉動 (Pat: 左右晃動)                                │
│  - 臉頰紅暈 (Pat: 輕微紅暈)                              │
│  - 眼睛變化 (Poke: 驚訝閉眼)                              │
│  - 身體晃動 (Chest: 左右晃動)                              │
│  - 呼吸變化 (Press: 明顯呼吸)                              │
│  - 頭髮擺動 (Stroke: 輕微擺動)                            │
│  - 表情變化 (根據情感: happy, sad, angry...)                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 觸覺事件示例

### 示例 1: 拍頭 (Pat Head)

```
滑鼠點擊頭部
    ↓
Input Handler 判定: bodyPart = 'top_of_head', touchType = 'pat', intensity = 0.8
    ↓
Haptic Handler: 振動 30ms (intensity: 0.8)
    ↓
WebSocket 發送到後端: { bodyPart: 'top_of_head', touchType: 'pat', intensity: 0.8 }
    ↓
PhysiologicalTactileSystem.process_stimulus():
    - 激活頭部受體: MEISSNER (輕觸), HAIR_FOLLICLE (毛髮運動)
    - 更新生理矩陣: arousal += 20
    - 激發情緒: joy (喜悅)
    ↓
Live2D Integration:
    - 查找 BODY_TO_LIVE2D_MAPPING['top_of_head']['pat']
    - 計算參數: 
        * ParamAngleX = -15 + (30) × 0.8 = 9
        * ParamAngleY = -10 + (20) × 0.8 = 6
        * ParamHairSwing = 0 + (0.8) × 0.8 = 0.64
    - 更新 Live2D 模型
    ↓
Live2D 視覺反應: 頭部左右晃動 + 頭髮擺動 + 微笑表情
```

### 示例 2: 戳臉 (Poke Face)

```
滑鼠點擊臉部
    ↓
Input Handler 判定: bodyPart = 'face', touchType = 'poke', intensity = 0.9
    ↓
Haptic Handler: 振動 20ms (intensity: 0.9)
    ↓
WebSocket 發送到後端: { bodyPart: 'face', touchType: 'poke', intensity = 0.9 }
    ↓
PhysiologicalTactileSystem.process_stimulus():
    - 激活臉部受體: FREE_NERVE (痛覺), MEISSNER (輕觸)
    - 更新生理矩陣: arousal += 35
    - 激發情緒: surprise (驚訝)
    ↓
Live2D Integration:
    - 查找 BODY_TO_LIVE2D_MAPPING['face']['poke']
    - 計算參數:
        * ParamEyeLOpen = 0.5 + (0.3) × 0.9 = 0.77
        * ParamEyeROpen = 0.5 + (0.3) × 0.9 = 0.77
        * ParamCheek = 0.3 + (0.3) × 0.9 = 0.57
    - 更新 Live2D 模型
    ↓
Live2D 視覺反應: 驚訝閉眼 + 臉頰紅暈 + Surprise 表情
```

### 示例 3: 拖拽胸部 (Drag Chest)

```
滑鼠拖拽胸部區域
    ↓
Input Handler 判定: bodyPart = 'chest', touchType = 'drag', intensity = 0.6
    ↓
Haptic Handler: 持續振動 (intensity: 0.6)
    ↓
WebSocket 發送到後端: { bodyPart: 'chest', touchType: 'drag', intensity: 0.6 }
    ↓
PhysiologicalTactileSystem.process_stimulus():
    - 激活胸部受體: MERKEL (壓力), PACINIAN (深層壓力)
    - 更新生理矩陣: arousal += 15
    - 激發情緒: comfort (舒適)
    ↓
Live2D Integration:
    - 查找 BODY_TO_LIVE2D_MAPPING['chest']['drag']
    - 計算參數:
        * ParamBodyAngleX = -8 + (16) × 0.6 = 1.6
        * ParamBreath = 0.1 + (0.3) × 0.6 = 0.28
    - 更新 Live2D 模型
    ↓
Live2D 視覺反應: 身體輕微晃動 + 呼吸變化 + 鬆鬆表情
```

---

## 🔧 參數計算公式

### 通用公式
```python
# 將強度 (0-1) 映射到參數範圍 (min-max)
value = min_value + (max_value - min_value) × intensity

# 示例: ParamAngleX = (-15) + (15 - (-15)) × 0.8 = 9
```

### 表情參數計算
```python
# 表情參數混合
final_value = current_value + (target_value - current_value) × blend_factor

# blend_factor 通常為 0.05 (平滑過渡)
```

### 動作參數計算
```python
# 動作持續時間
duration = base_duration × (1 + (1 - intensity) × 0.5)

# 示例: 輕觸時動作持續 2.0 秒
#       重觸時動作持續 1.2 秒
```

---

## 🎨 情緒到觸覺的映射

**位置**: `apps/backend/src/core/autonomous/physiological_tactile.py:552-597`

```python
EMOTIONAL_TACTILE_MAPPINGS = {
    "joy": {
        "associated_tactile": [TactileType.LIGHT_TOUCH, TactileType.TEMPERATURE],
        "intensity_modifier": 1.2,
        "preferred_locations": [BodyPart.HANDS, BodyPart.FACE]
    },
    "comfort": {
        "associated_tactile": [TactileType.LIGHT_TOUCH, TactileType.PRESSURE],
        "intensity_modifier": 0.9,
        "preferred_locations": [BodyPart.BACK, BodyPart.SHOULDERS, BodyPart.HANDS]
    },
    "anxiety": {
        "associated_tactile": [TactileType.TEMPERATURE, TactileType.PAIN],
        "intensity_modifier": 1.5,
        "preferred_locations": [BodyPart.CHEST, BodyPart.ABDOMEN, BodyPart.HANDS]
    },
    "relaxation": {
        "associated_tactile": [TactileType.PRESSURE, TactileType.TEMPERATURE],
        "intensity_modifier": 0.7,
        "preferred_locations": [BodyPart.BACK, BodyPart.SHOULDERS, BodyPart.NECK]
    },
    "excitement": {
        "associated_tactile": [TactileType.VIBRATION, TactileType.LIGHT_TOUCH],
        "intensity_modifier": 1.3,
        "preferred_locations": [BodyPart.HANDS, BodyPart.FACE, BodyPart.FOREARMS]
    },
    "sadness": {
        "associated_tactile": [TactileType.TEMPERATURE, TactileType.PRESSURE],
        "intensity_modifier": 0.8,
        "preferred_locations": [BodyPart.SHOULDERS, BodyPart.BACK]
    },
    "anger": {
        "associated_tactile": [TactileType.PAIN, TactileType.TEMPERATURE],
        "intensity_modifier": 1.4,
        "preferred_locations": [BodyPart.HANDS, BodyPart.FACE, BodyPart.CHEST]
    }
}
```

---

## 🔄 實作步驟

### 步驟 1: 建立 WebSocket 連接

**桌面端** (`apps/desktop-app/electron_app/js/app.js`):
```javascript
// 連接後端
async function connectBackend() {
    const ws = new WebSocket('ws://localhost:8000/ws');
    
    ws.onopen = () => {
        console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        
        if (message.type === 'tactile_response') {
            // 更新 Live2D 模型
            updateLive2DFromTactile(message.data);
        }
    };
}
```

### 步驟 2: 發送觸覺事件

**桌面端** (`apps/desktop-app/electron_app/js/input-handler.js`):
```javascript
function handleClick(region, position) {
    // 構建觸覺事件
    const tactileEvent = {
        type: 'tactile_event',
        data: {
            bodyPart: region.name,          // 'head', 'face', 'chest' 等
            touchType: 'pat',               // 根據點擊類型判定
            intensity: 0.8,                  // 計算的強度
            timestamp: Date.now()
        }
    };
    
    // 發送到後端
    if (window.angelaApp && window.angelaApp.websocket) {
        window.angelaApp.websocket.send(JSON.stringify(tactileEvent));
    }
}
```

### 步驟 3: 後端處理觸覺事件

**後端** (`apps/backend/src/main.py` 或相關 API):
```python
from apps.backend.src.core.autonomous.physiological_tactile import PhysiologicalTactileSystem
from apps.backend.src.core.autonomous.live2d_integration import Live2DIntegration

async def handle_tactile_event(event: dict):
    """處理觸覺事件"""
    
    # 解析事件
    body_part_str = event['bodyPart']
    touch_type = event['touchType']
    intensity = event['intensity']
    
    # 轉換 BodyPart 枚舉
    body_part = BodyPart[body_part_str.upper()]
    
    # 轉換 TactileType 枚舉
    touch_type_map = {
        'pat': TactileType.LIGHT_TOUCH,
        'stroke': TactileType.LIGHT_TOUCH,
        'poke': TactileType.PRESSURE,
        'pinch': TactileType.PRESSURE,
        'tickle': TactileType.VIBRATION
    }
    tactile_type = touch_type_map.get(touch_type, TactileType.LIGHT_TOUCH)
    
    # 創建觸覺刺激
    stimulus = TactileStimulus(
        tactile_type=tactile_type,
        intensity=intensity * 10,  # 0-10 範圍
        location=body_part,
        duration=2.0,
        source='user'
    )
    
    # 處理刺激 (更新生理矩陣)
    await physiological_tactile_system.process_stimulus(stimulus)
    
    # 更新 Live2D 模型
    live2d_integration.apply_body_touch(
        body_part=body_part_str,
        touch_type=touch_type,
        intensity=intensity
    )
    
    # 返回結果給前端
    return {
        'status': 'success',
        'body_part': body_part_str,
        'touch_type': touch_type,
        'arousal_level': physiological_tactile_system.arousal_level,
        'emotion': physiological_tactile_system.current_emotion
    }
```

### 步驟 4: 更新 Live2D 模型

**桌面端** (`apps/desktop-app/electron_app/js/app.js`):
```javascript
function updateLive2DFromTactile(data) {
    // 獲取 Live2D 參數變化
    const parameterChanges = data.parameters;
    
    // 應用參數到 Live2D 模型
    if (window.angelaApp && window.angelaApp.live2dManager) {
        for (const [paramName, value] of Object.entries(parameterChanges)) {
            window.angelaApp.live2dManager.setParameter(paramName, value);
        }
        
        // 設置表情
        if (data.emotion) {
            window.angelaApp.live2dManager.setExpression(data.emotion);
        }
        
        // 播放動作
        if (data.motion) {
            window.angelaApp.live2dManager.playMotion(data.motion);
        }
    }
}
```

---

## 📚 總結

### 觸覺系統的完整流程

1. **用戶操作**: 滑鼠點擊/拖拽 Live2D 模型
2. **判定部位**: Input Handler 判定點擊的 Live2D 部位
3. **觸發觸覺**: Haptic Handler 觸發振動回饋
4. **發送到後端**: WebSocket 發送觸覺事件到後端
5. **激活受體**: 生理觸覺系統激活相應部位的 6 種受體
6. **更新生理矩陣**: 更新 Angela 的 StateMatrix4D (α, β, γ, δ)
7. **參數映射**: 通過 BODY_TO_LIVE2D_MAPPING 將觸覺轉換為 Live2D 參數
8. **更新模型**: 更新 Live2D 模型的表情和動作參數
9. **視覺反應**: Live2D 模型顯示相應的視覺反應

### 核心架構組件

- **Input Handler** - 處理滑鼠輸入
- **Haptic Handler** - 觸發觸覺回饋
- **PhysiologicalTactileSystem** - 模擬皮膚受體和生理狀態
- **Live2D Integration** - 控制 Live2D 模型
- **BODY_TO_LIVE2D_MAPPING** - 身體部位到 Live2D 參數的映射表
- **StateMatrix4D** - Angela 的 4D 生理矩陣

---

**最後更新**: 2026-02-04  
**版本**: 1.0.0  
**狀態**: Draft
