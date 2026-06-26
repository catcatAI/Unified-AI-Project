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
| **ED3N 數學準確率** | `math_eval` 階段測試數字運算 | 92 測試（ED3N 總測試） | ✅ 77.7%（基本算術） |
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
| **CLP（持續學習）** | ED3NTrainer 已接線至聊天管線 | 整合測試 | ✅ 已接線，字典成長有效 |
| **測試數量** | pytest 收集 | 4,774 測試 | ✅ 41 skipped，0 errors |

### 1.2 無法驗證的優勢（數據不足）

| 宣稱 | 實際狀態 | 需要什麼數據 | 門檻 |
|------|---------|------------|------|
| ED3N 知識理解 | 只有數學準確率（77.7%）被測量 | 建立跨領域基準：MMLU 子集、知識問答、創造性寫作 | 每領域 100+ 測試題 |
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
| **TaskGenerator 佔位符** | MEDIUM | generate_tasks() 回傳單一寫死 dict | 22L 無用 |
| **AdversarialGenerationSystem 佔位符** | MEDIUM | 附加 "[adversarial variant]" 字串 | 18L 字串操作 |
| **CausalReasoningEngine 僅 Pearson** | MEDIUM | 99L，無時間因果、無混淆變數、無 do-calculus | 99L 骨架 |
| **FullTrainingPipeline 從未觸發** | MEDIUM | 383L 訓練管線存在但零個呼叫者 | 383L 無作用程式碼 |
| **ContinuousMultimodalLearning 從未觸發** | MEDIUM | 329L 自訓練存在但零個呼叫者 | 329L 無作用程式碼 |
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
| F1 | 修正 ED3N 數學評估中 >100L 的長函數 | `ed3n_engine.py` | P4 | 中 |
| F2 | 修正 ModelBus 路由中的 >100L 長函數 | `model_bus.py` | P4 | 中 |
| F3 | 修正所有文件中的錯誤分數（已完成） | 多個 MD | P0 | 低 |
| F4 | 修正 LLM 路由中缺少 timeouts/retries | ✅ **DONE** (commit `dcd7044e1~`, Jun 28) | `router.py` | P2 | 低 |
| F5 | NeuroAutoSelector LearnRecorder 連接至 MetaController | ✅ **DONE** (commit `44fec2abb~`, Jun 28) | `neuro_auto_selector.py:764-773` + `router.py:464-470` |

### 2.2 修復 (Repairs)

| # | 項目 | 檔案 | 優先級 | 難度 |
|---|------|------|:------:|:----:|
| R1 | 實作 CerebellumEngine — 真實本體感覺/姿勢內插 | `core/bio/cerebellum_engine.py` (27L) | P3 | 高 |
| R2 | 實作 AttentionController — 顯著性計算、IOR、掃描路徑 | `core/perception/attention_controller.py` (33L) | P3 | 高 |
| R3 | 實作 PerceptionEngine — 真實融合、模糊度解析 | `core/perception/perception_engine.py` (100L) | P3 | 高 |
| R4 | 實作 TaskGenerator — 真實任務預測/分解 | `ai/memory/task_generator.py` (22L) | P4 | 中 |
| R5 | 實作 AdversarialGenerationSystem — 真實對抗訓練 | `ai/alignment/adversarial_generation_system.py` (18L) | P4 | 高 |
| R6 | 移除 AuditoryAttention（空別名）或實作 | `core/perception/auditory_attention.py` (20L) | P3 | 低 |

### 2.3 更新 (Updates)

| # | 項目 | 優先級 | 說明 |
|---|------|:------:|------|
| U1 | 安裝 faster-whisper 以啟用高品質離線 STT | P2 | 目前用 SpeechRecognition (sr) 降級 |
| U2 | 安裝 torch + transformers 以啟用 CLIP 語意編碼器 | P2 | SemanticVisualEncoder 降級至 np.random.randn |
| U3 | 安裝 torch + openai-whisper 以啟用語意音訊編碼 | P2 | SemanticAudioEncoder 降級至 MFCC 統計 |
| U4 | 更新 LLM API 用戶端至最新版本 | P3 | openai>=1.0, anthropic>=0.30, google-genai |
| U5 | 更新相依性以修復 Dependabot 漏洞（141 個） | P2 | 3 critical, 72 high, 55 moderate, 11 low |

### 2.4 迭代 (Iterations)

| # | 項目 | 優先級 | 難度 | 目前 | 目標 |
|---|------|:------:|:----:|:----:|:----:|
| I1 | 改善 NeuroAutoSelector 後端選擇（連接至 MetaController） | P2 | 低 | 啟發式 | 適應性、數據驅動 |
| I2 | 改善 ED3N 字典編碼快取（LRU 取代基本逐出） | ✅ **DONE** (commit `b233361b1~`, Jun 28) | P3 | 低 | 基本逐出 | LRU |
| I3 | 改善 GARDEN SNN 前向傳傳傳傳傳播效率 | P3 | 中 | 稠密矩陣 | 稀疏計算 |
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
| T6 | 觸發 FullTrainingPipeline（對比預訓練 + 重建微調） | P2 | 低 | 383L 有 0 呼叫者 | 接線至啟動/計時器/API |
| T7 | 觸發 ContinuousMultimodalLearning（自主微訓練） | P2 | 低 | 329L 有 0 呼叫者 | 接線至多模態服務 |

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
| L1 | ED3NTrainer → SequenceTrainer/JointTrainer 接線（目前僅使用 ED3NTrainer 基本類別） | P2 | 中 | 僅使用基本 train_step | 3 個 trainer 子類別全部使用 |
| L2 | ED3N 引擎獨立使用時，CLP 自動建立 trainer | ✅ **DONE** (commit `5e537bd86`, Jun 28) | P2 | 低 | standalone CLP 跳過梯度步驟，trainer=None | 自動建構 ED3NTrainer |
| L3 | CML 品質趨勢 → 改善觸發器（改善/穩定/退化） | P3 | 低 | 僅記錄趨勢 | 根據趨勢動態調整觸發 |
| L4 | NeuroAutoSelector LearnRecorder 資料 → 適應性選擇 | P2 | 低 | 記錄但從不使用 | 選擇隨時間改善 |
| L5 | 公式回饋迴路 — 公式影響→情緒→回應 | P2 | 中 | 67 測試但影響未經驗證 | 量化的行為影響 |
| L6 | 跨語言學習 — 從一個語言的互動改善其他語言 | P3 | 高 | 所有語言獨立 | 知識跨語言共享 |

### 2.7 整理 (Organization)

| # | 項目 | 優先級 |
|---|------|:------:|
| O1 | 檔案頭部移除 Matrix 註解（157 檔案需處理，僅裝飾性） | P5 |
| O2 | 清理測試中 dead/commented 程式碼 | P4 |
| O3 | 標準化 imports（isort 跨所有 Python 檔案） | P4 |
| O4 | 清理 docs/ 中過時/重複文件（移入 09-archive/） | P3 |
| O5 | 更新 INDEX.md 和 UNIFIED_DOCUMENTATION_INDEX.md 以反映文件變動 | P3 |
| O6 | 為每個主要子系統建立統一的 `__init__.py`（公開 API） | P4 |

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
# 執行所有測試（基線：4,774）
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
