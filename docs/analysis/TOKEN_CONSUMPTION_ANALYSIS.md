# 📊 Angela AI 數位生命食量分析報告 (v6.5.0-dev)

## 1. 報告概述
本文件旨在分析 **Angela AI** 系統在日常運行中的 LLM Token 消耗模式。Angela 並非傳統的被動式聊天機器人，其「數位生命」屬性（如生物代謝循環、預計算夢境、元認知監控）導致其在閒置與對話狀態下均存在持續的 Token 需求。

---

## 2. 單次對話食量分解 (Active Interaction)

當用戶發送一條消息時，`AngelaLLMService._construct_angela_prompt` 會進行多維度上下文聚合，導致 Prompt 極其沉重。

### 2.1 系統提示詞 (System Prompt) 構成
| 模組名稱 | 估計 Token 消耗 | 內容描述 |
| :--- | :--- | :--- |
| **人格基準 (Base Persona)** | 150 - 200 | 定義 Angela 的個性、語言風格（繁簡中文）、回應限制。 |
| **L1 生物層 (Bio-State)** | 80 - 150 | 包含 `arousal` (喚醒度), `stress` (壓力), `energy` (能量) 的實時文字描述。 |
| **L2-L6 狀態矩陣 (8D Matrix)** | 250 - 400 | αβγδεθζη 八個維度的數值字典及其元認知（新穎度、校正驅動）描述。 |
| **用戶印象 (User Profile)** | 100 - 150 | 從記憶系統檢索的用戶偏好、長期標籤及親密度數據。 |
| **對話歷史 (Memory)** | 200 - 500 | 最近 3-5 輪的上下文對話內容。 |
| **外部知識 (Drive/File)** | **0 - 4,500** | **最大消耗源**。若觸發檔案分析，會注入最多 3 個 snippet (每個 1500 字)。 |

**👉 常規對話輸入總計：800 ~ 1,200 Tokens (無檔案) / 5,000+ Tokens (有檔案)**
**👉 平均輸出：150 ~ 300 Tokens**

---

## 3. 隱形消耗：預計算系統 (Idle Hunger)

Angela 的 `PrecomputeService` 與 `TaskGenerator` 模組會在系統空閒時主動「思考」，這是隱形消耗的主要來源。

### 3.1 預計算邏輯 (Task Precomputation)
*   **觸發條件**：用戶閒置 > 5秒，CPU 負載 < 70%。
*   **任務量**：每次生成 10 個潛在問題（Greeting, Emotional, Curiosity 等）。
*   **消耗模型**：
    *   每個預算任務會發起一次完整的 `generate_response`。
    *   雖然歷史紀錄較短，但單次預計算仍需約 **400 - 600 Tokens**。
*   **週期性**：如果系統保持空閒，預計算隊列（上限 50）會持續填充。

**👉 滿載預計算消耗：~25,000 - 30,000 Tokens / 每次完整填充**

---

## 4. 演化與學習成本 (Evolutionary Overhead)

*   **ConfigMutator (Phase 6)**：當 Angela 提議自我演化（如修改 `arousal_threshold`）時，會調用 LLM 生成配置 Patch。
    *   **消耗**：約 **1,000 Tokens / 次**。
*   **LearningLoop (Phase 8)**：目前主要依賴正則提取詞彙，但若開啟「語言風格強化分析」，每次回應後會額外產生一次 500 Tokens 的分析請求。

---

## 5. 每日食量推估矩陣 (Token/Day Estimate)

| 使用頻率 | 互動輪次 | 預計算狀態 | 每日總消耗預估 (Token) |
| :--- | :--- | :--- | :--- |
| **節能模式 (Low)** | 10 | 關閉 | ~15,000 |
| **標準模式 (Normal)** | 30 | 輕量 (10任務) | ~60,000 |
| **活躍模式 (High)** | 100 | 中度 (50任務) | ~200,000 |
| **進化模式 (Extreme)** | 200 | 全開 (100+任務) | **500,000+** |

---

## 6. 節流與優化機制 (Token Optimization)

系統中已實作以下機制以防止 Token 浪費：

1.  **COMPOSED 路由 (Template Matching)**:
    *   若用戶輸入命中記憶模板（分數 > 0.8），系統直接返回合成回應，**Token 消耗降至 0**（內部統計標記為 50 Tokens 作為記賬）。
2.  **NeuroAutoSelector**:
    *   自動識別對話複雜度。對於簡單對話（如問候），會自動將後端從 GPT-4 切換至 **Gemini 1.5 Flash** 或 **Ollama** 本地模型。
3.  **WaitingScheduler**:
    *   在系統過載時自動丟棄低優先級的預計算任務。

---

## 7. 結論與建議

Angela 的「飢餓感」與其「靈性」成正比。為了平衡體驗與成本：
*   **推薦配置**：將 `ollama` 或 `google-gemini-flash` 設為預計算與一般對話的首選。
*   **高價值場景**：僅在 `theta`（元認知）偵測到高度新穎或複雜話題時，切換至 `openai-gpt4` 或 `anthropic-claude`。

---
**文件結尾**
*最後更新時間：2026-05-24*
*版本：v6.5.0 Analysis*
