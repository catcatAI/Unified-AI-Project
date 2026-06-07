# ED3N Maturity Plan — From Prototype to Production-Ready

## Status Quo

| Metric | Value |
|--------|-------|
| Modules | 17 files, ~2,500+ lines |
| Tests | **0** ❌ |
| CLI | **None** ❌ |
| Config | Hardcoded in Python ❌ |
| Query latency | ~5-50ms (measured) ✅ |
| Checkpoint size | ~500 KB ✅ |
| Training time | 5 min for 12K samples ✅ |
| Training accuracy | 77.7% |
| Reflex patterns | 12,063 (substring match) |

## Maturity Tiers

### Tier 1 — Foundation (1-2h each, can do now)
| # | Task | Effort | Impact |
|---|------|--------|--------|
| 1.1 | **Test suite** — pytest for dictionary, network, trainer, engine, output_anchor, reflex | 2h | 🟢 CRITICAL |
| 1.2 | **Edge case hardening** — empty input, special chars, very long input, missing keys | 1h | 🟢 HIGH |
| 1.3 | **Config-driven presets** — JSON files instead of hardcoded Python dicts | 1h | 🟢 HIGH |
| 1.4 | **CLI tool** — `python -m ed3n query "你好"`, `python -m ed3n train --data path.json` | 1h | 🟢 HIGH |

### Tier 2 — Integration (2-4h each)
| # | Task | Effort | Impact |
|---|------|--------|--------|
| 2.1 | **Wiring: ED3N → app pipeline** — ED3N as a fallback provider in router.py | 3h | 🟢 HIGH |
| 2.2 | **Continuous learning loop** — wire CL pipeline to actual user interactions | 3h | 🟡 MEDIUM |
| 2.3 | **Multimodal integration** — wire image/audio encoders to real VisionService/AudioSystem | 4h | 🟡 MEDIUM |

### Tier 3 — Polish (1-4h each)
| # | Task | Effort | Impact |
|---|------|--------|--------|
| 3.1 | **Reflex deconfliction** — prevent short pattern collisions ("1" matching "100") | 2h | 🟢 HIGH |
| 3.2 | **Dictionary pruning** — auto-cull low-confidence/old entries when size limit reached | 1h | 🟡 MEDIUM |
| 3.3 | **Caching** — LRU cache for network forward + dictionary encode results | 0.5h | 🟡 MEDIUM |
| 3.4 | **Performance telemetry** — timing decorators, latency histogram | 1h | 🟢 LOW |
| 3.5 | **API documentation** — full pydoc strings, generated docs | 1h | 🟢 LOW |

## Execution Order

```
Tier 1 (now) → Tier 2 (next) → Tier 3 (polish)
     ↓               ↓              ↓
  Tests + Edge    Pipeline       Reflex fix
  Config + CLI    Integration    Pruning + Cache
```

## Decision: Plan vs Execute

Tier 1 items (1.1-1.4) are safe to do **now without a separate plan** — they're well-defined, independent, and each has clear success criteria.

Tier 2-3 items need coordination with the broader app (router.py integration, service wiring) and should be planned separately.

**Proceeding with Tier 1 now.**
