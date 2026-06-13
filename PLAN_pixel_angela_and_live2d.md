# Plan: pixel-angela 更新 + Live2D 修復

> Date: 2026-06-13
> Status: **Step 1-5 已完成，待測試**

---

## 第一部分：Live2D 加載失敗分析

### 硬件現狀

| 項目 | 值 |
|------|-----|
| GPU | Intel UHD Graphics（11th Gen，**1 GB 共享 VRAM**） |
| RAM | 8 GB |
| 設備 | ASUS BR1100FKA（教育級輕薄筆電） |
| 解析度 | 1366×768 |

硬件是性能瓶頸（4096x 紋理跑不動），但**不是「無法載入」的原因**。代碼有 bug 導致 Live2D 完全無法初始化。

### 根因分析

#### 核心發現：Wrapper 只需要 Core SDK，不需要 Framework

Wrapper（桌面和 web 共用同一套）使用的 API 全部來自 `Live2DCubismCore`：

| Wrapper 調用 | 所屬 SDK |
|-------------|---------|
| `Live2DCubismCore.Moc.fromArrayBuffer()` | Core |
| `Live2DCubismCore.Model.fromMoc()` | Core |
| `Live2DCubismCore.MotionGroup` | Core |
| `Live2DCubismCore.Viewport` | Core |

**Wrapper 從未使用 `Live2DCubismFramework` 的任何 API。**

#### 真正的根因：Manager 多餘的 Framework 檢查

**桌面端** `live2d-manager.js:200-204`：
```javascript
const hasCore = typeof window.Live2DCubismCore !== 'undefined';
const hasFramework = typeof window.Live2DCubismFramework !== 'undefined';
if (hasCore && hasFramework) {   // ← 多餘的 Framework 檢查！
    this._initializeWithSDK(window.Live2DCubismCore);
}
```

**Web 端** `live2d-manager.js:208`：
```javascript
if (typeof window.Live2DCubismCore !== 'undefined') {
    // Web 端只检查 Core，但初始化後 wrapper 仍可能因其他原因失敗
}
```

**流程：**
1. `index.html` 透過 `<script src>` 載入 Core SDK → `window.Live2DCubismCore` 已設定 ✅
2. Manager 輪詢等待 Core **和** Framework（5 秒超時）
3. Core 已就緒，但 Framework 載入較慢或不存在
4. 5 秒後超時 → 進入 `_createFallbackManager()`（2D sprite 模式）
5. Wrapper 從未被創建，Live2D 模型從未被嘗試載入

#### 各平台問題明細

| 平台 | 問題 | 嚴重度 | 文件 & 行 |
|------|------|--------|-----------|
| 桌面端 | Manager 多餘的 `hasFramework` 檢查導致 5 秒超時 | 🔴 Critical | `js/live2d-manager.js:200-204` |
| Web 端 | Framework bundle 不存在 + fallback mock 缺少 Core API | 🔴 Critical | `libs/live2d-fallback.js:26-63` |
| 桌面端 | CSP `script-src 'self'` 阻止 CDN fallback（但不影響本地載入） | 🟢 Low | `index.html:7` |
| 桌面端 | Wrapper fallback 路徑 `../libs/live2dcubismcore.min.js` 錯誤（但不影響，wrapper 短路返回） | 🟢 Low | `js/live2d-cubism-wrapper.js:82` |
| 硬件 | 4096x 紋理（13 MB）對 Intel UHD 1GB VRAM 太重 | 🟡 Medium | — |

#### 模型對比

| 模型 | 大小 | 紋理解析度 | 有 model3.json | 低配硬件適合度 |
|------|------|-----------|---------------|--------------|
| miara_pro_en | 13.5 MB | **4096x**（13 MB 紋理） | ✅ | ❌ 太大 |
| Epsilon_free | 2.8 MB | 2048x | ❌ **缺少** | ✅ 適合 |
| Epsilon | 2.6 MB | 1024x（3 張） | ❌ **缺少** | ✅✅ 最適合 |

---

## 第二部分：Live2D 修復方案

### Step 1: 移除 Manager 多餘的 Framework 檢查（最关键）

**文件**: `apps/desktop-app/electron_app/js/live2d-manager.js`

```javascript
// 修改前（line 200-204）
const hasCore = typeof window.Live2DCubismCore !== 'undefined';
const hasFramework = typeof window.Live2DCubismFramework !== 'undefined';
if (hasCore && hasFramework) {
    console.log('[Live2DManager] Both Core and Framework detected after', elapsed, 'ms');
    this._initializeWithSDK(window.Live2DCubismCore);
}

// 修改後：只檢查 Core
const hasCore = typeof window.Live2DCubismCore !== 'undefined';
if (hasCore) {
    console.log('[Live2DManager] Core SDK detected after', elapsed, 'ms');
    this._initializeWithSDK(window.Live2DCubismCore);
}
```

**文件**: `apps/web-live2d-viewer/js/live2d-manager.js:208`

Web 端已經只檢查 Core，確認無需修改。

### Step 2: 為 Epsilon_free 製作 model3.json ✅ 已完成

**文件**: `resources/models/Epsilon_free/runtime/Epsilon_free.model3.json`

基於目錄中已有的 16 個 motion 文件和 8 個 expression 文件（已驗證實際文件名）：

```json
{
  "Version": 3,
  "FileReferences": {
    "Moc": "Epsilon_free.moc3",
    "Textures": ["Epsilon_free.2048/texture_00.png"],
    "Physics": "Epsilon_free.physics3.json",
    "DisplayInfo": "Epsilon_free.cdi3.json",
    "Expressions": [
      {"Name": "Angry", "File": "expressions/Angry.exp3.json"},
      {"Name": "Blushing", "File": "expressions/Blushing.exp3.json"},
      {"Name": "Normal", "File": "expressions/Normal.exp3.json"},
      {"Name": "Sad", "File": "expressions/Sad.exp3.json"},
      {"Name": "Smile", "File": "expressions/Smile.exp3.json"},
      {"Name": "Surprised", "File": "expressions/Surprised.exp3.json"},
      {"Name": "f01", "File": "expressions/f01.exp3.json"},
      {"Name": "f02", "File": "expressions/f02.exp3.json"}
    ],
    "Motions": {
      "Idle": [{"File": "motion/Epsilon_idle_01.motion3.json"}],
      "Tap": [
        {"File": "motion/Epsilon_m_01.motion3.json"},
        {"File": "motion/Epsilon_m_02.motion3.json"},
        {"File": "motion/Epsilon_m_03.motion3.json"},
        {"File": "motion/Epsilon_m_04.motion3.json"},
        {"File": "motion/Epsilon_m_05.motion3.json"},
        {"File": "motion/Epsilon_m_06.motion3.json"},
        {"File": "motion/Epsilon_m_07.motion3.json"},
        {"File": "motion/Epsilon_m_08.motion3.json"}
      ],
      "Flic": [
        {"File": "motion/Epsilon_m_sp_01.motion3.json"},
        {"File": "motion/Epsilon_m_sp_02.motion3.json"},
        {"File": "motion/Epsilon_m_sp_03.motion3.json"},
        {"File": "motion/Epsilon_m_sp_04.motion3.json"},
        {"File": "motion/Epsilon_m_sp_05.motion3.json"}
      ],
      "Shake": [{"File": "motion/Epsilon_shake_01.motion3.json"}]
    },
    "Groups": [
      {"Target": "Parameter", "Name": "LipSync", "Ids": []},
      {"Target": "Parameter", "Name": "EyeBlink", "Ids": []}
    ],
    "HitAreas": []
  }
}
```

### Step 3: 複製 Epsilon_free 模型到桌面端和 Web 端 ✅ 已完成

```
resources/models/Epsilon_free/runtime/ →
  apps/desktop-app/electron_app/models/Epsilon_free/runtime/ (28 files)
  apps/web-live2d-viewer/models/Epsilon_free/runtime/ (28 files)
```

### Step 4: 切換默認模型到 Epsilon_free ✅ 已完成

**文件**: `apps/desktop-app/electron_app/js/angela-character-config.js`

```javascript
"model_path": "models/Epsilon_free/runtime/Epsilon_free.model3.json",
"fallback_models": [
  "models/Epsilon_free/runtime/Epsilon_free.model3.json",
  "models/miara_pro_en/runtime/miara_pro_t03.model3.json"
]
```

**文件**: `apps/web-live2d-viewer/js/angela-character-config.js` — 同上。

**文件**: `apps/desktop-app/electron_app/js/live2d-manager.js:291` — fallback 路徑同步更新。

### Step 5: 增加 SDK 超時時間 ✅ 已完成

**文件**: `apps/desktop-app/electron_app/js/live2d-manager.js:194`
**文件**: `apps/web-live2d-viewer/js/live2d-manager.js:202`

```javascript
// 修改後：低配硬件 WebGL 初始化較慢
_waitForSDKAndInitialize(maxWait = 10000, interval = 100)
```

### Step 6（可選）: 補全 Web 端 Framework bundle

Web 端 `libs/live2dframework/dist/` 目錄不存在（只有原始碼，未構建）。但由於 wrapper 不需要 Framework，此步驟非必須。如果未來需要 Framework 功能（如物理模擬、表情系統），可以從 Cubism SDK 源碼構建：

```bash
cd apps/web-live2d-viewer/libs/live2dframework
npm install && npm run build
```

---

## 第三部分：pixel-angela 更新

### 現狀

- 22 個文件，全在同一目錄（無子目錄）
- 純 PyQt6 桌面應用（無 web 入口）
- 無 `package.json`、`requirements.txt`、`.env`
- 硬編碼路徑：`D:\Projects\Unified-AI-Project\angela_01.jpg`、`ws://127.0.0.1:8000/ws`
- 無 Live2D（`overlay_engine.py` 註釋：「不受 Live2D 複雜引擎限制」）
- 核心類 `AngelaDNA` 在外部 `packages/biology-core/`

### 需要更新的項目

#### P0: 修復硬編碼路徑

| 文件 | 問題 | 修法 |
|------|------|------|
| `renderer.py:16` | 硬編碼 `../../packages/biology-core/src` | 用相對路徑或 `path_config` |
| `sprite_converter.py:39` | 硬編碼 `D:\Projects\...\angela_01.jpg` | 改為命令行參數或配置 |

#### P1: 添加依賴管理

- 創建 `requirements.txt`（PyQt6, websockets, numpy, Pillow, psutil）

#### P2: WebSocket URL 可配置

- `renderer.py:44` 硬編碼 `ws://127.0.0.1:8000/ws`
- 應從環境變量或配置讀取

#### P3: 與後端 WebSocket 協議對齊

- 檢查 `renderer.py` 的消息格式是否與後端 `websocket_manager.py` 匹配
- 特別是 `state_update`、`chat_message`、`tactile_event` 的 payload 結構

#### P4: 圖標和打包

- 無應用圖標
- 無 PyInstaller / cx_Freeze 打包配置

---

## 建議執行順序

| # | 步驟 | 狀態 |
|---|------|------|
| 1 | **Live2D Step 1**: 移除 Manager 多餘的 Framework 檢查 | ✅ 完成 |
| 2 | **Live2D Step 2**: 驗證 Epsilon_free motion 文件名 + 製作 model3.json | ✅ 完成 |
| 3 | **Live2D Step 3-4**: 複製模型 + 切換默認模型路徑 | ✅ 完成 |
| 4 | **Live2D Step 5**: 增加 SDK 超時時間 | ✅ 完成 |
| 5 | **pixel-angela P0**: 修復硬編碼路徑 | ✅ 完成 |
| 6 | **pixel-angela P1**: 添加 requirements.txt | ✅ 完成 |
| 7 | **測試驗證**: 啟動桌面端 + web 端，確認 Live2D 正常載入 | ⏳ 待執行 |
| 8 | **pixel-angela P2-P3**: WebSocket 可配置 + 協議對齊 | ⏳ 待執行 |

---

## 風險評估

| 風險 | 影響 | 緩解 |
|------|------|------|
| Epsilon_free motion 文件名與 model3.json 不匹配 | 動作無法播放 | 先執行 `ls` 驗證文件名 |
| Intel UHD 跑 2048x 仍卡頓 | 性能差 | 降級到 Epsilon（1024x，但需另外製作 model3.json） |
| Cubism Core SDK 版本不兼容 | 模型渲染異常 | 確認 SDK 版本（項目用 SDK 5-r.5） |
| 移除 Framework 檢查後有其他副作用 | 未知 | 充分測試桌面端和 web 端 |
