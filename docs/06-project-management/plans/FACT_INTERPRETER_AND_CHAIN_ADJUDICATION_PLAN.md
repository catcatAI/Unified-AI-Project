# 事實解讀器與鏈式裁決 — 完整計畫（Spec / Plan）

> 狀態：計畫 → P0 開工中。目標：把「兩端都說有、中間壞了」這類問題變成**編譯期/CI 期錯誤**，而不是線上靈異事件。手段：一個很小的**事實裁決 IR + 參考解讀器**（先 stdlib Python，語法穩定後再下沉），統一收斂現有的三套同構 verdict 機制，並把地圖工具從報表升級成鏈的事實源。

- 作者：Angela AI Development Team
- 版本：7.5.0-dev
- ANGELA-MATRIX：`[L6] [βγδ] [A] [L3]`

---

## 0. 一句話總結

現有判定是分散的（CIM 的 `GateReport`、edge 卡的 `verdicts`、audit 的 `corrections` 各寫一套），且只看端點；本計畫新增一個**全量事實的單一裁決點**：所有事實（含中間過程條件）同時求值，一次輸出 verdict 向量 + 證據 + 出處。Python 繼續寫邏輯，**裁決只認解讀器的輸出**。

---

## 1. 現狀調查（實際讀碼，非猜測）

### 1.1 三套同構的 verdict 機制（解讀器雛形，已存在）

| 位置 | 形狀 | 全量/短路 | 出處 |
| ---- | ---- | --------- | ---- |
| `apps/backend/src/ai/hardware/cim_verify.py` `GateReport`（`verify_block:186`） | 每 gate `{name, guards_against, passed, detail}`，`ok` 為全過 | 全量（註解明說不取首敗） | 每 gate 自帶防何種失敗 |
| `hardware/edge_card/edge_card_spec.yaml` `host_proxy_simulation.verdicts` + `scripts/sim_edge_card_software.py:160` | `[{item, value, unit, target, pass}]`，`pass=None` 為 INFO | 全量 | spec 欄位 + 量測 |
| `apps/backend/src/ai/hardware/card_architecture_audit.py` `audit:457` | `corrections[{id, severity, claimed, recomputed, detail, source}]` | 全量 | 每條帶 source |

→ 結論：哲學一致（全量、帶出處），但語義各寫一套，沒有統一的「衝突怎麼裁」「INFO 擋不擋門」規則。

### 1.2 地圖工具（鏈的事實源，雛形已存在）

`scripts/gen_project_map.py`（stdlib-only，1322 行）：區塊一依賴（AST import）、區塊二碰撞索引（同檔名多路徑）、區塊三行為核心 + P2 區塊四實時結構（`--module` 查 callers/callees/測試映射）+ `STATUS_MATRIX` 核對門 + 萬行 `--budget 10000` 超標 exit 1。產物 `docs/PROJECT_MAP_GENERATED.md` 標 Generated、手不改。

缺口：只有「報表」，沒有「引用存在性」門（7 份 `hardware/ai_compute_card/*` spec 零引用無人知是死是活），沒有鏈展開（從欄位一路走到路由再到前端消費者仍靠人查）。

### 1.3 UI 鏈（最痛的黑箱）

`apps/backend/src/api/routes/` 10+ 路由檔 → `packages/shared-js` → Electron/Web 前端。現狀：無合約門。後端加欄位、前端漏渲染，測試全綠。AI 無法目視判斷「有沒有顯示」，只能比結構（DOM/繪製指令樹 diff），不能比像素。

### 1.4 全量覆蓋率（為什麼有些問題注定看不見）

實測（`pytest tests/ --cov=apps/backend/src`）：`TOTAL 86525 stmts / 30943 miss / 64.24%`，722 檔。缺口最大全是整合路徑（`services/llm/router.py` 881 行、`ai/autonomous/angela_agent.py` 821 行、`api/routes/chat_routes.py` 638 行）。結論：行覆蓋到 100% 是長期工程；解讀器先改追「門覆蓋」——每個 gate 都要有能讓它變紅的測試。

## 2. 目標與非目標

- 目標：① 統一事實 schema；② 參考解讀器（全量求值、單一 verdict 向量、帶證據）；③ 地圖變鏈源（引用存在性門 + 鏈自動展開）；④ UI 五段鏈每段獨立裁決（含結構快照）；⑤ 先接進 CI 當門，不新增依賴。
- 非目標：不造通用程式語言語法；不接管 CPython；不重寫現有 6800+ 測試；不做靜態最優調度（先用戶態 runtime + envelope 數學）；不比像素。

## 3. 設計

### 3.1 事實 schema（所有新 spec/斷言的強制欄位）

沿用三件套：`acceptance_levels L0-L4` + `sources{url, type}` + `explicit_non_claims`，加 `reads/writes`（事實依賴邊，供地圖展開）。每個事實：`id / value / target / unit / source / evidence / level`。

### 3.2 解讀器語義（v1，只四種）

- `all_must_pass[...]`：任一 FAIL → `BLOCKED`（如 edge 卡 envelope/decode/load）。
- `info(...)`：`pass=None`，只記錄不擋門（如 host ratio 換算值）。
- `conservative_wins`：衝突時取保守值當 gate、另一方降 INFO（如 full-file bound vs active-weights bound）。
- `chain[a → b → c → d → e]`：任一段 FAIL 即定位到段（UI 五段專用）。

輸出永遠是向量：`{ok, verdicts[{id, passed|INFO, value, target, evidence, source}], failed[...]}`，沿 `GateReport.as_dict()` 形狀。

### 3.3 地圖升級（兩道新門，不改現有預算門）

- `fact-refs` 門：程式讀的 spec 必須存在且凍結；spec 無人讀取標 `UNREFERENCED`（如那 7 份，先標不刪）。
- `chain` 查詢：`--module <欄位>` 展開 `code → serialized → transported → interpreted → rendered` 五段骨架，缺段即報。

### 3.4 UI 五段鏈（每段一事實）

`code_computed → serialized → transported → interpreted → rendered`。`rendered` 只比結構快照（DOM 樹/繪製指令序列），不比像素。前端型別由後端 response model 生成，漂移即 CI 紅燈。

### 3.5 與 Python/MLIR 的關係

表面永遠是 Python（`@angela.fact/@angela.chain` 只是宣告）；參考解讀器 stdlib-only；熱路徑穩定後才下沉 MLIR 方言（`angela.schedule/task/fact`，復用 `arith/memref/scf/gpu/async`），再 lower LLVM。Mojo/MLIR 是後端選項，不是前提。

## 4. 分階段

- **P0（本輪，已開工）：** `core/facts/` 參考解讀器 + 首條鏈（edge 卡 envelope：spec → sim → test → README 四段已同構，補成五段形狀）+ CI 門。驗收：硬體包維持 100%，edge 卡 17 測試全綠，新增解讀器自身 100%。
- **P1：** UI 合約門（挑一條活鏈，如某路由 → 前端對話框）+ 結構快照首版。
- **P2：** `fact-refs`/`chain` 兩道地圖門 + runtime envelope（桌面 GPU/LLM 路由）。
- **P3（長期）：** MLIR 方言 + Orin L1 量測回填，屆時再議獨立語法。

## 5. 驗收門（每段可獨立停）

- P0：`pytest` 相關測試全綠；`flake8/black/isort` clean；`mypy` 預算門過；`prettier --check` 過；解讀器覆蓋率 100%。
- P1：任改後端欄位不改前端即紅；快照 diff 可定位到段。
- P2：零引用 spec 全部標出；超顯存請求被拒絕而非炸機。

## 6. 風險

最大成本是生態與除錯（IDE、報錯、招人），不是編譯器本身。對策：語法凍結前只做 DSL 宣告 + 參考解讀器；真機（Orin）證明通用 MLIR 擺不平 CIM/MVU 語義前，不啟動獨立語法。

## 7. 實作現況

- P0 進行中：`apps/backend/src/core/facts/`（見該目錄） + `tests/core/test_fact_interpreter.py` 首條鏈（edge 卡 envelope 三 verdict 經解讀器重裁）。
