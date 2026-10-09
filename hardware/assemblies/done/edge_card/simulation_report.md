# edge_card 整合仿真報告（2026-10-09）

> 範圍：兩版小板 **edge_x1（170mm）** 與
> **edge_x4（185mm）**，L0 圖文鎖定後的全量重跑。數字正本是
> `edge_card_spec.yaml`；本檔是「跑過什麼、結果、異常、沒跑什麼」的記錄。重跑命令在各節。

## 0. 變體差異（只差這四樣，其餘逐字相同）

| 項                  | edge_x1                          | edge_x4                                  |
| ------------------- | -------------------------------- | ---------------------------------------- |
| 邊緣手指            | x1（B=25.4mm，lanes1-3 NC）      | x4（B=39.4mm，lanes1-3 走線，PRSNT→B33） |
| PCB 長              | 170mm                            | 185mm（170+(39.4-25.4)=184→5mm 格 185）  |
| 鏈路 payload        | 1.969 GB/s/向                    | 7.876 GB/s/向                            |
| 冷載（3.35GB 權重） | 1.70s payload / 2.09s achievable | 0.43s payload / 0.52s achievable         |

供電、散熱路徑、風扇、支架、模組、M.2、時鐘、EMI 約束**兩版相同**（x4 的風扇隨手指 keepout 前移、排風道長 ~15mm——見「熱」節的 L2 驗證項）。

## 1. 電氣性能（analytical，L0；重跑=測試現算）

- 槽供電：12V 5.5A（66W）+ 3.3V 3.0A（9.9W），combined ≤75W（src_cem_rails）。
- 板預算：預設 25W 模式 35W cap、40W 解鎖 50W，皆 ≤66W（2.9A / 4.2A ≤5.5A）。
- PI：bulk cap 2000/1000/150µF 依 CEM；slew 0.1A/µs；12V
  excursion 走 Set_Slot_Power_Limit（src_cem_excursions）；3.3V 邏輯分配留 L2（open）。
- 驗證方式：`tests/unit/test_edge_card_spec.py::test_power_budget_sums_to_cap_within_slot`
  - `test_cem_rail_limits_recompute_from_source_facts`（2026-10-09 全綠）。
- **異常**：無新增。

## 2. 熱（analytical 預算 + 結構仿真；流體/CFD 未做）

- 路徑：40mm 風扇 → 鰭片 → TIM → 模組頂板 → 支架排氣；θ 預算 ≤2.0 K/W @25W /
  ≤1.25 K/W @40W =（90-40)/25、/40（測試現算鎖）。
- 環溫目標 ≤40°C、Tj 90°C sustained / 99°C 降速 / 105°C abs max。
- M.2 在風扇對側無直達熱路 → `open_items.nvme_thermal_path`（選型被擋）。
- **x4 差異**：風扇前移 ~15mm、排風道加長 → 該變體自己的 L2 驗證項（duct
  loss；不影響 x1）。
- 重跑：`pytest tests/unit/test_edge_card_spec.py -k thermal` 全綠（θ 現算）。
- **未做（明示）**：CFD/流阻、鰭片幾何、支架開孔風阻——皆 L2。
- **異常**：無新增。

## 3. 通訊（PCIe 鏈路）

- Gen4 x1：payload 1.969 GB/s/向（16 GT/s×128/130/8），achievable ≥1.6 GB/s（85%
  TLP，L3 實測）。x4：×4 線性（7.876 / 6.4）。
- 19 點平衡掃描（重跑）：decode **compute-bound**（3.56 tok/s @25W/32K，mac util
  100%，PCIe util ~1e-8）——鏈路在穩態 decode
  **不是**瓶頸；x1 唯一被用滿的地方是**冷載**（~100%
  duty，1.70s）；x4 解除該點。
- 側帶：PRSNT 綁帶（x1: A1-B17 / x4: B33）、PERST 後 rescan 發現流程、REFCLK
  100M host-source、WAKE/SMBus/CLKREQ/JTAG NC、禁熱插。
- 已知 open（L3）：C4 EP Gen4
  x1 訓練確認（c4_ep_link_speed）、C4+C7 併用（uphy_concurrency）、REFCLK 來源確認（ep_refclk_source）。
- **異常**：無新增（掃描與 10-07/10-08 記錄零漂移）。

## 4. 雜訊 / EMI / 時鐘

- 載板零本地時鐘；REFCLK 直通模組；M.2 refclk 由 C7
  refclk-out 出（零本地時鐘件）。
- 開關雜訊域僅 [fan-pwm,
  3.3V]；直接槽 3.3V 餵=零載板開關譜；若 L2 改本地 buck，switch
  node 遠離 REFCLK/PCIe 走線（clocking_and_noise）。
- 平面規則：PCIe 對與 REFCLK 路徑下禁参考平面分割（KiCad DRC 項）。
- L4 項目：發射 pre-compliance（acceptance.L4）。
- **未做（明示）**：實際頻譜、ESD 注入——皆 L2/L4。
- **異常**：無新增。

## 5. 重跑結果（2026-10-09）

### 5.1 平衡掃描（cycle sweep）

`.venv/bin/python scripts/sim_edge_card_sweep.py`

- 19 點（15 真模態 + 4 hw probe）**VERDICT: PASS**（22.2s）。
- baseline cross-check **3.56 vs 3.56 OK**；圖文所有數字（3.56、6.77、2.9-11.4%
  util range、1.70/2.09s load）與 spec 逐字重現。
- 15 tok/s 目標：**NONE**
  達標（compute-bound 結構性，與 10-07 記錄一致；這就是為什麼目標被標為預算而非實測）。

### 5.2 host-proxy（軟體仿真，非 L1）

`.venv/bin/python scripts/sim_edge_card_software.py`

- 硬閘**全 PASS 重現**：envelope 5.85GB ≤8/16、stream-bound [16.8,19.9] ≥15、eta
  0.491、load 1.7s ≤5s（projection 全部逐位重現）。
- host 錨點 14.3 GB/s / 499.8 / 12.06 vs 閒置日 18.0 / 905.2 / 13.19：**
  contention 漂移**（與 10-08 汙染記錄同類），資訊性數字，無閘依賴。已記入 spec
  `host_proxy_simulation.rerun_2026_10_09`。

## 6. 未完成清單（本層做不了、不得宣稱完成的）

| 項                                       | 層           | 擋誰                                      |
| ---------------------------------------- | ------------ | ----------------------------------------- |
| L1：Orin devkit 上 C4 EP 訓練 + DMA 驅動 | L1/L3        | c4_ep_link_speed、mailbox_protocol_freeze |
| SI/PI 場解算（85Ω、loss budget、眼圖）   | L2           | KiCad + 解算器                            |
| CFD/流阻與鰭片幾何                       | L2           | single_slot_thermal 閘                    |
| M.2 SSD 具體選型                         | L2           | nvme_thermal_path（→ wip 元件卡）         |
| 實測 BER/發射/ESD                        | L3/L4        | acceptance.L3/L4                          |
| x4 變體排風道驗證                        | x4 自己的 L2 | thermal_note（spec board_variants）       |

**原則**：以上任何一項未過，本目錄**不改口**為「產品完成」——工作區的「done」只指 L0 定義完成（圖文自洽+仿真重現+打包自含），L1-L4 是產品流程。
