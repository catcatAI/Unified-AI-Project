# hardware/ — 硬件工作區（三區地圖：研究 / 元件 / 組件）

> **一句話**：本目錄是統一AI專案的**硬件工作區**，按「研究區 / 元件區 / 組件區」三區放置，完成品與未完成品**分開放**。晶體管級版圖**不在 repo**，在
> `/home/cxuo/chip`；本機硬體偵測在 `apps/backend/src/core/hardware/`
> （目錄名撞車，與芯片設計無關）。本檔是硬件域的**唯一地圖**——「啥是啥、該放哪、哪些算完成」以本檔為準。

> ⚠️ **區性聲明（2026-10-09，與未進行的實體開發做區分）**：本工作區是
> **設計與設計驗證區**——只存放規格、設計圖、仿真、審計與打包文件；
> **未進行任何實體開發**（未下板、未打樣、未採購元件、未做任何實物量測）。本檔說的「done
> / 完成」一律指
> **L0 設計文件完成**（圖文自洽＋仿真可重現＋打包自含），**不等於**做出了實體；L1-L4 才是產品驗證流程。該聲明的程式可讀版在
> `edge_card_spec.yaml` 的 `development_stage` 欄位，未完成清單在
> `assemblies/done/edge_card/simulation_report.md` §6。

## 1. 三區結構與放置規則

```
hardware/
├── research/        研究區：推導分析、被取代的歷史檔（不承載定案數字）
├── components/      元件區：可複用零件（含芯片側元件）
│   ├── done/        完成品：來源齊、驗證過、可被組件打包複製
│   └── wip/         未完成：草稿/候選/被擋住——禁止宣稱完成、禁止被打包
│       └── chip/    芯片側元件（CIM 凍結草案、MVU header 候選）
└── assemblies/      組件區：產品級組合（板卡）
    ├── done/        完成組件：本層驗收定義全過，附打包含（複製自 components/done）
    └── wip/         未完成組件：概念/草稿級，不打包、不宣稱完成
```

| 區                 | 放什麼                                                          | 完成判準                                                           | 反例（該放別處）        |
| ------------------ | --------------------------------------------------------------- | ------------------------------------------------------------------ | ----------------------- |
| `research/`        | 推導分析（DERIVED_ESTIMATES）、被取代規格（mvu_reference_spec） | —（研究無「完成」）                                                | 定案數字、產品規格      |
| `components/done/` | 元件卡：外購件/標準件的事實+來源                                | `status: complete`、來源齊、關鍵欄位可被引用                       | 未選型的零件            |
| `components/wip/`  | 元件草稿/候選（芯片側在此子目錄）                               | —（明示 blocked/候選狀態）                                         | 已驗證事實（應升 done） |
| `assemblies/done/` | 產品規格+圖+仿真+打包                                           | 本層驗收定義全過（含層級註記）、打包清單只含 done 元件、附仿真報告 | 引用 wip 元件的「完成」 |
| `assemblies/wip/`  | 產品概念/草稿                                                   | —（概念級）                                                        | 定案數字、仿真結論      |

**打包規則（assemblies/done 的硬約束，由 `tests/unit/test_hardware_workspace.py`
鎖）**：

1. 完成組件必須有 `package_manifest.yaml`，列出複製進來的每個元件卡及其
   `source`（必須指向 `components/done/`）。
2. 元件卡從完成元件庫**複製**（copy）進組件包，不跨區引用——打包後自含。
3. **任何未完成元件不得被打包**：manifest 的 source 路徑含 `wip/` 即紅燈；
   `wip/` 下不得出現 `package_manifest.yaml`。
4. 複製件與來源必須逐位元一致（來源更新而未同步複製即紅燈）。
5. 不完整的東西**不得說完成**：done 元件卡必須
   `status: complete`；wip 元件卡不得寫 `status: complete`。

## 2. 現有檔案（status 欄位即真相）

### research/（研究區）

| 檔案                               | 是什麼                                      | 狀態                                                                    |
| ---------------------------------- | ------------------------------------------- | ----------------------------------------------------------------------- |
| `research/DERIVED_ESTIMATES.md`    | 對話推導的性能/鏈路整理（分析文件，非定案） | 以凍結值為輸入                                                          |
| `research/mvu_reference_spec.yaml` | 舊 MVU 參考規格                             | `superseded_reference_only`，`superseded_by: ai_compute_card_task.yaml` |

### components/（元件區）

| 檔案                                          | 是什麼                                    | 狀態                                            |
| --------------------------------------------- | ----------------------------------------- | ----------------------------------------------- |
| `components/component_registry.yaml`          | 零件註冊表（來源蒐集/驗證用，**未選型**） | `entries_are_not_selected: true`                |
| `components/done/compute_module_orin_nx.yaml` | Orin NX 16GB SO-DIMM 模組元件卡           | `complete`                                      |
| `components/done/m2_2230_module_class.yaml`   | M.2 Key-M 2230 介面等級元件卡             | `complete`（介面等級；**具體 SSD 選型在 wip**） |
| `components/done/cooling_fan_40mm.yaml`       | 40mm 4-pin PWM 風扇元件卡                 | `complete`                                      |
| `components/wip/chip/cim_freeze_draft.yaml`   | CIM 三個 pending 決策的 sky130 具體草案   | `draft_awaiting_acceptance_check`               |
| `components/wip/chip/mvu_header_spec.yaml`    | 使用者提供的 MVU header 候選              | `user_provided_candidate_not_frozen`            |
| `components/wip/m2_ssd_part_selection.yaml`   | M.2 SSD 具體選型（被散熱缺口擋住）        | `blocked`                                       |

### assemblies/（組件區）

| 檔案                                                                 | 是什麼                                                                                                                         | 狀態                                                     |
| -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------- |
| `assemblies/done/edge_card/edge_card_spec.yaml`                      | **小計算卡規格**：PCIe Gen4 端點（×1 主板 170mm + ×4 衍生 185mm 兩版都 L0 鎖定）、跑 Gemma 4 E2B 級、槽供電；附 5 張 L0 設計圖 | `draft_awaiting_acceptance_check`（L0 圖文全過，待人審） |
| `assemblies/done/edge_card/simulation_report.md`                     | 2026-10-09 整合仿真報告（電氣/熱/通訊/雜訊，含未完成清單）                                                                     | 與 spec 同步重跑                                         |
| `assemblies/done/edge_card/package_manifest.yaml`                    | 打包清單（複製自 components/done 的元件卡）                                                                                    | —                                                        |
| `assemblies/wip/ai_compute_card/ai_compute_card_task.yaml`           | AI 計算卡任務契約（自研矽大卡）                                                                                                | `environment_support_pending_acceptance_check`           |
| `assemblies/wip/ai_compute_card/angela_interface_freeze_packet.yaml` | 介面凍結包（eda_agent 唯一直接載入的規格）                                                                                     | `decision_verification_pending`                          |
| `assemblies/wip/ai_compute_card/concept_design.yaml`                 | 驗證用參數化 fixture（**不是**產品定案）                                                                                       | `environment_support_fixture`                            |
| `assemblies/wip/ai_compute_card/secondary_compute_draft.yaml`        | 權重更新路徑分析（每主張附出處、開放問題清冊）                                                                                 | `draft_awaiting_acceptance_check`                        |

> **兄弟產品線**：`assemblies/wip/ai_compute_card/`（自研矽大卡，概念級）與
> `assemblies/done/edge_card/`（外購模組小卡，L0 完成）互不回答問題——大卡 freeze
> packet 的 10 項 pending_decision
> **不由 edge_card 規格凍結或作答**。大卡整線未完成，故
> **不打包**（無 package_manifest）。

## 3. 與 `/home/cxuo/chip` 的邊界（三個合法接點，勿破壞）

兩個域是**不同層級的設計**，不是備份關係，互無文件副本（已掃描確認）：

- **本 repo** = 板卡/系統級（PCIe 卡、MVU、CIM 模型與驗證代碼）
- **`/home/cxuo/chip`** = 晶體管級標準格版圖（49 格 0/0，見該處
  `design/INDEX.md`）——這是**芯片元件的完成品庫**；repo 內
  `components/wip/chip/` 只放未完成的芯片側契約草案，完成的版圖正本不複製進來

接點（唯一三處，動之前先讀兩邊 INDEX）：

1. **共用 SPICE 模型**：repo 測試 `tests/ai/agents/test_eda_agent.py` 硬編碼讀
   `/home/cxuo/chip/.angela_repair/nfet_model_global.spice`（經
   `ANGELA_SKY130_SPICE_LIBRARY`；缺失時該測試 skip 而非假裝跑過）。
   **勿移動該檔。**
2. **chip → repo import**：`chip/.angela_repair/build_b01_v2.py` 以絕對路徑插入
   `apps/backend/src`，import `ai.hardware.cim_weight_strip`。
3. **常數血緣**：`ai/hardware/{cim_primitives,cim_weight_strip,cim_strip_reference}.py`
   內嵌的幾何/量測常數源自 chip 的 `DOT4`/`DOT4L` fixture（fixture 現居
   `chip/research/`，程式**只引數值、不讀檔案路徑**，故無路徑依賴）。

## 4. 代碼與運行時（不在三區內，但服務三區）

| 位置                                                  | 是什麼                                                                        | 域       |
| ----------------------------------------------------- | ----------------------------------------------------------------------------- | -------- |
| `apps/backend/src/ai/agents/specialized/eda_agent.py` | EDA/硬件代理（執行實驗、凍結包驗證）                                          | 代理代碼 |
| `apps/backend/src/ai/hardware/`                       | 代理函式庫：CIM 體系、MVU 參考模型、RTL 產生、sky130 SPICE 工具鏈與版圖驗證閘 | 代理代碼 |
| `apps/backend/src/core/tools/eda_tool_adapter.py`     | EDA 工具適配器                                                                | 工具     |
| `apps/backend/src/core/hardware/`                     | **本機硬體**偵測/調度（與芯片設計無關）                                       | 運行時   |
| `data/eda_runs/`                                      | EDA 運行工作區歷史（gitignored）                                              | 運行數據 |
| `scripts/sim_edge_card_{software,cycle,sweep}.py`     | 小卡 host-proxy / 離散事件 / 平衡掃描仿真                                     | 腳本     |
| `tests/unit/test_hardware_workspace.py`               | 三區結構+打包規則鎖                                                           | 測試     |

## 5. 歷史 / 失敗嘗試在哪（不要重建、不要當正本）

| 東西                                          | 在哪                                                                                                  | 為什麼                             |
| --------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ---------------------------------- |
| 已刪版圖嘗試 `cim_*_layout`/`cim_sense_chain` | 源碼已刪（**從未入 git**）；結論在 `tests/unit/test_cim_verify.py` 與 `cim_weight_strip.py` docstring | 四次失敗被 `cim_weight_strip` 取代 |
| MVU 舊規格                                    | `research/mvu_reference_spec.yaml`                                                                    | `superseded_by` 欄位已標           |
| EDA 運行殘留                                  | `data/eda_runs/`（gitignored）                                                                        | 實驗工作區，輸入 stub 當場生成     |
| 早年抽取殘檔                                  | `chip/research/a.ext`                                                                                 | 2026-10-04 已移出 repo             |

## 6. 名詞對照（ch 晶 vs 芯 分清楚）

文件英文統用 `die`/`package`/`chip`，中文務必分清，不可互換：

| 英文      | 中文     | 定義                                  | 關鍵參數                                     |
| --------- | -------- | ------------------------------------- | -------------------------------------------- |
| `die`     | **晶粒** | 單一晶圓切片，最小運算單元            | 1.5 mm² 目標、權重駐留 16 KB、16384 MAC/pass |
| `package` | **封裝** | 16 顆晶粒共封裝（wire-bond MCM 草案） | 權重 256 KB、d2d 48 pin、雙基板              |
| `card`    | **板子** | PCIe 加速卡                           | 4–16 封裝、L2 = 2×32GB DDR5、300 W           |
| `host`    | **主機** | PCIe 外                               | DDR5/PCIe 之外                               |

> 「die=晶片」是錯的：一顆對外晶片 = 一個封裝 =
> 16 顆晶粒。YAML 現有英文 key（`die_l1`、`dies_per_package`
> 等）被程式碼引用，保留不改，閱讀對照本表。
