# 🧪 Angela AI 跨平台測試指南

本指南旨在協助開發者與測試人員在不同平台（Windows, macOS, Linux, Mobile）上驗證 Angela AI 的功能完整性與安全性。

## 1. 測試環境準備

### 桌面端 (Desktop)
- **Windows**: 建議使用 Windows 10/11，需具備 WASAPI 音訊驅動。
- **macOS**: 建議使用 macOS 12+，需授予「錄製音訊」與「輔助功能」權限。
- **Linux**: 建議使用 Ubuntu 22.04+，需安裝 `libasound2-dev` 與 `libpulse-dev`。

### 行動端 (Mobile)
- **Android**: Android 10+，需允許網路通訊。
- **iOS**: iOS 14+ (需透過 Expo 或原生構建)。

---

## 2. 核心功能測試清單

### 2.1 安全防護 (A/B/C Security)
- [ ] **密鑰生成**: 啟動 `start_monitor.py` 後，檢查 `data/security/abc_keys.json` 是否正確生成。
- [ ] **行動端驗證**: 使用手機連接後端，驗證 HMAC 簽名是否生效（若無簽名或簽名錯誤應返回 401/403）。
- [ ] **桌面端同步**: 驗證桌面端是否能透過 `api/v1/security/sync-key-c` 獲取同步密鑰。

### 2.2 多模態交互 (Multimodal)
- [ ] **視覺 (Vision)**: 測試 `/api/v1/ai/vision/analyze` 接口的圖片識別延遲。
- [ ] **音訊 (Audio)**: 測試系統音訊擷取與 TTS 播放是否同步。
- [ ] **情感 (Tactile)**: 點擊桌面端 18 個感應部位，觀察情感矩陣變化。

### 2.3 集群運算 (Cluster)
- [ ] **硬體探測**: 執行 `tests/test_cluster_hardware.py` 驗證硬體評分邏輯。
- [ ] **任務分發**: 模擬高負載場景，驗證任務是否根據硬體能力正確分發。

---

## 3. 自動化測試腳本

專案提供了一系列自動化測試腳本，位於 `tests/` 目錄下：

```bash
# 1. 驗證全系統就緒度
python tests/verify_full_system.py

# 2. 測試集群與硬體探測
python tests/test_cluster_hardware.py

# 3. 測試安全性中間件
python tests/test_security.py
```

---

## 4. 常見問題排除 (Troubleshooting)

- **後端埠佔用 (Errno 10048)**: 確保沒有其他 Python 進程佔用 8000 埠。
- **Event Loop 錯誤**: 若遇到 `No running event loop`，請確保非同步任務在正確的循環中初始化。
- **密鑰不匹配**: 若手機無法連線，請嘗試重置 `abc_keys.json` 並重啟服務。

---
最後更新日期: 2026-02-05
