# Card Import Pipeline — 卡片導入與角色扮演工具化組件

> **目標**: 從 `G:\我的雲端硬碟\卡片堆` 導入卡片，使 Angela 能學會角色扮演、寫故事、演戲、畫漫畫
> **日期**: 2026-05-27
> **狀態**: Phase 0 (數據結構) ✅ + Phase 1 (自動解析引擎) ✅ + Phase 2 (Angela/LLM層) ✅

---

## 1. 現狀分析

### 1.1 卡片堆結構 (`G:\我的雲端硬碟\卡片堆`)

| 目錄/文件 | 說明 |
|-----------|------|
| `《迴廊之弦：秩序與熵增的交響》/` | 第一世界觀設定集 |
| `《艦娘：三戰餘暉》/` | 第二世界觀設定集 |
| `原始文件/` | 原始未處理文件 |
| `*.gdoc` (30+ 文件) | Google Docs 格式，含 CC/SL/E/RC 各類卡片 |

卡片類型: `CC` 角色卡, `SL` 故事線卡, `E` 事件卡, `RC` 規則卡
編號體系: ~222 張卡片 (97 多元宇宙 + 125 實證主義)

### 1.2 現有代碼庫可復用組件

| 組件 | 路徑 | 可復用於 |
|------|------|---------|
| `PersonalityManager` | `ai/personality/personality_manager.py` | 角色特質裝載、dot-notation 存取 |
| `DocumentBuilder` | `ai/dialogue/document_builder.py` | 多段卡片生成、格式學習 |
| `TemplateLibrary` | `ai/memory/template_library.py` | 卡片格式存儲與復用 |
| `IntentRegistry` | `core/intent_registry.py` | "導入卡片" 意圖檢測 |
| `GradientField/MemoryAttractor` | `ai/memory/attractor_field.py` | 敘事引力 — 狀態拉向角色特質 |
| `PotentialFieldEngine` | `core/engine/cognitive_operations.py` | 特質間引力/衝突計算 |
| `InfluenceSpace/GravityRule` | `core/influence/space.py` | 特質衝突解決 (可配置策略) |
| `CognitivePipeline` | `ai/memory/cognitive_pipeline.py` | 三階流水線模式 (auto→ai→llm) |
| `HAMMemoryManager` | `ai/memory/ham_memory/ham_manager.py` | 卡片作為記憶儲存 |
| `EthicsManager` | `core/ethics/ethics_manager.py` | 導入內容安全檢查 |
| `TaskExecutionEvaluator` | `ai/evaluation/task_evaluator.py` | 導入質量評分 |
| `DeviationTracker` | `ai/response/deviation_tracker.py` | 質量追蹤 |
| `RippleCascade` | `ai/memory/math_ripple_engine.py` | 級聯處理傳播 |

### 1.3 完全缺失 (需新建)

| 缺失組件 | 說明 |
|---------|------|
| 卡片文件解析器 | 解析 `.gdoc`/`.txt` 為結構化 `Card` 對象 |
| 確定性正則解析引擎 | Regex 模式匹配標準欄位 |
| 三階流水線框架 | auto→angela→llm 處理調度器 |
| 時間線衝突解決器 | 依文件時間自動覆蓋/合併 |
| 文本引力系統 | 核心特質自然牽引衝突解決方向 |
| 插圖導入/生成器 | 立繪自動關聯、裁剪、提示詞生成 |
| 導出打包器 | JSON/Markdown/HTML/PDF 導出 |
| 雙視角閱覽 UI | 表單 + 關係星雲圖 |

---

## 2. 系統架構

### 2.1 三階處理流水線

```
[卡片堆 *.gdoc/.txt]
        │
        ▼
┌─────────────────────────────────────────────────┐
│ Stage 1: 自動程序 (Auto)                         │
│ ● 正則解析標準欄位 (card_id, name, world_line...) │
│ ● 表格語意映射 (key: value → form field)          │
│ ● 跨文件合併 (同 world_line 內依 qualified_id 合併)               │
│ ● 時間戳排序 (LastWriteTime 決定優先級)           │
│ ● 基礎衝突檢測 (世界線/數值/格式)                  │
│ 輸出: StructuredCard + unresolved_fields          │
└──────────────────────┬──────────────────────────┘
                       │ (有剩餘未解析內容?)
                       ▼
┌─────────────────────────────────────────────────┐
│ Stage 2: Angela 核心處理                         │
│ ● 文本引力場分析 → 核心特質牽引方向判定            │
│ ● Token 提取 (從自然語意中萃取特質/強度)           │
│ ● 時間序列推理 (舊→新的合理演變)                   │
│ ● 動態欄位分類 (新欄位 → custom_fields)           │
│ ● 基調共振檢測 (tone + core conflict 一致性)       │
│ 輸出: ResolvedCard + conflict_report              │
└──────────────────────┬──────────────────────────┘
                       │ (有未解決的硬衝突?)
                       ▼
┌─────────────────────────────────────────────────┐
│ Stage 3: LLM 最終裁決                            │
│ ● 僅處理 Stage 1+2 都無法解決的殘留衝突            │
│ ● 語意理解複雜的敘事段落                           │
│ ● 生成簡短的結構化摘要                             │
│ 輸出: FinalCard                                   │
└──────────────────────┬──────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────┐
│ 質檢: 原文件 + 卡片化結果 → 導入質量評分            │
│ ● 結構保留率、語意保留率、衝突解決率                │
│ ● 核心特質引力檢查 (自然趨向 vs 強制指定)           │
│ └→ 分數記錄到 DeviationTracker                    │
└──────────────────────┬──────────────────────────┘
                       ▼
              [存儲到 HAM Memory + PersonalityManager]
              [角色扮演/寫故事/演戲/漫畫能力 自動解鎖]
```

### 2.2 核心數據結構

```python
@dataclass
class Card:
    card_id: str                    # "CC-43"
    world_line: str                 # "W01", "W02", "迴廊"
    qualified_id: str               # "CC-43@W01"  (複合主鍵, 跨文件合併用)
    alternate_selves: List[str]     # ["CC-43@W02", "CC-43@迴廊"] 同位體列表
    card_type: CardType             # CHARACTER | STORY_LINE | EVENT | RULE
    name: str
    source_files: List[SourceFile]  # 原始文件列表 + 時間戳
    meta_data: Dict[str, Any]       # world_line, tone, race, address...
    tokens: List[Token]             # [{category, name, strength}]
    social_distance: List[Relation] # [{target_id, grid, nature}]
    history_events: List[Event]     # 時間序列事件
    custom_fields: Dict[str, Any]   # 動態捕獲的新欄位
    visual_data: Optional[Visual]   # 立繪路徑/生成提示詞
    core_trait: str                 # 核心特質 (文本引力錨點)
    conflicts: List[Conflict]       # 已知衝突記錄 (含用戶意圖)
```

### 2.3 文本引力系統 (Text Gravity)

核心設計: 不直接告訴 Angela/LLM "要符合核心特質"，而是通過潛在場計算讓狀態自然趨向核心特質。

```python
class TextGravityField:
    """
    文本引力場 — 利用現有 PotentialFieldEngine 的反向
    讓角色的 conflict_resolution 向量自然被核心特質牽引
    """
    def compute_gravity(
        self,
        core_trait: str,          # 如 "務實行動派"
        candidates: List[str],    # 可能的衝突解決方案
        state_matrix: StateMatrix4D
    ) -> List[Tuple[str, float]]: # [(方案, 引力分數)]
```

引力分數 = `G * trait_mass / (semantic_distance² + softening)`

- `trait_mass`: 該特質在角色歷史中的累積強度
- `semantic_distance`: 解決方案與核心特質的語意距離
- `softening`: 防止除零

**關鍵**: 分數是物理計算而非 LLM 判決，Angela 的 state_matrix 在每個週期被引力場自然牽引。衝突發生時，趨向核心特質的方案自然獲得更高權重。

---

## 3. 設計缺陷與修正

### 3.1 缺陷: 三階流水線分界不明

**問題**: Stage 1 (auto) 與 Stage 2 (Angela) 的邊界模糊。何時算「自動程序能處理」？需要有明確閾值。

**修正**: 
- 定義 `RESOLUTION_THRESHOLD = 0.85` (欄位匹配率)
- Stage 1 對每個欄位輸出 confidence score
- Confidence ≥ 0.95 → 直接採用 (auto)
- 0.70 ≤ confidence < 0.95 → Stage 2 (Angela core)
- confidence < 0.70 → Stage 3 (LLM)

### 3.2 缺陷: 文本引力缺乏校準

**問題**: 純計算引力可能導致 all-solutions-toward-mean，失去多樣性。

**修正**:
- 引入 `repulsion_factor`: 當某特質近期已被頻繁選用，產生排斥力以維持探索
- 與 `GradientField` 現有的 `curiosity`/`boredom` 機制整合
- 加入 `entropy_bonus`: 選擇多樣性獎勵

### 3.3 (已解決) .gdoc 格式不可直接解析

**問題**: `.gdoc` 是 Google Docs 的捷徑檔 (189 bytes)，非實際內容。

**解決方案**: 使用現有 `GoogleDriveService` (`integrations/google_drive_service.py`)，用 OAuth2 (`credentials.json`) 認證後透過 Drive API `files.export(fileId, mimeType='text/plain')` 直接拉取文字內容。

**實作發現**: `GoogleDriveService` 原缺少 `export_gdoc()` 方法，已補上。`gdoc_reader.py` 使用公開 API 而非訪問 `_get_service()`。

```python
# 1. 讀取 .gdoc JSON 提取 document id
# .gdoc 內容範例: {"url": "...", "doc_id": "ABC123"}
with open("card.gdoc", "r") as f:
    meta = json.load(f)
    doc_id = meta.get("doc_id") or meta["url"].split("/d/")[1].split("/")[0]

# 2. 用 GoogleDriveService export 為純文字
from integrations.google_drive_service import get_drive_service
drive = get_drive_service()
content = drive._get_service().files().export(
    fileId=doc_id, mimeType='text/plain'
).execute()

# 3. 餵入卡片解析流水線
CardImportPipeline.process(content.decode('utf-8'))
```

無需手動導出。`get_drive_service()` 已註冊到 `ServiceRegistry`。首次使用需 OAuth 授權一次 (調用 `get_auth_url()` + `exchange_code()`)。

### 3.4 缺陷: 質量判斷缺乏基準

**問題**: "原文件 + 卡片化結果 = 導入的卡片" 的質量檢查需要可量化的基準。

**修正**:
- 定義 3 維度評分: 
  1. **結構保留率** (字段完整度): `matched_fields / total_fields`
  2. **語意保留率** (N-gram 重疊率 + 命名實體保留率)
  3. **衝突解決率** (解決的衝突 / 總檢測衝突)
- 總分 = `0.3 × 結構 + 0.4 × 語意 + 0.3 × 衝突`
- 准入閾值: 總分 ≥ 0.75

### 3.5 缺陷: 角色扮演/故事/漫畫等能力是派生而非獨立

**問題**: 這些能力不應該各自獨立實現，而應該從卡片化自然衍生。

**修正**:
- 角色扮演 = `Card.persona → PersonalityManager.load_personality()`
- 寫故事 = `Card.history_events → DocumentBuilder.build()`
- 演戲 = `Card.tokens + Card.social_distance → SceneInterpreter`
- 畫漫畫 = `Card.visual_data → Composer + Stable Diffusion API`
- 全部共用同一套 `Card` 數據和 `TextGravityField`

### 3.6 缺陷: 自動衝突解決不尊重用戶意圖

**問題**: 系統可能強制「解決」用戶刻意保留的設定衝突。有些衝突是故意的：
- 用戶不希望自動處理的衝突
- 角色間的認知差異 (A 以為 B 欠他錢, B 不認為)
- 敘事需要的戲劇性矛盾

**修正**: 引入衝突分類 + 用戶意圖標記系統。

```python
@dataclass
class Conflict:
    type: ConflictType      # HARD_ERROR | INTENTIONAL | MULTIVERSE | NARRATIVE_DEVICE
    dimension: str           # world_line | numerical | tone
    description: str
    resolution: Optional[str]  # 建議解法
    user_intent: IntentFlag  # PENDING | CONFIRMED_KEEP | SUPPRESS_FUTURE
    suppressed: bool = False # 用戶已確認保留
```

### 3.7 缺陷: 多元宇宙同位體被誤判為衝突

**問題**: 同一個編號的角色在不同世界線是不同的個體（同位體/alternate selves）。`CC-43@W01`（貪婪財閥）和 `CC-43@W02`（完全不同性格）不該合併，也不該視為衝突。

**修正**: 
- Card ID 改為 `{card_id}@{world_line}` 格式，如 `CC-43@W01`
- 合併引擎只在相同 world_line 內進行
- 跨 world_line 的相同 card_id 自動識別為「同位體」，記錄 `alternate_selves: List[str]`
- 文本引力場的作用域限定於該 world_line 的核心特質

```python
@dataclass
class Card:
    card_id: str                    # "CC-43"
    world_line: str                 # "W01", "W02", "迴廊"
    qualified_id: str               # "CC-43@W01"  (複合主鍵)
    alternate_selves: List[str]     # ["CC-43@W02", "CC-43@迴廊"]
    ...
```

### 3.8 缺陷: 質量評分不區分故意衝突 vs 錯誤衝突

**問題**: 當前質量評分把「衝突解決率」視為越高越好。但對於故意保留的衝突，不解決才是正確的。

**修正**:
- `衝突解決率` 改為 `衝突處理得當率`：
  ```
  衝突處理得當率 = (正確解決數 + 正確保留數) / 總衝突數
  ```
- 故意保留的衝突 (user_intent=CONFIRMED_KEEP) 計入「正確保留」
- 質量分數計算排除已 suppress 的衝突

---

## 4. 實作路線圖

### Phase 0: 基礎卡片數據結構 [✅ 已完成]

| 步驟 | 文件 | 說明 |
|------|------|------|
| 0.1 | `core/card/card_types.py` | Card, Token, SourceFile, Relation, Event dataclasses |
| 0.2 | `core/card/card_store.py` | CardRegistry (基於 ServiceRegistry) |
| 0.3 | `core/card/__init__.py` | 公開 API |

### Phase 1: 自動解析引擎 [✅ 已完成]

| 步驟 | 文件 | 說明 |
|------|------|------|
| 1.1 | `core/card/parser/gdoc_reader.py` | 讀取 `.gdoc` 捷徑檔 → 提取 doc_id → Drive API export 文字 |
| 1.2 | `core/card/parser/deterministic_parser.py` | Regex 解析器: CC-XX, 表格欄位, Token 格式 |
| 1.3 | `core/card/parser/merge_engine.py` | 跨文件編號合併 + 時間戳排序 |
| 1.4 | `core/card/parser/conflict_detector.py` | 三維衝突檢測 (物理/數值/基調) |
| 1.5 | `core/card/parser/timeline_resolver.py` | 時間序列自動覆蓋邏輯 |

### Phase 2: Angela 核心/LLM 層 [✅ 已完成]

| 步驟 | 文件 | 說明 |
|------|------|------|
| 2.1 | `core/card/resolver/text_gravity.py` | 文本引力場 (ngram Jaccard distance + repulsion + entropy bonus) |
| 2.2 | `core/card/resolver/token_extractor.py` | 非格式化文本 → Token 提取 (顯式格式 + 關鍵詞推斷) |
| 2.3 | `core/card/resolver/llm_fallback.py` | LLM 最終裁決器 (硬編碼規則，無 LLM 依賴) |
| 2.4 | `core/card/resolver/pipeline_orchestrator.py` | 三階流水線調度器 (auto→angela→llm) |

### Phase 3: 質量控制 + 存儲 (2 天)

| 步驟 | 文件 | 說明 |
|------|------|------|
| 3.1 | `core/card/quality/import_quality_checker.py` | 三維度質量評分 |
| 3.2 | `core/card/quality/gravity_calibration.py` | 引力校準 + entropy bonus |
| 3.3 | `core/card/integration/memory_adapter.py` | Card → HAM 記憶寫入 |
| 3.4 | `core/card/integration/personality_adapter.py` | Card → PersonalityManager 特質裝載 |

### Phase 4: 派生能力 (3-4 天)

| 步驟 | 文件 | 說明 |
|------|------|------|
| 4.1 | `core/card/capabilities/roleplay_engine.py` | 角色扮演: Card.persona → 對話生成 |
| 4.2 | `core/card/capabilities/story_writer.py` | 寫故事: Card.history_events → 敘事 |
| 4.3 | `core/card/capabilities/scene_interpreter.py` | 演戲: Card.tokens + 社會距離 → 場景 |
| 4.4 | `core/card/capabilities/comic_composer.py` | 畫漫畫: Card.visual_data → 提示詞 → API |

### Phase 5: 導入/導出 UI (3-4 天)

| 步驟 | 文件 | 說明 |
|------|------|------|
| 5.1 | `core/card/export/json_exporter.py` | JSON + 立繪 ZIP 打包 |
| 5.2 | `core/card/export/html_viewer.py` | 互動 HTML 閱覽頁 |
| 5.3 | `core/card/export/pdf_exporter.py` | PDF 實體卡片排版 |
| 5.4 | (前端) 雙視角 UI: 表單 + 關係星雲圖 | 基於 Electron |

### Phase 6: 測試 + 整合 (2 天)

| 步驟 | 文件 | 說明 |
|------|------|------|
| 6.1 | `tests/core/card/test_deterministic_parser.py` | 正則解析測試 |
| 6.2 | `tests/core/card/test_merge_engine.py` | 跨文件合併測試 |
| 6.3 | `tests/core/card/test_conflict_detector.py` | 三維衝突檢測測試 |
| 6.4 | `tests/core/card/test_text_gravity.py` | 文本引力校準測試 |
| 6.5 | `tests/core/card/test_quality_checker.py` | 質量評分測試 |
| 6.6 | `tests/core/card/test_pipeline_orchestrator.py` | 全流程整合測試 |

---

## 5. 質量檢查標準

### 5.1 導入質量評分

```
總分 = 0.3 × 結構保留率 + 0.4 × 語意保留率 + 0.3 × 衝突處理得當率

結構保留率 = 匹配欄位數 / 總欄位數
語意保留率 = (1 - |原N-gram集 - 結果N-gram集| / 原N-gram集) × 0.7
           + 命名實體保留率 × 0.3
衝突處理得當率 = (正確解決數 + 正確保留數) / 總衝突數
  # 正確保留 = user_intent==CONFIRMED_KEEP 且未強制修改的衝突
  # 注意: 故意保留的衝突不應降低分數
```

### 5.2 文本引力有效度檢驗

```
引力有效度 = (自然趨向核心特質次數) / (總衝突次數)

理想值: 0.6 - 0.85
  < 0.6: 引力太弱，角色性格不一致
  > 0.85: 引力過強，角色失去成長空間
```

### 5.3 准入標準

| 標準 | 通過 | 警告 | 拒絕 |
|------|------|------|------|
| 總分 | ≥ 0.75 | ≥ 0.5 | < 0.5 |
| 結構保留率 | ≥ 0.8 | ≥ 0.6 | < 0.6 |
| 衝突解決率 | ≥ 0.7 | ≥ 0.4 | < 0.4 |
| 引力有效度 | 0.6-0.85 | 0.4-0.6 或 0.85-0.95 | < 0.4 或 > 0.95 |

---

## 6. 與現有系統的集成點

| 現有組件 | 集成方式 |
|---------|---------|
| `ServiceRegistry` | `get_registry().register('card_registry', card_registry)` |
| `PersonalityManager` | `load_personality(card.to_personality_dict())` |
| `HAMMemoryManager` | `store_experience(card.to_dict(), 'character_card', ...)` |
| `StateMatrix4D` | `apply_intent_gravity(text_gravity.compute(...))` |
| `CognitivePipeline` | 復用其 `process()` 模式作為三階流水線原型 |
| `DocumentBuilder` | `build(card.to_context(), task_type='roleplay')` |
| `EthicsManager` | `check_content(card.to_dict())` 導入內容安全 |
| `DeviationTracker` | `record_quality(quality_score)` 記錄每次導入質量 |

---

## 7. 關鍵約束

1. **LLM 僅做最終裁決**: Stage 1 auto 處理佔 ≥ 70% 工作量, Stage 2 Angela core 佔 ~25%, Stage 3 LLM ≤ 5%
2. **Google Drive 直連**: 透過 `GoogleDriveService` + `credentials.json` OAuth2，自動從 `.gdoc` 捷徑檔提取 doc_id → Drive API export 文字內容，無需手動導出
3. **文本引力不直接指定**: 引力是物理場計算後的 side effect, 非 LLM prompt 指令
4. **不可重複實作**: 優先復用 GoogleDriveService / PotentialFieldEngine / GradientField / PersonalityManager 等現有組件
5. **代理檢查**: 每次導入後需通過 proxy 對比原文件+結果, 確保質量
6. **MD 更新**: 每個 Phase 完成後更新本計畫
