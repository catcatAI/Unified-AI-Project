<!--
  =============================================================================
  FILE_HASH: GENERATED
  FILE_PATH: docs/GARDEN_TRAINING_DATA_AUDIT.md
  FILE_TYPE: documentation
  PURPOSE: GARDEN 訓練資料/字典/推理深審計 — 需檢查實際狀態與內容才能發現的問題
  VERSION: 7.5.0-dev
  STATUS: active
  LANGUAGE: zh-TW
    LAST_MODIFIED: 2026-08-16
  AUDIENCE: developers, agents
  =============================================================================
-->

# GARDEN 訓練資料 / 字典 / 推理 深審計（2026-08-16）

> 本檔案記錄針對 **GARDEN 訓練→字典→推理** 鏈路的深審計發現。不同於一般代碼審計（跑測試就能抓），
> 這些問題**必須實際檢查訓練產物、字典內容、運行時記憶體**才能暴露。
> 審計方法：探查 checkpoint 實際內容 + 用 `TRAIN_NO_CORPUS=1` 重現資料生成與推理路徑。

## 摘要

審計發現 **1 個 CRITICAL 連鎖問題**（prefix 誤合併 → 字典污染 → 推理 OOM）與 4 個 HIGH/MEDIUM 問題。
**全部 5 項已修復**（修復位置見各節），但 **CRITICAL 的徹底解決需重訓**（見 §結論）。

## 修復狀態（2026-08-16）

| # | 嚴重度 | 問題 | 狀態 |
|---|--------|------|------|
| A | CRITICAL | `prefix_overlap` min_len 分母導致短詞吞併所有同前綴長詞 → 字典污染 → 推理 OOM | ✅ 算法修復；需重訓才能清潔現有 checkpoint |
| B | HIGH | `concept_N` 空洞填充樣本毒化 SNN（「consistent knowledge representations united」固定輸出） | ✅ 改為真實主題變體填充 |
| C | HIGH | Ollama 失敗日誌 + DummyModel 佔位符被當訓練資料（l244 是 JSON 日誌字串） | ✅ 垃圾標記 + 純數字過濾 |
| D | MEDIUM | `fallback_chain` dict 被當 list 迭代，`garden-1g` 永不可達 | ✅ 扁平化 dict values |
| E | MEDIUM | `drain_priority_queue` 無消費者，訓練佇列只進不出 | ✅ enqueue 後內聯 drain |

---

## A. CRITICAL — `prefix_overlap` 短詞吞併長詞 → 字典污染 → 推理 OOM

### 根因
`apps/backend/src/ai/data_eng/dedup.py:42` 的 `prefix_overlap` 用 `prefix_len / min_len` 計算相似度。
當較短詞是較長詞的**完整前綴**（如 `con` ⊂ `consultant`），`prefix_len == min_len` → 比值 **1.0**，
即使兩詞語義無關。`dictionary.py` 的 `_find_similar_key_no_tfidf` 以 `prefix_dedup` threshold=0.8 合併，
於是 `con`/`app`/`for` 這類短詞把**所有**共享該前綴的長詞吞併成單一條目。

### 實際影響（檢查 checkpoint 實證）
`data/checkpoints/garden_checkpoint/dictionary.json`：
- **9,799 條目、36,654 表面形式、26,945 獨特詞**。
- **l24 有 840 個 surface forms**；l244 有 561（含 Ollama JSON 日誌字串）；l333=118、l1727=100。
- **136 個條目 ≥20 forms**（污染前應 <5）。
- 超大 forms 條目使 `_rebuild_index()` 的 TF-IDF 詞彙膨脹到 **26,945 詞**。

### 推理 OOM（運行實證）
```
載入 checkpoint 成功（V=9799, RSS=1923MB）
eng.dictionary._rebuild_index() → 程序直接崩潰（OOM）
```
在 7.5GB 機器上，GARDEN **任何推理請求**（首次 encode 觸發 `_rebuild_index`）都會 OOM。
**即使 config 把 `garden-1g` 設為 `enabled: true`，模型也無法回應。**

### 修復（`dedup.py`）
短詞完全包含於長詞（`prefix_len >= min_len`）時改用 `prefix_len / max_len`：
```
'con' vs 'consultant': 1.0 → 0.30   (不再誤合併)
'app' vs 'apple':      1.0 → 0.60
'for' vs 'forum':      1.0 → 0.60
'happy' vs 'happiness':0.8（維持，正常詞形變化不受影響）
```
`tests/ai/data_eng/test_data_eng.py` 36 passed 保持不變。

---

## B. HIGH — `concept_N` 空洞填充樣本毒化 SNN

### 根因
`scripts/train_pipeline.py` `generate_knowledge_data()`：當模板產量不足 target（1000）時，
用 `concept_{i} is a conceptual unit in knowledge representation` 填充（517 樣本）。
這些語義空洞樣本在 SNN 產生最高頻 Hebbian 關聯，成為**任何開放式問答的固定輸出**
「consistent knowledge representations united」的來源。

### 修復
改用真實主題池（`topics_en + topics_zh`）輪詢 4 種問句變體：
```
'concept_77 is a conceptual unit in knowledge representation'   ❌（空洞）
'tell me about 面向对象编程' → '面向对象编程 is a domain concept...'  ✅（真實主題）
```
驗證：`generate_knowledge_data()` 產 **733 樣本、0 個 concept_N**，250 個填充全為真實主題。

---

## C. HIGH — Ollama 失敗日誌 / DummyModel 佔位符被當訓練資料

### 根因
`load_secondary_raw()` 載入 `ollama_cat_formulas_log.json` + `DummyModel.json` 當訓練樣本。
前者是 **Ollama 失敗回應**（`喵嗚... Ollama 暫時無法回應` + 原始 JSON 日誌），
後者是佔位符（`1`→`1`）。訓練後 l244 的 561 個 surface forms 就是這些 JSON 字串。

### 修復（`train_pipeline.py`）
- 垃圾標記過濾：`喵嗚`、`Ollama 暫時無法回應`、`dummy`、`DummyModel`、`"created_at"`、`"model":"`。
- 純數字/佔位符過濾（全為 `0123456789.+- ` 的字串）。
- 驗證：過濾後 secondary samples = **0**（原本含垃圾）。

---

## D. MEDIUM — `fallback_chain` dict 被當 list 迭代

### 根因
`router.py:318` 讀取 `fallback_chain`（config 中是 dict：`ed3n-v1: [garden-1g, ollama-llama3], ...`），
但 `_try_fallback_chain()`（`router.py:1661`）`for backend_name in chain` 直接迭代 dict **keys**
→ 重試剛失敗的後端，`garden-1g`（value）**永不可達**。

### 修復（`router.py:1661`）
`_try_fallback_chain` 開頭偵測 dict，扁平化所有 values 為有序去重 list。

---

## E. MEDIUM — `drain_priority_queue` 無消費者

### 根因
`training_coordinator.enqueue()` 被 `mainline_dispatcher.py:201` 呼叫（TRAIN action），
但 `drain_priority_queue()` 全庫**無呼叫者** → 佇列只進不出（無界增長 + 訓練請求被吞）。

### 修復（`mainline_dispatcher.py:_run_side_actions`）
enqueue 後內聯 `drain_priority_queue()` 並把樣本交給 `learn_fn` 路徑。

---

## 其他審計結論（非問題）

- **checkpoint 一致性**：`training_state.json`（batch_done=11180 / completed=[5] / ed3n_epochs=2）
  與 `garden_checkpoint/`（snn.pt 543MB / dictionary.json / engine_meta learn_count=11180）自洽。
- **ED3N 產物**：`ed3n_full.json` 與 `ed3n_sample.json` 內容一致（僅 `exported_at` 相差 3 分鐘）。
- **SNN 權重統計**：`W` 11652²，**0.5% 非零**（稀疏），max 權重 0.82，非零均值 0.031。
- **reflex 持久化**：`engine_meta.json` 無 `reflex_patterns` 欄位（checkpoint 存於 168b5894 修復前），
  但載入時 `_load_config_reflex_into()` 從 config 回填，行為正確。

## 結論與後續

- 5 項修復均已通過對應測試（data_eng 36 + garden 313 + mainline 9 + coordinator 14 + integration 10）。
- **CRITICAL A 的徹底解決需要重訓**：現有 checkpoint 的字典已被 840-form 污染（l24 等 136 條目），
  修復後的 `prefix_overlap` 不會再產生新污染，但既有條目不會自我清潔。
- **重訓後預期收益**：字典條目數下降、TF-IDF 詞彙收斂、`_rebuild_index` 不再 OOM、GARDEN 推理可用。
- **GARDEN `enabled: false`**（`llm.default.yaml:91`）在重訓完成前維持關閉是正確的——啟用後會 OOM 或輸出噪音。
