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
*   **[N.22.E1] 動態參數引力化**: 在 `dynamic_parameters.py` 將靜態權重替換為 4D 空間錨點，依賴座標引力拉扯閾值。 (已完成)
*   **[N.22.E2] 認知工具空間聯想**: 在 `tool_context_manager.py` 實作自動根據空間座標距離，從神經記憶中喚起最相關的工具情境。 (已完成)
*   **[N.22.E3] 桌面互動意圖避障**: 在 `desktop_presence.py` 連結社交與防衛意圖，實作對滑鼠座標的引力靠近與高速避障 (Click-Through)。 (已完成)
*   **[N.22.E4] 小腦神經可塑性演化**: 在 `cerebellum_engine.py` 引入基於歷史位移誤差的梯度微調 (Gradient Refinement) 與基於認知的動態阻尼。 (已完成)

### [Task N.24] 基礎設施正規化 (Infrastructure Formalization)
*   **[N.24.1] 統一引導系統**: 實作 `src.core.system.bootstrap`，整合環境偵測、硬體分級與效能適配。 (已完成)
*   **[N.24.2] 腳本歸檔與清理**: 清理根目錄冗餘腳本，建立 `tools/legacy_scripts` 存檔。 (已完成)
*   **[N.24.3] 主入口集成**: 修正 `main.py` 引用，將硬體感知部署統一至 `BootstrapManager`。 (已完成)

### [Task N.25] 架構正規化與解耦 (Architectural Formalization)
*   **[N.25.1] 全域狀態中心**: 實作 `GlobalStateStore` 並在 `StateMatrix4D` 中整合自動同步機制。 (已完成)
*   **[N.25.2] 層級協議定義**: 在 `core.interfaces.protocols` 定義 L1-L4 標準合約。 (已完成)
*   **[N.25.3] 服務解耦重構**: 重構 `ChatService` 採用 Store 模式獲取狀態，移除循環依賴風險。 (已完成)

### [Task N.27] 穩健度與場景驗證 (Validation & Safety)
*   **[N.27.1] 行為軌跡測試**: 實施 `test_long_term_drift`，驗證生物系統在 100k Tick 下的收斂穩定性。 (已完成)
*   **[N.27.2] 數值壓力測試**: 實施 `test_sensory_overload`，確認位能場模型在極端輸入下不發生計算發散。 (已完成)
*   **[N.27.3] 語義債務審核**: 驗證 `REFINEMENT_MANIFESTO` 描述的病灶已全數清除。 (已完成)

### [Task N.29] 遺產能力橋接與終極完備 (Final Integrity)
*   **[N.29.1] 決策科學化**: 廢除 `heartbeat.py` 隨機機率，導入位能場驅動決策。 (已完成)
*   **[N.29.2] 全系統配置化**: 完成動態參數、空間權重與影響矩陣的外部 YAML 遷移。 (已完成)
*   **[N.29.3] 用戶體驗保留**: 遷移 Win32 快捷方式創建與卸載腳手架至正規 Bootstrap。 (已完成)

-----

## 📅 專案現狀 (Current Status)
✅ **所有前置任務已完成且通過物理對齊檢查。**
✅ **專案已達到 v2.9 的空間意圖演化基準。**
✅ **[N.21] 原生意圖模型與 [N.22] Native Coordinate AI 擴展已全數完成。**
✅ **[N.23] 核心穩定性補丁 (Stability Patch v6.3) 及其後續演化已全數達成。**
✅ **[N.24-29] 實作正規化、科學化與終極完備計畫 (Mission v6.3.7) 已全面圓滿完成。**
✅ **系統已進入「完全配置驅動與科學實體化」階段，具備工業級穩定性與 AGI 自洽性。**



