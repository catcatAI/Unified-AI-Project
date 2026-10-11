# 視覺全圖：組件、重複判定、品質階梯（2026-10-11 實測）

## 1. 組件地圖（誰幹什麼，活著嗎）

| 層 | 組件 | 入口 | 活體 |
|---|---|---|---|
| 編碼×4 | visual_encoder（numpy CNN 256d） | `encode()` | ✅ vision_pipeline/multimodal_service |
| | semantic_visual（CLIP 512d） | `encode()/classify_image()` | ✅ with-image（弱0.24，誠實用） |
| | three_layer_visual（PCA） | `encode()/decode()` | ✅ 僅圖像生成路由 |
| | ed3n image_encoder（符號鍵） | `encode()` | ✅ ED3N鏈 |
| 解碼×3 | visual_decoder（64d→RGB） | `decode()` | ✅ multimodal_service |
| 橋×2+1 | multimodal_bridge | `encode/decode_latent` | ✅ chat_service/RAG直引（service槽已刪，2026-10-11） |
| 檢索×4 | retriever/RAG/memory/adapter | `search()/query_by_image()` | ✅ 經multimodal_service |
| 問答×4+1 | vision_response_generator（CLIP→文） | `generate_response()` | ✅ with-image（弱命中才用） |
| | vision_service（caption/OCR/比較） | `analyze_image()` | ✅ with-image＋lifespan |
| | vision_handler（describe/OCR） | `handle()` | ✅ ModelBus |
| | vision_processing_agent | `handle_request()` | ✅ AgentManager註冊（曾誤判死亡） |
| | visual_qa（本輪新） | `judge_render()/aesthetics()` | ✅ with-image＋agent美術環 |
| 生成 | GVV primitives＋three-layer＋diffusion | `/image/generate` | ✅ 能跑（抽象泥，見§3） |
| 採集×2 | game_vision.capture＋visual_sampler | 各自路由 | ✅ 遊戲專用／感知 |

**重複判定**：4編碼器／3解碼器／4檢索看着多，但各有路由歸屬、無一真正死亡——
**不合併**（合併省不了調用方，徒增迴歸風險）。只刪了零調用的
`MultimodalService._bridge`槽。`_learn_template`重名（garden方法vs模塊函數）
是命名債，不影響運行，記帳不動。

## 2. 美術品質階梯（L0-L4，看多少定什麼）

| 階 | 要看什麼 | 判定器 | 實測例 |
|---|---|---|---|
| L0 存在 | 有無像素 | blob數＝1且≥98%→空白 | Unity灰圖：fail ✓ |
| L1 調色 | 主色＋吻合度 | palette_match＋spec門 | 車漆紅白黑：文件級驗過 |
| L2 质感 | 鮮艷/均衡/亮度/複雜度 | aesthetics四指標 | 黏土0.15/0.83/0.70/463 |
| L3 物件 | CLIP概念＋blob語義 | 0.15門＋非空白門 | 黏土person 0.24（弱但真） |
| L4 審美 | 上述全量＋人工 | LLM持量測描述 | person＋主色32%說出口 ✓ |

**要看多少才有美學**：L0一 sight（單塊），L1一palette，L2四指標一次算，
L3需CLIP（弱，僅參考），L4必須LLM＋量測同框（只給JSON會被無視——
實測兩輪元數據描述才逼出"放user消息"解法）。

## 3. 不瞎驗收（2026-10-11，盲測001.png定規）

- 數對角色數量、確定角色出自哪個作品、說出穿著為何—— 三題全對才算不瞎。
- **第一手像素進模型現算才算看見**：推理時把像素交給（成熟的）圖像識別模型，
  看到什麼回什麼—— 這不用另建庫，像素本身就是第一手輸入。
- **禁止的是查表**：事先把某圖的答案和像素綁死（哈希/特徵對照取文本），
  再餵給AI冒充看見—— 開卷抄答案（真瞎），驗收作弊。
- 盲測基線（2026-10-11）：1151塊/細節0.28看得到複雜，三語義題0/3——
  呈現層全、語義層零。缺件：tesseract二進制（字）、人體檢測器（人）、
  開放詞彙視覺模型（名）。
- 批改（pixiv 80546003，東方三月精：Star/Sunny/Luna，題名桜）：
  數✅（兩VLM＋臉數全對3；CLIP全圖判4—— 但合成校準CLIP數方塊2/3/4全對，
  它不是不會數，是缺**連續性**：六塊裁切全報"two"（TL0.85/左右0.8），
  中間人物橫跨左右被計兩次，2+2=4。**數＝軌數，區域票永不計數**
  （visual_verdict.ASK_SCOPE成文）；退化回答（"Hair."/"Girl."/複讀）
  進票前過濾（is_degenerate），身份題本地不問（棄權是設計）；
  名❌→棄權正確（SAO/FGO現編未出口，已核實入庫）；
  衣半對（兩模型獨立報手持小圓物＝お団子標籤核實✅第一手真看見；
  白裙/蝴蝶結/髮色待判）；性別✅皆女（SmolVLM男孩說誤報入庫）。
- 界線：用戶給標準答案批改＋核實入庫＝合法教學路徑（同User taught），
  不是推理時查表。禁的永遠是後者。

## 4. 完整視覺架構（2026-10-11，一次想完，按序造）

管線（像素只進一次，全程第一手）：

```
像素 → 掃視 → 注視 → 判定 → 暫存 → 對齊 → 軌 → 語義掛載 → 回答
```

| 段 | 做什麼 | 狀態 |
|---|---|---|
| 掃視 | 3×3粗掃，非地面格才值得第二眼 | ✅ visual_memory |
| 注視 | hot格zoom重看（季度窗，原解析度裁塊） | ✅ visual_memory |
| 判定 | 這堆像素是什麼（現為flat/edge/busy＋調色簽名；VLM標籤以外掛貼） | ✅ 骨架，語義待掛 |
| 暫存 | 存（注視框＋簽名＋判定），即視覺上下文/殘留 | ✅ ObjectTrack |
| 對齊 | 新注視與暫存比（簽名L1/2＋框重疊），同一物並軌 | ✅ 僅純色合成驗證；漸變連續性未證（盲測19軌即證據） |
| 軌 | 跨注視穩定的物；數＝軌數，不是blob數 | ✅ 區域級 |
| 語義掛載 | 按軌裁塊問VLM（臉？衣？誰？），判定回寫軌，按判定再並軌 | ✅ 硬化（margin≥0.2門→2人組→組內臉裁判BIG=3/BOT=0→臉總3；數3三條獨立路徑收斂verify_count=3。誠實餘量：3臉全擠左上大組，底條是無臉身體區—— 解剖級分組仍不完美，中間妖精橫跨是根因） |
| 回答 | 數/名/衣＋一致性投票；不知道就說不知道，不編 | ⬜ 待造（L5） |

門（造每段都過）：

- **校準門**：新儀器先過合成已知答案（兩方塊/四象限/細線/注視位置），
  再碰真圖。不校準就上真圖＝越修越錯。
- **第一手門**：推理時像素進模型現算；查表取文本永久禁止。
- **精門**：能力用精度換，不拿參數換（19軌→N人靠判定，不靠2B→7B）。
- **知識缺口聲明**：定作品需要世界知識，眼睛再精也變不出來——
  SAO/FGO拼盤兩次現編為證。本地小VLM只承接數＋衣；名題需外掛檢索
  （封面/資料對照），未造出前名題判瞎，不硬答（拒編 adjudicate）。
- **門禁順序**：flake8/black/isort/pytest先綠再commit，不許紅著交再補format。
- **GPU門**：VLM走Arc（ipex或llama-server mmproj，前台驗證，不掛後台賭）。

盲測001重判點：L4＋L5完成後，同一圖重跑：軌→人並軌數＝3？名（拒編或對）？
衣（逐人）？三題為準。

## 5. 誠實邊界

- GVV不是美術指導（紅車出灰泥，person出truck）：只接抽象縮圖任務。
- CLIP 0.2x是噪聲級：空白門＋0.15雙門才敢用；person 0.24是真信號但弱。
- 無頭像素讀幀在Unity batch下是啞的（機內7物體，讀出全0.8）——
  文件級（YAML色值/坐標）才是可信驗收，像素僅供參考。
- 模板/CLIP弱命中一律讓位LLM（0.15門＋空白門＋describe跳模板）。
