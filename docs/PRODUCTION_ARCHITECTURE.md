# Unified AI Project - 生產環境架構指南

## 架構演進說明 (2026-01-25 更新)

> [!IMPORTANT]
> **架構轉型**: 本專案已從 Ray 分佈式架構轉向 **Local Async (本地異步)** 架構，以提升 Windows 環境穩定性與降低硬體門檻。這是一個有意識的設計決策，旨在實現「低資源 AGI」的核心目標。

### 為何放棄 Ray？

**原因**:
1. **Windows 兼容性問題**: Ray worker 進程無法正確繼承 `PYTHONPATH`，導致模組導入失敗。
2. **資源開銷**: Ray 需要額外的進程管理開銷，不符合「低硬體門檻」理念。
3. **部署複雜度**: 單機部署時 Ray 的分佈式特性成為負擔而非優勢。

**新架構優勢**:
- ✅ 跨平台穩定性（Windows/Linux/macOS）
- ✅ 低資源消耗（可在 4GB VRAM GPU 上運行）
- ✅ 簡化部署（單一 Python 進程）
- ✅ 更快的開發迭代週期

## 當前架構：Local Async (本地異步)

### 核心設計

```
┌─────────────────────────────────────────────────────────────┐
│                 Local Async 架構層次                         │
├─────────────────────────────────────────────────────────────┤
│  Layer 7: 認知層 (Cognition)                                │
│           - CognitiveOrchestrator (Local Class)             │
├─────────────────────────────────────────────────────────────┤
│  Layer 6: 記憶層 (Memory) - HAM                             │
│           - HAMMemoryManager + VectorStore (ChromaDB)       │
├─────────────────────────────────────────────────────────────┤
│  Layer 5: 學習層 (Learning)                                 │
│           - ExperienceReplay (Local Buffer)                 │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: 感知層 (Perception)                               │
│           - MultimodalBridge (Planned)                      │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: 行動層 (Action)                                   │
│           - ToolExecutor (Local Async)                      │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: 治理層 (Governance)                               │
│           - LinguisticImmuneSystem (Local LLM)              │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: 基礎設施層 (Infrastructure)                       │
│           - FastAPI + asyncio (Single Process)              │
└─────────────────────────────────────────────────────────────┘
```

### 資源管理

**Sleep Mode (閒置卸載)**:
- HybridBrain 追蹤最後互動時間
- 閒置 10 分鐘後自動卸載 Ollama 模型
- 釋放 VRAM/RAM 供其他應用使用

**ResourceMonitor**:
- 實時追蹤系統 RAM 與 NVIDIA VRAM
- 5 秒輪詢間隔
- 通過 `/api/v1/system/resources` 暴露給前端

## 數據生命週期

```
數據生命週期管理 (Data Lifecycle Management)

┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐
│  收集  │──▶│  處理  │──▶│  存儲  │──▶│  分析  │──▶│  備份  │
│Ingest  │   │Process │   │ Store  │   │Analyze │   │ Backup │
└────────┘   └────────┘   └────────┘   └────────┘   └────────┘
     │            │            │            │            │
     ▼            ▼            ▼            ▼            ▼
  Drive API   HAM Memory   SQLite +    HybridBrain   Google
  Sync        Manager      ChromaDB    Analyzer      Drive
```

## 穩定運行配置

### 生產環境變數

```bash
# .env.production
ARCHITECTURE_MODE=local_async
OLLAMA_BASE_URL=http://localhost:11434
GEMINI_API_KEY=your_api_key_here
DATABASE_PATH=apps/backend/data/economy.db
```

### 監控配置

```python
# 系統健康檢查端點
GET /api/v1/health              # 基礎健康
GET /api/v1/system/status       # 完整狀態
GET /api/v1/system/resources    # 硬體資源 (RAM/VRAM)
GET /api/v1/drive/backup/stats  # 備份狀態
 
## 概念對齊與實作對照
本文段落對照文檔中的概念設計與實際代碼的實作狀態：
- Local Async 架構已成為現實實作，Ray 分佈式架構已廢棄。
- HAMMemoryManager + VectorStore (ChromaDB) 已落地，記憶與向量儲存具持久化能力。
- Cognitive Orchestrator 作為核心認知循環的本地實作，與其他模組協同工作。
- Google Drive 整合已穩定，包含自動 token 管理與備份分析工作流。
- Linguistic Immune System 與治理機制（VDAF）已落地，提供風險評估與內容治理框架。
- Alpha Deep Model、Fragmenta Vision、Causal Reasoning Engine 等仍為概念層，尚未全面實作。
```

## 快速開始

### Windows/Linux 開發 (推薦)

```powershell
# 終端 1: 啟動後端
cd apps/backend
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS
uvicorn main:app --host 0.0.0.0 --port 8000

# 終端 2: 啟動前端
cd apps/frontend-dashboard
npm run dev

# 初始化系統
curl -X POST http://localhost:8000/api/v1/admin/initialize
```

### Docker 部署 (可選)

```bash
# Dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install -r apps/backend/requirements.txt

EXPOSE 8000 3000

CMD ["uvicorn", "apps.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# 運行 Docker
docker build -t unified-ai .
docker run -p 8000:8000 -p 3000:3000 unified-ai
```

## 結論

| 環境 | 推薦方案 | 狀態 |
|------|---------|------|
| Windows 開發 | Local Async | ✅ 穩定 |
| Linux 開發 | Local Async | ✅ 穩定 |
| macOS 開發 | Local Async | ✅ 穩定 |
| Docker 生產 | Local Async | ✅ 推薦 |
| ~~Ray 分佈式~~ | ~~已廢棄~~ | ❌ 不支援 |

**建議**: 
- 所有環境統一使用 Local Async 架構
- 通過 Sleep Mode 與 ResourceMonitor 優化資源使用
- 使用 Google Drive 自動備份確保數據安全
- 未來如需橫向擴展，考慮微服務架構而非 Ray
