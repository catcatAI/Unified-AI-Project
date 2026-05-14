# Angela 任務優先級清單 v2.0
## 2026-05-14 更新 — Post-Refactor Plan v1.0 完成 ✅

---

## ✅ 完成狀態

### 🟡 P1 — 架構瓶頸（限制潛力釋放）— 全部完成 ✅

| # | 任務 | 狀態 | 實現 | 驗證 |
|---|------|------|------|------|
| 1 | Phase 1: Axis + AxisField 重構 | ✅ 完成 | core/state/axis_field.py (334行), axis.py (215行) | 5 個測試通過 |
| 2 | Phase 2: TemporalState 重構 | ✅ 完成 | core/state/temporal.py (426行) | 14 個測試通過 |
| 3 | Phase 3: AllocationPolicy 重構 | ✅ 完成 | core/allocation/policy.py (260行) + resonance.py (184行) + negativity.py (310行) | 10 個測試通過 |
| 4 | Phase 4: 配置外部化 | ✅ 完成 | core/state/config_loader.py (239行) | 配置加載測試通過 |
| 5 | Phase 5: RippleNode 對象化 | ✅ 完成 | core/ripple/node.py (361行) | 10 個測試通過 |
| 6 | Phase 6: InfluenceSpace 抽象 | ✅ 完成 | core/influence/space.py (333行) + influence_applicator.py (124行) | 7 個測試通過 |
| 7 | Phase 7: 整合適配器 | ✅ 完成 | core/autonomous/state_matrix_adapter.py (378行) | smoke test 9 場景通過 |

---

### 🟡 P1 延伸 — Post-Refactor Plan v1.0（全部完成 ✅）

| # | 方向 | 任務細項 | 狀態 | 驗證 |
|---|------|----------|------|------|
| 1.1 | Smoke Test | 9 個場景 smoke test | ✅ | test_smoke_real.py: 9/9 通過 |
| 2.1 | God Class 清理 | `_record_history()` → TemporalState | ✅ | `_get_temporal_state()` / `_sync_to_temporal()` 同步測試通過 |
| 2.2 | God Class 清理 | `_apply_influence()` → InfluenceApplicator | ✅ | 15/15 影響規則覆蓋審計通過，tension 負效應一致 |
| 2.3 | God Class 清理 | `detect_misallocated_points()` → 索引版本 | ✅ | `detect_misallocated_points_indexed()` 測試通過 |
| 2.4 | God Class 清理 | `meta_allocate()` → AllocationPolicy 包裝 | ✅ | policy vs legacy 比對測試通過 |
| 2.6 | God Class 清理 | 清理 `_text_to_vector` 重複 helper | ✅ | `text_to_vector.py` 統一實作，ResonanceEngine 委託 |
| 2.7 | God Class 清理 | 硬編碼移到 StateConfig | ✅ | 配置加載 smoke test 通過 |
| 3.1 | CodeInspector 整合 | CodeInspectorBridge | ✅ | 8 個測試通過 |
| 4.1 | P2 N.22.6 | SelfIntrospectorV2 | ✅ | 8 個測試通過 |
| 5.1 | 完整測試套件 | 11 個測試檔案，71+ 測試 | ✅ | 全部通過 |

---

### 🟢 P2 — 迭代任務（重構完成後的實際功能）

| # | 任務 | 檔案 | 說明 | 狀態 |
|---|------|------|------|------|
| 1 | N.22-DUAL-RAIL 雙軌數學驗證 | math_verifier.py | 現有框架完成，可用新 TemporalState 做時間對比 | 未實作 |
| 2 | N.22.1-7 迭代功能 | various | 可以在新架構上重新實現 | 部分完成 |

---

### 🐛 Bug 修復記錄

| Bug | 檔案 | 問題 | 修復 |
|-----|------|------|------|
| TemporalState `get_at()` 負索引 | `temporal.py` | 負索引 `index < 0` 時先 compare 再 normalize，應 normalize 再 compare | 調整順序：先 `n + index`，再 bounds check |
| Facade `_group_kwargs_by_axis()` 路由錯誤 | `state_matrix_adapter.py` | 單一 kwarg 時路由到錯誤軸 | 先 group ALL kwargs，再 dispatch |
| InfluenceApplicator `amount` 被忽略 | `influence_applicator.py` | `apply_influence_to_axis()` 只用 `weight * src_val`，忽略 `amount`，導致 18.7x 過強影響 | 改為 `amount * weight * src_val` |
| Smoke S1 使用錯誤軸字段 | `test_smoke_real.py` | `focus` 在 beta 不在 alpha，test 只驗證 size 不驗證值 | 改用正確字段，添加明確值斷言 |

---

## 🔵 已完成文檔

| 文檔 | 更新內容 |
|------|---------|
| REFACTORING_PLAN.md | v1.0 → v2.0，Phase 1-7 全部標記完成 + Post-Refactor Plan v1.0 完成 + Bug修復記錄 + 新建模組清單（14個檔案，3881行）|
| TASK_PRIORITY.md | 本檔案，標記 P1 + Post-Refactor 全部完成 |
| POST_REFACTOR_PLAN.md | 標記 v1.0 完成 |

---

## 新的行動計劃

### 立即可用

```python
from core.autonomous.state_matrix_adapter import StateMatrixAdapter

sm = StateMatrixAdapter()

# 新 API — 充分利用重構後的架構
sm.temporal_trend('alpha', 'energy', window=50)
sm.influence_compute('alpha', 'beta')
sm.allocation_decide(vector, 'task')
sm.apply_ripple(MathOp.MUL, result, cascade_targets=['alpha','beta','gamma'])
sm.full_report()
```

### 待處理

1. **StateMatrix4D 進一步清理** — 目前仍是 ~1832 行，方向 2 的最終目標（~500行）未達到
2. **Semantic Anchor 向量改進** — 目前 32 維向量只有 4-5 個非零值，導致相似度普遍偏低，ASSIGN 閾值 (0.7) 幾乎無法觸發
3. **RippleApplicatorRegistry** — 方向 2.5 跳過，未來可實現
4. **P2 迭代任務** — N.22.x 其餘任務在新架構上實現

---

## 關鍵原則（更新）

**Phase 1-7 + Post-Refactor Plan v1.0 完成，P1 障礙已清除。**

重構帶來的改變：
1. 新增軸 — 只需修改 YAML 配置 + 新 AxisField
2. θ自糾檢測 — 使用 TemporalState 的 trend/anomaly 查詢，不再暴力遍歷
3. 影響規則實驗 — 在 InfluenceApplicator 中動態配置
4. 歷史分析 — TemporalState 提供 trend/correlation/anomaly/drift 查詢
5. 單元測試 — 每個模組可獨立測試，tests/refactor/ 目錄下有完整覆蓋（71+ 測試）

**目標：重構已完成。現在可以用新架構實現 P2 迭代任務。**