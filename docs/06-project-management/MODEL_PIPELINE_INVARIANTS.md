<!--
  FILE_PATH: docs/06-project-management/MODEL_PIPELINE_INVARIANTS.md
  FILE_TYPE: documentation
  PURPOSE: 資料→訓練→生成 各階段的底層演算法、合理數值與不變量
  VERSION: 1.0.0-dev
  STATUS: active
  LANGUAGE: zh-TW
  LAST_MODIFIED: 2026-11-28
-->

# 模型管線不變量（資料・訓練・生成）

> 這份文件提供**整體一致性**與**微觀細節**：任何階段都必須滿足對應的不變量，數值必須落在合理範圍。修改任一腳本前先對照本文，避免無止盡的單點修補。

## 0. 唯一權威的資料流

```
語料 (data/core_corpus/sessions.jsonl, 477k sessions, 206M tokens)
  → tokenizer (唯一，與模型綁定)
  → train (loss 只在答案 token；EOS 必計；memory write 有監督；BPTT 跨回合)
  → checkpoint (一份 weights + state projection/memory tokens)
  → generate (state 回合內固定；用同一 tokenizer 解碼；EOS 停止)
  → gate (real/zero/random state 消融 + 對話檢查)
```

任何時間點的 tokenizer 只有一個。混用兩個 tokenizer 會讓 pretrained
embedding 收到完全不同語意的 id（我方 BPE id 1=`<bos>`，Qwen id
1=`!`），是致命 bug。

## 1. 資料階段

| 項目             | 合理值                                     | 現況                                               | 判定 |
| ---------------- | ------------------------------------------ | -------------------------------------------------- | ---- |
| sessions         | > 100k                                     | 477,108                                            | ✅   |
| tokens           | > 100M                                     | 206,396,814                                        | ✅   |
| tokenizer 與模型 | **必須同一個**                             | 從頭模型用 32k BPE ✅；Qwen 混用 ❌ → 修           | ⚠️   |
| special tokens   | `<bos>/<eos>/<pad>/<unk>` 各一、id < vocab | BPE: 1/2/0/3；Qwen: 無 bos, eos=151645, pad=151643 | ⚠️   |
| 答案 loss 遮罩   | 只算答案 token，含最後 EOS                 | 已修 off-by-one                                    | ✅   |
| session 截斷     | 每回合 ≤ max_len//2，最多 4–6 turns        | 一致                                               | ✅   |

## 2. 訓練階段

| 不變量            | 合理值／理由                                                       | 現況                  |
| ----------------- | ------------------------------------------------------------------ | --------------------- |
| CE baseline       | ln(vocab)。32k→10.37；151k→11.93。loss 必須低於此才叫有學          | 32k 模型 loss 5–10 ✅ |
| EOS 必須進 loss   | 最後答案 token 不可被切片漏掉                                      | 已修 ✅               |
| write-memory 位置 | **序列尾端**，causal mask 下才看得到整句                           | 已修 ✅               |
| state 跨回合      | BPTT：一 session 一次 backward，梯度回流到 write                   | 已修 ✅               |
| state 回合內      | 固定，不可每 token 覆寫                                            | 已修 ✅               |
| write 監督        | CE(state→被教內容)，不是弱 MSE                                     | 已修 ✅               |
| synthetic 比例    | 0.15–0.2：太低 state 遺忘（0.1→4/30），太高過早 EOS（0.2→1 token） | 0.15 gate 21/30 ✅    |
| LR                | 微調 5e-5–2e-4；從頭 1e-3–2e-3                                     | 一致 ✅               |

## 3. 生成階段

| 不變量   | 合理值                                     | 現況                          |
| -------- | ------------------------------------------ | ----------------------------- |
| decode   | **必須用訓練時的同一 tokenizer**           | Qwen 版本混用 → 修            |
| stop     | 只在該 tokenizer 的 eos id 停              | BPE=2；Qwen=151645            |
| state    | 回合內固定（RMT）                          | 已修 ✅                       |
| 答案品質 | 完整代號 recall ≥ 8/30；自然語言不重複模板 | 代號 21–27/30 ✅；自然語言 ❌ |

## 4. 已發現的真問題與修復狀態

| #   | 問題                                       | 狀態                              |
| --- | ------------------------------------------ | --------------------------------- |
| 1   | state 被 detach，write 梯度斷              | ✅ 修（BPTT）                     |
| 2   | write-memory 放前面看不到整句              | ✅ 修（後置）                     |
| 3   | 雙重 special tokens                        | ✅ 修（add_special_tokens=False） |
| 4   | eval state 格式不符                        | ✅ 修                             |
| 5   | EOS off-by-one（最後 token 未訓練）        | ✅ 修                             |
| 6   | 不停／模板 loop                            | ✅ 修（EOS 進 loss）              |
| 7   | 從頭混語料稀釋 state                       | ✅ 修（curriculum）               |
| 8   | **Qwen RMT 混用 BPE id 與 Qwen embedding** | ❌ 待修                           |
| 9   | 自然語言 mode collapse（「这首歌」）       | ❌ 待查（修 #8 後重測）           |

## 5. 合理數值總表（2026-11-28 快照）

| 量                     | 合理值                          | 量測             |
| ---------------------- | ------------------------------- | ---------------- |
| 核心分（智能定義）     | 0.00/10（未被核心產生正確答案） | 0.00             |
| 系統分                 | 6.41/10（表層聚合，非智能）     | 6.41             |
| state gate real        | ≥ 8/30                          | 21–27/30         |
| state gate zero/random | 0/30                            | 0/0              |
| RMT 參數               | 59M（d512/l4/K32）              | 59M              |
| 語言 loss              | < ln(vocab) 且持續下降          | 5–10（收斂不足） |
