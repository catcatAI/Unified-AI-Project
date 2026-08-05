# 四則運算「學會且有泛化」實驗報告與 ED3N/GARDEN 修復標記

> 日期: 2026-08-04(第二次修訂,推翻 v1 負面結論)
> 目的: 驗證 ED3N/GARDEN 的表示 + 生成機制能否**真正學會**四則運算並泛化(而非硬編或死記),並標記兩引擎的修復點。
> 最終要求: ED3N 與 GARDEN 除體量與精度外,架構與行為應一致。

---

## 0. 執行摘要(TO;DR)

**初期判定「學習機制學不會四則」是錯誤的**,源自兩個實驗瑕疵:
1. **輸出表示錯誤**: 用純量回歸(1 個連續輸出),而非逐位符號分類
2. **數據分割錯誤**: 不公平的帶狀 held-out(符號 9 從未出現在訓練中)+ 靜態 60/40

修正後,用**逐位符號分類 + carry(進位)通道 + 組合公平 held-out**,加/減/乘**全部真正學會且在組合空間泛化**:
- 加法/減法: 0-999 全域,未見樣本 100% 正確(含進位/借位/負號)
- 乘法: 可重用單 digit 模組 + 部分積移位,0-99 全域 100% 正確
- 組合公平 held-out(所有符號都見過、只藏組合): held-out 100% 正確

**核心定義**: 「學會且有泛化」= 從組合元素學到規則,推廣到元素的所有組合。**不包含**「未見符號的外推」(那是符號層,B 類邊界)。

---

## 1. 實驗設定進化史(為什麼 v1 錯)

| 版本 | 輸出表示 | 數據分割 | 結果 | 問題 |
|------|---------|---------|------|------|
| v1 (arith5) | 純量回歸 | 帶狀 interp/extrap | `+`test~53%,`*`train 1% | 序列降級=平滑非規則;符號 9 未見不公平 |
| v2 (digitslot) | 逐位分類 | 帶狀 | `+`34% | 9 未見仍不公平 |
| v3 (digitslot_fair) | 逐位分類 | `a≤8 or b≤8` | `+`34% | `9+b` 行全對(進位泛化!),但 tens 位 50% |
| v4 (seq_arith) | 逐位分類+carry | 同上 | `+`52% | carry 通道加入 |
| v5 (seq_scale) | 逐位分類+carry | **隨機 60/40 | **加法 0-999 100%** | 修正兩種錯誤 |
| v6 (sub_learn) | +sign 槽 | 隨機 60/40 | **減法 0-999 100%** | |
| v7 (mul_learn) | 逐位分類 | 隨機 60/40 | `*`train 14% | 乘法非直接函數 |
| v8 (mul_compose) | 組合 | — | **乘法 0-99 100%** | |
| v9 (mul_strong) | 組合 | 只訓 0-5 digit | test 12.5% | **符號外推不可能** |
| v10 (mul_final) | 組合 | 藏組合 held-out | **held-out 100%** | **組合泛化可行** |

**根因診斷**(diag_add): 純量回歸時 units 位 94%、tens 位 50%——網路學會「單位加」但無法把 carry 傳到十位。逐位分類 + carry 通道正是缺失的組合結構。

**承診發現(v9 關鍵)**: 單 digit 模組只訓練 0-5×0-5,測試含 6-9 的對 → 12.5%(只有乘 0 對)。**符號是離散 key,embedding 無「未見 digit」的序結構可依賴** → 符號外推不可能。這不是參數可修,是表示層本質。

## 2. 最終驗證(「學會且有泛化」操作定義)

### 加法(0-999,隨機 60/40)
```
329+818=1147✓  490+991=1481✓  812+260=1072✓  719+14=733✓
train=1.000, test=1.000 (含每一位進位)
```

### 減法(0-999,隨機 60/40,含負號 + sign 槽 + borrow 通道)
```
784-369=415✓  380-692=-312✓  50-668=-618✓  858-454=404✓
train=1.000, test=1.000 (含借位 + 負數)
```

### 乘法(單 digit 模組 + 部分積移位,0-99)
1. **單 digit 模組**(0-9×0-9,100 對)train=1.000,由數據學習
2. **組合**: `a0b0 + 10(a0b1+a1b0) + 100(a1b1)`
3. **全域 0-99**: 10000/10000 = 1.000 ✓
4. **組合公平 held-out**(藏「雙操作數皆 10-19」): held-out 100% ✓
```
12*17=204✓  18*19=342✓  13*17=221✓  10*13=130✓
```

### 組合公平 held-out 的最終判定
所有符號(0-9)都在訓練出現過,只隱藏特定組合 → 組合規則成功泛化到藏起的組合。**這證明了「學會且有泛化」成立**——不是死記(死記無法命中所藏的 100 個組合),不是硬編(模組由數據學)。

## 3. 硬編 vs 學會的判定標準

- **硬編**: 在程式碼注入 `return a+b` / 乘法表 / 序結構 embedding。本實驗不含任何此類。
- **學會**: 表示層(embedding)+ 生成機制(carry/組合)都由數據梯度學習。carry 值、部分積、結果 digit 全是學出來的。
- **符號外推 vs 計數外推(關鍵區分,§3.1)**: 兩個不同概念,實驗證明一者不可、一者可。

### 3.1 符號外推 vs 計數外推(訓 0-5、測 6-9 對照)

| 表示方式 | 訓 0-5 | 測 6-9 | 結論 |
|---------|--------|--------|------|
| **A) 符號查表**(digit=孤立離散 token) | 0.000 | **0/4 全錯**(6→0.45, 7→-0.93) | 無法生造未見符號(原始人無字寫試卷) |
| **B) 計數**(digit=d 個重用的「一」單位向量) | 0.000 | **4/4 全對**(6→6.00 ... 9→9.00) | 數數可延伸到未知量 |

**核心結論(B2 修正)**: 同網路、同損失、同訓練集,唯一差異是表示方式——
- **符號查表** → 無法外推 digit 值(離散 key 無量值可依)
- **計數/組合表示**(可重用單位相加)→ 完美外推

因此「符號外推不可能」**不是天生鐵律,是表示選擇的結果**。若 digit 表示為可組合單位(計數式),則外推可行。

### 3.2 兩引擎 digit 表示實證(GARDEN / ED3N)

| 引擎 | 量測方法 | 結果 | 解讀 |
|-----|---------|------|------|
| GARDEN | 載入 TF-IDF 相容模式,量 m0..m9 向量 cosine 相似矩陣 | **全正交**: off-diagonal 全 0,`sim(4,5)=sim(0,9)=0` | 每個 digit 獨立孤立符號,無量值結構 → 符號查表 |
| ED3N | `_stage_math` 建 m1..m10,`sync_from_dictionary` 後檢查 relations | **m1..m10 relations 全空** | 孤立網路節點,無 inter-digit 權重 → 符號查表 |

### 3.3 佔位符延遲綁定研究(placeholder_bind.py)

**方案**: 字典加入 `m_gen` 泛化佔位槽,未見符號路由過去;佔位槽只提供「確定性學到的量值」(計數結構);網路在計數結構上外推取得暫無對應符號的結果;之後取得真實字形再綁定。

**對照實驗**(值回歸任務,訓 0-5,測未見量值 ★=6):

| 佔位槽表示 | ★(=6) 預測 | 結果 |
|-----------|-----------|------|
| **計數槽** `v(d)=d·u`(單位向量重複) | 5.65 | **✓ 外推成功**(線性結構自然延伸) |
| **孤立槽**(正交向量) | 2.99 | ✗ 只能指到訓練範圍內的值(綁定後也用不了) |

**關鍵前提**: 計數表示必須是「單位向量重複」`d·u`,不是「正字計數」prefix-ones——後者因第 6 個位置從未啟用,外推同樣失敗。

**結論**: 佔位符的價值在「**可組合單位的槽**」(計數),不在孤立符號槽。它提供的是**機制**(讓未命名的量值先能被計算、後綁字形),不是憑空生造字形的能力——量值外推仍由計數結構承擔,字形綁定是監督步驟。這與 §3.1 一致:可延伸的是量值,名字靠綁定。

## 4. ED3N/GARDEN 修復與對齊標記

> 原則: 修復分(A) 能修的真實缺陷、(B) 能力邊界(誠實記錄)。

### A 類: 已修/建議修

| # | 位置 | 問題 | 狀態 |
|---|------|------|------|
| A3 | ED3N `_build_math_presets` + `config/math_presets.json` | ASCII 運算子 `+ - * / =` encode 後丟失 | **✅ 已修** — m11..m15 en 加 ASCII(`"plus +"` 等);`3+4`→`['m4','m5','m11']`;與 GARDEN `op1..op5` 對齊;ED3N 86 測試全通過 |
| A8 | 表示層需「位置 + 計數式單位」概念 | 實驗證明逐位處理是學會多位元算術關鍵;計數表示(§3.1 B)可外推 digit 值;佔位符槽須為可組合單位(§3.3) | **建議研究**: ED3N/GARDEN 加入位置索引 + 可組合計數式 digit 單位 + `m_gen` 佔位槽(與 A3 同屬表示層對齊);§3.2 顯示目前 digit 為孤立符號,此為主要改良方向 |

### 降級項(評估後不修改)

| # | 差異 | 不修改理由 |
|---|------|-----------|
| A1 | ED3N `m1..m10` vs GARDEN `m0..m9` | 各自有持久化更新邏輯(`_apply_preset_updates` 依賴固定 key),重命名破壞 checkpoint 相容與測試 |
| A2 | ED3N `m11..m15` vs GARDEN `op1..op5` | 同上;key 純內部識別符,無數值解讀邏輯 |
| A5 | 布林 key | **兩引擎皆有 b1..b5**(初判誤) |

### B 類: 能力邊界(誠實記錄,不得硬編)

| # | 邊界 | 證據 | 處理 |
|---|------|------|------|
| B1 | 純量回歸無法泛化多位元算術 | diag_add(tens 位 50%) | 學習機制輸出須採逐位符號分類 |
| B2 | **符號表示下無法外推 digit 值(表示層選擇,非硬上限)** | counting.py A: 訓 0-5 測 6-9 全錯;B: 計數表示全對;GARDEN m0..m9 全正交、ED3N m1..m10 relations 全空 | 符號(正交/孤立)表徵學不出 magnitude;計數/組合表徵則可外推。兩引擎用符號表徵 → 目前無法,但可透過表示層對齊(A8 計數式/位置表示)改變,不得斷言天生不可能 |
| B3 | 乘法需組合性(非直接函數) | v7: 逐位分類 `*`train 14% | 需可重用的組合模組,B4 |
| B4 | 單 digit 模組需全域符號訓練才可組合 | v8 vs v9 | 組合泛化成立;符號外推不成立;兩者須明確區分 |
| B6 | SNN 加法為記憶(map),非演算法理解;外推=edge-case 全錯 | capability_generalize E1: 只學 carry0 → carry1 盲測 7% | 每個符號元件(含 carry 進位)須顯式納入訓練(carry0+1),無「自動學會進位規則」;構成「確定性引擎補組合、SNN補符號映射」的分工依據 |
| B5 | `//` 的「成功」為容差帶假象 | 早期 | 除法組合性需整除判定,列為後續研究,不得以準確率為證據 |

## 5. 對齊目標規格(ED3N vs GARDEN「僅體量與精度不同」)

- **確定性算術真相**: 兩引擎 `route_math` 皆委派 `evaluate_math` ✅ 已一致
- **ASCII 運算子進表示**: ED3N m11..m15 現含 ASCII,與 GARDEN op1..op5 一致 ✅(本批修復)
- **輸出表示(關鍵)**: 逐位符號分類 + carry 通道(實驗證實的可行方式)**已在 `capability_math3` 證實**:獨立 carry_in 0/1 真值表 → digit 母版 100%、多位加法 10/10 ✓;計數式單位表示(§3.1 B)可進一步達成 digit 值外推——列為 A8 建議,是兩引擎表示層對齊方向
- **能力邊界聲明一致**: 符號表示下無外推 digit 值(B2)、乘法需組合(B3),兩引擎統一
- **僅差**: 體量(字典/網路規模)、精度(量化/容差)
- **m-key/op-key 內部命名差異**: 因持久化相容維持現狀

## 6. 實驗腳本(temp 目錄)

- `seq_scale.py` — 加法 0-999 100% ✓
- `sub_learn.py` — 減法 0-999 100% ✓
- `mul_compose.py` — 乘法組合 0-99 100% ✓
- `mul_strong.py` — 符號外推測試(證偽 B2)✓
- `mul_final.py` — 組合公平 held-out 100% ✓
- `counting.py` — 符號 vs 計數表示對照(§3.1:B2 由「鐵律」改為「表示層選擇」)✓
- `placeholder_bind.py` — 佔位符綁定:計數槽可延伸未見量值、孤立槽不能(§3.3)✓
- `capability_math3.py` — digit 加法母版(carry0+1 獨立真值表):多位加法 10/10 ✓(carry 鏈 bug 修正過程見 `capability_math2.py`)
- `capability_generalize.py` — 泛化邊界:E1 只學 carry0→carry1 盲測 7%;E2 只學 digit0-7→digit8-9 盲測 0%;E3 完整母版→隨機 0-1999 加法 30/30 ✓
- `seq_arith.py` / `digitslot_fair.py` / `diag_add.py` — 中間迭代
- `arith5.py` / `mul_test.py` / `mul_cap.py` — v1 負面結論腳本(已被推翻,僅存歷史)

## 7. A+B 落地(專業化為正式碼)

本研發結論(A 表示層對齊 + B 訓練流程接入 + 對話學習 + 自主閉環)已從 `temp/` 實作進 `apps/backend/src`:

- **`apps/backend/src/ai/arithmetic/`**(新套件)— 自主加法 digit-cell 學習迴圈:
  - `DigitRepresentation` — 可切換 `onehot`(預設,研究 §5 閉合真值表可靠收斂)與 `counting`(僅供外推實驗 opt-in)。
  - `CellSample`(hashable)、`LoopSnapshot`(resume,含 `task_accuracy` 逐 op 精準度)資料類別。
  - `ArithmeticLearner` — `run()` 自主閉環:數據不足自動生成各 op 確定性真值表;學會自動結束(`learned-optimal`/`learned-threshold`)‧無法收斂自動結束(`unconvergeable-stall`/`max-epochs-reached`)‧`save()/load()` 可續訓(向後相容舊 checkpoint)。
  - 學習核心 `_CellMLP` 泛化研究證實的 **L-BFGS-B tanh-MLP + 多 softmax head**(`capability_math3.py`),1s 收斂 100%,非 Adam/線性 readout;**四個 op cell 共用同一優化路徑**:
    - **加法** carry cell(維持原樣,`min_cols` 保護不變);
    - **減法** borrow cell(`hidden_size≥128` 並 `maxiter=600`,因 borrow 輸出類別不平衡需要額外容量);
    - **乘法** 單 digit lattice(`da * db -> low, high`);
    - **邏輯閘** AND/OR/XOR/NAND/NOR/XNOR/NOT 閉合 `{0,1}` 真值表(`_logic_result` 純布林定義 —— `evaluate_math` 字集無位元運算)。
  - `predict_addition`/`predict_subtraction`/`predict_multiplication`/`predict_logic_gate` 逐欄組合 cell;carry/borrow 為輸入維度(§B6,無未見 carry/borrow 外推);carry 鏈加 `nd+4` 上限保護未收斂網路;負數差以對稱 `-(b-a)` 處理;多位乘法走 Schoolbook 部分積、以加法 cell 求和。
  - `learn_from_dialogue` — 從對話抽取 `x + y`/`x - y`/`x * y` 算式(確定性引擎為標籤來源→正確逐欄 cell;邏輯閘因自然語言 AND/OR 過於歧義僅從閉合真值表學習),`auto_run=False` 佇列、週期性全量 fit。
- **`apps/backend/src/ai/ed3n/continuous_learning.py`** — `ContinuousLearningPipeline` 新增 `arithmetic_learner` hook,`process_interaction` 於 `interaction % train_interval == 0` 觸發全量 re-fit。
- **`scripts/train_pipeline.py`** — B 類接入:新增 `_step5b_train_arithmetic`,`main()` 加 5b step 並 `save_state(5.5)`;擴充 spot-check 涵蓋 add/sub/mul/logic 並輸出 `arithmetic_per_op` 精準度。
- **`apps/backend/configs/system/ed3n.default.yaml`** — `ed3n.train.arithmetic.*` 配置(representation/dim/min_acc/max_epochs/stall_epochs)。
- **`tests/unit/test_arithmetic_learner.py`** — 32 tests:四 op cell 收斂 100%‧多位加/減/乘與負數差‧邏輯閘全組合‧隨機 200/100 例‧save/load 續訓(含 op cell weights)‧dialogue/CLP 整合‧真值表與表示模式‧終止保證。落地 commit:`281a2870`(A+B 基礎),本批擴充(sub/mul/logic cell)。

分工複述:數值真相永遠來自確定性引擎(`services.math_verifier.evaluate_math`,永不參與學習;減法/乘法標籤亦走引擎,邏輯閘標籤用純布林定義);SNN/digit-cell 只學習符號映射與 digit 組合。