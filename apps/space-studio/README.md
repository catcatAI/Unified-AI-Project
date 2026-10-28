# Space Studio (S0)

一個房間、一個角色、可調鏡頭、可錄影。這是
[`INTERACTIVE_SPACE_PLAN.md`](../../docs/06-project-management/plans/INTERACTIVE_SPACE_PLAN.md)
的 S0 骨架：**沒有建置步驟、沒有依賴**，資料在 `space/`，舞台在這裡。

## 跑起來

```bash
# repo 根目錄
python3 -m http.server 5174
# 開 http://127.0.0.1:5174/apps/space-studio/
```

必須從**根目錄**起伺服器（頁面用相對路徑讀 `space/rooms/…`），直接雙擊
`index.html` 會因為 `file://` 的 CORS 限制讀不到 JSON。

## 測試

```bash
cd apps/space-studio && node --test
```

30+ 個測試，覆蓋 `SpacePort` 生命週期、移動插值、動作時長、可見性、鏡頭投影、
換裝版本、錄影 blob 交棒，以及 renderer 的 headless 冒煙測試（用會記錄呼叫的假
2D context，不需要瀏覽器）。

## 檔案

| 檔案 | 職責 |
| --- | --- |
| `src/space_port.js` | `SpacePort`：spawn/despawn/move/face/play/express/look/snapshot |
| `src/actors.js` | `Actor`：呼吸、移動插值、動作計時、表情通道 |
| `src/camera.js` | 機位預設、世界→像素投影（純函式） |
| `src/wardrobe.js` | 穿著＝`{slot: {item, tint}}`，換裝回傳新 avatar 並 `rev+1` |
| `src/renderer.js` | 唯一碰 2D context 的檔案（換 Live2D/three.js 時只換它） |
| `src/recorder.js` | `canvas.captureStream` + `MediaRecorder`，含 codec 探測 |
| `src/main.js` | 載入 JSON、跑 rAF 迴圈、綁 UI |

## 後端（選配）

連得上 `ws://127.0.0.1:8000/ws/space` 就以後端為權威：`ws_client.js` 訂閱、
`snapshot_sync.js` 把快照套回 `SpacePort`（快照裡沒有的演員會被移除）。連不上
就留在本機模式，不是壞掉。後端啟動時用 `space/roles.json` 種好舞台，
`SPACE_SEED_ROLES=0` 可關。後端位址可用 `window.SPACE_WS_URL` 覆寫。

## 這版刻意不做

- 沒有 Live2D 載入器（角色是程序繪製；`avatar.model.path` 已預留給 S1.5）
- 沒有動作編輯器（S3）
- 沒有推流（S5）

## 已知邊界

- 錄影在 Safari 會退回 `video/mp4`；`pickMimeType` 已按 `isTypeSupported` 排序探測。
- `visible_to` 目前只是資料：前端用它決定畫誰，後端 `/ws/space` 仍是**整房廣播**，不做每觀眾過濾。真正的私密性要在 S2 之後做（per-viewer snapshot）。
