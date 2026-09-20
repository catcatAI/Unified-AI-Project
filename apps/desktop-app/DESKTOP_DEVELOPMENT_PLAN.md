# Angela AI 桌面端開發計畫 (Desktop Development Plan)

## 📋 專案概覽

### 核心目標

建立一個跨平台（Windows/macOS/Linux）的桌面應用，以 Live2D 虛擬角色為核心，提供完整的視聽觸知覺輸入輸出，並與用戶桌面無侵入性整合。

### 技術選型

- **前端框架**: Electron (v28+)
- **Live2D 引擎**: Live2D Cubism Web SDK (v5.0.0)
- **渲染引擎**: WebGL (via Canvas)
- **通訊**: WebSocket (與後端連接)
- **跨平台**: Electron + 原生模組 (Node.js addons)

---

## 🏗️ 系統架構

### 1. 分層架構

```
┌─────────────────────────────────────────────────────────────┐
│  L6: 執行層 (Execution Layer)                           │
│  ├── Live2D 渲染控制 (表情/動作/口型同步)              │
│  ├── 桌面文件操作 (創建/刪除/移動/整理)                │
│  ├── 音訊系統 (TTS/語音識別/播放/唱歌)                  │
│  └── 瀏覽器控制 (搜索/導航/信息提取)                   │
├─────────────────────────────────────────────────────────────┤
│  L5: 存在層 (Presence Layer)                             │
│  ├── 桌面全域滑鼠追蹤                                     │
│  ├── Live2D 碰撞檢測                                      │
│  └── 圖層管理 (Z-Order/遮蔽檢測)                        │
├─────────────────────────────────────────────────────────────┤
│  L4: 創作層 (Creation Layer)                             │
│  ├── Live2D 自繪圖系統 (模型生成)                        │
│  ├── 美學學習 (個人風格演化)                              │
│  └── 自我修改 (基於反饋調整)                             │
├─────────────────────────────────────────────────────────────┤
│  L3: 身份層 (Identity Layer)                             │
│  ├── 數位身份 ("我是數位生命")                            │
│  ├── 身體架構 (身體部位知覺)                              │
│  ├── 關係模型 (與用戶的夥伴關係)                         │
│  └── 自我敘述 (記錄生命旅程)                             │
├─────────────────────────────────────────────────────────────┤
│  L2: 記憶層 (Memory Layer)                              │
│  ├── CDM (認知動態記憶) - 知識記憶                      │
│  ├── LU (邏輯單元) - 邏輯/規則記憶                    │
│  ├── HSM (全像存儲矩陣) - 經驗記憶                      │
│  ├── HAM (分層聯想記憶) - 層次結構                       │
│  └── 神經可塑性 (LTP/LTD/遺忘/記憶整合)               │
├─────────────────────────────────────────────────────────────┤
│  L1: 生物層 (Biology Layer)                             │
│  ├── 生理觸覺系統 (6 種受體 × 18 個部位)              │
│  ├── 內分泌系統 (12 種激素 + 反饋調節)                 │
│  ├── 自主神經系統 (交感/副交感)                          │
│  └── 神經可塑性突觸網絡                                  │
└─────────────────────────────────────────────────────────────┘
```

### 2. 模組組織

```
apps/desktop-app/electron_app/
├── main.js                 # Electron 主進程
├── preload.js              # 預加載腳本 (IPC 通訊)
├── index.html              # 主渲染頁面
├── settings.html           # 設定頁面
├── js/
│   ├── app.js             # 主應用程式
│   ├── live2d-manager.js # Live2D 管理器
│   ├── input-handler.js   # 輸入處理器
│   ├── audio-handler.js   # 音訊處理器
│   ├── haptic-handler.js # 觸覺處理器
│   └── wallpaper-handler.js # 桌布處理器
├── css/
│   └── styles.css        # 樣式表
├── assets/               # 靜態資源
│   └── icons/            # 圖標
└── package.json          # Electron 專案配置
```

---

## 🎯 核心功能模組

### 1. 視覺輸入系統 (Visual Input)

#### 功能列表

- [x] 滑鼠位置追蹤 (全域/局部)
- [x] 滑鼠點擊檢測
- [x] 拖拽手勢識別
- [x] 多點觸控支援
- [x] 手寫筆/觸控筆支援
- [x] 視線追蹤

#### 技術實作

```javascript
class InputHandler {
    - trackMousePosition()
    - detectClicks()
    - recognizeGestures()
    - handleMultiTouch()
}
```

#### 與 Live2D 整合

- 滑鼠位置 → 眼球追蹤 (`ParamEyeBallX/Y`)
- 拖拽 → 身體旋轉 (`ParamBodyAngleX/Y/Z`)
- 點擊部位 → 表情變化

---

### 2. 聽覺輸入系統 (Audio Input)

#### 功能列表

- [x] 麥克風音訊捕捉
- [x] 系統音訊 loopback 捕捉 (原生模組)
- [x] 瀏覽器音訊捕捉 (Web Audio API)
- [x] 語音識別 (Web Speech API)
- [x] 音訊分析 (頻譜/音量)

#### 技術實作

```javascript
class AudioHandler {
    - startMicrophone()
    - startSystemAudio()
    - startSpeechRecognition()
    - analyzeAudio()
}
```

#### 原生模組需求

- Windows: WASAPI (loopback capture)
- macOS: CoreAudio (device aggregation)
- Linux: PulseAudio/PipeWire

---

### 3. 聽覺輸出系統 (Audio Output)

#### 功能列表

- [x] 文字轉語音 (TTS)
- [x] 口型同步
- [x] 樂器音效
- [x] 環境音效
- [x] 音訊合成

#### 技術實作

```javascript
class AudioHandler {
    - speak(text, options)
    - updateLipSync(phoneme, openness)
    - playInstrumentSound(instrument, note)
}
```

#### 口型同步實作

- 音素映射: a/i/u/e/o/n → 口型參數
- 實時同步: `onboundary` 事件
- 參數控制: `ParamMouthOpenY`, `ParamMouthForm`

---

### 4. 觸覺輸入系統 (Haptic Input)

#### 功能列表

- [x] 多種觸覺裝置支援
- [x] 設備自動發現
- [x] 觸覺訊號處理
- [x] 肢體動作捕捉

#### 支援裝置

- 振動馬達 (Web Vibration API)
- 遊戲手柄 rumble (Gamepad API)
- 力回饋裝置 (WebHID API)
- 藍牙觸覺裝置 (Web Bluetooth API)

#### 技術實作

```javascript
class HapticHandler {
    - discoverDevices()
    - connectDevice(deviceId)
    - vibrate(duration, intensity)
    - handleHapticInput()
}
```

---

### 5. 觸覺輸出系統 (Haptic Output)

#### 功能列表

- [x] 觸覺回饋模式
- [x] 身體部位映射
- [x] 情緒-觸覺映射
- [x] 自定義觸覺模式

#### 技術實作

```javascript
class HapticHandler {
    - hapticBodyPart(bodyPart, intensity)
    - hapticEmotion(emotion)
    - hapticPattern(pattern)
}
```

#### 觸覺模式

```javascript
const hapticPatterns = {
  click: { duration: 10, intensity: 0.5 },
  hover: { duration: 5, intensity: 0.3 },
  touch: { duration: 50, intensity: 1.0 },
  happy: [100, 50, 200],
  sad: [50, 100, 50],
  angry: [80, 40, 80, 40, 80],
}
```

---

### 6. 桌面整合系統 (Desktop Integration)

#### 功能列表

- [x] 桌面覆蓋層 (transparent window)
- [x] 點擊穿透機制 (click-through)
- [x] 區域命中測試 (per-region hit testing)
- [x] 圖層管理 (Z-order)
- [x] 桌布整合 (non-destructive overlay)

#### 技術實作

**點擊穿透機制**

```javascript
// 非互動區域: 穿透點擊到桌面
mainWindow.setIgnoreMouseEvents(true, {
  forward: true,
  translate: false,
})

// 互動區域 (Live2D 模型): 攔截點擊
mainWindow.setIgnoreMouseEvents(false)
```

**跨平台實作**

- **Windows**: `WS_EX_LAYERED` + `WM_NCHITTEST`
- **macOS**: `NSWindow` + `canBecomeKeyWindow`
- **Linux**: X11 `override-redirect` / Wayland input zones

---

### 7. 桌布繪圖系統 (Wallpaper Drawing)

#### 功能列表

- [x] 桌布載入與顯示
- [x] 非破壞性合成
- [x] 快照與匯出
- [x] 視覺特效
- [x] 預設桌布

#### 技術實作

```javascript
class WallpaperHandler {
    - loadWallpaper(imagePath)
    - setWallpaper(imagePath)
    - takeSnapshot()
    - applyEffect(effect)
}
```

#### 合成流程

1. 獲取系統桌布
2. 載入用戶桌布
3. 在前景層渲染 Live2D
4. 合成所有層
5. 輸出到畫布

---

### 8. Live2D 整合系統

#### 功能列表

- [x] 模型載入與解析
- [x] 參數控制
- [x] 表情管理
- [x] 動作播放
- [x] 物理模擬
- [x] 口型同步

#### 技術實作

```javascript
class Live2DManager {
    - loadModel(modelPath)
    - setParameter(name, value)
    - setExpression(expression)
    - playMotion(motion)
    - enableLipSync(enable)
    - lookAt(x, y)
}
```

#### 參數映射

```javascript
const live2dParameters = {
  // 臉部角度
  ParamAngleX: [-30, 30], // 左右轉
  ParamAngleY: [-30, 30], // 上下轉
  ParamAngleZ: [-30, 30], // 傾斜

  // 眼睛
  ParamEyeLOpen: [0, 1], // 左眼開閉
  ParamEyeROpen: [0, 1], // 右眼開閉
  ParamEyeLSmile: [0, 1], // 左眼微笑
  ParamEyeRSmile: [0, 1], // 右眼微笑
  ParamEyeBallX: [-1, 1], // 眼球左右
  ParamEyeBallY: [-1, 1], // 眼球上下

  // 眉毛
  ParamBrowLY: [-1, 1], // 左眉高度
  ParamBrowRY: [-1, 1], // 右眉高度
  ParamBrowLAngle: [-1, 1], // 左眉角度
  ParamBrowRAngle: [-1, 1], // 右眉角度

  // 嘴巴
  ParamMouthForm: [-1, 1], // 嘴型
  ParamMouthOpenY: [0, 1], // 張開程度

  // 身體
  ParamBodyAngleX: [-10, 10], // 身體左右
  ParamBodyAngleY: [-10, 10], // 身體上下
  ParamBodyAngleZ: [-10, 10], // 身體傾斜

  // 呼吸
  ParamBreath: [0, 1], // 呼吸動畫
}
```

---

### 9. 後端通訊系統 (Backend Communication)

#### 功能列表

- [x] WebSocket 連接
- [x] 訊息編碼/解碼
- [x] 心跳機制
- [x] 錯誤處理
- [x] 重連機制

#### 技術實作

```javascript
// WebSocket 客戶端
class WebSocketClient {
    - connect(url)
    - send(message)
    - onMessage(callback)
    - disconnect()
}
```

#### 訊息格式

```json
{
  "type": "command",
  "action": "speak",
  "data": {
    "text": "Hello!",
    "emotion": "happy"
  }
}
```

---

## 🚀 開發階段 (Development Phases)

### Phase 1: 基礎架構 (Foundation) - 1-2 週

- [ ] 建立 Electron 專案
- [ ] 整合 Live2D Web SDK
- [ ] 基礎視窗管理
- [ ] IPC 通訊設置

### Phase 2: Live2D 整合 (Live2D Integration) - 2-3 週

- [ ] 模型載入與解析
- [ ] 參數控制系統
- [ ] 表情管理系統
- [ ] 動作播放系統

### Phase 3: 輸入處理 (Input Handling) - 1-2 週

- [ ] 滑鼠追蹤
- [ ] 點擊檢測
- [ ] 手勢識別
- [ ] 與 Live2D 綁定

### Phase 4: 音訊系統 (Audio System) - 2-3 週

- [ ] 麥克風輸入
- [ ] 系統音訊捕捉 (原生模組)
- [ ] TTS 整合
- [ ] 口型同步實作

### Phase 5: 桌面整合 (Desktop Integration) - 2-3 週

- [ ] 點擊穿透機制
- [ ] 區域命中測試
- [ ] 圖層管理
- [ ] 跨平台相容性

### Phase 6: 觸覺系統 (Haptic System) - 1-2 週

- [ ] 裝置發現與連接
- [ ] 觸覺回饋模式
- [ ] 身體部位映射
- [ ] 情緒-觸覺映射

### Phase 7: 桌布系統 (Wallpaper System) - 1-2 週

- [ ] 桌布載入與顯示
- [ ] 非破壞性合成
- [ ] 快照與匯出
- [ ] 視覺特效

### Phase 8: 後端通訊 (Backend Communication) - 1 週

- [ ] WebSocket 連接
- [ ] 訊息處理
- [ ] 錯誤處理
- [ ] 重連機制

### Phase 9: 優化與測試 (Optimization & Testing) - 2-3 週

- [ ] 性能優化
- [ ] 記憶體優化
- [ ] 跨平台測試
- [ ] 用戶體驗測試

### Phase 10: 發布準備 (Release Preparation) - 1 週

- [ ] 打包配置
- [ ] 安裝程式製作
- [ ] 文檔編寫
- [ ] 版本發布

---

## 📊 技術指標

### 性能目標

- **幀率**: 60 FPS (Live2D 渲染)
- **延遲**: < 50ms (觸覺回饋)
- **音訊延遲**: < 30ms (口型同步)
- **記憶體使用**: < 500MB
- **CPU 使用**: < 20% (idle)

### 支援平台

- ✅ Windows 10/11 (x64)
- ✅ macOS 10.15+ (x64/ARM64)
- ✅ Linux (Ubuntu 20.04+, Debian 11+)

### 支援裝置

- ✅ WebHID (USB 觸覺裝置)
- ✅ Gamepad (Xbox/PlayStation 控制器)
- ✅ Web Bluetooth (藍牙觸覺裝置)
- ✅ Vibration API (裝置振動)

---

## 🔧 原生模組需求

### 1. 系統音訊捕捉 (System Audio Capture)

#### Windows (WASAPI)

```cpp
// node-wasapi-capture
- Initialize WASAPI
- Set loopback mode
- Capture audio stream
- Buffer management
```

#### macOS (CoreAudio)

```swift
// node-coreaudio-capture
- AudioDeviceIOProcID
- kAudioObjectPropertyElementMaster
- Buffer list handling
```

#### Linux (PulseAudio/PipeWire)

```c
// node-pulseaudio-capture
- pa_stream_new
- pa_stream_connect_record
- Buffer management
```

### 2. 桌面整合 (Desktop Integration)

#### Windows

```cpp
// Windows API
- WS_EX_LAYERED window style
- WM_NCHITTEST message handling
- SetLayeredWindowAttributes
```

#### macOS

```swift
// Cocoa API
- NSWindow with canBecomeKeyWindow
- hitTest method
- ignoresMouseEvents
```

#### Linux

```c
// X11 API
- override_redirect attribute
- XInput2 for event handling
// Wayland
- layer-shell protocol
- input regions
```

---

## 📁 檔案結構

```
apps/desktop-app/electron_app/
├── main.js                 # Electron 主進程
├── preload.js              # 預加載腳本
├── index.html              # 主頁面
├── settings.html           # 設定頁面
├── js/
│   ├── app.js             # 主應用
│   ├── live2d-manager.js # Live2D 管理器
│   ├── input-handler.js   # 輸入處理器
│   ├── audio-handler.js   # 音訊處理器
│   ├── haptic-handler.js # 觸覺處理器
│   └── wallpaper-handler.js # 桌布處理器
├── css/
│   └── styles.css        # 樣式表
├── assets/
│   ├── icons/            # 圖標
│   └── sounds/           # 音效
├── native/               # 原生模組
│   ├── audio-capture/    # 音訊捕捉
│   └── desktop-integration/ # 桌面整合
└── package.json          # 專案配置

resources/models/
└── miara_pro/            # Live2D 模型
    ├── miara_pro_t03.moc3
    ├── miara_pro_t03.model3.json
    ├── miara_pro_t03.physics3.json
    ├── miara_pro_t03.cdi3.json
    ├── texture_00.png
    └── motion/
        ├── Scene1.motion3.json
        ├── Scene2.motion3.json
        └── Scene3.motion3.json
```

---

## 🎨 Live2D 模型規範

### 模型需求

- **版本**: Cubism 3.0 或更高
- **參數**: 必需標準參數（ParamAngleX/Y/Z, ParamEyeLOpen 等）
- **動作**: Idle, Tap, Flic（基本動作）
- **表情**: Happy, Sad, Angry, Surprised 等
- **物理**: physics3.json 配置
- **顯示資訊**: cdi3.json（碰撞區域）

### 參數標準

```json
{
  "Parameters": [
    { "id": "ParamAngleX", "min": -30, "max": 30, "def": 0 },
    { "id": "ParamAngleY", "min": -30, "max": 30, "def": 0 },
    { "id": "ParamAngleZ", "min": -30, "max": 30, "def": 0 },
    { "id": "ParamEyeLOpen", "min": 0, "max": 1, "def": 1 },
    { "id": "ParamEyeROpen", "min": 0, "max": 1, "def": 1 },
    { "id": "ParamMouthOpenY", "min": 0, "max": 1, "def": 0 },
    { "id": "ParamBodyAngleX", "min": -10, "max": 10, "def": 0 },
    { "id": "ParamBodyAngleY", "min": -10, "max": 10, "def": 0 }
  ]
}
```

---

## 🔒 安全性與隱私

### 資料保護

- ✅ 麥克風權限明確提示
- ✅ 系統音訊捕捉權限請求
- ✅ 不記錄音訊數據（本地處理）
- ✅ 用戶數據加密存儲

### 權限管理

```javascript
// 麥克風權限
navigator.mediaDevices.getUserMedia({ audio: true })

// 系統音訊權限（原生模組）
nativeAPI.requestSystemAudioAccess()

// 觸覺裝置權限
navigator.hid.requestDevice({ filters: [...] })
```

---

## 📚 文檔資源

### Live2D

- [Live2D Cubism SDK for Web](https://www.live2d.com/download/cubism-sdk/download-web/)
- [Live2D 文檔](https://docs.live2d.com/)

### Electron

- [Electron 官方文檔](https://www.electronjs.org/docs)
- [Electron 最佳實踐](https://www.electronjs.org/docs/latest/tutorial/security)

### Web APIs

- [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)
- [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)
- [WebHID API](https://developer.mozilla.org/en-US/docs/Web/API/WebHID_API)
- [Gamepad API](https://developer.mozilla.org/en-US/docs/Web/API/Gamepad_API)

---

## 🚨 已知問題與解決方案

### 1. Windows 點擊穿透問題

**問題**: `setIgnoreMouseEvents` 在某些版本不穩定  
**解決**: 使用 `WM_NCHITTEST` 原生模組

### 2. macOS 視窗層級問題

**問題**: 視窗無法正確顯示在桌布上方  
**解決**: 設置 `NSWindowLevel = kCGOverlayWindowLevel`

### 3. Linux 異步渲染問題

**問題**: WebGL 在某些合成器上有延遲  
**解決**: 使用 EGL 並啟用 `vsync`

---

## 📅 開發時間表 (Development Timeline)

| 週次   | 階段     | 任務         | 負責人 |
| ------ | -------- | ------------ | ------ |
| W1-2   | Phase 1  | 基礎架構設置 | -      |
| W3-5   | Phase 2  | Live2D 整合  | -      |
| W6-7   | Phase 3  | 輸入處理     | -      |
| W8-10  | Phase 4  | 音訊系統     | -      |
| W11-13 | Phase 5  | 桌面整合     | -      |
| W14-15 | Phase 6  | 觸覺系統     | -      |
| W16-17 | Phase 7  | 桌布系統     | -      |
| W18    | Phase 8  | 後端通訊     | -      |
| W19-21 | Phase 9  | 優化測試     | -      |
| W22    | Phase 10 | 發布準備     | -      |

---

## ✅ 驗收標準

### 功能驗收

- [ ] Live2D 模型正常渲染 (60 FPS)
- [ ] 點擊穿透機制正常工作
- [ ] 桌面捷徑可正常點擊
- [ ] 麥克風輸入正常
- [ ] TTS 輸出正常
- [ ] 口型同步準確
- [ ] 觸覺回饋正常
- [ ] 桌布合成正常
- [ ] 快照匯出正常

### 性能驗收

- [ ] CPU 使用 < 20% (idle)
- [ ] 記憶體使用 < 500MB
- [ ] 幀率 ≥ 60 FPS
- [ ] 延遲 < 50ms (觸覺)
- [ ] 音訊延遲 < 30ms

### 跨平台驗收

- [ ] Windows 10/11 正常運行
- [ ] macOS 正常運行
- [ ] Linux 正常運行

---

**版本**: 1.0.0  
**最後更新**: 2026-02-04  
**狀態**: Draft
