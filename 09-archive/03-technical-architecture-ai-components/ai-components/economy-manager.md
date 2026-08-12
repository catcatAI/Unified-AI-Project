# Economy Manager (經濟管理器)

## 總覽 (Overview)

`EconomyManager` 是 Unified AI 專案中負責處理所有遊戲內經濟活動的核心元件。它管理著玩家的貨幣餘額、處理交易，並實施一套可動態調整的經濟規則。此模組的設計重點在於其適應性，允許核心 AI 根據遊戲世界的狀態變化來即時修改經濟參數，從而創造一個生動且能自我調節的經濟環境。

## 主要特性 (Key Features)

- **資料庫支援**: 所有玩家的經濟數據（如貨幣餘額）都透過 `EconomyDB` 元件持久化儲存在專用的資料庫中，確保資料的完整性和一致性。
- **交易完整性**: 在處理任何交易前，系統會嚴格檢查發起者的餘額，確保玩家不能花費超過其所擁有的貨幣，防止「透支」。
- **規則驅動系統**: 核心的經濟參數（例如交易稅率）並非寫死在程式碼中，而是儲存在一個可配置的 `rules` 字典裡，方便管理和調整。
- **動態與適應性**: `update_rules` 方法提供了一個強大的介面，讓核心 AI 能夠在執行階段修改經濟規則。這使得系統能夠應對通貨膨脹/緊縮等經濟狀況，實現更複雜的模擬。

## 核心元件 (Core Components)

- **`EconomyManager` Class**: 管理器的主要類別。
- **`rules` Dictionary**: 一個存放當前經濟參數的字典。主要參數包括：
    - `transaction_tax_rate`: 每次交易時，系統抽取的稅率。
    - `daily_coin_allowance`: 每日給予玩家的津貼（一個可擴展的規則範例）。
- **`EconomyDB`**: 底層的資料庫處理模組，`EconomyManager` 的主要依賴。

## 關鍵方法 (Key Methods)

- `process_transaction(transaction_data: Dict[str, Any]) -> bool`:
  處理一筆交易的核心方法。它會驗證餘額、計算稅金並更新資料庫。

- `get_balance(user_id: str) -> float`:
  查詢並返回指定使用者的目前貨幣餘額。

- `update_rules(new_rules: Dict[str, Any])`:
  供核心 AI 呼叫的介面，用於更新現行的經濟規則。

## 整合與應用 (Integration & Application)

`EconomyManager` 被設計為與遊戲主循環和 AI 決策系統緊密整合：

- **玩家互動**: 當玩家在遊戲中進行購買、出售或交易等操作時，遊戲邏輯會呼叫 `process_transaction` 來處理相應的經濟活動。
- **AI 宏觀調控**: 核心 AI 可以監控整個遊戲世界的經濟指標（例如，貨幣總量、物價指數）。當偵測到經濟失衡時，AI 可以主動呼叫 `update_rules` 來調整稅率或津貼，以穩定經濟。

## 使用範例 (Example Usage)

```python
# 初始化經濟管理器
config = {"initial_tax_rate": 0.05, "db_path": "game_economy.db"}
econ_manager = EconomyManager(config)

# 玩家 (player_01) 嘗試購買一個價值 100 元的物品
transaction = {
    "user_id": "player_01",
    "amount": 100.0,
    "item_id": "magic_sword_of_awesomeness"
}
success = econ_manager.process_transaction(transaction)

if success:
    print("購買成功！")
    new_balance = econ_manager.get_balance("player_01")
    print(f"玩家的新餘額是: {new_balance}")
else:
    print("購買失敗，餘額不足。")

# 核心 AI 為了抑制通貨膨脹，決定提高交易稅率
ai_new_rules = {"transaction_tax_rate": 0.08}
econ_manager.update_rules(ai_new_rules)
print("AI 已將交易稅率更新為 8%。")
```