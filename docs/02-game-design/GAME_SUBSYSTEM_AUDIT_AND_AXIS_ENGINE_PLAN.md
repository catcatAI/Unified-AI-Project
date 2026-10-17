# 遊戲子系統盤點、「萬物皆軸」引擎落地與資源修復總計畫

> 生成日期：2026-10-17。來源：全倉只讀調查（48 個 Python 檔 `ast.parse` 全過、JS `node --check`、
> 資產 `git ls-files` 追蹤核對、調用方 grep）。本檔是後續所有遊戲工作的單一事實基準與執行計畫。

## 一、目標

1. **盤點**：把倉庫內全部遊戲相關資產找齊、整理成單一清單（本檔 §二）。
2. **修復**：檢查 → 分析 → 除錯 → 修復現有破損（§四 P0/P1）。
3. **資產升級**：把現有 2D/3D 資源檢查、補繪成可用資產（§五）。
4. **架構落地**：以《萬物皆軸》設計（軸/群組/契約/中控時鐘/精度 step/tick_rate/插值管線）
   建構遊戲引擎原型，並確保顯示、交互正常可運行（§六~§七）。

## 二、遊戲資產總清單（12 子系統）

| # | 子系統 | 路徑 | 語言/框架 | 規模 | 可運行性 | 測試 | 主要破損/風險 |
|---|---|---|---|---|---|---|---|
| A | CLI RPG | `apps/game-rpg/` | Python stdlib 純 CLI | 12 py=**19,982 行**；data 5.1MB（351 卡/3,376 token，2026-10-17 訂正自述總和前為 3,720 陳舊值） | ✅ import 全過；`python apps/game-rpg/run_game.py` 可跑 | **139**（axis 116/bridge 14/craft 9）；主迴圈 7,317 行零覆蓋 | `analyze_cards.py` 檔名錯誤必炸；`gdrive_export/` 未入庫；axis_system 非 ECS |
| B | 卡牌/TUI 引擎 | `apps/backend/src/game/` | Python + Textual（headless 引擎） | 12 py=**3,924 行** | ⚠️ 引擎可用；❌ **textual 未裝 TUI 起不來** | **29**（subsystem 15+validator 14）；npc/quests/screens 零覆蓋 | `widgets.py` 文檔漂移；跨應用硬依賴 game_cards.json |
| C | Electron 卡牌 | `apps/crystal-cards/` | Electron 28.3.3 + ws | src+data=**12,869 行**（cards.js 8,266；22 類/70 角色/197 對話） | ✅ 可跑（node_modules 齊）；dist 750MB gitignored | ❌ **零行為測試** | **5/5 地點 storyNodes 斷鏈**；1 條對話斷链；**缺 assets/ 圖標** |
| D | 像素渲染 | `apps/pixel-angela/` | PyQt6+numpy/PIL/ws | 8 py=**711 行**（renderer 424） | ❌ **PyQt6/cv2 未裝**；需後端 ws :8000 | **11**（AST 菜單接線，非像素） | `base_sprite.png` 孤兒；`data/world_objects/` 不存在 |
| E | Luanti mod | `apps/luanti-mods/agent_poller/` | Lua | init.lua **881 行** | ⚠️ 結構可掛載，缺 3 前置文檔 | ❌ 無 Lua 測試；Python 側僅 2 | **`secure.http_mods` 全倉 0 文檔**（缺則 mod 靜默失效）；無安裝步驟 |
| F | 遊戲 AI 五層 | `apps/backend/src/ai/multimodal/game_*.py` | Python（numpy/pydantic/async） | 10 檔 **5,877 行**+materials 382+skill_selector 458+foveated 413 | ✅ 只經 `scripts/run_luanti_agent.py` 獨立進程接線；❌ 不進 FastAPI 主服務 | **132** | `game_vision.py` 259 行 **0 測試**；`game_materials` 孤兒（僅測試引用）；Policy 訓練/20FPS 自認未達 |
| G | 3D 黏土模型 | `models/angela_clay/` | Blender+glTF | blend 6.5M/glb 2.3M/render 4 PNG（700×900）/gallery 4.6M | ✅ 資產完整全入庫；再生需 Blender | ❌ 無測試（TASK_BREAKDOWN T4 驗收） | 除自身文檔外**零代碼引用**（純靜態） |
| H | Live2D | `apps/web-live2d-viewer/models/`+`apps/desktop-app/electron_app/models/` | Cubism Core JS+Electron/http.server | 各 40 檔 git 跟蹤（miara 40MB、Epsilon_free 2.9MB） | ✅ 34 引用 **0 缺失** | **82**（asset/menu/shared_js） | model3.json 為 2026-10-12 事後重建（HitAreas/Expressions 空）；`models.json` 孤兒且與代碼矛盾；根 `live2d_models/` 空殼 |
| I | 遊戲 API | `apps/backend/src/api/routes/game_routes.py` | FastAPI | 273 行 **10 端點**（/api/v1/game/*） | ✅ 掛載正常（失敗僅 warning） | **23**（高度匹配） | docstring 漏 `/validate`；`importlib` 跨應用硬加載 axis_system |
| J | 啟動腳本 | `scripts/start_game_stack.sh`+`patch_game_data.py` | Bash/Python | 47 行+patch 3 錨點 | 🔴 **step2 必炸**（起 run_angela.py 卻探活 :30003）；patch 三錨全 SKIP no-op | 無 | 與「代理分離」文檔決策脫節；假 "Verifying import" |
| K | 遊戲記憶 | `data/angela_memory/ham_game_memory.json` | JSON HAM episodic | 3.6MB/**4,982 條** | ✅ 格式有效 | 間接 27 | `data/` gitignored → clone 即失；templates/metadata 恆空 |
| L | 文檔/配置 | `docs/02-game-design/`（12 md）、`GAME_AI_IMPLEMENTATION_PLAN.md`、`game.default.yaml` | MD/YAML | 1,610+428 行 | — | config_coverage 鎖 7 個 dead key | FILE_INVENTORY 漂移（widgets.py 等 6 項不存在）；根 configs/ 零遊戲配置 |

**其他資產**：`resources/angela_0{1,2}.jpg/03.png/icon.png`；`apps/backend/configs/system/game.default.yaml`
（7 鍵自認無消費者）；Cubism SDK 樣例 7 套（`CubismSdkForWeb-5-r.5/Samples/Resources/`）；
`test_models/` 196 目錄 20MB（gitignored）。

## 三、「萬物皆軸」目標架構 vs 現狀 Gap

目標設計要點（用戶文檔）：實體=ID+群組下的軸；軸型別=連續/離散/狀態機+範圍；群組隔離
（空間/戰鬥/心理/劇情/表現…）；每組 step（0=連續）與 tick_rate/time_scale；組間契約訊號
帶時間戳+精度、啟動時驗證；顯示層只讀、快照+時間插值、像素吸附。

| 目標要素 | 現狀 | Gap 判定 |
|---|---|---|
| 軸（連續/離散/狀態機+範圍） | `axis_system.py` 是**物種分類軸譜**（4 系譜×3 軸+五維親和），無 class、無 step/tick | ❌ 完全不同的東西。分類軸譜可作為「劇情/戰鬥群組」的一個**屬性軸應用**，不是引擎基元 |
| 群組隔離 | 全倉 `群組`/`契約` 0 命中 | ❌ 不存在 |
| 中控時鐘 | `world_clock.py:89` 有 `master_clock`（多世界線）；`core/clock/global_system_clock.py` 有 `tick_rate_hz` 10Hz（CNS） | ⚠️ 兩個時鐘各管一攤，遊戲側無「群組依 tick_rate 累積 dt」機制 |
| step/精度量化 | game-rpg 全目錄 0 命中；`tick_rate_hz` 僅 CNS | ❌ 不存在 |
| 組間契約（訊號+時間戳+啟動驗證） | 無 | ❌ 不存在 |
| 快照+時間插值管線 | 無（CLI print；pixel-angela 直接 ws 狀態渲染） | ❌ 不存在 |
| 像素吸附/相機 | `pixel-angela/ui_config.py` 常數 128×384/10FPS，無 step 概念 | ❌ 不存在 |
| 實體容器 | `character_system.py`（角色生成/存檔）、`game_data.py`（1,919 items/99 quests）皆為**內容數據**，非 ECS | ❌ 不存在 |

**結論**：「萬物皆軸」引擎在倉庫中**尚未實作**，需新建。現有可複用積木：
- `world_clock.py` 的 world_lines/master_clock 經驗（時間線索引、快照思路）
- `core/clock/global_system_clock.py` 的 tick_rate_hz 命名慣例與 10Hz 基準
- `axis_system.py` 作為第一個「內容型軸」（掛進戰鬥/劇情群組的離散軸）
- `game_structs.py`（SkillID/SkillSpec/SkillContext 契約 dataclass 慣例）
- `primitives/game_materials.py` 組合式素材生成（繪製 2D 資源的積木）
- `pixel-angela`（PyQt6 表現層候選）、`angela_clay.glb`（3D 表現層資產）、Live2D（2D 骨骼）

## 四、破損與風險修復計畫

### P0（阻斷「可運行」，先修）— ✅ 2026-10-17 全部完成

| ID | 破損 | 證據 | 修法 | 驗收 |
|---|---|---|---|---|
| P0-1 | `start_game_stack.sh` step2 必炸：起 `run_angela.py`（統一啟動器，0 命中 30003）卻探活 `:30003/health` | 腳本 step2；`run_angela.py` grep 30003/angela_agent=0；30003 僅由 `integrations/luanti_polling_bridge.py` 綁定 | step2 改起 `scripts/run_luanti_agent.py`，或拆兩段（後端/代理各自探活） | 腳本 dry-run 探活邏輯通過；文檔同步 |
| P0-2 | `analyze_cards.py:10` 檔名錯：讀 `完整卡片目錄V1.0.txt`，實際 `完整卡片目錄V1.txt` | FileNotFoundError 實測 | 改檔名常數（或兩名都試） | `python apps/game-rpg/analyze_cards.py` 不炸 |
| P0-3 | `patch_game_data.py` 三錨全 SKIP 仍無條件回寫，且假印 "Verifying import..." | 實測三錨不匹配 | 改為：錨不匹配→報錯 exit 1；匹配→回寫後真跑 `import game_data` 驗證 | 幂等：重跑無 diff；失敗時非零退出 |
| P0-4 | crystal-cards 5/5 地點 storyNodes 指向不存在的 storyEvents（school/lake/market/corridor/library_start）+ 對話斷链 `ending_final→restart` | cards.js 實測 | 補 5 個 storyEvents 或改指向現有節點；修 restart 目標 | 斷链檢查腳本 0 斷鏈（新建 `scripts/check_crystal_links.js`） |
| P0-5 | crystal-cards 缺 `assets/icons/icon.png`（main.js:26 引用、build.files 含 `assets/**/*`） | 目錄不存在 | 用 `resources/icon.png` 複製/縮放為多尺寸 ico/png | 啟動無 404；打包配置不再指向幽靈目錄 |
| P0-6 | Luanti mod 缺 `secure.http_mods = agent_poller` 文檔與安裝步驟 | 全倉 grep `http_mods`=0 | 在 `apps/luanti-mods/README.md` 寫 4 前置（mods 安裝、world.mt、minetest.conf、bridge :30003）；`start_game_stack.sh` 註釋同步 | 文檔齊備；新人按文檔可掛載 |
| P0-7 | `textual`/`PyQt6`/`opencv-python`/`pygame` 未裝 → B 的 TUI、D 的像素渲染不可跑 | .venv 實測 | `pip install -e "apps/backend[tui,game]"`；`pip install -r apps/pixel-angela/requirements.txt`（評估 cv2 必要性——sprite_converter 可改純 PIL） | `python -m src.game.app --help` 級別可起；`python apps/pixel-angela/renderer.py --selftest` 起窗 |

**P0 執行結果（2026-10-17，逐項證據）**：

| # | 結果 | 驗收證據 |
|---|---|---|
| P0-1 | ✅ commit `e50026512` | bash -n 過；實測起 PollingBridge 後 `curl :30003/health` → `{"status":"ok",...}` exit 0 |
| P0-2 | ✅ commit `ab6d8e7f3` | `python apps/game-rpg/analyze_cards.py` exit 0（原必炸 FileNotFoundError），輸出 163 目錄卡/162 覆蓋/99.4% |
| P0-3 | ✅ commit `2ab969d72` | 連跑兩次 exit 0、md5+mtime 不變；破壞目標實測 VERIFY FAIL 捕獲 NameError exit 1 且不覆寫 |
| P0-4 | ✅ commit `2564ec80b` | **審計前提部分推翻**：`restart` 是 dialog.js:111 哨兵（非斷鏈）、storyNodes 全倉零消費者（死資料）；真破損是 **64/64 storyEvents.dialogue 全缺**（故事觸發靜默失效）。補 64 條派生 dialogue＋新增 `scripts/check_crystal_links.js`：64 fail/5 warn → **0 fail/5 warn** exit 0；node --check + eslint 過 |
| P0-5 | ✅ commit `ae4b1407d` | 256×256 icon 落地（resources/icon.png 32×32 NEAREST 8x）＋`build.icon` 接線；node 實測 main.js 相對路徑 exists=true、package.json 合法 |
| P0-6 | ✅ commit `1ef04e2f6` | `apps/luanti-mods/README.md` 四前置齊（含 `secure.http_mods`——原全倉 0 命中）＋6 端點表＋驗證清單；start_game_stack.sh 註釋同步；bash -n 過 |
| P0-7 | ✅ 本批 | 裝 `textual 8.2.8`/`pygame 2.6.1`/`PyQt6 6.11.0`/`opencv-python 5.0.0`；冒烟：Textual `run_test()` headless 掛載 TitleScreen OK、Qt offscreen QApplication＋renderer 模組匯入 OK；`tests/game/`+`test_pixel_angela_menu` 42 passed；**全量 pytest 7,824 passed / 107 skipped / 0 failed**（基線 7,413/91 是 `tests/` 單獨——其收集數 7,504 未變；本次首將 `apps/backend/tests/` 423 納入）；mypy gate 0=0、flake8 斷檔修正後 0 |

### P1（正確性/一致性）

| ID | 項目 | 修法 | 狀態/證據 |
|---|---|---|---|
| P1-1 | `game_routes.py` docstring 漏 `/validate`、卡片數寫死 351 | docstring 補齊；卡片數改從引擎讀取 | ✅ `521f64198`：docstring 補 `/validate`、去寫死 351，21 tests |
| P1-2 | `test_router_has_expected_paths` 寬鬆斷言（`issubset or all`） | 改嚴格 `issubset`，補 `/game/validate` 斷言 | ✅ `521f64198`：改嚴格集合差斷言含 `/validate` |
| P1-3 | `models/models.json` 孤兒且矛盾（只列 miara，代碼默認 Epsilon_free） | 刪除或改為真實鏡像（含 Epsilon_free），加「代碼不讀此檔」註記或讓代碼讀它 | ✅ `2d6bdd39f`：雙面真鏡像（Epsilon_free isDefault+`_note`），4 路徑實存，tests/frontend 163 passed |
| P1-4 | `FILE_INVENTORY.md` 漂移（widgets.py、根 data json、整合計劃不存在） | 逐項核對刪改 | ✅ `5ab3c9bd1`：11 項修正（歸檔指址/根 data 5 實項 git 狀態/設計文檔表 13 檔） |
| P1-5 | `game.default.yaml` 7 個 dead key | 二選一：接消費者（backbone_bridge 讀 max_cards 等）或刪鍵+更新 config_coverage | ✅ `b3dc18145`：刪 7 死鍵（只餘 `enabled`/`data_path` 真鍵）+coverage/c6 同步，69+303 passed |
| P1-6 | pixel-angela `base_sprite.png` 孤兒、`data/world_objects/` 缺 | 接進 renderer 或移到 `assets/` 加載路徑；建 `data/world_objects/` 規範樣例 | ✅ `9c32c9bb3`：tray 優先載 base_sprite（fallback 保留）+3 分類樣例+`.gitignore` negation；18 tests |
| P1-7 | Live2D miara model3.json 事後重建（HitAreas/Expressions 空） | 用 Cubism Editor 重生或從 `resources/models/miara_pro` 原始件還原 expressions；至少補 HitAreas | ✅ `ae02ec435`：Groups Ids 以 cdi3 實值填（ParamMouthOpenY/ParamEyeL,ROpen，雙面 byte 一致）；**Expressions/HitAreas 盤上無對應資產（無 expression3.json、hit-test 定義在 moc3 需 Editor），如實記錄不虛構**，manifest 契約測試 5 tests |
| P1-8 | 栮 `live2d_models/` 空殼目錄 | 刪或改指 `resources/models` | ✅（本 commit）：定性=generator 預設輸出（`live2d_avatar_generator.py:533` `mkdir exist_ok`），非孤兒→`.gitignore` 接管防生成物入 git+刪空殼（運行時重建） |
| P1-9 | `ham_game_memory.json` templates/metadata 恆空+不可復現 | bridge 寫入時補 metadata；文檔標注「本機資產，clone 無」 | ✅（本 commit）：`HAMMemoryManager._write_to_disk` 每次 save 蓋章 top-level metadata（schema_version/saved_at/counts/bucket_cap、merge 保留既有鍵）——涵蓋遊戲與主實例；templates 恆空定性為真實使用面（遊戲流只寫 conversations，store_template 唯一呼叫者在 llm/router 主實例）不虛構；`data/README.md` 落地本機資產清單+復現註記（gitignore 加錨定 `!/data/`+`/data/*`+`!/data/README.md` 使 README 可追蹤、其餘仍本地）；4 tests（TestMetadataStamping） |
| P1-10 | crystal-cards 零行為測試 | 新增 `tests/frontend/test_crystal_engine.mjs`（node:test）：tryStack/executeCombat/save-load 純函數層 | ✅（本 commit）：`test_crystal_engine.mjs` 11 tests 全綠（stack 上限/recipe 兩路徑/dialogue 觸發/擊殺+loot/反擊 game over/save-load 重建/非法存檔拒絕），node:vm 模擬瀏覽器 script 語意；pytest 橋 `test_crystal_engine_node.py` 使 `pytest tests/` 即跑；**順帶修死點**：bot-player.js 雙 eval 看不到 cards 的 const（載入即 ReferenceError）→ `global.CARDS` 橋接+刪模組層 TDZ const，實跑 30 日模擬恢復正常 |

## 五、2D/3D 資源檢查、升級與繪製計畫

### 5.1 現有資產體檢

| 資產 | 格式 | 狀態 | 動作 |
|---|---|---|---|
| `models/angela_clay/angela_clay.glb` | glTF v2, 95 meshes/18 materials | ✅ 完整入庫 | ✅ glTF 有效性+AABB 契約測試已入庫（`test_game_asset_contracts.py`，2026-10-17；96 節點=95 mesh+根） |
| `models/angela_clay/render/*.png` ×4 | 700×900 RGBA | ✅ | ✅ 尺寸/集合契約已入庫；作為 2D 立繪參考底圖 |
| Live2D Epsilon_free | moc3+physics+motions | ✅ 可玩 | 保持；進 fallback 鏈（P1-7 manifest 契約測試覆蓋） |
| Live2D miara_pro_en | Groups 已補 cdi3 實值 | ✅（P1-7） | Expressions/HitAreas 盤上無資產如實記錄（editor 需求見 manifest MetaData） |
| `apps/pixel-angela/base_sprite.png` | 128×128 | ✅（P1-6 接入托盤） | ✅ 尺寸契約已入庫 |
| `resources/angela_01.jpg` `angela_02.jpg` `angela_03.png` `icon.png`（平鋪於 `resources/`，非子目錄——本表原路徑有誤 2026-10-17 訂正） | 位圖 339×1024/338×1024/592×1792/32×32 | ✅ | ✅ 尺寸契約已入庫；icon 供 crystal-cards（P0-5）；立繪供 2D 管線 |
| `apps/game-rpg/data/game_cards.json`（原表寫 `data/game_cards.json` 有誤，2026-10-17 訂正） | 351 卡/3,376 token | ✅（自述總和 5 處陳舊值已訂正+契約鎖定） | 作為 ECS 內容灌入源（M5） |
| crystal-cards cards.js | 8,266 行 | ✅ 斷鏈已修（P0-4） | 劇情群組內容源；連結稽核 `check_crystal_links.js` |
| `test_models/` 200 目錄 | 20MB gitignored | ⚠️ | 清理或納入 .gitattributes LFS 評估 |

### 5.2 繪製升級（2D）

1. **精靈圖生產管線**（新 `apps/backend/src/ai/multimodal/primitives/` 擴充）：
   - 以 `game_materials.py` 的 `Material/Liquid/Container/compose_tool/render_potion` 為基底，
     建 `render_entity_sprite(axis_code, group_profile) -> PIL.Image`：依「軸位」決定配色/形態
     （例：物種軸 C 類原型→獸形輪廓；義體 C4→金屬高光）。這是「軸→視覺」的**契約化繪製**。
   - 輸出規格：32×32/64×64 像素圖層（body/overlay/emissive），PNG atlas + JSON 幀表。
2. **tile 集**：為空間群組畫 16×16 地形集（毒氣區/走廊/湖/市場——對 crystal-cards 地點）。
3. **驗收**：每張輸出過 `Image.open` + 尺寸/色深斷言；atlas 與 JSON 幀表一致性測試。

### 5.3 繪製升級（3D）

1. `angela_clay.glb` 已是合法 glTF v2——**驗證器測試**（二進制 magic `glTF`+JSON chunk 可解析+mesh>0）。
2. 用 `trimesh`（若可用）或 glb JSON chunk 派生**碰撞包圍盒**（extent 軸初值），供空間群組。
3. 精靈→3D 混合管線（可選後續）：glb 作展示層，2D atlas 作遊戲內實體層。

## 六、「萬物皆軸」引擎原型落地計畫

**落點**：新建 `apps/game-rpg/engine/`（純 stdlib，與現有 CLI 共存，不動 19,982 行既有代碼）。

### 6.1 資料結構（對應用戶文檔 §一/§二）

```python
# engine/axes.py
AxisType = Literal["continuous", "discrete", "fsm"]
@dataclass
class AxisSpec:
    name: str; kind: AxisType
    lo: float | None = None; hi: float | None = None
    step: float = 0.0          # 0=連續
    states: tuple[str, ...] = ()  # fsm 用

@dataclass
class AxisGroup:
    name: str                  # "space"/"combat"/"mind"/"story"/"render"
    tick_rate: float           # Hz
    time_scale: float = 1.0
    axes: dict[str, AxisSpec]
    contract: "GroupContract"  # 輸出訊號表

@dataclass
class Entity:
    eid: int
    groups: dict[str, dict[str, float | int | str]]  # 群組→軸值
    parent: int | None = None        # 連結非軸
    local_offset: tuple[float, ...] | None = None
```

### 6.2 管線（對應 §五）

```python
# engine/clock.py       —— 中控時鐘（借鏡 world_clock 的 world_lines 索引）
# engine/quantize.py    —— step 量化 round(v/step)*step；定點整數模式開關
# engine/contracts.py   —— GroupContract：訊號名/型別/精度/時間戳；register 時驗證
# engine/pipeline.py    —— tick：組依 tick_rate 累積 dt→組內 update→發訊號（下 tick 生效）
# engine/render_bridge.py —— 表現群組快照+插值（前後快照 lerp）；只讀模擬層
```

### 6.3 落地順序（用戶文檔 §八 + 本倉現實）

| 階段 | 內容 | 驗收 |
|---|---|---|
| M1 | 字典版原型：Entity/AxisSpec/AxisGroup + 空間+戰鬥兩群組 + 契約註冊驗證 | 單測：契約缺訊號啟動即 raise；組間訊號下一 tick 可見 |
| M2 | step 量化吸附（軸級覆寫）+ 定點模式 | 單測：0.01 step 往返無漂移；0=連續不量化 |
| M3 | 中控時鐘：master tick→組 dt 累積→time_scale 子彈時間 | 單測：戰鬥組 0.2×時心理組 UI 不受影響（用 tick 計數驗證） |
| M4 | 表現群組快照+時間插值+像素吸附（先做純數值渲染器，再接 PyQt6） | 單測：30Hz 模擬/144Hz 顯示中間幀為線性 lerp |
| M5 | 內容灌入：351 卡→劇情群組 FSM 軸；axis_system 譜系→離散軸字典 | 卡片→軸值轉換快照測試 |
| M6 | 2D 表現：§5.2 精靈管線接 render_bridge（PyQt6 或新 SDL/pygame） | 視覺冒煙：實體移動平滑、量化不抖動 |
| M7 | 效能：剖析→熱群組（空間/表現）換連續記憶體（array/numpy 結構） | 基準：1k 實體 60 tick/s 帧預算內 |

### 6.4 與現有系統的介面

- `world_clock.py`：M3 的中控時鐘**外包**它的 world_lines 索引（不重寫時間線），新增 group_dt 分發 API。
- `axis_system.py`：M5 作為內容適配器（`axis_code → AxisGroup("story").axes`），不改其 920 行。
- `game_routes.py`：新增 `GET /api/v1/game/engine/status`（只讀）暴露引擎 tick/組清單。
- `pixel-angela`：M6 表現端之一（ws 收 render_bridge 快照）。
- `angela_agent.py` 五層 AI：後續把 `game_structs.SkillContext` 對接 AxisGroup（L0 動作寫入戰鬥/空間軸）——遠期。

## 七、顯示/交互正常性驗證矩陣

| 子系統 | 顯示 | 交互 | 驗證手段（執行期） |
|---|---|---|---|
| game-rpg CLI | ANSI print | input() | 自動化：echo 指令序列餵 `run_game.py` 進程，斷言輸出關鍵幀 |
| backend/game TUI | Textual | 鍵盤 | 裝 textual 後 smoke 起屏；引擎層 headless 已有 29 測試 |
| crystal-cards | Electron DOM | 拖拽/點擊 | node:test 引擎層（P1-10）；手動冒煙 `pnpm start` |
| pixel-angela | PyQt6 透明窗 | 托盤/右鍵 | 裝依賴後 `--selftest`；AST 測試已有 11 |
| Luanti mod | Luanti 服務端 | 聊天/指令 | 起 flatpak 服務端+bridge 冒煙（文檔化步驟 P0-6） |
| Live2D web | http.server 8080 | 滑鼠 | `scripts/start.py` 起服+asset_integrity 16 測試 |
| 萬物皆軸引擎 M6 | PyQt6/精靈 | 鍵盤 | 單測 lerp+手動視覺冒煙清單 |

## 八、執行順序（建議）

1. **P0-1~P0-7**（阻斷項）→ 每項獨立提交+驗收。
2. **P1-1~P1-10**（正確性）→ 可與 3 並行。
3. **§5.1 體檢測試**（glb/atlas/card JSON 契約測試）→ 然後 §5.2/5.3 繪製。
4. **M1→M4 引擎核心**（每階段提交+測試）→ M5 內容灌入 → M6 顯示接線 → M7 效能。
5. 收尾：`docs/02-game-design/FILE_INVENTORY.md` 與本檔對齊；`start_game_stack.sh` 重寫成
   「後端/代理/Luanti」三段各自可選啟動。

## 九、風險與回退

- **依賴安裝**（P0-7）會改 .venv：先確認 PyQt6 在本機 headless 是否可 import（QT_QPA_PLATFORM=offscreen）。
- **crystal-cards dist 750MB** 不入庫——修資產不重打包，除非手動 `pnpm dist`。
- **Luanti 需 flatpak 服務端**：CI 無法跑，驗證靠文檔+本地冒煙。
- **引擎原型不動既有 19,982 行**：`engine/` 新目錄+獨立測試目錄 `apps/game-rpg/tests/engine/`，
  失敗可整目錄刪除不影響現狀。
- 所有修復遵守 AGENTS.md：手術式修改、無佔位符、mypy/flake8/gate 全綠、逐筆提交。

## 十、完成定義（DoD）

- [x] P0 七項全修，各自有驗證命令輸出證據（見 §四「P0 執行結果」表）
- [x] P1 十項全修或明確記錄「不修理由+替代」（P1-1~P1-10 全修，證據見 §四
      「P1」表狀態欄；P1-7 的 Expressions/HitAreas 為盤上無資產之「如實記錄
      不虛構」替代）
- [ ] 2D/3D 資產契約測試入庫（glb/atlas/卡片 JSON）——**部分：glb（v2/chunk/AABB/
      95 mesh/18 materials）+4 立繪+base_sprite+resources 位圖 5 檔+game_cards
      自述總和一致性（10 tests）已入庫 `tests/frontend/test_game_asset_contracts.py`
      （2026-10-17，同批訂正 game_cards 5 處陳舊自述值 3720→3376 token 等，
      計畫 §5.1 表 resources/data 路徑漂移）；**atlas 待 §5.2 補**
- [ ] 萬物皆軸 M1~M4 單測全綠；M5 卡片灌入快照測試綠
- [ ] 顯示/交互驗證矩陣逐行有「手動冒煙記錄」或自動化測試
- [ ] `flake8`/`mypy`/`complexity_budget_gate`/`mypy_budget_gate` 全綠
- [x] 全量 pytest 無回歸（P0-7 後新基線：**7,824 passed / 107 skipped / 0 failed**，
      paths=`tests/`+`apps/backend/tests/`；舊 7,413/91 為 `tests/` 單獨，收集數 7,504 未變）
- [x] 全量 pytest 無回歸（P1 收官覆測 2026-10-17：**7,838 passed / 107 skipped /
      0 failed**，同 paths，291s。新增測試逐一實證 +15（pixel_world 5、
      live2d manifest 5、HAM metadata 4、crystal node 橋 1），對 7,824 基線
      顯示 +14——差 1 未定位（P1 觸及測試檔 def/parametrize 前後對帳均無
      縮減；skipped 穩定 107、0 failed/0 error，非回歸訊號）。收集 7,941 與
      運行 7,945 之 +4 為既存結構性差，非 P1 引入）
