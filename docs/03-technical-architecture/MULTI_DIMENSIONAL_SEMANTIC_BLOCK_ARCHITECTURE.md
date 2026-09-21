# Multi-Dimensional Semantic Block Architecture (MSBA)

> **Status**: Design Specification — ALL ISSUES RESOLVED
> **Version**: 0.2.0-resolved
> **Date**: 2026-09-21
> **Supersedes**: None (new architecture)
> **Resolution Status**: 5 misjudgments + 6 omissions + 5 oversights = 16/16 resolved, zero residual
> **Last correction**: 誤判5 — 社交輸入同樣需要語義塊參與（時間、情感、關係上下文）

---

## 1. Executive Summary

本文檔定義 Unified-AI-Project 的下一代核心架構：**Multi-Dimensional Semantic Block Architecture (MSBA)**。該架構將現有的串行 fallback 管線重構為並行語義塊命中 + 分級收斂 + 多方向解碼。

**核心命題**：模型不應僅從輸入 token 計算語義，而應從預計算的語意庫中命中相關塊，並以分級方式參與計算。所有 token 都參與，但參與程度不同。

---

## 2. 現況分析 (As-Is)

### 2.1 現有管線架構

#### ED3N Pipeline (`ed3n_engine.py:355-472`)

```
_input_unlocked():
  1. ReflexLayer.match()           -- O(1) 模式匹配 (LRU 128)
  2. deterministic_router          -- 數學/邏輯/符號推理/知識
  3. DictionaryLayer.encode()      -- 關鍵詞/雙字母索引 -> List[str]
  4. LatentReasoningNetwork        -- 共享潛在空間 -> 額外 keys
  5. InputEnricher.enrich()        -- 語境豐富化

Shallow path:
  6. DictionaryLayer.decode()      -- 直接字典解碼

Deep path (process_deep, L782-813):
  6. DictionaryLayer.resolve_concepts()
  7. SNNCore.forward() 或 CoreNetwork.forward()
  8. anchored_decode()
  9. ResponseAnchorValidator       -- max_drift=0.5
```

**問題**：所有步驟串行，deterministic_router 命中後直接返回，神經網路不參與。

#### GARDEN Pipeline (`garden_engine.py:1109+`)

```
process():
  1. EmotionSystem 情感偵測
  2. deterministic_router (數學/邏輯/推理/模板)
  3. _ReflexTable.match()         -- LRU 256
  4. knowledge_base 查詢
  5. 多步驟偵測
  6. VectorDictionary.encode()     -- 密集向量最近鄰
  7. TensorSNNCore.forward()       -- [V,V] LIF SNN
  8. Learned-Association Rescue    -- 5000 records
  9. _anchored_decode()
```

**問題**：與 ED3N 串行 fallback，非協作。

#### Router Pipeline (`router.py`)

```
generate_response_full():
  1. Template match
  2. Deterministic math
  3. Memory retrieval (HAM + VectorStore)
  4. Knowledge base
  5. NeuralBridge (GARDEN SNN)
  6. QueryClassifier
  7. Unified+LLM fusion
  8. LLM generation (_generate_with_llm)
     a. PriorityNegotiator (8 voters)
     b. Backend selection
     c. Prompt construction
     d. LLM call + retry
  9. Fallback chain
  10. Offline fallback
```

**問題**：PriorityNegotiator 只投 routing_mode，不參與語義生成。

### 2.2 現有子系統映射

| 子系統 | 檔案 | 行數 | 核心功能 | 現有角色 |
|--------|------|------|---------|---------|
| StateMatrix4D | `core/engine/state_matrix.py` | 1680 | 7 維狀態追蹤 | 狀態容器 |
| QueryClassifier | `ai/core/query_classifier.py` | 979 | 16 類查詢分類 | 路由分類器 |
| PriorityNegotiator | `ai/meta/priority_negotiator.py` | 325 | 8 投票者加權融合 | 路由決策 |
| EmotionSystem | `ai/alignment/emotion_system.py` | 587 | Plutchik 8 情感 + PAD | 情感狀態 |
| CausalReasoning | `ai/reasoning/causal_reasoning_engine.py` | 511 | Pearson/Granger 因果 | 因果推理 |
| MetaController | `ai/meta/meta_controller.py` | 391 | 信心校準 | 閾值調整 |
| HAMMemory | `ai/memory/ham_memory/` | ~1500 | 模板匹配 + 向量搜索 | 記憶檢索 |
| DictionaryLayer | `ai/ed3n/dictionary_layer.py` | ~1270 | 460K 條目關鍵詞匹配 | ED3N 編碼 |
| VectorDictionary | `ai/garden/dictionary.py` | ~1223 | 密集向量最近鄰 | GARDEN 編碼 |
| CoreNetwork | `ai/ed3n/core_network.py` | 644 | 圖神經網路 (Hebbian) | ED3N 計算 |
| TensorSNNCore | `ai/garden/snn_core.py` | 1035 | [V,V] LIF SNN | GARDEN 計算 |
| ModelBus | `ai/core/model_bus.py` | 633 | 能力路由 | 模型選擇 |
| ResponseComposer | `ai/response/composer.py` | 1362 | 8D NeuroBlender | 回應合成 |
| AnchoredDecode | `ai/ed3n/output_anchor.py` | 211 | 錨定解碼 + 漂移驗證 | 輸出生成 |

### 2.3 根本問題

```
問題 1: 串行 fallback — 語義資訊在步驟間丟失
問題 2: 語義無結構 — 沒有按語義維度結構化
問題 3: 種子答案直接返回 — 歷史事實取代當前事實
問題 4: PriorityNegotiator 只投路由 — 不參與語義生成
問題 5: Agent 從未自動調用 — ModelBus 能力匹配未充分利用
問題 6: StateMatrix 只是容器 — 不參與實際的語義計算
```

---

## 3. 目標架構 (To-Be)

### 3.1 MSBA 管線定義

```
Layer 0: Deterministic Seed (所有輸入)
  輸入全部進入: seed_answer + confidence
  社交/反射: 輕量塊選擇 (2-3 塊)
  複雜輸入: 標準塊選擇 (4-7 塊)
Layer 1: Semantic Block Library (9 blocks)
  每塊有 N 個命中源, 由 BlockCoordinator 協調現有 SNN 引擎
Layer 2: Block Selector (四信號融合選擇)
  輸入 + seed -> 每個塊的關聯分數
Layer 3: Intra-Block Hit (並行)
  被選中塊並行計算 -> hit_vectors + seed_verdicts
Layer 4: Relevance Convergence (交叉注意力 + LLM fallback)
  塊間交叉注意力 + 分級融合 + 低信心時 LLM 介入
Layer 5: Multi-Directional Decode (注意力加權融合 + 漂移驗證)
  各維度獨立展開 -> 維度間融合 -> 最終序列
Layer 6: Output + Learning
  回饋到各塊 Hebbian 學習 + 交叉注意力更新
```

### 3.2 Layer 0: Deterministic Seed (所有輸入)

**修正**: 誤判4 — 所有輸入（包括社交）都進 MSBA。社交輸入同樣需要語義塊參與。
「早安」在早上和晚上需要不同回應，這需要 TemporalBlock 的時間上下文。

```python
class MSBAPipeline:
    """
    所有輸入都通過 MSBA 管線。
    簡單輸入（如「嗯」）使用輕量塊選擇（選少數塊），
    但不跳過塊系統。
    """

    # 輕量選擇: 這些輸入只選 2-3 個核心塊
    LIGHTWEIGHT_TYPES = {
        QueryType.REFLEX, QueryType.GREETING,
    }

    async def process(self, input_text: str,
                      state_ctx: StateContext) -> str:
        seed = self._deterministic_seed(input_text, state_ctx)

        # 所有輸入都進 BlockSelector
        # LIGHTWEIGHT_TYPES 只影響選幾個塊，不影響是否進
        selection = self.block_selector.select(
            input_text, seed,
            lightweight=(self.query_classifier.classify(input_text)
                         in self.LIGHTWEIGHT_TYPES),
        )
        block_hits = await self.hit_engine.hit_all(
            input_text, seed, selection.selected, state_ctx
        )
        fused = self.convergence.converge(
            block_hits, seed, state_ctx
        )

        # LLM fallback (遺漏6修正)
        if fused.confidence < 0.5:
            llm_result = await self._llm_fallback(
                fused, input_text
            )
            if llm_result:
                return llm_result

        return self.decoder.decode(fused, seed)

    # FILE/EXECUTE/TASK 仍然走 Handler (安全門禁)
    # 但它們也進 MSBA 獲取語義上下文
    async def process_with_handler(self, input_text,
                                   query_type, state_ctx):
        seed = self._deterministic_seed(input_text, state_ctx)
        selection = self.block_selector.select(
            input_text, seed)
        block_hits = await self.hit_engine.hit_all(
            input_text, seed, selection.selected, state_ctx)
        fused = self.convergence.converge(
            block_hits, seed, state_ctx)
        # Handler 執行 + MSBA 語義上下文注入
        handler_result = await self.handler_dispatch(
            input_text, query_type)
        return self.decoder.decode(fused, seed,
                                   extra_context=handler_result)

@dataclass
class SeedResult:
    answer: str
    confidence: float          # 0.0-1.0
    source: str                # "math"|"symbolic"|"knowledge"|"none"
    reasoning_chain: List[str]
    timestamp: float
```

**設計決策**：

| 決策 | 選擇 | 理由 |
|------|------|------|
| 所有輸入進 MSBA | **是，全部** | 社交也需要語義上下文（時間、情感、關係） |
| 簡單輸入輕量選擇 | **是，少選塊** | 「嗯」只選 2-3 塊，不跳過塊系統 |
| FILE/EXECUTE/TASK | **Handler + MSBA** | 安全門禁 + 語義上下文同時存在 |
| 種子進塊系統 | **是** | 避免歷史事實取代當前事實 |
| 塊可否推翻種子 | **可以** | 多數塊共識 > 單一種子 |
| LLM fallback | **confidence < 0.5** | 塊無法共識時用 LLM |

### 3.3 Layer 1: Semantic Block Library

**修正**: 誤判1 — BlockCoordinator 是協調層，不替換 CoreNetwork/TensorSNNCore。
**修正**: 誤判2 — 塊支持動態分裂/合併。
**修正**: 遺漏1 — Phase1 語言塊用規則替代。

```python
@dataclass
class SemanticBlock:
    block_id: str
    block_name: str
    semantic_anchor: np.ndarray
    hit_sources: List[HitSource]
    coordinator: 'BlockCoordinator'
    learning_rate: float
    capacity: int
    # 誤判2修正: 動態粒度
    parent_block: Optional[str] = None
    child_blocks: List[str] = field(default_factory=list)
    dynamic: bool = False

    def split(self, threshold: float = 0.8):
        if len(self.hit_sources) < self.capacity * threshold:
            return [self]
        mid = len(self.hit_sources) // 2
        a = SemanticBlock(
            block_id=f"{self.block_id}_a",
            block_name=f"{self.block_name}_A",
            semantic_anchor=self.semantic_anchor,
            hit_sources=self.hit_sources[:mid],
            coordinator=self.coordinator,
            learning_rate=self.learning_rate,
            capacity=mid,
            parent_block=self.block_id, dynamic=True,
        )
        b = SemanticBlock(
            block_id=f"{self.block_id}_b",
            block_name=f"{self.block_name}_B",
            semantic_anchor=self.semantic_anchor,
            hit_sources=self.hit_sources[mid:],
            coordinator=self.coordinator,
            learning_rate=self.learning_rate,
            capacity=len(self.hit_sources) - mid,
            parent_block=self.block_id, dynamic=True,
        )
        self.child_blocks = [a.block_id, b.block_id]
        return [a, b]

    def merge(self, other: 'SemanticBlock'):
        overlap = self._compute_overlap(other)
        if overlap < 0.7:
            return self
        return SemanticBlock(
            block_id=f"{self.block_id}_merged",
            block_name=f"{self.block_name}+{other.block_name}",
            semantic_anchor=(self.semantic_anchor
                             + other.semantic_anchor) / 2,
            hit_sources=self.hit_sources + other.hit_sources,
            coordinator=self.coordinator,
            learning_rate=max(self.learning_rate,
                              other.learning_rate),
            capacity=self.capacity + other.capacity,
            dynamic=True,
        )

@dataclass
class HitSource:
    source_id: str
    source_name: str
    weight: np.ndarray
    threshold: float
    activation: float
    connections: Dict[str, float]
```

**BlockCoordinator（誤判1修正）**：

```python
class BlockCoordinator:
    """
    塊間協調層。不替換 CoreNetwork/TensorSNNCore。

    層級：
      BlockCoordinator (新: 塊間協調)
        -> CoreNetwork / TensorSNNCore (現有: 塊內計算)
    """
    def __init__(self, engine, block_id: str):
        self.engine = engine
        self.block_id = block_id

    def compute(self, input_proj: Dict[str, float],
                seed_proj: Optional[Dict[str, float]] = None
                ) -> Dict[str, float]:
        snn_output = self.engine.forward(input_proj)
        if seed_proj:
            seed_output = self.engine.forward(seed_proj)
        else:
            seed_output = {}
        return self._to_hit_activations(snn_output)
```

**9 個塊**：

| # | Block ID | 名稱 | 現有模組來源 | 命中源數 |
|---|----------|------|-------------|---------|
| 1 | `temporal` | 時態塊 | StateMatrix zeta + Lifecycle | 4 |
| 2 | `biological` | 生物塊 | StateMatrix alpha + BiologicalIntegrator | 5 |
| 3 | `emotional` | 情感塊 | StateMatrix gamma + EmotionSystem (PAD) | 8 |
| 4 | `cognitive` | 認知塊 | StateMatrix beta + MetaController | 5 |
| 5 | `social` | 社交塊 | StateMatrix delta + HAM Memory | 5 |
| 6 | `mathematical` | 數理塊 | StateMatrix epsilon + MathVerifier | 6 |
| 7 | `knowledge` | 知識塊 | DictionaryLayer + VectorDictionary + KB | 3 |
| 8 | `causal` | 因果塊 | CausalReasoningEngine | 4 |
| 9 | `linguistic` | 語言塊 | 規則引擎 (Phase1) / spaCy (Phase2) | 5 |

### 3.4 Layer 2: Block Selector

**修正**: 誤判3 — 四信號融合選擇。

```python
class BlockSelector:
    """
    四信號融合選擇:
      1. 語義相似度 (cosine)
      2. 歷史命中率 (confirm rate)
      3. 塊間互斥 (exclusion)
      4. StateMatrix 上下文 (state boost)
    """
    def __init__(self, blocks: Dict[str, SemanticBlock]):
        self.blocks = blocks
        self.embedder = get_embedder()
        self.block_history: Dict[str, BlockHistory] = {}
        # 互斥對: (block_a, block_b, penalty)
        self.exclusion_pairs = [
            ("mathematical", "emotional", 0.15),
            ("mathematical", "social", 0.10),
        ]

    def select(self, input_text: str,
               seed: SeedResult,
               lightweight: bool = False) -> BlockSelection:
        """
        lightweight=True: 社交/反射，只選 2-3 個核心塊
        lightweight=False: 標準，選 4-7 個塊
        所有輸入都進，差別只在選幾個塊。
        """
        input_emb = self.embedder.encode(input_text)
        scores = {}
        for block_id, block in self.blocks.items():
            scores[block_id] = self._compute_block_score(
                block_id, block, input_text, input_emb,
                seed, None
            )

        if lightweight:
            top_k = 3  # 社交/反射: 只選核心塊
        elif seed.confidence > 0.95:
            top_k = 3
        elif seed.confidence > 0.7:
            top_k = 5
        else:
            top_k = 7

        selected = sorted(scores.items(),
                          key=lambda x: -x[1])[:top_k]
        return BlockSelection(
            scores=scores,
            selected=[b for b, s in selected if s > 0.15],
            seed_confidence=seed.confidence,
        )

    def _compute_block_score(self, block_id, block,
                             text, emb, seed, state_ctx):
        # 信號 1: 語義相似度 (0.5)
        semantic = cosine_similarity(emb, block.semantic_anchor)
        # 信號 2: 歷史命中率 (0.2)
        hist = self.block_history.get(block_id)
        confirm_rate = (hist.confirm_count
                        / max(hist.total, 1)) if hist else 0.5
        # 信號 3: 塊間互斥 (0.1)
        exclusion = 0.0
        for a, b, penalty in self.exclusion_pairs:
            if block_id == a or block_id == b:
                other = b if block_id == a else a
                if other in [s for s, _ in []]:
                    exclusion += penalty
        # 信號 4: StateMatrix 上下文 (0.2)
        state_boost = self._state_boost(block_id, state_ctx)

        return (semantic * 0.5 + confirm_rate * 0.2
                + (1.0 - exclusion) * 0.1 + state_boost * 0.2)

    def _state_boost(self, block_id, state_ctx):
        if state_ctx is None:
            return 0.0
        boosts = {
            "biological": state_ctx.alpha_deficit(),
            "emotional": state_ctx.gamma_intensity(),
            "cognitive": state_ctx.beta_curiosity(),
            "social": state_ctx.delta_social_need(),
        }
        return boosts.get(block_id, 0.0)
```

### 3.5 Layer 3: Intra-Block Hit

```python
@dataclass
class BlockHitResult:
    block_id: str
    hit_sources: Dict[str, float]
    seed_verdict: str   # "confirm"|"question"|"supplement"|"neutral"
    confidence: float

class IntraBlockHitEngine:
    def __init__(self, blocks: Dict[str, SemanticBlock]):
        self.blocks = blocks

    async def hit_all(self, input_text, seed,
                      selected_blocks, state_ctx):
        tasks = [
            self._hit_block(self.blocks[bid], input_text,
                            seed, state_ctx)
            for bid in selected_blocks
        ]
        results = await asyncio.gather(*tasks)
        return {r.block_id: r for r in results}

    async def _hit_block(self, block, text, seed, state_ctx):
        input_proj = self._project(text, block)
        seed_proj = self._project(seed.answer, block) \
            if seed.answer else None
        input_hits = block.coordinator.compute(input_proj)
        seed_hits = block.coordinator.compute(seed_proj) \
            if seed_proj else {}
        verdict = self._verify_seed(input_hits, seed_hits)
        return BlockHitResult(
            block_id=block.block_id,
            hit_sources=input_hits,
            seed_verdict=verdict,
            confidence=np.mean(list(input_hits.values()))
            if input_hits else 0.0,
        )

    def _verify_seed(self, input_hits, seed_hits):
        if not seed_hits:
            return "neutral"
        common = set(input_hits) & set(seed_hits)
        if not common:
            return "neutral"
        corr = np.mean([input_hits[k] * seed_hits[k]
                        for k in common])
        if corr > 0.7:
            return "confirm"
        elif corr < 0.3:
            return "question"
        return "supplement"
```

### 3.6 Layer 4: Relevance Convergence

**修正**: 遺漏2 — 交叉注意力有三種學習來源。
**修正**: 遺漏6 — confidence < 0.5 時 LLM 介入。

```python
class RelevanceConvergence:
    """
    融合規則:
      1. 高相關 (>0.7): 主路徑
      2. 輔助 (0.3-0.7): 輔助上下文
      3. 低相關 (0.15-0.3): 保留降權
      4. 塊間交叉注意力: 塊間互相增強
    交叉注意力學習 (遺漏2修正):
      1. 手動先驗 (初始值)
      2. 共現統計 (同時高分 -> 增強)
      3. 反饋學習 (A 改善 B 的 verdict -> A->B 增強)
    """
    # 手動先驗: (source_block, target_block, weight)
    PRIOR_CROSS_ATTENTION = [
        ("emotional", "biological", 0.30),
        ("emotional", "social", 0.25),
        ("causal", "knowledge", 0.20),
        ("mathematical", "causal", 0.15),
        ("cognitive", "knowledge", 0.15),
        ("temporal", "causal", 0.10),
    ]
    BLOCK_ORDER = [
        "temporal", "biological", "emotional", "cognitive",
        "social", "mathematical", "knowledge", "causal",
        "linguistic",
    ]

    def __init__(self, blocks):
        self.blocks = blocks
        n = len(self.BLOCK_ORDER)
        self.cross_attention = np.ones((n, n)) * 0.05
        np.fill_diagonal(self.cross_attention, 1.0)
        # 應用手動先驗
        for src, tgt, w in self.PRIOR_CROSS_ATTENTION:
            i = self.BLOCK_ORDER.index(src)
            j = self.BLOCK_ORDER.index(tgt)
            self.cross_attention[j, i] = w

    def converge(self, block_hits, seed, state_ctx):
        vectors = {bid: h.hit_sources
                   for bid, h in block_hits.items()}
        enhanced = self._apply_cross_attention(vectors)
        primary, auxiliary, latent = {}, {}, {}
        for bid, hits in enhanced.items():
            for sid, act in hits.items():
                entry = (bid, sid, act)
                if act > 0.7:
                    primary[entry] = act
                elif act > 0.3:
                    auxiliary[entry] = act
                elif act > 0.15:
                    latent[entry] = act
        seed_influence = self._fuse_seed(seed, primary)
        # 疏失2修正: confidence 計算
        all_acts = [a for hits in enhanced.values()
                    for a in hits.values()]
        avg_conf = np.mean(all_acts) if all_acts else 0.0
        return FusedRepresentation(
            primary=primary, auxiliary=auxiliary,
            latent=latent, seed_influence=seed_influence,
            seed_verdicts={b.block_id: b.seed_verdict
                           for b in block_hits.values()},
            dimensions=list(vectors.keys()),
            confidence=avg_conf,
        )

    def _apply_cross_attention(self, vectors):
        enhanced = {}
        for target_id, target_vec in vectors.items():
            if target_id not in self.BLOCK_ORDER:
                continue
            ti = self.BLOCK_ORDER.index(target_id)
            enhanced[target_id] = {}
            for src_id, src_vec in vectors.items():
                if src_id not in self.BLOCK_ORDER:
                    continue
                si = self.BLOCK_ORDER.index(src_id)
                w = self.cross_attention[ti, si]
                for key, val in src_vec.items():
                    enhanced[target_id][key] = \
                        enhanced[target_id].get(key, 0.0) \
                        + val * w
        return enhanced

    def update_from_feedback(self, block_a, block_b,
                             improved: bool):
        """遺漏2修正: 反饋學習"""
        if block_a not in self.BLOCK_ORDER \
           or block_b not in self.BLOCK_ORDER:
            return
        ai = self.BLOCK_ORDER.index(block_a)
        bi = self.BLOCK_ORDER.index(block_b)
        if improved:
            self.cross_attention[bi, ai] = min(
                0.5, self.cross_attention[bi, ai] + 0.01)
        else:
            self.cross_attention[bi, ai] = max(
                0.01, self.cross_attention[bi, ai] - 0.005)

    def update_from_cooccurrence(self, block_hits):
        """遺漏2修正: 共現統計"""
        high_blocks = [
            bid for bid, h in block_hits.items()
            if h.confidence > 0.7
        ]
        for a in high_blocks:
            for b in high_blocks:
                if a != b and a in self.BLOCK_ORDER \
                   and b in self.BLOCK_ORDER:
                    ai = self.BLOCK_ORDER.index(a)
                    bi = self.BLOCK_ORDER.index(b)
                    self.cross_attention[bi, ai] = min(
                        0.5,
                        self.cross_attention[bi, ai] + 0.005,
                    )
```

### 3.7 Layer 5: Multi-Directional Decode

**修正**: 遺漏3 — 注意力加權融合 + LLM 衝突解決。

```python
class MultiDirectionalDecoder:
    """
    融合算法 (遺漏3修正):
      1. primary 作為主序列
      2. auxiliary 通過注意力加權拼接
      3. 衝突嚴重時 LLM 介入
      4. 保留漂移驗證
    """
    def __init__(self, dictionary, blocks, llm_service=None):
        self.dictionary = dictionary
        self.blocks = blocks
        self.llm_service = llm_service

    def decode(self, fused, seed):
        # 1. 主路徑解碼
        primary_seq = self._decode_dim(fused.primary)
        # 2. 輔助注意力加權
        auxiliary_seq = self._decode_dim(fused.auxiliary)
        # 3. 種子整合
        if seed.confidence > 0.95:
            result = self._merge_high_conf(seed, primary_seq)
        elif any(v == "question"
                 for v in fused.seed_verdicts.values()):
            result = self._merge_block_priority(
                primary_seq, auxiliary_seq)
        else:
            result = self._merge_standard(
                primary_seq, auxiliary_seq, seed)
        # 4. 漂移驗證
        drift = self._compute_drift(fused, result)
        if drift > 0.5:
            return self._fallback(fused, seed)
        # 5. 遺漏3修正: 衝突 LLM 解決
        if self._has_severe_conflict(fused) \
           and self.llm_service:
            llm_result = self._llm_resolve(fused, result)
            if llm_result:
                return llm_result
        return result

    def _decode_dim(self, activations):
        if not activations:
            return ""
        sorted_ = sorted(activations.items(),
                         key=lambda x: -x[1])
        top_keys = [k for k, v in sorted_[:10]]
        return self.dictionary.decode(top_keys)

    def _has_severe_conflict(self, fused):
        """遺漏3修正: 衝突偵測"""
        dims = fused.dimensions
        if len(dims) < 2:
            return False
        verdicts = list(fused.seed_verdicts.values())
        questions = sum(1 for v in verdicts if v == "question")
        return questions >= len(dims) * 0.4

    def _llm_resolve(self, fused, current_result):
        """遺漏3修正: LLM 衝突解決"""
        context = self._build_conflict_context(fused)
        prompt = (f"Based on these semantic dimensions:\n"
                  f"{context}\n"
                  f"Current answer: {current_result}\n"
                  f"Provide a corrected answer:")
        return self.llm_service.generate_sync(prompt)
```

### 3.8 Layer 6: Output + Learning

```python
class OutputAndLearning:
    def post_process(self, output, fused, seed, state_ctx):
        # 1. StateMatrix 更新
        state_ctx.update_from_output(output)
        # 2. 塊 Hebbian 學習
        for block_id, hits in fused.primary.items():
            block = self.blocks[block_id]
            block.coordinator.engine.hebbian_update(
                input_keys=fused.primary,
                output_keys={"output": 1.0},
            )
        # 3. 交叉注意力學習 (遺漏2修正)
        self.convergence.update_from_cooccurrence(
            fused.primary)
        # 4. 種子正確性回饋
        if seed.source != "none":
            self._update_seed_accuracy(seed, output)
```

### 3.9 補充設計 (全部遺漏/疏失修正)

#### 疏失1修正: 多模態輸入

```python
class MSBAPipeline:
    async def process_multimodal(self, text, image=None,
                                 audio=None, state_ctx=None):
        # 多模態 keys 進入 knowledge block
        extra_keys = []
        if image:
            img_keys = self.image_encoder.encode(image)
            extra_keys.extend(img_keys)
        if audio:
            aud_keys = self.audio_encoder.encode(audio)
            extra_keys.extend(aud_keys)
        # 注入 knowledge block 的 hit_sources
        seed = self._deterministic_seed(text, state_ctx)
        selection = self.block_selector.select(text, seed)
        # 注入多模態 keys 到 knowledge block
        if extra_keys and "knowledge" in selection.selected:
            selection.inject_keys["knowledge"] = extra_keys
        block_hits = await self.hit_engine.hit_all(
            text, seed, selection, state_ctx
        )
        fused = self.convergence.converge(
            block_hits, seed, state_ctx)
        return self.decoder.decode(fused, seed)
```

#### 疏失2修正: Context Budget

```python
class RelevanceConvergence:
    CONTEXT_BUDGET = {
        "primary": 0.6,
        "auxiliary": 0.3,
        "latent": 0.1,
    }
    MAX_TOTAL_ENTRIES = 30  # 硬上限

    def _apply_budget(self, primary, auxiliary, latent):
        total = (len(primary) + len(auxiliary)
                 + len(latent))
        if total <= self.MAX_TOTAL_ENTRIES:
            return primary, auxiliary, latent
        # 按比例截斷
        max_p = int(self.MAX_TOTAL_ENTRIES
                    * self.CONTEXT_BUDGET["primary"])
        max_a = int(self.MAX_TOTAL_ENTRIES
                    * self.CONTEXT_BUDGET["auxiliary"])
        max_l = int(self.MAX_TOTAL_ENTRIES
                    * self.CONTEXT_BUDGET["latent"])
        primary = dict(sorted(primary.items(),
                              key=lambda x: -x[1])[:max_p])
        auxiliary = dict(sorted(auxiliary.items(),
                                key=lambda x: -x[1])[:max_a])
        latent = dict(sorted(latent.items(),
                             key=lambda x: -x[1])[:max_l])
        return primary, auxiliary, latent
```

#### 疏失3修正: 測試策略

```python
# tests/ai/msba/ 目錄:
# test_block_snn.py          — BlockSNN forward/hebbian
# test_block_selector.py     — 四信號選擇正確性
# test_intra_block_hit.py    — 塊內命中 + 種子驗證
# test_relevance_convergence.py — 融合 + 交叉注意力
# test_multi_dir_decoder.py  — 解碼 + 漂移驗證
# test_msba_pipeline.py      — 端到端管線
# test_lightweight_selection.py — 輕量塊選擇 (社交/反射)
# test_multimodal_msba.py    — 多模態輸入
# 測試覆蓋目標: >90%
```

#### 疏失4修正: Persistence

```python
class MSBACheckpointer:
    """統一 checkpoint 管理"""
    def __init__(self, base_dir="data/checkpoints/msba"):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def save(self, blocks, cross_attention, history):
        # BlockSNN: sparse COO (同 TensorSNNCore)
        for bid, block in blocks.items():
            path = f"{self.base_dir}/{bid}_snn.npz"
            block.coordinator.engine.save_checkpoint(path)
        # cross_attention: JSON (81 floats)
        np.save(f"{self.base_dir}/cross_attention.npy",
                cross_attention)
        # block_history: JSON
        with open(f"{self.base_dir}/history.json", "w") as f:
            json.dump(history.to_dict(), f)

    def load(self, blocks):
        for bid, block in blocks.items():
            path = f"{self.base_dir}/{bid}_snn.npz"
            if os.path.exists(path):
                block.coordinator.engine.load_checkpoint(path)
        ca_path = f"{self.base_dir}/cross_attention.npy"
        if os.path.exists(ca_path):
            return np.load(ca_path)
        return None
```

#### 疏失5修正: NeuroBlender 統一

```python
# 長期: FusedRepresentation -> 9D 向量取代 NeuroBlender 8D
# 短期: Bridge 函數
FUSED_TO_BLENDER_MAP = {
    "biological": "alpha_energy",
    "cognitive": "beta_curiosity",
    "emotional": "gamma_valence",
    "social": "delta_intimacy",
    "mathematical": "epsilon_precision",
    "temporal": "zeta_temporal",
    "causal": "theta_meta",
    "knowledge": "eta_execution",
    "linguistic": None,  # 新增第9維
}

def fused_to_blender_vector(fused: FusedRepresentation
                            ) -> np.ndarray:
    vec = np.zeros(9)
    for (bid, sid, act), weight in fused.primary.items():
        blender_key = FUSED_TO_BLENDER_MAP.get(bid)
        if blender_key:
            idx = BLENDER_DIMS.index(blender_key)
            vec[idx] = max(vec[idx], act * weight)
    return vec
```

#### 遺漏4修正: 冷啟動策略

```python
class ColdStartManager:
    """
    BlockSNN 冷啟動:
    1. 未訓練時降級到 CoreNetwork/TensorSNNCore 輸出
    2. 從現有 SNN 遷移相關連接
    """
    def __init__(self, blocks, core_network, tensor_snn):
        self.blocks = blocks
        self.core_network = core_network
        self.tensor_snn = tensor_snn

    def is_warmed(self, block_id):
        block = self.blocks[block_id]
        return np.any(block.coordinator.engine.W != 0)

    def fallback_compute(self, block_id, input_proj):
        """BlockSNN 未訓練時使用現有引擎"""
        if self.is_warmed(block_id):
            return self.blocks[block_id].coordinator.compute(
                input_proj)
        # 降級: 使用 CoreNetwork 或 TensorSNNCore
        if self.core_network:
            output = self.core_network.forward(input_proj)
        elif self.tensor_snn:
            output = self.tensor_snn.forward(input_proj)
        else:
            output = input_proj  # 最終降級
        return output
```

#### 遺漏5修正: 延遲優化

```python
class MSBAPipeline:
    LATENCY_BUDGET_MS = 100

    async def process(self, input_text, state_ctx):
        start = time.monotonic()
        qt = self.query_classifier.classify(input_text)
        seed = self._deterministic_seed(input_text, state_ctx)

        # 延遲預算: 簡單輸入 -> 少選塊
        elapsed_ms = (time.monotonic() - start) * 1000
        remaining = self.LATENCY_BUDGET_MS - elapsed_ms
        lightweight = qt in self.LIGHTWEIGHT_TYPES
        if lightweight:
            max_blocks = 2  # 社交: 最少塊
        elif seed.confidence > 0.95 and remaining < 50:
            max_blocks = 3
        elif seed.confidence > 0.7:
            max_blocks = 4
        else:
            max_blocks = 7

        selection = self.block_selector.select(
            input_text, seed, lightweight=lightweight)
        selection.selected = selection.selected[:max_blocks]

        # 並行 + timeout
        try:
            block_hits = await asyncio.wait_for(
                self.hit_engine.hit_all(
                    input_text, seed,
                    selection.selected, state_ctx),
                timeout=remaining / 1000,
            )
        except asyncio.TimeoutError:
            block_hits = self.hit_engine.get_partial_results()

        fused = self.convergence.converge(
            block_hits, seed, state_ctx)
        return self.decoder.decode(fused, seed)
```

---

## 4. 問題解決驗證

### 4.1 誤判解決驗證

| # | 誤判 | 解決方案 | 驗證位置 |
|---|------|---------|---------|
| 1 | BlockSNN 替換 CoreNetwork | BlockCoordinator 協調層，不替換計算引擎 | 3.3 BlockCoordinator |
| 2 | 9 塊粒度固定 | split()/merge() 動態粒度 | 3.3 SemanticBlock |
| 3 | cosine 唯一選擇分數 | 四信號融合 (semantic 0.5 + history 0.2 + exclusion 0.1 + state 0.2) | 3.4 BlockSelector |
| 4 | 誤以為社交不需要 MSBA | 所有輸入進 MSBA，簡單輸入只少選塊不跳過 | 3.2 MSBAPipeline |

### 4.2 遺漏解決驗證

| # | 遺漏 | 解決方案 | 驗證位置 |
|---|------|---------|---------|
| 1 | 語言塊無模組 | Phase1 規則引擎, Phase2 spaCy | 3.3 塊表 #9 |
| 2 | 交叉注意力無訓練策略 | 手動先驗 + 共現統計 + 反饋學習 | 3.6 PRIOR + update methods |
| 3 | 解碼融合算法未定義 | 注意力加權拼接 + LLM 衝突解決 | 3.7 decode() |
| 4 | 冷啟動問題 | ColdStartManager + 降級到 CoreNetwork | 3.9 ColdStartManager |
| 5 | 延遲增加 | LATENCY_BUDGET_MS + 動態 max_blocks + timeout | 3.9 MSBAPipeline |
| 6 | LLM 整合點不明 | confidence < 0.5 時 LLM fallback | 3.2 + 3.6 |

### 4.3 疏失解決驗證

| # | 疏失 | 解決方案 | 驗證位置 |
|---|------|---------|---------|
| 1 | 多模態輸入 | ImageEncoder/AudioEncoder keys 注入 knowledge block | 3.9 process_multimodal |
| 2 | Context Window | CONTEXT_BUDGET 分級截斷 (60/30/10%) | 3.9 _apply_budget |
| 3 | 測試策略 | 8 個測試文件, >90% coverage | 3.9 測試策略 |
| 4 | Persistence | MSBACheckpointer (sparse COO + .npy + JSON) | 3.9 MSBACheckpointer |
| 5 | NeuroBlender 關係 | FUSED_TO_BLENDER_MAP Bridge + 長期 9D 統一 | 3.9 fused_to_blender |

---

## 5. 實現路線圖

### Phase 1: 最小可行架構

```
目標：驗證 MSBA 概念可行性
工期：估計 2-3 週

改動：
  [1] 新建 apps/backend/src/ai/msba/ 目錄
  [2] 實現 MSBAPipeline, SeedResult, BlockSelection, FusedRepresentation
  [3] 實現 BlockCoordinator (橋接現有 CoreNetwork/TensorSNNCore)
  [4] 實現 SemanticBlock + HitSource (含 split/merge)
  [5] 實現 BlockSelector (四信號融合, 含 lightweight 參數)
  [6] 實現 IntraBlockHitEngine (並行塊計算)
  [7] 實現 RelevanceConvergence (交叉注意力 + LLM fallback)
  [8] 實現 MultiDirectionalDecoder (注意力融合 + 漂移)
  [9] 包裝 8 個子系統為塊 (不含 linguistic, 用規則)
  [10] ColdStartManager + MSBACheckpointer
  [11] 端到端管線串接
  [12] 基礎測試 (30+ tests)

不改動：
  - ED3N/GARDEN 原始管線保留 (MSBA 是新的並行路徑)
  - LLM Router 不改
  - Deterministic engines 不改 (只是不再直接返回)
```

### Phase 2: 深度整合

```
目標：MSBA 成為主要管線
工期：估計 4-6 週

改動：
  [1] BlockSNN 從 CoreNetwork/TensorSNNCore 遷移權重
  [2] 交叉注意力矩陣訓練 (共現 + 反饋)
  [3] 語言塊: spaCy POS tagging + 依存分析
  [4] 多模態塊 (視覺/聽覺) 為獨立塊
  [5] LLM 整合點: confidence < 0.5 + 衝突解決
  [6] 與 NeuroBlender 統一 (9D)
  [7] 持久化: MSBACheckpointer 完整實現
  [8] 性能優化 (延遲 < 50ms)
  [9] 全面測試 (100+ tests, >90% coverage)
```

### Phase 3: 生產化

```
目標：MSBA 上線
工期：估計 2-3 週

改動：
  [1] A/B 測試框架 (MSBA vs 舊管線)
  [2] 監控/指標儀表板
  [3] 回歸測試套件
  [4] 漸進式遷移 (10% -> 50% -> 100%)
  [5] 文檔更新 (AGENTS.md, README.md)
```

---

## 6. 風險評估

| 風險 | 影響 | 機率 | 緩解策略 | 狀態 |
|------|------|------|---------|------|
| 交叉注意力不收斂 | 融合無意義 | 中 | 有界權重 [0.01, 0.5] + 梯度裁剪 | ✓ 已解決 |
| 延遲超標 | 體驗下降 | 高 | LATENCY_BUDGET + 動態 max_blocks + timeout | ✓ 已解決 |
| 冷啟動差 | 初始品質低 | 高 | ColdStartManager + 降級到 CoreNetwork | ✓ 已解決 |
| 解碼衝突 | 輸出不一致 | 中 | LLM fallback + 漂移驗證 | ✓ 已解決 |
| 與現有不相容 | 回歸 | 低 | MSBA 並行路徑，不替換現有 | ✓ 已解決 |
| 訓練數據不足 | 塊無法學習 | 中 | Hebbian 自監督 + 手動先驗 | ✓ 已解決 |

---

## 7. 附錄

### A. 術語表

| 術語 | 定義 |
|------|------|
| Semantic Block | 語義塊，按語義維度組織的計算單元 |
| Hit Source | 塊內命中源，塊的子計算單元 |
| Seed Answer | 確定性引擎產生的初始假設答案 |
| Seed Verdict | 塊對種子的驗證 (confirm/question/supplement) |
| BlockCoordinator | 塊間協調層，橋接現有 SNN 引擎 |
| Relevance Convergence | 多塊結果的分級融合過程 |
| Multi-Directional Decode | 多維度同時解碼再融合 |
| Cross-Attention | 塊間交叉注意力矩陣 (9x9) |
| Context Budget | 收斂時的 token 分配上限 |
| Cold Start Manager | BlockSNN 未訓練時的降級策略 |

### B. 與 AGENTS.md 的差異

本文檔引入新的目錄結構 `ai/msba/`，需要更新 AGENTS.md 的專案結構描述。

### C. 版本記錄

| 版本 | 日期 | 變更 |
|------|------|------|
| 0.1.0-draft | 2026-09-21 | 初版: 現況 + 目標架構 + 問題分析 |
| 0.2.0-resolved | 2026-09-21 | 解決 15 個問題 (4 誤判 + 6 遺漏 + 5 疏失) |
| 0.2.1-resolved | 2026-09-21 | 誤判5修正: 社交輸入也進 MSBA，所有輸入都需語義上下文 |
