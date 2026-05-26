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

**A3（angela_llm_service.py 拆分，pending）：** 拆分後 `_construct_angela_prompt` 會搬到 `services/llm/prompt_builder.py`。Phase 2 修改程式碼需在拆分後重新定位 injection target。建議：先完成 A3 拆分，再實作 Phase 2，避免雙重搬遷。

## 不做的範圍

| 不做 | 理由 |
|------|------|
| 新增 `core/translation_vocabulary.py` 檔案 | `NeuroVocabulary` 已存在，擴充即可。零風險（已在 `ai/response/`） |
| 新增 LLM call 來萃取描述 | 專案正在減少額外 call，正則萃取已足夠（沿用 `FragmentExtractor`） |
| 覆蓋現有 prompt 描述格式 | 現有 threshold 分支描述（novelty_desc 等）保留不動，只附加 |
| session 隔離 | 沿用 `NeuroVocabulary` 的 `load_from_config` 機制，跨 session 持久化 |

## 實作順序建議

```
A3 拆分完成 (等待中)
  → Phase 1: NeuroVocabulary 擴充 (1天)
  → Phase 2: 注入機制 (0.5天)
  → Phase 3: 回存擴充 (0.5天)
  → Phase 4: 持續收斂
```

等待 A3 期間可先做 Phase 1（純 `composer.py` 變更，無依賴衝突）。

## 待確認

1. `NeuroVocabulary` 的 JSON 持久化路徑是否與 `config_loader` 一致，還是另開檔案？
2. `ValueRangeMapping` 的 `description` 是否需要雙語（中/英）？
3. mapping 數量上限（初始建議 200，之後可調整）
