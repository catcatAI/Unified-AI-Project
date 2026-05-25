# [DEPRECATED] Phase 9 — 架構一致性與版本治理（Architecture Consistency & Governance）

> **⚠️ 已被 `MASTER_CONSOLIDATED_PLAN.md` 取代 (2026-05-25)**  
> 此文件已被合併至全量計畫。請參閱 `MASTER_CONSOLIDATED_PLAN.md`。

> **基於**: `docs/FULL_ARCHITECTURE_ANALYSIS.md` §7 關鍵發現、§8 改進建議  
> **審計日期**: 2026-05-25  
> **當前架構一致性評分**: 62.6% — **目標**: 85%+

---

## 評分標準

| 維度 | 權重 | 說明 |
|------|------|------|
| **風險** | ×3 | 安全漏洞、運行時炸彈、資料遺失、版本誤判 |
| **耦合** | ×2 | 是否 blocking 其他任務 |
| **工時** | ×1 | 人天估算（越低分越好） |

**分數 = 風險×3 + 耦合×2 − 工時×1**

---

## S 級（本週 — 版本號統一陣線）

### S1. 統一全部 13 個版本號位置

| 文件 | 當前值 | 正確值 | 操作 |
|------|--------|--------|------|
| `VERSION` | 6.2.0 | **7.5.0-dev** | 純文字覆寫 |
| `config/angela_config.json` | 6.1.0 | **7.5.0-dev** | 改 `version` 字段 |
| `apps/backend/pyproject.toml` | 0.1.0 | **7.5.0-dev** | 改 `project.version` |
| `apps/backend/setup.py` | 0.1.0 | **7.5.0-dev** | 改 `version=` |
| `apps/backend/package.json` | 1.0.0 | **7.5.0-dev** | 改 `version` |
| `apps/backend/src/core/version.py` | 6.5.0-dev | **7.5.0-dev** | 改 `CURRENT_VERSION` |
| `apps/backend/src/core/__init__.py` | 6.2.0 | **7.5.0-dev** | 更新 docstring |
| `apps/desktop-app/electron_app/package.json` | 6.5.0-dev | **4.1.0-dev** | 實際成熟度 |
| `apps/mobile-app/package.json` | 6.5.0-dev | **1.2.0-dev** | 實際成熟度 |
| `packages/cli/package.json` | 1.0.0 | **1.1.0** | 與 `__init__.py` 統一 |

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🔴3 | 🔴3 | 0.5天 | **14.5** |

### S2. 修復 CHANGELOG v7.x 虛構版本

將 CHANGELOG 中 v7.2.0~v7.4.0 條目標註為 `[7.2.0] → Internal/Unreleased`，並在 `AGENTS.md` 增加規則：「禁止 AI 自行分配主版本號」。

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟡2 | 🟡2 | 0.3天 | **9.7** |

### S3. 建立 CI 版本一致性檢查

在 `.github/ci.yml` 中加入 step：對比全部版本位置是否一致，不一致則 fail。

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟡2 | 🔴3 | 0.5天 | **11.5** |

### S4. 合併 `config/` 與 `configs/` 雙目錄

| 步驟 | 操作 |
|------|------|
| 1 | 分析 `config/` 中未被 `configs/` 覆蓋的獨有文件 |
| 2 | 遷移獨有內容到 `configs/` |
| 3 | 更新所有引用路徑 |
| 4 | 刪除 `config/` 並在根目錄加入 `config → configs/` symlink（向後兼容） |

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟡2 | 🔴3 | 1天 | **11** |

---

## A 級（本月 — 架構健康度提升）

### A1. 拆分上帝模塊

| 檔案 | 當前行數 | 拆分方案 | 工時 |
|------|---------|---------|------|
| `main_api_server.py` | 1668 | → `api/lifespan.py` + `api/routes/*.py` + `services/websocket_manager.py` | 2天 |
| `angela_llm_service.py` | 2196 | → `services/llm/router.py` + `services/llm/providers/*.py` + `services/llm/prompt_builder.py` | 2天 |
| `core/autonomous/` | 60+ 文件 | → 按領域拆 `core/life/`, `core/bio/`, `core/engine/` | 2天 |

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟡2 | 🔴3 | 6天 | **6** |

### A2. 集成五大理論公式到 LLM Prompt

將 HSM Formula、CDM Dividend、Life Intensity、Active Cognition、Non-Paradox 的計算結果實際注入到 `_construct_angela_prompt()` 中。

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟡2 | 🟡2 | 1天 | **9** |

### A3. 補全 Matrix Annotation（4D → 8D）

更新 `ANGELA_MATRIX_ANNOTATION_GUIDE.md`，補充 εθζη 四維定義；掃描缺失註解的 `ai/` 子包補齊。

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟢1 | 🟡2 | 0.5天 | **6.5** |

### A4. 建立 `docs/ARCHITECTURE.md` 為單一事實來源（SSOT）

從 `FULL_ARCHITECTURE_ANALYSIS.md` §2 提取權威架構圖，濃縮為一份簡潔、開發者導向的 `docs/ARCHITECTURE.md`。

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟢1 | 🟡2 | 1天 | **6** |

---

## B 級（有時間再做）

### B1. 根目錄清理（143 條目 → <50）

| 動作 | 說明 |
|------|------|
| 搬 legacy 報告到 `reports/archive/` | ~20 個 MD 報告 |
| 搬獨立腳本到 `scripts/` | 根目錄零星 `.py` / `.sh` |
| 確保 `.github/`、`docs/`、`tools/` 覆蓋所有分類 |

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟢1 | 🟢0 | 0.5天 | **2.5** |

### B2. 整理 `docs/` 子目錄層級（179 文件 → 分類子目錄）

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟢1 | 🟢0 | 2天 | **1** |

### B3. 修 HSP `payload_schema_uri` 硬編碼

將 `core/hsp/` 中的 `hsp://` URI 改為動態 schema 註冊，與 `docs/HSP.md` 規範一致。

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟢1 | 🟢0 | 0.3天 | **2.7** |

### B4. 提升測試覆蓋率（目標 85%+）

優先補充 `core/`（當前 222 tests）和 `services/` 中大型模塊的測試。

| 風險 | 耦合 | 工時 | 分數 |
|------|------|------|------|
| 🟡2 | 🟢0 | 10天 | **-4** |

---

## 執行路線圖

```
Week 1: S1 (版本統一) + S2 (CHANGELOG) + S3 (CI檢查) + S4 (config合併)
        → 0.5 + 0.3 + 0.5 + 1.0 = 2.3 天，清掉 4 個 critical 問題

Week 2-3: A1 (拆上帝模塊) + A2 (公式集成)
        → 6 + 1 = 7 天，最大的架構健康度提升

Week 4:   A3 (Matrix 補全) + A4 (SSOT) + B1 (根目錄) + B3 (HSP)
        → 0.5 + 1 + 0.5 + 0.3 = 2.3 天，文檔與整理

Ongoing:  B2 (docs整理) + B4 (測試覆蓋率) — 可分散在 sprint 間隙
```

---

## 預期成果

| 指標 | 當前 | 目標 |
|------|------|------|
| 版本一致性 | 31% (13中4) | **100%** (CI 強制) |
| 架構一致性總分 | 62.6% | **85%+** |
| 上帝模塊 (1668/2196 行) | 2 個 | **0 個** (<500 行) |
| config/ 雙目錄 | 2 個 | **1 個** |
| docs/ARCHITECTURE.md SSOT | 不存在 | **存在且維護** |
| 理論公式集成 | 0% (定義未接線) | **100% 注入 Prompt** |
| 根目錄條目 | 143 | **<50** |
