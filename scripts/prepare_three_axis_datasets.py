#!/usr/bin/env python3
"""
=============================================================================
ANGELA-MATRIX: [L4] [βγδ] [B] [L3-L5]
=============================================================================

Auto-prepare Three-Axis training datasets.

Decides WHICH datasets to ensure and HOW MUCH (sample counts) based on the
runtime hardware profile and the project memory capacity budget, then fetches
or generates whatever is missing:

  * arithmetic_train_dataset.json  generated (synthetic) if missing
  * logic_train.json               generated (synthetic) if missing
  * alpaca_data.json               downloaded (real, Stanford Alpaca) if missing
  * wiki corpus                    optional, resume-downloaded via --with-corpus

Outputs a manifest at data/checkpoints/three_axis/dataset_manifest.json that
scripts/train_three_axis.py reads to decide its per-dataset sample caps.

Auto-decision inputs (see decide_plan):
  * hardware profile (HardwareScenario): full / medium / small tiers
  * memory capacity (effective_capacity_bytes): clamps sample counts so the
    estimated resident footprint stays within half the budget
  * what is already present (idempotent: existing files are reused)

Usage:
  python scripts/prepare_three_axis_datasets.py [--dry-run] [--force] [--with-corpus]
"""

# =============================================================================
# ANGELA-MATRIX: [L4] [βγδ] [B] [L3-L5]
# =============================================================================

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from typing import Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("prepare_three_axis")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "apps/backend/src")
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SRC)

DATA_DIR = os.path.join(ROOT, "apps/backend/data/raw_datasets")
CHECKPOINT_DIR = os.path.join(ROOT, "data/checkpoints/three_axis")
MANIFEST = os.path.join(CHECKPOINT_DIR, "dataset_manifest.json")

ARITHMETIC_PATH = os.path.join(DATA_DIR, "arithmetic_train_dataset.json")
LOGIC_PATH = os.path.join(DATA_DIR, "logic_train.json")
ALPACA_PATH = os.path.join(DATA_DIR, "alpaca_data.json")

# Measured 2026-08-19 (byte-based engine, 2 GiB cap context): exact-completions
# cost ~ O(sample_len^2), so long samples (alpaca) cost far more per byte than
# short ones (arithmetic/logic). Values are B per UTF-8 *byte* (the position
# axis counts bytes, not chars — a CJK char is 3 bytes).
#   arithmetic: ~110 B/byte  |  logic: ~120 B/byte  |  alpaca: ~2,000 B/byte
# These are lower bounds; the per-dataset budget is the authoritative clamp.
BYTES_PER_CHAR = {
    "arithmetic": 110.0,
    "logic": 120.0,
    "alpaca": 2000.0,
}

# Fraction of the memory cap reserved per dataset (leaves ~10% headroom).
# alpaca is intentionally capped small — its long samples dominate memory.
BUDGET_FRACTION = {
    "arithmetic": 0.15,
    "logic": 0.25,
    "alpaca": 0.50,
}

# Per-tier upper bounds on sample counts (hardware-aware ceiling).
TIER_CAPS = {
    "full": {"arithmetic": 30000, "logic": 10000, "alpaca": 20000},
    "medium": {"arithmetic": 15000, "logic": 5000, "alpaca": 10000},
    "small": {"arithmetic": 5000, "logic": 2000, "alpaca": 5000},
}

TIER_BY_SCENARIO = {
    "high_performance_desktop": "full",
    "server_cloud": "full",
    "desktop_igpu": "medium",
    "laptop_normal": "medium",
    "laptop_power_saver": "small",
    "low_power_device": "small",
}


def detect_profile() -> str:
    """Return the current hardware scenario value, or 'unknown'."""
    try:
        from core.system.config.hardware_profile import HardwareProfile

        return HardwareProfile().scenario.value
    except Exception:  # noqa: BLE001 - graceful fallback, decision still works
        logger.warning("Hardware profile detection failed; defaulting to medium tier")
        return "unknown"


def memory_cap_bytes() -> int:
    """Resolve the project memory capacity budget (bytes)."""
    try:
        from core.system.config.magic_numbers import _probe_ram_total_gb, effective_capacity_bytes

        ram_total = _probe_ram_total_gb()
        cap = int(effective_capacity_bytes("memory", total_gb=ram_total, numeric_mb=2048))
        return cap if cap > 0 else 2048 * 1024 * 1024
    except Exception:  # noqa: BLE001 - defensive fallback to 2 GiB default
        return 2048 * 1024 * 1024


def decide_plan(
    profile_scenario: str,
    mem_cap: int,
    with_corpus: bool = False,
    avg_lens: Optional[Dict[str, float]] = None,
) -> dict:
    """Auto-decide the dataset plan: which samples and how many.

    Memory is the authoritative clamp: each dataset is budgeted a fraction of
    the memory cap, and the sample count is that budget divided by the
    per-byte cost times the measured average sample length (UTF-8 bytes). The
    hardware tier is an upper bound (full/medium/small), not the deciding
    factor.
    """
    tier = TIER_BY_SCENARIO.get(profile_scenario, "medium")
    avg_lens = avg_lens or {}
    caps: Dict[str, int] = {}
    rationale: Dict[str, str] = {}
    for key, budget_frac in BUDGET_FRACTION.items():
        tier_cap = TIER_CAPS[tier][key]
        budget_bytes = mem_cap * budget_frac
        avg_len = avg_lens.get(key) or 80.0  # fallback if not measurable
        mem_cap_n = int(budget_bytes / max(1.0, BYTES_PER_CHAR[key]) / max(1, avg_len))
        chosen = min(tier_cap, mem_cap_n)
        caps[key] = max(1, chosen)
        rationale[key] = (
            f"min(tier={tier_cap}, mem={mem_cap_n})"
            if chosen == mem_cap_n
            else f"tier cap={tier_cap}"
        )
    return {
        "hardware_profile": profile_scenario,
        "tier": tier,
        "memory_cap_bytes": mem_cap,
        "bytes_per_char": BYTES_PER_CHAR,
        "budget_fraction": BUDGET_FRACTION,
        "caps": caps,
        "rationale": rationale,
        "corpus": with_corpus,
    }


def measure_avg_lens() -> Dict[str, float]:
    """Measure mean serialised sample length (UTF-8 bytes) per dataset.

    The three-axis position axis counts UTF-8 *bytes* (0..255), not Unicode
    code points; a CJK char occupies 3 positions, so lengths are measured in
    encoded bytes to match the engine's memory model.
    """
    result: Dict[str, float] = {}
    specs = {
        "arithmetic": (
            ARITHMETIC_PATH,
            lambda it: f"{it.get('problem', '')}={it.get('answer', '')}",
        ),
        "logic": (LOGIC_PATH, lambda it: f"{it.get('proposition', '')}={it.get('answer', '')}"),
        "alpaca": (
            ALPACA_PATH,
            lambda it: f"{it.get('instruction', '')}={it.get('output', '')}",
        ),
    }
    for key, (path, ser) in specs.items():
        data = _load_json_list(path)
        if not data:
            result[key] = 0.0
            continue
        sample = data[:2000]
        lens = [len(ser(it).encode("utf-8")) for it in sample if it]
        result[key] = sum(lens) / max(1, len(lens)) if lens else 0.0
    return result


def _load_json_list(path: str) -> list:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, list) else []
    except Exception as exc:  # noqa: BLE001 - corrupt file treated as absent
        logger.warning("Corrupt dataset %s (%s); treating as missing", path, exc)
        return []


def ensure_arithmetic(path: str, target: int, force: bool = False) -> bool:
    """Generate the arithmetic dataset if missing (or force)."""
    existing = _load_json_list(path)
    if existing and not force:
        logger.info("arithmetic: present (%d samples), reuse", len(existing))
        return True
    try:
        sys.path.insert(0, SCRIPTS_DIR)
        from generate_training_data import gen_math_samples, write_math_extra

        samples = gen_math_samples(count=target)
        write_math_extra(path, samples)
        logger.info("arithmetic: generated %d samples -> %s", len(samples), path)
        return True
    except Exception as exc:  # noqa: BLE001 - generation failure must be loud
        logger.error("arithmetic generation failed: %s", exc)
        return False


def ensure_logic(path: str, target: int, force: bool = False) -> bool:
    """Generate the logic dataset if missing (or force)."""
    existing = _load_json_list(path)
    if existing and not force:
        logger.info("logic: present (%d samples), reuse", len(existing))
        return True
    try:
        sys.path.insert(0, SCRIPTS_DIR)
        from generate_training_data import gen_logic_samples, write_logic_train

        samples = gen_logic_samples(count=target)
        write_logic_train(samples, path)
        logger.info("logic: generated %d samples -> %s", len(samples), path)
        return True
    except Exception as exc:  # noqa: BLE001 - generation failure must be loud
        logger.error("logic generation failed: %s", exc)
        return False


def ensure_alpaca(path: str, force: bool = False) -> bool:
    """Download the real Stanford Alpaca dataset if missing."""
    existing = _load_json_list(path)
    if existing and not force:
        logger.info("alpaca: present (%d samples), reuse", len(existing))
        return True
    script = os.path.join(SCRIPTS_DIR, "download_daily_data.py")
    if not os.path.exists(script):
        logger.error("alpaca: downloader missing (%s)", script)
        return False
    logger.info("alpaca: real instruction-dialogue dataset missing; downloading ...")
    try:
        proc = subprocess.run(
            [sys.executable, script],
            capture_output=True,
            text=True,
            timeout=900,
        )
        if proc.returncode != 0:
            logger.error("alpaca: download failed (rc=%d): %s", proc.returncode, proc.stderr[-500:])
            return False
        logger.info("alpaca: downloaded -> %s", path)
        return True
    except Exception as exc:  # noqa: BLE001 - network/timer failures handled
        logger.error("alpaca: download skipped: %s", exc)
        return False


def ensure_corpus() -> bool:
    """Resume-download the multilingual wiki/tatoeba corpus (optional, heavy)."""
    script = os.path.join(SCRIPTS_DIR, "download_corpus.py")
    if not os.path.exists(script):
        logger.warning("corpus: downloader missing; skipping")
        return False
    logger.info("corpus: resuming multilingual corpus download (resumable)...")
    try:
        proc = subprocess.run(
            [sys.executable, script],
            capture_output=True,
            text=True,
            timeout=1800,
        )
        if proc.returncode != 0:
            logger.warning("corpus: download failed; continuing without it")
            return False
        return True
    except Exception as exc:  # noqa: BLE001 - non-fatal
        logger.warning("corpus: download skipped: %s", exc)
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="print the plan, change nothing")
    parser.add_argument(
        "--force", action="store_true", help="re-generate/re-download existing files"
    )
    parser.add_argument(
        "--with-corpus", action="store_true", help="also resume wiki/tatoeba corpus"
    )
    args = parser.parse_args()

    profile = detect_profile()
    mem_cap = memory_cap_bytes()
    avg_lens = measure_avg_lens()
    plan = decide_plan(profile, mem_cap, with_corpus=args.with_corpus, avg_lens=avg_lens)

    logger.info("Hardware profile: %s -> tier %s", profile, plan["tier"])
    logger.info("Memory cap: %.1f MiB", mem_cap / 1024 / 1024)
    logger.info(
        "Avg sample length (UTF-8 bytes): %s", {k: round(v, 1) for k, v in avg_lens.items() if v}
    )
    logger.info("Plan: %s", json.dumps(plan["caps"], ensure_ascii=False))
    logger.info("Rationale: %s", json.dumps(plan["rationale"], ensure_ascii=False))

    if args.dry_run:
        logger.info("Dry-run: no changes made.")
        return 0

    ok = True
    ok &= ensure_arithmetic(ARITHMETIC_PATH, plan["caps"]["arithmetic"], force=args.force)
    ok &= ensure_logic(LOGIC_PATH, plan["caps"]["logic"], force=args.force)
    ok &= ensure_alpaca(ALPACA_PATH, force=args.force)
    if plan["corpus"]:
        ensure_corpus()

    # Write manifest (even on partial failure so training knows what exists).
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    manifest = dict(plan)
    manifest.update(
        {
            "avg_lens": avg_lens,
            "arithmetic_present": os.path.exists(ARITHMETIC_PATH),
            "logic_present": os.path.exists(LOGIC_PATH),
            "alpaca_present": os.path.exists(ALPACA_PATH),
            "updated": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    )
    with open(MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    logger.info("Manifest written: %s", MANIFEST)

    if not ok:
        logger.error("Some datasets could not be ensured; training may be partial.")
        return 1
    logger.info("All three-axis datasets ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
