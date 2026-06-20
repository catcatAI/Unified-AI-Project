# Angela AI 專案全面分析與修復計畫 v6.13

> **生成日期**: 2026-06-20 (第10輪 N3 導入路徑 — 腳本修復)  
> **分析範圍**: 5 個腳本導入路徑統一 + 2 個預先存在腳本 bug 修復  
> **專案版本**: 7.5.0-dev  

---

## 1. 測試健康度 ✅ 9.6/10

| 指標 | 數值 | 狀態 |
|------|------|------|
| unit+api 測試 | **724 通過, 0 失敗, 39 跳過** | ✅ **100%** |
| ED3N 引擎測試 | **114/114 通過** | ✅ |
| GARDEN SNN Core | **34/34 通過** | ✅ |
| GARDEN 引擎測試 | **197/197 通過** | ✅ |
| GARDEN 字典測試 | **31/42 通過** (11 torch 不可用) | 🟡 numpy fallback 就緒 |
| VectorStore | **chromadb 1515 向量, 搜索 ✅** | ✅ **語義搜索啟用** |
| 預先存在失敗修復 | 53 個 (無新增) | ✅ |

## 2. 第10輪變更詳情 (N3-A)

| 變更 | 檔案 | 影響 |
|------|------|------|
| **N3-A: import 路徑統一** | `scripts/train_ed3n.py` ✅ | `apps.backend.src.ai.ed3n.*` → `ai.ed3n.*` |
| **N3-A: import 路徑統一** | `scripts/train_pipeline.py` ✅ | 8 處 `apps.backend.src.*` → 短格式 |
| **N3-A: import 路徑統一** | `scripts/debug_memory.py` ✅ | `apps.backend.src.ai.memory.*` → `ai.memory.*` |
| **N3-A: import 路徑統一** | `scripts/utils/init_config.py` ✅ | + sys.path 設置 + 短格式導入 |
| **N3-A: import 路徑統一** | `scripts/analyze_roadmap_from_logs.py` ✅ | 固定 sys.path + 匯入不存在模組的處理 |
| **預先存在 bug 修復** | `scripts/utils/init_config.py` ✅ | `Config` → `AngelaConfig`, `validate()` 不存在方法修復 |
| **預先存在 bug 修復** | `scripts/analyze_roadmap_from_logs.py` ✅ | `HybridBrain` 不存在 → 優雅降級 |

## 3. 代碼品質 🟡 8/10

| 指標 | 數值 | 狀態 |
|------|------|------|
| 重複代碼消除 | 2 處 → 1 共用 | ✅ |
| Python 3.14 相容性 | numpy fallback 就緒 | ✅ |
| VectorStore chromadb | 完整 read/write/query 支援 | ✅ |
| N3 導入路徑 (腳本) | **5/5 腳本已修復** | ✅ |
| N3 導入路徑 (測試) | 169 處剩餘 | 🟡 待解決 |

## 4. 智能水準 🟡 4/10

無變化。腳本導入路徑統一提升了可維護性。

## 5. 關鍵問題矩陣 (v6.13)

| ID | 問題 | 優先級 | 狀態 |
|----|------|--------|------|
| N8 | LLM API 金鑰 | P0 | ✅ OPENAI + GEMINI 啟用 |
| — | VectorStore 種子 | P1 | ✅ 1515 向量就緒 |
| N7 | 引擎回應不一致 | P2 | ✅ 雙語 fallback |
| N3 | 174 導入路徑不一致 | P2 | 🟡 **5/174 已修復** |
| — | GARDEN 字典 11 測試 | P3 | 🟡 torch 不可用時遺留 |

## 6. 十輪修復總計

| 輪次 | 主要內容 | 成效 |
|------|---------|------|
| 1-6 | 測試修復 + 清理 | 724/724 通過, 48 修復 |
| 7 | LLM + 引擎統一 | OpenAI 啟用, 雙語 fallback |
| 8 | 去重 + Python 3.14 相容 | SNN 34/34, GARDEN numpy fallback |
| 9 | VectorStore 種子 + 語義搜索 | chromadb 1515 向量, 搜索驗證 |
| **10** | **N3-A: 腳本導入路徑統一** | **5/5 腳本, 2 預先存在 bug 修復** |
| **總計** | **10 輪, 10 commits** | **53+ 預先存在失敗修復, 14 檔案修改** |

## 7. 後續建議

1. 啟動後端並測試 OpenAI/Gemini 端到端整合
2. 完整種子所有字典 (分批執行避開 chromadb 瓶頸)
3. N3-B/C: 測試檔案導入路徑統一 (169 處剩餘) — 低優先級
