# 互動空間（Interactive Space）計畫書

> **這份文件是什麼**：一個「空間」的建設計畫——多位 AI（不同角色／人格）在同一個場地裡自由活動，能改自己的形象（穿著等）、編輯與播放動作、調整鏡頭與錄影，後期接 AI 直播。含資料模型、階段切法、增量更新機制、與既有系統的接點。
>
> **這份文件不是什麼**：不是實作（目前全倉沒有這個空間的執行時）；不是角色大腦（那是 `MULTI_ROLE_PLAY_AGENT_PLAN.md`）；不是美術規格書（不規定模型面數、材質流程）。
>
> **狀態**：draft — 方向已定（§4 決策）。**S0 ✅、S1 ✅**（多角色同場、`/ws/space` 權威廣播＋前端同步）、**S2 一半**（衣櫃 UI／undo／localStorage；AI 自改未做）、**S6 一半**（房間熱載入＋feature flag）。S1.5（Live2D 載入器，目前程序繪製）、S3（動作編輯器）、S5（直播，需外部條件）未做。
>
> - 作者：Angela AI Development Team
> - 版本：7.5.0-dev
> - ANGELA-MATRIX：`[L4] [βγδ] [B] [L3]`
> - 日期：2026-10-28

---

## 0. 一句話

**空間＝一個有座標、有鏡頭、有時間軸的舞台；AI 是舞台上的演員，不是瀏覽器裡的一張圖。**

把「角色」與「場地」解耦：角色的大腦（人格、記憶、模型綁定）已經在
`ai/roleplay/` 落地，空間只負責「身體在哪、長什麼樣、在做什麼、被誰看到」。

---

## 1. 現況盤點：專案裡有嗎？

**結論：有零件，沒有空間。** 五個零件各自成立，但沒有一個把它們串成「同一個場地裡的多位 AI」。

| 既有資產 | 實際能做什麼 | 缺什麼 |
| --- | --- | --- |
| `apps/luanti-mods/agent_poller`（Luanti/MinETest 伺服端 mod + `scripts/run_luanti_agent.py`） | **真正的 3D 世界**：`AngelaBot` 會 goto / dig / place / craft / look_at / scan / give，玩家聊天轉送到 Angela。2 秒輪詢，HTTP 橋接 :30003 | 形象不可改（只有玩家外觀）、沒有動作編輯、沒有鏡頭／錄影、單一 bot |
| `apps/pixel-angela`（`renderer.py`、`soft_body_engine.py`、`world_manifest.md`、`data/world_objects/`） | 2D 像素身體：NumPy 矩陣渲染、軟體物理、3 個物件樣例（牆／能量飲料／貓），代謝互動欄位契約有測試守 | **`PixelWorld` / `BasePixelObject` / `interaction_handler` 未實作**（`world_manifest.md` 自述「全倉零代碼引用」） |
| `apps/web-live2d-viewer`（`index.html`、`models/Epsilon_free`、`miara_pro_en`、`js/shared-js/angela-character-config.js`） | 瀏覽器裡的 Live2D 角色：表情（blush/wink/smile/happy…）、語音錄音按鈕、硬體降級 | 只有**一個**角色、沒有動作時間軸、沒有鏡頭、沒有錄影／推流 |
| `apps/game-rpg`（`character_system.py`、`axis_system.py`、`sim_systems.py`）＋ `docs/02-game-design/*` | 場景圖（村莊／森林／湖畔／礦山）、PC/NPC/GM 三類角色、裝備與道具、數值系統——**設計完整、以文字與規則為主** | 沒有視覺舞台；場景是資料不是畫面 |
| `apps/desktop-app`（Electron）＋ `apps/web-dashboard` | 桌面殼與控制台，可承載視窗／托盤／本機檔案 | 沒有 3D/2D 場景渲染 |
| `apps/crystal-cards`、`apps/data`、`apps/gemini-os-bridge` | 卡牌、資料、外部模型橋接 | 與空間無直接關係 |

歷史面：`docs/09-archive/` 沒有更早的空間實作；最接近的是 `pixel-angela` 的 MOD 規格（2026-10-17 標註未實作）與 Luanti 橋接。**沒有「做過又拆掉」的空間，只有「畫過沒做」的像素世界。**

---

## 2. 名詞（本文件只用這幾個）

| 名詞 | 定義 | 不是什麼 |
| --- | --- | --- |
| **Space** | 一個可被觀看的場地：座標系＋光源＋背景＋可站立區域 | 不是記憶、不是對話 |
| **Room** | Space 的一個具體場景（`room.json`）：地板、牆、道具、出生點 | 不是 `game-rpg` 的 `Scene`（那是文字冒險的節點） |
| **Actor** | 站在場上的實體，綁一個 `Role`（`ai/roleplay/role.py`）＋一個 `Avatar` | 不是 Agent 進程（Actor 沒有自己的 event loop） |
| **Avatar** | 外觀：模型、材質、穿著槽、體型參數、表情通道 | 不是人格（人格在 `PersonaEngine`） |
| **Motion** | 時間軸上的動作片段（keyframe 或 Live2D motion3.json），可被觸發／排隊／混音 | 不是 LLM 輸出 |
| **Camera** | 機位：位置、看向、焦距、運鏡曲線 | 不是使用者的滑鼠視角（那是 orbit 控制） |
| **Shot** | 一次錄影工作：機位＋時間範圍＋輸出格式 | 不是截圖 |
| **Stream** | 推流工作：目的地（RTMP/WebRTC）＋場景切換＋聊天回饋 | 不是錄影（可同時，但不是同一件事） |

---

## 3. 架構選項與否決理由

### 3.1 選項 A：全 3D（three.js / Babylon.js）自建房間

- 優點：鏡頭、錄影、運鏡、直播全部是原生能力；`canvas.captureStream()` + `MediaRecorder` 就能錄 WebM。
- 缺點：角色要嘛自建模（成本高），要嘛用 Live2D 貼片（3D 場景裡的 2D 立牌，觀感取決於做法）。

### 3.2 選項 B：以 Luanti 為空間（沿用 `agent_poller`）

- 優點：**已經有 3D 世界與移動協議**，`goto/look_at/place` 就是現成的 Actor 動作原語；多人同場天然支援。
- 缺點：**改不了形象**（外觀是 voxel 皮膚，需要改客戶端）、**沒有鏡頭 API**（只能跟隨視角）、**錄影要外部工具**（OBS）。要達到「形象編輯＋運鏡＋錄影」得改 Luanti 客戶端，等於換一個專案。

### 3.3 選項 C：2D 舞台（canvas / PixiJS）＋ Live2D 角色

- 優點：最省、最快出畫面、與 `web-live2d-viewer` 的資產（模型、表情、降級邏輯）直接接；像素世界（`pixel-angela`）也能當第二種房間。
- 缺點：沒有真 3D 景深，運鏡只能是 2.5D（平移／縮放／視差）。

### 3.4 決策

**採 C 為主、A 為輔、B 當第二後端**，並用一層 `SpacePort` 介面把三者隔開：

```
                    ┌────────────────────────────┐
   MultiRole        │  SpacePort (統一介面)       │
   Orchestrator ───▶│  spawn/move/play/see/shot  │
   (角色大腦)        └──────┬─────────┬──────────┘
                            │         │
                   ┌────────▼──┐  ┌───▼────────┐
                   │ web_stage │  │ luanti     │
                   │ (主線)     │  │ (第二後端)  │
                   │ 2D/2.5D   │  │ 3D voxel   │
                   └───────────┘  └────────────┘
```

理由：**大腦與場地必須能分開換**。今天用 2D 舞台把「多角色＋換裝＋運鏡＋錄影」跑通，明天要 3D 時只換 `SpacePort` 實作，`RolePlayAgent` 一行都不用改。Luanti 保留為「已經能跑的 3D 場地」，但它的動作集（goto/dig/place）是**世界操作**，不是**表演動作**，兩者不混。

---

## 4. 核心資料模型

### 4.1 Room（`space/rooms/*.json`）

```json
{
  "room_id": "studio_a",
  "name": "天使工房・攝影棚",
  "kind": "stage",
  "size": { "w": 16, "h": 9, "unit": "m" },
  "background": "assets/rooms/studio_a/bg.webp",
  "floor": { "y": 0.0, "material": "wood" },
  "spawn_points": [{ "id": "center", "x": 8, "y": 0, "z": 0.0 }],
  "props": [{ "prop_id": "sofa", "x": 3, "y": 0, "z": 0.2, "interactive": true }],
  "lighting": { "preset": "soft_day", "intensity": 0.8 },
  "camera_presets": ["wide", "medium", "close", "over_shoulder"]
}
```

### 4.2 Actor（執行時）

```python
@dataclass
class Actor:
    actor_id: str            # 通常 = role_id
    role_id: str             # 指向 ai.roleplay.Role
    avatar_id: str           # 指向 space/avatars/*.json
    room_id: str
    position: tuple[float, float, float]
    facing: float            # 弧度
    state: str               # idle / walk / talk / sit / custom:<id>
    visible_to: set[str]     # 誰看得到（沿用 RoleContext 的可見性語意）
```

### 4.3 Avatar（`space/avatars/*.json`）— 形象與穿著

```json
{
  "avatar_id": "angela_base",
  "model": { "type": "live2d", "path": "models/Epsilon_free", "scale": 1.0 },
  "body": { "height": 1.62, "build": 0.5 },
  "wardrobe": {
    "outfit": "casual_01",
    "slots": {
      "top":    { "item": "hoodie_blue",  "tint": "#3b6ea5" },
      "bottom": { "item": "skirt_plaid",  "tint": "#6b4f3a" },
      "shoes":  { "item": "sneakers",     "tint": "#f2f2f2" },
      "accessory": { "item": "ribbon",    "tint": "#d94f70" }
    }
  },
  "expression_channels": ["neutral", "smile", "blush", "wink", "sad"],
  "motion_set": "angela_core"
}
```

**穿著是資料，不是貼圖**：每個 slot 是一個可換的 `item`＋`tint`，換裝＝改 JSON＋重繪，不重新建模。這讓「AI 自己改形象」變成一次 `update_avatar(slot, item, tint)` 呼叫，而不是美術流程。

### 4.4 Motion（`space/motions/*.json`）

```json
{
  "motion_id": "wave_hello",
  "loop": false,
  "duration_ms": 1800,
  "blend_in_ms": 150,
  "tracks": [
    { "bone": "arm_r", "keys": [[0, 0.0], [450, 1.2], [1200, 1.2], [1800, 0.0]] }
  ],
  "live2d": { "group": "TapBody", "index": 0 }
}
```

- 兩種來源：**手寫 keyframe**（上面這種）與 **Live2D motion3.json**（直接引用模型自帶動作）。
- 播放器只認 `motion_id`＋優先級，不認來源，所以日後接外部動捕（BVH/VRM）不用改呼叫端。

### 4.5 Camera / Shot / Stream

```json
{
  "shot_id": "take_01",
  "camera": { "preset": "medium", "move": [{"t": 0, "pos": [8, 1.4, 4]}, {"t": 3000, "pos": [8, 1.4, 2.5]}] },
  "target_actor": "main",
  "range": { "from_ms": 0, "to_ms": 6000 },
  "output": { "format": "webm", "fps": 30, "resolution": [1920, 1080] }
}
```

`Stream` 與 `Shot` 同構，只是 `output` 換成 `{"protocol": "rtmp", "url": "rtmp://…"}`。

---

## 5. 階段（S0–S6）

> 每階段都要能**獨立驗收**；沒過驗收不進下一階段。估時是「一個人、有既有基建」的前提。

### S0 — 舞台骨架（3–5 天）✅ 2026-10-28

- [x] `apps/space-studio/`：**零建置**（`type: module` + ES modules），canvas 2.5D 房間、地板線、出生點。刻意沒用 Vite——`python3 -m http.server` 從 repo 根目錄就能跑，少一層工具鏈。
- [x] `SpacePort`（`spawn / despawn / move / face / play / express / look / visibleFrom / snapshot`）＋ 程序化 `web_stage` 實作。
- [x] 一個 Actor（`main`）：呼吸相位、移動平滑插值、動作計時（loop／一次性）、六個表情通道、穿著四槽上色。
- [x] 鏡頭：`wide / medium / close / over_shoulder / free`，世界→像素投影是純函式；`free` 可拖曳平移。
- [x] 錄影：`canvas.captureStream` + `MediaRecorder`，codec 探測（vp9 → vp8 → webm → mp4），停錄直接下載 WebM。
- [x] 驗收：`cd apps/space-studio && node --test` → **34 passed**（生命週期、插值、動作、可見性、投影、換裝、錄影 blob、renderer headless 冒煙）；靜態伺服 6 個資產全 200。

> 與原計畫的差異（誠實記錄）：角色是**程序繪製**，不是 Live2D——`avatar.model.path` 已預留 `models/Epsilon_free`，S1 再接載入器；測試數從「8」增加到 34（多出來的是 renderer 冒煙與錄影邊界）。

### S1 — 多角色同場（3–5 天，依賴 P1-3 ✅ / P2-4 ✅）— 前半落地

- [x] 接角色：`space/roles.json` 名冊（main / role_b / role_c）→ `spawnRoster()` 每個角色一個 Actor，各自 avatar、位置、表情通道。
- [x] 共享/私有可見性：`Actor.visibleTo` 決定「誰在誰的畫面裡」；`SpacePort.visibleFrom(viewer)` 已是純資料過濾，測試守住「對 role_c 隱藏 role_b」。
- [x] 說話：`Actor.say()` 氣泡狀態（含 CJK 逐字換行），三人輪流說話的節奏由 `scriptedBeat()` 驅動。
- [x] Live2D 探測：`detectLive2D()` 只回答「有沒有 Cubism runtime」，UI 誠實顯示目前是程序繪製（**載入器未接，S1.5**）。
- [x] 後端 WebSocket 廣播演員狀態（位置／表情／動作）：`services/space/`（`SpaceService` + `space_ws.py`，端點 `/ws/space`）。加入時先送權威快照，之後每個 action 廣播新快照；壞訊息只回 `space.error`，不斷線。啟動時用 `space/roles.json` 種好舞台（`SPACE_SEED_ROLES=0` 可關）。
- [x] 前端同步：`ws_client.js`（重連、狀態回報）＋ `snapshot_sync.js`（把快照套回 `SpacePort`，快照裡沒有的演員會被移除）。**連不上後端就留在本機模式**，不是壞掉。
- [ ] 驗收（兩個視窗同步、斷線重連恢復）——程式與測試已具備，實機雙視窗驗收待做。

### S2 — 形象編輯（4–6 天）— 一半落地

- [x] 衣櫃 UI：`space/wardrobe/catalog.json`（4 槽 × 3 件 × 各 2–4 色）→ 選槽 → 選件 → 點色票即時換。目錄由測試守住（每件都能套用、色碼合法、同槽 id 不重複）。
- [x] 版本化與回滾：`OutfitStore` 每次換裝 `rev+1`，保留 20 步 undo；`restore()` 可從快照還原。
- [ ] 存檔到 `space/avatars/`：**改成 localStorage**（瀏覽器不能寫檔），要寫回 JSON 需要後端端點（未做）。
- [ ] AI 自己改：`update_avatar(actor_id, slot, item, tint)` 尚未暴露成工具；目前只有人點 UI。
- [ ] 驗收：換裝後重整仍在（localStorage 已可）——真機驗收待做；「AI 觸發換裝」依賴上一項。

### S3 — 動作編輯（5–8 天）

- [ ] 時間軸編輯器：加 keyframe、拖曳、loop、blend；預覽即時播放。
- [ ] 動作庫：`wave_hello`、`nod`、`sit_down`、`turn_around`、`idle_a/b`（各 1–2 秒，先夠用）。
- [ ] 觸發規則：`AL 狀態 → 動作`（疲勞→`yawn`、開心→`bounce`），與 `PersonaEngine` 的 tone 對齊。
- [ ] 驗收：編輯一個 3 秒動作→存檔→別的角色也能用；`play(motion_id)` 在 100ms 內起播。

### S4 — 鏡頭與錄影（3–5 天）

- [ ] 機位預設＋運鏡曲線（位置／看向／焦距三軌）；orbit 自由視角一鍵切回機位。
- [ ] 錄影：`canvas.captureStream(30)` + `MediaRecorder`（WebM/VP9）＋音軌（TTS 輸出可選）。
- [ ] `Shot` 排程：按時間軸錄 5 秒，自動存到 `data/recordings/`，附 `shot.json`。
- [ ] 驗收：錄一段 5 秒有運鏡的影片，檔頭可播放、音畫同步誤差 < 80ms。

### S5 — 直播（5–8 天，**外部條件：推流位址／平台帳號**）

- [ ] 後端 `stream_relay`：WebRTC → RTMP（ffmpeg）或直接 WebRTC 對接；斷線自動重連。
- [ ] 場景切換（多機位／切房間）＋聊天回饋（觀眾訊息進 `RoleContext` 的 `viewer` 通道）。
- [ ] 安全：推流金鑰不落前端；`visible_to` 在直播時要能遮罩私有 overlay。
- [ ] 驗收：本地 RTMP 伺服器（nginx-rtmp）收到畫面；聊天訊息 2 秒內被角色讀到。

### S6 — 增量更新與微調（持續）— 一半落地

- [x] 房間熱載入：`watchJson()` 每 5 秒輪詢 `space/roles.json` 對應的 room JSON，內容變了才回呼（改色盤不用重啟，也不用重新整理）。輪詢是刻意的——靜態伺服器也能用。
- [x] feature flag：`SPACE_FEATURES=motion,camera,record`（或 localStorage `space.features`）→ 缺席的區塊建好但 `hidden`，之後打開不必重載模組。
- [ ] 衣櫃／動作目錄熱載入（同一支 `watchJson` 可接，尚未接線）。
- [ ] A/B：同一個 `motion_id` 兩個版本，用 `al_state` 分組看哪個更常被觸發。
- [ ] 驗收：改 `room.json` 燈光 → 5 秒內生效（程式已具備，實機待驗）；關掉 `record` flag → UI 沒有錄影區塊。

---

## 6. 增量更新與微調機制（S6 的具體做法）

| 層 | 機制 | 為什麼 |
| --- | --- | --- |
| 資料 | JSON + `space_rev` 版本號；前端比對版本號決定是否重載 | 改場景／衣服不用重啟後端 |
| 介面 | `SpacePort` 只增不改；新能力用 `capabilities()` 宣告 | 換後端（Luanti/3D）不動呼叫端 |
| 功能 | `SPACE_FEATURES` 環境變數＋前端 `hasFeature()` | 半成品可以上線但不出現在 UI |
| 動作 | `motion_id` 別名表（`wave` → `wave_hello_v2`） | 換動作不動觸發規則 |
| 模型 | `backend_slot`（已落地於 `ai/roleplay/role.py`） | 角色換模型不影響空間 |

---

## 7. 與既有系統的接點

| 接點 | 現況 | 空間要加什麼 |
| --- | --- | --- |
| `MultiRoleOrchestrator`（`ai/roleplay/multi_role_orchestrator.py`） | 已能 register / turn / group_turn | S1 把 Actor 生成／銷毀掛在 register/unregister |
| `RolePlayAgent`（`ai/roleplay/role_play_agent.py`） | 已有 persona 注入＋backend_slot 強制 | S1 把 `respond()` 的結果餵給 `play("talk")`＋字幕 |
| `PersonaEngine`（per-role） | 已支援 `get_persona_engine(role_id)` | 表情通道映射：tone → expression |
| AL 狀態（fatigue/stress/valence） | 已進 persona prompt | S3 動作選擇：閾值表放 `space/rules/al_motion.yaml` |
| 記憶 namespace（P1-3，**未做**） | 角色記憶尚未分 namespace | 空間事件（誰對誰做了什麼）要寫進各自 namespace |
| Live2D 資產（`apps/web-live2d-viewer`） | 模型、表情、降級邏輯 | S0 直接複用，不重寫載入器 |
| Luanti 橋接（`apps/luanti-mods`） | 3D 世界＋移動原語 | S6 之後可作 `SpacePort` 第二實作 |
| WebSocket | 需確認既有廣播通道（`services/*websocket*`） | S1 加 `space.state` 主題 |

---

## 8. 風險

| 風險 | 影響 | 緩解 |
| --- | --- | --- |
| Live2D 授權（Cubism SDK） | 商用直播可能受限 | 先確認 `Epsilon_free` / `miara_pro_en` 的授權條款；必要時改 VRM/自繪 |
| 瀏覽器錄影 codec 不一致 | Safari 只能 MP4/H.264 | 偵測 `MediaRecorder.isTypeSupported`，失敗時降級 MP4 或後端 ffmpeg 轉檔 |
| 直播延遲 > 3 秒 | 聊天互動像自言自語 | WebRTC 優先；RTMP 只作備援，UI 標示延遲 |
| 多角色同場的 GPU 壓力 | 幀率掉到 20 以下 | 只渲染 `visible_to` 內的 Actor；表情／動作用 CPU 端插值，不上傳每幀紋理 |
| 形象編輯被濫用（不當穿著） | 平台風險 | slot 白名單＋`tint` 只允許色相偏移；直播模式禁用自由上傳 |
| 與 `MULTI_ROLE_PLAY` 進度耦合 | S1 卡住 | S0 不依賴它（單 Actor 先跑通），S1 才接 |

---

## 9. 成功標準（可驗收，不是感覺）

1. **同場**：3 個角色在同一個房間，各自 30 秒內完成「移動→做動作→說話」三件事，幀率 ≥ 30fps（1080p、內顯）。
2. **換裝**：從 UI 換 4 個 slot 的衣服，畫面 200ms 內更新，重整後仍保留。
3. **動作**：新增一個 3 秒自訂動作，不寫程式（只用編輯器），別的角色可立即使用。
4. **錄影**：錄 10 秒帶運鏡的片段，音畫同步誤差 < 80ms，檔案可直接播放。
5. **直播**（有外部條件才驗）：推流 10 分鐘不斷線；觀眾訊息 2 秒內進入角色上下文。
6. **增量**：改 `room.json` 任一欄位，5 秒內生效，不需重啟。

---

## 10. 檔案變更清單

### 新增

| 路徑 | 用途 |
| --- | --- |
| `apps/space-studio/` | 舞台前端（Vite + canvas + Live2D 載入） |
| `apps/space-studio/src/space_port.js` | `SpacePort` 介面與 `web_stage` 實作 |
| `apps/space-studio/src/actors.js` | Actor 生命週期、可見性、插值 |
| `apps/space-studio/src/camera.js` | 機位與運鏡 |
| `apps/space-studio/src/recorder.js` | `captureStream` + `MediaRecorder` |
| `apps/space-studio/src/motion_editor.js` | 時間軸編輯器（S3） |
| `apps/space-studio/src/wardrobe.js` | 衣櫃 UI（S2） |
| `space/rooms/studio_a.json` | 第一個房間 |
| `space/avatars/angela_base.json` | 第一個 Avatar |
| `space/motions/*.json` | 動作庫 |
| `space/rules/al_motion.yaml` | AL 狀態 → 動作 |
| `apps/backend/src/services/space/space_service.py` | 後端：房間／演員狀態、WS 廣播、錄影索引 |
| `apps/backend/src/services/space/stream_relay.py` | S5 推流 |
| `tests/space/test_space_port.py` | 介面契約測試（≥ 15） |
| `tests/space/test_actor_visibility.py` | 可見性與共享語意（≥ 10） |
| `tests/space/test_avatar_wardrobe.py` | 換裝與版本（≥ 10） |

### 修改

| 路徑 | 改動 |
| --- | --- |
| `ai/roleplay/multi_role_orchestrator.py` | `register()` 可選回呼 `on_actor_spawn`（S1） |
| `ai/roleplay/role_play_agent.py` | `respond()` 回傳 `motion_hint`（S3） |
| `apps/web-live2d-viewer/js/...` | 抽出模型載入器供 `space-studio` 重用（不刪原檔） |
| `docs/06-project-management/plans/MULTI_ROLE_PLAY_AGENT_PLAN.md` | 標註 S1 依賴 P1-3／P2-4 |

### 不動

`apps/luanti-mods/`、`apps/game-rpg/`、`apps/pixel-angela/`（只讀不寫；S6 之後才考慮 Luanti 後端）。

---

## 11. 非目標（這版不做）

- 不做開放世界地圖編輯器（房間是 JSON 手寫＋少量預覽）。
- 不做角色捏臉（只有體型參數與穿著槽）。
- 不做多人大廳／配對（單機或單一直播間）。
- 不做語音驅動嘴型（`TTS → viseme` 是 S7 之後）。
- 不改 Luanti 客戶端。

---

## 12. 參考

### 專案內部

- `docs/06-project-management/plans/MULTI_ROLE_PLAY_AGENT_PLAN.md` — 角色大腦（本計畫的上游）
- `docs/03-technical-architecture/al-engine-contract.md` — AL 狀態欄位（疲勞／壓力／價性）
- `docs/02-game-design/MAP_AND_SCENES.md`、`CHARACTER_SYSTEM.md`、`ITEM_EQUIPMENT_SYSTEM.md` — 場景與裝備的既有語意
- `apps/pixel-angela/world_manifest.md` — 像素世界的物件契約（未實作，但欄位可沿用）
- `apps/luanti-mods/README.md` — 3D 世界橋接與動作原語
- `apps/web-live2d-viewer/index.html`、`js/shared-js/angela-character-config.js` — Live2D 載入與表情

### 外部

- Live2D Cubism SDK（模型／動作格式與授權）
- VRM / three-vrm（若要轉 3D 角色）
- `MediaRecorder` + `canvas.captureStream()`（瀏覽器錄影）
- OBS WebSocket / nginx-rtmp（推流與場景切換）
