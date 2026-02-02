# Item & Inventory System (物品與庫存系統)

## 總覽 (Overview)

遊戲中的物品與庫存系統由兩個核心模組構成，它們各自職責分明，共同運作：

1.  **物品定義 (Item Definition)**: 由 `items.py` 負責，作為一個全域的物品目錄，定義了遊戲中所有可能出現的物品及其屬性。
2.  **庫存管理 (Inventory Management)**: 由 `inventory.py` 負責，提供了一個可重用的庫存容器，用於追蹤每個角色（玩家、NPC等）所擁有的物品及其數量。

## 1. 物品定義 (`items.py`)

此模組是遊戲世界的物品資料庫。

- **`Item` 類別**: 一個簡單的資料類別，用於在執行階段代表一個實際的物品物件。它包含物品的 `name`（名稱）、`description`（描述）和 `icon`（圖示）。

- **`ITEM_DATA` 字典**: 這是物品系統的核心。它是一個靜態字典，儲存了遊戲中所有物品的唯一定義。每個物品都有一個獨一無二的 ID (例如 `"wood"`, `"turnip_seeds"`) 作為鍵，其值則是一個包含該物品詳細屬性（如顯示名稱、描述、類型）的字典。
  
  *設計說明：目前 `ITEM_DATA` 是硬編碼在 Python 檔案中的，但其結構使其未來可以輕易地改為從外部 JSON 或 YAML 檔案載入，方便管理和擴充。*

- **`create_item(item_id)` 工廠函式**: 這是從外部與物品資料庫互動的標準介面。透過傳入一個物品 ID，此函式會查詢 `ITEM_DATA` 並回傳一個對應的 `Item` 物件實例。

## 2. 庫存管理 (`inventory.py`)

此模組提供了一個通用的、可被任何角色掛載的庫存組件。

- **`Inventory` 類別**: 一個容器類別，其實例代表一個角色的背包或儲物箱。

- **核心資料結構**: `Inventory` 內部使用一個簡單的字典 `self.items` 來儲存物品。字典的鍵是物品的 ID (與 `ITEM_DATA` 中的 ID 對應)，值則是該物品的持有數量。

- **關鍵方法**:
    - `add_item(item_name, quantity=1)`: 將指定數量的物品添加到庫存中。
    - `remove_item(item_name, quantity=1)`: 從庫存中移除指定數量的物品。如果物品數量歸零，則會從字典中刪除該項目。
    - `get_item_count(item_name)`: 查詢並返回庫存中某個特定物品的數量，如果物品不存在則返回 0。

## 整合運作模式 (Integration Example)

這兩個模組在使用時緊密地結合在一起：

1.  一個角色（例如 `Player` 物件）在其初始化時，會同時建立一個 `Inventory` 的實例，賦值給 `self.inventory`。
2.  當玩家在遊戲中執行「撿起木材」的動作時，遊戲邏輯會呼叫 `player.inventory.add_item("wood", 1)`。
3.  當遊戲需要顯示玩家的背包介面時，UI 系統會遍歷 `player.inventory.items` 字典。
4.  對於字典中的每一個項目（例如，`{"wood": 10}`），UI 會使用其鍵（`"wood"`）來呼叫 `items.create_item("wood")`，從而獲取該物品的完整資訊（如名稱 "木材"、描述和圖示），以便將其正確地繪製在螢幕上。
