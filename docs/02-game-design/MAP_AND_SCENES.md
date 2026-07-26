# 地圖與場景 (Map, Scenes & Objects)

## 地圖系統

### 地圖結構

遊戲世界由數個場景組成，地圖是連接這些場景的區域網絡。玩家可以在場景之間移動，每個場景有其獨特的名稱、描述、連接和事件。

```
    ┌──────────┐     ┌──────────┐
    │  村莊中心  │────▶│  森林    │
    └──────────┘     └──────────┘
         │                  │
    ┌────┴──────────────────┴────┐
    ▼                              ▼
┌──────────┐    ┌──────────┐    ┌──────────┐
│  湖畔     │───▶│  礦山    │───▶│  南門    │
└──────────┘    └──────────┘    └──────────┘
  [你在这里]
```

### 場景類型

| 類型 | 說明 |
|------|------|
| outdoor | 室外場景 |
| indoor | 室內場景 |
| dungeon | 迷宮/地下場景 |
| special | 特殊場景（隱藏/獨特） |

### 場景結構

```python
Scene:
  scene_id: str           # 唯一識別 ID (如 "S15", "SC-02")
  name: str               # 場景名稱
  description: str        # 場景描述
  scene_type: str         # outdoor/indoor/dungeon/special
  connections: dict       # 方向 -> 場景 ID mapping
  npcs: list[str]         # 場景中的 NPC ID 列表
  objects: list[Object]   # 場景中的物件
  properties: list[Prop]  # 場景中的不動產
  entry_requirements: dict    # 進入條件
  
  # 卡片來源
  card_id: str            # 關聯的卡片 ID
  card_type: str          # "SCENE" | "NATION" | "ORGANIZATION"
```

### 場景連接方向

場景之間的移動支援以下方向：
- north / south / east / west
- up / down (垂直移動)
- enter (進入建築物)
- exit (離開建築物)

---

## 不動產系統 (Property System)

不動產是場景中的建造物，可以購買、升級和改建。

| 類型 | 說明 | 功能 |
|------|------|------|
| house | 住宅 | 休息、存取物品 |
| shop | 商店 | 買賣物品 |
| workshop | 工坊 | 製作、合成 |
| farm | 農場 | 種植、收穫 |
| warehouse | 倉庫 | 大量物品存儲 |
| tower | 塔樓 | 瞭望、研究 |

不動產屬性：
- 所有權 (owner_id)
- 是否可購買
- 價格
- 功能列表 (rest, craft, store, trade)
- 建築狀態 (condition)
- 容納人數 (capacity)
- 升級系統 ( upgrades, max_level )

---

## 物件系統 (SceneObject)

場景中的可互動物件：

### 物件類型

| 類型 | 說明 | 互動方式 |
|------|------|----------|
| container | 容器 | 打開/搜索內容物 |
| workstation | 工作台 | 使用進行製作 |
| decoration | 裝飾 | 只能觀察 |
| vehicle | 載具 | 可騎乘/操作 |
| mechanism | 機制 | 觸發特定效果 |

### 容器物件

容器可以存放物品：
- is_container: bool
- container_contents: list of items
- is_locked: bool
- key_id: str (鑰匙物品 ID)

### 工作台物件

工作台提供合成功能：
- is_workstation: bool
- workstation_type: "forge" | "alchemy_table" | "kitchen" | "workbench"
- available_recipes: list of recipe IDs

### 載具物件

載具是可操作的場景物件：
- 可互動以移動到其他場景
- 可騎乘以提高移動速度
- 可裝備部件 (引擎、護甲、工具)

載具屬性：
- speed: 移動速度倍率
- capacity: 載人數
- cargo_capacity: 貨物容量 (kg)
- fuel: 燃料/體力
- condition: 車況 (0-100)
