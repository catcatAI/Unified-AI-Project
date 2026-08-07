# Unified Data-Engineering Pipeline (`data_eng`)

## Status

**Active** — `apps/backend/src/ai/data_eng/`

## Problem

Data-engineering functions (dedup, chunking, reassembly, vocabulary growth) were
implemented **scattered across 15+ locations** with heavy duplication. Every
call-site had its own copy of the same logic, which drifted (e.g. two different
`anchored_decode` implementations, three copies of prefix dedup, four copies of
download key count-suffixing, five separate vocabulary-cap authorities).

| Duplicated capability | Scattered implementations |
|---|---|
| `anchored_decode` (anchor-first + SNN keys) | `garden_engine.py:128` + `ed3n/output_anchor.py` |
| Prefix dedup (happy/happiness) | `garden/dictionary.py` `_find_similar_key`, `_find_similar_key_no_tfidf`, inline encode Step 3 |
| Count-suffix download dedup | `scripts/download_datasets.py` (cedict / jmdict / wordnet / koedict) |
| Sentence splitting | `document/chunker.py` `_split_sentences` + `response/composer.py` `_split_template` |
| Vocabulary cap authority | GARDEN dict / ED3N dict / SNN / `semantic_key_mapper` / `magic_numbers` sizing |

## Design Goals

1. **One canonical implementation per capability** — all call sites delegate.
2. **Precision-loss, not truncation** — dedup merges similar word forms into an
   existing key rather than destroying them; caps stop growth rather than crash.
3. **Config-driven caps** — vocabulary limits flow from `magic_numbers`
   (`model_sizing_config`, `capacity.default.yaml`) instead of per-module
   hardcodes.
4. **Pure, dependency-free functions** — testable without loading torch/ED3N.
5. **No behaviour change on migration** — migrated call-sites keep identical
   semantics (verified by existing + new tests).

## Module Layout

```
apps/backend/src/ai/data_eng/
  __init__.py   # re-exports the public API
  dedup.py      # surface / prefix / semantic / hash-domain / download-key dedup
  chunk.py      # sections / paragraphs / sentences / template-block splitting
  assemble.py   # decode_slot_budget + select_anchored_keys (shared reassembly)
  grow.py       # growth-cap predicates (single cap-decision source)
```

### `dedup.py`

| Function | Replaces | Notes |
|---|---|---|
| `prefix_overlap` | `VectorDictionary._prefix_overlap` | exact 1.0, ~0.8 for happy/happiness |
| `prefix_dedup` | prefix branches of `_find_similar_key` / `_find_similar_key_no_tfidf` / encode Step 3 | returns `(key, score)`; encode caps confidence 0.85 at caller |
| `surface_dedup` | `_surface_set` O(1) lookup | lower-surface → key |
| `semantic_dedup` | TF-IDF/cosine branch of `_find_similar_key` | caller passes `encode` + `matrix` |
| `hash_domain_dedup` | `TrainingCoordinator._seen_hashes` | bounded sha256 per domain |
| `download_dedup_key` / `count_suffix_key` | 4 downloader key builders in `download_datasets.py` | normalize → count-suffix → prefix |

### `chunk.py`

| Function | Replaces |
|---|---|
| `split_sections` | `DocumentChunker._split_sections` |
| `split_paragraphs` | `DocumentChunker._split_paragraphs` |
| `split_sentences` | `DocumentChunker._split_sentences` |
| `split_sentence_blocks` | `Composer._split_template` |

### `assemble.py`

| Function | Replaces |
|---|---|
| `decode_slot_budget` | `garden_engine._slot_budget` (single slot policy) |
| `select_anchored_keys` | `garden_engine._anchored_decode` selection |

> **Scope note (not over-unified):** ED3N's `output_anchor.anchored_decode`
> is NOT migrated.  It is a genuinely different algorithm (variant-based key
> discovery, `top_k_anchors`/`top_k_network`, surface-form dedup) rather than
> the GARDEN slot-budget model.  Sharing a slot budget would change its output;
> the two decoders share the *anchor-first* philosophy but not the mechanics, so
> each keeps its own canonical implementation.  Only the GARDEN one delegates to
> `data_eng.assemble`.

### `grow.py`

| Function | Replaces |
|---|---|
| `resolved_max_entries` | per-layer default (garden 10000 / ED3N 500000) with config override |
| `growth_cap_ok` / `batch_cap_ok` / `growth_gate_batch` | `grow`/`grow_batch` cap gates, SNN 90% eviction decision |

## Capacity Integration

The 10GB GARDEN model target (`max_vocab=51812`, clamped by RAM via the joint
`[bytes, %ram]` capacity cascade) is the single sizing authority. `grow.py`
predicates accept the effective `max_entries` from `magic_numbers`, so a weak
RAM machine runs at a smaller vocabulary (precision-loss) instead of failing.

## Migration Plan

1. ✅ Create `data_eng` package with pure implementations.
2. ✅ Wire `garden/dictionary.py` dedup to `data_eng.dedup` (+ caps to `content` grow via `data_eng.grow`).
3. ✅ Wire `document/chunker.py` + `response/composer.py` splitting to `data_eng.chunk`.
4. ✅ Wire `garden_engine._anchored_decode`/`_slot_budget` to `data_eng.assemble`.
5. ✅ Wire `scripts/download_datasets.py` key builders (jmdict/wordnet/koedict) to `data_eng.dedup.count_suffix_key`.
6. ✅ Wire `training_coordinator` hashing to `data_eng.dedup.hash_domain_dedup`/`hash_input`.
7. ✅ `data_eng` unit tests (+ random sampling) + GARDEN robustness regression tests.
8. ✅ Full affected-suite verification (397 passed, 0 errors).

## Bugs Fixed Along The Way

While migrating, two real GARDEN training bugs were found and fixed:

- **Cross-batch "all input arrays must have the same shape" crash.** `VectorDictionary._rebuild_index()` re-fits the TF-IDF encoder, which grows the embedding dimension as the dictionary grows. Cached query vectors from before the re-fit kept the old dimension, so `encode()`'s batched `np.stack`/`torch.stack` mixed old + new dims and crashed during `learn_batch`. Fix: clear `_embed_cache` in `_rebuild_index()` so only current-dimension vectors are ever stacked. This was the root cause behind the earlier skipped `~47k` GARDEN samples.
- **Non-string training samples crashed `learn_batch`.** `None`/`int` `input`/`output` values raised `AttributeError` inside `_is_deterministic_match` / token splitting / `dictionary.encode`. Fix: coerce to `str` defensively before filtering and encoding.

## Scope Boundaries (Not Over-Engineered)

- `download_daily_data.py` dedup-by-instruction and `seed_vector_store.py` seed-key dedup are clean content-level seen-sets (not count-suffixing); a shared helper for a 5-line loop would add indirection without consolidation value — left as-is.
- ED3N `output_anchor.anchored_decode` is a genuinely different algorithm (variant discovery, top-k anchors/network, surface-form dedup) — intentionally *not* merged with the GARDEN slot-budget decoder.
- `download_datasets.py` cedict converter keeps its dataset-specific `duplicate_en`/`duplicate_zh` branch (mirrors real-world chinese/english collisions) — only the generic count-suffix cases were migrated.

## Verification

- New unit tests under `tests/ai/data_eng/`.
- Existing suites re-run after each migration step (no behaviour drift).
- Random-sample correctness probes on dedup + chunk functions.
- Full-flow test after migration.


## Corpus Streaming Downloader (New)

To fill the ~10GB dataset-volume target with real, openly-licensed multilingual
text, a resumable streaming downloader was added: `scripts/download_corpus.py`.

Sources (verified reachable 2026-08-08):

| Source   | Lang | License     | Ref size (bytes)       |
|----------|------|-------------|------------------------|
| wiki_zh  | zh   | CC BY-SA 4.0 | 3,559,343,816          |
| wiki_ja  | ja   | CC BY-SA 4.0 | 4,827,732,824          |
| wiki_en  | en   | CC BY-SA 4.0 | 26,668,484,995         |
| tatoeba  | multi| CC BY 2.0 FR | 217,621,221            |

Design (matches the streaming/resume plan):

* **Resumable**: each source stores its global byte offset in
  `raw_datasets/corpus/{slug}/state.json`; a re-run issues an HTTP Range request
  from that offset instead of restarting. HTTP 416 is handled as "already
  complete".
* **1 GB segments**: raw bytes are rolled into `{slug}-NNN` files of
  `SEGMENT_BYTES` (1 GB), so each on-disk file stays small and the writer only
  buffers one 64 KB chunk per request.
* **Target**: stops once the accumulated offset reaches the target (10 GB from
  `system.capacity.capacity.dataset.target_volume_mb`, no percent cap). `all`
  walks priority zh -> ja -> en -> tatoeba and stops at target.
* **Wired in**: `train_pipeline._ensure_corpus()` runs it (resumable, warns but
  does not abort training) at Step 1, alongside `_ensure_daily_data()`.

Scope boundary: decompression (.bz2 / .tar.bz2) and clean-paragraph extraction
are deliberately deferred to the training ingest step so the raw dumps stay
reusable.
