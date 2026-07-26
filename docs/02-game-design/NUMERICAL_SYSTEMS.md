# 數值系統 (Numerical Systems)

## 計算公式與規則

### HP 計算

角色 HP = base_hp + (體質 x 10) + 裝備加成 + 技能加成
- base_hp: 由角色種族/職業決定 (人類=100)
- 體質每點 +10 HP 上限
- 裝備加成來自所有裝備的 red_bar.bonus 總和
- 技能加成來自戰鬥技能 level x 5

### 靈力計算

current_spirit = max_spirit - 已消耗靈力
恢復速度 = inertia_decay x willpower x 場域加成

施法消耗靈力 = 干涉強度 x (1 - affinity)
休息恢復靈力 = inertia_decay x willpower x 2
高靈濃度場域恢復加倍，低靈濃度減半

### 經驗計算

exp_needed_for_level = 100 + (level - 1) x 50
    等級1->2: 100 exp
    等級2->3: 150 exp
    等級10: 累計 3100 exp

技能經驗成長 = 技能使用次數 x 技能類別倍率
- combat: x2.0
- craft: x1.5
- social: x1.0
- exploration: x1.0
- knowledge: x1.2

技能升級條件: skill.exp >= skill.exp_to_next_level
  exp_to_next = 50 + (skill.level - 1) * 25

### 傷害公式 (Combat)

base_damage = atk.strength x 10
weapon_bonus = weapon_multipliers.get("damage", 0) x 100
total_atk = base_damage + weapon_bonus + skill_mod

defense = target.constitution x 5
armor_bonus = sum(armor_multipliers x 100)
total_def = defense + armor_bonus

damage = max(1, int(total_atk - total_def))

暴擊判定: random < focus x 0.1 時 damage x 1.5

### 屬性乘區合計

角色最終屬性 = 基礎屬性 + sum(所有裝備乘區) + 技能加成 + 狀態效果修正

### 聲望系統

聲望影響 NPC 對話選項和商店價格:
- <0: 敵意
- 0-20: 冷淡
- 20-50: 中立
- 50-80: 友好
- >80: 親密 (解鎖特殊內容)

### 疲勞與痛覺效應

| 狀態 | 懲罰 |
|------|------|
| fatigue > 80 | 行動速度 -50%, 效能減半 |
| fatigue > 90 | 有 30% 機率無法行動 |
| pain > 60 | 有 30% 機率行動失敗 |
| pain > 80 | 有 50% 機率行動失敗 |
| bleed_rate > 0 | 每回合自動扣除 HP, 數值=bleed_rate |

### 物品耐久效能對照

| 耐久比例 | 狀態名稱 | 效能 |
|---------|---------|------|
| 80-100% | 完好 | 100% |
| 60-80% | 輕微磨損 | 90% |
| 40-60% | 中度磨損 | 75% |
| 20-40% | 嚴重磨損 | 50% |
| 1-20% | 瀕臨損壞 | 25% |
| 0% | 已損壞 | 0% (失效) |

### 等級提升屬性提升

每次升級自動提升:
- HP: +5
- spirit: +3
- stamina: +3
- strength: +0.1
- constitution: +0.1
- agility: +0.1
- focus: +0.1
- willpower: +0.1