#!/usr/bin/env python3
"""
Download external lexical datasets and convert to ED3N dictionary JSON format.

Usage:
    python scripts/download_datasets.py [dataset ...]

Datasets:
    cedict       CC-CEDICT (Chinese-English, ~5MB, ~120K entries)
    jmdict       JMdict (Japanese-English, ~15MB, ~200K entries)
    wordnet      WordNet 3.0 (English, ~11MB, ~155K synsets)
    all          Download all datasets (default)

Output: data/dictionaries/{dataset}.json
  Compatible with DictionaryLayer.import_from_json().

Zero external dependencies — uses only Python stdlib.
"""

import gzip
import json
import logging
import os
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("download_datasets")

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "dictionaries"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TIMEOUT = 300  # generous timeout for weak connections


def _urlretrieve(url: str, dest: Path, desc: str = "") -> None:
    """Download *url* to *dest* with simple progress output."""
    logger.info("Downloading %s …", desc or url)
    req = urllib.request.Request(url, headers={"User-Agent": "ED3N-Dataset-Downloader/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        chunk_size = 64 * 1024
        downloaded = 0
        with open(dest, "wb") as f:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded * 100 // total
                    sys.stdout.write(f"\r  {desc}: {downloaded//1024}KB/{total//1024}KB ({pct}%)")
                    sys.stdout.flush()
    print()
    logger.info("Downloaded %s (%.1fMB)", dest.name, dest.stat().st_size / (1024 * 1024))


# ---------------------------------------------------------------------------
# CC-CEDICT
# ---------------------------------------------------------------------------

CC_CEDICT_URL = "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz"
CC_CEDICT_GZ = OUT_DIR / "cedict_1_0_ts_utf-8_mdbg.txt.gz"


def download_cedict() -> Path:
    """Download CC-CEDICT gz archive; return path."""
    if CC_CEDICT_GZ.exists() and CC_CEDICT_GZ.stat().st_size > 100_000:
        logger.info("CC-CEDICT already downloaded (%s)", CC_CEDICT_GZ)
        return CC_CEDICT_GZ
    _urlretrieve(CC_CEDICT_URL, CC_CEDICT_GZ, desc="CC-CEDICT")
    return CC_CEDICT_GZ


def convert_cedict(gz_path: Path) -> Path:
    """Parse CC-CEDICT and write ED3N JSON with Chinese-English entries."""
    # Line format:
    #   傳統 传统 [pin1 yin1] /translation 1/translation 2/
    line_pat = re.compile(
        r"^(?P<traditional>[^ ]+) (?P<simplified>[^ ]+) \[(?P<pinyin>[^\]]*)\] /(?P<english>.*)/$"
    )

    entries: list[dict] = []
    key_counts: dict[str, int] = {}
    duplicate_en: set[str] = set()
    duplicate_zh: set[str] = set()

    logger.info("Parsing CC-CEDICT …")
    with gzip.open(gz_path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = line_pat.match(line)
            if not m:
                continue

            # Take simplified as primary Chinese form
            zh = m.group("simplified")
            en = m.group("english").strip()
            pinyin = m.group("pinyin").strip()

            # Skip entries where en is empty
            if not en:
                continue

            # The English side may contain multiple translations separated by /
            # Take the first meaningful translation (before any /, before any suffix)
            en_primary = en.split("/")[0].strip()
            if not en_primary:
                continue

            # Build surface forms: zh + en; optionally store pinyin as a variant
            sf: dict[str, str] = {"zh": zh, "en": en_primary}

            # Assign a unique key
            # Use the English word as basis, deduplicate with count suffix
            en_key = re.sub(r"[^a-zA-Z0-9_]", "_", en_primary.lower().strip())
            en_key = re.sub(r"_+", "_", en_key).strip("_")
            if not en_key or len(en_key) < 2:
                en_key = f"cedict_{hash(zh) % 10**6}"

            if en_key in duplicate_en:
                key_counts[en_key] = key_counts.get(en_key, 1) + 1
                dedup_key = f"{en_key}_{key_counts[en_key]}"
            elif zh in duplicate_zh:
                key_counts[f"{en_key}_{zh}"] = key_counts.get(f"{en_key}_{zh}", 0) + 1
                dedup_key = f"{en_key}_{key_counts[f'{en_key}_{zh}']}"
            else:
                dedup_key = en_key
                key_counts[en_key] = 1

            duplicate_en.add(en_key)
            duplicate_zh.add(zh)

            entry = {
                "key": f"cedict_{dedup_key}",
                "surface_forms": sf,
                "contexts": [{"context_id": "cedict", "pinyin": pinyin}] if pinyin else None,
                "relations": {},
                "confidence": 1.0,
            }
            entries.append(entry)

    out_path = OUT_DIR / "cedict.json"
    data = {"version": "2.0", "source": "CC-CEDICT", "entries": entries}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    logger.info("CC-CEDICT: %d entries written to %s (%.1fMB)",
                len(entries), out_path, out_path.stat().st_size / (1024 * 1024))
    return out_path


def process_cedict() -> Path:
    gz = download_cedict()
    return convert_cedict(gz)


# ---------------------------------------------------------------------------
# JMdict (Japanese-English)
# ---------------------------------------------------------------------------

JMDICT_URL = "http://ftp.edrdg.org/pub/Nihongo/JMdict_e.gz"
JMDICT_GZ = OUT_DIR / "JMdict_e.gz"


def download_jmdict() -> Path:
    if JMDICT_GZ.exists() and JMDICT_GZ.stat().st_size > 100_000:
        logger.info("JMdict already downloaded (%s)", JMDICT_GZ)
        return JMDICT_GZ
    _urlretrieve(JMDICT_URL, JMDICT_GZ, desc="JMdict")
    return JMDICT_GZ


def convert_jmdict(gz_path: Path) -> Path:
    """Parse JMdict XML and write ED3N JSON."""
    logger.info("Parsing JMdict …")

    entries: list[dict] = []
    key_counts: dict[str, int] = {}

    with gzip.open(gz_path, "rt", encoding="utf-8") as f:
        tree = ET.parse(f)
    root = tree.getroot()

    for entry_elem in root.findall("entry"):
        # Get kanji element (preferred) or reading element
        keb = entry_elem.find("k_ele/keb")
        reb = entry_elem.find("r_ele/reb")
        kanji = keb.text if keb is not None else None
        reading = reb.text if reb is not None else None

        # Get English gloss(es)
        glosses: list[str] = []
        for sense in entry_elem.findall("sense"):
            for gloss in sense.findall("gloss"):
                if gloss.get("g_type") is None or gloss.get("g_type") in ("", "lit"):
                    txt = (gloss.text or "").strip()
                    if txt:
                        glosses.append(txt)

        if not glosses:
            continue
        en = glosses[0]
        ja = kanji or reading or ""
        if not ja:
            continue

        sf: dict[str, str] = {"ja": ja, "en": en}

        en_key = re.sub(r"[^a-zA-Z0-9_]", "_", en.lower().strip())
        en_key = re.sub(r"_+", "_", en_key).strip("_")
        if not en_key or len(en_key) < 2:
            en_key = f"jmdict_{hash(ja) % 10**6}"

        key_counts[en_key] = key_counts.get(en_key, 0) + 1
        count = key_counts[en_key]
        dedup_key = f"{en_key}_{count}" if count > 1 else en_key

        entry = {
            "key": f"jmdict_{dedup_key}",
            "surface_forms": sf,
            "contexts": (
                [{"context_id": "jmdict", "reading": reading}] if reading and reading != ja else None
            ),
            "relations": {},
            "confidence": 1.0,
        }
        entries.append(entry)

    out_path = OUT_DIR / "jmdict.json"
    data = {"version": "2.0", "source": "JMdict", "entries": entries}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    logger.info("JMdict: %d entries written to %s (%.1fMB)",
                len(entries), out_path, out_path.stat().st_size / (1024 * 1024))
    return out_path


def process_jmdict() -> Path:
    gz = download_jmdict()
    return convert_jmdict(gz)


# ---------------------------------------------------------------------------
# WordNet 3.1
# ---------------------------------------------------------------------------

WN_URL = "https://wordnetcode.princeton.edu/3.0/WordNet-3.0.tar.gz"
WN_TGZ = OUT_DIR / "WordNet-3.0.tar.gz"
WN_DIR = OUT_DIR / "WordNet-3.0"


def download_wordnet() -> Path:
    if WN_TGZ.exists() and WN_TGZ.stat().st_size > 10_000_000:
        logger.info("WordNet-3.1 already downloaded (%s)", WN_TGZ)
        return WN_TGZ
    _urlretrieve(WN_URL, WN_TGZ, desc="WordNet-3.1")
    return WN_TGZ


def _parse_wn_line(line: str) -> dict | None:
    """Parse a single WordNet data.pos line; return {lemma, pos, gloss} or None."""
    parts = line.strip().split(" | ")
    if len(parts) < 2:
        return None
    head = parts[0].strip()
    gloss = parts[1].strip() if len(parts) > 1 else ""

    tokens = head.split()
    if len(tokens) < 4:
        return None
    # tokens[0] = offset, [1] = lex_footnote, [2] = synset_type, [3] = word_count
    word_count = int(tokens[3], 16) if re.match(r'^[0-9a-fA-F]+$', tokens[3]) else 0
    lemmas: list[str] = []
    idx = 4
    for _ in range(word_count):
        if idx < len(tokens):
            lemmas.append(tokens[idx].replace("_", " "))
            idx += 2  # skip lexical_id after each lemma
    if not lemmas:
        return None

    pos_code = tokens[2]
    pos_map = {"n": "noun", "v": "verb", "a": "adj", "s": "adj", "r": "adv"}
    pos = pos_map.get(pos_code, "unknown")

    return {"lemma": lemmas[0], "lemmas": lemmas, "pos": pos, "gloss": gloss, "offset": tokens[0]}


def convert_wordnet(tgz_path: Path) -> Path:
    """Extract and parse WordNet 3.0 data files; write ED3N JSON."""
    import tarfile

    logger.info("Extracting WordNet-3.0 …")
    with tarfile.open(tgz_path, "r:gz") as tar:
        tar.extractall(path=OUT_DIR)

    data_dir = WN_DIR / "dict"
    if not data_dir.exists():
        # WordNet 3.0 tarball has dict/ inside a WordNet-3.0/ subdirectory
        inner = WN_DIR / "WordNet-3.0" / "dict"
        if inner.exists():
            data_dir = inner
        else:
            logger.error("WordNet dict/ directory not found in %s", WN_DIR)
        return OUT_DIR / "wordnet.json"

    entries: list[dict] = []
    key_counts: dict[str, int] = {}

    for pos_file in sorted(data_dir.glob("data.*")):
        pos_name = pos_file.suffix[1:]  # n, v, a, r
        pos_map_full = {"n": "noun", "v": "verb", "a": "adj", "r": "adv"}
        pos_full = pos_map_full.get(pos_name, "unknown")

        logger.info("  Parsing data.%s …", pos_name)
        with open(pos_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("  "):
                    continue  # comment line
                parsed = _parse_wn_line(line)
                if parsed is None:
                    continue

                lemma = parsed["lemma"]
                lemmas = parsed["lemmas"]
                gloss = parsed["gloss"]

                # Extract first sentence from gloss as definition
                defn = gloss.split(";")[0].strip() if gloss else lemma

                sf: dict[str, str] = {"en": lemma}
                entry_key = lemma.lower().replace(" ", "_")
                entry_key = re.sub(r"[^a-z0-9_]", "", entry_key)

                key_counts[entry_key] = key_counts.get(entry_key, 0) + 1
                cnt = key_counts[entry_key]
                dedup_key = f"{entry_key}_{cnt}" if cnt > 1 else entry_key

                # Add synonyms as relations
                rels: dict[str, list[str]] = {}
                if len(lemmas) > 1:
                    syn_keys = []
                    for s in lemmas[1:]:
                        sk = s.lower().replace(" ", "_")
                        sk = re.sub(r"[^a-z0-9_]", "", sk)
                        if sk and sk != entry_key:
                            syn_keys.append(f"wn_{pos_full}_{sk}")
                    if syn_keys:
                        rels["synonym"] = syn_keys[:10]  # limit to avoid bloat

                entry = {
                    "key": f"wn_{pos_full}_{dedup_key}",
                    "surface_forms": sf,
                    "contexts": [{"context_id": "wordnet", "pos": pos_full, "gloss": defn}],
                    "relations": rels,
                    "confidence": 1.0,
                }
                entries.append(entry)

    out_path = OUT_DIR / "wordnet.json"
    data = {"version": "2.0", "source": "WordNet-3.0", "entries": entries}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    logger.info("WordNet: %d entries written to %s (%.1fMB)",
                len(entries), out_path, out_path.stat().st_size / (1024 * 1024))
    return out_path


def process_wordnet() -> Path:
    tgz = download_wordnet()
    return convert_wordnet(tgz)


# ---------------------------------------------------------------------------
# Korean-English Dictionary (KOEDict)
# ---------------------------------------------------------------------------

KOEDICT_URL = (
    "https://raw.githubusercontent.com/mhagiwara/korean-english-dictionary/"
    "master/data/korean_english_dictionary.txt"
)
KOEDICT_TXT = OUT_DIR / "korean_english_dictionary.txt"


def download_koedict() -> Path:
    """Download Korean-English dictionary tabfile; return path."""
    if KOEDICT_TXT.exists() and KOEDICT_TXT.stat().st_size > 100_000:
        logger.info("KOEDict already downloaded (%s)", KOEDICT_TXT)
        return KOEDICT_TXT
    _urlretrieve(KOEDICT_URL, KOEDICT_TXT, desc="KOEDict")
    return KOEDICT_TXT


def convert_koedict(txt_path: Path) -> Path:
    """Parse Korean-English tabfile and write ED3N JSON.

    Format per line:  korean<TAB>english
    """
    entries: list[dict] = []
    key_counts: dict[str, int] = {}
    seen_pairs: set[tuple[str, str]] = set()

    logger.info("Parsing KOEDict …")
    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t", 1)
            if len(parts) != 2:
                continue
            ko, en = parts[0].strip(), parts[1].strip()
            if not ko or not en:
                continue
            # Deduplicate identical ko↔en pairs
            pair = (ko, en)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            sf: dict[str, str] = {"ko": ko, "en": en}

            en_key = re.sub(r"[^a-zA-Z0-9_]", "_", en.lower().strip())
            en_key = re.sub(r"_+", "_", en_key).strip("_")
            if not en_key or len(en_key) < 2:
                en_key = f"koedict_{hash(ko) % 10**6}"

            key_counts[en_key] = key_counts.get(en_key, 0) + 1
            cnt = key_counts[en_key]
            dedup_key = f"{en_key}_{cnt}" if cnt > 1 else en_key

            entry = {
                "key": f"koedict_{dedup_key}",
                "surface_forms": sf,
                "contexts": [{"context_id": "koedict"}],
                "relations": {},
                "confidence": 1.0,
            }
            entries.append(entry)

    out_path = OUT_DIR / "koedict.json"
    data = {"version": "2.0", "source": "KOEDict", "entries": entries}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    logger.info("KOEDict: %d entries written to %s (%.1fMB)",
                len(entries), out_path, out_path.stat().st_size / (1024 * 1024))
    return out_path


def process_koedict() -> Path:
    txt = download_koedict()
    return convert_koedict(txt)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def show_stats(path: Path) -> None:
    if not path.exists():
        return
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    entries = data.get("entries", [])
    if entries:
        lang_counts: dict[str, int] = {}
        for e in entries:
            for lang in e.get("surface_forms", {}):
                lang_counts[lang] = lang_counts.get(lang, 0) + 1
        lang_summary = ", ".join(f"{k}={v}" for k, v in sorted(lang_counts.items()))
        logger.info("  %s: %d entries (%s)", path.name, len(entries), lang_summary)


def main():
    datasets = sys.argv[1:] if len(sys.argv) > 1 else ["all"]

    logger.info("Output directory: %s", OUT_DIR)

    results: dict[str, Path] = {}

    if "all" in datasets or "cedict" in datasets:
        results["cedict"] = process_cedict()
    if "all" in datasets or "jmdict" in datasets:
        results["jmdict"] = process_jmdict()
    if "all" in datasets or "wordnet" in datasets:
        results["wordnet"] = process_wordnet()
    if "all" in datasets or "koedict" in datasets:
        results["koedict"] = process_koedict()

    print()
    logger.info("=== Summary ===")
    for name, path in results.items():
        show_stats(path)

    print()
    logger.info("Done. Run 'python scripts/import_dictionaries.py' to load into ED3N.")


if __name__ == "__main__":
    main()
