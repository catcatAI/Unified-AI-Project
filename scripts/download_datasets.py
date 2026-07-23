#!/usr/bin/env python3
"""
ANGELA-MATRIX: [L4] [βγδ] [B] [L3-L5]
Download and prepare association training datasets for ED3N/GARDEN SNN.

Datasets downloaded:
  1. WordNet associations (synonyms, antonyms, hypernyms) ~5MB
  2. ConceptNet associations (common-sense relations) ~500MB (filtered)
  3. STS Benchmark (semantic similarity) ~10MB
  4. Tatoeba parallel sentences (multilingual) ~200MB
  5. PPDB Paraphrase Database ~100MB (filtered)

Total target: <1GB (well under 10GB limit)

Output: apps/backend/data/raw_datasets/association_*.json
"""

import json
import logging
import os
import sys
import time
import urllib.request
import urllib.error
import gzip
import csv
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("DatasetDownloader")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT, "apps/backend/data/raw_datasets")
os.makedirs(DATA_DIR, exist_ok=True)

# Max size per dataset in bytes (total budget: 1GB)
MAX_SIZES = {
    "wordnet": 10 * 1024 * 1024,       # 10MB
    "conceptnet": 500 * 1024 * 1024,    # 500MB
    "sts": 20 * 1024 * 1024,            # 20MB
    "tatoeba": 300 * 1024 * 1024,       # 300MB
    "ppdb": 150 * 1024 * 1024,          # 150MB
}


def _download(url: str, dest: str, max_size: int = 0) -> bool:
    """Download a file with progress reporting."""
    if os.path.exists(dest):
        sz = os.path.getsize(dest)
        logger.info("  Already exists: %s (%.1f MB)", os.path.basename(dest), sz / 1024 / 1024)
        return True
    try:
        logger.info("  Downloading: %s", url)
        req = urllib.request.Request(url, headers={"User-Agent": "AngelaAI/1.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            if max_size > 0 and total > max_size:
                logger.warning("  Skipping %s: too large (%d MB > %d MB limit)",
                             os.path.basename(dest), total / 1024 / 1024, max_size / 1024 / 1024)
                return False
            downloaded = 0
            with open(dest, "wb") as f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0 and downloaded % (1024 * 1024) < 65536:
                        logger.info("    %.1f / %.1f MB (%.0f%%)",
                                   downloaded / 1024 / 1024, total / 1024 / 1024,
                                   100 * downloaded / total)
        logger.info("  Downloaded: %s (%.1f MB)", os.path.basename(dest), downloaded / 1024 / 1024)
        return True
    except Exception as e:
        logger.error("  Failed to download %s: %s", url, e)
        if os.path.exists(dest):
            os.remove(dest)
        return False


# ---------------------------------------------------------------------------
# 1. WordNet Associations
# ---------------------------------------------------------------------------

def download_wordnet() -> List[Dict]:
    """Download WordNet and extract synonym/antonym/hypernyms triples."""
    logger.info("=== WordNet Associations ===")

    try:
        import nltk
        nltk.download("wordnet", quiet=True)
        nltk.download("omw-1.4", quiet=True)
        from nltk.corpus import wordnet as wn
    except ImportError:
        logger.warning("nltk not installed, skipping WordNet")
        return []

    triples = []
    seen = set()

    for synset in wn.all_synsets():
        # Synonyms (words in same synset)
        words = [w.name().replace("_", " ") for w in synset.lemmas()]
        for i, w1 in enumerate(words):
            for w2 in words[i + 1:]:
                key = (w1.lower(), "synonym", w2.lower())
                if key not in seen:
                    seen.add(key)
                    triples.append({"concept_a": w1, "concept_b": w2,
                                   "relation": "synonym", "strength": 0.9})

        # Antonyms
        for lemma in synset.lemmas():
            for antonym in lemma.antonyms():
                w1 = lemma.name().replace("_", " ")
                w2 = antonym.name().replace("_", " ")
                key = (w1.lower(), "antonym", w2.lower())
                if key not in seen:
                    seen.add(key)
                    triples.append({"concept_a": w1, "concept_b": w2,
                                   "relation": "antonym", "strength": 0.85})

        # Hypernyms (is-a relationships)
        for hypernym in synset.hypernyms():
            for lemma in synset.lemmas():
                w1 = lemma.name().replace("_", " ")
                for hlemma in hypernym.lemmas():
                    w2 = hlemma.name().replace("_", " ")
                    key = (w1.lower(), "hypernym", w2.lower())
                    if key not in seen:
                        seen.add(key)
                        triples.append({"concept_a": w1, "concept_b": w2,
                                       "relation": "hypernym", "strength": 0.8})

        # Hyponyms (reverse of hypernym)
        for hyponym in synset.hyponyms():
            for lemma in synset.lemmas():
                w1 = lemma.name().replace("_", " ")
                for hlemma in hyponym.lemmas():
                    w2 = hlemma.name().replace("_", " ")
                    key = (w1.lower(), "hyponym", w2.lower())
                    if key not in seen:
                        seen.add(key)
                        triples.append({"concept_a": w1, "concept_b": w2,
                                       "relation": "hyponym", "strength": 0.8})

    logger.info("  Extracted %d WordNet triples", len(triples))
    return triples


# ---------------------------------------------------------------------------
# 2. ConceptNet Associations
# ---------------------------------------------------------------------------

def download_conceptnet() -> List[Dict]:
    """Download ConceptNet from HuggingFace (trimmed English subset)."""
    logger.info("=== ConceptNet Associations ===")

    try:
        from datasets import load_dataset
        # Use the pre-trimmed English ConceptNet from HuggingFace
        dataset = load_dataset("CleverThis/conceptnet", split="data")
        triples = []
        for item in dataset:
            data = item.get("data", {})
            start = data.get("start", "").replace("/c/en/", "").replace("_", " ").split("/")[-1]
            end = data.get("end", "").replace("/c/en/", "").replace("_", " ").split("/")[-1]
            rel = data.get("relation", "").split("/")[-1]
            weight = data.get("weight", 0.5)

            if not start or not end or start == end:
                continue

            # Map relation names
            rel_map = {
                "Synonym": "synonym", "Antonym": "antonym",
                "IsA": "hypernym", "HasProperty": "property",
                "UsedFor": "purpose", "CapableOf": "capability",
                "AtLocation": "location", "HasA": "part",
                "PartOf": "whole", "RelatedTo": "related",
                "Causes": "causes", "SimilarTo": "similar",
            }
            mapped_rel = rel_map.get(rel, "related")
            triples.append({
                "concept_a": start.lower(),
                "concept_b": end.lower(),
                "relation": mapped_rel,
                "strength": min(1.0, max(0.1, float(weight))),
            })
            if len(triples) >= 500000:
                break

        logger.info("  Extracted %d ConceptNet triples from HuggingFace", len(triples))
        return triples

    except Exception as e:
        logger.warning("  HuggingFace download failed: %s", e)
        return _generate_conceptnet_sample()


def _generate_conceptnet_sample() -> List[Dict]:
    """Generate a small ConceptNet-like sample from curated common-sense."""
    logger.info("  Generating curated common-sense associations")
    associations = [
        # Physical properties
        ("fire", "hot", "property", 0.95), ("ice", "cold", "property", 0.95),
        ("sun", "bright", "property", 0.9), ("night", "dark", "property", 0.9),
        ("water", "wet", "property", 0.9), ("stone", "hard", "property", 0.85),
        ("feather", "light", "property", 0.85), ("lead", "heavy", "property", 0.9),
        # Functional
        ("knife", "cut", "capability", 0.9), ("hammer", "hit", "capability", 0.9),
        ("car", "drive", "purpose", 0.95), ("book", "read", "purpose", 0.95),
        ("phone", "call", "purpose", 0.9), ("shoes", "wear", "purpose", 0.9),
        # Locations
        ("fish", "water", "location", 0.9), ("bird", "sky", "location", 0.85),
        ("tree", "forest", "location", 0.8), ("fish", "ocean", "location", 0.85),
        # Is-a (hypernym)
        ("dog", "animal", "hypernym", 0.95), ("cat", "animal", "hypernym", 0.95),
        ("rose", "flower", "hypernym", 0.9), ("oak", "tree", "hypernym", 0.9),
        ("piano", "instrument", "hypernym", 0.9), ("guitar", "instrument", "hypernym", 0.9),
        ("spoon", "utensil", "hypernym", 0.85), ("fork", "utensil", "hypernym", 0.85),
        # Antonyms
        ("hot", "cold", "antonym", 0.95), ("big", "small", "antonym", 0.95),
        ("fast", "slow", "antonym", 0.9), ("up", "down", "antonym", 0.9),
        ("light", "dark", "antonym", 0.9), ("hard", "soft", "antonym", 0.85),
        ("old", "new", "antonym", 0.85), ("tall", "short", "antonym", 0.9),
        # Synonyms
        ("happy", "joyful", "synonym", 0.9), ("big", "large", "synonym", 0.9),
        ("fast", "quick", "synonym", 0.9), ("smart", "clever", "synonym", 0.85),
        ("brave", "courageous", "synonym", 0.9), ("easy", "simple", "synonym", 0.85),
        # Causes
        ("fire", "heat", "causes", 0.9), ("rain", "wet", "causes", 0.85),
        ("earthquake", "damage", "causes", 0.9), ("study", "knowledge", "causes", 0.8),
        # Part-whole
        ("wheel", "car", "whole", 0.9), ("key", "keyboard", "whole", 0.9),
        ("finger", "hand", "whole", 0.95), ("page", "book", "whole", 0.9),
    ]
    return [{"concept_a": a, "concept_b": b, "relation": r, "strength": s}
            for a, b, r, s in associations]


# ---------------------------------------------------------------------------
# 3. STS Benchmark (Semantic Textual Similarity)
# ---------------------------------------------------------------------------

def download_sts() -> List[Dict]:
    """Download STS Benchmark for semantic similarity training."""
    logger.info("=== STS Benchmark ===")

    try:
        from datasets import load_dataset
        dataset = load_dataset("sentence-transformers/stsb", split="test")
        triples = []
        for item in dataset:
            score = item.get("score", 0)
            strength = min(1.0, float(score))
            if strength < 0.2:
                continue
            triples.append({
                "concept_a": item.get("sentence1", "").lower(),
                "concept_b": item.get("sentence2", "").lower(),
                "relation": "similarity",
                "strength": strength,
            })
        logger.info("  Extracted %d STS pairs from HuggingFace", len(triples))
        return triples
    except Exception as e:
        logger.warning("  HuggingFace STS download failed: %s", e)
        return []


# ---------------------------------------------------------------------------
# 4. Tatoeba Parallel Sentences
# ---------------------------------------------------------------------------

def download_tatoeba() -> List[Dict]:
    """Download Tatoeba parallel sentences for cross-lingual alignment."""
    logger.info("=== Tatoeba Parallel Sentences ===")

    # Use Tatoeba API to get English sentences with Chinese translations
    # API endpoint: https://tatoeba.org/eng/api_v0/search?from=eng&to=cmn&...
    triples = []
    try:
        for offset in range(0, 30000, 100):
            url = (f"https://tatoeba.org/eng/api_v0/search?"
                   f"from=eng&to=cmn&limit=100&offset={offset}")
            req = urllib.request.Request(url, headers={"User-Agent": "AngelaAI/1.0"})
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    results = data.get("results", [])
                    if not results:
                        break
                    for r in results:
                        eng = r.get("text", "")
                        trans = r.get("translations", [[]])
                        if trans and isinstance(trans, list) and trans[0]:
                            zho = trans[0][0].get("text", "")
                            if eng and zho:
                                triples.append({
                                    "concept_a": eng.lower(),
                                    "concept_b": zho,
                                    "relation": "translation",
                                    "strength": 0.95,
                                })
            except Exception:
                break
            if len(triples) >= 20000:
                break
            time.sleep(0.3)
    except Exception as e:
        logger.warning("  Tatoeba API failed: %s", e)

    logger.info("  Extracted %d Tatoeba pairs", len(triples))
    return triples


# ---------------------------------------------------------------------------
# 5. PPDB Paraphrase Database (filtered)
# ---------------------------------------------------------------------------

def download_ppdb() -> List[Dict]:
    """Download PPDB paraphrase database for synonym-like associations."""
    logger.info("=== PPDB Paraphrases ===")

    try:
        from datasets import load_dataset
        # Use ParaNMT-50M or similar paraphrase dataset
        dataset = load_dataset("sentence-transformers/para-nmt-50m", split="train[:200000]")
        triples = []
        for item in dataset:
            t1 = item.get("text1", "").lower()
            t2 = item.get("text2", "").lower()
            if t1 and t2 and t1 != t2:
                triples.append({
                    "concept_a": t1,
                    "concept_b": t2,
                    "relation": "paraphrase",
                    "strength": 0.85,
                })
        logger.info("  Extracted %d paraphrase pairs from HuggingFace", len(triples))
        return triples
    except Exception as e:
        logger.warning("  HuggingFace paraphrase download failed: %s", e)
        return []


# ---------------------------------------------------------------------------
# Combine and save
# ---------------------------------------------------------------------------

def combine_and_save(all_triples: List[Dict]) -> str:
    """Combine all triples, deduplicate, and save."""
    # Deduplicate
    seen = set()
    unique = []
    for t in all_triples:
        key = (t["concept_a"], t["concept_b"], t["relation"])
        if key not in seen:
            seen.add(key)
            unique.append(t)

    # Sort by strength descending
    unique.sort(key=lambda x: x["strength"], reverse=True)

    # Save
    output_path = os.path.join(DATA_DIR, "association_training_data.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(unique, f, ensure_ascii=False, indent=1)

    size_mb = os.path.getsize(output_path) / 1024 / 1024
    logger.info("=== Total: %d unique triples (%.1f MB) ===", len(unique), size_mb)
    logger.info("  Saved to: %s", output_path)

    # Print stats
    relations = {}
    for t in unique:
        r = t["relation"]
        relations[r] = relations.get(r, 0) + 1
    logger.info("  Relation distribution:")
    for r, count in sorted(relations.items(), key=lambda x: -x[1]):
        logger.info("    %s: %d", r, count)

    return output_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    logger.info("Starting dataset download and preparation")
    logger.info("Data directory: %s", DATA_DIR)

    all_triples = []

    # 1. WordNet
    wordnet_triples = download_wordnet()
    all_triples.extend(wordnet_triples)

    # 1b. Curated common-sense (always included)
    curated = _generate_conceptnet_sample()
    all_triples.extend(curated)
    logger.info("  Added %d curated common-sense triples", len(curated))

    # 2. ConceptNet (skip - 34M rows too slow to download, curated sample above)
    # conceptnet_triples = download_conceptnet()
    # all_triples.extend(conceptnet_triples)

    # 3. STS Benchmark (skip - sentence similarity, not concept associations)
    # sts_triples = download_sts()
    # all_triples.extend(sts_triples)

    # 4. Tatoeba (skip - API too slow, add manually if needed)
    # tatoeba_triples = download_tatoeba()
    # all_triples.extend(tatoeba_triples)

    # 5. PPDB (skip - large download, add manually if needed)
    # ppdb_triples = download_ppdb()
    # all_triples.extend(ppdb_triples)

    # Combine and save
    output = combine_and_save(all_triples)

    logger.info("Done! Output: %s", output)
    return output


if __name__ == "__main__":
    main()
