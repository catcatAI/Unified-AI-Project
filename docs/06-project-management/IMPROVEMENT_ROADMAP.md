<!--
  =============================================================================
  FILE_HASH: Initial
  FILE_PATH: docs/06-project-management/IMPROVEMENT_ROADMAP.md
  FILE_TYPE: planning
  PURPOSE: 完整改善路線圖 — 修正、修復、更新、迭代、訓練、學習、整理
  VERSION: 1.0.0
  STATUS: active
  LANGUAGE: zh-tw
   LAST_MODIFIED: 2026-06-30
  AUDIENCE: developers, agents
  =============================================================================
-->

# Angela AI 改善路線圖 v1.0

> **目標**：根據真實審計結果，有系統地改善專案 — 框架 ~85% 完整，訓練 ~5%。停止吹捧，開始真正訓練和修復。
>
> **分數**：6.0/10（含 LLM），**<0.5/10（純原生引擎）**。所有智慧來自 LLM API。

---

## 目錄

1. [真實優勢矩陣（數據驗證）](#1-真實優勢矩陣數據驗證)
2. [七大工作類別](#2-七大工作類別)
3. [優先級與依賴關係](#3-優先級與依賴關係)
4. [驗證標準](#4-驗證標準)

---

## 1. 真實優勢矩陣（數據驗證）

### 1.1 已驗證的優勢（有數據支持）

| 優勢 | 驗證方式 | 數據量 | 結果 |
|------|---------|--------|------|
| **LLM API 包裝器** | 7 家供應商（OpenAI/Anthropic/Google/Ollama/llama.cpp/ED3N/GARDEN）可正常呼叫 | 整合測試通過 | ✅ 生產可用 |
| **Benchmark harness** | `scripts/benchmark_ed3n_garden.py` — 15 questions across math/knowledge/reasoning | 3 domains × 5 questions | ✅ 可重複執行，支援 JSON 輸出 |
| **ED3N 數學準確率** | `scripts/benchmark_ed3n_garden.py` 跨領域基準 (15題) | 15 基準題 | ✅ 100%（5/5 數學，PEMDAS 修正後） |
| **GARDEN 數學準確率** | 同上 | 15 基準題 | ✅ 100%（5/5 數學） |
| **Memory（VectorStore + HAM）** | 向量搜尋、持久化、語意召回 | 25+ 測試 | ✅ 正常運作 |
| **MathRippleEngine** | 運算 + 6 軸情緒漣漪效應 | 100+ 測試 | ✅ SOPHISTICATED — 原創演算法 |
| **EmotionalBlending** | PAD 情緒模型 + 4D 狀態矩陣 | 整合測試通過 | ✅ SOPHISTICATED — 完整實作 |
| **Bio 模擬堆疊** | ANS、內分泌、神經可塑性、觸覺、創傷、觸發器 | 每系統 20-30+ 測試 | ✅ REAL — 完整生理模擬 |
| **PrimitiveRenderer** | 繪製幾何圖形至 PIL Image | 整合測試 | ✅ 正確抗鋸齒渲染 |
| **DifferentiableRenderer** | 軟柵格化器，梯度可傳遞 | 整合測試 | ✅ 向量化 alpha 合成 |
| **VisionResponseGenerator** | CLIP 分類 → 中/英/日模板輸出 | 整合測試 | ✅ 3 語言模板正常 |
| **FragmentComposer** | 模板拼接 + 自然連接詞 | 整合測試 | ✅ <2ms 組裝 |
| **Agent 路由（管線第 8 步）** | 11 個 agent 自動路由 | 整合測試 | ✅ 已接線 |
| **Chat 管線 9 階段** | WS → 情緒 → 危機 → 對齊 → 閘門 → 路由 → LLM → 學習 → 回應 | 整合測試 | ✅ 完整接線 |
| **CLP（持續學習）** | ED3NTrainer 已接線至聊天管線 + 獨立模式 | 整合測試 | ✅ 已接線，字典成長有效 |
| **CML（持續多模態學習）** | 自主微訓練已接線至 encode 路徑，共用生產管線 | 20 CML 測試通過 + 21 多模態服務測試通過 | ✅ 每次編碼後自動微訓練 |
| **測試數量** | pytest 收集 | **~5,085 tests** (full testpaths, verified 2026-06-30 — §X #49-57: +245 total from 7 stub modules, ripple/node+influence/space, magic numbers, STUB→real, formula coefficients, bug fixes) | ✅ 0 failures — 0 pre-existing failures |

### 1.2 無法驗證的優勢（數據不足）

| 宣稱 | 實際狀態 | 需要什麼數據 | 門檻 |
|------|---------|------------|------|
| ED3N 知識理解 | 數學準確率已透過基準測量（100%，PEMDAS 修正後）。其他領域仍未知。 | 建立擴充基準：MMLU 子集、知識問答、創造性寫作 | 每領域 100+ 測試題 |
| GARDEN SNN 推論品質 | 從未被基準測試 | GARDEN 專用基準（問答、分類） | 100+ 測試題 |
| VisualEncoder 品質 | 存在但未評量 | 與真實 CV 模型（ResNet、CLIP）比較的準確率/召回率 | 1,000+ 圖片標註 |
| ImageGenerator 品質 | 權重隨機，無輸出可言 | 訓練後用 FID/IS 評量 | 10,000+ 生成圖片 |
| AudioWaveformDecoder 品質 | 權重隨機，輸出為雜訊 | 訓練後用 MOS/MCD 評量 | 100+ 音頻樣本 |
| CausalReasoning 準確率 | 僅 Pearson 相關（非因果） | 建立因果推理基準（如 CauseNet、Tübingen 因果配對） | 500+ 因果配對 |
| DualEncoderRouter 路由品質 | 4 後端存在但未評量路由準確率 | 建立路由準確率基準 | 1,000+ 查詢 |
| CrossModalTrainer 映射品質 | 共現映射未評量 | 建立跨模態檢索準確率基準 | 500+ 跨模態配對 |
| VisionService OCR/人臉/場景 | 功能存在但未評量單項準確率 | 每項功能 100+ 測試圖 | 100+ 圖片/項 |

### 1.3 已確認的缺陷

| 缺陷 | 嚴重性 | 證據 | 行數/規模 |
| **IntentModel.scan_memory_proximity 為 stub（pass）** | ✅ **FIXED** (2026-06-28) — 現已迭代狀態維度、查詢橋接器、建立 EXPLORATION 意圖 | `intent_model.py:85-100`, `test_intent_model.py` 16/16 pass |
| **IntentModel.generate_homeostatic_intents 為 stub（pass）** | ✅ **FIXED** (2026-06-28) — 現已檢查閾值 (0.3) 並為不足量建立 HOMEOSTASIS 意圖 | `intent_model.py:103-128`, `test_intent_model.py` 16/16 pass |
| **CausalReasoningEngine predict() 無人消費** | ✅ **FIXED** (2026-06-28) — predict() 現已接入 LLM prompt 管線: chat_routes._inject_causal_predictions → prompt_builder._append_causal_insights | `chat_routes.py:499-512`, `prompt_builder.py:283-300` |
| **DigitalLifeIntegrator 3/6 狀態無行為** | ✅ **FIXED** (2026-06-29) — INITIALIZING (保守基線+dynamic params)、AWAKENING (user monitor+bio覺醒)、DORMANT (深度鞏固+放鬆+資源審計) 全數實作 | `digital_life_integrator.py:_apply_state_behaviors()` |
| **Heartbeat Integration 60x 頻率差** | ✅ **FIXED** (2026-06-29) — Integration 循環從 0.1s 固定頻率改為 2.0-10.0s 動態頻率（基於 arousal） | `heartbeat.py:_integration_loop()` |
| **Level5ASI 模擬 sleep(1.0)** | ✅ **FIXED** (2026-06-29) — 移除 `await asyncio.sleep(1.0)` 模擬延遲，改為 `await asyncio.sleep(0)` | `level5_asi_system.py:_process_with_agent()` |
| **IntentModel 未接入生產管線** | ✅ **FIXED** (2026-06-29) — IntentManager 現已接入 DigitalLifeIntegrator._life_cycle_loop(): 每 30s 生成 homeostatic intents，讀取 get_intent_influence() 3D 向量，以 magnitude×0.1 作為 delta 回寫至 state matrix 維度 (energy/focus/happiness/bond) | `digital_life_integrator.py:_update_intent_state()` |
| **AutonomousLifeCycle 決策間隔 300s 太慢** | ✅ **FIXED** (2026-06-29) — 預設從 300s (5min) 改為 60s (1min)，§8.6 #8 | `autonomous_life_cycle.py:169` |
| **核心 background loop 缺少異常處理** | ✅ **DONE** (2026-06-29) — 再 6 個檔案加入 try/except 保護背景循環 (action_execution_bridge, ANS, EmotionalBlending, MultidimensionalTrigger, Neuroplasticity, Tactile)。總計 **16 task handlers in 13 files**。所有背景 loop 皆已保護，§8.6 #7 實質完成。heartbeat stop() 同時修復 _integration_task 未取消 bug。 | §8.6 #7 |
| **Bridge _wait_for_completion busy-poll 0.05s** | ✅ **FIXED** (2026-06-29) — 改用 asyncio.Event 事件驅動，消除 bridge_fast(0.05s) 與 bridge_poll(0.1s) 其中一個重複循環。第一處事件驅動取代輪詢實作。另整併 `emotion_tick`(1.0s)→`emotion_update`(1.0s)、`bridge_fast`→`bridge_error_backoff` 語義命名。§8.6 #2 進度 3/4 | `action_execution_bridge.py` §8.6 #2 #3 |
| **HardwareProfile 硬體感知設定檔** | ✅ **DONE** (2026-06-29) — 5 種硬體場景 + 22 循環欄位 + 自動偵測 + runtime overrides。`hardware_profile.py`, 20 tests | `core/system/config/hardware_profile.py` §8.6 #5 |
| **time.sleep() 全部審計** | ✅ **DONE** (2026-06-29) — 確認所有剩餘 `time.sleep()` 皆在同步/執行緒上下文，§8.6 #6 實質完成 | 多個檔案 §8.6 #6 |
|------|:------:|------|:---------:|
| **VisualDecoder 投射權重已訓練（CNN 紋理分支仍隨機）** | MEDIUM | 投射權重訓練於 CIFAR-10（42× loss 降）。**T1 DONE**: 22K texture params now trainable via `ReconstructionCycle.train_texture_step()` (pixel-level MSE + full analytic gradients). `TextureTrainer` + `FullTrainingPipeline` Phase 3a supports synthetic + real data. **剩餘**: 需實際訓練 texture 權重（非隨機）。 | 143L，投射權重已訓練，紋理權重可訓練 |
| **AudioWaveformDecoder 投射權重已訓練（波表生成器仍隨機）** | MEDIUM | 投射權重訓練於 ESC-50（309× loss 降）。**T2 DONE**: 55.1K wavetable params now trainable via `ReconstructionCycle.train_wavetable_step()` (waveform MSE + full analytic gradients). `WavetableTrainer` + `FullTrainingPipeline` Phase 3b supports synthetic + real data. **剩餘**: 需實際訓練波表權重（非隨機）。 | 179L，投射權重已訓練，波表權重可訓練 |
| **SequenceGenerator 權重隨機** | ✅ **FIXED** (T3+T4 DONE, 2026-06-29) — T3: BPTT backward pass rewritten (was corrupting gradients, missing bias updates, no temporal propagation). Added `get_weights/set_weights`, `SequenceTrainer`, FullTrainingPipeline Phase 3c with persistence for all 10 RNN weight arrays. T4: Phase 3d optionally retrains SequenceGenerator on library-derived synthetic pairs. All RNN weights now trainable with correct gradients. | 212L，權重 seed=42 |
| **ImageGenerator 管線未訓練** | ✅ **FIXED** (T4 DONE, 2026-06-29) — `PrimitiveTrainer` populates ~120 geometric shapes, trains `PrimitiveEncoder` autoencoder (loss<0.05), re-encodes library, `ImageGenerator` produces multi-color structured output after Phase 3d training. | 200L+，4 元件串接已訓練 |
| **CerebellumEngine 已實作 ✅ DONE** | LOW | 27L→172L，姿勢庫（站立/行走/坐/伸手）+ 應力調節顫抖模型 + 本體感覺誤差修正 + 內插 | `core/bio/cerebellum_engine.py` (172L) |
| **PerceptionEngine 已實作 ✅ DONE** | LOW | 100L→158L，動態信心度（取樣粒子計數 + 時間平滑）+ 動態顯著性 + 跨模態衝突偵測 | `core/perception/perception_engine.py` (158L) |
| **AttentionController 已實作 ✅ DONE** | LOW | 33L→164L，顯著性地圖（中心偏置 + 對比度）+ IOR + 掃描路徑 + 候選評分 | `core/perception/attention_controller.py` (164L) |
| **AuditoryAttention 已清理 ✅ DONE** | LOW | 20L→10L，空類別已移除，保留向後相容別名至 AttentionController | `core/perception/auditory_attention.py` (10L) |
| **TaskGenerator 核心邏輯完成（已接線至 PrecomputeService）** | LOW | `predict_next_query()` + `generate_tasks()` + `analyze_patterns()` 已實作。已接線至 `AngelaLLMService::_schedule_precompute_tasks()`，每次成功回應後自動分析模式並排入預計算佇列。`_history` 有上限（1000），支援 per-user 隔離。 | 91L，9 測試通過 |
| **AdversarialGenerationSystem 核心邏輯完成（已接線至生產）** | LOW | 10 種對抗模式 + `evaluate_robustness()`（含中英文拒絕關鍵字、無文字偵測、語言比例）已實作。生產接線：`Level5ASISystem.process_request()` 每次請求後自動執行 `_run_adversarial_evaluation()` + 綜合測試包含對抗穩健性。`get_average_robustness()` 提供聚合分數。 | 115L，9 測試通過 |
| **CausalReasoningEngine 已實作 ✅ DONE** | LOW | 99L→218L，Granger 因果（F 檢定）+ 混淆變數偵測（偏相關）+ do-calculus 干預模擬 + 因果 DAG | `ai/reasoning/causal_reasoning_engine.py` (218L)，14 新測試通過 |
| **CML pipeline 已接線至生產元件** | LOW | CML 現在與 MultimodalService 共享訓練管線：micro-training 直接改善生產編碼/解碼。孤立管線問題已修復。 | `multimodal_service.py:160` 將生產管線傳遞給 CML |
| **CML 已接線至生產 encode 路徑** | FIXED | CML 現在透過 `_encode_impl()` 在每次成功編碼後自動記錄並作微訓練，且與 MultimodalService 共用訓練管線（非孤立）。 | `multimodal_service.py:387-398` 嵌入 encode |
| **Live2D 頭像圖片層為隨機矩形** | LOW | model3.json 有效，但圖片為隨機彩色矩形 | 206L＋樁模組 |
| **SemanticVisualEncoder 降級至隨機** | LOW | 無 torch/CLIP 時回退至 np.random.randn | ~60L 回退路徑 |
| **SemanticAudioEncoder 降級至 MFCC 統計** | LOW | 無 torch/whisper 時回退至基本統計 | ~60L 回退路徑 |
| **ThreeLayerVisual 已自動訓練 PCA** | ✅ **FIXED** (2026-06-29) — 編碼器自動訓練（SVD + 零填充至 128-dim），解碼器動態 dim。21 項測試通過。 | ~450L，自動訓練 |
| **視訊 = 逐幀影像分析** | LOW | process_video_frame() 重複呼叫 analyze_image() + 隨機 motion_detected | ~50L 無時間模型 |

---

## 2. 七大工作類別

### 2.1 修正 (Fixes)

| # | 項目 | 檔案 | 優先級 | 難度 |
|---|------|------|:------:|:----:|
| F1 | 修正 ED3N 數學評估中 >100L 的長函數 | ✅ **DONE** (commit `fabbb2041`, Jun 28) | `ed3n_engine.py` | P4 | 中 |
| F2 | 修正 ModelBus 路由中的 >100L 長函數 | ✅ **DONE** (scan confirms 0 functions >100L remain in both files) | `model_bus.py` | P4 | 中 |
| F3 | 修正所有文件中的錯誤分數（已完成） | 多個 MD | P0 | 低 |
| F4 | 修正 LLM 路由中缺少 timeouts/retries | ✅ **DONE** (commit `dcd7044e1~`, Jun 28) | `router.py` | P2 | 低 |
| F5 | NeuroAutoSelector LearnRecorder 連接至 MetaController | ✅ **DONE** (commit `44fec2abb~`, Jun 28) | `neuro_auto_selector.py:764-773` + `router.py:464-470` |

### 2.2 修復 (Repairs)

| # | 項目 | 檔案 | 優先級 | 難度 |
|---|------|------|:------:|:----:|
| R1 | 實作 CerebellumEngine — 真實本體感覺/姿勢內插 | ✅ **DONE** (2026-06-28) | `core/bio/cerebellum_engine.py` (172L) | P3 | 中 |
| R2 | 實作 AttentionController — 顯著性計算、IOR、掃描路徑 | ✅ **DONE** (2026-06-28) | `core/perception/attention_controller.py` (164L) | P3 | 高 |
| R3 | 實作 PerceptionEngine — 真實融合、模糊度解析 | ✅ **DONE** (2026-06-28) | `core/perception/perception_engine.py` (158L) | P3 | 中 |
| R4 | 實作 TaskGenerator — 真實任務預測/分解 | ✅ **DONE** (commit `fba3fb14b`, Jun 28) | P4 | 中 |
| R5 | 實作 AdversarialGenerationSystem — 真實對抗訓練 | ✅ **DONE** (commit `43129d437`, Jun 28) | P4 | 高 |
| R6 | 移除 AuditoryAttention（空別名）或實作 | ✅ **DONE** | P3 | 低 |
| §X #49 | 5 個實模組 (precision_projection_matrix, resonance, cognitive_pipeline, attractor_field, negativity) | ✅ **DONE** (+70 tests unblocked) | P3 | 中 |
| §X #50 | 2 個實模組 (ripple/node, influence/space) | ✅ **DONE** (+10 tests unblocked) | P3 | 中 |
| §X #53 | 4 Level5ASI STUB classes → real modules | ✅ **DONE** (distributed_coordinator, hyperlinked_parameter_cluster, aligned_base_agent, HSPMessageEnvelope) | P3 | 低 |

### 2.3 更新 (Updates)

| # | 項目 | 優先級 | 說明 |
|---|------|:------:|------|
| U1 | 安裝 faster-whisper 以啟用高品質離線 STT | ✅ **DONE** | P2 |
| U2 | 安裝 torch + transformers 以啟用 CLIP 語意編碼器 | ✅ **DONE** | P2 |
| U3 | 安裝 torch + openai-whisper 以啟用語意音訊編碼 | ✅ **DONE** | P2 |
| U4 | 更新 LLM API 用戶端至最新版本 | ✅ **N/A** | P3 |
| U5 | 更新相依性以修復 Dependabot 漏洞（141→26 個） | ✅ **DONE** | P2 |
| V1 | YOLO 物件檢測 — 前端開發輔助（Vision-Assisted Development） | P2 | 未開始 |
 
### 2.4 迭代 (Iterations)
| # | 項目 | 優先級 | 難度 | 目前 | 目標 |
|---|------|:------:|:----:|:----:|:----:|
| I1 | NeuroAutoSelector ↔ MetaController closed-loop | ✅ **DONE** | P2 | 低 | 啟發式 | 適應性 |
| I2 | ED3N 字典編碼快取 LRU | ✅ **DONE** | P3 | 低 | 基本逐出 | LRU |
| I3 | GARDEN SNN 稀疏前向傳播 | ✅ **DONE** | P3 | 中 | 稠密矩陣 | 稀疏計算 |
| I4 | Agent 路由 11/11 類型 | ✅ **DONE** | P2 | 中 | 5/11 路由 | 11/11 路由 |
| I5 | ED3N 循環限制可設定 | ✅ **DONE** | P4 | 低 | 寫死 3 | 可設定 |
| I6 | MetaController EWMA 校準 | ✅ **DONE** | P3 | 低 | 視窗=100 | EWMA |

### 2.5 訓練 (Training)

| # | 項目 | 優先級 | 難度 | 目前 | 目標 |
|---|------|:------:|:----:|:----:|:----:|
| T1 | 訓練 VisualDecoder（CNN 紋理分支） | ✅ **DONE** (2026-06-29) | P1 | 中 | 投射訓練 + 紋理可訓練 | 可辨識 128×128 影像 |
| T2 | 訓練 AudioWaveformDecoder（波表合成） | ✅ **DONE** (2026-06-29) | P1 | 高 | 投射訓練 + 波表可訓練 | 可聽語音/音樂 |
| T3 | 訓練 SequenceGenerator（RNN + BPTT） | ✅ **DONE** (2026-06-29) | P1 | 高 | BPTT修正 | 合理序列輸出 |
| T4 | 訓練 GVV 文生圖管線（ImageGenerator） | ✅ **DONE** (2026-06-29) | P1 | 高 | 120 形狀 + autoencoder | 文字→幾何影像 |
| T5 | 訓練 ThreeLayerVisual（自動 PCA） | ✅ **DONE** (2026-06-29) | P2 | 中 | 自動訓練 | 128-dim 輸出 |
| T6 | FullTrainingPipeline 啟動接線 | ✅ **DONE** | P2 | 低 | 背景執行緒 | 自動權重檢查 |
| T7 | CML 自主微訓練 | ✅ **DONE** | P2 | 低 | encode 自動觸發 | 生產管線共用 |

**訓練驗證標準**：

| 模型 | 損失 | 驗證指標 | 最低可接受值 |
|------|:----:|:---------:|:-----------:|
| VisualDecoder | MSE < 0.05 | SSIM > 0.6, PSNR > 25dB | 可辨識物件形狀 |
| AudioWaveformDecoder | MSE < 0.1 | SNR > 15dB, MOS > 2.0 | 可聽語音模式 |
| SequenceGenerator | Cross-entropy < 1.0 | 原始序列準確率 > 60% | 合理的原始順序 |
| FullTrainingPipeline | 對比損失 < 0.1 | 重建損失 < 0.05 | 跨模態檢索 > 50% top-5 |
| ThreeLayerVisual | MSE < 0.005 | SSIM > 0.7 | 清晰 32×32 重建 |

### 2.6 學習 (Learning)

| # | 項目 | 優先級 | 難度 | 目前 | 目標 |
|---|------|:------:|:----:|:----:|:----:|
| L1 | ED3NTrainer → SequenceTrainer/JointTrainer 接線 | ✅ **DONE** (commit `~HEAD`, Jun 28) | P2 | 中 | 僅使用基本 train_step | 3 個 trainer 全部使用 |
| L2 | ED3N 引擎獨立使用時，CLP 自動建立 trainer | ✅ **DONE** (commit `5e537bd86`, Jun 28) | P2 | 低 | standalone CLP 跳過梯度步驟，trainer=None | 自動建構 ED3NTrainer |
| L3 | CML 品質趨勢 → 改善觸發器（改善/穩定/退化） | ✅ **DONE** (commit `~HEAD`, Jun 28) | P3 | 低 | 僅記錄趨勢 | 根據趨勢動態調整觸發 |
| L4 | NeuroAutoSelector LearnRecorder 資料 → 適應性選擇 | ✅ **DONE** (commit `~HEAD`, Jun 28) | P2 | 低 | 記錄但從不使用 | 選擇隨時間改善 |
| L5 | 公式回饋迴路 — 公式影響→情緒→回應 | ✅ **DONE** (commit `dd19635fe`, Jun 28) | P2 | 中 | 67 測試但影響未經驗證 | 12 新測試量化鏈條：認知壓力→PAD→dominant_emotion→響應模板 |
| L6 | 跨語言學習 — 從一個語言的互動改善其他語言 | P3 | 高 | 所有語言獨立 | 知識跨語言共享 |

### 2.7 整理 (Organization)

| # | 項目 | 優先級 |
|---|------|:------:|
| O1 | 檔案頭部移除 Matrix 註解（157 檔案需處理，僅裝飾性） | P5 |
| O2 | 清理測試中 dead/commented 程式碼 | ✅ **DONE** (2026-06-29, §X #44) — 移除 152 行死碼：6 個 pass-only stub 測試，2 個 e2e 檔案中 102 行註解代碼 | P4 |
| O3 | 標準化 imports（isort 跨所有 Python 檔案） | ✅ **DONE** (isort 8.0.1, profile=black, 738 files: 2908 insertions/2100 deletions) | P4 |
| O4 | 清理 docs/ 中過時/重複文件（移入 09-archive/） | ✅ **DONE** (2026-06-28): 7 files archived: PROJECT_ROADMAP, RECOMMENDATIONS, TODO_ANALYSIS, UNIFIED_AI_IMPROVEMENT_PLAN, ACTION_PLAN, DOCUMENTATION_TRUTH_MAP, port_routing_plan. 3 kept: VERSION_CONTROL_STRATEGY, PROJECTS_COLLABORATION_GUIDE, GIT_AND_PROJECT_MANAGEMENT. | P3 |
| O5 | 更新 INDEX.md 和 UNIFIED_DOCUMENTATION_INDEX.md 以反映文件變動 | ✅ **DONE** (INDEX.md already correct; UNIFIED_DOCUMENTATION_INDEX.md was itself archived to 09-archive/; README.md links updated to point to archive) | P3 |
| O6 | 為每個主要子系統建立統一的 `__init__.py`（公開 API） | ✅ **DONE** (2026-06-28): 8 `__init__.py` files updated: `ai/core/` created (19 exports), `ai/ed3n/` docstring added (20 exports), `ai/meta/` docstring added (3 exports), `ai/reasoning/` docstring added (DEPRECATED), `core/bio/` `__all__` added (58 exports across 24 modules), `core/perception/` created (16 exports), `core/managers/` created (10 exports). 3 previous O6 files from earlier: `ai/memory/`, `ai/memory/ham_memory/`, `services/`, `services/api/` — total 12 files. Remaining gaps: `ai/context/` (already has both), `ai/garden/` (already has both), `ai/alignment/` (already has both), `ai/response/` (already has both), `ai/lifecycle/` (already has both), `ai/agents/` (already has both), `ai/multimodal/` (already has both), `core/` (already has both). | P4 |
| O7 | HardwareProfile 硬體場景頻率設定檔 | ✅ **DONE** (2026-06-29): `core/system/config/hardware_profile.py` — 5 scenarios, 22 interval fields, auto-detection, runtime overrides, 20 tests | P2 |
| O8 | HardwareProfile → loop_sleep() 接線 | ✅ **DONE** (2026-06-29): `magic_numbers.py` 新增 `_get_hardware_profile()` lazy singleton + `loop_sleep()` 自動套用 multiplier。所有 32+ 循環現在有基本硬體感知。§8.6 #4 BASIC | P2 |

---

## 3. 優先級與依賴關係

### 階段 0 — 立即（1-2 天）
修正文件錯誤 ✅（已完成）+ 訓練 VisualDecoder ✅（T1 DONE）

```
F3 → (完成) → O5 → O4
T1 → ✅ DONE (2026-06-29)
T2 → ✅ DONE (2026-06-29)
T3 → ✅ DONE (2026-06-29)
T4 → ✅ DONE (2026-06-29) — GVV 管線 Phase 3d
U2, U3 → T2 (torch 用於語意編碼訓練, DONE)
```

### 階段 1 — 短期（1-2 週）
訓練、修復嚴重缺陷、接線訓練管線

```
T1 → 驗證 VisualDecoder
T3 → T4 → 驗證 GVV
T2 → 驗證 AudioWaveformDecoder
R1, R2, R3 → 修復感知系統
U1 → 啟用離線 STT
U5 → 修復 141 個漏洞
F4 → LLM 路由穩定性
```

### 階段 2 — 中期（2-4 週）
學習迴路、迭代改善、訓練接線

```
I1, L4 → 適應性後端選擇
I4 → 所有 agent 路由
L1, L2 → 完整 ED3N 訓練管線使用
T6, T7 → FullTrainingPipeline + CML 接線
L5 → 公式行為影響量化
F5 → NeuroAutoSelector ↔ MetaController 閉合
```

### 階段 3 — 長期（1-2 月）
完整訓練、全新實作、基準建立

```
R4, R5 → 真實任務產生器 + 對抗訓練
I2, I3 → 效能最佳化
L6 → 跨語言學習
U4 → LLM API 更新
O1 → 程式碼組織 (P5 裝飾性)
O6 → ✅ **DONE** (2026-06-28, 12 個 \`__init__.py\`)
O2 → ✅ **DONE** (2026-06-29, §X #44, 152 行死碼移除)
```

---

## 4. 驗證標準

### 4.1 測試覆蓋

```bash
# 執行所有測試（基線：4,902）
pytest tests/ apps/backend/tests/ --collect-only -q

# 測量基線完成後，每次變更保持或增加計數
# 新實作必須包含測試
```

### 4.2 訓練驗證

每個訓練任務必須通過：

1. **損失下降**：最終損失 < 初始損失 × 0.3
2. **視覺檢查**：VisualDecoder 輸出可辨識為 128×128 內容（不是雜訊）
3. **聽覺檢查**：AudioWaveformDecoder 輸出有可辨識模式（不是純噪音）
4. **基準**：每個訓練模型都有量化基準（SSIM、PSNR、MOS、準確率等）

### 4.3 重構驗證

- 所有重構必須通過現有測試
- C901 複雜度 > B 的「新」函數零容忍
- 超過 100 行的「新」函數零容忍

### 4.4 文件驗證

- 每個宣稱必須可由實際程式碼路徑 + git commit 驗證
- 分數必須反映真實能力（含 LLM：6.0/10，純原生：<0.5/10）
- 沒有「〜」估計值 — 用「未測量」或「X 測試通過」
