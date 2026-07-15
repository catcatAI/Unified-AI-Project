<!--
  =============================================================================
  ANGELA-MATRIX: L3 [β] [B] [L4]
  FILE_HASH: Initial
  FILE_PATH: docs/usage/SCENARIOS.zh.md
  FILE_TYPE: documentation
  PURPOSE: 使用場景 — 直接開始、先訓練、先設定
  VERSION: 1.0.0
  STATUS: active
  LANGUAGE: zh-tw
  AUDIENCE: users, developers
  LAST_MODIFIED: 2026-07-07
  =============================================================================
-->

# 使用場景

## 場景 A：直接開始（最快速）

適合想立刻看到系統運作的用戶。

```powershell
# 1. 安裝（詳見 QUICK_START.zh.md）
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e "apps/backend"          # 最快路徑：輕量層級（[standard]/[dev] 見 QUICK_START.zh.md）
npx pnpm install --no-frozen-lockfile

# 2. 啟動
python scripts/run_angela.py
```

**直接開始可獲得**：
- ED3N+GARDEN 推論（不需外部 LLM）
- 情緒系統生效
- 記憶/向量儲存運作
- 聊天 API 在 `http://localhost:8000`

**無 LLM 限制**：
- 準確率約 3.0/10（有 LLM 約 6.0/10，2026-07-15 重新測量）
- 無進階推理或程式碼生成
- 回應較短、較模板化

---

## 場景 B：先訓練，再開始

想獲得最佳本地推論品質的用戶。

### B1. 快速訓練（5-10 分鐘）

```powershell
# 訓練 ED3N 文字編碼器 + GARDEN SNN
python scripts/train_pipeline.py --quick

# 驗證訓練權重
python scripts/verify_training.py
```

訓練內容：
- **ED3N**：Reflex + SNN + Decode 循環（約 500 步）
- **GARDEN**：Hebbian 學習收斂（約 200 步）
- **JointTrainer**：跨模態對齊

### B2. 完整訓練（30-60 分鐘）

```powershell
# 階段 0：視覺/音訊編碼器投影
python scripts/train_visual_decoder.py --texture-steps 500

# 階段 1-2：對比 + 重構學習
python scripts/train_multimodal_real.py

# 階段 3-5：完整管線（8 階段）
python scripts/train_pipeline.py --all-phases
```

### B3. 驗證訓練結果

```powershell
# 檢查權重是否存在
python -c "import numpy as np; data=np.load('data/multimodal/weights/p29_trained.npz'); print(list(data.keys()))"
# 預期輸出：7 個 ED3N + 8 個 JointTrainer = 15 個權重陣列
```

### B4. 預期品質提升

| 指標 | 未訓練 | 快速訓練 | 完整訓練 |
|------|--------|----------|----------|
| ED3N 文字準確率 | 0.60 | ~0.80 | ~0.91 |
| GARDEN SNN | 0.50 | ~0.65 | ~0.70 |
| SSIM | 0.85 | 0.90 | 0.95+ |

> **注意**：ED3N 準確率 (0.91) 為訓練集準確率，真實環境可能因分佈偏移而較低。

---

## 場景 C：先設定，再開始

### C1. LLM 提供者設定

系統支援 9 種 LLM 後端。在 `.env` 中設定至少一個：

```ini
# --- OpenAI（最佳品質） ---
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# --- Anthropic ---
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-20260514

# --- Ollama（本地，免費） ---
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3

# --- 其他後端 ---
# GOOGLE_API_KEY=...
# AZURE_OPENAI_KEY=...
# DEEPSEEK_API_KEY=...
# GROK_API_KEY=...
# XAI_API_KEY=...
# CUSTOM_LLM_ENDPOINT=...
```

後端優先順序（可透過 `LLM_PRIORITY_ORDER` 環境變數設定）：
1. OpenAI → Anthropic → Ollama → Google → Azure → DeepSeek → Grok → xAI → Custom

### C2. 硬體設定檔

```ini
# 自動偵測（desktop/laptop/power-saver/low-power/server）
# 可手動覆蓋：
HARDWARE_SCENARIO=SERVER_CLOUD
```

各設定檔效果：

| 設定檔 | 決策間隔 | 心跳 | 神經可塑性 | 適用場景 |
|--------|:--------:|:----:|:----------:|----------|
| HIGH_PERFORMANCE_DESKTOP | 60s | 5-30s | 60s | 開發/遊戲 PC |
| LAPTOP_NORMAL | 120s | 10-60s | 120s | 日常筆電 |
| LAPTOP_POWER_SAVER | 300s | 30-120s | 300s | 省電模式 |
| LOW_POWER_DEVICE | 600s | 60-300s | 600s | Raspberry Pi |
| SERVER_CLOUD | 30s | 1-10s | 30s | 雲端部署 |

### C3. 情緒系統

```ini
# 人格預設（alpha/beta/gamma/delta）
# alpha: 精力充沛、好奇、表達性強（預設）
# beta: 分析型、專注、內斂
# gamma: 溫暖、同理心強、好玩
# delta: 忠誠、保護性強、穩定
PERSONALITY_PRESET=delta

# 回饋敏感度 (0.0–1.0)
EMOTION_FEEDBACK_SENSITIVITY=0.7

# 持續負面閾值（幾次互動後情緒轉變）
EMOTION_SUSTAINED_NEGATIVE_THRESHOLD=3
```

### C4. 訓練設定

```ini
# 訓練超參數
TRAINING_LEARNING_RATE=0.001
TRAINING_BATCH_SIZE=32
TRAINING_EPOCHS=100

# 資料集路徑（預設自動下載）
TEXT_DATASET_PATH=data/datasets/text
IMAGE_DATASET_PATH=data/datasets/images

# 向量儲存
VECTOR_STORE_PATH=data/vector_store
VECTOR_STORE_BACKEND=auto  # chromadb 或 numpy+json
```

### C5. 記憶與上下文

```ini
# 記憶限制
MAX_CONTEXT_LENGTH=4096
HAM_MAX_ENTRIES=10000
VECTOR_STORE_MAX_RESULTS=20

# 會話管理
SESSION_TIMEOUT_MINUTES=30
```

### C6. 日誌與除錯

```ini
LOG_LEVEL=DEBUG      # DEBUG/INFO/WARNING/ERROR
LOG_FORMAT=detailed  # detailed 或 simple
API_LOG_BODY=true    # 記錄請求和回應內文
```

---

## 場景 D：不使用 LLM

僅使用 ED3N + GARDEN（無外部 API 呼叫）。

```powershell
# 不設定任何 LLM 直接啟動
python scripts/run_angela.py
```

**可做到**：
- 任務狀態回報
- 簡單模式匹配回應
- 基本記憶操作
- 圖片處理

**無法做到**：
- 複雜推理
- 多輪規劃
- 知識整合
- 程式碼生成

---

## 場景 E：Docker 部署

> Docker 支援為實驗性功能。後端可在容器中運行，但 GPU 加速需額外設定。

```powershell
# 建立映像檔
docker build -t angela-ai -f apps/backend/Dockerfile .

# 運行（僅 CPU）
docker run -p 8000:8000 -v ${PWD}/data:/app/data angela-ai

# 運行（GPU 搭配 Ollama sidecar）
docker run -p 8000:8000 --gpus all -e OLLAMA_HOST=http://ollama:11434 angela-ai
```

---

## 選擇你的場景

| 你的目標 | 推薦路徑 | 時間 |
|----------|---------|------|
| 「先看看能不能跑」 | **場景 A** → 直接開始 | 5 分鐘 |
| 「最佳本地品質」 | **場景 B** → 先訓練（快速） | 15 分鐘 |
| 「生產品質」 | **場景 B** → 完整訓練 + **C1**（LLM） | 45 分鐘 |
| 「自訂部署」 | **場景 C** → 先設定 + **A** → 啟動 | 10 分鐘 |
| 「無網路/API 金鑰」 | **場景 D** → 無 LLM | 5 分鐘 |
| 「伺服器部署」 | **場景 C2** → 伺服器設定檔 + **E** → Docker | 20 分鐘 |

## 相關文件

- [快速開始](QUICK_START.zh.md) — 基本安裝
- [ACTIVE_SCRIPTS.md](../scripts/ACTIVE_SCRIPTS.md) — 命令參考
- [MASTER_TASK_MAP.md](../06-project-management/MASTER_TASK_MAP.md) — 開發路線圖
