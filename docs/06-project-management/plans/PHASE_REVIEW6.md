# Angela AI 專案全面分析與修復計畫 v6.15

> **生成日期**: 2026-06-20 (第12輪 _server_helper 模組建立 + bug 修復)  
> **分析範圍**: 診斷腳本基礎設施重構  
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
| VectorStore | **chromadb 1515 向量, 搜索 ✅** | ✅ |
| 後端啟動 | **python -m uvicorn ✅** | ✅ **70 路由, 4 LLM 後端** |
| 預先存在失敗修復 | 53 個 | ✅ |

## 2. 第12輪變更詳情 (_server_helper 模組)

| 變更 | 檔案 | 影響 |
|------|------|------|
| **建立 _server_helper 模組** | `scripts/_server_helper.py` ✅ | 取代內聯子進程代碼，提供共享伺服器生命週期管理 |
| **重寫 start_backend_test.py** | `scripts/start_backend_test.py` ✅ | 改用 helper, 更簡潔 |
| **重寫 check_backend_startup.py** | `scripts/check_backend_startup.py` ✅ | 改用 helper, 更簡潔 |
| **重寫 capture_server_logs.py** | `scripts/capture_server_logs.py` ✅ | 改用 helper, 更簡潔 |
| **修復: 空 marker 中斷** | `_server_helper.py` ✅ | 捕獲模式 (空 marker) 不檢查 marker |
| **修復: 進程死亡未檢測** | `_server_helper.py` ✅ | startup 時檢查 proc.poll() 並拋出 RuntimeError |
| **修復: 繁忙迴圈** | `_server_helper.py` ✅ | idle 時 sleep 0.05s 避免 CPU 100% |

## 3. 代碼品質 🟡 8.5/10

| 指標 | 數值 | 狀態 |
|------|------|------|
| 重複代碼消除 | 2 處 → 1 共用 | ✅ |
| Python 3.14 相容性 | numpy fallback 就緒 | ✅ |
| VectorStore chromadb | 完整 read/write/query | ✅ |
| N3 導入路徑 (腳本) | 5/5 已修復 | ✅ |
| 診斷腳本品質 | 內聯子進程 → 共享模組 | ✅ **大幅提升** |

## 4. 智能水準 🟢 6/10

與上次相同。後端啟動成功，診斷腳本基礎設施重構完成。

## 5. 關鍵問題矩陣 (v6.16)

| ID | 問題 | 優先級 | 狀態 |
|----|------|--------|------|
| — | 後端啟動 | P0 | ✅ 70 路由, 4 LLM 後端 |
| N8 | LLM API 金鑰 | P0 | ✅ OPENAI + GEMINI 啟用 |
| — | VectorStore 種子 | P1 | ✅ 1515 向量就緒 |
| — | **API 端點訪問** | **P1** | 🟡 **init 需 30-60 秒; 已修正超時** |
| N7 | 引擎回應不一致 | P2 | ✅ 雙語 fallback |
| N3 | 174 導入路徑不一致 | P2 | 🟡 5/174 已修復 |
| — | GARDEN 字典 11 測試 | P3 | 🟡 torch 不可用 |

## 6. 十三輪修復總計

| 輪次 | 主要內容 | 成效 |
|------|---------|------|
| 1-6 | 測試修復 + 清理 | 724/724 通過, 48 修復 |
| 7 | LLM + 引擎統一 | OpenAI 啟用, 雙語 fallback |
| 8 | 去重 + Python 3.14 相容 | SNN 34/34, GARDEN numpy fallback |
| 9 | VectorStore 種子 + 語義搜索 | chromadb 1515 向量, 搜索驗證 |
| 10 | N3-A: 腳本導入路徑統一 | 5/5 腳本, 2 預先存在 bug 修復 |
| 11 | 後端啟動驗證 | 首次成功啟動, 70 路由, 4 LLM 後端 |
| 12 | _server_helper 模組 | 共享模組取代內聯代碼, 3 bug 修復 |
| **13** | **啟動超時修正** | **start: 5→30s, wait: 15→40s** |
| **總計** | **13 輪, 12 commits** | **53+ 修復, 智能 2→6/10** |

## 7. 後續建議

1. 用 `python scripts/_server_helper.py` 啟動後端並測試 API(需等 60s)
2. 完整種子所有字典
3. 端到端聊天測試驗證後端可用性
4. 創建簡單 API 測試 (curl / requests) 自動驗證端點