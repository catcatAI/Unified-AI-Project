# hardware/ — 板卡級設計規格（統一AI專案的硬件域地圖）

> **一句話**：本目錄放**板卡/系統級**設計規格（YAML）。晶體管級版圖
> **不在 repo**，在 `/home/cxuo/chip`；本機硬體偵測在
> `apps/backend/src/core/hardware/`（與芯片設計無關，只是目錄名撞車）。本檔是硬件域的**唯一地圖**——「啥是啥、設計類檔案該放哪、哪些是歷史」以本檔為準；內容不複製到別處，避免雙份失同步。

## 1. 硬件相關位置一覽（分清楚啥是啥）

| 位置                                                                                                                                                                                                                                                                           | 是什麼                                                                                        | 域       | 狀態                 |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------- | -------- | -------------------- |
| `hardware/`（本目錄）                                                                                                                                                                                                                                                          | 板卡/系統級設計規格 YAML（PCIe AI 卡、MVU、Gen4×1 小計算卡）                                  | 設計規格 | 活的正本             |
| `apps/backend/src/ai/agents/specialized/eda_agent.py`                                                                                                                                                                                                                          | **EDA/硬件代理**（執行實驗、凍結包驗證的 agent）                                              | 代理代碼 | 活                   |
| `apps/backend/src/ai/hardware/`                                                                                                                                                                                                                                                | 代理的函式庫：CIM 體系、MVU 參考模型、RTL 產生、標準目錄、sky130 SPICE 工具鏈與版圖驗證閘     | 代理代碼 | 活                   |
| `apps/backend/src/core/tools/eda_tool_adapter.py`                                                                                                                                                                                                                              | EDA 工具適配器（工作區、工具偵測、artifact 落盤）                                             | 工具     | 活                   |
| `apps/backend/src/core/hardware/`                                                                                                                                                                                                                                              | **本機硬體**偵測/調度（GPU、HAL、compute matrix）                                             | 運行時   | 活，與芯片設計無關   |
| `data/eda_runs/`                                                                                                                                                                                                                                                               | EDA 運行工作區歷史（**gitignored**；每 run 含 manifest+輸入 stub+輸出）                       | 運行數據 | 可再生成，非設計正本 |
| `scripts/run_mvu_reference.py`、`hardware_intelligence_report.py`、`verify_hardware_tiers.py`                                                                                                                                                                                  | 硬件相關腳本                                                                                  | 腳本     | 活                   |
| `tests/unit/test_{cim_verify,cim_strip_reference,mvu_reference,rtl_generator,ai_card_reference,ai_card_interface_packet,card_architecture_audit,edge_card_spec,hardware_standards_catalog,eda_episode}*.py`、`tests/ai/agents/test_eda_agent.py`、`tests/core/tools/test_eda_tool_adapter.py` | 硬件域測試                                                                                    | 測試     | 活                   |
| `/home/cxuo/chip`（**repo 外**）                                                                                                                                                                                                                                               | 晶體管級 sky130 標準格版圖（`design/` 正確堆 / `research/` 研究堆，見該處 `design/INDEX.md`） | 版圖設計 | 活                   |
| `docs/PROJECT_MAP_GENERATED.md`                                                                                                                                                                                                                                                | 生成的目錄地圖（含本目錄統計）                                                                | 生成物   | 勿手改               |

## 2. 本目錄檔案（狀態欄位即真相）

| 檔案                                                  | 是什麼                                                                                                           | status 欄位                                                                                               |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `ai_compute_card/ai_compute_card_task.yaml`           | AI 計算卡任務契約（**取代** mvu reference spec）                                                                 | `environment_support_pending_acceptance_check`                                                            |
| `ai_compute_card/angela_interface_freeze_packet.yaml` | **介面凍結包**：分離「初始條件 vs Angela 設計決策」，`eda_agent.py` 唯一直接載入的規格                           | `decision_verification_pending`                                                                           |
| `ai_compute_card/cim_freeze_draft.yaml`               | CIM 三個 pending 決策的 sky130 具體草案（過 acceptance check 才算決策）                                          | `draft_awaiting_acceptance_check`                                                                         |
| `ai_compute_card/secondary_compute_draft.yaml`        | 以副計算為軸的權重更新路徑分析：每個主張附出處、9 項前論修正（P1-P9）、與 freeze packet/mvu 合併後的開放問題清冊 | `draft_awaiting_acceptance_check`                                                                         |
| `ai_compute_card/concept_design.yaml`                 | 驗證用參數化 fixture（**不是**產品架構定案）                                                                     | `environment_support_fixture`                                                                             |
| `ai_compute_card/component_registry.yaml`             | 來源蒐集/驗證用零件註冊表（**未選型**：`entries_are_not_selected: true`）                                        | 註冊表角色明示                                                                                            |
| `ai_compute_card/DERIVED_ESTIMATES.md`                | 本輪對話推導的性能/鏈路/成本整理（**分析文件**，非定案）                                                         | 以 yaml 凍結值為輸入                                                                                      |
| `edge_card/edge_card_spec.yaml`                       | **小計算卡規格**：PCIe Gen4×1 端點、跑 Gemma 4 E2B 級（Orin NX 16GB 基線、槽供電 ≤35W）       | `draft_awaiting_acceptance_check`                                                                         |
| `mvu/mvu_header_spec.yaml`                            | 使用者提供的 MVU header（`mvu_config.vh`）候選                                                                   | `user_provided_candidate_not_frozen`                                                                      |
| `mvu/mvu_reference_spec.yaml`                         | 舊 MVU 參考規格                                                                                                  | `superseded_reference_only`，`superseded_by: ai_compute_card_task.yaml`（保留僅供追溯，**無程式碼引用**） |

狀態欄位皆為 `*_pending` / `draft` / `candidate` —— **全部未定案**；定案流程以
`angela_interface_freeze_packet.yaml` 的驗收為準。

> `edge_card/` 是**兄弟產品線**（外購模組的小卡，近期產品），與
> `ai_compute_card/` 的自研矽大卡互不回答問題：大卡 freeze packet 的
> 10 項 pending_decision **不由 edge_card 規格凍結或作答**。

## 3. 與 `/home/cxuo/chip` 的邊界（三個合法接點，勿破壞）

兩個域是**不同層級的設計**，不是備份關係，互無文件副本（已掃描確認）：

- **本 repo** = 板卡/系統級（PCIe 卡、MVU、CIM 模型與驗證代碼）
- **`/home/cxuo/chip`** = 晶體管級標準格版圖（33 格 0/0）

接點（唯一三處，動之前先讀兩邊 INDEX）：

1. **共用 SPICE 模型**：repo 測試 `tests/ai/agents/test_eda_agent.py` 硬編碼讀
   `/home/cxuo/chip/.angela_repair/nfet_model_global.spice` （經
   `ANGELA_SKY130_SPICE_LIBRARY`；缺失時該測試 skip 而非假裝跑過）。
   **勿移動該檔。**
2. **chip → repo import**：`chip/.angela_repair/build_b01_v2.py` 以絕對路徑插入
   `apps/backend/src`，import `ai.hardware.cim_weight_strip`。
3. **常數血緣**：`ai/hardware/{cim_primitives,cim_weight_strip,cim_strip_reference}.py`
   內嵌的幾何/量測常數源自 chip 的 `DOT4`/`DOT4L` fixture（fixture 現居
   `chip/research/`，程式**只引數值、不讀檔案路徑**，故無路徑依賴）。

## 4. 歷史 / 失敗嘗試在哪（不要重建、不要當正本）

| 東西                                                                                             | 在哪                                                                                                       | 為什麼                                                                             |
| ------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| 已刪除的版圖嘗試 `cim_cell_layout` / `cim_array_layout` / `cim_group_layout` / `cim_sense_chain` | 源碼已刪（**從未入 git**）；結論寫在 `tests/unit/test_cim_verify.py` 與 `cim_weight_strip.py` 的 docstring | 四次失敗嘗試（word line 未分離、sense chain 不解碼等），被 `cim_weight_strip` 取代 |
| MVU 舊規格                                                                                       | `mvu/mvu_reference_spec.yaml`                                                                              | `superseded_by` 欄位已標                                                           |
| EDA 運行殘留（含 4 份相同 md5 的 PCB stub 輸入）                                                 | `data/eda_runs/`（gitignored）                                                                             | 每次實驗的獨立工作區；輸入 stub 由代理**當場生成**，無正本需求                     |
| 早年抽取殘檔                                                                                     | `chip/research/a.ext`                                                                                      | 於本 repo 根目錄拾獲，2026-10-04 已移出                                            |
| magic 執行殘留                                                                                   | `chip/.angela_repair/data/`                                                                                | 運行期資料                                                                         |

## 5. 設計類檔案放置規則（新增前先看）

| 類型                   | 放哪                                                                                               |
| ---------------------- | -------------------------------------------------------------------------------------------------- |
| 板卡/系統級規格        | `hardware/<子系統>/*.yaml`，**status 欄位必填**，被取代時填 `superseded_by`                        |
| 晶體管級版圖與版圖報告 | `/home/cxuo/chip`：通過三道閘門才進 `design/`，研究殘餘進 `research/`（見 `chip/design/INDEX.md`） |
| 代理/工具代碼          | `ai/agents/specialized/`、`ai/hardware/`、`core/tools/`                                            |
| 本機硬體偵測           | `core/hardware/`（**不要**把芯片設計放這裡）                                                       |
| EDA 運行產物           | `data/eda_runs/`（gitignored，勿當正本、勿提交）                                                   |
| 概念圖手稿             | 需要文字化時：圖 + 對應 SPEC 一起進 `chip/design/`，**概念不得進 `VERIFIED_COMPARE.md`**           |

## 6. 名詞對照（ch 晶 vs 芯 分清楚）

文件英文統用 `die`/`package`/`chip`，中文務必分清，不可互換：

| 英文      | 中文                               | 定義                                  | 關鍵參數（cim_freeze_draft / freeze_packet）                      |
| --------- | ---------------------------------- | ------------------------------------- | ----------------------------------------------------------------- |
| `die`     | **晶粒**                           | 單一晶圓切片，最小運算單元            | 1.5 mm² 目標、權重駐留 16 KB、16384 MAC/pass、L1 32 MB            |
| `package` | **封裝**（對外一顆「晶片」的實體） | 16 顆晶粒共封裝（wire-bond MCM 草案） | 權重 256 KB、262144 MAC/pass、d2d 48 pin、熱管+針腳母頭（雙基板） |
| card      | **板子**                           | PCIe 加速卡                           | 4–16 封裝、L2 = 2×32GB DDR5、300 W                                |
| host      | **主機**                           | PCIe 外                               | DDR5/PCIe 之外                                                    |

> 舊習慣「die=晶片」是錯的：一顆對外晶片 = 一個封裝 =
> 16 顆晶粒。YAML 內現有 key（`die_l1`、`dies_per_package`、`die_area_*`）是英文 key，保留不改（被程式碼引用）；閱讀時一律對照本表。
