# Angela AI 桌面應用 - 快速開始指南

## 🚀 快速開始

### 前置需求

- Node.js 18+ 和 npm
- Python 3.10+ (for backend)
- Git

### 安裝步驟

#### 1. 安裝依賴

```bash
# 進入桌面應用目錄
cd apps/desktop-app/electron_app

# 安裝 Node.js 依賴
npm install
```

#### 2. 安裝 Electron

```bash
# 如果 Electron 沒有自動安裝
npm install electron --save-dev
```

#### 3. 啟動應用

**開發模式**
```bash
npm start
```

**調試模式**
```bash
npm run dev
```

#### 4. 打包應用

```bash
# Windows
npm run build:win

# macOS
npm run build:mac

# Linux
npm run build:linux
```

---

## 🎯 核心功能使用

### 1. Live2D 模型控制

```javascript
// 加載模型
await window.angelaApp.live2dManager.loadModel('path/to/model');

// 設置表情
window.angelaApp.live2dManager.setExpression('happy');

// 播放動作
await window.angelaApp.live2dManager.playMotion('tap');

// 視線追蹤
window.angelaApp.live2dManager.lookAt(0.5, -0.3);

// 重置姿態
window.angelaApp.live2dManager.resetPose();
```

### 2. 音訊控制

```javascript
// 啟動語音識別
window.angelaApp.audioHandler.startSpeechRecognition();

// 語音合成 (TTS)
window.angelaApp.speak('Hello! How are you today?');

// 播放音效
window.angelaApp.audioHandler.playSoundEffect('click');

// 啟動麥克風
await window.angelaApp.audioHandler.startMicrophone();
```

### 3. 觸覺控制

```javascript
// 發現觸覺裝置
const devices = await window.angelaApp.hapticHandler.discoverDevices();

// 連接裝置
await window.angelaApp.hapticHandler.connectDevice(deviceId);

// 觸覺反饋
window.angelaApp.hapticHandler.vibrate(100, 0.8); // duration, intensity
window.angelaApp.hapticHandler.hapticTouch(0.5); // intensity
window.angelaApp.hapticHandler.hapticEmotion('happy'); // emotion

// 肢體部位觸覺
window.angelaApp.hapticHandler.hapticBodyPart('head', 0.8);
```

### 4. 桌布控制

```javascript
// 加載桌布
await window.angelaApp.wallpaperHandler.loadWallpaper('path/to/image.jpg');

// 設置桌布
await window.angelaApp.wallpaperHandler.setWallpaper('path/to/image.jpg');

// 載入預設桌布
await window.angelaApp.wallpaperHandler.loadPreset('gradient');
await window.angelaApp.wallpaperHandler.loadPreset('dark');
await window.angelaApp.wallpaperHandler.loadPreset('light');

// 應用特效
window.angelaApp.wallpaperHandler.applyEffect('blur');
window.angelaApp.wallpaperHandler.applyEffect('darken');
window.angelaApp.wallpaperHandler.applyEffect('none');

// 拍攝快照
window.angelaApp.wallpaperHandler.saveSnapshot('angela-snapshot.png');
```

### 5. 後端通訊

```javascript
// 連接後端
await window.angelaApp.connectBackend('ws://localhost:8000/ws');

// 斷開後端
await window.angelaApp.disconnectBackend();
```

---

## 🎨 自定義配置

### 模型配置

編輯 `resources/models/miara_pro/miara_pro_t03.model3.json` 來調整模型參數。

### 窗口配置

編輯 `main.js` 中的窗口初始化參數：

```javascript
mainWindow = new BrowserWindow({
    width: 400,        // 窗口寬度
    height: 600,       // 窗口高度
    x: width - 450,    // 初始 X 位置
    y: height - 650,   // 初始 Y 位置
    transparent: true, // 透明背景
    frame: false,      // 無邊框
    alwaysOnTop: false, // 是否置頂
    // ... 其他配置
});
```

### 觸覺配置

編輯 `js/haptic-handler.js` 中的觸覺模式：

```javascript
const hapticPatterns = {
    'click': { duration: 10, intensity: 0.5 },
    'hover': { duration: 5, intensity: 0.3 },
    'touch': { duration: 50, intensity: 1.0 },
    'happy': [100, 50, 200],
    'sad': [50, 100, 50]
    // ... 自定義模式
};
```

---

## 🔧 調試與故障排除

### 啟用開發者工具

```javascript
// 在 main.js 中設置
if (isDevMode) {
    mainWindow.webContents.openDevTools();
}
```

### 常見問題

**問題 1: Live2D 模型無法加載**
```
解決方案: 
1. 檢查模型路徑是否正確
2. 確認所有必需文件存在 (moc3, model3.json, physics3.json, texture.png)
3. 檢查控制台錯誤訊息
```

**問題 2: 點擊穿透不工作**
```
解決方案:
1. 檢查 setIgnoreMouseEvents 調用
2. 確認點擊區域定義正確
3. 在不同平台上測試
```

**問題 3: 音訊無法播放**
```
解決方案:
1. 檢查音訊設備權限
2. 確認 AudioContext 已初始化
3. 檢查瀏覽器安全策略
```

**問題 4: WebSocket 連接失敗**
```
解決方案:
1. 確認後端服務正在運行
2. 檢查連接 URL 是否正確
3. 查看網絡錯誤
```

---

## 📱 快捷鍵

| 快捷鍵 | 功能 |
|--------|------|
| `Ctrl+Shift+A` | 顯示/隱藏應用 |
| `Ctrl+Shift+S` | 打開設置 |
| `Ctrl+Shift+Q` | 退出應用 |

---

## 🌐 API 參考

### Live2DManager API

```javascript
class Live2DManager {
    // 初始化
    async initialize(): Promise<boolean>
    
    // 模型管理
    async loadModel(modelPath: string): Promise<boolean>
    
    // 參數控制
    setParameter(name: string, value: number): void
    getParameter(name: string): number
    
    // 表情控制
    setExpression(expression: string): void
    
    // 視線追蹤
    lookAt(x: number, y: number): void
    
    // 重置
    resetPose(): void
    shutdown(): void
}
```

### AudioHandler API

```javascript
class AudioHandler {
    // 麥克風
    async startMicrophone(): Promise<boolean>
    stopMicrophone(): void
    
    // 語音識別
    startSpeechRecognition(): void
    stopSpeechRecognition(): void
    
    // 語音合成
    speak(text: string, options: object): void
    stopSpeaking(): void
    
    // 音效
    playSoundEffect(name: string): void
    
    // 音訊分析
    getAudioLevel(): number
    
    // 關閉
    shutdown(): void
}
```

### HapticHandler API

```javascript
class HapticHandler {
    // 設備管理
    async discoverDevices(): Promise<Array>
    async connectDevice(deviceId: string): Promise<boolean>
    
    // 觸覺反饋
    vibrate(duration: number, intensity: number, pattern: Array): void
    hapticTouch(intensity: number): void
    hapticEmotion(emotion: string): void
    hapticBodyPart(bodyPart: string, intensity: number): void
    
    // 啟用/禁用
    enable(): void
    disable(): void
    
    // 關閉
    shutdown(): void
}
```

### WallpaperHandler API

```javascript
class WallpaperHandler {
    // 桌布管理
    async loadWallpaper(imagePath: string): Promise<Image>
    async setWallpaper(imagePath: string): Promise<void>
    
    // 預設
    async loadPreset(preset: string): Promise<void>
    
    // 特效
    applyEffect(effect: string): void
    
    // 快照
    takeSnapshot(): string
    saveSnapshot(filename: string): void
    
    // 狀態
    exportState(): object
    async importState(state: object): Promise<void>
    
    // 清理
    cleanup(): void
}
```

---

## 📚 進階主題

### 添加新的 Live2D 模型

1. 將模型文件放到 `resources/models/your-model/`
2. 確保包含所有必需文件
3. 重啟應用
4. 模型將自動被發現

### 添加新的觸覺裝置

1. 在 `js/haptic-handler.js` 中添加設備檢測邏輯
2. 實現設備特定的通訊協議
3. 添加觸覺模式映射

### 自定義點擊區域

1. 編輯 `js/live2d-manager.js` 中的 `getClickableRegions()`
2. 定義新的區域參數
3. 區域將自動應用點擊穿透

### 創建自定義特效

1. 在 `js/wallpaper-handler.js` 中添加新的特效方法
2. 使用 Canvas API 或 WebGL 實現特效
3. 通過 `applyEffect()` 調用

---

## 🤝 貢獻指南

### 開發流程

1. Fork 專案
2. 創建功能分支
3. 進行開發
4. 運行測試
5. 提交 Pull Request

### 代碼規範

- 使用 ES6+ 語法
- 遵循 JSDoc 文檔標準
- 添加錯誤處理
- 註釋複雜邏輯

### 提交規範

```
type(scope): subject

body

footer
```

示例:
```
feat(live2d): add new expression support

Add support for custom expressions in Live2D models.

Closes #123
```

---

## 📄 許可證

MIT License - 詳見 LICENSE 文件

---

**版本**: 1.0.0  
**最後更新**: 2026-02-04  
**狀態**: Alpha
