# Angela AI Desktop App - 完整使用指南

## 📖 目錄

1. [簡介](#簡介)
2. [功能特性](#功能特性)
3. [安裝指南](#安裝指南)
4. [快速開始](#快速開始)
5. [核心功能](#核心功能)
6. [後端整合](#後端整合)
7. [擴展開發](#擴展開發)
8. [故障排除](#故障排除)
9. [API 參考](#api-參考)
10. [貢獻指南](#貢獻指南)

---

## 簡介

Angela AI Desktop
App 是一個跨平台（Windows/macOS/Linux）的桌面應用，以 Live2D 虛擬角色「Angela」為核心，提供完整的視聽觸知覺輸入輸出，並與用戶桌面無侵入性整合。

### 核心特性

- **Live2D 虛擬角色**：Miara Pro 模型，50+ 參數控制
- **4D 狀態矩陣**：α（生理）β（認知）γ（情感）δ（社交）
- **硬體自適應**：根據硬體能力動態調整性能
- **成熟度系統**：L0-L11 成長路徑
- **精度管理**：INT/DEC1-DEC4 精度模式
- **多語言支持**：en, zh-CN, zh-TW, ja, ko
- **主題系統**：light, dark, angela
- **插件系統**：可擴展架構
- **用戶管理**：多用戶支持，關係追蹤

---

## 功能特性

### 視覺輸入

- ✅ 滑鼠位置追蹤（全域/局部）
- ✅ 滑鼠點擊檢測（左右鍵）
- ✅ 拖拽手勢識別
- ✅ 多點觸控支援
- ✅ 手寫筆/觸控筆支援
- ✅ 視線追蹤

### 聽覺輸入

- ✅ 麥克風音訊捕捉
- ✅ 語音識別（Web Speech API）
- ✅ 系統音訊 loopback（準備中）
- ✅ 音訊分析（頻譜/音量）

### 聽覺輸出

- ✅ TTS（文字轉語音）
- ✅ 口型同步
- ✅ 音效播放
- ✅ 樂器音效（振盪器）
- ✅ 音訊視覺化

### 觸覺輸入

- ✅ 多種觸覺裝置支援
- ✅ 裝置自動發現
- ✅ 觸覺訊號處理

### 觸覺輸出

- ✅ 觸覺回饋模式
- ✅ 身體部位映射
- ✅ 情緒-觸覺映射
- ✅ 自定義觸覺模式

### 桌面整合

- ✅ 桌面覆蓋層
- ✅ 點擊穿透機制
- ✅ 區域命中測試
- ✅ 圖層管理
- ✅ 桌布非破壞性合成

### Live2D 整合

- ✅ 模型載入與解析
- ✅ 參數控制（50+）
- ✅ 表情管理（7 種）
- ✅ 動作播放（10 種）
- ✅ 物理模擬
- ✅ 口型同步

---

## 安裝指南

### 前置需求

#### 必需

- **Node.js**: 18.x 或更高版本
- **Python**: 3.9 或更高版本（後端）
- **Git**: 最新版本

#### 可選

- **Visual Studio Code**: 推薦的 IDE
- **Electron Builder**: 用於打包

### 安裝步驟

#### 1. 克隆倉庫

```bash
git clone https://github.com/catcatAI/Unified-AI-Project.git
cd Unified-AI-Project/apps/desktop-app/electron_app
```

#### 2. 安裝依賴

```bash
npm install
```

#### 3. 啟動開發模式

```bash
npm start
# 或
npm run dev
```

#### 4. 打包應用

```bash
# 打包所有平台
npm run build

# 僅打包 Windows
npm run build:win

# 僅打包 macOS
npm run build:mac

# 僅打包 Linux
npm run build:linux
```

打包後的安裝包位於 `dist/` 目錄。

---

## 快速開始

### 1. 啟動應用

雙擊 `Angela AI.exe`（Windows）或 `Angela AI.app`（macOS）或在終端運行：

```bash
npm start
```

### 2. 基本操作

#### 點擊互動

- 點擊 Angela 的不同部位會觸發不同的反應
- 頭部：驚訝表情
- 臉部：開心表情
- 胸部：害羞表情
- 手臂：開心表情

#### 拖拽互動

- 按住 Angela 並拖動，身體會跟隨移動
- 釋放後，Angela 會恢復到原來的位置

#### 語音指令

- "hello" / "hi"：打招呼
- "sad"：顯示悲傷表情
- "happy" / "smile"：顯示開心表情
- "angry"：顯示生氣表情
- "reset" / "neutral"：重置為平靜狀態
- "screenshot" / "snapshot"：保存快照
- "theme light"：切換到亮色主題
- "theme dark"：切換到暗色主題
- "language en"：切換到英語
- "language zh"：切換到中文

#### 鍵盤快捷鍵

- `Ctrl/Cmd + Shift + H`：顯示/隱藏 Angela
- `Ctrl/Cmd + Shift + S`：打開設置
- `Ctrl/Cmd + Shift + Q`：退出應用

### 3. 設置

點擊左下角的設置按鈕（⚙️）打開設置面板。

#### 設置選項

- **通用設置**：窗口、行為
- **外觀設置**：模型選擇、縮放、桌布
- **音訊設置**：TTS、語音識別、系統音訊
- **觸覺設置**：裝置管理、強度調整
- **高級設置**：性能、調試工具
- **危險區域**：重置設置、清除快取

---

## 核心功能

### 4D 狀態矩陣

Angela 的行為由 4D 狀態矩陣控制：

#### α（生理）維度

- **energy**：能量水平
- **comfort**：舒適度
- **arousal**：喚醒度
- **rest_need**：休息需求
- **vitality**：生命力
- **tension**：緊張度

#### β（認知）維度

- **curiosity**：好奇心
- **focus**：專注度
- **confusion**：困惑度
- **learning**：學習度
- **clarity**：清晰度
- **creativity**：創造力

#### γ（情感）維度

- **happiness**：快樂
- **sadness**：悲傷
- **anger**：憤怒
- **fear**：恐懼
- **disgust**：厭惡
- **surprise**：驚訝
- **trust**：信任
- **anticipation**：期待
- **love**：愛
- **calm**：平靜

#### δ（社交）維度

- **attention**：注意力
- **bond**：連結
- **trust**：信任
- **presence**：存在感
- **intimacy**：親密度
- **engagement**：參與度

### 成熟度系統

Angela 從 L0（新生）到 L11（全知）的成長路徑：

| 等級   | 名稱      | 記憶門檻 | 能力                     |
| ------ | --------- | -------- | ------------------------ |
| L0     | 新生      | 0-100    | 基本問候、簡單回應       |
| L1     | 幼兒      | 100-1K   | 簡單聊天、偏好學習       |
| L2     | 童年      | 1K-5K    | 深入對話、笑話、故事     |
| L3     | 少年      | 5K-20K   | 情感支持、建議、辯論     |
| L4     | 青年      | 20K-50K  | 深度親密、承諾、共同目標 |
| L5     | 成熟      | 50K-100K | 智慧、細緻理解           |
| L6-L11 | 高級~全知 | 100K+    | 超越、全知               |

### 性能管理

根據硬體能力自動調整性能：

| 硬體能力 | 性能模式 | FPS | 解析度 | 特效 |
| -------- | -------- | --- | ------ | ---- |
| 非常低   | very-low | 30  | 0.5x   | 0    |
| 低       | low      | 30  | 0.6x   | 1    |
| 中       | medium   | 45  | 0.75x  | 2    |
| 高       | high     | 60  | 1.0x   | 3    |
| 極致     | ultra    | 120 | 1.25x  | 4    |

### 精度管理

根據系統資源自動調整精度：

| 精度模式 | 小數位數 | 量級   | 記憶使用 | 性能影響 |
| -------- | -------- | ------ | -------- | -------- |
| INT      | 0        | 1x     | 最小     | 最低     |
| DEC1     | 1        | 10x    | 極低     | 極低     |
| DEC2     | 2        | 100x   | 低       | 低       |
| DEC3     | 3        | 1000x  | 中       | 中       |
| DEC4     | 4        | 10000x | 高       | 高       |

---

## 後端整合

### WebSocket 通訊

應用通過 WebSocket 與後端通信：

#### 發送到後端

```javascript
{
    type: 'init',              // 初始化
    type: 'state_update',      // 狀態更新
    type: 'performance_change', // 性能變化
    type: 'precision_change',  // 精度變化
    type: 'level_up',         // 等級提升
    type: 'hardware_detected', // 硬體檢測
    type: 'speech'            // 語音輸入
}
```

#### 從後端接收

```javascript
{
    type: 'state_update',      // 後端狀態同步
    type: 'performance_change', // 性能調整指令
    type: 'precision_change',  // 精度調整指令
    type: 'level_up',         // 等級確認
    type: 'hardware_detected'  // 硬體檢測確認
};
```

### 連接後端

在設置中配置後端 URL（默認：`ws://localhost:8765`）。

---

## 擴展開發

### 開發插件

#### 插件結構

```javascript
// my-plugin.js
const exports = {
  name: 'my-plugin',
  version: '1.0.0',
  description: 'My first Angela plugin',
  dependencies: [],

  hooks: {
    'before-update': async (data) => {
      console.log('Before update:', data)
      return data
    },
    'after-update': async (data) => {
      console.log('After update:', data)
    },
  },

  async activate(context) {
    console.log('Plugin activated!')

    // 訪問 Angela API
    const api = context.getAPI()
    console.log('Current state:', api.stateMatrix.getState())

    // 添加鉤子
    context.addHook('custom-event', async (data) => {
      console.log('Custom event:', data)
    })
  },

  async deactivate() {
    console.log('Plugin deactivated!')
  },
}
```

#### 安裝插件

```javascript
const pluginCode = await fetch('path/to/my-plugin.js').then((r) => r.text())
await window.angelaApp.pluginManager.loadPlugin('my-plugin', null)
window.angelaApp.pluginManager.enablePlugin('my-plugin')
```

### 使用 API

```javascript
// 訪問 Angela 模組
const api = window.angelaApp

// Live2D 控制
api.live2dManager.setParameter('ParamEyeLOpen', 0.8)
api.live2dManager.setExpression('happy')

// 狀態矩陣
api.stateMatrix.updateAlpha({ energy: 0.8 })
api.stateMatrix.handleInteraction('click', { part: 'head' })

// 成熟度
api.maturityTracker.addExperience('click', 10)

// 性能管理
api.performanceManager.setPerformanceMode('high')

// 精度管理
api.precisionManager.setGlobalPrecision(3)

// 用戶管理
const user = api.userManager.getCurrentUser()
api.userManager.updateStats(user.id, { clickCount: 1 })

// 日誌
api.logger.info('Custom log message')

// 國際化
const text = api.i18n.t('ui.settings')

// 主題
api.theme.setTheme('dark')

// 數據持久化
api.dataPersistence.set('my_key', 'my_value')
```

---

## 故障排除

### 常見問題

#### 1. 應用無法啟動

**解決方案**：

```bash
# 清除 npm 緩存
npm cache clean --force

# 重新安裝依賴
rm -rf node_modules package-lock.json
npm install

# 重新啟動
npm start
```

#### 2. Live2D 模型無法加載

**解決方案**：

- 檢查模型文件是否在 `resources/models/miara_pro/` 目錄
- 確認所有必需文件存在：
  - `miara_pro_t03.moc3`
  - `miara_pro_t03.model3.json`
  - `miara_pro_t03.physics3.json`
  - `miara_pro_t03.cdi3.json`
  - `texture_00.png`

#### 3. 麥克風無法工作

**解決方案**：

- 檢查瀏覽器權限設置
- 確認系統麥克風已啟用
- 嘗試刷新頁面並重新授權

#### 4. WebSocket 連接失敗

**解決方案**：

- 檢查後端服務是否運行
- 確認 WebSocket URL 正確
- 檢查防火牆設置

#### 5. 性能問題

**解決方案**：

- 降低性能模式：在設置中選擇較低的性能模式
- 降低解析度：在設置中調整解析度
- 關閉不必要的特效

---

## API 參考

### AngelaApp

主應用類，協調所有模組。

#### 方法

| 方法                        | 描述             |
| --------------------------- | ---------------- |
| `initialize()`              | 初始化應用       |
| `loadModel(path)`           | 加載 Live2D 模型 |
| `setExpression(expression)` | 設置表情         |
| `speak(text)`               | 語音播放         |
| `takeSnapshot()`            | 保存快照         |
| `connectBackend(url)`       | 連接後端         |
| `disconnectBackend()`       | 斷開後端         |
| `shutdown()`                | 關閉應用         |

### Live2DManager

Live2D 模型管理器。

#### 方法

| 方法                        | 描述              |
| --------------------------- | ----------------- |
| `loadModel(path)`           | 加載模型          |
| `setExpression(name)`       | 設置表情          |
| `setParameter(name, value)` | 設置參數          |
| `playMotion(group, name)`   | 播放動作          |
| `resetPose()`               | 重置姿勢          |
| `enableLipSync(enabled)`    | 啟用/禁用口型同步 |

### StateMatrix4D

4D 狀態矩陣。

#### 方法

| 方法                            | 描述           |
| ------------------------------- | -------------- |
| `updateAlpha(kwargs)`           | 更新 α 維度    |
| `updateBeta(kwargs)`            | 更新 β 維度    |
| `updateGamma(kwargs)`           | 更新 γ 維度    |
| `updateDelta(kwargs)`           | 更新 δ 維度    |
| `handleInteraction(type, data)` | 處理互動       |
| `computeInfluences()`           | 計算維度間影響 |
| `getAnalysis()`                 | 獲取綜合分析   |

### MaturityTracker

成熟度追蹤器。

#### 方法

| 方法                          | 描述         |
| ----------------------------- | ------------ |
| `addExperience(type, impact)` | 添加經驗     |
| `getStatus()`                 | 獲取當前狀態 |
| `getLevelInfo(level)`         | 獲取等級信息 |
| `getRecommendedAngelaMode()`  | 獲取推薦模式 |

---

## 貢獻指南

### 開發流程

1. Fork 倉庫
2. 創建特性分支：`git checkout -b feature/my-feature`
3. 提交更改：`git commit -m 'Add my feature'`
4. 推送到分支：`git push origin feature/my-feature`
5. 創建 Pull Request

### 代碼規範

- 使用 4 空格縮進
- 使用 camelCase 命名變量和函數
- 使用 PascalCase 命名類
- 添加 JSDoc 註釋
- 遵循 ESLint 規則

### 測試

```bash
# 運行測試
npm test

# 運行 lint
npm run lint

# 運行 typecheck
npm run typecheck
```

---

## 許可證

MIT License

---

## 聯絡與支持

- **專案首頁**: https://github.com/catcatAI/Unified-AI-Project
- **問題報告**: https://github.com/catcatAI/Unified-AI-Project/issues
- **文檔**: https://docs.angela-ai.com
- **Discord**: https://discord.gg/angela-ai

---

**最後更新**: 2026-02-05  
**版本**: 1.0.0  
**維護者**: Angela AI Development Team
