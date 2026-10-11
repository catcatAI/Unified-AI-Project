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

## 4. 誠實邊界

- GVV不是美術指導（紅車出灰泥，person出truck）：只接抽象縮圖任務。
- CLIP 0.2x是噪聲級：空白門＋0.15雙門才敢用；person 0.24是真信號但弱。
- 無頭像素讀幀在Unity batch下是啞的（機內7物體，讀出全0.8）——
  文件級（YAML色值/坐標）才是可信驗收，像素僅供參考。
- 模板/CLIP弱命中一律讓位LLM（0.15門＋空白門＋describe跳模板）。
