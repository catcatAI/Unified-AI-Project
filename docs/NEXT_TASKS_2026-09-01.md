<!--
  =============================================================================
  FILE_HASH: TASKS-20260901
  FILE_PATH: docs/NEXT_TASKS_2026-09-01.md
  FILE_TYPE: task-list
  PURPOSE: 基於 2026-09-01 審計報告的後續任務清單 — 按優先級排序，可直接轉 GitHub Issues
  VERSION: 7.5.0-dev
  STATUS: active
  LANGUAGE: zh-TW
  LAST_MODIFIED: 2026-09-01
  AUDIENCE: maintainers, agents
  =============================================================================
-->

# 後續任務清單 — 2026-09-01（基於審計報告）

> 來源：`docs/AUDIT_REPORT_2026-09-01.md §11`
> 每項含：背景 → 具體動作 → 驗收標準 → 預估工作量

---

## P0 — 本週（3 項）

### T-HYGIENE-1 — 清理 crystal-cards untracked 腳本

- **背景**: `git status` 顯示 6 個 `??` 腳本（`extracted-content.js`, `fix-content-quality.js` 等），為內容生成一次性工具但未提交/忽略。
- **動作**: 審視每個 `fix-*.js` 是否仍需；需保留則移至 `apps/crystal-cards/scripts/` 並提交，不需則加入 `.gitignore`。
- **驗收**: `git status --short` 無 `??`（或僅剩有意圖的 untracked）。
- **工作量**: S（<0.5d）

### T-DOC-1 — 測試數漂移 CI 門檻

- **背景**: 歷史曾 `4,499 vs 5,361` 漂移（`AUDIT_FINDINGS_2026-08-18:27`），現已收斂至 5,432±2，但無自動校驗。
- **動作**: 新增 `scripts/check_test_count.py`（`pytest --collect-only -q` vs `README.md`/`AGENTS.md` 宣稱值），加入 `.github/workflows/ci.yml`。
- **驗收**: 測試數漂移時 CI 失敗。
- **工作量**: S

### T-SEC-1 — 安全告警 CI 門檻

- **背景**: 72+ 告警已全綠，但無 CI 門檻防止回退。
- **動作**: GitHub 分支保護規則 + `dependabot`/`codeql` 檢查 required。
- **驗收**: 有 open alert 時 PR 無法 merge。
- **工作量**: S

---

## P1 — 本月（6 項）

### T-PRODUCT-1 — 明確 Angela AI vs Crystal Cards 產品邊界

- **背景**: 最近 20 commit 中 13 個為 crystal-cards，與後端 AI 共 repo 導致敘事分裂；`FRAMEWORK_OVERVIEW.md` 對此零提及。
- **動作**: 方案 A：在 `README.md`/`FRAMEWORK_OVERVIEW.md` 新增獨立章節說明 Crystal Cards 為「世界觀衍生遊戲，非 AI 核心」；方案 B：拆獨立 repo（`Angela-AI/Crystal-Cards` 已在 `package.json:homepage` 出現，暗示曾有此計畫）。
- **驗收**: 文件與 `git log --oneline -- apps/crystal-cards/` 現實一致；新人可分辨兩個產品。
- **工作量**: M（1-2d）
- **依賴**: T-HYGIENE-1

### T-PRODUCT-2 — Crystal Cards 獨立版本與 CHANGELOG

- **背景**: `apps/crystal-cards/package.json` 為 `1.0.0`，而根 `7.5.0-dev` 混淆；`CHANGELOG.md` 無 crystal-cards 條目。
- **動作**: 為 crystal-cards 建立獨立 `CHANGELOG.md` 或在根 CHANGELOG 分區；版本語意與 Angela AI 解耦。
- **驗收**: 版本號不混淆，發佈流程清晰。
- **工作量**: S

### T-DOC-2 — MD 膨脹歸檔（A 類）

- **背景**: `docs/MD_CONSISTENCY_REVIEW.md` 掃描出 163 份 `coverage=0.0` 且 tokens≥5（描述功能但原始碼無符號）。
- **動作**: 執行該報告 §4 的 A/B/C 分類；A 類（如 `multi-llm-api.md` 描述 `/api/llm/*` 但實際無此 endpoint）移至 `docs/09-archive/`。
- **驗收**: `coverage=0.0` 從 163 → <100；`audit` 類文件保留。
- **工作量**: M（2-3d，需人工逐份判斷）
- **依賴**: 無

### T-LINT-1 — .flake8 分階段收緊

- **背景**: `.flake8` ignore 37 條，使 `0 errors` 失真；`pyflakes` 實有 ~40 F401。
- **動作**: 階段 1：移除 `F401` ignore，批次清理 40 處未使用 import（沿用 `AUDIT_FINDINGS_2026-08-18:L8` 的 4 層防護方法）；階段 2：`E501`（行長）抽樣收緊。
- **驗收**: `pyflakes apps/backend/src` 0 警告；`flake8` 仍 0 errors 但含金量提升。
- **工作量**: M

### T-BACKBONE-1 — Backbone 拓撲文件

- **背景**: `core/backbone/` 17 檔取代 ~130 工廠，但 `ARCHITECTURE_AUDIT.md` 資訊流圖未涵蓋。
- **動作**: 新增 `docs/architecture/BACKBONE_TOPOLOGY.md`，含註冊拓撲圖 + `python -m core.backbone dump` 範例輸出 + `get_backbone()` 使用指南。
- **驗收**: 新人可據圖理解「誰註冊了什麼、誰依賴誰」。
- **工作量**: M

### T-PROC-1 — 分支與 PR 流程

- **背景**: 僅 `main` 單分支，無 feature branch/PR 痕跡；審計報告 §10 評為 🟡 中風險。
- **動作**: GitHub 保護 `main`（require PR + CI 綠），建立 `CONTRIBUTING.md` 分支策略。
- **驗收**: `git branch -a` 可見流程；`main` 不可直接 push。
- **工作量**: S

---

## P2 — 本季（5 項）

### T-AI-1 — SNN 開放域泛化迭代

- **背景**: `INTELLIGENCE_ASSESSMENT.md §1.1` 開放域泛化僅 1.0/10（改述/CJK 召回 ~11%），但關聯能力 1.0 已可測（`validate_association.py` 3 節點）。
- **動作**: ① `validate_association.py` 從 3 節點擴至更深鏈/更廣圖；② `association_train.json` 12K→更大規模 + 更多比較維度；③ 以 §4.1.2 四指標作回歸門檻。
- **驗收**: 關聯能力保持 1.0 且泛化 >1.0。
- **工作量**: L（1w+）

### T-AI-2 — 標準基準補齊

- **背景**: `IMPROVEMENT_ROADMAP §1.2` 列 9 項「無法驗證的優勢」（MMLU/HumanEval 等），每項需 100+ 題。
- **動作**: 引入 MMLU/HumanEval 子集作為 `scripts/benchmark_*.py` 新 domain。
- **驗收**: 每領域 100+ 題可重複基準。
- **工作量**: L

### T-DEBT-1 — 殘留 hack 清理

- **背景**: `__import__` 13 處 + `get_event_loop` 3 處 + `sleep` 8 處（見審計 §5.2 TD-2/3/4）。
- **動作**: 批次替換為標準 import / `get_running_loop` / `loop_sleep`。
- **驗收**: `grep -r "__import__\|get_event_loop\|time.sleep"` 在 `apps/backend/src` 0 命中（除註解/測試）。
- **工作量**: M

### T-OPS-1 — 字典/模型備份策略

- **背景**: `data/dictionaries/` 242K 條目（132 MB JSON）+ `models/*.npz` checkpoints 無備份策略。
- **動作**: 定時備份（`scripts/backup_checkpoints.py` + cron/GitHub Action）+ 還原演練。
- **驗收**: 可從備份還原並通過 `ED3NEngine.load()`。
- **工作量**: M

### T-TEST-1 — 測試覆蓋補齊

- **背景**: 309/504 檔案無對應測試（38.7% 缺口）。
- **動作**: 為 38.7% 缺口補 smoke/參數化測試，優先 `ai/ed3n`, `core/bio`, `services/handlers`。
- **驗收**: 缺口 38.7% → <20%（或行覆蓋 60%+）。
- **工作量**: L

---

## P3 — 持續（2 項）

### T-DOC-3 — 月度滾動審計

- **背景**: `AUDIT_FINDINGS_2026-08-18` 為優秀模板，應滾動執行。
- **動作**: 每月跑 `flake8/pyflakes/pytest + 模式掃描 + 設計意圖對照`，更新 `AUDIT_FINDINGS_YYYY-MM-DD.md`。
- **驗收**: 0 CRITICAL 持續。
- **工作量**: M/月

### T-PERF-1 — 基準納入 CI

- **背景**: `benchmark_ed3n_garden.py` 20/20（兩引擎 100%）為確定性引擎能力，需防回退。
- **動作**: CI 加入 `python scripts/benchmark_ed3n_garden.py --engine both` 並斷言 20/20。
- **驗收**: 基準回退時 CI 失敗。
- **工作量**: S

---

## AI 能力階梯任務（0~10 分級）

> **詳見** `docs/06-project-management/AI_CAPABILITY_LADDER.md` — 按分數段拆解，明確「現有/下一階/再下一階/LLM 層」。
> **一句話**：0~2 是已兌現的確定性能力（守），2~4 讓神經學會改述（懂），4~6 讓本地串成助手（用），6~ 讓外部 LLM 編排成產品（好用）。

### L0 — 0~2 現有（守成，1 週）

| ID | 任務 | 驗收 | 工作量 |
|----|------|------|--------|
| **L0-1** | `benchmark 20/20` 納入 CI | CI 斷言 20/20 | S |
| **L0-2** | `validate_association 1.0` 納入 CI | 4 指標全綠 | S |
| **L0-3** | 確定性引擎邊界測試補齊 | +10 邊界測試 | S |

### L1 — 2~4 本地可理解（1~2 月）

| ID | 任務 | 驗收 | 工作量 |
|----|------|------|--------|
| **L1-1** | 關聯訓練數據 12K→100K（14→30 維度） | 100K 訓練，關聯仍 1.0 | M |
| **L1-2** | 關聯鏈 3→50 節點（deep/branching/noisy） | deep ≥90% | M |
| **L1-3** | SNN-ONLY 改述/CJK 11%→40% | 召回 ≥40%，1.0→2.5 | L |
| **L1-4** | Hold-out 泛化驗證（80/20 切分） | gap <15% | M |
| **L1-5** | 字典去重與品質分 | 重複 <5% | M |
| **L1-6** | SharedLatentSpace 對比訓練 300→3,000 | loss <0.1 | M |

出階：改述 ≥40% + deep ≥90% + gap <15% → **1.0→3.0**

### L2 — 4~6 本地可用（2~3 月）

| ID | 任務 | 驗收 | 工作量 |
|----|------|------|--------|
| **L2-1** | 多輪一致性 5 輪 | 人設 ≥80% | L |
| **L2-2** | 記憶 top-5 命中 | ≥60% | L |
| **L2-3** | 純神經推理（關確定性）0%→50% | ≥50% | L |
| **L2-4** | 多模態 MSE 0.271→<0.05 | 可辨形狀 | L |
| **L2-5** | 本地小模型備選（Qwen2-0.5B/Phi-3） | <2s, <4GB | M |
| **L2-6** | 評測集 20→500 題 | HYBRID ≥60% | M |

出階：一致性 80% + 記憶 60% + 推理 50% + MSE<0.05 → **3.0→5.5**

### L3 — 6~10 LLM 編排（持續）

| ID | 任務 | 驗收 | 工作量 |
|----|------|------|--------|
| **L3-1** | MMLU/HumanEval 子集基準 | MMLU ≥50% | L |
| **L3-2** | 工具調用成功率 | ≥85% 崩潰 0 | M |
| **L3-3** | 多智能體協作 | ≥70% | L |
| **L3-4** | 長記憶跨會話 | ≥70% | L |
| **L3-5** | LLM 路由智能度 | 準確率 ≥80% | M |
| **L3-6** | 多模態 LLM 端到端 | 圖片問答可用 | M |

出階：MMLU 60% + 工具 85% + 協作 70% → **6.0→8.5**

---

## 研究課題（非任務，思考方向）

| 課題 | 問題 | 思考 |
|------|------|------|
| **R-1** | Monorepo 邊界 | Angela AI 與 Crystal Cards 是否應物理分離？`pnpm-workspace` 已支持 `apps/*`，但 git 歷史/CI/版本/文件已開始互相污染。 |
| **R-2** | SNN 的角色 | 既然確定性引擎已覆蓋 20/20 benchmark，SNN 的長期定位是「關聯性專職」還是應重新定位為「學習型泛化器」？`INTELLIGENCE_ASSESSMENT §4.1.2` 已給出正確度量，但訓練管線仍以 Q→A 映射為主，與「關聯性」定位不一致。 |
| **R-3** | 文件即代碼 | 670 MD 的維護成本已超過代碼；是否應引入「MD 即代碼」校驗（如 `md_consistency_check.py` 強制 CI）而非人工同步？ |
| **R-4** | 商業化路徑 | 當前「6.0/10 有 LLM API，1.0/10 無 LLM」意味著無 API key 時產品價值有限；是否應明確「Angela AI = 框架 + 需自帶 LLM」而非「開箱即用 AI」？`README.md:68` 已誠實標註，但行銷敘事仍易誤導。 |
| **R-5** | 階梯可信度 | 0~2/2~4/4~6/6~ 的分數是否應與 `AI_CAPABILITY_LADDER.md` 的可量測門檻強綁定，而非沿用 `INTELLIGENCE_ASSESSMENT §1.3` 的定性描述？ |

---

> **下一步**: 將 P0 3 項直接建為 GitHub Issues（標籤 `priority:P0` + `area:hygiene/docs/security`），P1/P2 依人力排期。
