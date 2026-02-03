# UI System (使用者介面系統)

## 總覽 (Overview)

UI (User Interface) 系統負責在遊戲畫面中繪製所有非遊戲世界本身的視覺元素，旨在向玩家傳達資訊並提供互動的介面。這包括選單、狀態顯示、對話框等。

一個設計良好的 UI 系統對於玩家能否理解遊戲狀態和順暢地與遊戲世界互動至關重要。在目前的實作中，`ui.py` 模組是所有 UI 元件的集中地，其最核心的元件是 `DialogueBox`。

## 對話框 (`DialogueBox` Class)

`DialogueBox` 是目前 UI 系統中功能最完整的元件，專門用於展示角色之間的對話。

### 職責 (Responsibilities)

- 在畫面底部繪製一個半透明的背景框。
- 顯示說話角色的頭像（`portrait`）。
- 顯示說話角色的名字（`character_name`）。
- 顯示對話的文字內容（`text`）。

### 運作模式 (How it Works)

`DialogueBox` 的運作基於一個簡單的狀態控制和渲染流程：

1.  **初始化**: 在一個需要對話功能的場景（例如 `VillageScene`）中，會先建立一個 `DialogueBox` 的實例。
2.  **觸發顯示**: 當一個對話事件被觸發時（例如，玩家與 NPC 互動），場景的邏輯會呼叫 `dialogue_box.show()` 方法，並將需要顯示的文字、角色名和頭像圖片傳遞給它。此操作會將對話框的內部狀態 `is_active` 設為 `True`。
3.  **持續渲染**: 在場景的 `render` 方法中，每一幀都會呼叫 `dialogue_box.render()`。`render` 方法會檢查 `is_active` 狀態。
4.  **繪製**: 如果 `is_active` 為 `True`，`render` 方法就會使用 `pygame` 的繪圖功能，將背景、邊框、頭像、名字和文字等所有視覺元素繪製到傳入的 `surface`（通常是主螢幕）上。
5.  **隱藏**: 當對話結束時（例如，玩家按下特定按鍵），場景會呼叫 `dialogue_box.hide()`，將 `is_active` 設為 `False`。這樣在下一幀渲染時，對話框就不會再被繪製出來。

### 未來擴展 (Future Expansion)

`ui.py` 模組未來可以擴展以包含更多可重用的 UI 元件，例如：

- `MainMenu`: 遊戲主選單。
- `InventoryMenu`: 用於顯示和管理玩家庫存的介面。
- `HUD (Heads-Up Display)`: 用於在遊戲主畫面上顯示玩家的生命值、體力等即時狀態。
- `QuestLog`: 任務日誌介面。
