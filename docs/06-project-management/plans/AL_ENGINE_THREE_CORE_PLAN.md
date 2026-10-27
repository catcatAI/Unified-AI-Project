# AL 引擎三核心審閱：誤判清單、拆庫判斷與行動計畫

> **任務來源**：`zzzz`（＝原 session 最後一則指令）——「研究、分析以下條件，看看有沒有誤判，並分析是否該開個子 git 庫放 AL 引擎（與現有散亂 AL 分開來）……都先不繼續執行，整理好計畫並記得分析。」
>
> **本文件的立場**：只做分析與計畫，不動代碼。所有「現狀」結論都是本輪實測（讀碼 +
> grep + 檔案檢查），不是引用既有宣稱。
>
> - 作者：Angela AI Development Team
> - 版本：7.5.0-dev
> - ANGELA-MATRIX：`[L3-L4] [βγ] [B] [L2]`
> - 日期：2026-10-25

---

## 0. 三句結論（先看這三句）

1. **三分法（AI 能／AL 活與時／記憶留）方向成立，但有 7 處需要修正**
   —— 最重要的兩處是：這套分類**與專案既有的五層分層契約（memory/knowledge/reasoning/learning/surface）沒有對齊**，以及它**把「目標句」寫得像「現狀」**（三條邊界今日全部被違反）。
2. **不建議現在開子 git 倉** ——
   AL 的邊界還沒畫出來（出站 9 處跨層 import、入站 62 個檔案依賴它），此時拆倉等於把糾結畫成 git 邊界。**先在單庫內做出「可拆」的條件（目錄 +
   import 門禁 + 契約），4 條觸發條件全數滿足再拆，且用 subtree
   split 保留歷史。**
3. **「散亂」的病因不是「同一個 git 倉」，是「沒有單一擁有者」**
   —— 同一個生命狀態散在 5 處、life_intensity 有 3 個獨立實例、約 3,600 行孤兒碼、ζ/η 兩個漂移指標從未被寫入。先清場、再收斂、後割邊；拆倉是最後一步，不是第一步。

---

## 1. 專案目前在什麼任務、什麼進度

### 1.1 git 上的在途工作（實測）

| 項                       | 狀態                                                                                                                                  |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| 最新 commit              | `85c4dcae1`（2026-10-24 15:59）`docs: surface-layer audit results; scores refreshed with the leakage verdict`                         |
| 最近 15 個 commit 的主題 | **全部**是 token-SNN 核心差距那條線：provenance census、wiki 評分修復、membrane readout A/B、LLM 對照組 chat template、學習曲線平台期 |
| **未提交（在途）**       | `.gitignore`(+`.xpu_runtime/`)、`ai/ed3n/token_snn.py`(+`resolve_device()`：xpu>cuda>cpu、禁 FP64)、`scripts/train_token_snn.py`      |
| **未跟蹤**               | `scripts/xpu_run.sh`、`scripts/restore_guc_firmware.sh`、7 個 `benchmarks/results/bench_20261023-*.json`                              |
| 分支 / remote            | 單一 `main` ← `github.com/catcatAI/Unified-AI-Project`；**無 submodule、無嵌套倉、無 worktree**                                       |
| 體積                     | `.git` 514M；工作區 32G（含 node_modules / data / models —— 與本題無關，別混進拆庫理由）                                              |

**判讀**：另一條支線正在做「給 SNN 上 GPU（Intel Arc XPU）跑 surrogate
BPTT」——正是上一輪報告（10-23
18:03）列出的三個岔路選項 1。**AL 這條線是平行支線，不該打斷它，也不該共用它的口徑。**

### 1.2 `angela.json` 是什麼

同一條 session（`ses_eaadd46e3ffedYNwBuG2wGtEoK`，標題「Angela 專案整合、重命名與代碼審查」）的匯出：3,305 則訊息，2026-10-19
→
10-25。最後的使用者指令就是本任務原文，並註明「你的工作已交由另一邊執行了」。該 session 之前的實體工作（per-user 改名
`POST /api/v1/identity/name`、persona 露茜法埃拉、模板示例進上下文）**已完成並提交**，與本題無衝突。

### 1.3 與本題直接相關的既有資產（不要重造）

| 資產                         | 位置                                                                                                                                                    | 對本題的意義                                                                                                                               |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| 五層分層契約 + 登記簿 + 門禁 | `docs/06-project-management/LAYER_SEPARATION.md`、`LAYER_REGISTRY.json`、`scripts/check_layer_separation.py`                                            | **本專案「邊界怎麼釘死」的既定做法**：文件 + 登記簿 + AST 門禁，不靠自律。AL 邊界應複製此模式                                              |
| 狀態動力學研究計畫           | `docs/06-project-management/plans/ANGELA_SELF_IDENTITY_STATE_DYNAMICS_PLAN.md`                                                                          | 已提出 H1–H3 干預假說與 E1 實驗（固定文本動狀態看行為翻轉）——**這正是 AL 引擎的驗收方法**                                                  |
| 主幹線盤點（🟢🟡🔴）         | `docs/architecture/backbone/ARCHITECTURE_BACKBONE.md` L820–871                                                                                          | 官方記錄了哪些模組「全庫無實例化」「無統一主幹線對接」                                                                                     |
| backbone 單例登錄            | `apps/backend/src/core/backbone/backbone.py`                                                                                                            | docstring 自述「取代 lifespan.py 中 ~130 個 `_get_*` 工廠」，已收 memory / state_matrix / emotion —— **AL 聚合器應該註冊進這裡，不要新造** |
| 單一檢查入口                 | `scripts/check_fact_gates.py`（edge/audit/chat/cluster/config/version/docs/modules/gates/hygiene/intelligence/benchmarks/layers/placement/definitions） | 新的 AL 門禁應成為其中一個域，而不是又開一支腳本                                                                                           |

---

## 2. 三分法審閱：站得住的部分

| 主張                                                                                        | 檢驗                                                                     | 判定                                     |
| ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ | ---------------------------------------- |
| AI＝當下能力、AL＝跨時間演化、記憶＝被時間留下的東西                                        | 三者職責互斥且互補，無重疊定義                                           | ✅ 成立                                  |
| 「AL 以時態為核心、狀態為條件」與 AI「相反」是刻意分工                                      | 概念清楚，且給出了可驗證的失敗模式（漂成「很會說話的別人」）             | ✅ 成立（但見 §3.6 的代碼現狀）          |
| 「先不加第四核心」                                                                          | 避免在契約未定前擴張分類                                                 | ✅ 謹慎，但需給量測層一個位置（見 §3.1） |
| 「AL 要收成一個可問責的引擎，輸出時間係數／漂移度量／修正參數，而不是另一套更會聊天的推理」 | **全文最重要的一句**，直接排除了「把 AL 做成第二個 LLM」這個最容易犯的錯 | ✅ 必須寫進契約的「非職責」              |
| 「接下來的工程問題是 AL 的輸入／輸出契約是什麼，它和 AI、記憶只交換哪些量」                 | 與實測一致：本專案缺的確實是契約，不是模組                               | ✅ 準確                                  |

---

## 3. 誤判清單（逐條，附證據）

### 3.1 【誤判・分類】三分法漏掉了本專案最活躍的第四塊：量測／治理層

最近 15 個 commit **全部**落在量測層（provenance census、benchmark 評分、pass
criteria、surface audit），而三分法裡沒有它的位置。硬把它塞進任何一格都會重演 §X
#267 之前「十一套智能評分」的病：**同一個詞在不同檔案指不同的量尺**。

- **修正**：三分法 = **運行時架構**（執行期只有三核心）；量測層 =
  **橫切關注**，不是第四個運行時核心，但在計畫中必須單列，並註明它不歸 AL 也不歸 AI 管。
- 「對齊／價值邊界掛在 AL」這句要拆兩半：**身份與方向的約束**（不宣稱未完成操作、不謊稱能力）→
  AL；**可驗證性**（門禁、基準、口徑）→ 量測層。混在一起 = 又一個雙義詞。

### 3.2 【誤判・分類】與既有五層分層契約沒有對齊

`LAYER_SEPARATION.md` 已定義五層（memory / knowledge / reasoning / learning /
surface），本句的「記憶」只是其中一層。若不聲明對齊關係，專案會同時有「五層」和「三核心」兩套分類，
`LAYER_REGISTRY.json` 與新 AL 契約各說各話 —— 這正是 `check_fact_gates.py` 的
`definitions` 域存在的原因（「一個定義、一個數字、一個地方」）。

- **修正**：契約文件裡放一張對照表 —— 三核心 × 五層 × 現有模組，明寫「knowledge 層不屬於三分法的『記憶』」「surface 層不屬於『AI 引擎的推理』」。

### 3.3 【誤判・證據】「Maturity L0–L11」被列為 AL 材料，但它今天是死碼

實測：`core/maturity/maturity_system.py` 的引用只有 `core/__init__.py` 的 lazy
export、 `tests/unit/test_smoke_imports.py`，以及它自己。**無生產實例。**
更糟的是前端另有一套完全無關的 L0–L11（`packages/shared-js/js/maturity-tracker.js`，以
`memory_count` 分級、存
`localStorage['angela_maturity']`），兩套同名階梯零共享。

- **修正**：把 Maturity 從「AL 材料」改列為「**待裁決項**」—— 要嘛接線成真的成熟度（前後端統一），要嘛刪除。**不要「搬」死碼**：搬進新引擎只會讓新引擎從假指標起步。

### 3.4 【誤判・證據】「有零件，還沒收成一個引擎」低估了幽靈指標的比例

零件其實分三態，而文案把三態混成一態：

| 狀態                       | 例子（本輪實測）                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **活的**                   | `DigitalLifeIntegrator`(1,326L)、`BiologicalIntegrator`(903L, 單例)、`AutonomousLifeCycle`(1,387L)、`MetabolicHeartbeat`(440L)、`EmotionSystem`(733L)                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| **幽靈（存在但從不生效）** | ① `update_zeta()` 只有定義（`state_matrix.py:386`、`state_matrix_adapter.py:296`），**零生產呼叫**，但 ζ 被 `chat_routes` / `prompt_builder` / `system_routes` / `websocket_manager` / `composer` 5+ 處讀取；② `η.structural_drift` 只序列化、**永不計算，恆為 0**，卻出現在 prompt 的 `angela.eta.drift`；③ `TemporalState.find_drift()`（318L 零依賴，真正能算漂移）**只有 test 呼叫**；④ `EmotionSystem.save_state()` 從未生效 —— `data/emotion_state.json` **不存在**，情緒不跨重啟；⑤ `data/state/` **是空的**，狀態矩陣從不存檔；⑥ DLI 的 `life_stats.age`/birth_time 不持久化 —— **「年齡」每次重啟歸零** |
| **死的（孤兒，3,280 行）** | `core/maturity/`、`core/life/evolution_engine.py`、`core/life/cyber_identity.py`、`core/life/self_generation.py`、`core/metamorphosis/soul_core.py`、`core/engine/angela_model_core.py`、`ai/lifecycle/memory_integration_loop.py`、`ai/lifecycle/behavior_feedback_loop.py`（後兩個被 `ARCHITECTURE_BACKBONE.md` 自承「全庫無實例化」）——**2026-10-25 裁決修正**：此列把 2 個**活的**（`cyber_identity`/`self_generation`，有實例化）誤列為死；最終 6 項已刪、2 項保留，見 Phase 1 完成記錄                                                                                                                     |

- **修正**：這不是文字問題，是**計畫風險**
  —— 若照字面「收成一個引擎」，會把恆 0 的漂移、從未觸發的情緒存檔、歸零的年齡一起收進去，然後新引擎「具備漂移度量與連續性」卻全無效果。
  **Phase
  1 必須先做幽靈指標裁決：真算，或從 prompt／context 拿掉。二選一，不許維持現狀。**

### 3.5 【漏項・證據】最大的一塊 AL 邏輯不在這些模組裡，而在聊天管線的編排

實測：`api/routes/chat_routes.py` **3,475 行**、`services/llm/prompt_builder.py`
**1,374 行**。後者在 L554–604 **自己建了 5 個公式 singleton（含
`LifeIntensityFormula`）** —— 也就是
**AI 層正在替 AL 算狀態**；前者 L710–847 把 bio / state_matrix /
life_essence 直接拌進 LLM context，L1537–1645 自建 `TemporalState` causal
bridge，L1592 把反饋餵回 emotion / DLI / ALC，L2321–2365 逐步套用 lifecycle /
intent / modality。

AL 狀態真正影響行為的匯流點是 `ai/meta/priority_negotiator.py` 的 **9 個 voter**
（lifecycle / emotional / intent / angela_emotion / causal / meta_calibration /
heartbeat / dli_state / abstain），在 `services/llm/router.py` 註冊 ——
**這已經是「AL → AI」的介面雛形，但它是隱性的、逐 voter 散落的**。

- **修正**：三分法的工程描述要加一句：**收斂 AL
  = 收狀態擁有者（搬類容易）＋ 收使用面（搬 step 編排才是主戰場）**。只搬類不搬使用面，等於新引擎建好了、狀態照舊在 chat_routes 被算。

### 3.6 【誤判・現狀】三條邊界（AI 不擁長期身份／AL 不存知識／記憶不決定我是誰）**今日全部被違反**

以現狀檢驗：

1. **AI 不擁有長期身份** → 違反。per-user 名字存在
   `core/system/config/identity.py`（**config 層**），persona 在
   `core/persona/`，而真正該表達連續性的 `ζ.identity_continuity`
   **從未被寫入**。結果：身份的「長期」既不在 AI 也不在 AL，是**空的**。
2. **AL 不直接存知識**
   → 違反方向相反。DLI 寫 4 個狀態檔、LifeEssence 寫 1.7MB、ALC 記錄 per-type 成功率（那是學習統計）；而本該負責「AL 決定進出記憶的速率」的
   `ai/lifecycle/memory_integration_loop.py` **從未實例化**
   —— 這條邊界**尚不存在**。
3. **記憶不決定我是誰**
   → 無規則可違反，因為根本沒有「什麼算核心身份」的判定規則。

- **修正**：三條要標成 **gate 目標（Goal）**，每條配一個可自動驗證的檢查（仿
  `check_layer_separation.py`
  的 AST 檢查），而不是寫成與現狀並列的描述句。否則讀的人會以為「已經分好了」。

### 3.7 【誤判・措辭】「AL 材料分散」的病因診斷偏了一半

文案隱含「分散 → 收斂到一個模組」的解法。但實測的病因是三件事，收斂只解第一件：

1. **無單一擁有者**（生命狀態散在 DLI.life_stats / ALC.phase /
   LifeEssence.傾向 / heartbeat.health / intensity×3 共 5 處）→ 收斂可解；
2. **指標從未接線**（ζ / η / find_drift）→ 收斂**解不了**，要接計算；
3. **死碼與雙份定義**（孤兒 3,280 行、雙 maturity 階梯）→ 收斂**解不了**，要刪或裁決。

- **修正**：計畫順序改為
  **清場 → 收斂 → 割邊 → （才談）拆庫**，而不是「先開倉再整理」。開倉不會讓死碼消失，只會把散亂複製一份到新倉。

---

## 4. 該不該開子 git 倉放 AL 引擎

### 4.1 結論

**現在不開。**
不是因為想法錯，是因為**拆庫的前提（乾淨邊界）尚未存在**，而造出這個前提本身就是計畫的 Phase
2–3。先拆等於把糾結畫成 git 邊界。

### 4.2 反對現在拆的六條實測理由

| #   | 理由                                                                                              | 證據                                                                                                                                                                                                                                                                                               |
| --- | ------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **出站有洩漏**：AL 反向依賴 AI／services／api 層                                                  | `digital_life_integrator.py:32,33`（→`ai.lifecycle`）、`:441`（→`ai.memory`）、`:442`（→`services`）、`:473`（→`api.lifespan`）、`heartbeat.py:20`（→`integrations`）、`proactive_interaction_system.py:19`（→`services.weather`）、`llm_decision_loop.py`（→`core.prompt_manager`）等 **共 9 處** |
| 2   | **入站耦合深**：拆出去後每次改動都要跨倉                                                          | **76 個檔案 import AL 集群，其中 62 個在 AL 目錄之外**（含 `api/lifespan`、`chat_routes`、`router`、`priority_negotiator`、backbone、大量測試）                                                                                                                                                    |
| 3   | **單一 import 根**：Python 端是 `apps/backend/src` 一個套件佈局（`core.*`／`ai.*`／`services.*`） | 拆倉必須先拆套件（pip install、版本、依賴、path 設定），否則 submodule 只是「另一個目錄」，**零收益、全成本**                                                                                                                                                                                      |
| 4   | **CI 與治理全是單庫假設**                                                                         | 7 個 workflow（`ci.yml`、`integration-tests.yml`、`codeql.yml`…）、`scripts/check_fact_gates.py` 單一入口、`scripts/gen_project_map.py`、`tests/test_version_consistency.py` 的版本一致性、AGENTS.md 的所有命令與 NOTE chain                                                                       |
| 5   | **證據鏈會斷**                                                                                    | 本專案用 `git log`/hash 做取證是制度（`MASTER_TASK_MAP`：每條宣稱要 commit hash + 檔案存在 + 內容相符）。跨倉後，一次 AL 改動會散成兩個 hash，追溯成本即刻上升                                                                                                                                     |
| 6   | **沒有第二個消費者**                                                                              | AL 今天沒有外部用戶、沒有第二個 app 依賴它 —— 拆倉的收益（獨立發布、獨立版本）**無人受益**                                                                                                                                                                                                         |

> ⚠️ **一個誘惑要擋掉**：`.git`
> 514M、工作區 32G 看起來「很大」，但那是 data／models／node_modules 造成的，**與 AL 無關**。拆 AL 倉解決不了體積問題，別把兩件事綁一起當理由。

### 4.3 什麼時候該拆（觸發條件，寫死以免事後找理由）

四條**全部**滿足才開倉：

1. **出站零跨層 import**：AL 目錄只 import `core.*` 基礎設施（config / utils /
   tracing / state_store），不碰 `ai.*`、`services.*`、`api.*`、`integrations.*`
   —— 由 AST 門禁保證；
2. **有單一狀態讀寫點與定義好的交換量**：AL 對外只透過一個 snapshot（時間係數、漂移、生命階段、健康、強度…）暴露，AI 與記憶**只能讀它**，不直接摸內部 5 處狀態；
3. **AL 有自己的測試子集可獨立跑綠**：`tests/core/life` + `tests/core/bio` +
   `tests/ai/lifecycle`
   - `tests/core/state`（目前 13+16+164+52 ≈ 245 個
     `def test`）能單獨收集、單獨跑綠；
4. **出現第二個消費者或獨立發布需求**：第二個 app／外部庫要復用 AL，或 AL 需要獨立的 release
   cadence。

**拆的順序**（真要拆時）：`git subtree split`（保留歷史，單庫 CI 不斷）→ 獨立倉 + 自己的 CI
→ 主倉以 subtree/submodule 引回。**不要**開新倉複製代碼 —— 那會製造雙份維護，正是今日「散亂」的成因被複製一次。

### 4.4 四個方案比較

| 方案                                                                                                                                     | 成本                                         | 收益                                           | 判定                                        |
| ---------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- | ---------------------------------------------- | ------------------------------------------- |
| **A. 單庫內硬邊界**：`core/al/`（或維持目錄、只加門禁）＋ import AST 檢查（仿 `check_layer_separation.py`）＋ `AL_CONTRACT.md` ＋ 登記簿 | 低；CI／測試／證據鏈全不動                   | 立刻得到「誰能碰誰」的強制約束；達成 §4.3 條件 | ✅ **首選**                                 |
| **B. git subtree**：在單倉內把 AL 放成可整段拆出的子樹                                                                                   | 中；需維護目錄紀律                           | 保留隨時可拆的能力與完整歷史                   | 🟡 **A 的後續步驟**，不是第一步             |
| **C. submodule／獨立倉**                                                                                                                 | 高；CI、測試收集、版本治理、雙倉同步全要重做 | 獨立發布、獨立版本                             | ⛔ **現階段不做**；滿足 §4.3 四條件後再啟動 |
| **D. 另開新倉複製 AL**                                                                                                                   | 高                                           | 無                                             | ❌ **不做**：歷史斷裂 + 雙份維護 + 散亂×2   |

### 4.5 一句話回答原問題

> 「是否該開個子 git 倉放 AL 引擎（與現有散亂 AL 分開來）？」
>
> **該分開的是「邊界」，不是「倉」。**
> 今天拆倉分開的是目錄，不是散亂 ——散亂的原因是 5 處狀態沒有單一擁有者、2 個漂移指標沒接線、3,280 行死碼沒裁決。先用方案 A 把邊界做成**可被機器執行的約束**，等四條觸發條件全滿，再用 subtree 無痛切倉。

---

## 5. 計畫：做哪些、怎麼做

> 原則：**不打斷**另一條支線（token-SNN /
> XPU）；**不新造**聚合器（註冊進 backbone）；
> **不把 AL 做成另一個 prompt 層**；每個 Phase 都要有機器可驗的收尾，不接受「做完了」三個字。

### Phase 0 — 對齊定義（0.5 天，本文件即交付物）

- **做**：把三核心 × 五層分層 × 現有模組的對照表寫成契約草案；明確 AL 的**非職責**（不存知識、不做當下推理、不寫 prompt、不長駐 LLM）。
- **產出**：本文件 §2–§4；後續轉正為
  `docs/06-project-management/AL_ENGINE_CONTRACT.md`。
- **驗**：與 `LAYER_SEPARATION.md` 無衝突詞（同一個詞不得有兩種定義）。

### Phase 1 — 清場：裁決死碼與幽靈指標（1–2 天，**先做**）

- **做**：
  1. **孤兒裁決表**（8 項，逐項「接線 or 刪」，附理由）：`core/maturity/`（含前端重複階梯）、
     `evolution_engine`、`cyber_identity`、`self_generation`、`soul_core`、`angela_model_core`、
     `memory_integration_loop`、`behavior_feedback_loop`。
  2. **幽靈指標二選一**：`ζ`（4 個子指標）、`η.structural_drift`、`find_drift()`、情緒跨重啟、`life_stats.age`
     —— 每項決定「接上真計算」或「從 prompt/context 移除」，
     **不許維持恆 0 卻照常展示**。
  3. **去重**：`LifeIntensityFormula`
     3 個獨立實例（`autonomous_life_cycle:169`、
     `cyber_identity:207`、`prompt_builder:576`）→
     1 個單例；`prompt_builder:554–604` 同款 5 個重複 singleton 一併處理。
- **怎麼做**：逐項小 PR，每項都帶「刪了會不會有人疼」的證據（grep 引用 + 測試）。
- **驗**：`pytest tests/ apps/backend/tests/`
  全綠；`python3 scripts/check_fact_gates.py`
  全域通過；記錄行數變化（目標：孤兒 3,645 行 → 0）。

#### ✅ Phase 1 完成記錄 — 孤兒裁決（2026-10-25）

**裁決結果：8 項中 6 項刪、2 項留；前端另 1 項留（判據更正）。**

| #   | 項目                                       | 裁決 | 證據（刪除前實測）                                                                     |
| --- | ------------------------------------------ | ---- | -------------------------------------------------------------------------------------- |
| 1   | `core/maturity/`（2 檔，105L）             | 刪   | 生產引用僅 `core/__init__` lazy export 與 smoke 測試；無實例化                         |
| 2   | `core/life/evolution_engine.py`（177L）    | 刪   | 生產零引用；僅 2 個測試檔                                                              |
| 3   | `core/life/cyber_identity.py`（765L）      | 留   | `core/autonomous/__init__.py` 真實例化；`test_version_consistency.py` 依賴             |
| 4   | `core/life/self_generation.py`（778L）     | 留   | 同上（`core/autonomous/__init__.py` 兩處實例化）                                       |
| 5   | `core/metamorphosis/soul_core.py`（335L）  | 刪   | 生產零引用（`create_soul_core` 的歷史陷阱已改由 `config/identity.py` 承接）            |
| 6   | `core/engine/angela_model_core.py`（172L） | 刪   | 生產零引用；僅 3 個測試檔                                                              |
| 7   | `ai/lifecycle/memory_integration_loop.py`  | 刪   | 「全庫無實例化」＋ `CODE_AUDIT_DECISIONS_2026-10-13` §5 已裁「不接線」                 |
| 8   | `ai/lifecycle/behavior_feedback_loop.py`   | 刪   | 生產零引用；`ai/lifecycle/__init__` 僅 re-export                                       |
| 9   | 前端 `maturity-tracker.js`（365L）         | 留   | **判據更正**：有真實接線（`app.js:723` 實例化、`app.js:244-246` 掛 WS/stateMatrix、    |
|     |                                            |      | `plugin-manager.js:515` 暴露、兩 `index.html` 載入）。原判據「`sync_shared_js.py` 閘會 |
|     |                                            |      | exit 1」經實測**不成立**（移走 source 後 `--check` 與 vendor 模式皆 exit 0）           |

**執行方式**：直接刪除，未走 `09-archive/` 歸檔——實測兩個 archive 目錄內 `.py`
檔數 = 0（專案無代碼歸檔慣例），git 歷史即可復原；風險表 #1 的 `git mv`
建議據此偏離並記錄。

**行數變化**：生產 `apps/backend/src` **−1,796 行**（含 3 個 `__init__`
導出清理 59 行）、測試 **−1,313 行**，合計
**−3,109 行**。原盤點的 3,280 行孤兒中，1,543 行屬保留的 `cyber_identity` +
`self_generation`，故實際可刪 = 1,737 行生產碼 + 1,271 行測試碼 + 導出清理。前端
`maturity-tracker.js` 365 行保留（合計剩 365 行孤兒 → 目標 3,645 →
365，保留項皆有活接線）。

**連帶清理**：`core/__init__.py`（maturity 4 + soul 7 條 lazy export 與
`__all__` 項）、`core/metamorphosis/__init__.py`（soul import 塊與
`__all__`）、`ai/lifecycle/__init__.py`（2 import + 2 `__all__` +
docstring）、4 個測試檔整刪 + 3 個測試檔改寫（`test_smoke_imports`、
`test_config_coverage`、`test_b8_bug_fixes`）、 `check_fact_gates.py` identity
sources 與 `ham_manager.py` 註解各 1 處。

**文件同步**（存活文件，歷史/帶日期文件不動）：`MODULE_MAP.md`、
`ANGELA_FULL_ARCHITECTURE.md`、`ARCHITECTURE_BACKBONE.md`（含更正proactive「全庫無實例化」舊標記）、`THREE_AXIS_SCALEUP.md`、
`PROJECT_OVERVIEW.md`、`DETERMINISM_CLASSIFICATION.md`。

**驗證**：受影響測試 346 passed / 2 skipped；`core`、`ai.lifecycle`、
`core.metamorphosis` 導入正常（未知名稱回 `_SubmoduleSentinel` 是既有設計）。

#### ✅ Phase 1 完成記錄 — 幽靈指標二選一（2026-10-25）

**裁決：5 項 —— 2 項移除展示（真算排入 Phase
2）、1 項保留待接、1 項實測證實已接、1 項列 Phase 2 持久化；同族的
`η.success_rate` 一併處置。**

| #   | 項目                     | 裁決                               | 證據（本輪實測）                                                                                                                         | 動作                                                    |
| --- | ------------------------ | ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| ①   | `ζ` 四個子指標           | **移除展示**，真算排 Phase 2       | `update_zeta()` 零生產呼叫；值恆為凍結預設（`memory_depth` 0.6、`identity_continuity` 0.75 等）                                          | `chat_routes` 與 `prompt_builder` 的軸迴圈拿掉 `zeta`   |
| ②   | `η.structural_drift`     | **移除展示**，Phase 2 先定義來源   | 全庫只有序列化與 `from_dict`，無任何計算者；prompt 曾印 `Structural drift: 0.00`、儀表板曾印 `drift=0.0000`                              | prompt／`/api/context/summary`／repl 三處改為「未觀測」 |
| ②b  | `η.success_rate`（同族） | **移除展示**（原未列入，但同區塊） | 恆為預設 `1.0`，而 `execution_count` 生產恆 `0`（模組只註冊、從不執行）→ 曾印 `Success rate: 100.0%`，比恆 0 更嚴重                      | `execution_count == 0` 時回 `None`，不渲染              |
| ③   | `find_drift()`           | **保留待接**（不刪）               | 318 行零依賴、真能算值漂移，但只有 test 呼叫                                                                                             | 無程式碼變動；交給 Phase 2 給 `ζ` 用                    |
| ④   | 情緒跨重啟               | **已接，結案**                     | `apps/data/emotion_state.json` 於 2026-10-25 16:55 更新；`emotion_system.py:265/523` 呼叫 `save_state()`；`lifespan.py:717` adopt 舊狀態 | 無改動；Phase 2 清單中該項標為已完成                    |
| ⑤   | `life_stats.age`         | **列 Phase 2 持久化**              | `get_age()`／`get_life_summary()` 只在 DLI 內部與示範日誌使用；`birth_time` 無持久化 → 每次重啟歸零；prompt/context 本就未展示 age       | 無展示可移除；`age` 已在 Phase 2 `ALState` 欄位清單     |

**執行偏離（記錄，不是照抄）**：原計畫寫「`η.drift` 調用已存在的
`find_drift()`」——**不成立**。`find_drift(axis, field, expected, threshold)`
量的是「單一欄位對期望值的偏離」，`η.structural_drift`
要的是「模組組成的變化」，兩者不同物，硬接會得到一個語義錯的數字。因此改為「Phase
2 先定義 η.drift 的觀測來源，再接」，`find_drift()` 保留給 `ζ` 的值漂移。

**單一判定點**：`core/engine/eta_axis.py::measured_eta_metrics()` ——「**未觀測 =
`None`，絕不寫 0.0 / 1.0**」。`chat_routes` 與 `context_routes`
共用它；prompt 端遇 `None` 不渲染該行，儀表板顯示 `n/a`，repl 顯示
`n/a`。判定寫在一個地方，就不會有第六個消費者各自 `get(..., 0)` 把缺值填回 0。

**同族殘留（明確不在本輪）**：`websocket_manager` 與 `system_routes`
仍原樣匯出矩陣的 `zeta`
值 —— 那是**矩陣的忠實傾印**，不是替讀者詮釋；正解是 Phase
2 在來源寫真值，而不是在 6 個消費者各過濾一次。prompt 與 context 是會把數字寫成「當前狀態」的地方，所以先修這兩處。

**驗證**：新增 `tests/api/test_state_context_honesty.py` 8 條（`None`
契約、ζ 不入 LLM context、prompt 遇未觀測不渲染、已觀測仍渲染）；相鄰測試
`test_prompt_builder` + `test_formula_behavioral_impact` +
`test_context_summary_recent_count` + `test_eta_axis` 共 **84 passed**；flake8
0。

#### ✅ Phase 1 完成記錄 — 公式單例化去重（2026-10-25）

**交付**：一個公式一個實例，讀與寫分離。

| 公式                        | 實例數（前 → 後） | 站點                                                                     |
| --------------------------- | ----------------- | ------------------------------------------------------------------------ |
| `LifeIntensityFormula`      | **3 → 1**         | `autonomous_life_cycle:169`、`cyber_identity:207`、`prompt_builder:576`  |
| `ActiveCognitionFormula`    | **3 → 1**         | 同上三處                                                                 |
| `CDMCognitiveDividendModel` | **4 → 1**         | ALC、`prompt_builder:594`、`router:924`（memory_coordinator 的第四本帳） |
| `HSMFormulaSystem`          | 2 → 1             | ALC、prompt_builder                                                      |
| `NonParadoxExistence`       | 2 → 1             | ALC、prompt_builder                                                      |

**等價性證據**：5 個 `*_config`
鍵（`life/ac/cdm/hsm/npe_config`）全庫只出現在 ALC 的 `self.config.get(...)`
查詢處，**無任何設定檔定義它們** → 一律 `None` → `X(config=None)` ≡
`X()`（`self.config = config or {}` + `get(key, default)`
全走預設）。單例化零行為差異；per-instance 調參通道隨之移除，未來調參走
`magic_numbers`/`llm_param`（HSM 本來就是這麼做的）。

**讀寫分離（歸一的安全前提）**：三實例原本各養各的狀態，prompt 用的是一份「從沒人餵過」的私有副本；**若直接歸一而不改讀法，prompt 的讀取會變成污染共享狀態的第二條寫路徑**——違反契約 §9。因此：

- `LifeIntensityFormula.peek_life_intensity()`：零寫入。時間積分特別拆出
  `_preview_time_integral()`——`calculate_time_integral()` 會
  `accumulated_gap_integral +=` 並推進
  `last_calculation`（讀會切斷寫者的累積窗口），peek 只預覽、不入帳、**不動時鐘**。
- `CDMCognitiveDividendModel.peek_life_sense_output()`：不 append
  `outputs`/`conversion_history`、不長 `total_output`、不觸發 output callbacks。
- HSM／ActiveCognition／NonParadox 的 `calculate_*` 經
  **AST 遞歸純度檢查**（沿 self 方法呼叫鏈掃寫入）確認純 → 直接共享，無需 peek。
- prompt 的 5 條公式行改走上述唯讀路徑；ALC、cyber_identity、router 改用各模組的
  `get_*()` 單例。

**順帶查到的既有事實（未改，屬展示裁決）**：prompt 的 CDM 行從不呼叫
`calculate_consumption()`，`resource_consumed` 恆 0 → 該行 `amount` 一直顯示
`0.00`。若要修，應連「這個數字該不該展示」一起裁（幽靈指標家族）。

**行為變更（有意，記錄）**：`cyber_identity.initialize()`
原本每次重建公式實例（身份重啟歸零公式狀態）；歸一後只是取得共享實例——知識與觀察者狀態屬於「這一條生命」，不因哪個子系統重新初始化而歸零。

**驗證**：新增 `tests/core/test_formula_singletons.py`
9 條（三站點同一物件、重複取得同一、peek 六項狀態前後不變、calculate 仍記帳的正控制、prompt 五行端到端零寫入）；相鄰 10 個測試檔
**198 passed**；flake8 0、black 過（router/chat_routes 各有 1 個 **既有**
hunk 在 HEAD 同樣不合，非本輪所觸，未動）。

### Phase 2 — 收斂：單一狀態面（2–4 天）

- **做**：
  1. 定義 **`ALState` snapshot
     schema**（JSON，欄位建議：`life_phase`、`health`、
     `intensity`、`drift{zeta,eta}`、`time_coefficients`、`age`、`emotion`、
     `updated_at`、`source`）—— 這就是「AL 與 AI／記憶交換的量」，寫進契約。（原建議含
     `maturity`，已依契約 §3 裁決**不進 schema**：後端階梯已刪、前端階梯與 AL 無關。）
  2. **接上真計算並恢復展示**：`ζ` 由 `TemporalState`
     的 trend/anomalies 驅動（Phase 1 已先從 prompt/context 拿掉，真值到位後在
     `chat_routes` 與 `prompt_builder` 兩處軸迴圈加回）、`η.drift`
     **先定義觀測來源再接**（語義應為「模組組成的變化」，不要用
     `find_drift()`，它量的是單一欄位對期望值的偏離 —— 見 Phase
     1 完成記錄的執行偏離）、`age` 改為持久化。恢復展示只需改
     `measured_eta_metrics()` 一個地方。 **情緒 `save_state()` 已於 Phase
     1 實測確認真正落盤（檔案 2026-10-25 16:55 更新、lifespan
     adopt 舊狀態），本項無需再做。**
  3. **聚合器註冊進
     `core/backbone`**（已收 memory/state_matrix/emotion，補 DLI／ALC／heartbeat／emotion 的持久化），**不新建**
     aggregator。
  4. **實作** retention/decay policy 介面（契約 §10）—— 舊候選
     `memory_integration_loop` 已於 Phase
     1 刪除，「恢復或廢棄」變成「新建」，需按 §10 介面從頭實作。
- **怎麼做**：schema 先行（文件 + 測試），再逐欄接計算；每接一欄補一條測試。
- **驗**：
  - 狀態跨重啟保留（`emotion_state.json` 已於 Phase 1 實測確認存在且會更新；剩
    `age` 每次重啟歸零，持久化修完後應跨重啟可驗）；
  - **干預測試**：沿用 `ANGELA_SELF_IDENTITY_STATE_DYNAMICS_PLAN`
    的 E1 方法 ——固定同一段文本、只動 snapshot 欄位，看 `resolved_by`
    是否指名到對應 voter、行為是否可重複翻轉。這是「AL 狀態不是提示詞裝飾」的唯一有效證明。

#### ✅ Phase 2 item 1 完成記錄 — ALState schema 與讀路徑（2026-10-27）

**交付**：`apps/backend/src/core/life/al_state.py`（schema + 時鐘 + 唯讀快照）＋
`tests/core/test_al_state.py`
25 條。schema 先行，本 commit 不接任何新計算——每欄接真計算按計畫逐項、每項一 commit。

- **8 欄 schema**（契約 §3.2）落成 `FIELD_CLASSES`：`born_at`/`ticks`/
  `life_phase`=invariant、`health`/`emotion`=fast、`intensity`/`tendency`
  =slow、`drift`=derived；`maturity` 依 D9 不進 schema。
- **I9 歸因**：`ALSnapshot.as_dict()` 必含 `version` + `effective` + 分量 +
  `weights` + `source`，每欄 `source` 記 provenance、未觀測即 `None`。`weights`
  v1 =
  `{ai:1.0, user:0.0, group_fast:0.0, group_slow:0.0}`（D7 群體留槽位）；`effective`
  與分量恆 `None`——參數層一階濾波（§7.2）尚未接線，D11 未觀測不寫假數。
- **I1/I2**：`validate_weights()` 驗 `Σw = 1 ± 1e-6` 與
  `w_self ≥ al_w_self_min`（`threshold_value`
  配置鍵、預設 0.5＝自己至少佔一半）； `get_al_state()` 出口呼叫
  `validate_snapshot()`，違反即拋（boot 失敗語意）。
- **I3 機械保證**：`_persist()` 對任何 `derived` 鍵直接拋
  `ALValidationError`——drift 落盤在結構上不可能，不靠「記得別寫」。
- **單一時鐘（§4）**：`init_clock()`
  先讀檔、有即沿用（跨重啟**不得以當前時間重建**，§4.4）；`advance_tick()`
  每次推進落盤；缺檔 → `(None, None)`（D11），讀路徑不偷寫。
- **讀路徑（§9）**：core 側單例直接讀——`intensity` ←
  `peek_life_intensity()`（Phase 1 的唯讀路徑）、`tendency` ←
  `get_all_blended_tendencies()`；實例握在 api 側的 `life_phase`/
  `health`/`drift` 走 provider 登記簿 `register_al_source()`（只收
  `PROVIDABLE_SOURCES` 三名，打錯字直接拋），item
  3 由 lifespan 統一註冊——AL 不出站伸手。
- **`emotion` v1 恆 `None`**：情緒實例在 `ai/alignment`，AL 出站 import `ai.*`
  即 I8 違規（Phase 3 要修的 9 處，不新增第 10 處）；`emotion` 不在
  `PROVIDABLE_SOURCES`，登記也登不進來，等 §8 `submit_event` 事件通道。

**驗證**：25 條測試全過——含 I8 自檢（AST 掃模組 import 只有 stdlib +
`core.*`）、跨重啟 `born_at`/`ticks` 不歸零、I3 拒寫、來源故障降級
`None`；相鄰 4 檔合計 **55 passed**；flake8 0、black 過、 `check_fact_gates.py`
ALL PASS。

#### ✅ Phase 2 item 2a 完成記錄 — age 與單一出生時鐘（2026-10-27）

**根因**：`LifeStats`（DLI）與 `SelfModel`（cyber_identity）都是
`default_factory=datetime.now`——每次重建＝新生：`age`
每次重啟歸零、身份自述「我诞生于…」每次重啟漂移。全庫兩個互不同步的出生時鐘，違§4「單一時間基準」。

**修**：`al_state.birth_datetime()`——§4 單一時間基準的 `datetime`
視圖（首次呼叫起鐘持久化、其後一律沿用檔案裡的 `born_at`）。DLI 改
`LifeStats(birth_time=birth_datetime())`、cyber_identity 改
`self_model.birth_date = birth_datetime()`。cyber_identity 屬同根因擴充：計畫點名 DLI，但兩個出生鐘只修一個等於單一時鐘沒做成。

**驗**：`tests/core/test_al_state.py` +2（把時鐘凍結在 1970 → 兩個物件的 birth
**精確等於**持久化值、`age > 1000` 天；舊行為是 `now - now`
恆 0）；相鄰 5 檔合計 **70 passed**；flake8 0、black 過。

### Phase 3 — 割邊：把 AL 從 AI 層拔出來（3–5 天，**主戰場**）

- **做**：
  1. `prompt_builder` 不再自建
     `LifeIntensityFormula`，改讀 snapshot；ζ/η 文字注入改由 snapshot 供應（消除「AI 層替 AL 算狀態」）。
  2. `chat_routes` 的 `_ctx_*` AL 讀取收斂成一個
     `_ctx_al_state()`；L1537 的 TemporalState
     bridge 移入 AL 側、對外只留查詢介面。
  3. `priority_negotiator` 的 9 個 AL
     voter 改讀同一個 snapshot（今日逐 voter 散落讀鍵）。
  4. **新增 import 門禁**（仿 `check_layer_separation.py`）：AL 目錄禁
     `ai.*`／`services.*`／
     `api.*`／`integrations.*`；AI 側禁直摸 AL 內部狀態、只能
     `get_al_state()`。併入 `check_fact_gates.py` 新域 **`al`**。
- **驗**：新門禁 0 violations；`flake8`/`black` 乾淨；全 testpaths 綠；
  `gen_project_map.py --budget 10000` 不超標。

### Phase 4 — 拆庫評估（0.5 天，Phase 3 之後才做）

- **做**：對照 §4.3 四條觸發條件逐條打分（是／否 + 證據）。
- **結果 A**：四條全滿 → 走 §4.3 的 `git subtree split` 流程，獨立倉 +
  CI + 引回。
- **結果 B**：未全滿 → 本文件記錄「已評估、不拆」及缺口，附下次複評條件（不要無限期懸著 ——按
  `check_open_gates.py` 的慣例，臨時判斷要寫明拆除理由與複評條件）。

### 5.x 明確不做的事（清單）

- ❌ 不開新倉複製 AL 代碼（方案 D）。
- ❌ 不把 AL 做成另一個 LLM／prompt 層（契約明寫「非職責」）。
- ❌ 不新造第二個聚合器（backbone 已在，註冊即可）。
- ❌ 不把量測／治理層塞進 AL（見 §3.1）。
- ❌ 不在拆庫前先搬代碼（搬了也白搬，邊界還會再動一次）。
- ❌ 不動另一條支線的在途工作（XPU / token-SNN 未提交檔）。

---

## 6. 風險與開放問題

| #   | 風險／問題                                                                                                     | 影響 | 建議處理                                                                                          |
| --- | -------------------------------------------------------------------------------------------------------------- | ---- | ------------------------------------------------------------------------------------------------- |
| 1   | Phase 1 刪孤兒可能刪掉「將來要用」的東西                                                                       | 中   | 已處置（2026-10-25）：直接刪——兩個 `09-archive/` 目錄內 `.py` = 0，無代碼歸檔慣例；git 歷史可復原 |
| 2   | 三核心口徑與既有五層口徑並存期的混亂                                                                           | 高   | Phase 0 對照表 + `definitions` 域監控同名雙義                                                     |
| 3   | `chat_routes` 3,475 行的 step 編排重排，回歸面大                                                               | 高   | Phase 3 分步小 PR，每步跑干預測試 + 全測試                                                        |
| 4   | 兩條支線同時改 `chat_routes` / 狀態檔 → 衝突                                                                   | 中   | 與另一邊先對齊改動範圍（本文件先作為共識底稿）                                                    |
| 5   | 「拆倉」被日後重新提出卻沒有判據                                                                               | 中   | §4.3 四條件已寫死；複評走 `check_open_gates.py` 的登記慣例                                        |
| 6   | 開放問題：AL 狀態的**時間係數**由誰調參？（半衰期、固化速率、修正參數集的學習）                                | 待定 | 契約 Phase 0 先定「誰擁有參數」，調參演算法留到 Phase 2 之後另立計畫                              |
| 7   | 開放問題：多使用者時 AL 狀態是 per-user 還是 per-process？（身份已是 per-user，生命狀態目前是 process-global） | 待定 | Phase 2 定 snapshot 時一併決定，建議 snapshot 帶 `user_id` 維度                                   |

---

## 7. 附錄：本輪實測數據

| 指標                                                          | 數值                                                                                                                                                                                                             |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AL 相關總行數（不含聊天管線接線）                             | ≈ 26,000+ 行 / 9 個集群                                                                                                                                                                                          |
| `core/life/`                                                  | 6,540L / 14 files                                                                                                                                                                                                |
| `core/bio/`                                                   | 8,734L / 26 files                                                                                                                                                                                                |
| `core/engine/state_matrix.py` + `eta_axis.py` + `core/state/` | 1,767 + 472 + 1,873 = 4,112L                                                                                                                                                                                     |
| life_intensity 公式族                                         | 2,670L（3 個獨立實例）                                                                                                                                                                                           |
| `ai/lifecycle/`                                               | 2,873L / 7 files（其中 3 個無生產實例；Phase 1 刪 2 個後 = 5 files）                                                                                                                                             |
| `core/state/temporal.py`（現成的時間/漂移核心）               | 318L，零依賴，`find_drift()` 無生產呼叫                                                                                                                                                                          |
| import AL 集群的檔案                                          | 76 個（62 個在 AL 目錄外）                                                                                                                                                                                       |
| AL 出站跨層 import                                            | 9 處                                                                                                                                                                                                             |
| 孤兒碼（僅測試引用）                                          | 3,280 行 / 8 項（前端 `maturity-tracker.js` 另 365 行，合計 3,645 行）——**2026-10-25 裁決後**：6 項已刪（生產 −1,796 / 測試 −1,313），保留 `cyber_identity`+`self_generation`（1,543 行，有實例化）+ 前端 365 行 |
| 生命狀態的分散寫入點                                          | 5 處（DLI.life_stats / ALC.phase / LifeEssence / heartbeat / intensity×3）                                                                                                                                       |
| AL 相關測試                                                   | `tests/core/life` 13、`tests/core/bio` 16、`tests/ai/lifecycle` 164、`tests/core/state` 52                                                                                                                       |
| 狀態持久化現況                                                | `data/emotion_state.json` 不存在；`data/state/` 空；`life_essence_state.json` 1.7MB；`autonomous_lifecycle_state.json` 29KB                                                                                      |
