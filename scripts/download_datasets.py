#!/usr/bin/env python3
"""
Download external lexical datasets and multimodal training datasets.

Usage:
    python scripts/download_datasets.py [dataset ...]

Lexical datasets:
    cedict       CC-CEDICT (Chinese-English, ~5MB, ~120K entries)
    jmdict       JMdict (Japanese-English, ~15MB, ~200K entries)
    wordnet      WordNet 3.0 (English, ~11MB, ~155K synsets)
    koedict      Korean-English Dictionary (~1MB, ~40K entries)

Multimodal training datasets:
    cifar10      CIFAR-10 (60K 32×32 images, 10 classes, ~163MB)
    esc50        ESC-50 (2000 audio clips, 50 classes, ~650MB)

    all          Download all datasets (default: lexical only)
    all-multimodal  Download all multimodal datasets for P28 training

Lexical output: data/dictionaries/{dataset}.json
Multimodal output: data/multimodal/{dataset}/

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
# CIFAR-10 (multimodal image dataset)
# ---------------------------------------------------------------------------

CIFAR10_URL = "https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz"
CIFAR10_TGZ = OUT_DIR.parent / "multimodal" / "cifar-10-python.tar.gz"
CIFAR10_DIR = OUT_DIR.parent / "multimodal" / "cifar-10-batches-py"
CIFAR10_OUT = OUT_DIR.parent / "multimodal" / "cifar10"


def download_cifar10() -> Path:
    """Download CIFAR-10 tar.gz archive; return path."""
    multimodal_dir = OUT_DIR.parent / "multimodal"
    multimodal_dir.mkdir(parents=True, exist_ok=True)
    if CIFAR10_TGZ.exists() and CIFAR10_TGZ.stat().st_size > 100_000_000:
        logger.info("CIFAR-10 already downloaded (%s)", CIFAR10_TGZ)
        return CIFAR10_TGZ
    _urlretrieve(CIFAR10_URL, CIFAR10_TGZ, desc="CIFAR-10")
    return CIFAR10_TGZ


def _unpickle_cifar10(filepath: Path) -> dict:
    """Unpickle a CIFAR-10 batch file."""
    import pickle
    with open(filepath, "rb") as f:
        data = pickle.load(f, encoding="bytes")
    return data


def convert_cifar10(tgz_path: Path) -> Path:
    """Extract CIFAR-10 and save images as .npy files organized by class."""
    import tarfile

    logger.info("Extracting CIFAR-10 …")
    # CIFAR-10 batches are inside cifar-10-batches-py/
    with tarfile.open(tgz_path, "r:gz") as tar:
        tar.extractall(path=CIFAR10_TGZ.parent)

    if not CIFAR10_DIR.exists():
        logger.error("CIFAR-10 extraction failed: %s not found", CIFAR10_DIR)
        return CIFAR10_OUT

    CIFAR10_OUT.mkdir(parents=True, exist_ok=True)

    # Class names for CIFAR-10
    class_names = ["airplane", "automobile", "bird", "cat", "deer",
                   "dog", "frog", "horse", "ship", "truck"]

    batch_files = [
        CIFAR10_DIR / "data_batch_1",
        CIFAR10_DIR / "data_batch_2",
        CIFAR10_DIR / "data_batch_3",
        CIFAR10_DIR / "data_batch_4",
        CIFAR10_DIR / "data_batch_5",
    ]

    all_images = []  # List of (image_bytes, label) tuples
    for bf in batch_files:
        if not bf.exists():
            continue
        batch = _unpickle_cifar10(bf)
        data = batch[b"data"]  # (10000, 3072)
        labels = batch[b"labels"]  # list of 10000 ints
        for i in range(len(labels)):
            # Reshape from 3072 to (32, 32, 3)
            img = data[i].reshape(3, 32, 32).transpose(1, 2, 0)  # (32, 32, 3)
            label = labels[i]
            class_name = class_names[label]
            class_dir = CIFAR10_OUT / class_name
            class_dir.mkdir(exist_ok=True)
            np_path = class_dir / f"img_{i}_{bf.name}.npy"
            np.save(np_path, img.astype(np.uint8))
            all_images.append((img.astype(np.uint8), label, class_name))

    # Also save a combined index for fast loading
    index = {
        "total": len(all_images),
        "classes": class_names,
        "class_counts": {cn: sum(1 for _, _, cn_ in all_images if cn_ == cn) for cn in class_names},
    }
    with open(CIFAR10_OUT / "index.json", "w") as f:
        json.dump(index, f, indent=1)

    logger.info("CIFAR-10: %d images saved to %s (%d classes)",
                len(all_images), CIFAR10_OUT, len(class_names))
    return CIFAR10_OUT


def process_cifar10() -> Path:
    tgz = download_cifar10()
    return convert_cifar10(tgz)


# ---------------------------------------------------------------------------
# ESC-50 (multimodal audio dataset)
# ---------------------------------------------------------------------------

ESC50_URL = "https://github.com/karoldvl/ESC-50/archive/master.zip"
ESC50_ZIP = OUT_DIR.parent / "multimodal" / "ESC-50-master.zip"
ESC50_DIR = OUT_DIR.parent / "multimodal" / "ESC-50-master"
ESC50_OUT = OUT_DIR.parent / "multimodal" / "esc50"


def download_esc50() -> Path:
    """Download ESC-50 zip archive; return path."""
    multimodal_dir = OUT_DIR.parent / "multimodal"
    multimodal_dir.mkdir(parents=True, exist_ok=True)
    if ESC50_ZIP.exists() and ESC50_ZIP.stat().st_size > 100_000_000:
        logger.info("ESC-50 already downloaded (%s)", ESC50_ZIP)
        return ESC50_ZIP
    _urlretrieve(ESC50_URL, ESC50_ZIP, desc="ESC-50")
    return ESC50_ZIP


def convert_esc50(zip_path: Path) -> Path:
    """Extract ESC-50 and convert audio to .npy arrays organized by class."""
    import zipfile

    logger.info("Extracting ESC-50 …")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(path=ESC50_ZIP.parent)

    audio_dir = ESC50_DIR / "audio"
    meta_path = ESC50_DIR / "meta" / "esc50.csv"

    if not audio_dir.exists() or not meta_path.exists():
        logger.error("ESC-50 extraction failed: audio/ or meta/ not found")
        return ESC50_OUT

    ESC50_OUT.mkdir(parents=True, exist_ok=True)

    import csv
    entries = []
    with open(meta_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append({
                "filename": row["filename"],
                "category": row["category"],
                "class_id": int(row["target"]),
                "fold": int(row["fold"]),
            })

    # Group by category
    categories = {}
    for e in entries:
        cat = e["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(e)

    saved = 0
    for cat, cat_entries in categories.items():
        cat_dir = ESC50_OUT / cat.replace(" ", "_")
        cat_dir.mkdir(exist_ok=True)
        for e in cat_entries:
            wav_path = audio_dir / e["filename"]
            if not wav_path.exists():
                continue
            # Save a reference to the original WAV file path (lazy loading)
            ref_path = cat_dir / f"{wav_path.stem}.ref"
            with open(ref_path, "w") as rf:
                rf.write(str(wav_path.resolve()))
            saved += 1

    index = {
        "total": saved,
        "categories": list(categories.keys()),
        "category_counts": {c: len(v) for c, v in categories.items()},
    }
    with open(ESC50_OUT / "index.json", "w") as f:
        json.dump(index, f, indent=1)

    logger.info("ESC-50: %d audio clips indexed in %s (%d classes)",
                saved, ESC50_OUT, len(categories))
    return ESC50_OUT


def process_esc50() -> Path:
    zip_path = download_esc50()
    return convert_esc50(zip_path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

MULTIMODAL_DATASETS = {"cifar10", "esc50"}


def show_stats(path: Path) -> None:
    if not path.exists():
        return
    if path.suffix == ".json":
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
        else:
            logger.info("  %s: %d entries", path.name, len(entries))
    elif (path / "index.json").exists():
        with open(path / "index.json", "r") as f:
            idx = json.load(f)
        logger.info("  %s: %d samples, classes=%s", path.name, idx["total"], idx.get("classes", idx.get("categories", [])))


def main():
    datasets = sys.argv[1:] if len(sys.argv) > 1 else ["all"]

    # "all" means lexical only; "all-multimodal" means multimodal only
    if datasets == ["all"]:
        datasets = ["cedict", "jmdict", "wordnet", "koedict"]
    elif datasets == ["all-multimodal"]:
        datasets = list(MULTIMODAL_DATASETS)

    logger.info("Output directory: %s", OUT_DIR)

    results: dict[str, Path] = {}

    # Lexical datasets
    if "cedict" in datasets:
        results["cedict"] = process_cedict()
    if "jmdict" in datasets:
        results["jmdict"] = process_jmdict()
    if "wordnet" in datasets:
        results["wordnet"] = process_wordnet()
    if "koedict" in datasets:
        results["koedict"] = process_koedict()

    # Multimodal datasets
    if "cifar10" in datasets:
        results["cifar10"] = process_cifar10()
    if "esc50" in datasets:
        results["esc50"] = process_esc50()

    print()
    logger.info("=== Summary ===")
    for name, path in results.items():
        show_stats(path)

    print()
    if any(k in ("cifar10", "esc50") for k in results):
        logger.info("Multimodal datasets ready. Use 'python -m ai.multimodal.data_loader' to verify.")
    logger.info("Done.")


if __name__ == "__main__":
    main()
