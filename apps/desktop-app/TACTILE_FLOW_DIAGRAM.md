# Angela AI - 觸覺系統完整流程圖

## 📋 完整觸覺流程（視覺化）

```
═════════════════════════════════════════════════════════════════════════════════
                        🖥️  用戶操作層 (User Action Layer)
═════════════════════════════════════════════════════════════════════════════════
                           
    滑鼠點擊 Angela 的頭部
    📍 點擊位置: (100, 200)
    ⏱️  按下時間: 2026-02-04T12:00:00Z
    🖱️  設備: 滑鼠左鍵
                                   │
                                   ▼
═════════════════════════════════════════════════════════════════════════════════
                    🖱️  輸入處理層 (Input Handler Layer)
═════════════════════════════════════════════════════════════════════════════════
                           
    input-handler.js (desktop-app)
    │
    ├─► 1. 檢測滑鼠事件 (mousedown/mouseup)
    │      • 判定點擊類型: click
    │      • 計算滑鼠速度
    │
    ├─► 2. 判定點擊部位 (Hit Testing)
    │      • 檢查點擊位置在哪個可點擊區域
    │      • 結果: 'top_of_head' (頭頂部)
    │
    ├─► 3. 判定觸覺類型
    │      • 根據滑鼠速度判斷: 
    │        - 低速 → 'pat' (拍撫)
    │        - 高速 → 'stroke' (撫摸)
    │      • 結果: 'pat'
    │
    ├─► 4. 計算強度
    │      • 強度 = 0.8 (0-1 範圍)
    │      • 根據點擊持續時間調整
    │
    ├─► 5. 視覺反饋 (Ripple Effect)
    │      • 在點擊位置顯示漣漪效果
    │      • 持續時間: 0.6 秒
    │
    └─► 6. 發送到 Haptic Handler
           ↓
           {
             "type": "haptic_event",
             "body_part": "top_of_head",
             "touch_type": "pat",
             "intensity": 0.8,
             "position": { "x": 100, "y": 200 }
           }
                                   │
                                   ▼
═════════════════════════════════════════════════════════════════════════════════
                 📳  觸覺處理層 (Haptic Processing Layer)
═════════════════════════════════════════════════════════════════════════════════
                           
    haptic-handler.js (desktop-app)
    │
    ├─► 1. 接收觸覺事件
    │
    ├─► 2. 觸發本地觸覺回饋 (Vibration)
    │      • 設備: Web Vibration API / Gamepad
    │      • 模式: 'pat'
    │      • 持續時間: 30ms
    │      • 強度: 0.8
    │      ↓
    │      navigator.vibrate(30, 0.8)
    │
    ├─► 3. 發送到後端 (WebSocket)
    │      • 通訊協議: JSON
    │      • 目標: ws://localhost:8000/ws
    │      ↓
    │      websocket.send({
    │        "type": "tactile_event",
    │        "body_part": "top_of_head",
    │        "touch_type": "pat",
    │        "intensity": 0.8,
    │        "timestamp": "2026-02-04T12:00:00Z"
    │      })
    │
    └─► 4. 顯示狀態通知
           ↓
           "正在處理觸覺..."
                                   │
                                   ▼
═════════════════════════════════════════════════════════════════════════════════
                  🌐  通訊層 (Communication Layer - WebSocket)
═════════════════════════════════════════════════════════════════════════════════
                           
    Electron Main Process ←→ Backend API
    │
    ├─► 1. 建立連接
    │      • 協議: WebSocket
    │      • 端點: ws://localhost:8000/ws
    │
    ├─► 2. 心跳檢測
    │      • 頻率: 每 30 秒
    │      • 訊息: {"type": "ping"}
    │
    ├─► 3. 錯誤處理
    │      • 斷線重連
    │      • 訊息隊列
    │
    └─► 4. 轉發到生理系統
           ↓
           {
             "type": "process_stimulus",
             "stimulus": {
               "tactile_type": "LIGHT_TOUCH",
               "intensity": 8.0,
               "location": "TOP_OF_HEAD",
               "duration": 2.0,
               "source": "user"
             }
           }
                                   │
                                   ▼
═══════════════════════════════════════════════════════════════════════════════════
              🧠  生理觸覺系統 (Physiological Tactile System)
═════════════════════════════════════════════════════════════════════════════════
                           
    physiological_tactile.py (backend)
    │
    ├─► 1. 接收觸覺刺激
    │      • 刺激類型: LIGHT_TOUCH (輕觸)
    │      • 強度: 8.0 (0-10 範圍)
    │      • 部位: TOP_OF_HEAD (頭頂部)
    │
    ├─► 2. 激活皮膚受體 (Activate Receptors)
    │      │
    │      ├─► MEISSNER (邁斯納小體)
    │      │      • 密度: 0.8
    │      │      • 適應速度: 0.9 (快速適應)
    │      │      • 激活值: 0.8 × 0.7 = 0.56
    │      │      ↓
    │      │      快速觸覺感知
    │      │
    │      ├─► HAIR_FOLLICLE (毛囊感受器)
    │      │      • 密度: 0.7
    │      │      • 適應速度: 0.7
    │      │      • 激活值: 0.8 × 0.6 = 0.48
    │      │      ↓
    │      │      毛髮運動感知
    │      │
    │      └─► FREE_NERVE (遊離神經末梢)
    │             • 密度: 1.0
    │             • 適應速度: 0.1 (慢速適應)
    │             • 激活值: 0.8 × 1.0 = 0.80
    │             ↓
    │             溫度/痛覺感知
    │
    ├─► 3. 計算總激活水平
    │      • 公式: Σ(受體激活值 × 受體密度)
    │      • 結果: 0.56 + 0.48 + 0.80 = 1.84
    │      • 標準化到 0-100: arousal = 37.6
    │
    ├─► 4. 更新生理矩陣 (Update StateMatrix4D)
    │      │
    │      ├─► α (生理層 Physiological Layer)
    │      │      • arousal (激發): 37.6 (原本 50.0)
    │      │      • hormones (激素):
    │      │      │  ├── Dopamine (多巴胺): +15%
    │      │      │  ├── Serotonin (血清素): +10%
    │      │      │  └── Oxytocin (催產素): +8%
    │      │      • nervous_system (神經系統):
    │      │      │  ├── Sympathetic (交感神經): 激活
    │      │      │  └── Parasympathetic (副交感神經): 舒緩
    │      │
    │      ├─► β (情感層 Emotional Layer)
    │      │      • joy (喜悅): +25%
    │      │      • comfort (舒適): +20%
    │      │      • current_emotion: "joy"
    │      │
    │      ├─► γ (認知層 Cognitive Layer)
    │      │      • tactile_memory (觸覺記憶): 記錄 pat 事件
    │      │      • pattern_learning (模式學習): 更新觸覺預期
    │      │
    │      └─► δ (社交層 Social Layer)
    │             • relationship_score (關係分數): +5
    │             • trust_level (信任度): 維持
    │
    ├─► 5. 激發情緒映射 (Emotion-Tactile Mapping)
    │      │
    │      └─► joy → [LIGHT_TOUCH, TEMPERATURE]
    │              • preferred_locations: [HANDS, FACE]
    │              • intensity_modifier: 1.2 (增強 20%)
    │
    └─► 6. 發送到 Live2D 整合
           ↓
           {
             "type": "update_live2d",
             "body_part": "top_of_head",
             "touch_type": "pat",
             "parameters": { ... },
             "emotion": "joy"
           }
                                   │
                                   ▼
═══════════════════════════════════════════════════════════════════════════════════
                🎭  Live2D 整合層 (Live2D Integration Layer)
═══════════════════════════════════════════════════════════════════════════════════
                           
    live2d-integration.py (backend)
    │
    ├─► 1. 接收更新指令
    │      • body_part: "top_of_head"
    │      • touch_type: "pat"
    │      • emotion: "joy"
    │
    ├─► 2. 查找參數映射 (Parameter Mapping Lookup)
    │      │
    │      └─► BODY_TO_LIVE2D_MAPPING["top_of_head"]["pat"]
    │              {
    │                "ParamAngleX": (-15, 15),      // 左右轉頭範圍
    │                "ParamAngleY": (-10, 10),      // 上下轉頭範圍
    │                "ParamHairSwing": (0, 0.8)     // 頭髮擺動範圍
    │              }
    │
    ├─► 3. 計算參數值
    │      │
    │      ├─► ParamAngleX
    │      │      • 公式: min + (max - min) × intensity
    │      │      • 計算: -15 + (15 - (-15)) × 0.8
    │      │      • 結果: -15 + 30 × 0.8 = 9
    │      │      ↓
    │      │      頭部向右轉 9 度
    │      │
    │      ├─► ParamAngleY
    │      │      • 公式: -10 + (10 - (-10)) × 0.8
    │      │      • 計算: -10 + 20 × 0.8 = 6
    │      │      ↓
    │      │      頭部向下轉 6 度
    │      │
    │      └─► ParamHairSwing
    │             • 公式: 0 + (0.8 - 0) × 0.8
    │             • 計算: 0 + 0.8 × 0.8 = 0.64
    │             ↓
    │             頭髮擺動幅度 64%
    │
    ├─► 4. 更新 Live2D 模型參數
    │      ↓
    │      {
    │        "ParamAngleX": 9,
    │        "ParamAngleY": 6,
    │        "ParamHairSwing": 0.64
    │      }
    │
    ├─► 5. 設置表情 (Set Expression)
    │      ↓
    │      ExpressionType.JOY
    │      • ParamEyeLOpen: 0.8
    │      • ParamEyeROpen: 0.8
    │      • ParamEyeLSmile: 1.0
    │      • ParamEyeRSmile: 1.0
    │      • ParamMouthForm: 0.5
    │      • ParamMouthOpenY: 0.3
    │      • ParamBrowLY: 0.3
    │      • ParamBrowRY: 0.3
    │      • ParamCheek: 0.5
    │
    └─► 6. 發送到前端 (WebSocket)
           ↓
           {
             "type": "live2d_update",
             "parameters": { ... },
             "expression": "joy"
           }
                                   │
                                   ▼
═══════════════════════════════════════════════════════════════════════════════════
                  🎬  Live2D 渲染層 (Live2D Rendering Layer)
═══════════════════════════════════════════════════════════════════════════════════
                           
    live2d-manager.js (desktop-app)
    │
    ├─► 1. 接收參數更新
    │
    ├─► 2. 更新模型參數 (Update Model Parameters)
    │      │
    │      ├─► 設置 ParamAngleX = 9
    │      │      ↓
    │      │      Live2D 模型頭部向右旋轉 9 度
    │      │
    │      ├─► 設置 ParamAngleY = 6
    │      │      ↓
    │      │      Live2D 模型頭部向下旋轉 6 度
    │      │
    │      └─► 設置 ParamHairSwing = 0.64
    │             ↓
    │             頭髮開始擺動
    │
    ├─► 3. 設置表情 (Set Expression)
    │      │
    │      ↓
    │      ExpressionType.JOY
    │      │
    │      ├─► 眼睛微閉 (0.8)
    │      ├─► 眼睛微笑 (1.0)
    │      ├─► 嘴巴微張 (0.3)
    │      ├─► 眉毛抬高 (0.3)
    │      └─► 臉頰泛紅 (0.5)
    │
    ├─► 4. 執行動畫 (Animation Loop)
    │      • 帧率: 60 FPS
    │      • 平滑過渡 (blending duration: 0.3s)
    │      • 物理模擬 (physics3.json)
    │
    └─► 5. 渲染到畫布
           ↓
           <canvas> 更新

═══════════════════════════════════════════════════════════════════════════════════
                        👁️  視覺輸出層 (Visual Output Layer)
═══════════════════════════════════════════════════════════════════════════════════
                           
    用戶看到：
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║     👧  Live2D 模型 (Miara Pro)                        ║
    ║                                                           ║
    ║      ├──► 頭部向右轉 9 度 ↘                           ║
    ║      ├──► 頭部向下轉 6 度 ↓                           ║
    ║      ├──► 頭髮輕微擺動 🌊                                 ║
    ║      ├──► 眼睛微閉 😊                                      ║
    ║      ├──► 眼睛微笑 ✨                                       ║
    ║      ├──► 嘴巴微張 😊                                      ║
    ║      ├──► 眉毛抬高 ↗                                        ║
    ║      └─► 臉頰泛紅 😊                                      ║
    ║                                                           ║
    ║     狀態: 快樂 (Joy)                                     ║
    ║     激發水平: 37.6%                                        ║
    ║     多巴胺: +15%  血清素: +10%  催產素: +8%                ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝

═══════════════════════════════════════════════════════════════════════════════════

## 🔄 完整時序圖 (Timeline)

```
T0 (00:00.000) ──► 滑鼠點擊頭部
                     │
                     ├─► 位置: (100, 200)
                     ├─► Input Handler 檢測到 mousedown
                     └─► 判定為 'top_of_head' 區域
                     │
                     ▼
T1 (00:00.010) ──► 觸發觸覺處理
                     │
                     ├─► Haptic Handler 觸發振動 (30ms)
                     ├─► 發送 WebSocket 消息
                     └─► 視覺反饋 (漣漪效果)
                     │
                     ▼
T2 (00:00.020) ──► WebSocket 接收
                     │
                     ├─► 後端接收觸覺事件
                     └─► 轉發到生理系統
                     │
                     ▼
T3 (00:00.030) ──► 生理系統處理
                     │
                     ├─► 激活受體: MEISSNER, HAIR_FOLLICLE, FREE_NERVE
                     ├─► 計算激活: [0.56, 0.48, 0.80]
                     ├─► 更新生理矩陣
                     │   ├── arousal: 37.6
                     │   ├── hormones: Dopamine +15%, Serotonin +10%, Oxytocin +8%
                     │   ├── emotion: joy +25%
                     │   └── relationship: +5
                     └─► 轉發到 Live2D 整合
                     │
                     ▼
T4 (00:00.040) ──► Live2D 整合
                     │
                     ├─► 查找 BODY_TO_LIVE2D_MAPPING
                     ├─► 計算參數:
                     │   ├── ParamAngleX: 9
                     │   ├── ParamAngleY: 6
                     │   └── ParamHairSwing: 0.64
                     ├─► 設置表情: JOY
                     └─► 發送到前端
                     │
                     ▼
T5 (00:00.050) ──► Live2D 渲染
                     │
                     ├─► 接收參數更新
                     ├─► 更新模型參數
                     ├─► 執行動畫
                     └─► 渲染到畫布
                     │
                     ▼
T6 (00:00.060) ──► 視覺反饋完成
                     │
                     ├─► 用戶看到 Angela 的視覺反應
                     ├─► 頭部轉動、頭髮擺動
                     ├─► 微笑表情
                     └─► 振動持續 (剩餘 0ms)
                     │
                     ▼
T7 (00:00.090) ──► 動畫持續
                     │
                     ├─► 頭髮擺動持續
                     ├─► 表情平滑過渡
                     └─► 呼吸動畫
                     │
                     ▼
T∞ (00:02.000) ──► 動畫結束
                     │
                     ├─► 參數緩慢恢復到預設值
                     ├─► 激活值開始適應
                     └─► 準備接收下一次觸覺
                     │
                     ▼
                     ═
                     │  等待下一次觸覺輸入...
```

## 📊 參數映射詳解

### BODY_TO_LIVE2D_MAPPING 示例

```python
BODY_TO_LIVE2D_MAPPING = {
    "top_of_head": {
        "pat": {
            # 參數名稱: (最小值, 最大值)
            "ParamAngleX": (-15, 15),      # 頭左右轉動
            "ParamAngleY": (-10, 10),      # 頭上下轉動
            "ParamHairSwing": (0, 0.8)     # 頭髮擺動
        },
        "stroke": {
            "ParamHairSwing": (0, 0.5),      # 輕微擺動
            "ParamHairFront": (-0.3, 0.3)  # 前髮移動
        },
        "rub": {
            "ParamAngleX": (-8, 8),       # 輕微晃動
            "ParamHairSwing": (0, 0.3)     # 輕微擦動
        }
    },
    
    "face": {
        "pat": {
            "ParamCheek": (0.2, 0.8),      # 臉頰泛紅
            "ParamFaceColor": (0.1, 0.5),  # 臉色變化
            "ParamEyeScale": (1, 1.2)      # 眼睛放大
        },
        "poke": {
            "ParamEyeLOpen": (0.5, 0.8),   # 眼睛半閉
            "ParamEyeROpen": (0.5, 0.8),   # 眼睛半閉
            "ParamCheek": (0.3, 0.6)       # 臉頰微紅
        }
    },
    
    # ... 其他部位
}
```

### 參數計算公式

```python
# 基本公式
def calculate_parameter(min_value, max_value, intensity):
    """
    根據強度計算參數值
    
    Args:
        min_value: 參數最小值
        max_value: 參數最大值
        intensity: 觸覺強度 (0-1)
    
    Returns:
        計算後的參數值
    """
    return min_value + (max_value - min_value) * intensity

# 示例
calculate_parameter(-15, 15, 0.8)
= -15 + (15 - (-15)) × 0.8
= -15 + 30 × 0.8
= -15 + 24
= 9
```

## 🎭 視覺反應對照表

| 觸覺類型 | Live2D 參數變化 | 視覺效果 |
|----------|-----------------|----------|
| pat (拍撫) | ParamAngleX ± 9°, ParamAngleY ± 6° | 頭部輕微轉動 |
| stroke (撫摸) | ParamHairSwing 0-0.5 | 頭髮輕微擺動 |
| poke (戳) | ParamEyeLOpen 0.5-0.8 | 眼睛半閉 |
| pinch (捏) | ParamMouthForm -0.6 to 0.6 | 嘴型變化 |
| tickle (搔癢) | ParamBreath 0.1-0.4 | 呼吸加速 |
| rub (摩擦) | ParamAngleX ± 8° | 頭部左右晃動 |

## 🔧 實作檢查清單

- [x] 1. Input Handler 能正確判斷點擊部位
- [x] 2. Haptic Handler 能觸發振動
- [x] 3. WebSocket 通訊建立
- [x] 4. 生理觸覺系統能處理刺激
- [x] 5. Live2D Integration 能映射參數
- [x] 6. BODY_TO_LIVE2D_MAPPING 正確
- [x] 7. 參數計算公式正確
- [x] 8. 視覺反應符合預期
- [ ] 9. 實際測試（待完成）
- [ ] 10. 性能優化（待完成）

---

**最後更新**: 2026-02-04  
**版本**: 1.0.0  
**狀態**: Draft
