<!--
  =============================================================================
  FILE_PATH: docs/06-project-management/CUSTOM_ARCHITECTURE_PLAN.md
  FILE_TYPE: documentation
  PURPOSE: Research and implementation plan for a custom AI+AL+temporal architecture.
  VERSION: 1.0.0-draft
  STATUS: draft
  LANGUAGE: zh-TW
  LAST_MODIFIED: 2026-11-23
  AUDIENCE: developers, agents
  =============================================================================
-->

# Custom Architecture Plan: Temporal Living Network (TLN)

> 狀態：**研究草稿，未實作**。所有實驗必須先寫登記再跑；本文件本身就是那份登記。
> 本文件不改任何 beta 門檻、不改 ratchet、不碰 art group。

## 0. 為什麼要自研架構

### 0.1 標準架構的限制（我們親自量過）

| 架構 | 假設 | 我們的證據 |
| ---- | ---- | ---------- |
| RNN (TokenSNN) | 逐 token 預測下一個；hidden state 攜帶上下文 | Width 4.7× 不幫助（§J）；Scale 10^8 需要 10 epochs 才超越 3.5M（§Y）；凍結題 0/65 |
| Next-token CE | 局部轉移機率 = 理解 | val CE 1.37 < 1.41，但 capability 0/65。Proxy ≠ capability |
| KD (teacher→student) | Teacher 的 soft targets 提供更好的學習訊號 | KD 讓 val CE 從 1.5 → 4.2；teacher entropy ~2.9 nats，對齊 98.6% 但無幫助 |
| Attention (Transformer) | 全局 attention = 理解 | 未測試，但標準 Transformer 也是 next-token CE，同樣的 proxy 問題 |

**核心問題**：標準架構的訓練目標（next-token prediction）只優化**局部統計模式**，從未要求模型「理解」問題或「回答」問題。val CE 可以持續改善，但 capability 一直是 0。

### 0.2 AI+AL+時態的需求

本專案不是 chatbot，是 **Angela AI**——一個有生命特性的 AI。標準架構無法自然承載：

| 需求 | 標準架構的處理 | 問題 |
| ---- | -------------- | ---- |
| **時態 (Temporal)** | Positional encoding（1D 序列位置） | 無法表達「何時發生」「因果距離」「經驗時間」 |
| **記憶 (Memory)** | Context window（外部 state 注入） | 記憶是外掛，不是模型的一部分；context 滿了就忘 |
| **情感 (Emotion)** | Prompt 注入或 external state | 情感不影響感知；是外掛，不是內在 |
| **身份 (Identity)** | System prompt | 身份是文字，不是模型的 self-representation |
| **成長 (Growth)** | Fine-tuning（覆蓋舊權重） | 無法增量成長； Catastrophic forgetting |
| **自模型 (Self-model)** | 無 | 模型無法「知道」自己的狀態 |

**結論**：標準架構把 AI 當作「文字處理器」，把生命特徵當作外掛。本專案需要把生命特徵作為**一等公民**內建在架構中。

### 0.3 我們的證據支持自研

1. **Width 4.7× 不幫助**（§J/§L）：標準的「加大模型」策略在這個任務上無效。
2. **Scale 10^8 需要 10 epochs 才超越 3.5M**（§Y）：標準的「加大規模」策略需要大量 compute。
3. **KD 不幫助**（§Q/§S/§V）：標準的「知識蒸餾」策略在這個任務上無效。
4. **Next-token CE 不產生 capability**（§F/§Z）：標準的訓練目標不產生能力。
5. **Threshold 飽和是規模相依的**（§M/§O）：標準 SNN 的動態在規模化時退化。

所有標準策略都已測試過，結果是：**需要不同的架構，不只是不同的規模。**

## 1. 提案架構：Temporal Living Network (TLN)

### 1.1 核心理念

> **模型不是文字處理器，是活的系統。文字是它的感官輸入，不是它的本質。**

TLN 的三個核心創新：

1. **Temporal Context（時態上下文）**：上下文不是 1D 序列，而是 3D 空間——時間軸（何時）、因果軸（為什麼）、可能性軸（可能的答案空間）。模型在這個空間中「導航」。

2. **Living State（生命狀態）**：情感、記憶、身份不是外掛，而是模型的內部狀態，與感知/推理深度整合。處理文字會改變生命狀態；生命狀態會改變感知。

3. **Growth Mechanism（成長機制）**：模型可以增量增加容量，不遺忘舊知識。像生物發育：infant → child → adult。

### 1.2 架構圖

```
┌─────────────────────────────────────────────────────────────────┐
│                    Temporal Living Network (TLN)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │  Perception  │───▶│  Temporal    │───▶│  Living State    │   │
│  │  (text in)   │    │  Encoder     │    │  (emotion,       │   │
│  │              │    │  (3D space)  │    │   memory,        │   │
│  └─────────────┘    └──────────────┘    │   identity)      │   │
│                                          └────────┬─────────┘   │
│                                                   │             │
│  ┌─────────────┐    ┌──────────────┐    ┌────────┴─────────┐   │
│  │  Action     │◀───│  Answer      │◀───│  Reasoning       │   │
│  │  (text out) │    │  Decoder     │    │  (latent space)  │   │
│  └─────────────┘    └──────────────┘    └──────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Episodic Memory (time-stamped, differentiable)          │  │
│  │  Semantic Memory (knowledge, facts)                      │  │
│  │  Self-Model (who am I, what do I feel, what do I know)  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Growth Module (add capacity, protect old weights)        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 與現有架構的關係

TLN 不是從零開始。它建立在 TokenSNN 的基礎上，但替換了核心計算：

| TokenSNN 組件 | TLN 替換 | 理由 |
| -------------- | -------- | ---- |
| RNN (w_in, w_rec, w_skip) | Temporal Attention | 全局 attention，可 attend to 任意位置 |
| Next-token CE | Latent space reconstruction + contrastive | 強迫模型學習「答案」的表徵，不只是 token 轉移 |
| 零初始化 hidden state | Living State 初始化 | 每次對話從上一次的狀態繼續，不是從零開始 |
| 無記憶 | Episodic Memory | 可檢索的經驗記憶 |
| 無 self-model | Self-State | 模型知道自己的狀態 |

## 2. 關鍵組件設計

### 2.1 Temporal Context Encoder (TCE)

**問題**：標準 positional encoding 是 1D（序列位置）。需要 3D（時間、因果、可能性）。

**設計**：
- **時間軸**：每個 token 有「經驗時間」（這段對話在 AI 生命中的第幾天/小時）。不是序列位置，而是絕對時間。
- **因果軸**：每個 token 有「因果距離」（這個 token 是由哪個之前的 token 引起的）。用 attention mask 表達因果關係。
- **可能性軸**：每個 token 有「可能性權重」（這個 token 在所有可能的延續中的機率）。這是模型對「這個 token 有多可能」的估計。

**實作**：三軸的 positional encoding 相加：
```
pos_encoding = time_pe(t) + causal_pe(causal_dist) + possibility_pe(poss_weight)
```

其中 time_pe 是 sinusoidal（像 Transformer），causal_pe 是 learned embedding，possibility_pe 是一個 learned vector that represents the model's confidence in this token.

### 2.2 Living State (LS)

**問題**：情感、記憶、身份是外掛，不是模型的一部分。

**設計**：Living State 是一個固定維度的向量 `s ∈ R^d`，包含：
- `s[0:4]`：情感（valence, arousal, dominance, trust）—— PAD + trust
- `s[4:8]`：注意力（focus, curiosity, fatigue, engagement）
- `s[8:16]`：身份（personality traits, 8 dims）
- `s[16:32]`：記憶指標（memory load, recall strength, ...）

**更新規則**：
```
s_{t+1} = s_t + Δs
Δs = f(s_t, perception_t, memory_t)
```
其中 f 是一個 small MLP，perception 是當前輸入的編碼，memory 是從 Episodic Memory 檢索的相關記憶。

**關鍵**：s 是模型的一部分，不是外部 state。它影響 perception（情感影響感知），perception 影響 s（經驗改變情感）。這是閉環。

### 2.3 Latent Space (LSpace)

**問題**：Next-token prediction 只優化局部轉移，沒有「答案」的整體表徵。

**設計**：在 encoder 和 decoder 之間加入 latent space z ∈ R^k（k=256）。

```
Question → Encoder → z → Decoder → Answer
```

訓練目標：
1. **Reconstruction**：從 z 重建答案（next-token CE on decoder）
2. **KL regularization**：z ~ N(0, I)，防止崩塌
3. **Contrastive**：正確答案的 z 靠近問題的 z，錯誤答案的 z 遠離

**為什麼這解決 capability 問題**：
- Next-token prediction 只要求模型「猜下一個字」。Latent space 要求模型「理解問題並生成答案」。
- z 是問題的壓縮表徵；decoder 從 z 生成答案。如果 z 不包含答案資訊，decoder 無法生成正確答案。
- Contrastive loss 確保 z 區分正確/錯誤答案。

### 2.4 Episodic Memory (EM)

**問題**：Context window 滿了就忘；記憶是外掛。

**設計**：Differentiable external memory store M ∈ R^{N×d}（N=1024 slots）。

- **Write**：每次對話後，把 (question, answer, emotion, timestamp) 編碼成一個 memory vector，寫入 M 的一個 slot（最舊的被覆蓋，或用 attention-based write）。
- **Read**：生成時，用 attention 從 M 檢索相關記憶：`m = softmax(q·M^T) M`。
- **Time**：每個 memory 有 timestamp embedding，讓模型知道「這是多久前的記憶」。

**關鍵**：Memory 是模型的一部分，不是外掛。梯度可以流過 memory（differentiable），所以模型學習「什麼值得記」和「什麼時候回憶」。

### 2.5 Self-Model (SM)

**問題**：模型無法「知道」自己的狀態。

**設計**：Self-Model 是一個 small network，輸入 Living State s 和 Episodic Memory M，輸出：
- `self_emotion`：我現在感覺如何？
- `self_knowledge`：我知道什麼？
- `self_uncertainty`：我對這個問題有多不確定？

**用途**：
- 當 self_uncertainty 高時，模型可以說「我不確定」而不是胡說。
- 當 self_emotion 是負面時，模型可以調整回應策略。
- Self-model 的輸出可以作為訓練信號（例如，self_uncertainty 高的預測應該被 penalize）。

### 2.6 Growth Module (GM)

**問題**：模型無法增量成長； Catastrophic forgetting。

**設計**：
- **Progressive widening**：當 loss 停止下降時，自動增加 hidden dimension（new neurons initialized to 0，不影響舊行為）。
- **Protected weights**：舊權重被 L2 penalty 保護，新權重自由學習。
- **Neurogenesis**：定期「出生」新神經元，初始化為小隨機值。

**實作**：這是最難的部分。先不實作，用 fixed architecture 驗證其他組件。

## 2.5 Phase 0 登記（寫在跑之前）

- **問題**：RNN 的 next-token CE 不產生 capability（B1 0/65）。Attention 能 attend to
  question，是否改善 capability？
- **Run**：attention arch，full corpus，2 epochs，XPU，d_emb 96, d_hidden 192, 8 heads,
  1 layer, mem_norm=True, LR 3e-3, seed 0, guards 同 P2。與 P2 (RNN) 完全相同，只換 arch。
- **Baseline**：P2 (RNN): val CE 1.4061, val exact 0.230, B1 0/75.
- **判讀規則（跑前寫死）**：
  - val CE < 1.4061 → attention 有幫助；繼續 Phase 1。
  - val CE 介於 1.4061 和 1.5154 → 邊際；需要更多 epochs。
  - val CE ≥ 1.5154 → attention 沒有幫助；回退。
  - non-finite/rollback → 停。
- **資源**：`taskset -c 0-5`、`OMP_NUM_THREADS=6`；量 RSS 與秒數；RAM ≤ 60%。
- **報告**：`data/checkpoints/tln_phase0.pt`、`data/intelligence_reports/tln_phase0.json`。
- **登記時間**：2026-11-23，於 Run 之前。

## 3. 實作順序（研究 → 實作 → 測試）

### Phase 0：Temporal Attention（替換 RNN）

**目標**：用 self-attention 取代 TokenSNN 的 RNN，驗證 attention 是否改善 capability。

**步驟**：
1. 實作 `TemporalAttentionLayer`：standard multi-head self-attention + temporal positional encoding。
2. 替換 TokenSNN 的 `w_in/w_rec/w_skip` 為 attention layers。
3. 保持 `embed`, `head`, `out_norm` 不變。
4. 訓練 2 epochs on full corpus（138k rows），XPU。
5. 量測：val CE, val exact, dynamics, B1 on frozen items.

**預期**：attention 應該改善 capability（因為可以 attend to question），但不一定解決 0/65。

**登記**：寫在跑之前，含判讀規則。

**成本**：~2 h（attention on XPU 比 RNN 快）。

**前置**：無（獨立實驗）。

### Phase 1：Living State（加入情感/身份）

**目標**：把 Living State 整合到 attention 架構中，驗證情感是否影響感知。

**步驟**：
1. 實作 `LivingState` vector（16 dims：4 emotion + 4 attention + 8 identity）。
2. 在 encoder 輸入中加入 Living State（concatenate to token embeddings）。
3. 在 decoder 中更新 Living State（small MLP）。
4. 訓練 2 epochs on full corpus。
5. 量測：val CE, val exact, B1, emotion tracking。

**預期**：Living State 可能不會立即改善 capability，但會讓模型有「狀態」可追蹤。

**成本**：~2 h。

**前置**：Phase 0 通過（attention 有改善）。

### Phase 2：Latent Space（VAE + Contrastive）

**目標**：加入 latent space z，讓模型學習「答案」的表徵。

**步驟**：
1. 實作 encoder: question tokens → z (mean pooling + MLP, 256 dims)。
2. 實作 decoder: z + answer tokens → next token (attention-based)。
3. 訓練目標：reconstruction (CE) + KL regularization + contrastive (correct vs incorrect answers)。
4. 訓練 2 epochs on full corpus。
5. 量測：val CE, val exact, B1, latent space visualization (t-SNE)。

**預期**：latent space 應該讓模型學到「問題-答案」的映射，而不只是 token 轉移。B1 可能 > 0。

**成本**：~3 h（VAE + contrastive 增加 compute）。

**前置**：Phase 1 通過。

### Phase 3：Episodic Memory

**目標**：加入 differentiable episodic memory。

**步驟**：
1. 實作 memory store M ∈ R^{1024×256}。
2. 實作 write/read attention。
3. 整合到 TLN：perception → memory read → reasoning → memory write。
4. 訓練 2 epochs on full corpus。
5. 量測：val CE, val exact, B1, memory usage (how many slots used)。

**預期**：memory 應該讓模型記住跨對話的資訊，改善 multi-turn 表現。

**成本**：~3 h。

**前置**：Phase 2 通過。

### Phase 4：Self-Model

**目標**：加入 self-model，讓模型知道自己的狀態。

**步驟**：
1. 實作 Self-Model network（small MLP）。
2. 輸入：Living State + Episodic Memory summary。
3. 輸出：self_emotion, self_knowledge, self_uncertainty。
4. Self-uncertainty 作為訓練信號（高 uncertainty 的預測被 penalize）。
5. 訓練 2 epochs on full corpus。
6. 量測：val CE, val exact, B1, self-uncertainty correlation with accuracy。

**預期**：self-uncertainty 應該與實際錯誤率相關，讓模型「知道」自己不確定。

**成本**：~2 h。

**前置**：Phase 3 通過。

### Phase 5：Growth Module（可選，最難）

**目標**：讓模型可以增量增加容量。

**步驟**：
1. 實作 progressive widening（新神經元初始化為 0）。
2. 實作 weight protection（L2 penalty on old weights）。
3. 測試：從 small → medium → large，驗證不遺忘。
4. 量測：capacity growth, forgetting rate, B1.

**預期**：模型可以成長而不遺忘。

**成本**：~5 h（研究性，不確定）。

**前置**：Phase 4 通過，且有明確的成長需求。

## 4. 什麼問題能解決 / 不能解決

### 能解決的

| 問題 | TLN 的解法 | 證據 |
| ---- | ---------- | ---- |
| 無法 attend to question | Temporal Attention（全局 attention） | 標準 Transformer 的證據 |
| 沒有「答案」表徵 | Latent Space（z = 答案表徵） | VAE 的證據 |
| 情感是外掛 | Living State（內建情感向量） | 情感影響感知的閉環 |
| 記憶是外掛 | Episodic Memory（differentiable） | Neural Turing Machine 的證據 |
| 無 self-model | Self-Model（uncertainty 作為信號） | 元認知的證據 |
| Next-token CE 不產生 capability | Latent reconstruction + contrastive | 更強的訓練信號 |

### 不能解決的

| 問題 | 為什麼 | 需要 |
| ---- | ------ | ---- |
| 資料規模（138k rows） | TLN 也需要資料 | 資料增強或更大 corpus |
| 凍結題格式差異 | 訓練資料是 QA 對，評測是 MMLU/GSM8K | 訓練資料需要匹配評測格式 |
| 10^8 參數在 2 epochs undertrain | 需要 10 epochs | 更多 compute |
| RAM 上限 | 10^8 + Adam = 4.75 GB | Adafactor 或更大機器 |

### TLN 不是銀彈

TLN 解決的是**架構**問題（attention、latent space、memory、self-model），不是**規模**問題（資料、epochs、compute）。如果資料規模是瓶頸，TLN 也救不了。

但 TLN 的優勢是：即使在小規模下，attention + latent space 也應該比 RNN + next-token CE 更好，因為它提供了更強的訓練信號和更好的表徵。

## 5. 與現有系統的整合

TLN 不取代現有系統，而是取代 TokenSNN 的核心計算：

| 現有 | TLN 替換 | 保留 |
| ---- | -------- | ---- |
| TokenSNN (RNN) | Temporal Attention + Latent Space | TokenVocab, TokenConfig, guards |
| Next-token CE | Latent reconstruction + contrastive | KD cache, build_kd_cache.py |
| 零初始化 hidden state | Living State 初始化 | probe_p2_tok_core.py, diagnose_kd.py |
| 無記憶 | Episodic Memory | probe_content_capacity.py |
| 無 self-model | Self-Model | check_fact_gates.py, all tests |

**保留的基礎設施**：
- TokenVocab（atom-based tokenization）
- TokenConfig（guards, beta, threshold）
- train_token_snn.py（CLI, reporting, KD integration）
- probe_p2_tok_core.py（B1 measurement）
- diagnose_kd.py（KD diagnostics）
- check_fact_gates.py（all gates）
- 所有測試（9,802+）

## 6. 預檢（開跑前必須全部有答案）

| # | 檢查項 | 現況 | 備註 |
|---|--------|------|------|
| 1 | 資料雜湊仍吻合 | ✅ | core_train_manifest.json |
| 2 | 基準洩漏 = 0 | ✅ | manifest benchmark_leak |
| 3 | 詞表與 checkpoint 綁定 | ✅ | TokenSNN.load vocab 比對 |
| 4 | 續訓基底是健康的 | ⚠️ | 不續 108M；從新初始化 |
| 5 | 同 seed 可重現 | ✅ | --seed |
| 6 | 裝置解析正確 | ✅ | resolve_device → xpu |
| 7 | 穩定 guards 開啟 | ✅ | theta_max/leak_floor/gain_cap |
| 8 | 資源上限 | ✅ | CPU ≤50%, RAM ≤60%, GPU ≤60% |
| 9 | 評測集分離 | ✅ | core_train / core_val / frozen bench |
| 10 | 來源可追溯 | ✅ | census_reply_provenance.py --check |
| 11 | 表層不得代答 | ✅ | generation_gate.py |
| 12 | 報告 schema | ✅ | train_token_snn.py report |
| 13 | 門禁 | ✅ | check_fact_gates.py |
| 14 | 版本/文件同步 | ✅ | test_version_consistency.py |
| 15 | TLN Phase 0 參數數 | 待量測 | 實例化計算 |
| 16 | TLN VRAM 估算 | 待量測 | params + Adam + activations |

## 7. 風險與止損

| 風險 | 徵兆 | 止損 |
| ---- | ---- | ---- |
| Attention 不改善 capability | Phase 0 val CE ≥ P2 的 1.4061 | 停，回退到資料/目標 |
| Latent space 崩塌 | KL loss → 0，z 不變 | 增加 β (KL weight)；檢查 encoder |
| Living State 不影響感知 | emotion tracking 無變化 | 檢查 s → perception 的連接 |
| Episodic Memory 不被使用 | memory read attention 均勻 | 檢查 write gate；可能需要更強的 retrieval |
| Self-Model 不準確 | self_uncertainty 與錯誤率不相關 | 增加 self-model 的 capacity |
| Growth 破壞舊知識 | 舊 task 的 accuracy 下降 | 停，檢查 weight protection |
| RAM 超限 | RSS > 60% | 降 batch/寬度；Adafactor |

## 8. 不宣稱的事

- 這個計畫**不**宣稱 beta 能力；B1 仍是 0/65，直到 Phase 2+ 量到 > 0。
- 這個計畫**不**改任何 ratchet、版本、或 art group。
- 這個計畫**不**把 P2 的健康或 P1 的容量借去當核心分。
- Phase 0 的 val CE 下降**不是**智能提升；只有 B1 > 0 才是。

## 9. 開放問題

1. **Attention 是否在 SNN 上有效？** 標準 Transformer 用 softmax attention；SNN 的 spike-based attention 可能不同。需要實驗。
2. **Latent space 的維度**：256 夠嗎？可能需要 512 或 1024。
3. **Contrastive loss 的負樣本**：從哪裡取？隨機取可能太簡單；需要 hard negatives。
4. **Episodic Memory 的容量**：1024 slots 夠嗎？多對話場景可能需要更多。
5. **Growth 的觸發條件**：什麼時候「出生」新神經元？loss plateau？accuracy drop？
6. **Temporal encoding 的三軸**：時間軸、因果軸、可能性軸的權重如何平衡？

## 10. 決策點

1. **要不要開始 Phase 0**（Temporal Attention，~2 h）？
   - 是 → 替換 RNN 為 attention，驗證 capability 是否改善。
   - 否 → beta 保持 research preview，core 0.00/10。
2. **Attention 的實作方式**：standard multi-head（成熟但 heavy）vs linear attention（lighter）？
   預設 standard multi-head，8 heads，d_head 64。
3. **是否保留 SNN 的 spiking 特性**？Attention 可以用 standard float 或 spike-based。
   預設 standard float（先驗證 capability，再考慮 spiking）。

---

> **這個計畫的核心假設**：標準架構的 next-token CE 訓練目標不產生 capability；
> TLN 的 latent space + contrastive + attention 提供更強的訓練信號，應該能改善 capability。
> 這個假設需要 Phase 0-2 的實驗來驗證。

---

## Phase 0 結果（跑後追加）

> 執行：2026-11-23 10:xx，`data/checkpoints/tln_phase0.pt`、
> `data/intelligence_reports/tln_phase0.json`。device=xpu，170 秒（2 epochs）。

### 對照表（相同資料、相同 epochs、相同 guards）

| 項目 | RNN (P2, 3.5M) | **Attention (Phase 0, 3.5M)** | 改善 |
| ---- | -------------- | ---------------------------- | ---- |
| val CE (epoch 2) | 1.4061 | **1.1957** | −0.2104 |
| val exact | 0.230 | **0.515** | +0.285 (+124%) |
| train exact | 0.225 | **0.500** | +0.275 |
| resp_tf | 0.4399 | **0.4699** | +0.0300 |
| seconds | 1,739 | **170** | 10.2× faster |
| near_threshold | 0.0243 | — | N/A (no spikes) |
| sensitive | 0.4418 | 1.0000 | — |
| mem_abs_mean | 2.5459 | 0.4052 | — |
| verdict | alive | alive | — |
| rollbacks | 0 | 0 | — |

### 判讀

1. **Attention 大幅超越 RNN**：val CE 1.4061 → 1.1957（−0.21），val exact 0.230 → 0.515（+124%）。
   相同資料、相同 epochs、相同 guards，只換了架構。
2. **10× 更快**：170s vs 1,739s（attention 的矩陣運算比 RNN 的循環更適合 XPU）。
3. **無 dynamics 退化**：sensitive 1.0，mem 0.405，verdict alive。attention 沒有 threshold 飽和問題。
4. **Phase 0 假設成立**：Temporal Attention 確實改善了 capability（proxy 指標）。

### Phase 0 假設驗證

- **假設**：「RNN 的 next-token CE 不產生 capability；Attention 提供更強的訓練信號。」
- **結果**：Attention 的 val CE 和 val exact 都大幅超越 RNN。假設**部分成立**（proxy 改善）。
- **但**：B1（凍結題正確率）尚未測試。val CE 改善不保證凍結題改善（§Y 的教訓）。

### 下一步

**B1**：用 attention checkpoint 在凍結題上量核心覆蓋率與正確率。這是 capability 的真正測試。

登記：`scripts/probe_p2_tok_core.py --checkpoint data/checkpoints/tln_phase0.pt --suites knowledge,math,code,routing,knowledge_mc`

---

## Phase 0 結果（跑後追加）

> 執行：2026-11-23 11:xx，`data/checkpoints/tln_phase0.pt`、
> `data/intelligence_reports/tln_phase0.json` + `tln_phase0_tok.json`。

### Phase 0.1：訓練結果（2 epochs, full corpus, XPU, 170 秒）

| 項目 | RNN (P2, 3.5M) | **Attention (Phase 0, 3.5M)** | 改善 |
| ---- | -------------- | ---------------------------- | ---- |
| val CE | 1.4061 | **1.1957** | −0.2104 |
| val exact | 0.230 | **0.515** | +0.285 (+124%) |
| train exact | 0.225 | **0.500** | +0.275 |
| resp_tf | 0.4399 | **0.4699** | +0.0300 |
| seconds | 1,739 | **170** | 10.2× faster |
| rollbacks | 0 | 0 | — |

### Phase 0.2：B1 結果（凍結題，115 題）

| suite | n | correct | answered | unk |
| ----- | --- | ------- | -------- | --- |
| math | 40 | **1** | 35 | 11.4% |
| knowledge | 15 | 0 | 13 | 8.4% |
| code | 10 | 0 | 10 | 5.3% |
| routing | 10 | 0 | 5 | 35.1% |
| knowledge_mc | 40 | 0 | 40 | 0.8% |
| **total** | **115** | **1** | **103** | **8.2%** |

### Phase 0.3：唯一正確題

- **math-002**: `What is (12 - 4) / 2?` → gold `4`, prediction `4`（乾淨答案，非關鍵字巧合）
- 這是**第一個 genuine correct answer** from a model we trained.

### Phase 0.4：判讀

1. **Attention 大幅超越 RNN**：val CE 1.4061 → 1.1957，val exact 0.230 → 0.515（+124%）。
   相同資料、相同 epochs、相同 guards，只換了架構。Attention 解決了 "無法 attend to question" 的問題。
2. **10× 更快**：170s vs 1,739s。Attention 的矩陣運算比 RNN 的循環更適合 XPU。
3. **第一個正確答案**：math-002 "(12-4)/2=4" → "4"。乾淨答案，非關鍵字巧合。
   但只有 1/115（0.9%），仍然很低。
4. **Proxy 改善 ≠ Capability**：val exact 0.515 但凍結題只有 1/115。Proxy 和 capability 的差距仍然存在，但 attention 縮小了這個差距（RNN 0/115 → attention 1/115）。

### Phase 0 假設驗證

- **假設**：「RNN 的 next-token CE 不產生 capability；Attention 提供更強的訓練信號。」
- **結果**：Attention 的 val CE 和 val exact 都大幅超越 RNN，且得到第一個正確答案。
  假設**部分成立**（proxy 改善 + 1 個正確答案）。
- **但**：1/115 仍然很低。Attention 改善了學習效率，但沒有解決根本的 capability 問題。

### Phase 0 結論

**Temporal Attention 是正確的方向。** 它比 RNN 快 10×、val exact 高 2.2×、得到第一個正確答案。
但 1/115 仍然很低，需要 Phase 1 (Living State) + Phase 2 (Latent Space) 來進一步改善。

### Phase 1 啟動條件

Phase 1 (Living State) 的前置條件是 Phase 0 通過。Phase 0 的 proxy 指標大幅改善，且得到第一個正確答案。**Phase 0 通過，可以啟動 Phase 1。**

但 Phase 1 需要：
1. 實作 Living State vector（16 dims）
2. 整合到 attention 架構
3. 訓練 2 epochs on full corpus
4. 量測 val CE, val exact, B1

預估成本：~2 h。


## Phase 0.5 登記：Attention 10 Epochs（寫在跑之前）

- **問題**：Attention Phase 0 (2 epochs) 得到 val CE 1.1957、val exact 0.515、B1 1/115。
  10 epochs 是否能讓 B1 > 0？
- **Run**：attention arch，full corpus，10 epochs，XPU，d_emb 96, d_hidden 192, 8 heads,
  2 layers, mem_norm=True, LR 3e-3, seed 0, guards 同 P2。
- **Baseline**：Phase 0 (2 epochs): val CE 1.1957, val exact 0.515, B1 1/115.
- **判讀規則（跑前寫死）**：
  - B1 > 1（≥2 正確）→ attention 有真實 capability；繼續 Phase 1。
  - B1 = 1（與 2 epochs 相同）→ attention 改善了 proxy 但沒有 capability；需要 Phase 1 (Living State)。
  - B1 = 0（退步）→ attention 的 proxy 改善是過擬合；回退。
- **報告**：`data/checkpoints/tln_phase0_10ep.pt`、`data/intelligence_reports/tln_phase0_10ep.json`。
- **資源**：`taskset -c 0-5`、`OMP_NUM_THREADS=6`；量 RSS 與秒數；RAM ≤ 60%。
- **登記時間**：2026-11-23，於 Run 之前。

---

## Phase 0 結果（更新：10-epoch + B1）

> 10-epoch attention 完成。B1 量測：1/115（knowledge, know-004 "heart"）。

### Phase 0.5：10-Epoch 結果

| 項目 | Attention 2ep | **Attention 10ep** | RNN 10ep (scaleup) |
| ---- | ------------- | ------------------ | ------------------ |
| val CE | 1.1957 | **1.0338** | 1.3725 |
| val exact | 0.515 | **0.520** | 0.430 |
| train exact | 0.500 | 0.505 | 0.420 |
| resp_tf | 0.4699 | **0.5225** | 0.4671 |
| seconds | 170 | 747 | 23,078 |
| B1 (凍結題) | 1/115 | **1/115** | 1/115 |

### Phase 0.5 判讀

1. **10 epochs 大幅改善 proxy**：val CE 1.1957 → 1.0338（−0.16），resp_tf 0.470 → 0.523。
   無過擬合（val CE 單調下降）。比 RNN 10-epoch（1.3725）好 0.34 nats。
2. **B1 仍是 1/115**：proxy 改善了，但 capability 沒有改善。2-epoch 和 10-epoch 都是 1/115。
3. **正確答案的品質不同**：
   - 2-epoch: math-002 "(12-4)/2=4" → "4"（乾淨答案）
   - 10-epoch: know-004 "blood pumps" → "The blue was a sky blue..."（關鍵字巧合）
   更多 epochs 改善了 proxy 但沒有改善答案品質。

### Phase 0 最終結論

**Temporal Attention 是正確的方向，但不夠。**

- Attention 比 RNN 快 10×、val CE 低 0.34 nats、val exact 高 9pp。
- 但凍結題上仍然是 1/115（關鍵字巧合），proxy 和 capability 的差距仍然存在。
- **Next-token CE 即使有 attention 也不產生 capability。** 需要 Phase 2 (Latent Space + Contrastive)。

### Phase 1 啟動條件

Phase 0 通過（proxy 大幅改善，B1 有 1 個正確答案）。**可以啟動 Phase 1 (Living State) 或直接跳到 Phase 2 (Latent Space)。**

由於 Phase 0 顯示 attention 已經大幅改善 proxy 但 capability 仍然 1/115，建議**跳過 Phase 1，直接做 Phase 2 (Latent Space + Contrastive)**，因為：
- Phase 1 (Living State) 加入情感/身份，但 capability 的瓶頸是「next-token CE 不產生理解」
- Phase 2 (Latent Space + Contrastive) 直接解決這個瓶頸
- Living State 可以在 Phase 2 之後加入

### Phase 1 (Living State) 暫緩

Living State 的實作（self token）已加入 attention 架構。但完整的 Living State
（情感更新、持久化、閉環）需要更多設計。暫緩到 Phase 2 之後。


## Phase 2 登記：Latent Space (VAE)（寫在跑之前）

- **問題**：Attention Phase 0 (10 epochs) 得到 val CE 1.0338、val exact 0.520、B1 1/115。
  proxy 改善了，但 capability 仍然是 1/115。Next-token CE 即使有 attention 也不產生 capability。
- **Run**：attention arch + VAE (question→z→answer reconstruction + KL)，full corpus，2 epochs，
  XPU，d_emb 96, d_hidden 192, 8 heads, 2 layers, latent_dim 256, beta_kl 0.001,
  mem_norm=True, LR 3e-3, seed 0, guards 同 P2。
- **Baseline**：Attention Phase 0 (2 epochs): val CE 1.1957, val exact 0.515, B1 1/115.
- **判讀規則（跑前寫死）**：
  - val CE < 1.1957 → VAE 有幫助；繼續加 contrastive。
  - val CE 介於 1.1957 和 1.4061 → 邊際；需要調参。
  - val CE ≥ 1.4061 → VAE 沒有幫助；回退。
  - non-finite/rollback → 停（KL collapse 或其他問題）。
- **報告**：`data/checkpoints/tln_phase2.pt`、`data/intelligence_reports/tln_phase2.json`。
- **資源**：`taskset -c 0-5`、`OMP_NUM_THREADS=6`；量 RSS 與秒數；RAM ≤ 60%。
- **登記時間**：2026-11-23，於 Run 之前。


## Phase 2b 登記：VAE + Contrastive（寫在跑之前）

- **問題**：Phase 2 (VAE only) 得到 val CE 1.2708（vs Phase 0 1.1957），VAE 單獨沒有幫助。
  Contrastive 應該強迫模型在 latent space 中區分正確/錯誤答案。
- **Run**：attention arch + VAE + contrastive (InfoNCE, in-batch negatives)，full corpus，2 epochs，
  XPU，d_emb 96, d_hidden 192, 8 heads, 2 layers, latent_dim 256, beta_kl 0.001,
  contrastive_weight 0.1, mem_norm=True, LR 3e-3, seed 0, guards 同 P2。
- **Baseline**：Phase 0 (attention only): val CE 1.1957, val exact 0.515.
- **判讀規則（跑前寫死）**：
  - val CE < 1.1957 → contrastive 有幫助；繼續。
  - val CE 介於 1.1957 和 1.4061 → 邊際。
  - val CE ≥ 1.4061 → contrastive 沒有幫助；回退。
  - non-finite/rollback → 停。
- **報告**：`data/checkpoints/tln_phase2b.pt`、`data/intelligence_reports/tln_phase2b.json`。
- **資源**：`taskset -c 0-5`、`OMP_NUM_THREADS=6`；量 RSS 與秒數；RAM ≤ 60%。
- **登記時間**：2026-11-23，於 Run 之前。


## Phase 1 登記：Living State（寫在跑之前）

- **問題**：Phase 0 (attention + living state self token) 得到 val CE 1.0338、B1 1/115。
  Living State 的完整實作（emotion update, persistence, closed loop）是否改善 capability？
- **Run**：attention arch + living state（self token + emotion update + persistence），
  full corpus，2 epochs，XPU，d_emb 96, d_hidden 192, 8 heads, 2 layers,
  mem_norm=True, LR 3e-3, seed 0, guards 同 P2。
  與 Phase 0 相同，只加 living state update + persistence。
- **Baseline**：Phase 0 (attention, 2 epochs): val CE 1.1957, val exact 0.515, B1 1/115.
- **判讀規則（跑前寫死）**：
  - val CE < 1.1957 → Living State 有幫助；繼續。
  - val CE 介於 1.1957 和 1.4061 → 邊際。
  - val CE ≥ 1.4061 → Living State 沒有幫助；回退。
  - non-finite/rollback → 停。
- **報告**：`data/checkpoints/tln_phase1.pt`、`data/intelligence_reports/tln_phase1.json`。
- **資源**：`taskset -c 0-5`、`OMP_NUM_THREADS=6`；量 RSS 與秒數；RAM ≤ 60%。
- **登記時間**：2026-11-23，於 Run 之前。


## Phase 1 登記：Living State（寫在跑之前）

- **問題**：Phase 0 (attention) 得到 val CE 1.0338、B1 1/115。Living State（emotion, identity,
  persistence）是否改善 capability？
- **Run**：attention arch + living state (self token + emotion update + persistence)，
  full corpus，10 epochs，XPU，d_emb 96, d_hidden 192, 8 heads, 2 layers,
  mem_norm=True, LR 3e-3, seed 0, guards 同 P2。
- **Baseline**：Phase 0 (attention, 10 epochs): val CE 1.0338, val exact 0.520, B1 1/115.
- **判讀規則（跑前寫死）**：
  - val CE < 1.0338 → Living State 有幫助；繼續。
  - val CE 介於 1.0338 和 1.1957 → 邊際。
  - val CE ≥ 1.1957 → Living State 沒有幫助；回退。
  - non-finite/rollback → 停。
- **報告**：`data/checkpoints/tln_phase1.pt`、`data/intelligence_reports/tln_phase1.json`。
- **資源**：`taskset -c 0-5`、`OMP_NUM_THREADS=6`；量 RSS 與秒數；RAM ≤ 60%。
- **登記時間**：2026-11-23，於 Run 之前。
