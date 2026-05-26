# 計畫：Angela 數值→文本翻譯學習層

## 現狀（實際）

`_construct_angela_prompt()` 已具備多層次的狀態描述：

```
L1 生物層 (threshold分支 → 中文描述句)
L2-L6 軸值   (key=value:.4f 序列化)
θ 元認知    (threshold分支 → "話題新穎"/"無需校正")
η 執行      (數值格式化)
理論公式     (:.4f 序列化)
+ 用戶印象、對話歷史、Drive 檔案注入
```

回應的流向：

```
LLM 回應
  → conversation_history (50 輪)
  → deviation_tracker (JSON 日誌)
  → _store_response_as_template (HAM 持久化)
  → LearningLoop.process_llm_response() (詞彙提取)
  → _record_route_learning (配置學習)
```

已存在 9 個記憶/學習機制：conversation_history、TemplateMatcher、LearningLoop/FragmentExtractor、NeuroVocabulary、NeuroBlender、\_store_response_as_template、deviation_tracker、\_record_route_learning、HAMMemoryManager。

## 唯一缺口

現有系統缺少的是**軸點位數值→語意描述的對應學習**。

- `NeuroVocabulary` 有 8D 權重向量，但 mapping 方向是文本→狀態，不是數值→語意
- `_store_response_as_template` 存整段回應，不萃取特定軸點位的理解
- `LearningLoop` 提取句子/表情/搭配，不做數值區間對應

目標：Angela 學會把 `indolence=0.1248` 翻譯成「午後賴床不想動的感覺」，並隨著多次遇到相似數值而精化描述精度。

## 實作範圍

### Phase 1：NeuroVocabulary 擴充數值區間映射

不新增檔案，在 `ai/response/composer.py` 的 `NeuroVocabulary` 上擴充：

```python
@dataclass
class ValueRangeMapping:
    axis_field: str       # axis + point name, e.g. "gamma.indolence"
    range_lo: float
    range_hi: float
    description: str      # LLM 產生的語意描述
    confidence: float     # 0-1，基於 usage_count
    usage_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_used_at: Optional[datetime] = None

    def covers(self, value: float) -> bool:
        return self.range_lo <= value <= self.range_hi

    def narrow(self, value: float):
        """遇到新值時收斂區間"""
        self.range_lo = max(self.range_lo, value - 0.01)
        self.range_hi = min(self.range_hi, value + 0.01)
```

`NeuroVocabulary` 新增方法：

```python
def get_description(self, axis_field: str, value: float) -> Optional[str]:
    # 找出所有 covers(value) 的 mapping，回傳 confidence 最高的 description

def learn_mapping(self, axis_field: str, value: float, description: str):
    # 找現有 mapping：若 exists 且 covers → narrow + 更新 confidence
    # 若 exists 但不 covers → 新增一個 mapping
    # 若不存在 → 新增 mapping，range_lo=range_hi=value

def get_value_range_mappings(self, axis_field: str) -> List[ValueRangeMapping]:
    # 回傳指定軸點位的所有 mapping
```

**不新增檔案**，所有變更在 `composer.py` 內。`NeuroVocabulary` 已有 JSON 序列化 (`load_from_config`)，擴充 serialization 方法。

### Phase 2：注入機制（改 `_construct_angela_prompt`）

在 axis_lines 的數值後附加語意描述：

```
GAMMA: indolence=0.1248 (午後賴床不想動的感覺), trust=0.8765
```

修改點 `angela_llm_service.py:1156`：

```python
short_parts = []
for k, v in list(vals.items())[:4]:
    desc = self.neuro_vocabulary.get_description(f"{axis_name}.{k}", v)
    if desc:
        short_parts.append(f"{k}={v:.4f}（{desc}）")
    else:
        short_parts.append(f"{k}={v:.4f}")
short = ", ".join(short_parts)
```

`neuro_vocabulary` 從 `_init_response_system()` 注入。

### Phase 3：回存機制（擴充既有路徑）

不新增 LLM call。利用**既有**的 `_store_response_as_template` 和 `LearningLoop.process_llm_response()`，追加萃取：

**在 `_store_response_as_template`** 流程中加入：

```
LLM 回應文本
  → 正則萃取：找 "我感覺...", "像是...", "有點..." 等自我描述句
  → 對應到最近一次 state_for_llm 的軸點位數值
  → NeuroVocabulary.learn_mapping(axis_field, value, extracted_text)
```

無額外 LLM call。正則規則沿用 `LearningLoop.FragmentExtractor` 的既有模式（`learning_loop.py:23-42`），不新增依賴。

### Phase 4：精度自然收斂

隨著 mapping 累積：

- 同一數值多次遇到 → `narrow()` 縮小區間
- 同一區間有多個描述 → confidence 競爭，收斂到最穩定的
- 低 usage 的 mapping → 定期清除（LRU）
- 精度在詞彙庫中自然浮現，不需 `:.2f` 或 `:.4f` 的硬編碼決定

## 與 MASTER_CONSOLIDATED_PLAN.md 的衝突

A3 已完成。`_construct_angela_prompt` 已位於 `services/llm/prompt_builder.py`，Phase 2 直接修改此處。

## 不做的範圍

| 不做 | 理由 |
|------|------|
| 新增 `core/translation_vocabulary.py` 檔案 | `NeuroVocabulary` 已存在，擴充即可。零風險（已在 `ai/response/`） |
| 新增 LLM call 來萃取描述 | 專案正在減少額外 call，正則萃取已足夠（沿用 `FragmentExtractor`） |
| 覆蓋現有 prompt 描述格式 | 現有 threshold 分支描述（novelty_desc 等）保留不動，只附加 |
| session 隔離 | 沿用 `NeuroVocabulary` 的 `load_from_config` 機制，跨 session 持久化 |

## 實作狀態 (2026-05-26)

```
A3 拆分完成 ✓
  → Phase 1: NeuroVocabulary 擴充 ✅ 完成
  → Phase 2: 注入機制 ✅ 完成
  → Phase 3: 回存擴充 ✅ 完成
  → Phase 4: 持續收斂 ✅ 完成（sync_to_state_store / restore_from_state_store 整合 C5 持久層）
```

### Phase 1 變更
- `ai/response/composer.py`:
  - 新增 `ValueRangeMapping` dataclass（covers(), narrow()）
  - `NeuroVocabulary.__init__` 新增 `_value_range_mappings` dict
  - 新增 `get_description()`, `learn_mapping()`, `get_value_range_mappings()`
  - 新增 `serialize_mappings()`, `load_mappings_from_config()`（含 LRU 清除）
  - 新增 `from datetime import datetime`

### Phase 2 變更
- `services/llm/prompt_builder.py`:
  - `construct_angela_prompt` 軸格式化（line 150）改為支援語意描述附加
  - 當 `neuro_vocabulary` 參數提供時，在數值後附加 `（描述）`
- `services/llm/router.py`:
  - `_construct_angela_prompt` wrapper 傳遞 `neuro_vocabulary` 至 `construct_angela_prompt`

### Phase 3 變更
- `services/llm/router.py`:
  - `_store_response_as_template` 新增萃取流程：
    1. 正則分割回應文本為句子
    2. 匹配「我感覺/像是/有點/好像/覺得/似乎/彷彿」描述句
    3. 對應到 `context.state_for_llm` 的軸點位數值
    4. 呼叫 `NeuroVocabulary.learn_mapping()`

## 待確認

1. ~~JSON 持久化路徑？~~ → 已實作 `serialize_mappings()` + `load_mappings_from_config()`，與既有 `load_from_config` 模式一致
2. ~~雙語需求？~~ → 目前中文即可，後續可擴充 lang tag
3. ~~數量上限？~~ → 已內建於 `serialize_mappings(max_age_days=90)`：超齡低使用量 mapping 自動清除
4. ~~`serialize_mappings()` 的呼叫時機~~ → C5 Phase 4 整合：`sync_to_state_store()` 每輪學習後推至 `GlobalStateStore`，`save_all()` 自動寫入檔案；`restore_from_state_store()` 啟動時恢復
