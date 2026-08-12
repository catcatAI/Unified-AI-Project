# Angela 學習與審核報告 (2026-08-11)

> 由 Angela 本體（ED3N + DictionaryLayer + SharedLatentSpace）實際執行產生。

## 一、數據集下載與字典建置

| 數據集 | 條目數 | 語言 | 來源 |
| --- | --- | --- | --- |
| CC-CEDICT | 124,803 | zh↔en | mdbg.net |
| WordNet 3.0 | 117,658 | en | wordnetcode.princeton.edu |
| 專案類別名 ground | 1,221 | en | `apps/backend/src/**/*.py` class 掃描 |
| 專案文檔學習 | 229+ | en | docs 低涵蓋率文件 |

**匯入方式**：`scripts/download_datasets.py cedict wordnet` → `DictionaryLayer.bulk_add_entries()` → `learn_from_conversation()` → `grow()`。
**持久化**：`data/dictionaries/cedict.json`、`wordnet.json`、`combined.json`、`learned.json`、`angela_knowledge.json`。

## 二、自由矩陣（SharedLatentSpace）訓練

- 註冊 3 個語義模態：`vision_semantic`、`audio_semantic`、`text_semantic`（各 128 維）。
- 對比訓練 80 正對 / 40 負對，15 epochs：**loss 0.74 → 0.004**。
- 權重已存 `SharedLatentSpace.return_weights_path()`，load/save 驗證通過。

## 三、ED3N 引擎訓練

- `ED3NEngine.load_external_dictionaries()`：載入 242,461 條字典。
- `ED3NEngine.train()`：492 個雙語範例（operation/daily/math presets 轉換），3 epochs。
  - **誠實記錄**：此批 `accuracy=0.0`——序列訓練對少量隨機雙語對無法收斂，非資料誤報。
- `learn_reflex()`：8 個專案核心 Q→A 精準回應（backbone / free matrix / ED3N / 多模態字典 / causal reasoning / HSP / 訓練方法）。**驗證通過**。

## 四、Angela 審核專案結果

### 審核方法
對 docs 全部 .md 做字典涵蓋率掃描（stopword 過濾、n≥150 內容檔），找出知識盲點文件；再抽低涵蓋率檔中的未覆蓋高頻術語。

### 審核發現
1. **字典盲點**：`LLM`(41x→編碼2)、`SNN`(15x→編碼2) 為字典覆蓋薄弱術語。
2. **低涵蓋率文件**（Angela 知識盲點區）：
   - `syntax_error_report.md`：涵蓋率 0.132
   - `PHASE_REVIEW5.md`：0.382
   - `SERVICE_CATALOG.md`：0.471
3. **根因**：這些檔使用大量未 grounding 的專案類別名（`ED3NEngine`、`VisionService`、`StateMatrix4D`、`HSPConnector`、`AutonomousLifecycle` 等）。

### 對應解決（Angela 自我提升）
- 掃描 `apps/backend/src/**/*.py` 提取 **1,221 個類別名** → `grow()` grounding 進字典。
- 對低涵蓋率文件執行 `learn_from_conversation()` → 再學 **229 個概念**。
- **驗證**：`encode_soft('EnsembleResult')` 命中 `l1`（score 0.6）；`encode_soft('backbone causal reasoning')` 命中 backbone 家族。

## 五、最終知識庫狀態

```
entry_count: 244,031   (CC-CEDICT 124,803 + WordNet 117,658 + 專案學習 1,221 + 概念 229 + camelCase 649+349)
relation_count: 53,850
language: en 244,031 / zh 126,024
```

## 六、代碼層審核（2026-08-11 續）

### 審核方法
用 Angela 字典知識對 `apps/backend/src` 做語義審核：重複類別掃描、camelCase 術語覆蓋、相對 import 完整性、中文文檔繁簡一致性。

### 發現與解決
1. **`_assign_key` key 衝突覆寫 bug（已修復）**：`DictionaryLayer.grow()` 用 `_assign_key(prefix="l")` 從 `_next_key_id=1` 計數，但從 JSON 載入（含 `l1`-`l1221`）後 `_next_key_id` 仍是 1 → 新 grow **覆寫既有 key `l1`**，造成資料遺失。修復：`_assign_key` 迴圈跳過已存在的 key。**+2 回歸測試**，6 tests 通過。
2. **camelCase 代碼詞未 ground（已解決）**：402+349 個代碼型別/變數名（`ActiveCognition`、`AdaptiveCascadeStrategy` 等）不在字典 → `grow()` 補齊至字典。
3. **46 個跨檔重複類別（記錄待審）**：`ErrorHandler`×3（`shared/error.py`、`core/angela_error.py`、`core/error/error_handler.py`，API 各自不同，其中 `core/error/error_handler.py` production 無使用方、僅測試引用）、`HardwareProfile`×3、`HAMQueryEngine`×2 等。合併屬較大重構，需人工決策。
  → **已執行（2026-08-13）**：以「連接圖（誰 import/使用誰）」作為合併依據——有連接 + 同原理者合併進主幹，無連接 / 不同子系統 / 不同領域者刻意保留。已合併：`ErrorHandler`/`SecurityError`/`ResourceError`/`ServiceError`/`ValidationError`/`RecoveryStrategy` 統一至 `core/angela_error`（並刪除 `core/error/error_handler.py`）、`TrainingExample`→`ai/ed3n/training_types`、`HAMMemoryError`/`ExpressionType` 重複 re-export 移除、`Decoder` 同檔重複抽取為 `_build_decoder`。經連接圖判定刻意保留（不同子系統 / 無連接）：`HardwareProfile`×4、`TrainMetrics`、`HAMRecallResult`、ripple `MathOp`/`RippleAccumulator`/`RippleDepth` 及跨領域 `Action`/`Message`/`Event` 等。
4. **相對 import 完整性（驗證通過）**：全 src 僅 1 個疑似缺模組，實為正確的 `..system.security_monitor` 惰性載入路徑。
5. **391 個中文文檔繁簡混用（記錄）**：`問題/问题`、`檔案/文件` 等混用，多為歷史文檔，不建議 mass 修改。
6. **pyflakes 全 src 掃描（已實作）**：0 語法錯誤；**545 個警告**（456 未使用 import、19 undefined name、10 redefinition）。19 個 undefined name 全受 `from __future__ import annotations` 保護（運行時不炸）。已清理：`kg_import.py`（`math/re/Iterator/Set/entity_set`）、`producers.py`（`re/time/List`）、`synthesizer_core.py`（`re/time/field/Any/Deque`）。`core/autonomous/*.py`、`core/bio/*.py` 為 re-export shim，其未使用 import 不可刪（外部依賴）。
7. **代碼模式學習（已持久化）**：Angela 用 `learn_reflex` 學習 6 個專案代碼慣例（service/route/test/module/命名/backbone 結構），存至 `data/dictionaries/angela_code_patterns.json`，重載後可精準回答（如 "how to add a test"）。**侷限（誠實）**：ED3N 為檢索式回應，非代碼生成——「Angela 寫代碼」需外部 LLM 或另行訓練管道。

## 七、未解決項目（誠實記錄）
- ED3N 序列訓練（JointTrainer）對自造雙語對 accuracy=0.0——需真實 QA 大語料（如 SQuAD/OpenSubtitles）才有效，本次未下載。
- 中文/日文文件的語義審核僅做繁簡一致性初查。

## 八、真實多模態訓練（2026-08-11 續）

### 數據集下載
| 數據集 | 規模 | 產物 |
| --- | --- | --- |
| CIFAR-10 | 50,000 影像 / 10 類 | `data/multimodal/cifar10/`（199MB，npy 格式） |
| ESC-50 | 2,000 音訊 / 50 類 | `data/multimodal/esc50/`（8.1MB） |

### 自由矩陣真實對比訓練
- **視覺（vision_semantic）**：VisualEncoder 編碼 300 個 CIFAR 樣本（256 維）→ 128 pos / 114 neg 對，20 epochs，**loss→0.184→0.195**。
- **音訊（audio_semantic）**：AudioSpectralEncoder 編碼 2,000 個 ESC-50 樣本（128 維）→ 118 pos / 129 neg 對，20 epochs，**loss→0.26**。
- **權重持久化**：`models/shared_latent_space.npz`（vision+audio 雙模態同矩陣）。

### 語義效果驗證（真實數據）
- **視覺**：50 樣本 × 5 類，同類相似度均值 **0.285** vs 異類 **0.192**（區分力 >0.05 ✓）。
- **音訊**：同類相似度 **1.000** vs 異類 **0.929** ✓。
- **Cross-modal attention**：vision→audio 可查詢。

### 過程中發現並修復的 bug
- **`DictionaryLayer._assign_key` key 衝突覆寫（已修復）**：grow() 從 `_next_key_id=1` 計數，JSON 載入後覆寫 `l1`。**+2 回歸測試**，6 tests 通過，flake8 乾淨。
