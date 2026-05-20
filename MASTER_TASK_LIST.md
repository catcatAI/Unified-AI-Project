# 總任務追蹤清單 (Master Task List) - 架構審計報告版

本檔案彙整了專案任務。**狀態已根據代碼庫實證審計更新，並納入架構健壯性與安全性修復目標。**

## 1. 任務清單 (Status Verified)

| # | 任務 | 狀態 | 優先級 | 備註 |
|---|------|------|--------|--------------|
| 1 | 核心架構重構 (Phase 1-7) | ✅ 完成 | - | 檔案結構驗證通過 |
| 2 | WebSocket Session 管理 | ✅ 完成 | - | 基礎設施存在，需強化異常恢復 |
| 3 | WebSocket RSV Error 修復 | 🔄 進行中 | 🔴 HIGH | 需重構 `main_api_server.py` 的異常處理邏輯 |
| 4 | StateMatrix4D 架構重構 | 🔄 進行中 | 🟡 MEDIUM | 待執行 `AxisManager` 職責剝離 |
| 5 | WebSocket 生命週期測試 | ⚠️ 缺失 | 🔴 HIGH | **需建立 `test_websocket_lifecycle.py` 驗證重連與中斷** |
| 6 | 檔案路徑注入防護 | ⚠️ 缺失 | 🔴 HIGH | **需建立 `file_handler.py` 進行路徑沙盒化 (Sandboxing)** |
| 7 | 安全性加固：EvaluationDB | ⚠️ 缺失 | 🟡 MEDIUM | 需在 `evaluation_db.py` 加入路徑合法性驗證 |

---

## 2. 關鍵架構債務與行動方案 (Action Plan)

| 類型 | 問題點 | 建議行動 |
|---|------|------|
| **架構健壯性** | WebSocket 異常處理過於消極 (`continue`) | 重構 `websocket_endpoint`，強制執行斷線清除狀態 |
| **安全性** | `evaluation_db.py` 缺乏路徑範圍檢查 | 實作路徑解析與範圍強制檢查 (Path Scoping) |
| **測試覆蓋率** | 缺乏 WebSocket 生命週期邊界測試 | 建立穩定性測試套件，模擬異常中斷 |

---
**審計總結**:
- 系統已具備核心功能，但架構穩定性與安全性邊界處於「開發者模式」（缺乏防禦性編碼）。
- 下一階段目標：從「功能實現」轉向「韌性工程」(Resilience Engineering)，首要任務為補強 WebSocket 的健壯性與檔案系統安全性。
