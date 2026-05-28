# Config Refactoring Plan

## Architecture

### `get_authority()` pattern (config_loader.py:142)
All new config keys will be added as sections under `angela_core.yaml` (one of the `_authority_files`). Code reads them via:

```python
cfg = get_angela_config()
val = cfg.get_authority("angela_core", {}).get("new_section", {}).get("key", default)
```

For deeply nested access, use chained `.get()` calls. Already-established shortcut methods (like `get_intent_keywords()`, `get_complexity_thresholds()`) should be reused where applicable, but new sections will require inline `.get_authority()` reads.

### New YAML sections added to `angela_core.yaml`
Each phase below defines a new top-level section (e.g. `math_verifier:`, `spatial_math:`, `user_profile:`, `llm:`). These are additive — no existing `angela_core.yaml` keys are removed or renamed.

### Code changes
Each hardcoded value is replaced with a config read at module/class init time. Fallback defaults match current hardcoded values so behavior is identical when config keys are absent.

---

## Phase 1: math_verifier.py (highest priority)

### New yaml section: `math_verifier:`

```yaml
math_verifier:
  math_keywords:
    - "多少", "多少錢", "價格", "計算", "等於", "總共", "剩下", ...
    - "+", "-", "*", "/", "×", "÷", ...
    - "加", "減", "乘", "除", "平方", "開根號", "次方", "次幂"
  unit_pattern: "\\d+\\s*(元|塊|美元|人民幣|日圓)"
  word_problem:
    pow_kw: ["次方", "次幂", "幂"]
    subtract_ops: ["吃了", "吃掉", "減", "-", "剩", "還有", "拿走", ...]
    add_ops: ["加", "+", "又買", "再拿", "撿到", "找到", "獲得", "生出"]
    multiply_ops: ["倍", "乘", "*", "x"]
  fallback_confidences:
    llm_success: 0.3
    json_fallback: 0.2
    extraction_fallback: 0.1
  verification:
    confidence_clarify_threshold: 0.7
    confidence_direct_threshold: 0.8
    match_epsilon: 0.01
  allowed_chars: "0123456789.+-*/()"
  extract_patterns:
    - "[\\d\\.]+[\\s]*[\\+\\-\\*\\/\\(\\)][\\s]*[\\d\\.]+"
    - "[\\d\\.]+[\\s]*×[\\s]*[\\d\\.]+"
    - "[\\d\\.]+[\\s]*÷[\\s]*[\\d\\.]+"
    - "\\([\\d\\.\\s\\+\\-\\*\\/\\(\\)]+\\)"
```

### Code changes
- **`math_verifier.py:136-143`** — `math_keywords` list → `cfg.get_authority("angela_core", {}).get("math_verifier", {}).get("math_keywords", [...])`, read once in `MathExtractor.__init__` or `_contains_likely_math`
- **`math_verifier.py:148`** — unit regex `r"\d+\s*(元|塊|美元|人民幣|日圓)"` → `re.compile(...)` from config
- **`math_verifier.py:200-208`** — `pow_kw`, `subtract_ops`, `add_ops`, `multiply_ops` tuples → read from `math_verifier.word_problem.*` in `_parse_chinese_word_problem` (lazy load on first call or init)
- **`math_verifier.py:117,122,129`** — hardcoded `confidence = 0.3/0.2/0.1` → `fallback_confidences.*`
- **`math_verifier.py:177-181`** — extract patterns list → `math_verifier.extract_patterns`
- **`math_verifier.py:275`** — `allowed = set("...")` → `math_verifier.allowed_chars`
- **`math_verifier.py:327,332,380`** — threshold 0.01/0.7/0.8 → `math_verifier.verification.*`

---

## Phase 2: chat_service.py (user profile, intent de-dup, state constants)

### New yaml sections

```yaml
user_profile:
  extract_patterns:
    name_intro: ['我叫', '我的名字(?:是|叫)?']
    name_i_am: ['我是']
    favorite: ['最喜歡']
    my_attr: ['我的']
  capture_group_stop_chars: ['，', '。', '。', '.', '!']

services:
  drive:
    base_url: "http://127.0.0.1:8000/api/v1"
    timeouts_seconds:
      status: 10
      list: 15
      sync: 30
      create: 30
      analyze: 60
  web_search:
    default_num_results: 3
    search_prefix_regex: '搜(?:尋|找)(?:一下|)(.+?)(?:好|吗|吗|？)?$'
```

```yaml
# Keys to consolidate under `intents:` (already exists)
# Add `neuro_intent_keywords` sub-section so both
# _build_neuro_intent_vec and _try_neuro_synthesis read from config:
intents:
  # ... existing code/handler keys unchanged ...
  neuro_math: ["計算", "數學", "積分", "微分"]
  neuro_code: ["代碼", "程式", "python", "function"]
```

```yaml
  # Add sub-section inside math intent config:
  math:
    # ... existing keywords, priority, handler ...
    operators: ["+", "-", "*", "/", "×", "÷", "=", "等於"]
    unit_pattern: '\\d+\\s*(隻|個|條|元|塊|美元|米|公分|kg|ml)'
    word_problem_indicators: ["剩", "還有", "吃掉", "吃了", "共"]

  learning:
    # ... existing keywords, priority, handler ...
    learn_keywords: ["記住", "記錄", "學", "learn"]
    teach_keywords: ["教我", "教導", "teach"]
```

```yaml
state_constants:
  theta_decay:
    novelty: 0.05
    negativity: 0.02
    correction_urge: 0.05
  eta_update:
    success_rate_increment: 0.002
    drift_rate: 0.0005
    parameter_tuning_rate: 0.001
    temporal_coherence_decay: 0.01
    memory_depth_rate: 0.001
  state_deltas:
    alpha_energy_stress_factor: 0.05
    alpha_rest_stress_factor: 0.03
    alpha_comfort_stress_factor: 0.5
    alpha_tension_stress_factor: 0.8
    alpha_tension_arousal_factor: 0.2
    beta_focus_short: 0.01
    beta_focus_medium: 0.03
    beta_focus_long: 0.06
    beta_curiosity_base: 0.02
    beta_creativity_positive_boost: 0.03
    beta_creativity_negative_penalty: 0.02
    beta_learning_empathy_scale: 0.02
    gamma_happiness_boost: 0.05
    gamma_love_boost: 0.03
    gamma_sadness_boost: 0.05
    gamma_calm_penalty: 0.03
    gamma_fear_boost: 0.05
    gamma_anger_boost: 0.05
    gamma_trust_base: 0.01
    delta_attention_active: 0.8
    delta_attention_decay: 0.02
    delta_bond_base: 0.01
    delta_presence_base: 0.02
    delta_engagement_base: 0.01
    epsilon_certainty_boost: 0.1
    epsilon_certainty_penalty: 0.15
    epsilon_fatigue_penalty: 0.05
```

### Code changes
- **`chat_service.py:66-73`** — `_build_neuro_intent_vec` intent keywords → `intents.neuro_math` / `intents.neuro_code`
- **`chat_service.py:497-523`** — `_extract_and_store_user_info` hardcoded regex strings → `user_profile.extract_patterns.*`
- **`chat_service.py:456-458`** — `_detect_math_intent` inline operators/unit_pattern/indicators → `intents.math.operators`, `intents.math.unit_pattern`, `intents.math.word_problem_indicators`
- **`chat_service.py:605`** — Drive `base_url` and all `timeout=...` kwargs → `services.drive.*`
- **`chat_service.py:782-784`** — Web search regex and `num_results=3` → `services.web_search.*`
- **`chat_service.py:795-796`** — `learn_kws` / `teach_kws` → `intents.learning.learn_keywords` / `intents.learning.teach_keywords`
- **`chat_service.py:297,348-351,357-361,363,368-372,377-386,389-392,726-731,736-748`** — All state update constants (decays, gains, deltas) → `state_constants.*`; read once in `__init__` or lazily before use
- **`chat_service.py:928-937`** — `_try_neuro_synthesis` duplicated math_kws/code_kws → same as `_build_neuro_intent_vec` fix (read from `intents.neuro_*`)
- **`chat_service.py:1598-1607`** — duplicated again → same fix

---

## Phase 3: cognitive_operations.py (spatial math constants)

### New yaml section: `spatial_math:`

```yaml
spatial_math:
  spatial_ratio: [1.0, 0.3, 0.15]
  precedence:
    "+": 1
    "-": 1
    "*": 2
    "/": 2
    "**": 3
  influence:
    softening: 10.0
    numerator: 25.0
    min_factor: 0.5
    max_factor: 2.0
  epsilon_updates:
    complexity_divisor: 20.0
    certainty_base: 0.5
    certainty_scale: 0.05
    fatigue_increment: 0.02
  gravity:
    pull_factor: 0.05
    epsilon: 0.001
  drag:
    factor: 0.02
```

### Code changes
- **`cognitive_operations.py:40`** — `SPATIAL_RATIO` module-level constant → read from `spatial_math.spatial_ratio` via config at module init (or lazy)
- **`cognitive_operations.py:56-57`** — `softening = 10.0` and `25.0` → `spatial_math.influence.*`
- **`cognitive_operations.py:142`** — `precedence` dict → `spatial_math.precedence`
- **`cognitive_operations.py:167`** — `len(expression) / 20.0` → `spatial_math.epsilon_updates.complexity_divisor`
- **`cognitive_operations.py:200-201`** — `0.5 + 0.05 * len(expression)` → `spatial_math.epsilon_updates.certainty_base` / `.certainty_scale`
- **`cognitive_operations.py:203-204`** — `+ 0.02` fatigue → `spatial_math.epsilon_updates.fatigue_increment`
- **`cognitive_operations.py:215`** — `pull_factor = 0.05` → `spatial_math.gravity.pull_factor`
- **`cognitive_operations.py:221`** — `0.001` epsilon → `spatial_math.gravity.epsilon`
- **`cognitive_operations.py:236`** — `drag_factor = 0.02` → `spatial_math.drag.factor`

---

## Phase 4: angela_llm_service.py (timeouts, backend defaults)

### New yaml sections

```yaml
llm:
  defaults:
    temperature: 0.7
    max_tokens: 512
    timeout_seconds: 30.0
    chat_completion_max_tokens: 256
    generate_text_timeout: 60.0
  backend_priority:
    - "llamacpp"
    - "ollama"
    - "openai"
    - "anthropic"
    - "google"
  health_check_timeouts:
    llamacpp: 5
    ollama: 10
    openai: 5
  biological_state_thresholds:
    energy_low: 30
    energy_medium: 60
    hunger_high: 70
    stress_high: 0.8
    stress_medium: 0.5
    arousal_high: 0.8
    arousal_low: 0.2
    life_intensity_high: 8.0
  template_match:
    direct_threshold: 0.8
    hybrid_min_threshold: 0.5
  memory:
    min_score: 0.7
```

### Code changes
- **`angela_llm_service.py:1699-1701`** — `timeout_seconds = 30.0`, `temperature = 0.7`, `max_tokens = 512` → `llm.defaults.*`
- **`angela_llm_service.py:1096-1102`** — `priority = [LLMBackend.LLAMA_CPP, ...]` → `llm.backend_priority`; map strings to `LLMBackend` enum
- **`angela_llm_service.py:196,351,422,486`** — Backend class `timeout = 120.0` → read from provider config or `llm.defaults.timeout_seconds`
- **`angela_llm_service.py:202,273,362`** — Health check timeouts `5`, `10`, `5` → `llm.health_check_timeouts.*`
- **`angela_llm_service.py:1155-1181`** — `_get_biological_state()` hardcoded thresholds `30`, `60`, `70`, `0.8`, `0.5`, `0.2`, `8.0` → `llm.biological_state_thresholds.*`
- **`angela_llm_service.py:1333,1374`** — `match_score > 0.8` and `> 0.5` → `llm.template_match.*`
- **`angela_llm_service.py:1655`** — `min_score=0.7` → `llm.memory.min_score`
- **`angela_llm_service.py:2143-2144,2197-2198`** — `max_tokens=512`, `temperature=0.7`, `max_tokens=256` → `llm.defaults.*`
- **`angela_llm_service.py:2167,2207`** — `timeout=60.0` → `llm.defaults.generate_text_timeout` / `.chat_completion_max_tokens`

---

## Summary: all yaml additions checklist

| Section Key | Added In | Contains |
|---|---|---|
| `math_verifier:` | Phase 1 | math_keywords, unit_pattern, word_problem ops, fallback confidences, verification thresholds, allowed_chars, extract_patterns |
| `user_profile:` | Phase 2 | extract regex patterns, capture group stop chars |
| `intents.neuro_math:` | Phase 2 | NeuroBlender math keyword list |
| `intents.neuro_code:` | Phase 2 | NeuroBlender code keyword list |
| `intents.math.operators:` | Phase 2 | math operator chars |
| `intents.math.unit_pattern:` | Phase 2 | math extraction unit regex |
| `intents.math.word_problem_indicators:` | Phase 2 | word problem keywords for math detection |
| `intents.learning.learn_keywords:` | Phase 2 | learning handler learn keywords |
| `intents.learning.teach_keywords:` | Phase 2 | learning handler teach keywords |
| `services.drive:` | Phase 2 | Drive API base_url, all timeouts |
| `services.web_search:` | Phase 2 | search regex, num_results |
| `state_constants:` | Phase 2 | theta decay, eta update, all state deltas |
| `spatial_math:` | Phase 3 | spatial_ratio, precedence, influence factors, epsilon update constants, gravity, drag |
| `llm.defaults:` | Phase 4 | temperature, max_tokens, timeout_seconds, generate_text_timeout |
| `llm.backend_priority:` | Phase 4 | ordered list of backend names |
| `llm.health_check_timeouts:` | Phase 4 | per-backend health check timeouts |
| `llm.biological_state_thresholds:` | Phase 4 | energy/hunger/stress/arousal/intensity thresholds |
| `llm.template_match:` | Phase 4 | direct (0.8) and hybrid (0.5) match thresholds |
| `llm.memory:` | Phase 4 | min_score for memory retrieval |
