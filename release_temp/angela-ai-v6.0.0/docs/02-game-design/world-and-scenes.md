# World & Scenes System (世界與場景系統)

## 總覽 (Overview)

遊戲的世界與場景系統負責兩項核心任務：

1.  **場景管理 (Scene Management)**: 定義遊戲的宏觀邏輯流程與狀態。例如，玩家是處於「主選單」、「遊戲世界」還是「對話」中。
2.  **世界結構 (World Structure)**: 定義「遊戲世界」場景的物理佈局和地面結構。

這兩個部分由 `scenes.py` 和 `tiles.py` 兩個模組分別實現，並協同運作以創造出玩家可探索的遊戲環境。

## 1. 場景管理 (`scenes.py`)

此模組採用了經典的**狀態機 (State Machine)** 設計模式來控制遊戲流程。

- **`GameStateManager` 類別**: 這是場景管理的核心。它持有一個包含所有可能場景的字典（`self.states`），並追蹤當前處於活動狀態的場景（`self.current_state`）。遊戲主循環 (`main.py`) 不會直接處理具體的遊戲邏輯，而是將所有 `handle_events`, `update`, 和 `render` 的呼叫全部委派給 `GameStateManager`，再由管理器轉發給當前活動的場景。這種設計模式極大地簡化了主循環的複雜度，並使不同遊戲狀態的邏輯得以完全解耦。

- **`Scene` 基礎類別**: 這是一個所有場景類別都必須繼承的父類別。它定義了一個場景所需具備的標準介面（`handle_events`, `update`, `render`），確保任何場景都能被 `GameStateManager` 正確地管理。

- **`VillageScene` 實例**: 這是一個具體的場景實現。它負責載入該場景特有的背景、NPCs，並處理該場景下的特定玩家互動（例如，按 `E` 鍵與 NPC 對話）。當 `VillageScene` 處於活動狀態時，只有它的 `update` 和 `render` 邏輯會被執行。

## 2. 世界結構 (`tiles.py`)

此模組定義了遊戲地圖的底層網格結構，是構成遊戲世界的基礎。

- **`TileMap` 類別**: 代表一整張遊戲地圖。其核心是一個二維陣列（`self.tiles`），其中儲存了大量的 `Tile` 物件，構成了地圖的網格。

- **`Tile` 類別**: 代表地圖上的一個「圖塊」或「格子」。每個圖塊都有一個 `tile_type` 屬性（例如 `grass`, `tilled`, `rock`），這決定了它的外觀和行為。此外，一個圖塊還可以包含其他物件，例如作物 (`crop`) 或石頭 (`rock`)，為農場或採集系統提供了基礎。

- **程序化生成**: 目前版本的 `TileMap` 在初始化時，會透過簡單的隨機算法來程序化地生成地圖的基本佈局（例如，隨機放置一些石頭）。

## 整合運作模式 (Integration)

場景和世界結構是這樣結合在一起的：

1.  一個具體的場景（如 `VillageScene`）在其初始化時，會建立一個 `TileMap` 的實例作為其場景地圖。
2.  當 `GameStateManager` 呼叫 `VillageScene` 的 `render` 方法時，`VillageScene` 會首先呼叫其 `TileMap` 成員的 `render` 方法，將地面、草地、石頭等背景圖塊繪製到畫面上。
3.  接著，`VillageScene` 會在繪製完背景的基礎上，再將該場景中的其他物件（如玩家、NPCs）繪製上去，從而完成一個完整的遊戲畫面。
