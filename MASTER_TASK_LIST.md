# 總任務追蹤清單 (Master Task List) - 實證審計完整版

本檔案基於代碼庫實體稽核。所有任務已與實際檔案系統路徑進行一對一對應。

## 1. 核心模組與架構驗證 (Verified)
| ID | 任務 | 檔案路徑 | 狀態 |
|---|------|------|------|
| 1.1 | 核心狀態軸 (Axis) | `core/state/axis.py` | ✅ |
| 1.2 | 軸字段註冊 (AxisFieldRegistry) | `core/state/axis_field.py` | ✅ |
| 1.3 | 時間狀態管理 (TemporalState) | `core/state/temporal.py` | ✅ |
| 1.4 | 資源分配政策 (AllocationPolicy) | `core/allocation/policy.py` | ✅ |
| 1.5 | 影響空間抽象 (InfluenceSpace) | `core/influence/space.py` | ✅ |
| 1.6 | 狀態矩陣適配器 (StateMatrixAdapter) | `core/autonomous/state_matrix_adapter.py` | ✅ |
| 1.7 | η (Eta) 軸執行層 | `core/autonomous/eta_axis.py` | ✅ |
| 1.8 | 狀態持久化 (StatePersistence) | `core/autonomous/state_persistence.py` | ✅ |

## 2. 服務與通訊驗證 (Verified)
| ID | 任務 | 檔案路徑 | 狀態 |
|---|------|------|------|
| 2.1 | WebSocket API 服務 | `services/main_api_server.py` | 🔄 (RSV 錯誤中) |
| 2.2 | 會話管理 (ConnectionSession) | `services/connection_session.py` | ✅ |
| 2.3 | Angela LLM 服務 | `services/angela_llm_service.py` | ✅ |
| 2.4 | 安全中間件 | `shared/security_middleware.py` | ✅ |

## 3. 安全性與穩健性修復 (In Progress/Pending)
| ID | 任務 | 優先級 | 狀態 | 備註 |
|---|------|--------|------|------|
| 3.1 | WebSocket 生命週期測試 | 🔴 HIGH | ⚠️ 缺失 | 需補建 `tests/integration/test_websocket_lifecycle.py` |
| 3.2 | 路徑沙盒化防護 | 🔴 HIGH | ⚠️ 缺失 | 需建立 `security/file_handler.py` |
| 3.3 | 資料庫路徑校驗 | 🟡 MEDIUM | 🔄 進行中 | 修復 `evaluation_db.py` 路徑風險 |

## 4. 代碼瘦身計畫 (Refactoring Roadmap)
| ID | 任務 | 目標 | 狀態 |
|---|------|------|------|
| 4.1 | 軸更新邏輯委託 | `state_matrix.py` → `AxisManager` | 🟡 待開始 |
| 4.2 | 語義處理邏輯拆分 | `state_matrix.py` → `text_utils.py` | 🟡 待開始 |
| 4.3 | 舊版決策邏輯遷移 | `state_matrix.py` → `AllocationPolicy` | 🟡 待開始 |

---
**審計總結**:
- 本清單是對應實際磁碟路徑的實證審計，取代所有過去的預估清單。
- 接下來將依照「安全性防護」→「測試補建」→「架構瘦身」的順序進行修復。
