# Plan: pixel-angela 更新 + Live2D 修復

> Date: 2026-06-13
> Status: Draft

---

## 第一部分：Live2D 加載失敗分析

### 硬件現狀

| 項目 | 值 |
|------|-----|
| GPU | Intel UHD Graphics（11th Gen，**1 GB 共享 VRAM**） |
| RAM | 8 GB |
| 設備 | ASUS BR1100FKA（教育級輕薄筆電） |
| 解析度 | 1366×768 |

**結論：硬件是瓶頸之一，但不是唯一原因。** 代碼层面有更嚴重的問題導致 Live2D 完全無法載入。

### 根因分析（3 個平台各自的問題）

#### 桌面端 (Electron) — 3 個致命問題

| # | 問題 | 文件 & 行 |
|---|------|-----------|
| 1 | **CSP `script-src 'self'` 阻止 CDN 載入和內聯腳本** | `electron_app/index.html:7` |
| 2 | **SDK fallback 路徑錯誤**（`../libs/live2dcubismcore.min.js` 指向錯誤位置） | `js/live2d-cubism-wrapper.js:82` |
| 3 | **5 秒超時被 CDN 嘗試耗盡**，本地 fallback 來不及載入 | `js/live2d-manager.js:194` |

#### Web 端 — 2 個致命問題

| # | 問題 | 文件 & 行 |
|---|------|-----------|
| 1 | **缺少 Framework SDK bundle**（只有 Core，沒有 Framework） | `index.html:707-713` |
| 2 | **Fallback 創建的 mock SDK 缺少 `Moc`、`Model` 等核心 API** | `libs/live2d-fallback.js:26-63` |

#### 模型本身問題

| 模型 | 大小 | 紋理解析度 | 有 model3.json | 能否用於低配硬件 |
|------|------|-----------|---------------|-----------------|
| miara_pro_en | 13.5 MB | **4096x**（13 MB 紋理） | ✅ | ❌ 太大，1GB VRAM 跑不動 |
| Epsilon_free | 2.8 MB | 2048x | ❌ **缺少** | ✅ 適合 |
| Epsilon | 2.6 MB | 1024x（3 張） | ❌ **缺少** | ✅✅ 最適合 |

**Epsilon 和 Epsilon_free 是合適的替代模型，但它們缺少 `.model3.json` 清單文件，SDK 無法載入。**

### Live2D 修復方案

#### Step 1: 為 Epsilon_free 製作 model3.json（讓低配硬件能跑）

基於 `Epsilon_free`（2048x，2.8 MB），參考 miara_pro_en 的格式創建 `Epsilon_free.model3.json`。

**文件**: `resources/models/Epsilon_free/runtime/Epsilon_free.model3.json`

```json
{
  "Version": 3,
  "FileReferences": {
    "Moc": "Epsilon_free.moc3",
    "Textures": ["Epsilon_free.2048/texture_00.png"],
    "Physics": "Epsilon_free.physics3.json",
    "DisplayInfo": "Epsilon_free.cdi3.json",
    "Motions": {},
    "Groups": [],
    "HitAreas": []
  }
}
```

#### Step 2: 為 Epsilon 製作 model3.json

**文件**: `resources/models/Epsilon/runtime/Epsilon.model3.json`

```json
{
  "Version": 3,
  "FileReferences": {
    "Moc": "Epsilon.moc3",
    "Textures": [
      "Epsilon.1024/texture_00.png",
      "Epsilon.1024/texture_01.png",
      "Epsilon.1024/texture_02.png"
    ],
    "Physics": "Epsilon.physics3.json",
    "DisplayInfo": "Epsilon.cdi3.json",
    "Motions": {},
    "Groups": [],
    "HitAreas": []
  }
}
```

#### Step 3: 修復桌面端 CSP（解除 CDN 和內聯腳本阻擋）

**文件**: `apps/desktop-app/electron_app/index.html:7`

```html
<!-- 修改前 -->
<meta http-equiv="Content-Security-Policy"
  content="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'">

<!-- 修改後：允許 CDN 載入（作為 fallback）+ 內聯腳本 -->
<meta http-equiv="Content-Security-Policy"
  content="default-src 'self'; script-src 'self' https://cubism.live2d.com https://cdn.jsdelivr.net https://unpkg.com 'unsafe-inline'; style-src 'self' 'unsafe-inline'">
```

#### Step 4: 修復桌面端 SDK fallback 路徑

**文件**: `apps/desktop-app/electron_app/js/live2d-cubism-wrapper.js:82`

```javascript
// 修改前
const localSdkUrl = '../libs/live2dcubismcore.min.js';
// 修改後：指向正確的相對路徑
const localSdkUrl = '../libs/cubism/Core/live2dcubismcore.min.js';
```

#### Step 5: 將默認模型切換為 Epsilon_free

**文件**: `apps/desktop-app/electron_app/js/angela-character-config.js`

將 `model_path` 從 miara_pro_t03 改為 Epsilon_free。

**文件**: `apps/web-live2d-viewer/js/angela-character-config.js`

同上。

#### Step 6: 複製 Epsilon_free 模型到桌面端和 Web 端

```
apps/desktop-app/electron_app/models/Epsilon_free/runtime/...
apps/web-live2d-viewer/models/Epsilon_free/runtime/...
```

#### Step 7: 補全 Web 端 Framework SDK

**文件**: `apps/web-live2d-viewer/index.html`

添加缺失的 framework bundle 引用：
```html
<script src="libs/live2dframework/dist/live2dcubismframework.bundle.js"></script>
```

如果 bundle 不存在，從桌面端複製或從 Cubism SDK 重新構建。

#### Step 8: 增加 SDK 超時時間

**文件**: `js/live2d-manager.js:194`

```javascript
// 修改前
const maxWait = 5000;
// 修改後：給予更多時間（特別是低配硬件）
const maxWait = 10000;
```

---

## 第二部分：pixel-angela 更新

### 現狀

- 22 個文件，全在同一目錄（無子目錄）
- 純 PyQt6 桌面應用（無 web 入口）
- 無 `package.json`、`requirements.txt`、`.env`
- 硬編碼路徑：`D:\Projects\Unified-AI-Project\angela_01.jpg`、`ws://127.0.0.1:8000/ws`
- 無 Live2D（`overlay_engine.py` 註釋明確表示「不受 Live2D 複雜引擎限制」）
- 核心類 `AngelaDNA` 在外部 `packages/biology-core/`

### 需要更新的項目

#### P0: 修復硬編碼路徑

| 文件 | 問題 | 修法 |
|------|------|------|
| `renderer.py:16` | 硬編碼 `../../packages/biology-core/src` | 用相對路徑或 `path_config` |
| `sprite_converter.py:39` | 硬編碼 `D:\Projects\...\angela_01.jpg` | 改為命令行參數或配置 |

#### P1: 添加依賴管理

- 創建 `requirements.txt`（PyQt6, websockets, numpy, Pillow, psutil）
- 或 `pyproject.toml` 統一管理

#### P2: WebSocket URL 可配置

- `renderer.py:44` 硬編碼 `ws://127.0.0.1:8000/ws`
- 應從環境變量或配置讀取

#### P3: 與後端 WebSocket 協議對齊

- 檢查 `renderer.py` 的消息格式是否與後端 `websocket_manager.py` 匹配
- 特別是 `state_update`、`chat_message`、`tactile_event` 的 payload 結構

#### P4: 圖標和打包

- 無應用圖標
- 無 PyInstaller / cx_Freeze 打包配置
- 無自動更新機制

---

## 建議執行順序

1. **Live2D Step 1-2**: 製作 Epsilon_free / Epsilon 的 model3.json（5 分鐘）
2. **Live2D Step 3-4**: 修復桌面端 CSP + fallback 路徑（10 分鐘）
3. **Live2D Step 5-6**: 切換默認模型 + 複製模型文件（5 分鐘）
4. **Live2D Step 7-8**: 補全 Web Framework + 增加超時（10 分鐘）
5. **pixel-angela P0-P1**: 修復硬編碼路徑 + 添加 requirements.txt（15 分鐘）
6. **pixel-angela P2-P3**: WebSocket 可配置 + 協議對齊（20 分鐘）
7. **測試驗證**: 啟動桌面端 + web 端，確認 Live2D 正常載入

---

## 風險評估

| 風險 | 影響 | 緩解 |
|------|------|------|
| Epsilon_free model3.json 格式不正確 | 模型仍無法載入 | 參考 Cubism SDK 文檔驗證 |
| Intel UHD 仍跑不動 2048x 紋理 | 卡頓 | 降級到 Epsilon（1024x） |
| CSP 修改引入安全風險 | XSS | 僅允許已知 CDN 域名 |
| Framework bundle 需要構建 | Web 端延遲 | 先從桌面端複製 |
