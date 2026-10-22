# 純本地基模清單：包含什麼、不包含什麼

> 這份清單回答一個問題：**脫離外部 LLM（雲端金鑰、本地 ollama／llama.cpp）之後，
> 專案自己還剩下什麼？** 每一項都標了程式位置與「在量測裡扮演什麼角色」。
>
> 驗證方式：`python scripts/probe_native_dialogue.py` 會在**不註冊任何非專案
> 後端**的情況下跑（啟動時斷言，發現雲端或本地 LLM 後端就直接報錯），量出來的
> 數字就是這份清單的實測結果。

> 這份清單只描述**元件與角色**。它「值幾分」由統一定義回答：
> `INTELLIGENCE_ASSESSMENT.md §0`（`ai/meta/intelligence.py`）＋
> `scripts/report_intelligence.py`（唯一總分，快照在 `intelligence_report.json`）。
> 2026-10-22 實測：**4.41/10（平均落在 L2 帶），但達成的階梯是 L0**——L1 的
> 關鍵度量「改述泛化」仍是 0/10。

## 一、包含（專案自己的模型與資產）

### 1. 模型主體（可獨立回答問題的三個引擎）

| 元件 | 位置 | 它是什麼 | 純本地的角色 |
| --- | --- | --- | --- |
| **UnifiedEngine** | `ai/unified_engine/unified_engine.py` | 確定性層（reflex／數學／邏輯）＋**統計核心**（FixedSizeCore，n-gram 的 log-odds 與答案投票）＋**SLS 語意層**（SemanticQA，梯度訓練的檢索模型） | 純本地的**主回答模型**（`unified` 後端） |
| **ED3N** | `ai/ed3n/ed3n_engine.py` | 反射／關聯式 SNN ＋字典 ＋連續學習管線 | 教學後的關聯記憶（`ANGELA_LEGACY_ED3N=1` 才啟用） |
| **GARDEN** | `ai/garden/garden_engine.py` | 結構化 SNN ＋模板學習（輸入骨架 → 輸出骨架） | 學會的**結構**（例：學過「X is taller than Y」→「Y is shorter than X」） |
| **多語編碼器**（ONNX） | `ai/garden/dictionary.py` 的 `_OnnxEncoder`（sentence-transformers paraphrase-multilingual-MiniLM） | 句向量 | **接觸**（把未見改述落到概念原型）與**語意檢索**（回憶層的候選排序） |

### 2. 確定性推理層（不需訓練，精確）

| 元件 | 位置 | 能力 |
| --- | --- | --- |
| `symbolic_reasoner` | `ai/symbolic_reasoner.py` | 比較鏈、傳遞閉包、yes/no 蘊涵、日期與質量等（**老師**） |
| `neural_bridge` | `ai/reasoning/neural_bridge.py` | **中間層**：用編碼器把未見改述落到老師的概念原型（維度 × 方向），再合成關係圖 |
| `claims` | `ai/reasoning/claims.py` ＋ `configs/standard/reasoning/claims.yaml` | **斷言推理**：「X 這句話對嗎？」→ 事實＋條件＋例外（**最正確**那一級） |
| `deterministic_router` | `ai/arithmetic/deterministic_router.py` | 數學（MathVerifier）、邏輯、知識、推理、橋接的**單一路由入口** |
| `knowledge_base` | `ai/knowledge_base.py` | 策展事實（天空是藍的、每週 7 天…） |

### 3. 記憶與狀態

| 元件 | 位置 | 能力 |
| --- | --- | --- |
| HAM 記憶 | `ai/memory/ham_memory/ham_manager.py` | 事實／對話／模板三個桶；**對話回憶**（教過的姓名、地址、喜好） |
| 向量庫 | `ai/memory/vector_store.py` | 語意檢索（chromadb 或純 numpy） |
| 狀態矩陣／情緒 | `ai/core/state_matrix.py`、`ai/alignment/` | 8 維狀態、情緒偵測——驅動模板選擇 |
| 模板庫 | `ai/memory/template_library.py` ＋ `templates_data.json` | 49 條模板（問候、情緒、知識…） |
| 反射預設 | `ai/data_eng/presets.py` | 60 條 reflex（你好／今天／講個笑話…） |
| 神經詞彙 | `ai/response/composer.py` 的 `NeuroVocabulary`（`configs/standard/behavior/angela_core.yaml`） | 情緒狀態 → 片語（**現在只黏 3 句**） |

### 4. 工具（不是模型，但不需要 LLM）

檔案／程式碼執行、任務管理、視覺（CLIP）、圖像生成、Drive 掛載、學習（教事實）——
全部是 deterministic handler（`services/handlers/`）。

## 二、不包含（脫離外部基模就沒了）

| 缺什麼 | 位置 | 少了會怎樣 |
| --- | --- | --- |
| **自由生成的回覆** | `services/llm/providers/{openai,anthropic,google,ollama,llamacpp}.py` | 純本地的回覆只能**組裝**（模板＋事實＋檢索），不能**寫**——這就是 QA 機器率 43% 的根源 |
| **開域知識** | 外部檢索 | 斷言庫沒有的斷言只能誠實棄權（標準集那 324 題 0% 的原因） |
| **任意命題推理** | LLM | 只能跑預先定義的推理形狀（比較鏈、斷言庫、數學） |
| **網路搜尋**（若走 handler 需要外部服務） | `services/handlers/web_search_handler.py` | 離線時無外來資訊 |
| **語音合成** | `core/art/real_edge_tts.py`（edge-tts＝微軟的雲端服務） | **連「說話」都不是本地的**——若要純本地，TTS 也得換掉 |
| **情緒的細緻理解** | LLM | 只���模板級的共情（辛苦啦！快休息一下） |

## 三、所以「離目標還多遠」

以 `scripts/probe_native_dialogue.py` 的**人話標準**（六條規則）為準，標準量 1102 回合：

| 類別 | 通過率 | 差在哪 |
| --- | --- | --- |
| 問答（數學／知識／比較） | 85% | 幾乎全對 |
| 斷言題（斷言庫覆蓋） | 88% | 機制可用 |
| 對話回合 | 83% | 罐頭模板（QA 機器） |
| 多重事實 | 54% | 組合與記錯（這輪已修一部分） |
| **斷言庫外的邊界題** | **0%** | **知識缺口**：斷言庫沒收錄的主題 |
| **總通過率** | **57.8%** | — |

**距離的結構**：不是「模型不夠大」，而是兩件事——
① **知識覆蓋**（斷言庫收多少主題）② **自由生成**（能不能不靠模板寫出像樣的句子）。
前者可以在純本地下持續推進（每條斷言＝一個主題）；後者**在本質上需要一個生成模型**
——這就是「除了 LLM 以外都有吧？」的答案：**幾乎都有，唯獨「把話說得像人」的那一層沒有**。
