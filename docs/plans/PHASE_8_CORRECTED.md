# Phase 8 — 技術債清償（修正版 v2.0）

**審計日期**: 2026-05-22  
**基於實際代碼 v6.5 現狀**，修正原計畫中過時的假設。

---

## 已完成（從原計畫移除）

| 原任務 | 原因 |
|--------|------|
| ~~S1 拆 chat_service.py~~ | 已重寫為 280 行 class 版本，不需再拆 |
| ~~S3c pickle deserialization~~ | 無 active `pickle.load`，已註解掉 |
| ~~A5 串 P8 閉環~~ | MathVerifier→CodeInspector→StateMatrixAdapter 已通過 state_matrix_api.py 和 state_matrix_adapter.py 接線 |
| ~~B3 TCS 配置遷移~~ | 11 default + 11 user + 11 evolved 已建立，angela_core.yaml 已棄用 |

---

## 評分標準（更新）

| 維度 | 權重 | 說明 |
|------|------|------|
| **風險** | ×3 | 安全漏洞、運行時炸彈、資料遺失 |
| **耦合** | ×2 | 是否 blocking 其他任務 |
| **工時** | ×1 | 人天估算（越低分越好） |

**分數 = 風險×3 + 耦合×2 − 工時×1**

---

## S 級（本週就要做）

| # | 任務 | 風險 | 耦合 | 工時 | 分數 | 檔案 |
|---|------|------|------|------|------|------|
| **S1** | 修 `execution_monitor.py` — `shell=True` 預設移除 | 🔴3 | 🟡2 | 0.5天 | **14** | `core/managers/execution_monitor.py` L333, L448 |
| **S2** | 移除 `/security/sync-key-c` endpoint（KeyC 洩漏） | 🔴3 | 🟢0 | 0.1天 | **8.9** | `services/main_api_server.py` L761 |
| **S3** | 修 `get_abc_key_manager` 前向引用（L333 呼叫 L525） | 🟡2 | 🟡2 | 0.2天 | **9.6** | `services/main_api_server.py` L330-337 |
| **S4** | 拆 `main_api_server.py` wiring（77行→獨立 wiring.py） | 🟡2 | 🟡2 | 1天 | **11** | `services/main_api_server.py` L547-623 |

---

## A 級（這月要做）

| # | 任務 | 風險 | 耦合 | 工時 | 分數 | 檔案 |
|---|------|------|------|------|------|------|
| **A1** | 移除 57 個 `logging.basicConfig` 保留最後一個 | 🟡2 | 🟢0 | 0.5天 | **5.5** | 全系統 |
| **A2** | 修 2 個 `__all_` typo | 🟢1 | 🟢0 | 0.1天 | **2.9** | `ai/trust/__init__.py`, `ai/service_discovery/__init__.py` |
| **A3** | 清理 3 個真正死 factory + 標記 13 個為休眠資產 | 🟢1 | 🟡2 | 0.5天 | **6.5** | 多處（詳見 DEAD_FACTORY_FORENSICS.md） |
| **A4** | 修 `models/` 反向依賴 | 🟡2 | 🟡2 | 0.5天 | **7.5** | `models/__init__.py` L1 |
| **A5** | 啟動副作用隔離（transformers_compat + sys.path 重複） | 🟡2 | 🟡2 | 1天 | **7** | `core/compat/transformers_compat.py`, `services/main_api_server.py` |
| **A6** | 補 DI 框架（先從 FastAPI Depends 開始） | 🟡2 | 🔴3 | 2天 | **11** | `services/main_api_server.py` |

---

## B 級（有時間再做）

| # | 任務 | 風險 | 耦合 | 工時 | 分數 | 檔案 |
|---|------|------|------|------|------|------|
| **B1** | 修 middleware 命名 `Encrypted` → `Signed` | 🟢1 | 🟢0 | 0.2天 | **2.8** | `shared/security_middleware.py` |
| **B2** | endpoints lazy loading（8 個路由 eager→lazy） | 🟢1 | 🟢0 | 0.5天 | **2.5** | `api/v1/endpoints/__init__.py` |
| **B3** | 把 ~20 個 singleton 改 instance 傳遞 | 🟡2 | 🟢0 | 3天 | **3** | 全系統（詳見 audit） |
| **B4** | `core/interfaces/` 補 `__init__.py` 匯出 | 🟢1 | 🟢0 | 0.1天 | **2.9** | `core/interfaces/` |
| **B5** | P9 持久層統一（save_state/load_state 散落 3 檔案→統一介面） | 🟡2 | 🟢0 | 2天 | **4** | `state_matrix_api.py`, `state_matrix_adapter.py`, `metacognitive_capabilities_engine.py` |

---

## P8.5 — 原始 LLM 閉環（已獨立於技術債清理）

以下任務屬於「功能開發」而非「技術債」，原本列在 P8 但應獨立追蹤：

| # | 任務 | 狀態 | 備註 |
|---|------|------|------|
| P8.5a | 記憶鏈串接（HAM/LU/CDM → query/storage flow） | ❌ 未做 | 類別定義完整但 query/storage flow 未連 |
| P8.5b | 持久層統一（save_state/load_state → StateStore） | 🟡 分散 | 3 檔案有各自實作，無統一介面 |
| P8.5c | Desktop→Live2D WebSocket 控制鏈 | ❌ 未做 | 後端 WebSocket 到 Electron 從未完成 |
| P8.5d | 插件系統後端 hooks | ❌ 未做 | 前端 JS 存在，後端 hooks 不存在 |

---

## 執行路線圖（修正版）

```
Week 1: S1 (shell=True 修復) + S2 (KeyC endpoint 移除) + S3 (前向引用修復)
        + A2 (typo) + A3 (死 factory 清理)
        → 0.5+0.1+0.2+0.1+0.5 = 1.4 天

Week 2: A1 (logging.basicConfig 清理) + A4 (models 反向依賴) + A5 (啟動副作用)
        + B1 (middleware 命名)
        → 0.5+0.5+1+0.2 = 2.2 天

Week 3-4: S4 (拆 wiring.py) + A6 (DI 框架)
        → 1+2 = 3 天，耦合紅線解除

Week 5+: B2-B5 依需求選擇
```

**總工時估算：~6.6 天（全職）或 3-4 週（兼職）**  
*比原計畫減少 ~5 天，因 4 項任務已在 Phase 6+7 中完成*

---

## 驗收標準

| 階段 | 驗收點 |
|------|--------|
| S 級完成 | `execution_monitor.py` 無 `shell=True` 預設；`/security/sync-key-c` endpoint 移除；服務器啟動無 middleware warning；`wiring.py` 存在 |
| A 級完成 | `logging.basicConfig` 剩 ≤1 個；`__all_` typo 為 0；死 factory 剩 0；models 無反向依賴；module-level 副作用隔離；`Depends` 在 ≥3 路由使用 |
| B 級完成 | Middleware 命名為 `Signed`；endpoints lazy-loaded；singleton ≤5 個；`interfaces/` 有匯出；持久層有統一介面 |
