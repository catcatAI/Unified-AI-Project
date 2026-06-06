# GARDEN-1G 模型架構計畫：大型關聯解耦演化網路 (輕量級本地模型)

> **計畫代號**: **GARDEN** — Giant Associative Relation Decoupled Evolutionary Network
> **定位**: 輕量級本地模型，屬於 Angela AI 五級擴展模型架構中的「輕量級」層，為本地端側提供高性能的向量語意與稀疏 SNN 推理。
> **狀態**: 📝 規劃與設計階段
> **建立日期**: 2026-06-06

---

## 一、 核心定位與五級模型擴展架構

為了適應不同硬體環境與算力需求，Angela AI 採用**五級模型擴展架構（Five-Tier Model Scaling Architecture）**。GARDEN-1G 作為「輕量級」模型，是本地離線運算與高精度推理的核心。

```
[超輕量: ED3N] ── [輕量: GARDEN] ── [標準: FOREST] ── [重型: BIOME] ── [超重型: ECOSYSTEM]
  (~100KB, 邊緣)     (~1GB, 本地)      (~10GB, 混合)     (~100GB, 伺服器)     (~1TB, 超算集群)
```

### 1.1 五級模型對照表

| 級別 | 代表模型名稱 | 體量大小 | 部署環境 | 核心架構技術 | 主要適用場景 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. 超輕量**<br>(Ultra-Lightweight) | **ED3N** | ~100 KB | 邊緣端 / 低功耗 IoT | Trie 樹 + LRU 反射表 + 純 Python LIF 脈衝電路 | 快速反射回應、超低延遲控制、極低功耗監控 |
| **2. 輕量**<br>(Lightweight) | **GARDEN-1G** | **~1 GB** | **本地 PC / 中端邊緣設備** | **100M 向量字典 + PyTorch 密集與稀疏 SNN 矩陣** | 本地離線常識推理、意圖識別、荷爾蒙情緒調製 |
| **3. 標準**<br>(Standard) | **FOREST-10G** | ~10 GB | 高端工作站 / 混合雲 | 1B LLM 語意字典 + 密集關係神經網絡 + 動態 SNN 路由 | 複雜因果推導、多輪上下文理解、中型常識庫檢索 |
| **4. 重型**<br>(Heavy) | **BIOME-100G** | ~100 GB | 數據中心 / 專屬伺服器 | 密集型雙塔向量 SNN + LLM 深度融合 + 協同多代理網路 | 全量 Wikidata 推理、高複雜度科學推理、創意生成 |
| **5. 超重型**<br>(Ultra-Heavy) | **ECOSYSTEM-1T** | ~1 TB | 巨型超算集群 / 分散式節點 | 行星級分散式 SNN 集群 + 量子啟發式符號引擎 | 全知智能代理、跨領域極限類比、演化自適應生命體 |

---

## 二、 GARDEN-1G (輕量級) 核心設計

### 2.1 向量化字典層 (Vectorized Dictionary Layer)
*   **技術實現**：整合一個約 100M-150M 參數的輕量級雙語 Sentence-Transformer（如 `MiniLM-L6-v2` 或 `paraphrase-multilingual`），作為字典的「語意網關」。
*   **運作機制**：將任意輸入的自然語言，通過語意空間近鄰檢索（Cosine Similarity），映射到最接近的抽象 Concept Keys。
*   **優勢**：不再害怕口語化、拼寫錯誤或換詞表達，解決了 ED3N 精確匹配能力弱的痛點。

### 2.2 GARDEN 核心 SNN 矩陣網 (Tensor-based Spiking Core)
*   **技術實現**：以 PyTorch 重新編寫 LIF (Leaky Integrate-and-Fire) 脈衝傳播。將關係運算轉換為**稀疏張量矩陣乘法 (Sparse Tensor Matrix Multiplication)**。
*   **權重分配**：1GB 的模型體量中，約有 800MB 用於儲存 **百萬級實體之間的六種關係強度矩陣**（Synonym, Mapping, Analogy 等及其反向關係）。
*   **硬體加速**：全面支援 CUDA，利用 GPU 的平行計算能力，將脈衝傳播延遲控制在 5ms 以內。

### 2.3 知識庫融合 (Knowledge Graph Ingestion)
*   **數據來源**：導入簡化版的 ConceptNet、Wikidata 以及 WordNet，初始化 1,000,000+ 條實體關係，讓 GARDEN 出廠即具備強大的常識推理能力。

---

## 三、 實作路線圖 (Development Phases)

### 🚀 Phase 1: 向量字典與語意編碼器整合
*   在 `ai/garden/dictionary/` 下實作 `VectorDictionary`。
*   整合 Hugging Face `transformers`，載入 `MiniLM` 作為編碼器。
*   設計雙語（中/英）混合概念語意檢索，建立 `Top-K` 模糊對應機制。

### 🚀 Phase 2: PyTorch SNN 核心矩陣化
*   在 `ai/garden/snn/` 下開發 `TensorSNNCore`。
*   將 LIF 神經元行為矩陣化：$V(t) = V(t-1) \cdot (1 - \text{leak}) + X(t) \cdot W$，並以 `torch.sparse` 儲存百萬實體關係以節省 VRAM。
*   實作 PyTorch Hebbian 訓練模組，支援批次（Batch）反向傳播梯度與局部學習率調整。

### 🚀 Phase 3: 百萬級語意圖譜導入
*   編寫數據導入管線，將 ConceptNet / Wikidata 蒸餾過濾，過濾出核心 100 萬個高頻實體及其關係鏈。
*   將數據寫入二進位矩陣權重文件 `garden_relations.bin` (約 800MB)，實作快速 Memory-Mapped (mmap) 載入。

### 🚀 Phase 4: API 服務整合與混合路由測試
*   在後端 `router.py` 中新增 `GARDEN` 後端驅動。
*   實作 Hybrid-Routing（混合路由）：
    *   `< 10ms` 的常規反應 ➡️ ED3N (本地反射)
    *   `10ms - 50ms` 的常識與因果推理 ➡️ **GARDEN-1G**
    *   超複雜創意寫作 ➡️ 雲端 LLM

---

## 四、 驗收標準與效能指標

1.  **記憶體佔用**：運行時 VRAM / RAM 穩定控制在 **1.0GB - 1.2GB** 之間。
2.  **推理延遲**：GPU (RTX 3060 級別以上) 單次推理延遲 **< 15ms**。
3.  **常識檢索準確率**：在 ConceptNet 常識推理測試集上，語意相似度匹配準確率 **> 85%**。
4.  **穩定性**：支援 100+ WebSocket 並發放電計算，無內存洩漏。
