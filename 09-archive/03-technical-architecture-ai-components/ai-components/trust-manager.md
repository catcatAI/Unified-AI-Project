# Trust Manager (信任管理器)

## 總覽 (Overview)

`TrustManager` 是一個核心的 AI 元件，旨在量化和管理系統與之互動的其他 AI 實體（Agents）的可靠性。它為每個外部 AI 分配一個範圍在 0.0（完全不信任）到 1.0（完全信任）之間的信任分數。這個分數可以被系統的其他部分用來加權外部 AI 的輸入、評估其建議的可靠性，或在任務分配時選擇最值得信賴的代理。

## 核心概念 (Core Concepts)

1.  **信任分數 (Trust Score)**:
    - 一個介於 0.0 和 1.0 之間的浮點數，代表對某個 AI 的信任程度。
    - 分數會被嚴格限制在此範圍內，任何超出範圍的更新都會被「鉗制」(clamp) 到邊界值。

2.  **範圍化信任 (Scoped Trust)**:
    - 信任度不是單一的，而是可以針對特定範圍進行評分。系統支援兩種範圍：
        - **`general`**: 對該 AI 的總體、通用信任度。
        - **`capability_name`**: 針對特定能力的信任度（例如，一個 AI 可能在 `data_analysis` 方面非常可信，但在 `creative_writing` 方面較不可信）。

3.  **回退邏輯 (Fallback Logic)**:
    - 當查詢信任分數時，系統會遵循一個清晰的回退順序：
        1.  首先，查詢特定能力的信任分數。
        2.  如果不存在，則回退到查詢該 AI 的 `general` 分數。
        3.  如果該 AI 完全未知，則返回系統預設的初始信任分數（通常是中立的 0.5）。

4.  **動態更新 (Dynamic Updates)**:
    - 信任分數是動態的，可以根據 AI 的表現進行調整。系統支援兩種更新方式：
        - **相對調整 (`adjustment`)**: 根據一次互動的結果，對現有分數進行小幅增減（例如，成功的協作 `+0.05`，失敗的結果 `-0.1`）。
        - **絕對設定 (`new_absolute_score`)**: 直接將分數設定為一個新值。

## 如何整合與使用 (Integration & Usage)

`TrustManager` 的分數可以被系統中多個決策點使用：

- **`DialogueManager`**: 在處理來自多個 AI 的混合對話時，可以根據信任分數來決定資訊的優先級。
- **`AgentCollaborationManager`**: 在分配子任務時，可以選擇在特定能力上信任分數最高的代理來執行。
- **`SelfCritiqueModule`**: 在評估一次任務的最終結果後，可以回頭更新參與該任務的外部 AI 的信任分數。

## 關鍵方法 (Key Methods)

- `get_trust_score(ai_id: str, capability_name: Optional[str] = None) -> float`:
  獲取指定 AI 在特定能力（或通用）上的信任分數，會執行回退邏輯。

- `update_trust_score(ai_id: str, adjustment: Optional[float] = None, new_absolute_score: Optional[float] = None, capability_name: Optional[str] = None) -> float`:
  更新 AI 的信任分數，是修改信任度的主要入口。

- `get_all_trust_scores() -> Dict[str, float]`:
  獲取當前所有已知 AI 的信任分數。

## 使用範例 (Example Usage)

```python
# 初始化 TrustManager，可以提供初始分數
trust_manager = TrustManager(initial_trust_scores={
    "did:hsp:ai_data_expert": {"general": 0.7, "data_analysis": 0.95},
    "did:hsp:ai_creative_writer": 0.6
})

# --- 查詢分數 ---

# 查詢專家在特定能力上的分數
expert_analysis_score = trust_manager.get_trust_score("did:hsp:ai_data_expert", capability_name="data_analysis")
# > 0.95

# 查詢專家在未知能力上的分數（回退到 general）
expert_writing_score = trust_manager.get_trust_score("did:hsp:ai_data_expert", capability_name="creative_writing")
# > 0.7

# 查詢一個完全未知的 AI（返回系統預設值）
unknown_score = trust_manager.get_trust_score("did:hsp:ai_unknown")
# > 0.5

# --- 更新分數 ---

# 創意作家完成了一次出色的任務，給予正面調整
trust_manager.update_trust_score("did:hsp:ai_creative_writer", adjustment=0.05)

# 數據專家提供了一次有問題的分析，針對該能力降低分數
trust_manager.update_trust_score(
    "did:hsp:ai_data_expert", 
    adjustment=-0.2, 
    capability_name="data_analysis"
)
```