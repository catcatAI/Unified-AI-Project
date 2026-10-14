# 定義稽核報告 (Definitions Audit) — 2026-10-14

> 本檔由 `scripts/check_fact_gates.py --write-definitions-audit`
> **自動掃描生成**，請勿手改內容本體。重跑：`.venv/bin/python scripts/check_fact_gates.py --write-definitions-audit [<本檔>]`
> （寫出後自動跑 prettier
> --write，輸出即符合 CI 格式）分類：未定義／定義有誤／定義差（多重釋義：同對象於不同視角可多重詮釋）／定義合理。

## 摘要

| 桶                 | 項數               |
| ------------------ | ------------------ |
| 未定義             | 0                  |
| 定義有誤           | 21                 |
| 定義差（多重釋義） | 11                 |
| 定義合理（已驗證） | 23+ 處顯式定義標記 |

## 修復記錄（本次）

- `core/engine/state_matrix.py` —
  DEFAULT_DIMENSIONS（live 定義源）補齊 11 個使用中未定義槽：alpha+=vitality/tension、beta+=clarity/creativity、gamma+=love/calm、delta+=engagement/intimacy、theta+=doubt/caution/self_reflection/meta_accuracy（與 JS 鏡像同步）、zeta 改名 identity→identity_continuity
  (0.75)、memory_access→memory_depth
  (0.6)（舊名零讀寫者，新名為座標讀取器/影響規則/JS 正式名）
- `core/engine/state_matrix_types.py` —
  ① 座標 epsilon 雙讀 abstraction_level|abstraction 簡化為 abstraction（abstraction_level 為 YAML 草稿槽、epsilon 從未持有，雙讀永遠落 fallback）；②
  DimensionState.update() 靜默丟鍵改 logger.warning（未定義槽不再無聲消失）
- `ai/alignment/emotion_system.py` — influence_map 補 trust: (0.3, -0.1, 0.1) —
  apply_influence('interaction_feedback', 'trust', …) 先前查無此鍵 →
  PAD 漂移靜默 no-op；係數為標明的設計者 heuristic（正效價/低喚醒/微支配，同 oxytocin 型）
- `configs/standard/matrix/matrix.default.yaml`
  — 死配置對齊 live：gamma 補 disgust/surprise、epsilon complexity
  0.0→0.5、theta 換為正式 12 槽（棄 abstraction_level）、zeta temporal 0.8→0.5 /
  narrative
  0.7→0.5、cn_name 全數對齊 DEFAULT。weight/coordinate/anchor 維持原草稿值並在檔頭標明（接線＝行為變更，需人工定奪）
- `packages/shared-js/js/state-matrix.js` —
  θ 軸補 6 槽（novelty/complexity/ambiguity/dimension_fit/creation_urge/correction_urge）使後端 θ 狀態可同步進鏡像；epsilon
  complexity 0.0→0.5；zeta memory_depth 0.3→0.6、identity_continuity
  0.5→0.75；cn_name 對齊；修正檔頭錯誤標頭（γ 原標『物理维度』、δ 原標『精神维度-mood/…』與實際槽不符）（desktop 副本由 sync_shared_js.py 同步）
- `docs/00-overview/GLOSSARY.md` — 4 處失準數值改為實測：ED3N ~5,500→~7,500
  lines (26 files)、GARDEN ~2,600→~6,000 lines (9 files)、GVV 14/~62→16 files/85
  tests、StateMatrix
  1,244 行/6 軸→1,751 行/7 軸 αβγδεθζ；「8 軸尚未實作」改述為 ζ 已實作、η=Python 獨立子系統/JS 第 8 軸
- `core/i18n/locales/prompts.{zh-CN,en-US}.json`
  — 移除 4 個零引用死定義：angela.planning_error / generation_error /
  decompose_prompt / integrate_prompt（94→90 鍵，雙語 parity 維持 0）
- `services/llm/prompt_builder.py` — angela.bio.uninitialized 定義接線：bio
  dict 為空時回傳該模板（原註冊+locale 皆有、零渲染 = 死定義；現為 1 註冊 +
  1 呼叫）
- `tests/core/autonomous/test_state_matrix_adapter.py`
  — 錯軸/不存在槽名改正：alpha.focus→energy、gamma.excitement→happiness、epsilon.awareness→logic、zeta.surprise→temporal_coherence；專屬 zeta 測試改 memory_depth；temporal 記錄 focus→energy（原資料示範錯誤定義）
- `tests/core/backbone/test_subscriptions.py` —
  domain→axis 寫入測試資料 focus@alpha 改為 focus@beta +
  energy@alpha（同步機制不變，測試資料不再示範錯軸定義）

### 已評估、決策保留（非本次修復）

- **21 個孤兒事件**（emit 無 subscribe）：文件宣稱的閉環多以直接函數呼叫（PriorityNegotiator
  voter、get_system_health 等）實現，事件為遙測預留；新增 subscribe 屬行為變更，另案評估 —
  emit 無消費者目前無害（global_store.emit_event 無訂閱即 return）。
- **權重三方分歧**（Python 全 1.0 / YAML ε0.3θ0.8ζ0.2 / JS
  ε0.3θ0.2ζ0.3）：YAML 為死配置、JS 權重影響本地影響力衰減 — 統一即改行為，各保留現值。
- **matrix.default.yaml 未接線**：槽定義已與 DEFAULT_DIMENSIONS 完全對齊（對齊後接線＝行為不變），接線本身涉及 formula 配置載入器變更，另案處理。
- **StateMatrixAdapter 寬進 vs DimensionState 嚴格**：兩種 update 合約並存 —
  adapter 為 Phase
  7 代理層（dict 透傳），改為嚴格會破壞其既有用途，記錄為定義差。

## 一、未定義（使用中但無定義）

（無 — 全部使用中的定義皆可解析。）

## 二、定義有誤（有定義但錯誤／失準）

### 孤兒事件（emit 有、subscribe 無 → 發了無人聽）

- `causal.learned`
- `causal.prediction`
- `dli.feedback_processed`
- `dli.state_changed`
- `essence.generational_bloom`
- `essence.trace_recorded`
- `execution.gate_decided`
- `execution.result_recorded`
- `heartbeat.integration`
- `heartbeat.pulse`
- `intent.adjustment_computed`
- `intent.homeostatic_generated`
- `intent.outcome_recorded`
- `lifecycle.behavioral_adjustment`
- `lifecycle.interaction_recorded`
- `meta.closed_loop_adjusted`
- `meta.confidence_recorded`
- `meta.weighted_adjustment`
- `modality.gate_updated`
- `routing.context_prepared`
- `routing.telemetry`

（subscribe 無 emit：無）

> 決策：保留 — 見「已評估、決策保留」；emit 無消費者目前無害（無訂閱即 return）。

## 三、定義差（多重釋義 — 同對象、多視角／多源）

### 同名槽跨軸（同一詞、兩個測量點）

- `complexity` @ epsilon/theta
- `trust` @ delta/gamma

### 軸數規格分歧

- Python `StateMatrix4D` =
  7 軸；JS 鏡像另含 ['eta'] 軸；GLOSSARY「8 軸規格為理想目標」—
  η 在 Python 為獨立子系統 (eta_axis.py)、在 JS 為矩陣第 8 軸。
- 決策：保留各自現狀（改任一邊皆為行為變更），以本表記錄視角差異。

### 多重釋義詞表（人類視角 vs AI 機制視角）

| 詞         | 定義源                                                                                                      | 人類視角（世界為上下文）             | AI 視角（經人的過濾／代碼機制）                              |
| ---------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------ | ------------------------------------------------------------ |
| trust      | γ 軸槽（情感信任）/ δ 軸槽（社交信任）/ influence_map 類型 / EmotionType.TRUST；StateMatrix 槽 @gamma/delta | 感覺層：相信對方、放心交托（情感態） | 機制層：γ=主觀可信度訊號；δ=關係黏著度；influence=PAD 漂移量 |
| complexity | ε 軸槽（問題複雜度）/ θ 軸槽（認知複雜度）/ ripple schema；StateMatrix 槽 @epsilon/theta                    | 事情有多難懂                         | ε=輸入結構度量；θ=自身認知負荷——同一詞、兩個測量點           |
| stress     | influence_map 類型 / ac.stress_cap 鍵 / heartbeat 健康 / 生理 cortisol                                      | 感到緊繃、有壓力                     | 至少 3 個獨立機制各自記 stress，無共享狀態                   |
| engagement | δ 軸槽 / resp_msg_ratio 互動回饋 / avg_engagement 聚合；StateMatrix 槽 @delta                               | 對方有多投入這段互動                 | δ=關係參與度狀態；回饋比=訊號計算——狀態 vs 計量              |
| memory     | zeta memory_depth 槽 / HAM memory / vector store / dialogue context；GLOSSARY 條目                          | 記得什麼                             | 4 個不互通的儲存子系統各有一套 memory 語義                   |
| attention  | δ 軸槽 / mf_attention_weight（生命強度公式）/ 注意力機制；StateMatrix 槽 @delta                             | 注意力放在哪                         | δ=社交關注狀態；公式權重=喚醒係數——同名不同量綱              |
| calm       | γ 軸槽（本次補齊）/ influence_map 類型 (0.1,-0.2,0) / 失控優先級 calm routing；StateMatrix 槽 @gamma        | 平靜                                 | γ 槽=狀態量；influence=事件量；routing mode=行為策略         |
| identity   | zeta identity_continuity 槽 / soul_core IDENTITY / protocols identity_id                                    | 我是誰                               | zeta=敘事連續度量；soul_core=枚舉；identity_id=實體編號      |

### 語義／行為層多重定義（文件記錄）

- **update 語義二元**：`DimensionState.update()` 嚴格（未定義鍵丟棄）vs
  `StateMatrixAdapter._update_axis` 寬進（任意鍵皆收）vs JS `update*()`
  嚴格 — 三處同名 update、兩種合約。
- **權重三方分歧**：Python 全 1.0 vs matrix.default.yaml (ε0.3/θ0.8/ζ0.2) vs JS
  (ε0.3/θ0.2/ζ0.3)
  — 後兩者一為死配置、一影響 JS 本地影響力衰減；決策：各自保留現值（統一即行為變更），接線前需人工定奪。

## 四、定義合理（驗證通過）

- GLOSSARY 數值宣稱 5/5 項與實測一致。
- i18n prompt：使用 90 鍵、zh 90 / en 90、雙語 parity diff=0、未定義=0。
- magic_numbers：410 個使用中鍵、YAML 可解析 66、僅 inline
  default（設計如此，呼叫點有預設值）344、未定義且崩潰=0（所有取用器簽名帶 default 參數）。
- `get_parameter`：3 個呼叫鍵全部在 `_DEFAULT_THRESHOLDS`。
- `ResponseCategory`（apps/backend/src/ai/memory/memory_template.py）：模板 JSON 類別未定義=無。
- influence_map 有定義但目前無呼叫的類型（備用，非缺陷）：adrenaline, anger,
  boost, negative_thought, oxytocin, serotonin。
- 顯式定義標記（`定義（`/`Definition:`）共 23 處，格式良。

## 附錄：掃描事實

- StateMatrix 鍵：DEFAULT {'alpha': 6, 'beta': 6, 'gamma': 10, 'delta': 6,
  'epsilon': 6, 'theta': 12, 'zeta': 4}
- 事件：emit 25 / subscribe 4 → 孤兒 21
- 錯誤軸測試欄位 0；跨軸同名槽 2
