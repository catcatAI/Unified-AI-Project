# =============================================================================
# ANGELA-MATRIX: [L3] [αβγ] [B] [L2]
# =============================================================================
"""
data_eng.dedup — single canonical implementations of deduplication.

Consolidates scattered duplicate logic:

  * ``prefix_overlap``      — was ``VectorDictionary._prefix_overlap``
  * ``prefix_dedup``        — was inline encode Step 3 + ``_find_similar_key``
                              and ``_find_similar_key_no_tfidf`` prefix branches
  * ``surface_dedup``       — was ``_surface_set`` O(1) surface-form lookup
  * ``semantic_dedup``      — was the TF-IDF/cosine branch of ``_find_similar_key``
  * ``hash_domain_dedup``   — was ``TrainingCoordinator`` sha256 _seen_hashes
  * ``download_dedup_key``  — was the per-dataset count-suffix logic in
                              scripts/download_datasets.py (cedict/jmdict/wn/koedict)

Design intent: dedup is "precision loss" (merging similar word forms into an
existing key) — never destructive truncation.  Bounds live in the caller.
"""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger(__name__)

__all__ = [
    "count_suffix_key",
    "download_dedup_key",
    "hash_domain_dedup",
    "hash_input",
    "prefix_dedup",
    "prefix_overlap",
    "semantic_dedup",
    "surface_dedup",
]

# --- word-form prefix dedup --------------------------------------------------


def prefix_overlap(a: str, b: str, min_prefix: int = 3) -> float:
    """Compute prefix overlap ratio between two strings.

    Returns 1.0 for exact match, ~0.8 for 'happy'/'happiness', 0.0 for
    unrelated.  Used for word-form dedup (happy/happiness, run/running,
    big/bigger).  Single source of truth — was ``_prefix_overlap``.

    When the shorter string is ENTIRELY contained as a prefix of the longer
    one (``prefix_len == min_len``, e.g. 'con' vs 'consultant'), the score is
    the shorter's fraction of the longer (3/10 = 0.3) — NOT 1.0.  The old
    ``prefix_len / min_len`` returned 1.0 in that case, which made a short
    word like 'con' or 'app' swallow EVERY longer word sharing that prefix
    into one dictionary entry (l24 ended up with 840 unrelated surface
    forms).  Word forms (happy/happiness) keep the high score via the
    ``prefix_len / min_len`` branch because there the prefix is strictly
    shorter than the shorter word.
    """
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0
    prefix_len = 0
    for ca, cb in zip(a, b):
        if ca == cb:
            prefix_len += 1
        else:
            break
    if prefix_len < min_prefix:
        return 0.0
    min_len = min(len(a), len(b))
    if prefix_len >= min_len:
        # Shorter string is a full prefix of the longer one.
        max_len = max(len(a), len(b))
        return prefix_len / max_len if max_len > 0 else 0.0
    return prefix_len / min_len if min_len > 0 else 0.0


def prefix_dedup(
    text: str,
    forms: Iterable[Tuple[str, str]],
    threshold: float = 0.5,
    min_prefix: int = 3,
) -> Tuple[Optional[str], float]:
    """Find the best existing key by word-form prefix overlap.

    ``forms`` is an iterable of ``(lower_surface_form, key)``.  Returns
    ``(key, best_score)`` or ``(None, 0.0)``.  Mirrors the prefix branch of
    ``_find_similar_key`` and the inline encode Step 3 (both used exactly the
    same overlap scoring; encode additionally capped confidence at 0.85).
    """
    lower = text.lower().strip()
    best_key: Optional[str] = None
    best_score = 0.0
    for form, key in forms:
        if not form:
            continue
        score = prefix_overlap(lower, form.lower().strip(), min_prefix=min_prefix)
        if score > best_score:
            best_score = score
            best_key = key
    if best_score >= threshold and best_key:
        return best_key, best_score
    return None, 0.0


# --- surface-form (exact) dedup ---------------------------------------------


def surface_dedup(
    surface: str,
    surface_set: Dict[str, str],
) -> Optional[str]:
    """O(1) exact surface-form lookup.  ``surface_set`` maps lower-surface→key.

    Was ``_surface_set`` maintenance in ``add_entry``/``grow``.
    """
    return surface_set.get(surface.lower().strip())


# --- semantic (TF-IDF / cosine) dedup ---------------------------------------


def semantic_dedup(
    query_text: str,
    encode,
    matrix,
    key_order: List[str],
    threshold: float = 0.5,
    top_k: int = 1,
) -> Tuple[Optional[str], float]:
    """Find the most similar existing key by cosine similarity.

    ``encode`` must accept a list of texts and return a batch of vectors that
    supports ``@ matrix.T`` and ``.argmax()`` (torch or numpy).  Was the
    semantic branch of ``_find_similar_key``.
    """
    try:
        query_vec = encode([query_text])
        scores = matrix @ query_vec.T
        max_score = float(scores.max()) if hasattr(scores, "max") else 0.0
        if max_score >= threshold:
            idx = int(scores.argmax()) if hasattr(scores, "argmax") else 0
            if idx < len(key_order):
                return key_order[idx], max_score
    except Exception as e:
        logger.debug(f"dedup semantic search failed: {e}", exc_info=True)
        return None, 0.0
    return None, 0.0


# --- hash / domain dedup -----------------------------------------------------


def hash_input(sample_input: str) -> str:
    """Return the canonical sha256 hexdigest for a sample.  Single source of
    truth for training-dedup hashing (was TrainingCoordinator's inline sha256)."""
    return hashlib.sha256(sample_input.encode("utf-8")).hexdigest()


def hash_domain_dedup(
    sample_input: str,
    seen_hashes: Dict[str, set],
    domain: str,
    max_hashes_per_domain: int = 10000,
) -> bool:
    """Return True if *sample_input* was already seen for *domain*.

    Mirrors ``TrainingCoordinator._seen_hashes`` sha256 tracking with bounded
    per-domain sets.  When the set exceeds ``max_hashes_per_domain`` the oldest
    entries (last of the set) are dropped — precision loss, not crash.
    """
    h = hashlib.sha256(sample_input.encode("utf-8")).hexdigest()
    domain_hashes = seen_hashes.setdefault(domain, set())
    if h in domain_hashes:
        return True
    domain_hashes.add(h)
    if len(domain_hashes) > max_hashes_per_domain:
        seen_hashes[domain] = set(list(domain_hashes)[-max_hashes_per_domain:])
    return False


# --- download / dataset key count-suffixing ---------------------------------


def _normalize_key(token: str, max_len: Optional[int] = None) -> str:
    """Normalize a word into a dict-key base: lowercase, non-alnum→_, collapse.

    Was repeated in all four downloader converters in download_datasets.py.
    """
    key = re.sub(r"[^a-zA-Z0-9_]", "_", token.lower().strip())
    key = re.sub(r"_+", "_", key).strip("_")
    if max_len is not None and len(key) > max_len:
        key = key[:max_len]
    return key


def count_suffix_key(
    base: str,
    counts: Dict[str, int],
    prefix: str = "",
) -> Tuple[str, int]:
    """Return ``(key, new_count)`` with a count suffix on duplicates.

    Was the ``key_counts[base] += 1; dedup_key = f"{base}_{n}"`` pattern
    repeated four times in download_datasets.py.
    """
    counts[base] = counts.get(base, 0) + 1
    cnt = counts[base]
    dedup_key = f"{base}_{cnt}" if cnt > 1 else base
    return (f"{prefix}{dedup_key}", cnt)


def download_dedup_key(
    en_word: str,
    counts: Dict[str, int],
    prefix: str,
    seen_words: Optional[set] = None,
) -> str:
    """Build a count-suffixed, prefix-qualified dictionary key for a word.

    Consolidated version of the cedict/jmdict/wordnet/koedict key builders:
    normalizes the English surface, assigns a count-suffix when the base key
    repeats, and prefixes with the dataset tag.  ``seen_words`` (when given)
    tracks already-claimed normalized forms so the same word in a different
    language column does not collide.

    Returns e.g. ``cedict_hello`` or ``cedict_hello_2``.
    """
    base = _normalize_key(en_word)
    if not base or len(base) < 2:
        base = f"{prefix}_{abs(hash(en_word)) % 10**6}"
    if seen_words is not None:
        # Claim the base on first sight; collide only on repeat.
        if base in seen_words:
            cnt = counts.get(base, 0) + 1
            counts[base] = cnt
            return f"{prefix}_{base}_{cnt}"
        seen_words.add(base)
    return count_suffix_key(base, counts, prefix=f"{prefix}_")[0]