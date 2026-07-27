# 角色系統 (Character System)

## 角色類型

遊戲中有三種角色類型：

| 類型 | 代碼 | 說明 | 控制者 |
|------|------|------|--------|
| PC | Player Character | 玩家操控的角色 | 玩家 |
| NPC | Non-Player Character | AI 驅動的角色 | AI / GM |
| GM | Game Master | 遊戲主持人 | Angela AI |

### PC — 玩家角色

PC 可以：
- 從現有角色卡中選擇一個原型作為 PC（59+ 張角色卡）
- 或使用角色卡新建一個自定義角色
- 控制角色在世界中移動、互動、交流

---

## 種族系統 (Race/Body System)

### 核心設計：種族 = 天生肢體 + Token 組合

角色的「種族」不是固定欄位，而是由 **token 組合** 決定：
- 卡片上的 token 類別決定了角色的種族歸屬
- 不同種族有不同的天生肢體（body parts）
- 天生肢體提供額外的裝備欄位（equipment slots）
- 天生肢體有獨立的 HP，受傷會影響功能

### 種族資料結構

```python
RACE_DATA = {
    "人類": {
        "body_parts": ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg"],
        "extra_slots": [],
        "required_tokens": [],  # 預設種族，無需特定token
        "innate_bonuses": {},   # no innate bonuses
        "base_hp": 100,
        "desc": "標準人型生物"
    },
    "艦娘": {
        "body_parts": ["head", "torso", "arms", "legs", "rigging_body"],
        "extra_slots": ["rigging"],
        "required_tokens": ["naval"],
        "innate_bonuses": {"spd": 0.5},  # 水上移動加成
        "base_hp": 120,
        "desc": "擁有艦裝身的人型艦艇"
    },
    "獸娘": {
        "body_parts": ["head", "torso", "arms", "legs", "tail", "claws"],
        "extra_slots": ["tail", "claws"],
        "required_tokens": ["beast", "vitality"],
        "innate_bonuses": {"spd": 0.3, "atk": 0.2},
        "base_hp": 110,
        "desc": "具有動物特徵的人型生物"
    },
    "術士": {
        "body_parts": ["head", "torso", "arms", "legs", "mana_core"],
        "extra_slots": ["core"],
        "required_tokens": ["element"],
        "innate_bonuses": {"karma": 0.5, "sp": 20},
        "base_hp": 80,
        "desc": "擁有魔力核心的魔法使用者"
    },
    "竜族": {
        "body_parts": ["head", "torso", "arms", "legs", "wings", "horns"],
        "extra_slots": ["wings", "horns"],
        "required_tokens": ["draconic"],
        "innate_bonuses": {"atk": 0.5, "def": 0.3},
        "base_hp": 150,
        "desc": "具有龍族血統的強大生物"
    },
    "機械": {
        "body_parts": ["head", "torso", "arms", "legs", "cyber_limbs"],
        "extra_slots": ["upgrade"],
        "required_tokens": ["mechanism"],
        "innate_bonuses": {"def": 0.4, "spd": -0.1},
        "base_hp": 130,
        "desc": "機械義體改造者"
    },
}
```

### Token → 種族映射

角色的種族由 token 決定：

| Token 類別 | 偵測種族 | 優先級 |
|-----------|---------|--------|
| naval | 艦娘 | 最高 |
| beast | 獸娘 | 高 |
| draconic | 竜族 | 高 |
| mechanism | 機械 | 中 |
| element | 術士 | 中 |
| spiritual | 精霊 | 中 |
| (無特殊token) | 人類 | 最低 (預設) |

### 角色立繪系統 (Symbol Portrait)

遊戲中的角色立繪**不是圖片**，而是由符號組成的文字藝術。這是 CLI 遊戲的核心設計決策。

### 立繪設計規則

```
PC 角色 (符號組成):     NPC 角色 (符號組成):
  ██╗    ██╗              ╔═╗  ╔═╗
 ╚═╝    ╚═╝              ║█║  ║█║
  ╔═╗  ╔═╗               ║█║  ║█║
  ║█║  ║█║               ╚═╝  ╚═╝
  ╚═╝  ╚═╝
```

- 使用 █ (塊狀)、║ (豎線)、═ (橫線) 等 ASCII 符號
- 不同種族有不同符號組合（戰士、工匠、術士、商人、艦娘等）
- 表情狀態使用臉部符號

### 角色卡與世界觀生成

#### 卡片堆概覽

| 卡片類型 | 數量 | 說明 |
|----------|------|------|
| 角色卡 | 59+ | CC-01 ~ CC-67 + CCK-01，全部角色原型 |
| 場景卡 | 24 | 場景定義 |
| 劇情節點卡 | 76 | 故事節點 |
| 組織卡 | 16 | 勢力/公會 |
| 規則卡 | 15 | 遊戲規則 |

#### Token 類別分布

| Token 類別 | 出現次數 | 對應屬性 |
|------------|----------|----------|
| lore | 343 | 知識、學識、歷史 |
| relation | 97 | 人際關係 |
| social | 78 | 社交技能 |
| vitality | 75 | 生命力 |
| combat | 67 | 戰鬥能力 |
| element | 57 | 元素能力 |
| status | 44 | 狀態效果 |
| skill | 41 | 技能等級 |
| knowledge | 36 | 學識深度 |
| craft | 32 | 製作能力 |
| energy | 29 | 能量/靈力 |
| mechanism | 22 | 機構/機關 |
| exploration | 5 | 探索能力 |

---

## 三色屬性條系統

### 🔴 紅條 (身體狀態)

代表角色的物理身體狀態。

#### 主屬性

| 屬性 | 說明 | 初始值 |
|------|------|--------|
| HP (血量) | 生命值，歸零則昏迷/死亡 | 依種族 |
| max_hp | HP 上限 | 依種族 |
| 身體 (body) | 身體強度，影響物理傷害 | 1.0 |
| 肢體 (limbs) | 肢體完整性，每個肢體獨立 HP | 動態 |

#### 肢體系統

基礎肢體（所有人類都有）：
| 肢體 | ID | 影響 |
|------|-----|------|
| 頭部 | head | 頭部受損影響視力和理智 |
| 軀幹 | torso | 軀幹受損影響所有行動 |
| 左臂 | left_arm | 左手無法裝備/使用物品 |
| 右臂 | right_arm | 右手無法裝備/使用物品 |
| 左腿 | left_leg | 移動速度減半 |
| 右腿 | right_leg | 移動速度減半 |

種族專屬肢體：
| 種族 | 肢體 | ID | 影響 |
|------|------|-----|------|
| 艦娘 | 艦裝身 | rigging_body | 艦裝受損→艦裝能力失效，無法水上移動 |
| 獸娘 | 尾巴 | tail | 尾巴受損→平衡感下降，SPD-30% |
| 獸娘 | 爪 | claws | 爪受損→近戰攻擊-50% |
| 術士 | 魔力核 | mana_core | 魔力核受損→SP 恢復減半 |
| 竜族 | 翼膜 | wings | 翼膜受損→無法飛行 |
| 竜族 | 角 | horns | 角受損→魔力輸出-30% |

肢體 health ≤ 0 = 該肢體失去功能

### 🔵 藍條 (靈活躍度)

代表個體靈的清醒與活躍程度。

| 屬性 | 說明 | 初始值 |
|------|------|--------|
| SP | 靈力 (技能/魔法消耗) | 依種族 |
| max_sp | SP 上限 | 依種族 |
| stamina | 體力 (物理行動消耗) | 100 |

### 🟢 綠條 (經歷狀態)

代表角色的成長與經歷。

| 屬性 | 說明 | 初始值 |
|------|------|--------|
| level | 角色等級 | 1 |
| exp | 當前經驗值 | 0 |
| skills | 技能字典 | 空 |
| reputation | 聲望 | 0 |

#### 技能系統

技能按類別分類：
- combat — 戰鬥技能
- craft — 製作技能
- social — 社交技能
- exploration — 探索技能
- knowledge — 學識技能

每個技能有 level、exp、max_level，技能經驗通過使用增長。
