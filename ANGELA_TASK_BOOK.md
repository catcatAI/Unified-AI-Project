# Angela [N+N] 任務書 (Task Book) - v2.9 (Spatial-Intent SYNC)

> **🛡️ 自癒與對齊條款 (Self-Healing Clause)**:
> 本任務書 v2.9 代表了專案在 2026-05-09 的最終校準狀態。任何後續任務必須基於此基準點。

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
*   **[Repair] 統一集成**: 修復 `DialogueManager` 引用斷路，對接 `ai-dashboard` 真實 API。 (已完成於 v2.8)

-----

### [Task N.20] 座標系 AI 增強實作 (Coordinate-Based AI)
*   **[N.20.1] 基礎座標張量協議**: 在 `state_matrix.py` 中引入 `VectorFieldComputation` 與座標維度。 (已完成)
*   **[N.20.2] 模態閘控控制邏輯**: 在 `digital_life_integrator.py` 實作動態資源開關。 (已完成)
*   **[N.20.3] 具身感官與 Live2D 對齊**: 實作 `physiological_tactile.py` 與 `live2d_integration.py` 的座標同步。 (已完成)
*   **[N.20.4] 空間定址記憶系統**: 實作 `memory_neuroplasticity_bridge.py` 的空間錨定記憶。 (已完成)
*   **[N.20.5] 原生空間推理 (幾何數學)**: 在 `state_matrix.py` 實作基於張量變換的幾何運算邏輯（含 Shunting-yard 算法與 RPN 執行器）。 (已完成)

### [Task N.21] 原生意圖模型 (Native Intent Model)
*   **[N.21.3] 意圖重力吸引 (Intent Gravity Pull)**: 在 `state_matrix.py` 實作 `apply_intent_gravity`，將維度座標緩緩吸向意圖向量。 (已完成)
*   **[N.21.7] 維度連動拖拽 (Inter-Dimensional Drag)**: 在 `state_matrix.py` 實作 `apply_inter_dimensional_drag`，觸發維度對其他維度的拖拽效應。 (已完成)
*   **[N.21.x] 意圖一致性校驗 (Intent Alignment)**: 在 `self_introspector.py` 實作 `check_intent_alignment`，偵測 LLM 行動提案與生理意圖的認知失調。 (已完成)
*   **[N.21.x] 自主意圖生成 (Homeostatic Intents)**: 在 `intent_model.py` 實作 `generate_homeostatic_intents`，依生理狀態自主生成意圖。 (已完成)

### [Task N.20.4+] 空間記憶增強
*   **[N.20.4b] 空間錨定記憶**: 在 `memory_neuroplasticity_bridge.py` 實作 `retrieve_by_spatial_proximity`，基於 3D 座標半徑檢索記憶。 (已完成)

### [Task N.22] 原生 AI 邏輯取代 (Native Coordinate AI)
*   **[N.22.1] 藝術工作流佔位符補完**: 在 `art_learning_workflow.py` 實作 Power Law 技能評估與 AL 衰減學習。 (已完成)
*   **[N.22.2] 生理張力成功率**: 在 `action_executor.py` 移除假隨機，改由 α 維度座標張量計算真實動作成功率。 (已完成)
*   **[N.22.3] 空間成熟度計算**: 在 `digital_life_integrator.py` 移除時間閾值，改以 4D 穩定性向量綜合出空間成熟度。 (已完成)
*   **[N.22.4] 生理週期行為補完**: 實作 GROWING 狀態的學習強化與 MATURE 狀態的公式驅動。 (已完成)
*   **[N.22.5] 空間美學推斷**: 在 `art_learning_system.py` 移除硬編碼顏色對應表，將 γ 維度情緒投影至 RGB 空間，並實作引力反饋 (Gravity Pull)。 (已完成)
*   **[N.22.6] 自我內省趨勢追蹤**: 在 `self_introspector.py` 加入歷史趨勢判斷與 AL 自適應失調閾值。 (已完成)

-----

## 📅 專案現狀 (Current Status)
✅ **所有前置任務已完成且通過物理對齊檢查。**
✅ **專案已達到 v2.9 的空間意圖演化基準。**
🔄 **[N.21] 意圖模型核心邏輯實作中（`intent_model.py` + `self_introspector.py`）。**

