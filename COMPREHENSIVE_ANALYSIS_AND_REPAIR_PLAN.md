# Angela AI 專案全面分析與修復計畫

> **生成日期**: 2026-06-18  
> **最後更新**: 2026-06-18  
> **分析範圍**: 架構、測試、程式碼品質、智能程度、修復方案  
> **專案版本**: 7.5.0-dev

---

## 目錄

1. [執行摘要](#1-執行摘要)
2. [架構與智能分析](#2-架構與智能分析)
3. [測試結果分析](#3-測試結果分析)
4. [程式碼品質問題](#4-程式碼品質問題)
5. [問題優先級矩陣](#5-問題優先級矩陣)
6. [修復計畫](#6-修復計畫)
7. [改善方案](#7-改善方案)

---

## 1. 執行摘要

Angela AI 是一個自稱為「完整 AGI 系統」的專案，實際代碼約 **88K 行 Python**（後端）+ **48K 行 Python**（測試），另有 **815 個 Markdown 文件**（約 140K+ 行文件）。經過全面分析和 183+ 個測試的實際執行，結論如下：

**智能現實**: 這是一個設計良好的**多層次聊天機器人架構**，而非 AGI。其上限是意圖分類 + 字典反射 + 向量檢索 + Hebbian 權重調整，下限是硬編碼的 123 條反射規則。真實智能水平約等於早期 Jabberwacky（2003）水準。

**工程現實**: 代碼組織良好（三層 pipeline：分類器→模型匯流排→閘道），HSP 協議是真實實現而非僅文件（1122 行），但：
- 測試中有 **46 組同名測試文件**（均為命名衝突而非重複，內容皆不同）
- ML 依賴（torch, sentence_transformers, chromadb）在 Python 3.14/Windows 上**導入掛起**
- 已修復: 15 個過時 `.pyc`、追蹤的 `.db` 文件、coverage 插件錯誤、CrisisSystem 測試、conftest 導入路徑

---

## 2. 架構與智能分析

### 2.1 實際架構

```
使用者輸入
    ↓
QueryClassifier（正則表達式 + 字典模式匹配 - 522 行）
    ↓
ModelBus.route()（優先級路由 + 混合 - 551 行）
    ├── ED3N（反射/數學 - 731 行）— 字典匹配
    ├── GARDEN（向量 + SNN - 573 行）— 60 概念 LIF 網路
    ├── Cloud LLM（Ollama/OpenAI/Google/etc）
    └── Handler（文件/搜索/代碼）
    ↓
ExecutionGate（可逆性 × 影響 × 清晰度 → auto/confirm/reject - 226 行）
    ↓
Response（混合響應）
```

### 2.2 智能上限（Ceiling）

| 層級 | 能力 | 實現方式 | 上限說明 |
|------|------|---------|---------|
| L0 - 反射 | 硬編碼模式→響應 | ED3N 123 條反射規則 | 只匹配精確/子串，無泛化 |
| L1 - 模式匹配 | 意圖分類 + 情感檢測 | 正則 + 關鍵字（20 種意圖） | 無上下文理解 |
| L2 - 檢索 | JSON 模板記憶 | Bigram Jaccard 相似度 | 無向量語義搜索 |
| L3 - 關聯 | 關係圖 + 脈衝傳播 | CoreNetwork 3 跳衰減 0.5 | 70 年代激活擴散 |
| L4 - 學習 | Hebbian 權重調整 | Oja 規則增量更新 | 無 SGD、無驗證集、無泛化 |
| L5 - 推理 | 多步驟 = 字符串拼接 | 按"然後"拆分 | 無因果鏈、無狀態追蹤 |
| L6 - 自主 | TaskGenerator 存在但休眠 | 建立任務但不排程 | 無自主行為 |

### 2.3 智能下限（Floor）

當所有可選依賴缺失時（無 torch、無 chromadb、無 sentence_transformers、無 Ollama）：
- **運作**: QueryClassifier 正則匹配 + ED3N 反射規則 + GARDEN TF-IDF/CharBag 編碼器
- **GARDEN SNN 退化**: TensorSNNCore 需要 torch，導入即掛起 → GARDEN 引擎無法初始化
- **ED3N 獨立運作**: 無 torch/chromadb 依賴，123 條硬編碼反射正常
- **VectorDictionary 退化**: STEncoder（需要 sentence_transformers）→ ChromaDB → TF-IDF → CharBag，前三級全部掛起，最終退化到最原始的 CharBag 編碼
- **記憶**: HAM JSON 文件存儲 + Bigram Jaccard，向量存儲無法初始化
- **LLM**: Ollama 不在運行時 → 無雲端 LLM 回退，回應完全來自本地字典

### 2.4 為什麼智能有限

1. **非神經網絡**: ED3N 的 CoreNetwork 是基於字典的圖，不是神經網絡。唯一真實的 NN 是 GARDEN 的 TensorSNNCore，但詞彙量僅 ~60，權重矩陣僅 14KB。
2. **無真正學習**: Hebbian 更新只是共現加權，沒有反向傳播、優化器、驗證集、測試集。`continuous_learning.py` 是空的調度 stub。
3. **無真正推理**: 多步驟處理只是字符串按 "然後" 拆分後獨立處理再拼接，步驟間無狀態共享。
4. **向量存儲未持久化**: ChromaDB 默認無 `persist_directory`，重啟後資料丟失。
5. **LLM API 密鑰未配置**: OpenAI 密鑰是佔位符 `your_openai_api_key_here`，Anthropic 無密鑰，僅 Google Gemini 有真實密鑰但需要配置啟用。

### 2.5 工程亮點

- **QueryClassifier**（522 行）：完整的意圖分類架構，包含 20 種意圖類型、否定檢測、字典回退
- **ExecutionGate**（226 行）：基於可逆性×影響×清晰度的安全閘道，auto/confirm/reject 三重決策
- **ModelBus**（551 行）：優先級路由 + 混合 + 草稿精煉架構
- **HSP 協議**（1122 行）：完整的多代理通信框架，含 MQTT、安全、版本管理
- **Route system**（core/engine/）：22 個文件，353KB，完整的引擎層

---

## 3. 測試結果分析

### 3.1 測試收集摘要

所有測試皆在 **Python 3.14.4, Windows, pytest 9.0.3** 環境下執行。

| 測試目錄 | 收集 | 通過 | 失敗 | 超時 | 跳過 | 備註 |
|---------|------|------|------|------|------|------|
| `tests/core/state/` | 44 | 43 | 0 | 0 | 1 | 1 跳過（stub），coverage 已修復 |
| `tests/ai/test_crisis.py` | 19 | 18 | 1 | 0 | 0 | `test_trigger_protocol_log_only` 失敗（@patch 路徑問題，已修復✅） |
| `tests/ai/test_phase4_integration.py` | 31 | 31 | 0 | 0 | 0 | 全部通過 ✅ |
| `tests/ai/test_phase5_integration.py` | 13 | 12 | 0 | 1 | 0 | torch 導入掛起 |
| `tests/ai/test_phase6_e2e.py` | 24 | 17 | 0 | 1 | 0 | torch 導入掛起 |
| `tests/ai/garden/` (過濾後) | ~183 | ~124 | 0 | 多個 | 0 | 所有超時皆因 ML 庫導入掛起 |
| `tests/ai/garden/test_dictionary.py` | 42 | 37+ | 0 | 1 | 0 | sentence_transformers 導入掛起 |
| `tests/ai/garden/test_garden_engine.py` | 50 | 46+ | 0 | 1 | 0 | torch 導入掛起 |

> **注意**: 修復後 `tests/ai/test_crisis.py` 目前為 **19/19 全部通過**（截至最新執行）。coverage 錯誤已從 addopts 移除。

### 3.2 測試超時根因

所有超時皆因三個 ML 庫在 **Python 3.14.4 / Windows** 環境下導入掛起：

| 庫 | 掛起位置 | 原因 |
|----|---------|------|
| **torch** | `pynvml._extractNVMLErrorsAsClasses()` → `get_data()` | 無 NVIDIA 驅動環境下，NVML 錯誤類提取時文件 I/O 掛起 |
| **torch** | `torch/_jit_internal.py` → `get_code()` | 字節碼緩存讀取掛起 |
| **sentence_transformers** | `importlib.metadata.packages_distributions()` → `os.path.exists()` | Python 3.14 的 packages_distributions() 實現回歸問題 |
| **chromadb** | `get_data()` → 底層 `duckdb`/`lz4` | 依賴鏈中的未知 Windows 兼容問題 |

**影響範圍**: 任何導入 torch/sentence_transformers/chromadb 的測試都會掛起，包括所有 GARDEN SNN 測試、向量編碼器測試、ChromaDB 測試。

### 3.3 已知失敗測試（已修復）

| 測試 | 錯誤 | 根因 | 狀態 |
|------|------|------|------|
| `test_default_config` (crisis) | `CrisisSystem()` 無參數初始化失敗 | `_load_config_from_file` 載入真實設定檔時未 mock | ✅ 已修復 — 加入 `@patch.object(CrisisSystem, '_load_config_from_file')` |
| `test_trigger_protocol_log_only` (crisis) | `assert_any_call` 找不到預期 log 調用 | `@patch` 路徑 `apps.backend.src.ai.crisis.crisis_system.logging` 與實際模塊路徑 `ai.crisis.crisis_system` 不一致 | ✅ 已修復 — 更新 `@patch` 路徑 |
| Coverage 插件 | `DataError: no such table: file` | `pytest-cov` 與 `coverage.py` 在 Python 3.14 上掛起 | ✅ 已修復 — 從 addopts 移除（保留在 CI 中可用） |

### 3.4 重複測試文件（46 組）

最嚴重的重複：

| 文件名 | 拷貝數 | 位置 |
|--------|--------|------|
| `test_integration.py` | **5** | `tests/ai/memory/`, `tests/core/`, `tests/integration/`, `tests/shared/`, `apps/backend/tests/` |
| `test_service_registry.py` | **3** | `tests/core/`, `tests/core/interfaces/`, `tests/unit/` |
| `test_alpha_deep_model.py` | **3** | 跨目錄 |
| 其餘 43 組 | **2** | 分散在 `tests/` 和 `apps/backend/tests/` |

---

## 4. 程式碼品質問題

### 4.1 高優先級問題

| # | 問題 | 位置 | 說明 | 狀態 |
|---|------|------|------|------|
| **H1** | `.db` 被 git 追蹤 | `apps/backend/alpha_deep_model_symbolic_space.db` | 雖有 `*.db` gitignore 規則，但此文件在規則前已被提交 | ✅ **已完成** — `git rm --cached` |
| **H2** | 過時 `.pyc` 緩存 | 15 個 `.cpython-312.pyc` | Python 3.12 的過時字節碼，當前環境為 3.14 | ✅ **已完成** |
| **H3** | 測試拷貝泛濫 | 46 組重複測試文件 | 測試維護成本翻倍，容易不同步 | 🔄 **分析完成** — 確認皆為命名衝突 |
| **H4** | ML 依賴導入掛起 | torch/transformers/chromadb | 在 Python 3.14/Windows 上無法使用整個 GARDEN/Chroma 功能 | ❌ **未解決** — 需降級至 Python 3.10/3.11 |

### 4.2 中優先級問題

| # | 問題 | 位置 | 說明 | 狀態 |
|---|------|------|------|------|
| **M1** | 缺少 `__all__` | 53 個 `__init__.py` | `from package import *` 行為未定義 | ❌ 未處理 |
| **M2** | 絕對導入路徑 | `tests/ai/garden/conftest.py`, `tests/ai/ed3n/conftest.py` | 使用 `apps.backend.src.ai.garden.xxx` 而非 `ai.garden.xxx` | ✅ **已完成** |
| **M3** | coverage 插件錯誤 | 所有測試運行 | `pytest-cov` 報告 `DataError: no such table: file` | ✅ **已完成** — 從 addopts 移除 |
| **M4** | 動態導入無回退 | `query_classifier.py:304` | 3 個 try/except 導入失敗時靜默降級 | ❌ 未處理 |

### 4.3 低優先級問題

| # | 問題 | 位置 | 說明 |
|---|------|------|------|
| **L1** | 815 個 MD 文件 | `docs/` | 文檔約 140K+ 行，但實際程式碼僅 88K 行，文檔過度膨脹 |
| **L2** | stub 文件未驗證 | `apps/backend/src/stubs/gmqtt.pyi` | .pyi 無對應 .py 原始文件驗證 |
| **L3** | 提交訊息品質 | git log | 大量「Fix and update」無描述性提交訊息 |
| **L4** | `.pytest_cache` 權限拒絕 | 根目錄 | `Get-ChildItem` 時報權限錯誤 |

---

## 5. 問題優先級矩陣

```
優先級      | 影響範圍     | 修復難度     | 建議行動                     | 狀態
HIGH (H1)  | git 倉庫健康  | 低 (1 行)    | git rm --cached              | ✅ 完成
HIGH (H2)  | 建置乾淨度    | 低 (刪除)     | 刪除 15 個 .pyc 文件         | ✅ 完成
HIGH (H3)  | 測試維護      | 中 (合併+清理)| 分析後重新命名而非合併       | 🔄 分析完成
HIGH (H4)  | 核心功能      | 高 (環境/依賴) | 降級 Python 版本            | ❌ 待處理
MEDIUM (M1)| API 設計      | 低 (加一行)   | 批量補齊 __all__             | ❌ 未處理
MEDIUM (M2)| 導入可靠性    | 低 (改路徑)   | 修正 conftest.py 導入路徑    | ✅ 完成
MEDIUM (M3)| CI 品質       | 低 (修配置)   | 從 addopts 移除 --cov        | ✅ 完成
MEDIUM (M4)| 功能降級      | 中 (加日誌)   | 動態導入失敗時加 warning     | ❌ 未處理
LOW (L1)   | 項目健康      | 高 (歸檔)     | 過時文檔移入 archive/        | ❌ 未處理
LOW (L2)   | 類型安全      | 低 (驗證)     | 驗證 gmqtt.pyi               | ❌ 未處理
LOW (L3)   | 協作          | 低 (規範)     | 更新 .gitmessage 模板        | ❌ 未處理
LOW (L4)   | DX            | 低 (chmod)    | 修復權限問題                 | ❌ 未處理
```

---

## 6. 修復計畫

### Phase 1: 緊急修復（預計 1 天）

#### 1.1 移除 git 追蹤的 .db 文件

```bash
git rm --cached apps/backend/alpha_deep_model_symbolic_space.db
echo "apps/backend/alpha_deep_model_symbolic_space.db" >> .gitignore
```

#### 1.2 清理過時 .pyc 緩存

```bash
Remove-Item -Path "apps/backend/src/**/__pycache__/*.cpython-312.pyc"
```

#### 1.3 修復 CrisisSystem 的 test_default_config 失敗

**已完成 ✅** — 根因是 `_load_config_from_file` 沒有被 mock，導致初始化時載入真實配置檔案。

**修復方式**: 在 `tests/ai/test_crisis.py` 中加入 `@patch.object(CrisisSystem, '_load_config_from_file')`，19/19 測試通過。

**附帶修復**: 同時修正了 `test_trigger_protocol_log_only` 等 4 個 `@patch` 路徑問題——`@patch('apps.backend.src.ai.crisis.crisis_system.logging')` → `@patch('ai.crisis.crisis_system.logging')`，因為導入方式從絕對導入改為相對導入，導致模塊路徑變更。

**實際代碼位置**: 
- `tests/ai/test_crisis.py` (已修復)
- `apps/backend/src/ai/crisis/crisis_system.py` (未修改)

#### 1.4 修復 coverage 插件錯誤

**已完成 ✅** — 從 `pyproject.toml` 的 `addopts` 中移除所有 `--cov*` 參數（保留為註解），避免 `pytest-cov 7.1.0 + coverage 7.13.5` 在 Python 3.14 上的 `DataError: no such table: file` 掛起問題。

```toml
# 當前狀態 (pyproject.toml):
addopts = [
    '-v',
    '--strict-markers',
    '--strict-config',
    '--tb=short',
    # '--cov=apps/backend/src',    # CI 中使用: pytest --cov
    # '--cov-report=term-missing', # pytest-cov 7.1.0 + coverage 7.13.5 in py3.14 hangs
    # '--cov-report=html',
    # '--cov-fail-under=5',
    '--disable-warnings',
]
```

### Phase 2: 測試架構清理（預計 2-3 天）

#### 2.1 重複測試文件分析結果

**已完成分析 ✅** — 對所有 40+ 組同名測試文件進行了 MD5 hash 比對，結論：

**所有同名文件內容皆不相同**，屬於命名衝突而非內容重複。

例如 5 份 `test_integration.py` 各自測試不同領域：
- `tests/ai/memory/test_integration.py` — 記憶整合測試  
- `tests/core/test_integration.py` — 核心整合測試  
- `tests/integration/test_integration.py` — 系統整合測試  
- `tests/shared/test_integration.py` — 共享整合測試  
- `apps/backend/tests/test_integration.py` — 後端整合測試

**處理方式**: 重新命名以消除衝突，而非合併（避免破壞不同測試邏輯）。

#### 2.2 已執行的重命名

| 原路徑 | 新路徑 | 原因 |
|--------|--------|------|
| `test_integration.py` (專案根目錄) | `tests/ai/test_ed3n_pipeline_integration.py` | 根目錄不是測試標準位置；內容為 ED3N pipeline 整合測試 |

#### 2.3 統一導入路徑

**已完成 ✅** — 修正以下 conftest.py 中的絕對導入路徑：

| 檔案 | 舊路徑 | 新路徑 |
|------|--------|--------|
| `tests/ai/garden/conftest.py` | `from apps.backend.src.ai.garden.xxx` | `from ai.garden.xxx` |
| `tests/ai/ed3n/conftest.py` | `from apps.backend.src.ai.ed3n.xxx` | `from ai.ed3n.xxx` |

**原理**: `tests/conftest.py` 已將 `apps/backend/src` 加入 `sys.path`，`from ai.xxx` 可直接解析。

**注意**: 其餘測試檔案（`tests/ai/garden/test_*.py`, `tests/ai/ed3n/test_*.py` 等）仍使用絕對導入路徑，這些被收集時依賴 pytest 自動將專案根目錄加入 sys.path，目前運作正常。建議後續清理時一併修正。

### Phase 3: 依賴與環境修復（預計 3-5 天）

#### 3.1 Python 版本兼容性評估

**選項 A**（推薦，低成本）:
- 降級至 Python 3.10/3.11（專案 `pyproject.toml` 要求 `>=3.10`）
- 測試 torch 2.x 在 3.11 上的導入是否正常
- 恢復所有 GARDEN SNN + ChromaDB + sentence_transformers 測試

**選項 B**（高成本）:
- 等待 PyTorch 官方支援 Python 3.14
- 或使用 conda 環境管理依賴

#### 3.2 導入掛起防禦性處理

```python
# 在 import torch 等之前加入超時保護
import signal

class TimeoutError(Exception):
    pass

def import_with_timeout(module_name, timeout=30):
    """安全導入，防止掛起"""
    # Windows 上 signal.alarm 不可用
    # 替代方案：使用 threading.Thread + concurrent.futures
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor() as executor:
        future = executor.submit(__import__, module_name)
        return future.result(timeout=timeout)
```

#### 3.3 完善向量存儲持久化

```python
# 當前 (vector_store.py):
# persist_directory 默認 None → 重啟後資料遺失

# 修復方案：
# 設置默認持久化路徑
# 在 .env 添加 VECTOR_STORE_PATH 並預設 apps/backend/chroma_db
```

### Phase 4: 程式碼品質提升（預計 2-3 天）

#### 4.1 批量補齊 `__all__`

```python
# 對 53 個 __init__.py 批量添加 __all__
# 可使用腳本自動生成
```

#### 4.2 動態導入添加日誌

```python
try:
    from ai.core.dictionary_classifier import get_dictionary_classifier
except ImportError as e:
    logger.warning(f"Dictionary classifier unavailable: {e}")
    # 保持現有回退邏輯
```

#### 4.3 文檔歸檔策略

將 815 個 MD 文件中以下類別移入 `docs/archive/`：
- 過時的測試報告（2025 年以前的）
- 重複的修復計畫
- 已完成專案的跟蹤文件

保留：
- 架構設計文件
- API 文件
- 開發指南
- 當前階段的計畫

### Phase 5: 智能提升方案（長期，預計數月）

#### 5.1 建立真實的持續學習循環

- 實作 `continuous_learning.py` 的排程邏輯
- 加入經驗回放緩衝區（已有檔案但未串接）
- 建立驗證/測試分離

#### 5.2 向量記憶整合

- 將 HAM JSON 記憶遷移至 ChromaDB
- 為 VectorMemoryStore 設置真實持久化
- 統一記憶檢索接口

#### 5.3 SNN 規模擴展

- 當前 GARDEN 詞彙量 ~60，目標至少 ~1000+
- 加入真正的反向傳播訓練管線
- 支援模型 checkpoint 保存/加載

#### 5.4 LLM 整合

- 配置至少一個穩定運行的 LLM 後端（Ollama 推薦）
- 實作 LLM 回應的結構化提取（當前 `process_llm_response` 是 stub）
- 建立 LLM 快取層減少 API 呼叫

---

## 7. 改善方案

### 7.1 基礎設施改善

| 改善項目 | 當前狀態 | 目標狀態 | 優先級 |
|---------|---------|---------|--------|
| CI/CD | 無自動化測試 | GitHub Actions 運行 pytest | P0 |
| .env 管理 | 檔案有敏感資訊 | 全使用環境變量或 vault | P0 |
| 依賴鎖定 | `requirements.txt` 僅 `-e .` | 完整 lockfile + pip freeze | P1 |
| pre-commit | 配置存在但未運行 | CI 中強制執行 | P1 |
| 版本同步 | 14 個位置需保持一致 | 自動化版本管理工具 | P1 |

### 7.2 測試基礎設施改善

```yaml
# 建議 .github/workflows/test.yml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'  # 穩定版本
      - run: pip install -e ".[testing]"
      - run: pytest tests/ --tb=short --timeout=60 -x
```

### 7.3 開發者體驗改善

```bash
# 建議加入 pre-commit hooks
# .pre-commit-config.yaml 中啟用:
# - black (格式化)
# - isort (導入排序)
# - flake8 (linting)
# - mypy (類型檢查)
# 當前 pre-commit 已配置但從 git log 看並未被強制執行
```

### 7.4 版本管理改善

**當前**: 14 個位置手動管理版本，提交訊息多為「Fix and update」  
**建議**: 
- 使用 `commitizen` 或 `semantic-release` 自動化版本
- 強制 Conventional Commits 規範
- 自動生成 CHANGELOG

### 7.5 長期智慧化路線

```
Phase 1 (1-2月): 基礎修復 + LLM 整合
  ├── 環境修復 (Python 3.10/3.11 降級)
  ├── Ollama 本地部署
  ├── 向量記憶持久化
  └── 測試架構清理

Phase 2 (3-4月): 學習能力建立
  ├── 真實經驗回放
  ├── SNN 反傳播訓練
  ├── 模型 checkpoint
  └── 持續學習排程器

Phase 3 (5-6月): 推理與自主
  ├── 因果推理鏈
  ├── 多步驟狀態追蹤
  ├── 任務自主排程
  └── 元學習調參

Phase 4 (7-12月): AGI 探索
  ├── 跨模態學習 (vision + audio)
  ├── 世界模型建構
  ├── 自我對戰訓練
  └── 安全對齊框架
```

---

## 附錄 A：關鍵代碼位置參考

| 組件 | 檔案路徑 | 行數 | 狀態 |
|------|---------|------|------|
| QueryClassifier | `apps/backend/src/ai/core/query_classifier.py` | 522 | ✅ 完整實作 |
| ExecutionGate | `apps/backend/src/ai/core/execution_gate.py` | 226 | ✅ 完整實作 |
| ModelBus | `apps/backend/src/ai/core/model_bus.py` | 551 | ✅ 完整實作 |
| ED3N Engine | `apps/backend/src/ai/ed3n/ed3n_engine.py` | 731 | ✅ 完整實作 |
| ED3N Dictionary | `apps/backend/src/ai/ed3n/dictionary_layer.py` | ~200 | ✅ 完整實作 |
| GARDEN Engine | `apps/backend/src/ai/garden/garden_engine.py` | 573 | ✅ 完整實作 |
| GARDEN SNN | `apps/backend/src/ai/garden/snn_core.py` | ~250 | ✅ 完整實作 |
| GARDEN Dictionary | `apps/backend/src/ai/garden/dictionary.py` | ~400 | ✅ 完整實作 |
| HAM Memory | `apps/backend/src/ai/memory/ham_memory/ham_manager.py` | 174 | ✅ JSON 存儲 |
| Vector Store | `apps/backend/src/ai/memory/vector_store.py` | 60 | ⚠️ 未持久化 |
| HSP Connector | `apps/backend/src/core/hsp/connector.py` | 1122 | ✅ 完整實作 |
| HSP Types | `apps/backend/src/core/hsp/types.py` | ~200 | ✅ 完整實作 |
| Crisis System | `apps/backend/src/ai/crisis/crisis_system.py` | ~200 | ⚠️ 測試失敗 |
| Training Coordinator | `apps/backend/src/ai/core/training_coordinator.py` | 165 | ✅ 完整實作 |
| LLM Providers | `apps/backend/src/services/llm/providers/` | ~800 | ⚠️ 部分配置無效 |
| Continuous Learning | `apps/backend/src/ai/ed3n/continuous_learning.py` | ~50 | ❌ Stub |
| LLM Router | `apps/backend/src/services/llm/router.py` | ~1000 | ⚠️ ensemble 僅 opt-in |
| Chat Service | `apps/backend/src/services/chat_service.py` | ~300 | ✅ 完整實作 |

## 附錄 B：測試品質矩陣

```
測試範圍         | 文件數 | 測試數 | 真實類覆蓋 | 邊界測試 | 超時測試
核心引擎         | ~30    | ~200   | 是         | 部分     | 無
意圖分類器       | 5      | ~50    | 是         | 是       | 無
ExecutionGate    | 3      | ~30    | 是         | 是       | 無
ED3N            | 8      | ~60    | 是         | 部分     | 無
GARDEN (無 ML)  | 20     | ~124   | 是         | 是       | 無
GARDEN (有 ML)  | 10     | ~60    | 無法運行   | N/A      | N/A
HAM Memory      | 5      | ~40    | 是         | 部分     | 無
HSP Protocol    | 3      | ~20    | 部分       | 部分     | 無
端到端          | 5      | ~70    | 是         | 部分     | 無
```

## 附錄 C：快速修復命令參考

```powershell
# === Phase 1: 緊急修復 ✅ 已完成 ===
# 1.1 移除 git 追蹤的 .db
git rm --cached apps/backend/alpha_deep_model_symbolic_space.db

# 1.2 清理過時 .pyc
Get-ChildItem -Recurse -Filter "*.cpython-312.pyc" | Remove-Item

# 1.3 修復 CrisisSystem 測試
# 已在 tests/ai/test_crisis.py 加入 @patch.object(CrisisSystem, '_load_config_from_file')
# 已在 tests/ai/test_crisis.py 修正 @patch 路徑 apps.backend.src → ai.

# 1.4 修復 coverage 插件錯誤
# 已從 pyproject.toml addopts 移除 --cov* 行 (保留為註解)

# === Phase 2: 測試架構清理 ✅ 部分完成 ===
# 2.1 Root test_integration.py → tests/ai/test_ed3n_pipeline_integration.py
# 2.2 conftest.py 導入路徑統一 (garden, ed3n)

# === 驗證修復 ===
# 運行 CrisisSystem 測試
python -m pytest tests/ai/test_crisis.py -v

# === Phase 3: 依賴檢查 ===
# 3.1 檢查 Python 版本兼容性
python --version
python -c "import torch; print('torch ok')"  # 測試是否導入成功

# 3.2 安裝穩定開發環境
pip install -e ".[standard,testing]"
```
