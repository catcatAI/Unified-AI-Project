# 權重拆 vs 任務拆：優缺、結合、預設裁決

- 日期：2026-10-10（Unity小車＋雙模型實測後）
- 問題（用户）：執行/思考混在整個模型裡，外部無法精細分離且保持長程能力；
  拆分器能否從AI内部權重去拆？與任務拆各有何優缺？能否一起用？
  拆出來的權重如何對應具體任務？按優缺點定是否進預設。

## 1. 現狀調查（不再重查）

- 真權重拆分基建（LoRA/PEFT/adapter訓練、MoE門控）：**倉裡沒有**。
- 最接近的只有 E4 steering 實驗群：劑量敏感、探針依賴、autopsy 降級——
  **陰性為主**，沒有可用的 steering 向量。
- 訓練真 adapter 需要 GPU＋數據＋評測：7GB CPU 機器不具備。
- 已有的是「軟」控制：模型選擇（thinker/executor 雙槽）、温度/長度/上下文、
  prompt 框架——全在 `dual_model.preset.yaml` 裡可配。

## 2. 優缺對照（實測背書，非空想）

| | 任務拆（TaskSplitter，已落地） | 權重拆・真（LoRA/adapter/MoE） | 權重拆・軟（per-kind配置） |
|---|---|---|---|
| 長程能力 | ledger 攜帶（弱於同權重，但可驗） | 同權重＋adapter 切換（理論最強） | 同上各自為政 |
| 可分離精度 | 件級（可測：BuildBody一次寫對） | 方向級（需訓練驗證） | 模型級＋參數級 |
| 成本 | 零訓練，prompt 開銷 | GPU＋數據＋評測（現無） | 零（已在預設） |
| 失敗模式 | 片超包絡（可遞歸再拆） | adapter 干擾／災難遺忘 | 選錯槽（降級兜底） |
| 證據 | Unity 4片＋驗證全跑通 | E4 陰性為主 | qwen 2.5s／gemma 6s 分流驗收 |

## 3. 結合設計（已落地）：映射層

任務拆（外層：拆什麼）× 權重配置（内層：怎麼跑）——交會點是
`dual_model.preset.yaml` 的 `per_kind_params` ＋ `adapters` 插槽：

- 件種類 → 槽位（think→thinker，micro-act→executor，deterministic→solver，verify→agent）
- 槽位 → 生成配置（温度/長度/超時）＋ 未來 adapter 路徑（現 null）
- 真 adapter 到位之日：填路徑即插即用，拆分器、Runner、評測全不動。

## 4. 預設裁決

- [x] 進預設：任務拆全套＋軟權重配置（`configs/presets/` 三件：dual_model、
  executor_framing、agent_mounts）＋映射層＋Runner。理由：零成本、有實測、可退化。
- [ ] 不進預設（記為研究）：真 LoRA/adapter 訓練、MoE門控、steering 向量。
  門檻：GPU到位＋E4類陽性證據＋評測門。寫死日期前不動，避免佔位宣稱。
- [x] 主AI不需深入拆分（也做不到）：拆是確定性規則＋配置的事；
  主AI只管提任務、收交付、判驗收——已由 intent→handler→mount→act 鏈覆蓋。
