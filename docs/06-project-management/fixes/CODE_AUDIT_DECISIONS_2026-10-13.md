# 程式碼審計：修復與增刪決定留痕（2026-10-13）

> 目的：記錄本輪「全面稽核 → 排除誤報 → 正確修復 → 增刪決定」的**每一個決定與其原因**，使後續 agent 或人類可以覆核，而不是只看到結果。驗證環境：Linux
> Mint 22.3 (Zena)、Python 3.12.3、`DISPLAY=:0`（可實跑 GUI）。

---

## 1. 判定方法（先排除誤報，再動手）

本輪把候選缺陷分成三類，**只有第 3 類才修改**：

| 類別            | 判準                                            | 處置                  |
| --------------- | ----------------------------------------------- | --------------------- |
| A. 誤報         | 型別檢查器/靜態規則的合理慣用法                 | **明確不動**（見 §6） |
| B. 歷史正確刪除 | 被刪對象原本就是死碼/stub                       | 維持刪除（見 §5）     |
| C. 真缺陷       | 能在**實機**重現出錯訊息、或 API 回傳與契約不符 | 修復（見 §3）         |

實機重現的證據來源（每條修復都對到具體訊息）：

- Electron 實跑：`cd apps/desktop-app/electron_app && timeout -s KILL 22 ../node_modules/.bin/electron . --enable-logging`
  → 日誌 `/tmp/opencode/electron_log{5,6,7}.log`（含二進位，grep 需加 `-a`）
- 後端實跑：`/tmp/opencode/backend_ctl.py 8000`、聊天實測
  `/tmp/opencode/chat1.sh "<msg>"`
- LLM 額度：`/home/cxuo/文件/GitHub/可用`（`gemini-3.1-flash-lite` RPD
  500，本輪只用 1 次）

---

## 2. 生產碼修復清單

### 2.1 LLM 降級鏈與狀態（`services/llm/router.py`、`api/routes/llm_routes.py`）

- 原本降級只按 `BACKEND_PRIORITY` 硬排序，**完全無視 `llm.default.yaml` 的
  `routing.fallback_chain`**。新增
  `_plan_fallback_backends(chain, exclude)`：①全鏈精確 → ②前綴比對 →
  ③補足未提及的後端； `_try_fallback_chain` 成功後補
  `self.active_backend_type = btype`（原本 `active_backend_type`
  永遠停在第一次失敗的後端，`/llm/status` 會顯示錯的 active）。
- `_backend_token()` 統一 enum → token 的對應，避免 `'Google' in chain`
  這類字串比對漏掉 `google-gemini`。
- `/llm/status` 原本回寫常數 health、且把未載入的 provider 一併列出。改為
  `_health_cache` + `record_backend_health()` / `backend_health()` /
  `backend_category()` 三個共用函式；`llm_routes.py`
  回傳真實 type/health/active，並在 `_pruned_backends` 顯式列出被裁掉的後端。
- **實測**：`POST /llm/switch GOOGLE` → 1 次 `gemini-3.1-flash-lite`
  真實呼叫（認證成功、Google 503 重試 3 次）→ 依計畫降級本地 → 已切回
  `LLAMA_CPP`。

### 2.2 記憶 API 假死（`services/chat_service.py`）

`/api/v1/context/summary` 回 `initialized: false`，因為路由讀
`chat_service.memory_manager` 而該欄位根本不存在（屬性 `_memory_manager`）。新增
`@property memory_manager` 暴露既有實例。 **實測**：回 `initialized: true`。

### 2.3 sync 事件與監聽器（`core/sync/realtime_sync.py`、`api/lifespan.py`）

- `MODULE_CONTROL` / `WALLPAPER_OBJECT_INJECTION`
  兩個事件在 registry 裡字串值寫錯 → 訂閱者永遠收不到（真缺陷，非誤報）。修正字串值 + 新增 13 個測試（`tests/core/test_realtime_sync_events.py`）。
- **根因**：vision/audio 的 sync 監聽器**從未註冊**（`_init_sync_listener()`
  沒人呼叫）。在 `lifespan.py` 的 `sync_manager.initialize()` 之後補註冊
  `vision._vision_service._init_sync_listener()` 與
  `audio.get_audio_service()._init_sync_listener()`。
- GET `/vision/control`、`/audio/control` 原本是**寫**（會把 `enabled=None`
  寫進狀態，等同於每次都關掉）。改 `enabled: Optional[bool] = None`
  → 只有帶值才寫，GET 純讀取。

### 2.4 訓練崩潰（`ai/multimodal/visual_encoder.py`、`audio_encoder_spectral.py`）

投影片維度與原始特徵維度不一致導致 backward 必炸。補 `feature_dim`
property、`_extract_raw()`、
`_init_projection(n_raw)`、`_adapt_target()`，`train_step` 改走 raw 梯度 + LMS +
`cap=max(10,sqrt(fd))`。 **實測**：4 組 loss 單調下降。

### 2.5 前端美術（`packages/shared-js/js/` 源，已 sync 到 desktop/web 兩個 surface）

| #   | 缺陷                                                                                                                    | 修復                                                                                                            | 實機證據                                                                   |
| --- | ----------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| 1   | 表情檔路徑被再拼一次 → `runtime/Epsilon_free.2048/texture_00.png` 404                                                   | `loadTexture()` 認得直傳圖片路徑（`isDirectTexture`）                                                           | `Failed to load texture` **0** 次                                          |
| 2   | 用 Framework API 取參數，本 repo **沒打包** `live2dcubismframework.bundle.js` → 每幀 33 次 `Failed to update parameter` | 新增 `_findParameter()` Core 適配器（`model.parameters.{ids,values}` 直接寫入）+ `_normalizeParamId()` 異名比對 | `Failed to update parameter` **0** 次                                      |
| 3   | `setupModelParameters()` 依賴 `FileReferences.Parameters`（本模型沒有）                                                 | 改存 Core `defaultValues` 為基準                                                                                | `Loaded 30 parameters`                                                     |
| 4   | 換表情不重設 → Smile 殘留到 Sad                                                                                         | `applyExpressionFile()` 先 `_resetParametersToDefaults()` 再套用                                                | `Applied "Normal" (reset to defaults)`、`Applied "Smile" (7/7 parameters)` |
| 5   | 模型只會表情、**永遠不眨眼不呼吸**                                                                                      | 新增 `applyLifeSigns({blink, breath})`，以「表情寫入值」為基準做乘法/加法合成                                   | `[LifeSigns] blink/breath driven into model parameters every frame`        |
| 6   | `stopMotion()`/`playMotion()` 直接呼叫不存在的 Framework 方法 → TypeError                                               | 加 `typeof === 'function'` 守衛，缺 Framework 時明確印訊息                                                      | 0 exception                                                                |

**關鍵判斷（本輪最花時間的一處）**：生命跡象一開始加在 `Live2DManager` 的
`_animationLoop` 裡，實跑後 **沒有任何 `[LifeSigns]`**。查證發現
`_startAnimation()` 只在 `_create2DFallbackCharacter()`（2D 降級路徑）與
`switchToFallback()` 的 `else` 分支被呼叫，也就是**只在 2D
fallback 模式跑**，而該模式會
`this.canvas.style.display = 'none'`（Live2D 畫布是隱藏的）。因此把驅動改掛在
**wrapper 自己的 `render()` loop**（非 fallback 模式唯一在跑的迴圈），並**還原**
`live2d-manager.js` 的那段（不留死碼）。重跑後 `[LifeSigns]` 出現。

### 2.6 原生音訊模組路徑（`packages/shared-js/js/audio-handler.js`）

`import('../../native_modules/...')` 相對於 `electron_app/libs/shared-js/` 指向
`electron_app/native_modules/` —— **該目錄在 git 歷史中從未存在**
（`git log --all -- apps/desktop-app/electron_app/native_modules` →
0 筆）。實際位置是
`apps/desktop-app/native_modules/`，需往上三層。修正後實跑訊息由
`Could not load native module for linux: Cannot find module ...electron_app/native_modules/...`
變成模組**真的被 import**，然後依既設計落入
`Native module for linux not compiled, falling back to Web Audio API`。
**注意**：這只影響「系統音訊擷取」；麥克風走
`navigator.mediaDevices.getUserMedia`（正常）。

### 2.7 其他已修（本輪較早，見 `git status` 對應檔案）

`.flake8` 移除 F821、mypy budget 0/0、`core/hsp/connector.py` cast、`.gitignore`
移除 `*.model3.json`、4 個 Live2D manifest 重建、shared-js 六檔修正、electron
icon / `ALLOWED_DIRECTORIES` /
sync 路徑、pixel-angela、web-live2d-viewer 主題與重複 id、scripts 六檔、`.prettierignore`
加 `apps/*/next-env.d.ts` → `prettier --check .` 全綠。

---

### 2.8 記憶面板（MemoryViewer）契約修復 — 由「模仿用戶行為」實測發現

判決流程：先用真實對話序列（打招呼 → 「記住我不吃辣」→ 追問 →「記住我的貓叫小花」→ 追問）走完
`POST /api/v1/chat/unified`，再讀 `GET /api/v1/context/memory/recent` 與
`data/memory/ham_memory.json`。

實測**修復前**每一列都是空殼：`type: ""`、`importance: 0.0`、`emotion: ""`、
`timestamp: null`，`content` 是 Python
repr 字串（`{'user': ...}`）——面板完全不可讀。**修復後**（同一端點、新寫入的記憶）：

```
content:   我的貓叫什麼名字？她喜歡吃什麼？ | 我記得：我的貓叫小花，她最喜歡吃鮪魚罐頭
type:      conversation
importance: 0.354
emotion:   happy
timestamp: 2026-10-12T18:37:11.003072+00:00
```

根因與修法（每一條都對到具體程式碼）：

| #   | 根因                                                                                                                                                                  | 修法                                                                                                                                                  |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `ham_manager.store_experience()` 從不寫 `metadata.timestamp`                                                                                                          | 調用者沒送時補 `datetime.now(timezone.utc).isoformat()`                                                                                               |
| 2   | `query_core_memory(data_type_filter=...)` 比對 `c["type"]`，而 store 寫的是 `data_type` → **篩選永遠落空**                                                            | 改比 `data_type or type`                                                                                                                              |
| 3   | `_as_memory_object()` 沒把 `data_type` 帶出來 → route 的 `getattr(r, "data_type")` 恆為 `None`                                                                        | `_Mem` 增加 `data_type`                                                                                                                               |
| 4   | `chat_service._store_interaction_memories()` 完全不送 metadata → importance/emotion 恆空                                                                              | 新增 `_build_memory_metadata()`：取 `context["emotion"]`（可為 dict 或 str）+ **await** 既有 `ham_importance_scorer.ImportanceScorer` 寫入 importance |
| 5   | 該 HAM `calculate()` 是 `async`，而同步外觀 `ai/memory/importance_scorer.py` 用 `asyncio.run()` —— 在執行中的事件迴圈會拋 `RuntimeError` 然後被 `except` 吞成 `0.0`   | 改在 async 路徑直接 `await` 真 scorer（**沒有**動那個外觀，避免影響既有測試）                                                                         |
| 6   | `_calculate_time_score()` 用 naive `datetime.now()` 減 aware UTC 時間戳 → `TypeError` → 落 `TIME_ERROR_FALLBACK`(0.5) 且每次寫入都噴 warning                          | 依輸入的 `tzinfo` 決定 now                                                                                                                            |
| 7   | `_as_memory_object()` 把 dict content `str()` 掉 → 面板顯示 Python repr，且 `game_memory_bridge.py:453` 的 `isinstance(content, dict)` 分支**永遠不會命中**（死分支） | 回傳原始 content，並讓 `_Mem` 提供 dict-like `get()`（`cli/repl.py` 是用 `.get()` 取值的）                                                            |
| 8   | `cli/repl.py` 的 `/memory` 直接 `r.get(...)` —— `_Mem` 之前沒有 `get()` → **必拋 AttributeError** 被外層吞成 `Memory error: ...`                                      | `_Mem.get()` 屬性優先、metadata 次之；repl 對 dict content 做 `                                                                                       | ` 串接 |

新測試：`tests/api/test_memory_recent_panel.py`（18 tests，全綠）。

> 已知殘留：修復**之前**就存在的 262 筆舊記憶仍無 metadata（歷史資料未回填）。這不是缺陷而是資料遷移議題；未回填的理由是「不要為了美觀去改寫既有記憶檔」。

### 2.9 路徑自動抓取（消除硬編碼，28 個腳本）

盤點出三類硬編碼，全部改成「從檔案位置 / 環境變數即時解析」：

| 類別              | 原本                                                                                                                                                                                                                                                                  | 現在                                                                                                                                                                | 影響檔數                           |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| HuggingFace cache | `"/home/cxuo/.cache/huggingface/hub/models--..."`（換機器即失效）                                                                                                                                                                                                     | `_HF_HUB = os.environ.get("HF_HUB_CACHE") or os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")`，再 `os.path.join(_HF_HUB, "models--...", ...)` | 19                                 |
| 倉庫根目錄        | `sys.path.insert(0, "D:\\Projects\\Unified-AI-Project\\apps\\backend\\src")`（`scripts/quick_snn_test.py`，Linux 上必炸）與 `"/home/covo/文件/GitHub/Unified-AI-Project/..."`（`apps/backend/scripts/unified_engine_principle_experiments.py`，**用戶名根本不存在**） | 以 `__file__` 往上推到 repo root 再組路徑                                                                                                                           | 2                                  |
| shell 模型路徑    | `$HOME/.cache/...`（吃不到 `HF_HUB_CACHE`）                                                                                                                                                                                                                           | `${HF_HUB_CACHE:-$HOME/.cache/huggingface/hub}`                                                                                                                     | 1（`scripts/start_game_stack.sh`） |

實測：

- `scripts/exp_accuracy_dose.py --help` **exit 0**（模組層的
  `QWEN = os.path.join(...)` 真的算出存在的檔案）。
- `_HF_HUB` 解析出 `/home/cxuo/.cache/huggingface/hub`，`models--Qwen--...` 與
  `models--google--gemma-4-...` 兩個目錄都存在。
- 28 個被改動的腳本：`black --check` / `isort --check-only` / `flake8` 全 0。

**未改**：`apps/web-dashboard/.next/**`（build 產物，已被 `.next/` ignore）、
`configs/presets/*.preset.yaml` 的 `/home/cxuo/chip`
之類（preset本來就是使用者自訂的掛載點，屬設定而非程式路徑）。

> 順手修掉：`scripts/test_individual_encode.py` 的 `print(f"SNN output top5:")`
> （F541 空 f-string，該檔本輪稍早已修過 `tests`
> 未定義 NameError，這次一併清乾淨）。

### 2.10 提交前複核發現的兩處（**撤銷 / 更正**）

複核階段對「本輪所有變更」逐一驗證，發現兩處**不正確**的改動，處置如下：

| 對象                                                  | 當時的理由                                                                 | 複核證據                                                                                                                                                                                                          | 處置                                             |
| ----------------------------------------------------- | -------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| `tests/ai/multimodal/test_game_agent_integration.py`  | 檔頭改成 `pytest.skip("requires google API dependencies")`，915 行 → 13 行 | `grep -rn "import google\|googleapiclient" apps/backend/src/ai/multimodal/*.py` **0 命中**（藉口不成立）；`git checkout` 還原後 `pytest` → **41 passed in 0.66s**                                                 | **還原原始檔**（不提交那次刪除）                 |
| `garden_engine.py` 的 `cycle_penalty_weight` 局部變數 | 早先被判為「可調權重，屬設計決定」而列入 §6 白名單                         | `git show HEAD:` 該行**只賦值、從未被讀**；公式裡真正的懲罰項是 `cycle_penalty`（由另一個鍵 `ai.garden.engine.cycle_penalty_step` 算出），這個權重從未接上；`F841` 本就在 `.flake8` ignore 清單，也不是 lint 需要 | **保留刪除**（無行為差異的死碼），並更正 §6 該列 |

> 教訓：白名單上的「設計決定」也要能指出**實際使用點**；指出來就改白名單，而不是讓兩份紀錄互相矛盾。

---

## 3. 本輪「刪除」決定與理由（留痕核心）

### 3.1 資料垃圾（**刪**）

| 對象                                                                                                           | 證據                                                                       | 理由                                                                         |
| -------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `tests/test_data/{temp_test_files,temp_backend_tests,temp_root_tests,test_fix_report,test_modules_output}.txt` | 內容是某次執行的輸出快照；唯一引用是生成檔 `docs/PROJECT_MAP_GENERATED.md` | 一次性輸出，不承載斷言，且專案規定該生成檔**不可手改、每次重生成**           |
| `tests/fragmenta/`（含殘留 `__pycache__`）、`apps/backend/src/fragmenta/`（僅 `__pycache__`）                  | `apps/backend/src/fragmenta/` 內無任何 `.py`，只剩編譯快取                 | 模組本體早已被刪，殘留快取會讓 `import fragmenta` 在某些情況下成功而掩蓋真相 |
| `tests/README.md` 的 `fragmenta/`、`modules_fragmenta/`、`test_data/` 三列                                     | 對應目錄已不存在                                                           | 文件與實況一致（AGENTS.md 要求 MD 同步）                                     |
| 根目錄 `pytest`（11 MB）                                                                                       | `file pytest` → ImageMagick 產出的 PostScript；無任何引用                  | 某次圖片轉換把輸出檔命名成 `pytest` 的誤產物                                 |
| `scripts/utils/_run_pc_tests_file.output`                                                                      | 內容是 `[ABORT] ... this isolation-test runner is a leftover`              | 工具自己宣告是殘留物                                                         |

### 3.2 失效的測試執行器（**刪**）

`scripts/utils/_run_pc_tests.py`、`scripts/utils/_run_pc_tests_file.py`
兩個檔案**都**在檔頭檢查 `ai/dialogue/project_coordinator.py` /
`document_builder.py` 是否存在，不存在就 `[ABORT]` —— 這兩個模組在 Phase
11 已刪，所以**永遠 abort**。專案地圖也標記「未使用 2」。→ 兩者連同 `.output`
一起刪，並從 `scripts/ACTIVE_SCRIPTS.md` 移除對應兩行（文件同步）。

### 3.3 false-pass 測試（**刪 62 個**）

判定：這些測試大量使用 `mock.patch("core.<已刪模組>...")` /
`pytest.importorskip(...)` 指向**不存在的模組**，而
`core/__init__.py:158 _SubmoduleSentinel` + `:191 __getattr__`
會為任何不存在的名字**偽造 dummy**，令 `mock.patch`
靜默成功 → 永遠 green、零覆蓋。

| 檔案                                                             | 刪除數 | 保留數（乾淨） |
| ---------------------------------------------------------------- | ------ | -------------- |
| `apps/backend/tests/integration/test_end_to_end_scenarios.py`    | 15     | 9              |
| `apps/backend/tests/integration/test_error_recovery.py`          | 12     | 4              |
| `apps/backend/tests/integration/test_full_system_integration.py` | 15     | 10             |
| `apps/backend/tests/integration/test_performance_benchmarks.py`  | 12     | 6              |
| `apps/backend/tests/integration/test_digital_life_compliance.py` | 8      | 10             |
| **合計**                                                         | **62** | **39**         |

另刪 1 個永久 SKIPPED 的假測試：`tests/ai/memory/test_ham_memory.py::test_ham_config_exists`
（`ai/memory/ham_memory/ham_config.py` **從未在 git 歷史出現**，0 commits
→ 這是測試一個從來不存在的檔案，永遠 skip）。

**做法**：用 AST 定位含 stale 目標的 `test_*` 函數並整段移除（不是加 skip），再
`black` 重排 → `apps/backend/tests/integration/` 實跑 **40 passed / 7
skipped**。

### 3.4 死條目移除（**刪**）

`services/llm/providers/__init__.py` 的 `_LAZY_PROVIDERS` / `__all__` 保留了
`ED3NBackend`、`GARDENBackend`
兩個**沒有對應模組**的條目 → 匯入時必炸且訊息誤導。移除後
`from services.llm.providers import ED3NBackend` 現在**正確拋**
`ImportError: cannot import name 'ED3NBackend'`（實測）。理由：保留條目唯一的用途是「讓人以為它存在」，屬無效益的假實作。

---

### 3.5 死碼與殘留（第二輪，實機行為模擬後的判定）

| 對象                                                                                   | 證據                                                                                                                                                                                                                                     | 理由                                                                                                                                                                                                                                             |
| -------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `ai/multimodal/skill_selector.py` 的 `class SkillLibrary`                              | 全 repo（Python/JS/MD/JSON/測試/`__init__` 匯出）**零引用**；且其唯一「未來功能」`update_priority()` 函式體只有 `pass` + 一行宣稱「實際上會更新 selector 的 _skill_priorities」的註解                                                    | 這正是 AGENTS.md 禁止的 placeholder：**寫著會做事但什麼都不做**。補實作等於為一個沒有呼叫者的 API 造功能（投機建構）；連同 import 的 `SkillSpec` 一起移除（flake8 F401 已驗證）。`GAME_SKILLS`/`SkillID` 仍被 `SkillSelector` 本體使用，**保留** |
| `ai/memory/types.py` 的 `class MemoryType`                                             | 唯一引用是 `ai/memory/__init__.py` 的 re-export；成員（core/episodic/semantic/procedural/working）在全 repo **0 使用**，與實際儲存的 `data_type` 字串（`conversation`/`game_experience`/`behavior_learning`/`user_fact`…）**完全不對應** | 保留它只會讓「已有型別分離」的假象成立；採用它則需要改寫所有 store 的字串語彙＝大重構。**決定：刪**，型別分離的需求另案處理（見 §7）。同檔的 `HAMDataPackageInternal`/`HAMRecallResult` **有實際使用，保留**                                     |
| `scripts/utils/_run_pc_tests.py`、`_run_pc_tests_file.py`、`_run_pc_tests_file.output` | 兩支 runner 檔頭都檢查 `ai/dialogue/project_coordinator.py`／`document_builder.py`，不存在就 `[ABORT] ... this isolation-test runner is a leftover`（**永遠 abort**）；專案地圖標記「未使用 2」                                          | 自我宣告為殘留物的工具，連同輸出檔刪除，並同步 `scripts/ACTIVE_SCRIPTS.md`                                                                                                                                                                       |
| 根目錄 `pytest`（11 MB PostScript）                                                    | `file pytest` → ImageMagick 產出，標題 `(pytest)`，無任何引用                                                                                                                                                                            | 某次圖片轉換把輸出命名成 `pytest` 的誤產物                                                                                                                                                                                                       |

## 4. 新增的防線（防止同樣問題再發生）

新增 `tests/test_no_stale_mock_targets.py`（本輪唯一新增的「測試基礎設施」）：

- 掃描 `tests/` 與 `apps/backend/tests/` 的 `patch(...)` /
  `monkeypatch.setattr(...)` / `pytest.importorskip(...)` 字串目標，用
  `importlib.util.find_spec` 判定模組是否存在。
- 判準刻意含 root-package sentinel 的情況：**最長存在的前綴 == 0 → stale**，或
  **最長前綴 == 1 且片段 >= 3 → stale**（`core.__getattr__`
  會偽造子模組，`find_spec("core")` 成功但 `core.xxx`
  根本不存在 → 只看「第一段是否可 import」會漏判）。
- `importorskip` 額外要求全名本身是模組（那是模組級 skip，不是 target）。
- `ALLOWLIST = {"ctypes.windll"}`（前綴比對，該測試有
  `pytest.skip("Windows-only...")` 守衛）。
- **結果：94 個 stale 命中 → 0，本檔實跑通過。**

---

## 5. 維持刪除的歷史決定（覆核後認為「刪對了」）

| 對象                                                                                                              | 證據                                                                              | 結論                                                                                                         |
| ----------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| commit `2150f93b0 "Fix and update"` 刪除的 **38 個生產檔**                                                        | `git show 2150f93b0^:<path> \| wc -l` 全部 **<= 4 行**，內容是 `pass` placeholder | **維持刪除**。AGENTS.md 明文禁止 `pass` placeholder，保留 38 個空殼只會讓「有實作」的假象成立                |
| `core/degraded_mode`、`core/fault_isolation`、`core/desktop_pet_controller`、`ai/memory/ham_memory/ham_config.py` | `git log --all -- <path>` → **0 commits（從未存在）**                             | **不補**。這是從未實作的願望清單，不是「刪多了」；補實作需要先有需求與設計，不能為了讓 mock 通過而憑空造模組 |
| `ai/dialogue`（ProjectCoordinator / DocumentBuilder）                                                             | Phase 11「Delete 11 dead subsystems」明列；兩個 runner 自己 ABORT                 | **維持刪除**，並連帶刪掉兩支失效 runner（§3.2）                                                              |

| `ai/lifecycle/memory_integration_loop.py` 的 `MemoryIntegrationLoop`
接線到生產 | 類別完整且有 21 個測試，但 src 內零呼叫；**它所有會寫入的分支**都用
`hasattr(self.memory_manager, ...)` 包著，而 `store_structured_memory` /
`add_to_knowledge_base` / `generate_template` / `get_access_count`
**四個方法在整個 codebase 都不存在** |
**不接線**。接了等於開一個每 3 分鐘喚醒一次、只在 RAM 累積、**什麼都不落地**的背景迴圈；更糟的是它會把模式寫進 template
bucket，而 template bucket 的內容會被 `TemplateMatcher` 當答案直接播出去（這正是
`_UNSERVABLE_CONTENT_MARKERS`
要攔的化石回放）。要接必須先實作那 4 個方法並設計防污染，屬新功能而非接線 |

> 與 commit 訊息為 `Fix and update`
> 的歷史相符的判準：**只看刪除當下該檔的內容**，不看 commit
> message。所有 38 檔逐一驗證，無一例外。

---

## 6. 誤報白名單（明確不動，寫下來避免下次又被改掉）

| 類別                                     | 範例                                                          | 為什麼是誤報                                                                    |
| ---------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `is True` / `is False`                   | —                                                             | 本專案對 `bool` 明確語意，改 `==` 反而容許 `1`/`0` 混入                         |
| PEP 563 字串註解                         | `-> "SomeType"`                                               | `from __future__ import annotations` 下為合法延遲註解                           |
| `global _SUBSCRIBED`（`semantic_qa.py`） | —                                                             | 唯一寫入點就是該函式，global 是刻意的模組級旗標                                 |
| `visual_*` 型別註解                      | —                                                             | 註解不影響執行期；mypy 預算已鎖定                                               |
| `to_simplified` / `t2s_table`            | `ai/core/t2s_table.py` 被 `unicode_utils.py:193` **實際匯入** | 是有實作、有測試（`tests/unit/test_unicode_utils.py:124`）的正常模組，不是 stub |

---

## 7. 未修的項目與「為什麼不修」（已知限制）

| 項目                                                              | 狀態                                            | 原因                                                                                                                                                                                                         |
| ----------------------------------------------------------------- | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Live2D **動作（motion）** 無法播放                                | 已由「TypeError 崩潰」降級為「明確提示」        | 需要打包 `libs/live2dframework/dist/live2dcubismframework.bundle.js`（Framework，非 Core）。`scripts/sync_shared_js.py` 把它標為 `OPTIONAL_SUFFIXES`，屬**刻意可選**的依賴；補齊牽涉授權與體積決定，不是 bug |
| **系統音訊擷取**                                                  | 走 Web Audio fallback（設計內）                 | 需要 (a) 編譯 `pulseaudio-capture.node`（缺 `libpulse-dev` headers、缺 `node-gyp`）與 (b) 在 ESM renderer 用 `createRequire` 載入 CJS。麥克風路徑不受影響。屬環境/打包課題，不是程式邏輯缺陷                 |
| `apps/backend/tests/` 的 56 條 E541 級既有 flake8 告警            | 不動                                            | CI 的 lint 範圍是 `flake8 apps/backend/src tests/`，**不含** `apps/backend/tests/`；動它只會製造無關 diff                                                                                                    |
| `unicode_utils.py` F601 重複 `頭`                                 | 不動                                            | `AGENTS.md` §X #261 明文「需領域判讀」，不在本輪職責內                                                                                                                                                       |
| 記憶**型別分離**（能力表第 1 項）                                 | 已刪未使用的 `MemoryType`，`data_type` 維持字串 | 三套語彙並存（`types.py` 五類 / `game_memory_bridge` 遊戲 Enum / HAM 自由字串）。收斂需要跨 store 的遷移與 bucket 路由測試，屬重構，不塞進本輪                                                               |
| 舊記憶 metadata 回填                                              | 不回填                                          | 262 筆歷史資料缺 timestamp/importance/emotion；回填需要編輯既有記憶檔，收益僅是面板美觀                                                                                                                      |
| 使用者事實（`learning_handler` 的 `fact_*`）不出現在 MemoryViewer | 不動                                            | 事實存在 `VectorMemoryStore`，面板讀的是 HAM `conversations` bucket —— 是**取用範圍**選擇，不是契約錯誤。合併兩 store 的列表屬新功能                                                                         |
| `.env` 中 `ANGELA_LLM_BASE_URL` / `ANGELA_EXTENDED_MODEL`         | 記錄為死配置                                    | 全專案 0 消費點。已記入本文件；**未刪 `.env`**（含真 key，任何寫入都可能損及金鑰）                                                                                                                           |

---

## 8. 驗證數據（修復後實測）

| 項目                                                                     | 結果                                                                                                                                         |
| ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `flake8 apps/backend/src tests/`                                         | **rc=0**                                                                                                                                     |
| `black --check apps/backend/src tests/`                                  | 1261 files unchanged，**rc=0**                                                                                                               |
| `isort --check-only apps/backend/src tests/`                             | **rc=0**                                                                                                                                     |
| `prettier --check .`                                                     | **All matched files use Prettier code style!**                                                                                               |
| `pnpm lint:js`                                                           | **0 errors**（2910 warnings，與基線同級）                                                                                                    |
| `scripts/sync_shared_js.py --surface desktop\|web`                       | **all surfaces verified**                                                                                                                    |
| `pytest -k "llm or router or fallback or angela_chat or prompt_builder"` | 379 passed                                                                                                                                   |
| `pytest apps/backend/tests/integration/`                                 | **40 passed, 7 skipped**                                                                                                                     |
| `tests/test_no_stale_mock_targets.py`                                    | passed（94 → 0 stale）                                                                                                                       |
| Electron 實跑（`electron_log7.log`）                                     | `[LifeSigns]` ✅、`Applied "Normal"/"Smile"` ✅、`Failed to update parameter` **0**、`Failed to load texture` **0**、app console error **0** |
| `/llm/switch GOOGLE`                                                     | 1 次真實 Gemini 呼叫（額度 ≈1-3 / 500），已切回 `LLAMA_CPP`                                                                                  |

**基線**（本輪改動前全量）：`python -m pytest tests/ --timeout=90 -q` → **7190
passed, 121 skipped, 2 xfailed**。

**最終全量（本輪全部改動完成後，含 §2.10 還原，2026-10-13）**：
`python -m pytest tests/ --timeout=90 -q` → **7339 passed, 118 skipped, 2
xfailed, 0 failed（4:30）**；`pytest tests/ --collect-only -q` → **7458
collected**（連續兩次量測一致）。`pytest apps/backend/tests/` → **418 passed, 35
skipped, 0 failed**。

淨變化拆解：+41（還原
`test_game_agent_integration.py`）、+18（`test_memory_recent_panel`）、+13（`test_realtime_sync_events`）、+34（`test_llm_status_and_fallback`）與先前輪次新增的測試；−62（false-pass 測試）、−1（永久 skip 的
`test_ham_config_exists`）、−1（`SkillLibrary` 無測試，不影響）。

文件同步：`AGENTS.md`、`tests/README.md`（×2）、`.github/workflows/ci.yml`
註解、`MASTER_TASK_MAP.md` 尾端追加一行，全部對到 **7458 / 2026-10-13**。

其餘最終結果：

| 檢查                                         | 結果                                                                                                                                                                                                                                           |
| -------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `flake8 apps/backend/src tests/`             | **rc=0**                                                                                                                                                                                                                                       |
| `black --check apps/backend/src tests/`      | **1262 files unchanged, rc=0**                                                                                                                                                                                                                 |
| `isort --check-only apps/backend/src tests/` | **rc=0**                                                                                                                                                                                                                                       |
| `prettier --check .`                         | **All matched files use Prettier code style!**                                                                                                                                                                                                 |
| `pnpm lint:js`                               | **0 errors**, 2910 warnings（與基線同級）                                                                                                                                                                                                      |
| `scripts/mypy_budget_gate.py`                | **mypy errors: 0｜budget: 0 ✅**                                                                                                                                                                                                               |
| `scripts/sync_shared_js.py --check`          | **all surfaces verified**（1 optional：Framework bundle 未打包，見 §7）                                                                                                                                                                        |
| 後端 smoke（8000）                           | `/health` 200、`/llm/status` → `active: LLAMA_CPP` + 每後端真實 `type/health`、`/context/summary` → `initialized: true`、`/context/memory/recent` → 四欄全填、`POST /chat/unified` → `backend: llama.cpp / model: gemma-4-E2B-it / route: llm` |

---

## 9. 本文件的使用方式

- **要看「改了什麼」** → §2（生產碼修復）。
- **要看「刪了什麼、為什麼」** → §3（本輪刪除）、§5（維持歷史刪除）。
- **要看「為什麼什麼都沒動」** → §5 的 `MemoryIntegrationLoop`
  列、§7（已知限制）。
- **要重跑驗證** → §8 的指令清單（第二輪見 §13）。
- 任何後續 agent 若想重新引入被刪對象，**必須先推翻本文件對應那一列的證據**。

---

# 第二輪（同日續修）：六類新缺陷 + 誤報排除

## 10. 本輪方法

先重跑基線，確認前輪結論仍成立（flake8 / black / isort / prettier / mypy
budget 全 0；`pytest tests/` 7335 passed、`pytest apps/backend/tests/` 418
passed），再用五種系統性掃描找**前輪沒抓到的類別**：

1. 全 `src` import sweep（找出無法 import 的模組）
2. `hasattr` / `getattr` 字串 guard 對照全 repo 已定義符號（找永遠不成立的分支）
3. `except Exception: pass` 全量清單（找靜默吞錯）
4. 專案地圖的 orphan / unused 清單
5. 已刪模組名稱的全 repo 掃描（找殘留引用）

判準不變：**只有能在實機重現、或 API/契約與實況不符的才算缺陷**（§10.3 列出本輪明確判為誤報、不動的項目）。

## 11. 本輪修復

### 11.1 `--stream` 必拋 AttributeError（`packages/cli/cli/ai_models_cli.py`）

- **證據**：`single_query` / `chat` 在 `if stream:` 分支直接呼叫
  `self.service.stream_completion(...)`，而 `self.service` 唯一可能的型別
  `AngelaLLMService` **沒有** 這個方法（實測
  `hasattr(AngelaLLMService, "stream_completion")` → False）、也沒有
  `__getattr__` 代理。此旗標是對使用者的承諾：`packages/cli/package.json` 的
  `start:ai-models`、 `docs/05-development/USER_GUIDE.md:190`。
- **修法**：新增 `_emit_response()`，先
  `getattr(self.service, "stream_completion", None)` 探測；缺方法時退回 buffered
  `chat_completion` 並在 stderr 說明（與 `ai/ensemble.py::streaming_ensemble`
  既有「探測→警告→回退」慣例一致）。順帶修掉串流模式**不寫入 assistant 歷史**的缺陷（原本只有非串流分支 append，導致下一輪只看到 user 訊息）。
- **測試**：`tests/tools/test_cli_tooling.py` +2（AST 鎖定不得再出現裸
  `self.service.stream_completion`；行為測試用無 `stream_completion`
  的假 service）。

### 11.2 情緒→閾值的第三條路徑永遠不生效（`ai/unified_engine/semantic_qa.py`）

- **證據**：`_emotion_threshold_adjustment()` 在 `adj == 0.0` 時 `importlib`
  匯入 `api.lifespan`，再取 `get_emotion_system` 或 `_get_emotion_system`；實測
  `hasattr(api.lifespan, ...)` **兩者皆 False** → `get_es`
  恆為 None，整段（含 fear/sadness→+0.05、joy/trust→−0.04 的映射）永遠不會執行，且每次呼叫都白做一次重量級 import。此路徑是 §X
  #271 明列的「三路徑探測（注入>state_store>EmotionSystem）」第三步。
- **修法**：依 `api/lifespan.py` 既有 accessor 慣例（`get_crisis_system` /
  `get_causal_reasoning` / `get_metabolic_heartbeat` …）補上
  `get_emotion_system()`，走 backbone registry 的 `chat.emotion_system`
  key——**與 `chat_routes._get_emotion_system()` 共用同一個實例**（該檔的
  `_backbone_module` 也是這個 key），避免兩個 EmotionSystem 並存。
- **實測**：`fear → +0.05`、`joy → −0.04`（修復前兩者皆 0.0）；
  `lifespan.get_emotion_system()` → `EmotionSystem`。
- **測試**：`tests/api/test_lifespan_getters.py` +1（單例共用）、
  `tests/ai/unified_engine/test_semantic_qa_emotion_loop.py`
  +1（該分支可達且有正確方向性）。

### 11.3 `["python", ...]` 直譯器可攜性（5 處）

- **證據**：本機與 CI 只有 `python3`（`python` → exit
  127）。本 repo 已有一支測試（`tests/tools/test_cli_tooling.py::test_no_script_invokes_bare_python`）專門守
  _package.json_ 不得呼叫裸 `python`，但**同樣的問題沒被守到 Python 腳本自己**。
- **修法**：全部改用 `sys.executable`：
  `scripts/utils/smart_test_runner.py:59`（跑 pytest）、
  `apps/backend/scripts/smart_dev_runner.py`（啟動 ChromaDB）、
  `apps/backend/scripts/execute_smart_fix.py` ×3、
  `apps/backend/tests/test_v63_config_driven.py` 的 `__main__` 手動執行區。

### 11.4 已刪自動修復工具的殘留呼叫（3 檔，commit 證據）

- **證據**：`git show 311ad8d53`（v6.0.4「清理自动修复系统」）刪除 8 支 auto_fix 腳本；`advanced_auto_fix`
  / `runtime_auto_fix` / `enhanced_auto_fix` 在整個 repo 找不到檔案。
- `apps/backend/scripts/smart_dev_runner.py`（文件上的啟動入口，見
  `docs/03-technical-architecture/api/START_BACKEND.md:19`）：
  - `run_auto_fix()`
    每次 import 失敗→印出與真正失敗無關的 traceback→回傳 False。改成明確回傳 False（呼叫端行為不變，少了誤導輸出）。
  - uvicorn 異常退出路徑的
    `from apps.backend.scripts.runtime_auto_fix import RuntimeAutoFixer`
    **不在任何 except 的涵蓋範圍**（該層只接
    `KeyboardInterrupt`），會讓使用者看到與 uvicorn 退出原因無關的錯誤。改為明確回報並回傳 1（兩條路徑原本都必然失敗，屬行為等價）。一併移除約 40 行等不到東西的
    `MockProcess` 鷹架。
- `apps/backend/scripts/execute_smart_fix.py`：`run_smart_auto_fix()`
  檢查不存在的
  `enhanced_auto_fix.py`→回傳 False→`execute_complete_fix_process()`
  **第一步就中止**，整個腳本等於不可用。改為回報不可用、由呼叫端跳過該步驟續行。
- `apps/backend/scripts/smart_executor.py`：`run_auto_fix()` 的 `try`
  不可能拋錯，其 `except` 是死分支；收斂為明確 no-op。

### 11.5 `workflow_controller.py` 產生的 PowerShell 四個獨立錯誤

- **證據**：`run_in_separate_terminals()` 產生 `start_workflow.ps1`，其中
  1. `$projectRoot = Path(__file__).parent.parent.parent.parent` → **repo
     root**，但腳本在 `apps/backend/scripts/`，於是每個 `scripts/<tool>.py`
     都指向不存在的路徑；
  2. `scripts/test_runner.py` → **全 repo MISSING**（`find -name test_runner.py`
     無結果）；
  3. 用裸 `python`；
  4. 等待循環 `Test-Path 'test_results.json'`，而 `error_analyzer` 讀的是
     `test_results/latest_test_results.json` → 條件永遠不成立，分析永不觸發。
- **修法**：`$projectRoot` 改指 backend root（含 `scripts/`）→ 改用
  `python3 -m pytest` → 輪詢同一個檔名。
- **離線驗證**（本機無 PowerShell）：執行該函式並攔截產出的
  `.ps1`，確認只引用存在的腳本（`error_analyzer.py` / `fix_executor.py`）、無裸
  `python`、`projectRoot` 正確、輪詢檔名與 `error_analyzer`
  一致，事後刪除暫存檔。
- **限制**：此路徑 Windows 專用，Linux 無法端到端執行——屬 §7 的 (C) 環境限制，不是遺漏。

### 11.6 文件與實況不符（修 3 份、刪 2 份）

- `apps/backend/scripts/README.md`：正文教使用者跑 **7 支不存在的工具**
  （`simple_auto_fix.py`、`auto_fix_complete.py`、`advanced_auto_fix.py`、
  `auto_fix.bat`、`auto_fix.sh`、`test_fix_demo.py` …）與 **8 個不存在的 `pnpm`
  指令**（`pnpm fix`、`pnpm fix:complete`、`pnpm fix:advanced`、`pnpm fix:test`、
  `pnpm validate`、`pnpm validate:fix`、`pnpm demo:fix`、`pnpm fix:advanced:test`——
  `package.json`
  一個都沒有）→ 重寫為現存 21 支 Python 腳本的實況索引，並在檔頭留下「不可再引入」的歷史說明與 commit 依據。
- `apps/backend/scripts/USAGE_GUIDE.md`、`COMPLETION_REPORT.md`：整份都在描述同一套已於 v6.0.4 移除的系統（前者 18 處、後者 20 處引用已刪工具）→
  **刪除**。
- `apps/backend/scripts/README_separated_test_fix.md`：內容多數仍有效（`error_analyzer`
  / `fix_executor` / `workflow_controller` / `start_separate_terminals.ps1`
  都在），故**修而不刪**：移除 `enhanced_auto_fix.py` 段、`test_runner.py` 改為
  `python3 -m pytest`、所有 `python ` → `python3 `。

## 12. 本輪誤報（明確不動，避免下次又被改掉）

| 項目                                                                                    | 為什麼是誤報                                                                                                                         |
| --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `textual` import 失敗 ×4（`game.app` / `title_screen` / `gameover_screen` / `screens`） | `textual` 是 `apps/backend/pyproject.toml` 的 `tui` extra，未安裝屬預期；`game/__init__.py` 不 eager import 它們，`import game` 正常 |
| `ai/ensemble.py::streaming_ensemble` 探測 `stream_completion`                           | 探測失敗時會 `yield "[Ensemble Error: …]"`（明確訊息，非靜默空值），且目前無呼叫者                                                   |
| `core/autonomous/playground.py`（地圖標 L1 高疑孤兒）                                   | 刻意保留的退役示範，`tests/test_playground_retired.py` 鎖定 exit 2 且不得拋 traceback                                                |
| 18 個 `getattr`/`hasattr` guard（`retrieve_by_spatial_proximity`、`ham_memory` …）      | 對注入物件 duck-typing；缺席時有 `logger` 訊息 + 明確回退，是設計而非缺陷                                                            |
| `except asyncio.CancelledError: pass`（約 25 處）                                       | 關閉/取消是正常流程，靜默即正確語意                                                                                                  |
| 專案地圖「未使用 import」清單（數百條）                                                 | F401 類 cosmetic；`.flake8` 已按專案慣例 ignore                                                                                      |
| `scripts/utils/check_resources.py:28` 的 `"python"`                                     | 是 psutil 進程名過濾字串，不是直譯器呼叫（**與 §11.3 不同**）                                                                        |
| `ai/lifecycle/memory_integration_loop.py`                                               | 維持前輪 §5 判定：不接線（四個依賴方法在 codebase 都不存在）                                                                         |

## 13. 本輪驗證數據

| 檢查                                                     | 結果                                                                                                |
| -------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `flake8 apps/backend/src tests/`                         | **rc=0**（CI 範圍）                                                                                 |
| `flake8`（本輪所有改動檔，含 `apps/backend/scripts/*`）  | **rc=0**                                                                                            |
| `black --check` / `isort --check-only`（本輪所有改動檔） | **rc=0**                                                                                            |
| `prettier --check .`                                     | **All matched files use Prettier code style!**                                                      |
| `scripts/mypy_budget_gate.py`                            | **mypy errors: 0 ｜ budget: 0 ✅**                                                                  |
| `pytest tests/ --timeout=120 -q`                         | **7339 passed, 118 skipped, 2 xfailed, 0 failed（4:30）**                                           |
| `pytest apps/backend/tests/ --timeout=120 -q`            | **418 passed, 35 skipped, 0 failed（0:38）**                                                        |
| 行為實測（CLI）                                          | 無 `stream_completion` 的 service 下 `--stream` 由「AttributeError」變成回退 buffered + stderr 說明 |
| 行為實測（情緒閾值）                                     | `fear +0.05` / `joy −0.04`（修復前皆 0.0）                                                          |
| 行為實測（workflow PS 產生器）                           | 產出的 `.ps1` 只引用存在的腳本、無裸 `python`、輪詢檔名一致                                         |

淨變化：`7335 → 7339`（+4：`test_cli_tooling.py` ×2、`test_lifespan_getters.py`
×1、`test_semantic_qa_emotion_loop.py` ×1）。

## 14. 已發現但本輪未修：文件引用的腳本路徑（新工作流，需逐條判讀）

**為什麼不塞進本輪**：這是一整批跨檔案的判讀工作，每一條都要在「修正路徑 / 標記已移除 / 保留為歷史」之間決定；改錯路徑比現狀更糟。§11.6 已修完與本輪直接相關的
`apps/backend/scripts/` 幾份，其餘留給專門一輪。

**復現指令**（在 repo root）：

```bash
grep -rhoE "python3? (scripts/[A-Za-z0-9_./-]+\.py)" --include="*.md" \
  docs/ README.md QUICKSTART.md AGENTS.md | grep -v 09-archive \
  | awk '{print $2}' | sort -u | while read p; do [ -f "$p" ] || echo "MISSING $p"; done
```

**結果**：約 70 個相異路徑中，與 repo root 相對的 **~38 個不存在**，可分三類：

| 類別                    | 例                                                                                                                                                                          | 處置建議                                   |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| A. 路徑寫錯（檔在別處） | `scripts/smart_test_runner.py` → `scripts/utils/`；`scripts/smart_dev_runner.py`、`scripts/workflow_controller.py`、`scripts/final_validation.py` → `apps/backend/scripts/` | 修路徑（低風險、可機械化）                 |
| B. 已移除的腳本         | `scripts/train_three_axis.py`、`scripts/prepare_three_axis_datasets.py`、`scripts/benchmark_mmlu_subset.py`（§X #266 明文退役）、`scripts/clean_backup_archive.py`          | 標記為已移除或自文件撤下，**不要**憑空重建 |
| C. 已歸檔               | `scripts/train_ed3n.py`、`scripts/train_multimodal_real.py` → `scripts/_archive/`                                                                                           | 文件改指 `_archive` 或標記已封存           |

命中檔案包括
`docs/QUICK_START.md`、`docs/03-technical-architecture/THREE_AXIS_SYSTEM.md`、
`docs/03-technical-architecture/api/START_BACKEND.md`、`docs/03-technical-architecture/api/`
等活躍文件（部分屬歷史報告，可接受）。另有一項**跨全 repo 的慣例問題**：文件普遍寫
`python <script>`，而本機與 CI 只有
`python3`——已修的三處見 §11.3，其餘需一次整批決定（不是逐檔修）。
