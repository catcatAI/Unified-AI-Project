<!--
  =============================================================================
  FILE_HASH: Initial
  FILE_PATH: docs/06-project-management/IMPROVEMENT_ROADMAP.md
  FILE_TYPE: planning
  PURPOSE: 完整改善路線圖 — 修正、修復、更新、迭代、訓練、學習、整理
  VERSION: 1.0.0
  STATUS: active
  LANGUAGE: zh-tw
  LAST_MODIFIED: 2026-06-28
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
| **測試數量** | pytest 收集 | 4,785 測試 | ✅ 41 skipped，0 errors |

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
|------|:------:|------|:---------:|
| **VisualDecoder 投射權重已訓練（CNN 紋理分支仍隨機）** | MEDIUM | 投射權重訓練於 CIFAR-10（42× loss 降），但 CNN 紋理分支仍隨機 → 輸出 = 結構化但模糊 | 143L，投射權重已訓練，紋理權重隨機 |
| **AudioWaveformDecoder 投射權重已訓練（波表生成器仍隨機）** | MEDIUM | 投射權重訓練於 ESC-50（309× loss 降），但波表生成器仍隨機 → 輸出 = 結構化但非語音 | 179L，投射權重已訓練，波表權重隨機 |
| **SequenceGenerator 權重隨機** | HIGH | RNN 架構真實，輸出 = 隨機向量 | 212L，權重 seed=42 |
| **ImageGenerator 管線未訓練** | HIGH | 灰色畫布或隨機形狀（CLIP 降級為 hash(text)） | 200L+，4 元件串接但無訓練 |
| **CerebellumEngine 樁模組** | MEDIUM | 27L，interpolate() 為 no-op，標示「等待完整實作」 | 27L 樁模組 |
| **PerceptionEngine 寫死值** | MEDIUM | visual confidence=0.85 hardcoded | 100L，80L 可執行 |
| **AttentionController 樁模組** | MEDIUM | 33L，無顯著性計算，無 IOR，無掃描路徑 | 33L 無計算 |
| **AuditoryAttention 空類別** | MEDIUM | 20L，別名至 AttentionController（本身為樁模組） | 20L 空類別 |
| **TaskGenerator 核心邏輯完成（已接線至 PrecomputeService）** | LOW | `predict_next_query()` + `generate_tasks()` + `analyze_patterns()` 已實作。已接線至 `AngelaLLMService::_schedule_precompute_tasks()`，每次成功回應後自動分析模式並排入預計算佇列。`_history` 有上限（1000），支援 per-user 隔離。 | 91L，9 測試通過 |
| **AdversarialGenerationSystem 核心邏輯完成（已接線至生產）** | LOW | 10 種對抗模式 + `evaluate_robustness()`（含中英文拒絕關鍵字、無文字偵測、語言比例）已實作。生產接線：`Level5ASISystem.process_request()` 每次請求後自動執行 `_run_adversarial_evaluation()` + 綜合測試包含對抗穩健性。`get_average_robustness()` 提供聚合分數。 | 115L，9 測試通過 |
| **CausalReasoningEngine 僅 Pearson** | MEDIUM | 99L，無時間因果、無混淆變數、無 do-calculus | 99L 骨架 |
| **CML pipeline 已接線至生產元件** | LOW | CML 現在與 MultimodalService 共享訓練管線：micro-training 直接改善生產編碼/解碼。孤立管線問題已修復。 | `multimodal_service.py:160` 將生產管線傳遞給 CML |
| **CML 已接線至生產 encode 路徑** | FIXED | CML 現在透過 `_encode_impl()` 在每次成功編碼後自動記錄並作微訓練，且與 MultimodalService 共用訓練管線（非孤立）。 | `multimodal_service.py:387-398` 嵌入 encode |
| **Live2D 頭像圖片層為隨機矩形** | LOW | model3.json 有效，但圖片為隨機彩色矩形 | 206L＋樁模組 |
| **SemanticVisualEncoder 降級至隨機** | LOW | 無 torch/CLIP 時回退至 np.random.randn | ~60L 回退路徑 |
| **SemanticAudioEncoder 降級至 MFCC 統計** | LOW | 無 torch/whisper 時回退至基本統計 | ~60L 回退路徑 |
| **ThreeLayerVisual 需 PCA 檔案** | LOW | 最佳生成器但需已訓練 PCA 檔案（選擇性載入） | ~400L，需外部檔案 |
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
| R1 | 實作 CerebellumEngine — 真實本體感覺/姿勢內插 | ✅ **DONE** (2026-06-28): 27L→172L. Posture library (standing/walking/sitting/reaching) with 9-element theta_matrix + 5-finger matrices. `execute_command()` — stress-modulated tremor (10Hz, amplitude scaled by bio_state stress). Proprioceptive error correction via `update_proprioception()`. Smooth linear `interpolate()` with theta + finger blending. Backward compatible: heartbeat.py uses unchanged interface. | `core/bio/cerebellum_engine.py` (172L) | P3 | 中 |
| R2 | 實作 AttentionController — 顯著性計算、IOR、掃描路徑 | ✅ **DONE** (2026-06-28): 33L→164L. Added saliency map computation (center-bias + contrast via local std), Inhibition of Return (configurable radius/duration, auto-pruning), scan path + fixation history tracking, candidate scoring with IOR-aware selection, `compute_saliency_map()`, `get_scan_path()`, `get_fixation_history()`, `set_time()`, `get_saliency_at()`. Backward compatible: 3 existing tests pass, `AuditoryAttentionController` alias unchanged. | `core/perception/attention_controller.py` (164L) | P3 | 高 |
| R3 | 實作 PerceptionEngine — 真實融合、模糊度解析 | ✅ **DONE** (2026-06-28): 100L→158L. Removed hardcoded confidence/saliency — now dynamic: confidence from sampler particle count with temporal smoothing (5-window); saliency from attention controller + modality weights. Added `detect_conflicts()` for cross-modal conflict detection by confidence. `decide_focus()` uses attention controller saliency map when no modality given. | `core/perception/perception_engine.py` (158L) | P3 | 中 |
| §X #27 | 實作 CausalReasoningEngine — 因果推論 | ✅ **DONE** (2026-06-28): 99L skeleton→218L. Added Granger causality (temporal F-test), confounding detection (partial correlation), do-calculus intervention simulation, causal graph adjacency. 14 new unit tests. | `ai/reasoning/causal_reasoning_engine.py` (218L) | P3 | 高 |

| R4 | 實作 TaskGenerator — 真實任務預測/分解 | ✅ **DONE** (commit `fba3fb14b`, Jun 28) | `ai/memory/task_generator.py` (46→91L) + `router.py` (_schedule_precompute_tasks) | P4 | 中 |
| R5 | 實作 AdversarialGenerationSystem — 真實對抗訓練 | ✅ **DONE** (commit `43129d437`, Jun 28) | `ai/alignment/adversarial_generation_system.py` (65→115L) + `level5_asi_system.py` (_run_adversarial_evaluation) | P4 | 高 |
| R6 | 移除 AuditoryAttention（空別名）或實作 | ✅ **DONE** (`auditory_attention.py`: removed empty stub class, kept backward-compat alias to AttentionController) | `core/perception/auditory_attention.py` (20→10L) | P3 | 低 |

### 2.3 更新 (Updates)

| # | 項目 | 優先級 | 說明 |
|---|------|:------:|------|
| U1 | 安裝 faster-whisper 以啟用高品質離線 STT | ✅ **DONE** (faster-whisper 1.2.1 installed, ctranslate2 4.8 int8, Whisper base model auto-downloads on first call) | P2 |
| U2 | 安裝 torch + transformers 以啟用 CLIP 語意編碼器 | ✅ **DONE** (torch 2.11.0, transformers 5.5.4 installed, CLIP model cached, 512-dim vectors verified) | P2 |
| U3 | 安裝 torch + openai-whisper 以啟用語意音訊編碼 | ✅ **DONE** (openai-whisper 20250625 installed, Whisper tiny model cached, 384-dim vectors verified) | P2 |
| U4 | 更新 LLM API 用戶端至最新版本 | P3 | openai>=1.0, anthropic>=0.30, google-genai |
| U5 | 更新相依性以修復 Dependabot 漏洞（141 個） | P2 | 3 critical, 72 high, 55 moderate, 11 low |
| V1 | YOLO 物件檢測 — 前端開發輔助（Vision-Assisted Development） | P2 | 整合 YOLO 後可使專案透過螢幕截圖分析參與前端開發。**關鍵要求：多視窗辨識** — 系統必須能區分自己的前端 UI 與其他應用程式視窗（VS Code、Slack、瀏覽器等），不得誤檢。做法：① OS API 視窗識別（pygetwindow/win32）比對白名單行程與標題。② 前端源碼特徵指紋（Electron DOM / Live2D canvas / PyQt6 固定佈局）建立專屬特徵庫。③ 非白名單視窗區域檢測結果直接排除。④ 佈局一致性驗證 — 檢測結果須符合預期元件結構才判定為自己 UI。預期能力：① UI 元件檢測（按鈕、輸入框、卡片、導航欄、圖示）→ 結構化元件樹。② 前端 diff — 截圖比較。③ 可及性檢查。④ E2E 測試生成（Playwright/Cypress selector）。依賴 `ultralytics` + YOLO11 + pygetwindow + 前端佈局特徵庫。非 ML 瓶頸 — 純模型整合與 wrapper 實作。 |
 
### 2.4 迭代 (Iterations)

| # | 項目 | 優先級 | 難度 | 目前 | 目標 |
|---|------|:------:|:----:|:----:|:----:|
| I1 | 改善 NeuroAutoSelector 後端選擇（連接至 MetaController） | ✅ **DONE** (L4: NeuroAutoSelector ↔ MetaController closed-loop — MetaController history filters backends by recent performance, record_result forwards hw_score+success) | P2 | 低 | 啟發式 | 適應性、數據驅動 |
| I2 | 改善 ED3N 字典編碼快取（LRU 取代基本逐出） | ✅ **DONE** (commit `b233361b1~`, Jun 28) | P3 | 低 | 基本逐出 | LRU |
| I3 | 改善 GARDEN SNN 前向傳播效率 | ✅ **DONE** (commit `15d3f3d70`, Jun 28) | P3 | 中 | 稠密矩陣 (`a @ W`) | 稀疏計算 (僅活躍神經元) |
| I4 | 改善 Agent 路由以包含更多查詢類型（目前僅 5 種路由） | ✅ **DONE** (commit `dcd7044e1~`, Jun 28) | P2 | 中 | 5/11 路由 | 11/11 路由 |
| I5 | 改善 ED3N 循環限制（由寫死 3 改為可設定） | ✅ **DONE** (commit `f3520ca1e~`, Jun 28) | P4 | 低 | 寫死 3 | 可設定 + 收斂偵測 |
| I6 | 改善 MetaController 信心校準（windowing→EWMA） | ✅ **DONE** (commit `HEAD~`, Jun 28) | P3 | 低 | 視窗=100 | EWMA |

### 2.5 訓練 (Training)

| # | 項目 | 優先級 | 難度 | 目前 | 目標 |
|---|------|:------:|:----:|:----:|:----:|
| T1 | 訓練 VisualDecoder（128×128 RGB via transposed conv） | P1 | 中 | 投射權重已訓練（42× loss 降），CNN 紋理分支仍隨機 | 可辨識 128×128 影像 |
| T2 | 訓練 AudioWaveformDecoder（多頻帶波表合成） | P1 | 高 | 投射權重已訓練（309× loss 降），波表生成器仍隨機 | 可聽語音/音樂 |
| T3 | 訓練 SequenceGenerator（RNN + BPTT，CLIP→原始序列） | P1 | 高 | 權重隨機 → 隨機向量 | 合理的原始序列輸出 |
| T4 | 訓練完整 GVV 文生圖管線（ImageGenerator） | P1 | 高 | 灰色畫布/隨機形狀 | 文字→幾何影像 |
| T5 | 訓練 ThreeLayerVisual（PCA + 非線性解碼器）於真實資料 | P2 | 中 | 選擇性載入 PCA 檔案 | 自動訓練 PCA |
| T6 | 觸發 FullTrainingPipeline（對比預訓練 + 重建微調） | ✅ **DONE** (commit `HEAD~`, Jun 28) | P2 | 低 | 383L 有 0 呼叫者 → 在 `_get_pipeline()` 中自動背景訓練 | 接線至啟動（背景執行緒 + 權重檢查） |
| T7 | 觸發 ContinuousMultimodalLearning（自主微訓練） | ✅ **DONE** (commit `HEAD~`, Jun 28) | P2 | 低 | CML 現在透過 `_encode_impl()` 自動觸發，且共用生產管線 | 每次編碼後自動微訓練 |

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
| O2 | 清理測試中 dead/commented 程式碼 | P4 |
| O3 | 標準化 imports（isort 跨所有 Python 檔案） | ✅ **DONE** (isort 8.0.1, profile=black, 738 files: 2908 insertions/2100 deletions) | P4 |
| O4 | 清理 docs/ 中過時/重複文件（移入 09-archive/） | ✅ **DONE** (2026-06-28): 7 files archived: PROJECT_ROADMAP, RECOMMENDATIONS, TODO_ANALYSIS, UNIFIED_AI_IMPROVEMENT_PLAN, ACTION_PLAN, DOCUMENTATION_TRUTH_MAP, port_routing_plan. 3 kept: VERSION_CONTROL_STRATEGY, PROJECTS_COLLABORATION_GUIDE, GIT_AND_PROJECT_MANAGEMENT. | P3 |
| O5 | 更新 INDEX.md 和 UNIFIED_DOCUMENTATION_INDEX.md 以反映文件變動 | ✅ **DONE** (INDEX.md already correct; UNIFIED_DOCUMENTATION_INDEX.md was itself archived to 09-archive/; README.md links updated to point to archive) | P3 |
| O6 | 為每個主要子系統建立統一的 `__init__.py`（公開 API） | ✅ **DONE** (2026-06-28): 8 `__init__.py` files updated: `ai/core/` created (19 exports), `ai/ed3n/` docstring added (20 exports), `ai/meta/` docstring added (3 exports), `ai/reasoning/` docstring added (DEPRECATED), `core/bio/` `__all__` added (58 exports across 24 modules), `core/perception/` created (16 exports), `core/managers/` created (10 exports). 3 previous O6 files from earlier: `ai/memory/`, `ai/memory/ham_memory/`, `services/`, `services/api/` — total 12 files. Remaining gaps: `ai/context/` (already has both), `ai/garden/` (already has both), `ai/alignment/` (already has both), `ai/response/` (already has both), `ai/lifecycle/` (already has both), `ai/agents/` (already has both), `ai/multimodal/` (already has both), `core/` (already has both). | P4 |

---

## 3. 優先級與依賴關係

### 階段 0 — 立即（1-2 天）
修正文件錯誤 ✅（已完成）+ 訓練 VisualDecoder/SequenceGenerator

```
F3 → (完成) → O5 → O4
T1, T3 → T4 (GVV 管線依賴 SequenceGenerator)
U2, U3 → T2 (torch 用於語意編碼訓練)
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
T5 → ThreeLayerVisual 自動 PCA 訓練
I2, I3 → 效能最佳化
L6 → 跨語言學習
U4 → LLM API 更新
O1, O2, O6 → 程式碼組織
```

---

## 4. 驗證標準

### 4.1 測試覆蓋

```bash
# 執行所有測試（基線：4,785）
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
