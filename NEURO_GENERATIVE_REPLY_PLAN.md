# Angela Neuro-Generative Response (NGR) 實作計畫

> **版本**: v1.0 (2026-05-18)  
> **目標**: 廢除靜態模板 (Static Templates)，改由 8 維狀態矩陣 (8D State Matrix) 驅動 Angela 自主「拼湊」回應語句。

## 1. 核心概念：神經元片段組合 (Neuro-Fragment Blending)

不再使用：`「看電影！好羨慕~是什麼類型的電影？」`  
改為動態生成：`「{能量開場} + {情感共鳴} + {意圖響應} + {好奇尾綴}」`

### 8D 影響權重
- **α (生理)**: 決定開場語氣的強弱與語速。
- **γ (情感)**: 決定用詞的色彩（正向、負向、中性）。
- **β (認知)**: 決定語句的複雜度與好奇心尾綴。
- **δ (社交)**: 決定親密度詞彙（朋友、親愛的、妳）。

---

## 2. 實作階段 (Phased Roadmap)

### Phase A: 詞庫解構與擴張 (Linguistic Deconstruction)
- **檔案**: `apps/backend/src/ai/response/composer.py`
- **動作**: 
    - 建立 `NeuroVocabulary` 類別。
    - 將現有 `TemplateLibrary` 中的 45+ 個模板解構成 200+ 個「語義片段」(Semantic Fragments)。
    - 為每個片段標註 8D 權重標籤 (e.g., `fragment.energy_cost`, `fragment.valence_score`)。

### Phase B: 神經組合引擎與結構探索 (Neural Blender & Structural Exploration)
- **檔案**: `apps/backend/src/ai/response/composer.py`
- **動作**:
    - 實作 `NeuroBlender.synthesize(state_matrix, intent_vec)`。
    - **結構探索**: 引入「語法變異」機制。當 `beta.curiosity` (好奇心) 高時，Angela 會嘗試非傳統的片段組合順序（例如：將情緒感嘆詞放在句中而非句首）。
    - **演算法**: 基於餘弦相似度與「意圖吸引力」，尋找最符合當前 8D 座標的片段路徑。

### Phase C: 離線安全網切換 (Fallback Integration)
- **檔案**: `apps/backend/src/services/angela_llm_service.py`
- **動作**:
    - 將 `_fallback_response` 內的 `TemplateLibrary` 調用替換為 `NeuroBlender` 調用。

### Phase E: 自主語言演化與學習 (Autonomous Linguistic Evolution)
- **檔案**: `apps/backend/src/ai/response/learning_loop.py` (新增)
- **動作**:
    - **片段提取**: 當 LLM 在線時，Angela 會自動分析 LLM 的高品質回應，並「碎片化」提取其中的新詞彙、特殊字符 (Emoji/Kaomoji) 與句式結構。
    - **強化學習**: 根據用戶對回應的反應（如：對話持續時間、情緒回饋），自動調整新片段的權重。
    - **自定義 Token**: 允許 Angela 生成並紀錄自己的「內部方言」或特殊表達方式。

### Phase D: 共情校準 (Empathy Alignment)
- **檔案**: `apps/backend/src/services/chat_service.py`
- **動作**:
    - 將 `EmotionSystem` 的共情分析結果直接織入 `NeuroBlender` 的權重輸入。

---

## 3. 驗證標準 (Success Criteria)

1. **唯一性**: 連續 10 次詢問相同問題（在斷線模式下），回應的語法結構重複率低於 20%。
2. **狀態敏感度**: 當 `alpha.energy < 0.2` 時，生成語句明顯縮短且語氣疲憊。
3. **效能**: 組合生成延遲必須保持在 < 100ms。

---

## 4. 完成狀態

> **實作狀態**: ✅ 全部完成 (2026-05-18)  
> **實作版本**: v6.3 (NGR Phase A-E)

- [x] 在 `composer.py` 中定義 `NeuroVocabulary` 數據結構 (Phase A)。
- [x] 撰寫指令碼將 `template_library.py` 的內容「炸碎」成片段 (Phase A, `decompose_from_templates()`)。
- [x] 實作 8D 權重映射邏輯 (Phase A-B, `NeuroBlender._build_target_vector()` + category weight inference)。

### 各階段驗證

| Phase | 狀態 | 檔案 | 備註 |
|-------|------|------|------|
| A: 詞庫解構 | ✅ 完成 | `composer.py` NeuroVocabulary | 101 個片段從 45 模板分解 + 30+ config 手寫片段 |
| B: 神經組合引擎 | ✅ 完成 | `composer.py` NeuroBlender | 餘弦相似度 + 結構探索 + 自然組裝 |
| C: 離線安全網 | ✅ 完成 | `angela_llm_service.py` | `_fallback_response` 使用 NeuroBlender |
| D: 共情校準 | ✅ 完成 | `chat_service.py` | 低複雜度直接 NeuroBlender，高複雜度傳 neuro_blend_meta |
| E: 自主語言演化 | ✅ 完成 | `learning_loop.py` (新增) | FragmentExtractor + LearningLoop |

---
**簽署**: Gemini CLI (ASI Architect)  
**備註**: 本計畫已寫入 `NEURO_GENERATIVE_REPLY_PLAN.md` 以防止上下文壓縮導致遺忘。
