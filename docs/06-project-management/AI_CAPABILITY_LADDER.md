<!--
  =============================================================================
  FILE_HASH: LADDER-20260901
  FILE_PATH: docs/06-project-management/AI_CAPABILITY_LADDER.md
  FILE_TYPE: planning
  PURPOSE: AI 能力階梯 0~10 分級路線圖 — 按分數段拆解任務，明確「現有/下一階/再下一階/LLM 層」
  VERSION: 7.5.0-dev
  STATUS: active
  LANGUAGE: zh-TW
  LAST_MODIFIED: 2026-09-01
  AUDIENCE: maintainers, agents
  =============================================================================
-->

# AI 能力階梯 0~10 — 分級路線圖

> **對應**：`INTELLIGENCE_ASSESSMENT.md §1.3` 分數對照表 + `AUDIT_REPORT_2026-09-01.md §8.2` 三類分數分離
> **原則**：每階有**可量測門檻**（benchmark / 回歸測試），不靠主觀描述。跨階不跳級。
> **當前快照**（2026-09-01 更新 2026-09-02）：
> - 確定性引擎 9.5~10（MathVerifier/KB/symbolic，真實能力，已達標）
> - 神經關聯 1.0（`validate_association.py` 4/4）→ **L2-3 FixedSizeCore 5K 60% 達標（硬件規格自適應 Arc B570 15.5GB）**
> - 開放域泛化 1.0→**1.0→2.5**（SNN-ONLY 改述 88%超標 via `probe_snn_unseen` 硬件自適應，已從 1.0 提升）
> - 有 LLM API 6.0（`benchmark_ed3n_garden.py` 20/20）→ **L3-1 65% via 知識擴充 20 條，L3-2 100% 真實工具**
> - **硬件**：Arc B570 10GB + 15.5GB `high_performance_desktop` 規格驅動 chassis-agnostic（`garden vocab 35000`）

---

## 總覽

```
0 ─── 2 ─── 4 ─── 6 ───────────────── 10
│     │     │     │                    │
│現有 │本地 │本地 │ LLM 層              │ AGI
│確定性│可理解│可用 │ 外部大模型編排       │
│+反射 │     │     │                    │
```

| 階梯 | 分數 | 定位 | 一句話 | 關鍵度量 | 是否依賴外部 LLM |
|------|------|------|--------|----------|------------------|
| **L0** | **0~2（現有）** | 確定性 + 反射 + 字典 | 能算、能查、能回罐頭，但不會「想」 | `benchmark 20/20` 全由確定性引擎；SNN 關聯 1.0 | ❌ 不依賴 |
| **L1** | **2~4** | 本地可理解 | 能把未見過的問法對上已知概念，改述召回穩定 | SNN-ONLY 改述/CJK 召回 ≥40%，關聯鏈 ≥10 跳 | ❌ 不依賴 |
| **L2** | **4~6** | 本地可用 | 多輪對話不跑題，記憶/推理/多模態能串起來當助手用 | 多輪一致性 + 記憶命中 + 推理泛化 ≥60% | ❌ 不依賴（可選本地小模型） |
| **L3** | **6~10** | LLM 編排 | 自然對話、工具調用、多智能體協作，達到 GPT-3~4 級 | MMLU/HumanEval 子集 + 工具成功率 | ✅ 依賴（Ollama/OpenAI 等 7 後端） |

> **為何這樣切**：`INTELLIGENCE_ASSESSMENT.md:384-438` 已證明「確定性引擎會做題 ≠ 神經會做題」。0~2 是**已兌現**的確定性能力；2~6 必須讓**神經/統計核心自己學會**，不能再靠 `if math: return ast.eval` 充數；6~ 才是把外部 LLM 當「大腦」編排起來。

---

## L0 — 0~2（現有，已達標，守成）

### 已有什麼（不需再做，只需守）

| 能力 | 實現 | 驗證 |
|------|------|------|
| 數學 5/5 | `MathVerifier` (`ast` 安全求值，中英數字/運算符) | `benchmark_ed3n_garden.py: math 5/5` |
| 知識 5/5 | `ai/knowledge_base.route_knowledge`（sky→blue/反義/週天數/Red Planet） | `knowledge 5/5` |
| 符號推理 5/5 | `ai/symbolic_reasoner.route_reasoning`（傳遞/三段論/日曆/數量陷阱） | `reasoning 5/5` |
| 關係鏈 5/5 | `ai/reasoning/relational_chain.py` 傳遞閉包 | `chain 5/5` |
| 反射/罐頭 | `unified_engine/presets` `REFLEX_PRESETS` | 問候/閒聊穩定 |
| 關聯 1.0 | `scripts/validate_association.py` directional/transitive/ranking/perturbation 4/4 | ED3N & GARDEN 1.0 |
| 改述基線 1.0 | SNN-ONLY 改述/CJK 召回 ~11%（ONNX 多語言 + 閾值 0.75） | `INTELLIGENCE_ASSESSMENT §1.1` |

### 守成任務（防回退）

| ID | 任務 | 驗收 | 工作量 |
|----|------|------|--------|
| **L0-1** | `benchmark_ed3n_garden.py 20/20` 納入 CI | CI 斷言 20/20，任一 Stage 回退即紅 | S |
| **L0-2** | `validate_association.py 1.0` 納入 CI | 4 指標全綠 | S |
| **L0-3** | 確定性引擎單元測試補齊（`knowledge_base` 星期/月份接續等邊界） | 新增 10+ 邊界測試 | S |

---

## L1 — 2~4（本地可理解）— 下一階

> **目標**：**不靠 LLM**，讓統計核心/關聯網路對「沒見過的說法」也能對上已知概念。從「背答案」到「懂改述」。

### 為何是 2~4

當前 SNN-ONLY 改述召回僅 ~11%（`INTELLIGENCE_ASSESSMENT §1.1`），`validate_three_column.py` 顯示 HYBRID 43.1% / SNN-ONLY 7.8% — 知識/數學全靠確定性引擎，神經幾乎不貢獻。2~4 的核心是**讓神經開始貢獻**。

### 任務

| ID | 任務 | 背景 | 具體動作 | 驗收（可量測） | 工作量 | 依賴 |
|----|------|------|----------|---------------|--------|------|
| **L1-1** | FixSizeCore 訓練數據 12K→100K | `association_train.json` 僅 12K，14 維度偏少 | `generate_training_data.py:generate_association_data()` 擴至 100K，增加比較維度 14→30（含中文比較詞、口語改述、否定/反轉） | `association_train.json` 100K，訓練後 `validate_association` 仍 1.0 且 SNN-ONLY 改述召回不下降 | M | — |
| **L1-2** | 關聯鏈深度 3→50 節點 | 現僅 3 節點玩具圖，無法驗證長鏈傳遞 | `validate_association.py --deep` 新增 `deep_chain`（50 跳）、`branching_graph`（分叉/合併）、`noisy_chain`（含 10% 噪聲邊）三檔；**研究發現** 50 跳在 `hops=3, decay=0.5, threshold=0.7` 下恆 0（3 跳後 0.9×0.5³=0.112 <0.7），需 `hops=6+decay=0.8` 或 `threshold 0.5` 在 `high_performance` 檔位才可能，**精進** 先以 10 跳≥90% 為 lean 門檻，50 跳為 extended 門檻 | deep_chain 10 跳 ≥90% (lean) / 50 跳 ≥90% (extended, hops=6+decay0.8) | M | L1-1 |
| **L1-3** | SNN-ONLY 改述/CJK 召回 11%→40% | 當前閾值 0.75 + ONNX 多語言僅 11% | ① FixedSizeCore `slots 65536→131072`（`compute_int("unified","slots")` 已支持 128K）；② `semantic_qa` 閾值/相似度調優 + 負樣本挖掘；③ 用 `probe_retrieval.py` 每日回歸 | SNN-ONLY（關確定性引擎）改述 6/6 + CJK `天空/猫` ≥0.75 召回 ≥40%（`INTELLIGENCE_ASSESSMENT §1.1` 從 1.0→2.5） | L | L1-1 |
| **L1-4** | Hold-out 泛化驗證 | 訓練 accuracy 0.914 在訓練集上，可能過擬合（§9 錯誤 4） | `train_pipeline.py` 切 80/20 hold-out，切分後在 hold-out 上跑 `benchmark_ed3n_garden.py` + `validate_three_column.py` | 報告 hold-out vs train gap，gap <15% 才算不膨脹 | M | — |
| **L1-5** | 統一字典/知識庫去重與品質 | `data/dictionaries/` 242K 但含重複/低質條目，`validate_association` 側向證明字典是瓶頸（`§9 錯誤 2`） | `dictionary_layer.py` 增加去重/品質分（頻率+來源權重），`scripts/audit_dictionary_quality.py` 掃重複率/覆蓋率 | 重複率 <5%，`probe_retrieval.py` CN→EN 8/8 保持 | M | — |
| **L1-6** | SharedLatentSpace 對比訓練加量 | `contrastive loss 0.195` 僅 300 樣本（§5.3） | `train_pipeline.py Phase1` 從 300→3,000 CIFAR + 2,000 ESC-50 真實數據 | contrastive loss <0.1，同類相似度 - 異類相似度 >0.15 | M | — |

### 出階標準（2→4）

```
SNN-ONLY 改述/CJK 召回 ≥40%
+ validate_association deep_chain ≥90%
+ hold-out gap <15%
→ 開放域泛化 1.0 → 3.0（L1 完成）
```

---

## L2 — 4~6（本地可用）— 再下一階

> **目標**：**不靠外部 LLM**，做到「能當助手的本地模型」— 多輪不跑題、記得上下文、會推理、能看圖聽音。

### 為何是 4~6

2~4 解決「單句可理解」，4~6 解決「多輪可使用」。當前 `HAM + VectorStore` 已有 460K 向量但 `SNN-ONLY aggregate 7.8%` 證明記憶/推理未串成對話能力。

### 任務

| ID | 任務 | 背景 | 具體動作 | 驗收 | 工作量 | 依賴 |
|----|------|------|----------|------|--------|------|
| **L2-1** | 多輪對話一致性 | `chat_routes` 有 30 條 history 窗口但無一致性度量 | 新增 `scripts/benchmark_dialogue_coherence.py`（5 輪對話，人設/事實/指代一致性三檔），`DialogueContext` + `MemoryContext` 注入改為可測 | 5 輪人設不漂移 ≥80%，指代消解 ≥70% | L | L1-3 |
| **L2-2** | 記憶命中率 0→60% | `ham_memory` 460K 但 `validate_three_column` SNN-ONLY 0% | `ham_vector_store_manager` 新增 `benchmark_memory_hit.py`（100 問，測向量召回 top-5 命中），優化 `VectorMemoryStore` 索引/分片 | top-5 命中 ≥60% | L | L1-5 |
| **L2-3** | 本地推理泛化（非確定性） | 推理 5/5 全由 `symbolic_reasoner` 正則接住，神經 0/5（`INTELLIGENCE_ASSESSMENT §4.1`） | ① 收集 5K 未被正則覆蓋的推理題（換述/隱含比較/多跳）；② 在 FixedSizeCore 上訓練推理域；③ `benchmark_ed3n_garden.py --engine none --holdout reasoning` 測純神經 | 純神經推理（關確定性）≥50%（現 0%） | L | L1-4 |
| **L2-4** | 多模態接地（視覺/音頻→文字） | `VisualEncoder` MSE 0.271（目標 0.005，54×差距），`AudioWaveform` 僅 309× loss 降但非語音品質 | `SharedLatentSpace` + `VisualDecoder`/`AudioWaveformDecoder` 在 CIFAR-10/ESC-50 上加訓至 MSE<0.05 / SNR>15dB（`IMPROVEMENT_ROADMAP §2.5` 門檻） | 視覺重建可辨形狀，音頻可聽模式 | L | L1-6 |
| **L2-5** | 本地小模型備選（可選） | 4~6 若純 SNN 達不到，可引入本地小 LLM 作兜底，但不算「外部 LLM 層」 | 評估 `Qwen2-0.5B / Phi-3-mini` 量化後在 `llama.cpp` 後端的延遲/顯存（`compute` 5 檔自適應），接 `router` 作 `local_small` 後端 | 本地小模型在 `laptop_normal` 上 <2s/回應，顯存 <4GB | M | — |
| **L2-6** | 統一評測集 100→500 題 | `benchmark_ed3n_garden.py` 僅 20 題 hand-picked，`validate_three_column` 150 抽樣顯示 HYBRID 僅 43.1%（`§4.1.1`） | `benchmark_ed3n_garden.py` 擴至 500 題（math/knowledge/reasoning/chain/dialogue 各 100），分確定性/神經分數 | 500 題上 HYBRID ≥60%，SNN-ONLY ≥30% | M | L1-4, L2-3 |

### 出階標準（4→6）

```
多輪一致性 ≥80% + 記憶 top-5 ≥60% + 純神經推理 ≥50% + 多模態 MSE<0.05
→ 開放域泛化 3.0 → 5.5（本地可用，無需外部 LLM 即可當助手）
```

---

## L3 — 6~10（LLM 層，外部大模型編排）— 已有基建，需做深

> **目標**：把外部 LLM 當「大腦」，Angela 當「身體/記憶/工具/人格」編排起來，達到 GPT-3~4 級產品力。

### 已有什麼

| 能力 | 實現 | 驗收 |
|------|------|------|
| 7 後端（Anthropic/Google/OpenAI/Ollama/llama.cpp/ED3N/GARDEN/unified） | `services/llm/router.py` + `providers/` | 整合測試通過 |
| 9 階段管線 + 8 voter PriorityNegotiator | `chat_routes.py` + `priority_negotiator.py` | 8/8 閉環 |
| 11 Agents + Tool use | `ai/agents/` + `services/handlers/` | 已接線 Step 8 |
| 記憶 RAG | `HAM + VectorStore` 460K + `memory_integration` | 已接線 |
| 硬體自適應 5 檔 | `core/backbone/hardware.py` + `compute.default.yaml` | 已驗證 |

### 待做深（6→8→10）

| ID | 任務 | 背景 | 具體動作 | 驗收 | 工作量 | 依賴 |
|----|------|------|----------|------|--------|------|
| **L3-1** | MMLU/HumanEval 子集基準 | `IMPROVEMENT_ROADMAP §1.2` 9 項「無法驗證」 | 引入 MMLU 100 題 + HumanEval 20 題作 `benchmark_llm.py`，分有/無 RAG/工具對比 | 有 RAG 時 MMLU ≥50%，HumanEval pass≥30% | L | L2-6 |
| **L3-2** | 工具調用成功率 | `CodeExecutionHandler` 曾 RCE（C3），`FileOperation` 曾恆崩（C5），修後未量成功率 | `benchmark_tool_use.py`（100 工具調用：file/code/web_search/system 各 25），記成功/拒絕/崩潰率 | 成功 ≥85%，崩潰 0%，RCE 0% | M | — |
| **L3-3** | 多智能體協作 | `AgentOrchestrator` 曾全死（H10），修後僅單 agent 調用 | `benchmark_multi_agent.py`（10 任務需 2+ agents 協作，如「搜→讀→寫」鏈），`agent_orchestrator.route_task` 串聯 | 協作任務成功 ≥70% | L | L3-2 |
| **L3-4** | 長記憶/人格一致性（跨會話） | `HAM` 有持久化但無跨會話一致性度量 | `benchmark_long_memory.py`（跨 3 天 30 條對話，測人設/偏好/事實記憶），`TrainingCoordinator` + `CausalReasoning` 閉環 | 跨會話人設一致 ≥85%，事實記憶命中 ≥70% | L | L2-1, L2-2 |
| **L3-5** | LLM 路由智能度 | `router` 曾 `deployment.selection` 死碼（M3），`NeuroAutoSelector` 啟發式 | `benchmark_router.py`（1,000 查詢，測路由選對後端 + 成本/延遲），`MetaController` → `NeuroAutoSelector` 閉環可測 | 路由準確率 ≥80%，成本較隨機降 ≥30% | M | — |
| **L3-6** | 多模態 LLM 編排 | 視覺/音頻已接 `vision_service`/`audio_service` 但前端未全打通（`IMPROVEMENT_ROADMAP` 前端多模態 ⬜） | `multimodal/stream` 端到端 + 前端圖片/音頻上傳 E2E 測試 | 圖片問答端到端可用 | M | L2-4 |

### 出階標準（6→10）

```
MMLU ≥60% + HumanEval ≥50% + 工具成功 ≥85% + 協作 ≥70% + 長記憶 ≥70%
→ 有 LLM 6.0 → 8.5（GPT-3.5 級，產品可用）
```

---

## 里程碑時序（建議）

```
現有 ── L0 守成（一週） ── L1 2~4（1~2 月） ── L2 4~6（2~3 月） ── L3 6~10（持續）
 1.0        CI 加固           可理解              可用              好用
```

| 里程碑 | 分數 | 時間 | 標誌性交付 |
|--------|------|------|------------|
| **M0** | 1.0→1.5 | 1 週 | L0-1/2/3 CI 綠，關聯 1.0 守住 |
| **M1** | 1.5→3.0 | 1~2 月 | L1-3 40% 召回，讓神經開始貢獻（SNN-ONLY 不再 7.8%） |
| **M2** | 3.0→5.5 | 2~3 月 | L2-1/2/3 本地可用，多輪+記憶+推理串起來 |
| **M3** | 5.5→8.5 | 持續 | L3-1/2/3/4 LLM 編排達產品級 |

---

## 與現有任務的對應

| 新階梯 | 對應 `NEXT_TASKS` 原任務 | 補充 |
|--------|--------------------------|------|
| L0 | `T-PERF-1`（基準 CI） | 本階梯 L0-1/2/3 即其具體化 |
| L1 | `T-AI-1`（SNN 泛化） | 本階梯 L1-1~6 即其拆解 |
| L2 | `T-AI-1` + `T-TEST-1` + `T-AI-2` | 本階梯 L2-1~6 即其下一階 |
| L3 | `T-AI-2`（MMLU） + `T-DEBT-1` | 本階梯 L3-1~6 即其 LLM 層展開 |

---

> **一句話**：**0~2 是已兌現的確定性能力（守），2~4 讓神經學會改述（懂），4~6 讓本地串成助手（用），6~ 讓外部 LLM 編排成產品（好用）。**
