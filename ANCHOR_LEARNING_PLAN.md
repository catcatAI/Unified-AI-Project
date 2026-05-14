# Semantic Anchor Learning System — Design & Implementation Plan
## 2026-05-14 | Version 6.2.1 | Status: DESIGN DRAFT

---

## 1. 現狀診斷（Root Cause Analysis）

### 1.1 為什麼相似度這麼低？

`text_to_vector()` 演算法（`state_matrix.py:444`）：
```python
def _text_to_vector(self, text: str, size: int) -> List[float]:
    words = text.lower().split()
    vector = [0.0] * 32
    for i, word in enumerate(words):
        hash_val = hash(word) % size          # 32 取餘，碰撞極高
        vector[hash_val] += 0.5 * (1.0 if i % 2 == 0 else -0.3)
    norm = math.sqrt(sum(v * v for v in vector))
    if norm > 0:
        vector = [v / norm for v in vector]
    return vector
```

**問題：**
- 一個 6-8 詞的描述文本 → 只有 6-8 個位置被設置（大部分 hash 碰撞）
- 結果：32維向量中只有 ~5-6 個非零維度
- Cosine similarity 公式：`dot(a, b) / (||a|| * ||b||)`
  - 兩個稀疏向量：大量維度是 0 → dot product 極低
  - 即使有意義的詞重疊，由於 hash 碰撞，位置也不一定對齊
  - L2 normalize 後，||a|| = ||b|| = 1.0，但有效維度只有 ~5-6 維

**實際測量：**
| 向量類型 | 非零維度 | Cosine Sim (vs alpha anchor) |
|---------|---------|----------------------------|
| "energy comfort arousal physical body" | 4 個 | ~0.0-0.15 |
| "think learn focus curiosity understanding" | 5 個 | ~0.0 |
| 測試向量 [0.1]*31 + [0.8] | 1 個 | 0.0000 |
| 測試向量 [梯度遞增] | ~10 個 | 0.276 (ε 是最高的) |

### 1.2 為什麼 ASSIGN 閾值 (0.7) 無法觸發？

`AllocationPolicy` 的 `AssignStage` (`policy.py:113`)：
```python
if ctx.max_resonance >= self.threshold:  # threshold = 0.7
    return AllocateDecision(AllocationAction.ASSIGN, ...)
```

而 `max_resonance` 來自 `ResonanceEngine.compute_resonance()` = cosine similarity。

**實際最大相似度：**
- 最好的情況（梯度向量 vs ε anchor）：0.276
- 一般情況：0.0-0.15
- **結論：0.276 < 0.7 → ASSIGN 永遠不會觸發**

### 1.3 為什麼錨點如此稀疏？

**根本原因：沒有訓練機制，只有初始硬編碼。**

現有的 `_init_semantic_anchors()`（`state_matrix.py:403`）：
- 在 `__init__` 中用固定描述文本一次性生成
- **從不更新** — 沒有任何代碼路徑會修改 `semantic_anchors`
- 軸創建後，anchor 是靜態的

**對比其他模組的學習能力：**
- `HAMMemoryManager` — 有存儲、檢索、刪除、衰減
- `negativity.py` 的 `_misallocation_log` — 記錄錯誤分配
- `art_learning_workflow` — 有風格學習
- **但沒有一個模組會更新 semantic_anchor 向量**

---

## 2. 設計目標

### 2.1 核心問題
Semantic anchor 向量是靜態的、稀疏的，導致：
1. 輸入向量無法有效匹配到任何軸（相似度 < 0.3）
2. 分配決策全部落到 DEFER/CREATE，ASSIGN 永不觸發
3. 整個 ResonanceEngine 的相似度評分失去實際意義

### 2.2 目標
讓 semantic anchor 向量能夠從實際使用中學習，逐步調整，朝向有意義的聚類中心。

---

## 3. 系統架構

### 3.1 六軸的語義角色（設計意圖）

```
α (alpha/生理)   — 身體能量、舒適度、喚醒水平
                 錨點描述: "energy comfort arousal rest physical health"

β (beta/認知)   — 好奇心、專注、學習、理解
                 錨點描述: "think learn focus curiosity understanding cognition"

γ (gamma/情感)  — 喜怒哀懼愛恨等基本情緒
                 錨點描述: "happy sad angry fear love joy emotion feeling"

δ (delta/社交)  — 注意力、連結、信任、存在感
                 錨點描述: "social trust bond attention connection presence community"

ε (epsilon/數理) — 邏輯、精確、抽象、計算
                 錨點描述: "math logic precise calculation abstraction certainty"

θ (theta/元認知) — 新穎度、複雜度、模糊度、自我懷疑
                 錨點描述: "novelty complexity ambiguity meta cognition doubt"
```

### 3.2 學習來源

Semantic anchor 不是從天而降的，而是從真實數據中提煉出來的。學習來源包括：

```
[來源 1] 軸狀態快照
  - 每次軸更新 (`update_alpha()`, `update_beta()` 等) 產生的快照
  - 快照記錄了「某個情境下，α軸的值是 energy=0.8, arousal=0.6」
  - 這些快照是 anchor 應該靠近的「現實中心」

[來源 2] 分配決策歷史
  - `meta_allocate()` 每次決策
  - 包括：輸入向量、選擇的軸、決策類型、置信度
  - 正確的 ASSIGN 決策 = 該軸的 anchor 應該靠近輸入向量
  - 錯誤的 DEFER/CREATE = anchor 需要調整以匹配更好的相似度

[來源 3] Misallocation Log（θ 自糾）
  - `NegativityDetector._misallocation_log` 記錄了「錯誤分配的案例」
  - 錯誤分配說明：某個輸入被分配到一個軸，但後來被 θ 懷疑
  - 這是 anchor 應該遠離的「錯誤中心」

[來源 4] 軸間影響 (Influence)
  - `compute_influences()` 的計算結果
  - 影響強度揭示了軸間的實際關係
  - 例如：γ.happiness 高時 → α.tension 下降
  - 這可以指導 anchor 的相對位置

[來源 5] Feedback Loop
  - 用戶反饋、行為結果
  - 「這個分配讓我感到更好/更糟」→ anchor 應該調整

[來源 6] 外部文本關聯
  - 每次 `text_to_vector(text)` 呼叫時
  - 記錄「這段文本被映射到哪個軸」
  - 構建「文本 → 軸」映射庫，逐步完善 anchor
```

### 3.3 訓練演算法

#### 演算法 A: Anchor Drift（錨點漂移）— 基礎版

```
每次軸更新時：
  1. 快照進入 TemporalState
  2. 如果快照是「穩定狀態」（不是瞬時變化）：
     - 計算快照的 field 平均值 → 32-dim 向量
     - 用 EMA (Exponential Moving Average) 更新 anchor:
       anchor = α * anchor + (1-α) * snapshot_vector
```

**問題：** 快照只有 4-6 個 field 值（α 有 6 個），不是 32 維。需要映射。

**解決：field → vector 映射**
```python
def snapshot_to_vector(snapshot: Dict[str, float], size: int = 32) -> List[float]:
    """將軸快照轉換為 32-dim 向量"""
    # 方法：每個 field hash 到一個位置
    # field 值作為權重（歸一化後）
    vector = [0.0] * size
    for field_name, value in snapshot.items():
        pos = hash(field_name) % size
        vector[pos] += value  # 0.0-1.0
    norm = sqrt(sum(v*v for v in vector))
    if norm > 0:
        vector = [v/norm for v in vector]
    return vector
```

#### 演算法 B: Resonance Feedback（共振回饋）— 核心版

```
每次 meta_allocate() 決策後：
  1. 如果 ASSIGN 成功（ctx.max_resonance >= 0.3）：
     - anchor_target = ctx.vector（目標軸的 anchor 應該靠近輸入向量）
     - target_anchor = EMA_update(target_anchor, anchor_target, lr=0.1)
  2. 如果 CREATE 新軸：
     - 新軸的 anchor = ctx.vector 的值
     - 新軸註冊到 ResonanceEngine
  3. 如果 DEFER（所有相似度都低）：
     - 記錄到 unclassified_vectors 池
     - 如果 unclassified 累積 > N 個：
       - 聚類分析 → 找出新的軸潛力點
       - 提示 θ 是否需要調整閾值或創建新軸
```

#### 演算法 C: Misallocation Correction（錯誤修正）— θ 驅動版

```
每次 θ 自糾檢測到 misallocation：
  1. 識別：輸入向量被分配到軸 A，但後來被 θ 懷疑
  2. 更正值：
     - 軸 A 的 anchor 輕微遠離該輸入向量
     - 可能更匹配的軸 B 的 anchor 靠近該輸入向量
     anchor_A = anchor_A - lr * (input_vector - anchor_A) * misallocation_confidence
     anchor_B = anchor_B + lr * (input_vector - anchor_B) * misallocation_confidence
  3. 記錄修正歷史，用於未來的 θ 學習
```

#### 演算法 D: Text-Context Expansion（文本擴展）

```
每次 text_to_vector(text) 被調用：
  1. 記錄 (text, result_vector)
  2. 如果該向量被成功分配到軸 X：
     - 將 text 中的關鍵詞添加到軸 X 的 anchor 描述
     - 下次用更豐富的描述重建 anchor
  3. 長期：建立「關鍵詞 → 軸」的權重矩陣
     keyword_axis_weights[word][axis] += count
     → 最終：每個軸有一個 keyword profile，可以直接用於文本分類
```

### 3.4 架構：AnchorLearningEngine

```python
class AnchorLearningEngine:
    """
    Semantic Anchor 學習引擎

    從軸狀態快照、分配決策歷史、θ 自糾結果中學習，
    逐步調整 semantic anchor 向量，使相似度評分有意義。
    """

    def __init__(self, resonance_engine: ResonanceEngine, temporal: TemporalState):
        self._resonance = resonance_engine
        self._temporal = temporal
        self._misallocation_log: List[Dict] = []
        self._allocation_history: List[AllocationRecord] = []
        self._unclassified: List[List[float]] = []
        self._keyword_axis_weights: Dict[str, Dict[str, float]] = {}  # word -> axis -> weight
        self._ema_alpha = 0.9  # EMA 平滑因子（anchor 調整速度）

    # === 觸發點 1: 軸狀態更新 → 更新錨點 ===
    def on_axis_update(self, axis_name: str, snapshot: Dict[str, float], is_stable: bool = False) -> None:
        """
        每次軸更新時調用（從 StateMatrixAdapter 觸發）
        """
        if not is_stable:
            return  # 只有穩定狀態才更新 anchor
        vec = self._snapshot_to_vector(snapshot)
        anchor = self._resonance._semantic_vectors.get(axis_name)
        if anchor:
            updated = self._ema_update(anchor, vec)
            self._resonance._semantic_vectors[axis_name] = updated

    # === 觸發點 2: 分配決策 → 反饋學習 ===
    def on_allocation_decision(
        self,
        vector: List[float],
        action: AllocationAction,
        target: Optional[str],
        confidence: float,
    ) -> None:
        """
        每次 meta_allocate() 決策後調用
        """
        record = AllocationRecord(vector, action, target, confidence)
        self._allocation_history.append(record)

        if action == AllocationAction.ASSIGN and target and confidence >= 0.3:
            self._push_toward(vector, target, lr=0.05)
        elif action == AllocationAction.DEFER:
            self._unclassified.append(vector)
            if len(self._unclassified) > 20:
                self._analyze_unclassified()

    # === 觸發點 3: θ 自糾 → 錯誤修正 ===
    def on_misallocation_detected(
        self,
        input_vector: List[float],
        wrong_axis: str,
        right_axis: Optional[str],
        confidence: float,
    ) -> None:
        """
        每次 θ 自糾檢測到 misallocation 時調用
        """
        self._misallocation_log.append({
            'vector': input_vector,
            'wrong_axis': wrong_axis,
            'right_axis': right_axis,
            'confidence': confidence,
        })
        # 修正 wrong_axis 的 anchor
        self._push_away(input_vector, wrong_axis, lr=0.05 * confidence)
        # 如果找到了 right_axis，同時修正
        if right_axis:
            self._push_toward(input_vector, right_axis, lr=0.05 * confidence)

    # === 觸發點 4: 文本向量化 → 關鍵詞學習 ===
    def on_text_vectorized(self, text: str, vector: List[float], assigned_axis: Optional[str]) -> None:
        """
        每次 text_to_vector 被調用並成功分配時
        """
        if not assigned_axis:
            return
        words = text.lower().split()
        for word in words:
            if word not in self._keyword_axis_weights:
                self._keyword_axis_weights[word] = {a: 0.0 for a in self._resonance._axes}
            self._keyword_axis_weights[word][assigned_axis] += 1.0

    # === 向量更新 ===
    def _ema_update(self, anchor: List[float], target: List[float], lr: float = 0.1) -> List[float]:
        """EMA 更新錨點"""
        updated = []
        for a, t in zip(anchor, target):
            new_val = self._ema_alpha * a + (1 - self._ema_alpha) * t
            updated.append(new_val)
        norm = math.sqrt(sum(v * v for v in updated))
        if norm > 0:
            updated = [v / norm for v in updated]
        return updated

    def _push_toward(self, vector: List[float], axis_name: str, lr: float) -> None:
        """將錨點推向向量"""
        anchor = self._resonance._semantic_vectors.get(axis_name)
        if anchor:
            new_anchor = self._ema_update(anchor, vector, lr=lr)
            self._resonance._semantic_vectors[axis_name] = new_anchor

    def _push_away(self, vector: List[float], axis_name: str, lr: float) -> None:
        """將錨點遠離向量"""
        anchor = self._resonance._semantic_vectors.get(axis_name)
        if anchor:
            opposite = [-v for v in vector]
            new_anchor = self._ema_update(anchor, opposite, lr=lr)
            self._resonance._semantic_vectors[axis_name] = new_anchor

    def _snapshot_to_vector(self, snapshot: Dict[str, float], size: int = 32) -> List[float]:
        """將快照轉換為 32-dim 向量"""
        vector = [0.0] * size
        for field_name, value in snapshot.items():
            pos = hash(field_name) % size
            vector[pos] += value
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector

    def _analyze_unclassified(self) -> Dict[str, Any]:
        """分析未分類向量，尋找新軸潛力"""
        if len(self._unclassified) < 10:
            return {}
        # K-means 或簡單聚類
        vectors = self._unclassified[-20:]
        # 簡單：找與現有錨點最遠的點集群
        # 詳細實現略
        return {}

    def get_learning_report(self) -> Dict[str, Any]:
        """獲取學習狀態報告"""
        return {
            'allocation_history_size': len(self._allocation_history),
            'misallocation_count': len(self._misallocation_log),
            'unclassified_count': len(self._unclassified),
            'keyword_vocabulary_size': len(self._keyword_axis_weights),
            'anchor_stats': {
                ax: {
                    'nonzero_dims': sum(1 for v in vec if abs(v) > 1e-6),
                    'magnitude': math.sqrt(sum(v*v for v in vec)),
                }
                for ax, vec in self._resonance._semantic_vectors.items()
            },
        }


@dataclass
class AllocationRecord:
    vector: List[float]
    action: AllocationAction
    target: Optional[str]
    confidence: float
    timestamp: float = field(default_factory=time.time)
```

---

## 4. 實現順序

### Phase 1: AnchorLearningEngine 基礎（最高優先級）
- [ ] 實現 `AnchorLearningEngine` 類
- [ ] 整合進 `StateMatrixAdapter`
- [ ] 實現 `_ema_update`、`_push_toward`、`_push_away`
- [ ] 實現 `_snapshot_to_vector`
- [ ] 單元測試

### Phase 2: 觸發點整合
- [ ] 在 `StateMatrixAdapter.update_*()` 後觸發 `on_axis_update()`（每 N 次觸發一次，避免過度更新）
- [ ] 在 `allocation_decide()` 後觸發 `on_allocation_decision()`
- [ ] 在 `NegativityDetector` 檢測到 misallocation 後觸發 `on_misallocation_detected()`
- [ ] 在 `ResonanceEngine.compute_resonance()` 後觸發 `on_text_vectorized()`

### Phase 3: 動態閾值
- [ ] `AllocationPolicy` 的 ASSIGN 閾值從固定 0.7 改為動態
- [ ] 閾值根據當前最高相似度自動調整
- [ ] 如果 max_resonance 普遍偏低，自動降低閾值；如果普遍偏高，提高閾值

### Phase 4: 關鍵詞學習 + Anchor Expansion
- [ ] 實現 `_keyword_axis_weights` 矩陣構建
- [ ] 實現文本到軸的直接映射（不經過 text_to_vector）
- [ ] 用 keyword profile 重構 anchor 的 `keywords` 列表

### Phase 5: Misallocation 深度學習
- [ ] 分析 `_misallocation_log`，找出錯誤模式的規律
- [ ] 識別：「哪些類型的向量總是被錯誤分配」
- [ ] 實現「軸相似度衝突檢測」：如果兩個軸的 anchor 太近，標記為潛在衝突

---

## 5. 預期效果

| 指標 | 現在 | Phase 1 後 | Phase 3 後 |
|------|------|-----------|-----------|
| 最大相似度 | 0.0-0.276 | 0.3-0.5 | 0.5-0.8 |
| ASSIGN 觸發率 | 0% | 20% | 60% |
| Anchor 非零維度 | ~5 個 | ~10-15 個 | ~16-24 個 |
| 分配決策準確性 | 無法評估 | 逐步改善 | 顯著改善 |

---

## 6. 關鍵文件變更

| 檔案 | 變更 |
|------|------|
| `core/autonomous/anchor_learning.py` | **新增** — AnchorLearningEngine (~300行) |
| `core/autonomous/state_matrix_adapter.py` | 整合 AnchorLearningEngine；軸更新時觸發學習 |
| `core/allocation/resonance.py` | `_semantic_vectors` 改為可寫；添加 EMA 更新方法 |
| `core/allocation/policy.py` | ASSIGN 閾值動態化 |

---

## 7. 測試策略

### 單元測試
```
test_anchor_learning.py:
  - test_ema_update_densifies_anchor()       # 驗證 anchor 逐步變密
  - test_push_toward()                    # 驗證錨點朝向正確方向
  - test_push_away()                       # 驗證錨點遠離錯誤方向
  - test_snapshot_to_vector()              # 驗證快照轉換
  - test_on_allocation_assign_feedback()    # ASSIGN 後錨點更新
  - test_on_allocation_defer_accumulates()  # DEFER 後添加到未分類池
  - test_on_misallocation_correction()     # θ 自糾後錨點修正
  - test_text_keyword_tracking()           # 關鍵詞追蹤
```

### 整合測試
```
test_anchor_learning_integration.py:
  - 100 次軸更新後，anchor 從 ~5 非零維度增加到 ~12+
  - 50 次 ASSIGN 後，最大相似度從 0.2 提升到 0.5+
  - Misallocation 修正後，相似度評估準確性提升
  - Full pipeline：分配 → 學習 → 再分配，循環改善
```

---

## 8. 風險與緩解

| 風險 | 緩解 |
|------|------|
| 學習方向錯誤（anchor 越學越偏） | 使用 EMA（α=0.9）限制每次更新幅度；保留原始錨點作為 fallback |
| 過擬合到特定輸入模式 | 使用 unclassified 池分析，避免單一模式主導 |
| 性能下降（學習計算開銷） | 學習只在軸更新後每 N 次觸發一次，非每次 |
| θ 自糾結果不穩定（anchors 波動） | θ 的修正使用更低的 lr（0.05 vs 軸更新的 0.1） |

---

## 9. 版本規劃

| 版本 | 日期 | 狀態 |
|------|------|------|
| v0.1 | 2026-05-14 | 本設計文件 |
| v1.0 | TBD | AnchorLearningEngine Phase 1 完成 |
| v2.0 | TBD | Phase 2-3 完成，ASSIGN 閾值動態化 |
| v3.0 | TBD | 完整學習系統，包含關鍵詞學習 |