# [DEPRECATED] Phase 8 — 技術債清償（代號：擦屎行動）

> **⚠️ 已被 `MASTER_CONSOLIDATED_PLAN.md` 取代 (2026-05-25)**  
> 此文件內容已過時且包含與實際代碼不符的任務。請參閱合併後的全量計畫。

## 目標

將四份分析 MD 中發現的問題排定優先級，用最短工時換取最大的架構健康度提升。

---

## 評分標準

每項任務依以下三維度評分：

| 維度 | 權重 | 說明 |
|------|------|------|
| **風險** | ×3 | 安全漏洞、運行時炸彈、資料遺失 |
| **耦合** | ×2 | 是否 blocking 其他任務 |
| **工時** | ×1 | 人天估算（越低分越好） |

**分數 = 風險×3 + 耦合×2 − 工時×1**

---

## S 級（本週就要做，分數 ≥15）

| # | 任務 | 風險 | 耦合 | 工時 | 分數 | 檔案 |
|---|------|------|------|------|------|------|
| S1 | 拆 `chat_service.py`（1,416 行 → 3 個檔案） | 🔴3 | 🟡2 | 2天 | **13** | `services/chat_service.py` |
| S2 | 拆 `main_api_server.py` wiring 到獨立 `wiring.py` | 🔴3 | 🟡2 | 1天 | **13** | `services/main_api_server.py` |
| S3 | 修 3 處安全漏洞（command injection + credential leak + pickle） | 🔴3 | 🟢0 | 0.5天 | **8.5** | `cleanup_utils.py`, 多處, `bootstrap_manager.py` |
| S4 | 補 DI 框架（先從 FastAPI Depends 開始） | 🟡2 | 🔴3 | 2天 | **11** | 全系統 |

## A 級（這月要做，分數 8-14）

| # | 任務 | 風險 | 耦合 | 工時 | 分數 | 檔案 |
|---|------|------|------|------|------|------|
| A1 | 移除 58 個 `logging.basicConfig` 保留最後一個 | 🟡2 | 🟢0 | 0.5天 | **5.5** | 全系統 |
| A2 | 修 2 個 `__all_` typo | 🟢1 | 🟢0 | 0.1天 | **2.9** | `ai/trust/`, `ai/service_discovery/` |
| A3 | 刪除 16 個死 factory + 對應檔案 | 🟢1 | 🟡2 | 0.5天 | **6.5** | 多處 |
| A4 | 修 `models/` 反向依賴（把 api_models.py 搬到 models/） | 🟡2 | 🟡2 | 0.5天 | **7.5** | `models/`, `services/` |
| A5 | 串 P8 閉環（MathVerifier → CodeInspector → StateMatrixAdapter） | 🟡2 | 🟡2 | 2天 | **8** | 3 個檔案 |
| A6 | 啟動時副作用隔離（transformers_compat, sys.path, module-level init） | 🟡2 | 🟡2 | 1天 | **7** | `compat/`, `main.py` |

## B 級（有時間再做，分數 <8）

| # | 任務 | 風險 | 耦合 | 工時 | 分數 | 檔案 |
|---|------|------|------|------|------|------|
| B1 | 修加密 middleware 命名（Encrypted → Signed） | 🟢1 | 🟢0 | 0.2天 | **2.8** | `shared/security_middleware.py` |
| B2 | 級聯 import 解耦（endpoints lazy loading） | 🟢1 | 🟢0 | 0.5天 | **2.5** | `api/v1/endpoints/__init__.py` |
| B3 | TCS 配置遷移完成（清 legacy + populate 空白目錄） | 🟡2 | 🟢0 | 3天 | **3** | `configs/` |
| B4 | 把 20+ singleton 改 instance 傳遞 | 🟡2 | 🟢0 | 3天 | **3** | 全系統 |
| B5 | 補上 `interfaces/` 匯出 | 🟢1 | 🟢0 | 0.1天 | **2.9** | `interfaces/` |
| B6 | P9 持久層（save_state/load_state） | 🟡2 | 🟢0 | 3天 | **3** | 新檔案 |

---

## 執行路線圖

```
Week 1: S3 (安全漏洞) + A1 (logging) + A2 (typo) + A3 (死factory)
        → 0.5+0.5+0.1+0.5 = 1.6 天，清掉最大量的低垂果實
        
Week 2: A4 (models 反向依賴) + A6 (啟動副作用) + B1 (加密命名)
        → 0.5+1+0.2 = 1.7 天，架構紀律恢復

Week 3-4: S1 (拆 chat_service) + S2 (拆 main_api_server wiring)
        → 2+1 = 3 天，耦合紅線解除

Week 5-6: A5 (串 P8 閉環) + S4 (DI 框架)
        → 2+2 = 4 天，從「有類別」變「有功能」

Week 7+: B2-B6 依需求選擇
```

**總工時估算：~12 天（全職）或 4-6 週（兼職）**

---

## 驗收標準

| 階段 | 驗收點 |
|------|--------|
| **Week 1 完成** | `pytest` 通過率不低於現在，安全掃描無 high severity |
| **Week 2 完成** | `from models import UserInput` 不再觸發 `services/` 的 import |
| **Week 4 完成** | `chat_service.py` <500 行，`main_api_server.py` wiring 抽出到獨立檔案 |
| **Week 6 完成** | POST /api/v1/dialogue 完整跑通 MathVerifier → CodeInspector → StateMatrixAdapter |
| **全部完成** | 所有分析 MD 中標記的問題有明確的 resolved/wontfix/deferred 狀態 |
