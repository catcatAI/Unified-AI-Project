# 流式響應＋窗口容器＋雙模型計劃（STREAMING_WINDOW_DUALMODEL）

- 日期：2026-10-10（實測驅動：Unity小車任務連續觸發60s HTTP超時）
- 目標：長生成不斷線（SSE流式）、流式下路由判斷不變差（窗口容器）、
  難/易任務分流雙模型（thinker/executor），三者皆可獨立驗證。
- 狀態：調查完成；Phase 0 已執行（自檢＋Vulkan根因）；Phase 1+ 待執行。

## 0. 已確認的現狀（調查結論，不再重查）

- 聊天無流式端點：僅 `/document/stream`（SSE）存在；`/chat/unified` 只回整包。
- Provider 全是非流：`llamacpp.generate` 寫死 `stream:false`（`providers/llamacpp.py:86`）；
  ollama 同級（待驗，但調用形狀一致）。
- 流式基建只有傳輸層：`ai/streaming/`（TokenStream/StreamingPipeline/ producers）
  面向 garden/ed3n 神經生產者，無 LLM token 生產者，更無判斷窗口。
- 窗口容器確認不存在：全倉只有截斷（dialogue 100/200、session-80、digest cache），
  沒有滾動判斷窗口。用戶擔憂成立：逐 token 路由窗口窄、模板更易誤發——
  必須先有窗口再談流式路由，否則只是把整包誤判切碎。
- 模型不穩根因已定位：`libggml-vulkan.so` segfault（dmesg實錘），非模型問題；
  `n_gpu_layers=0` 純CPU連跑3次全活。Unity小車當時是被腳手架崩潰拖死，
  不是Angela路由問題（5個路由bug同期已修，見 git log 3bcc1c440/e257b95bd）。
- 雙模型RAM可行：gemma 3.35GB + qwen 0.4GB + Angela本體，7GB機器剩2-3GB，
  放得下（已實測同時常駐可啟動；未做長 soak）。

## 1. Phase 0（已完成，2026-10-10）

- [x] 主AI自檢代理：`WorkspaceMountHandler._inspect`（應用＋會話＋健康），
  intent `app_mount` 復用動詞繞行，chat可問「代理狀態如何」。
- [x] 外部工作區：files agent 直列 `/home/cxuo/chip`（200上限，.gds/.mag/.ext）。
- [x] Vulkan根因＋CPU穩定驗證（3/3 alive）。

## 2. Phase 1：傳輸流式（先解決超時，不動路由判斷）

原則：流式只換「傳輸」，判斷仍用整包——窗口窄化風險為零。

- [x] P1-1 Provider流式：`LlamaCppBackend.generate(..., stream_callback)`，
  `stream:true` 發POST，逐chunk解析`choices[0].delta.content`，每token回調；
  非流調用保持原行為（`stream_callback=None`）。Ollama同形跟進（未做：無可用daemon驗）。
- [x] P1-2 腳手架shim支援`stream:true`（SSE chunk回放，真實測超時消除）。
- [x] P1-3 HTTP端點 `POST /api/v1/chat/stream`（SSE `text/event-stream`）：
  callback經context透傳進整條管線（零改動管線）；非LLM命中照常快回；
  45s stall ping＋300s總牆。活體驗收（gemma token逐個＋done）。
- [ ] P1-4 前端/調用方：desktop-app 與 web-viewer 用 EventSource 消費（若暫不改
  前端，curl/SSE驗收即可，不阻塞後端合併）。
- [x] 驗收（後端）：Unity長腳本生成不斷線（token流不斷）；首字即時（open先回）。
  斷線重連（續傳）未做：重連拿整包（可接受，記為後續）。

## 3. Phase 2：窗口容器（流式下的判斷才敢做）

只在傳輸流式驗收後動。設計（新建 `services/llm/stream_judge.py`，stdlib only）：

- [x] `StreamJudgeWindow`：滾動文本窗（336字），每8 token判一次，
  K=2連續一致鎖定；鎖定前只輸出不承諾。端點同流發鎖定事件＋done帶一致性。
- [x] 一致性門：活體鎖定unknown/full unknown一致（混合閒聊文本，穩定即過）；
  單元鎖定math/greeting全綠。模板誤發由整包既有門（無知/情感讓位）先擋，
  窗口只做穩定性投票——兩層分工，不重疊。
- [x] 不確定預設整包行為（空流永不鎖定，finalize consistent=false誠實）。

## 4. Phase 3：雙模型分流（thinker/executor）

- thinker=gemma-4-E2B（難：code/logic/open），executor=qwen2.5-0.5b
  （易：問候/社交/短答，延遲低）。注意：真正的「執行」是agent層（shell/files
  確定性執行），LLM雙模型分的是「想的難度」，不是想/動——動手面已由掛載覆蓋。
- [x] P3-1 雙槽註冊（llamacpp-gemma :8080＋llamacpp-qwen :8081，LLAMA_CPP_QWEN槽；
  ollama daemon runner壞故不用ollama協議）。寒暄走qwen（2.5s vs 6s），
  有問句守thinker；另加壞槽即時降級＋revive接回（壞active不再卡死）。
- [~] P3-2 soak：交替6請求全綠、雙shim＋主服務全活；gemma仍偶發倒
  （Vulkan已除，疑似7GB記憶體邊界），降級機制 cover，長soak待GPU機。
- [ ] P3-3 Unity小車重跑（掛載→腳本→batch→驗證全閉環），作為雙模型驗收案
  ——腳本缺穩定長生成，待LLM穩定後續跑。

## 5. 風險與不做什麼

- 不改整包路由順序（Phase 1只加傳輸）；不斷言流式更快（只不斷線）。
- 不在窗口驗收前做流式路由決策（防止模板碎片誤發放大）。
- 不把qwen當thinker（實測寫碼/規劃不夠）；不把gemma當低延遲層（CPU慢）。
- 雲端key/GPU機仍是終解，本地雙模型是過渡。
