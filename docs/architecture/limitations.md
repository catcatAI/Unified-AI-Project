<!--
  =============================================================================
  FILE_PATH: docs/architecture/limitations.md
  FILE_TYPE: documentation
  PURPOSE: 架構邊界與限制 — 單一真相源
  VERSION: 1.0.0
  STATUS: active
  LANGUAGE: zh-TW
  LAST_MODIFIED: 2026-09-17
  AUDIENCE: users, developers
  =============================================================================
-->

# 架構限制（Architecture Limitations）

> 本頁是架構邊界的單一真相源。`RELEASE_CRITERIA.md` 與 `docs/user_guide/unsupported.md` 引用此頁。
> 這些是**設計邊界**，不是 bug；列入正式版範圍聲明。

## 部署形態

| 項目 | 現況 |
|------|------|
| 多使用者並發會話隔離 | **不支援** — 單用戶架構；狀態（情緒、生物矩陣、記憶、會話）為單一實例，多人同時使用會互相干擾 |
| 分散式部署／多節點協同 | **不支援** — 單機部署；HSP 內部匯流排為進程內機制，非跨節點分散式系統 |

## 推理與效能

| 項目 | 現況 |
|------|------|
| 硬體加速推理（CUDA/ROCm/Metal） | **不支援** — 僅 CPU 推理；見 `docs/user_guide/hardware.md` |
| 開放域智能 | 依賴外部／本地 LLM；原生引擎僅確定性任務＋試點泛化，分數拆分見 `docs/INTELLIGENCE_ASSESSMENT.md` |

## 會話與狀態

| 項目 | 現況 |
|------|------|
| 並發會話 | WebSocket session 管理存在，但底層狀態矩陣與記憶為全域單例，未做 per-user 隔離 |
| 長時間自主循環 | AutonomousLifeCycle／Heartbeat 具例外處理，但長時間無人值守運行未經正式版驗收門檻驗證 |

## 已知品質邊界（誠實清單）

- mypy 類型覆蓋債：632 errors（2026-09-17 實測；結構性，分域收斂中）——見 `RELEASE_CRITERIA.md`。
- TS/TSX 無 parser：`lint:js` 僅覆蓋 JS。
- 開放域泛化（純神經路徑）目前為低分能力；確定性能力為強項。
