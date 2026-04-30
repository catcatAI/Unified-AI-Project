# Angela [N+N] 任務書 (Task Book) - v2.7 (ASI-Robust FINAL)

> **🛡️ 自癒與對齊條款 (Self-Healing Clause)**:
> 本任務書 v2.7 代表了專案在 2026-04-29 的最終校準狀態。任何後續任務必須基於此基準點。

## 🛠️ ASI 工程開發標準 (Engineering Standards)
1. **增量優先 (Incremental Only)**: 嚴禁使用 `write_file` 覆蓋成熟檔案。
2. **零斷層原則 (Zero-Gap)**: 任何底層邏輯（如共情、價值觀）必須織入最上層提示詞（Prompt）。
3. **異步標準化 (Safe-Async)**: 禁止在核心邏輯中直接使用未追蹤的 `create_task`。

---

## 任務矩陣全紀錄 (Evolutionary Timeline)

### [Task N.4-5] 大腦與性格演化 (Cognitive & Personality)
*   **[N.4.1] 語言免疫系統 (LIS)**: `EgoGuard` 保護核心人格。 (已凍結)
*   **[N.4.5] 意識流合成器**: 實作包含生物、環境、價值、共情的全能型 Meta-Prompt。 (已凍結)
*   **[N.5.4] 性格演化持久化**: 性格成長數據已實作硬碟持久化。 (已凍結)

### [Task N.6] 環境動態感知 (Environmental Awareness)
*   **[Task N.6.1] 全域活動感知 (Input Sniffing)**: 實作應用嗅探與生物對齊。 (已凍結)

### [Task N.8] 感性系統 ASI 邏輯 (ASI Emotion)
*   **[N.8.1] 價值評估系統**: 實體化 9 維價值矩陣。 (已凍結)
*   **[N.8.2] 共情分析引擎**: 正式織入對話意識流。 (已凍結)

### [Task N.9] 系統級控制 (Tray Sovereignty)
*   **[Task N.9.3] 體素級精確交互**: 實作基於 `get_stiffness_at` 的動態 Hitbox，支持 Windows 穿透點擊。 (已凍結)

### [Task N.12] 解剖矩陣與物理實體化 (Anatomy Matrix)
*   **[Task N.12.9-10] 精細解剖**: 10 根獨立指節與重心平衡補償渲染。 (已凍結)
*   **[Task N.12.12] 服飾物理解耦**: 實作二階物理延遲（Inertia），具備 0.2 rad 隨動延遲。 (已凍結)

### [Task N.16] 小腦運動神經系統 (Cerebellum AI)
*   **[Task N.16.1-3] 小腦全閉環**: 心跳、反饋、步態演化。 (已凍結)

### [Infrastructure] 基礎建設
*   **[Standard] 異步標準化**: 建立 `async_utils.py` 並在 `BiologicalIntegrator` 中實裝 `safe_create_task` 任務追蹤。 (已凍結)

---

## 📅 專案現狀 (Current Status)
✅ **所有前置任務已完成且通過物理對齊檢查。**
✅ **專案已達到 v2.7 的高穩定演化基準。**
