# DERIVED_ESTIMATES.md — 由現有資料推算的性能/成本/鏈路整理（2026-10-06）

> 本檔是**從現有凍結草案與概念設計推導出來的分析**，不是新定案。所有數字都依賴：`cim_freeze_draft.yaml`（validated
> model 為主）、
> `concept_design.yaml`、`angela_interface_freeze_packet.yaml`、`component_registry.yaml`。磁碟上的版圖實測值不在這裡（見
> `chip/design/VERIFIED_COMPARE.md`）。

## 0. 名詞（先分清）

| 英文    | 中文     | 說明                                                |
| ------- | -------- | --------------------------------------------------- |
| die     | **晶粒** | 最小運算單元（1.5 mm²、16 KB 駐留、16384 MAC/pass） |
| package | **封裝** | 對外一顆「晶片」= 16 晶粒                           |
| card    | 板子     | 4–16 封裝 + DDR5 L2                                 |

## 1. 算力怎麼算出來的（推導鏈）

```
每 pass MAC/die = strip_count(8) × strip_input_width(2048) = 16384
pass/s/die      = 1 / sense_window(50ns, validated) = 20M
→ 327.7 GMAC/s/die
× 16 晶粒/封裝   = 5.24 TMAC/s/封裝
× 2 (MAC=2op)   = ~10.5 TOPS INT8/封裝
× 4 封裝/卡     = ~21 TMAC/s ≈ 42 TOPS INT8/卡
```

能效（validated model）：0.594 pJ/MAC → 1.68 TOPS/W、卡級 12.5
W。draft（1.8V/1µs）：707 pJ/MAC、742 W（超 300W cap，已被文件標記失敗）。

**注意**：50ns sense
window 無實體驗證，算力數字是 fixture（ngspice）等級，非 silicon/時序 signoff。

## 2. 鏈路速度 vs 計算等級（整條路）

```
PCIe Gen5 (50 GB/s)
 → 卡級 DDR5 L2 (~58 GB/s 實效, 2ch)   ← batch=1 瓶頸
   → 封裝內晶粒間(未凍結, 8–16 pin ≈ 100–200 GB/s)
     → 每晶粒 L1 SRAM(目標 32MB, sky130 1.5mm² 放不下 → end_state)
       → strip array pass (107ns broadcast DDR200, 50ns sense)
```

batch=1、7B int8、42 TOPS：

- 算力牆 ≈ 3000 tok/s
- 卡級 DDR5 牆 ≈ 58/7 ≈ **8 tok/s** ← 實際 ceiling
- 重疊點：搬運 120ms vs 每 token 計算 0.67ms → B≈180 時填滿算力

## 3. 站位（側對側/背對背/面對面）整理

| 站法                       | 距離           | token/s 效果                        | 備註                |
| -------------------------- | -------------- | ----------------------------------- | ------------------- |
| 側對側+卡級 DDR5（現案）   | 5–15mm         | ~8 tok/s                            | 最便宜              |
| 同板背對背                 | 3–5mm          | 可提高鏈路頻寬，但不動規格          | 板外徑略            |
| 雙基板面對面（SPEC S2/S3） | 熱管厚數 mm–cm | 受限針腳母頭 8–16 腳 ≈ 100–200 GB/s | SPEC 衛生紙階段 TBD |

## 4. 不同 DDR/頻率/channel 的 token/s（7B int8, batch=1, 75% 損失率）

| 配置                  | 實效頻寬 | 7B   | 1B   |
| --------------------- | -------- | ---- | ---- |
| DDR4-3200×2ch         | 19.2     | 2.7  | 19   |
| DDR5-4800×2ch（現案） | 57.6     | 8    | 58   |
| DDR5-6400×2ch         | 76.8     | 11   | 77   |
| DDR5-8000×4ch         | 192      | 27   | 192  |
| LPDDR5x-7500 64bit    | 45       | 6.4  | 45   |
| GDDR6 256bit@16G      | 384      | 55   | 384  |
| HBM3 ×1 stack         | 614      | 88   | 614  |
| HBM3E ×4 stack        | ~3600    | ~514 | 3600 |

加顆粒有上限：封裝出口針 8–16、FHFL 槽位、等長。要破牆只剩 HBM。

## 5. 為什麼不做 ^2

d=2^14 的層權重 = d² = 2^28 int4 ≈ 128MB → sky130 SRAM ~1.5 Mbit/mm² 要 ~57
cm²，放不進。現案用的是 time-for-space：

```
passes/層/token = 2^28 / 16384 = 16384
時間/層/token  = 16384 × 50ns ≈ 0.82 ms（每晶粒）
```

總能量不變（仍 2^28 個 MAC），只有面積少三個量級。

## 6. 多任務/超長程的真實邊界

- 無狀態 pass + 外置狀態 → 天生可交錯/可長跑
- 但切換一次 = 重灌權重（受 DDR5 牆綁定）；超長程受 KV cache（64GB）與熱（12.5 W
  valid.）

## 7. 成本

- prototype cap $3000；所有 candidate `price_usd: null` + `*_quote_required`
- HBM
  silicon（Versal-HBM/MI300X/H100）超 cap；唯一可守 cap 的是自研 MPW 小晶粒路線
- 不自研芯片、拿現成 FPGA silicon 做卡（Versal/Agilex
  HBM）= 更快驗證、仍超 cap 風險

## 8. 當前這卡「變成」啥

42 TOPS INT8、12.5 W、64GB DDR5、FHFL 雙槽、雙基板 TBD、sense
chain 未實作。單查詢 7B ≈ 8
tok/s；batch≥180 才能吃滿算力。突破必須換 HBM，代價是 cap。
