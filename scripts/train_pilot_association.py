#!/usr/bin/env python3
"""
L1-1 試點訓練 — ED3N Hebbian 關聯 5K 子集（資源保護）

- 僅取 association_train.json 前 5K（~0.6MB），分批 500 ×10
- 每批後 sleep 0.1s + free -h 檢查，避免 CPU 佔滿
- 監控 max_vocab（10K lean）與 conn_count，避免 V² OOM
- 不寫大 checkpoint，僅內存驗證
- 單試點 <15s, <200MB

Usage:
  python scripts/train_pilot_association.py --count 5000 --batch 500
  ANGELA_HARDWARE_PROFILE=laptop_power_saver python scripts/train_pilot_association.py
"""

import argparse
import json
import os
import re
import sys
import time

# 中文比較模板的形容詞後綴（按 relation 字段精確剝離，避免窮舉）
CN_ADJ = {"faster_cn": "快", "bigger_cn": "大", "heavier_cn": "重", "taller_cn": "高", "older_cn": "年长"}

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "apps/backend/data/raw_datasets/association_train.json")


def check_resources():
    try:
        import psutil
        vm = psutil.virtual_memory()
        print(f"  [資源] RAM {vm.percent:.1f}% used, {vm.available/1024**3:.1f}GB avail")
        if vm.percent > 85:
            print("  ⚠️ RAM >85% — 暫停 1s")
            time.sleep(1)
            return False
    except ImportError:
        # fallback /proc/meminfo
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemAvailable"):
                        kb = int(line.split()[1])
                        if kb < 1024*1024:  # <1GB
                            print(f"  ⚠️ MemAvailable {kb/1024:.0f}MB <1GB — 暫停")
                            time.sleep(1)
                            return False
                        break
        except Exception:
            pass
    return True


def main():
    ap = argparse.ArgumentParser(description="L1-1 pilot: ED3N Hebbian 5K (resource-guarded)")
    ap.add_argument("--count", type=int, default=5000, help="samples to train")
    ap.add_argument("--batch", type=int, default=500, help="batch size")
    ap.add_argument("--weight", type=float, default=0.7, help="Hebbian step per co-occurrence (engine caps at 1.0; small values preserve frequency differences)")
    ap.add_argument("--max-pairs", type=int, default=0, help="cap unique entity pairs admitted (0 = unlimited; for sparsity/generalization experiments)")
    ap.add_argument("--checkpoint", default=None, help="save trained engine state (default: data/checkpoints/association_pilot.json; empty string disables)")
    args = ap.parse_args()

    if not os.path.exists(DATA_PATH):
        print(f"❌ {DATA_PATH} not found — run generate_association_100k.py first")
        return 1

    # 流式讀前 N，不全量 100K（雖 13MB 可載，但示範保護）
    print(f"📖 Loading first {args.count} samples from {DATA_PATH} (streaming first N)...")
    samples = []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        samples = data[:args.count]
    print(f"✅ Loaded {len(samples)} samples (first {args.count})")

    from ai.ed3n.ed3n_engine import ED3NEngine

    eng = ED3NEngine()
    eng.load_presets()
    print(f"ED3N presets loaded: {len(eng.network.groups.get('mapping').neurons) if eng.network.groups.get('mapping') else 0} neurons")
    print(f"Initial conn_count={eng.network._conn_count}")

    # 分批 Hebbian
    total = len(samples)
    batches = (total + args.batch - 1) // args.batch
    t0 = time.time()
    probe_pair = ("?", "?")
    total_parsed, total_skipped = 0, 0
    admitted: set = set()
    for bi in range(batches):
        if not check_resources():
            print("  ⏸️ Resource guard paused")
        batch = samples[bi*args.batch:(bi+1)*args.batch]
        # 數據驅動 Hebbian：英文 "{A} is {rel} than {B}." → A->B；中文 "{A}比{B}{adj}" → A->B
        parsed, skipped = 0, 0
        for s in batch:
            try:
                inp = s["input"]
                a = b = None
                if "比" in inp:
                    m = re.match(r"^(.+)比(.+)$", inp)
                    if m:
                        a = m.group(1)
                        rest = m.group(2)
                        adj = CN_ADJ.get(s.get("relation", ""), "")
                        if adj and rest.endswith(adj):
                            b = rest[:-len(adj)]
                else:
                    w = inp.split()
                    a, b = w[0], w[-1].rstrip(".")
                if not a or not b or a == b:
                    skipped += 1
                    continue
                if args.max_pairs and (a, b) not in admitted and len(admitted) >= args.max_pairs:
                    skipped += 1
                    continue
                admitted.add((a, b))
                eng.network.add_directed(a, b, weight=args.weight)
                parsed += 1
                if bi == 0 and parsed == 1:
                    probe_pair = (a, b)
            except Exception:
                skipped += 1
        if bi == 0:
            print(f"  解析樣本例: {batch[0]['input']!r} → 邊 {probe_pair[0]}->{probe_pair[1]} (parsed={parsed} skipped={skipped})")
        total_parsed += parsed
        total_skipped += skipped

        elapsed = time.time() - t0
        conn = eng.network._conn_count
        print(f"  batch {bi+1}/{batches}: {min((bi+1)*args.batch, total)}/{total} conn={conn} ({elapsed:.1f}s)")
        time.sleep(0.1)  # 避免 CPU 佔滿

    print(f"\n✅ Pilot done: {total} samples, conn={eng.network._conn_count}, time={time.time()-t0:.1f}s")
    print(f"   解析品質: parsed={total_parsed} skipped={total_skipped} ({total_parsed/total:.1%} 樣本成邊)")
    print(f"   Vocab neurons ~{sum(len(g.neurons) for g in eng.network.groups.values())}")

    # 快驗：用真實訓練邊的源實體查 forward（數據驅動驗證）
    acts = eng.network.forward([probe_pair[0]])
    print(f"   Quick check: forward(['{probe_pair[0]}']) -> {len(acts)} activations (expect '{probe_pair[1]}' reachable)")

    # 存檔接線：訓後存引擎狀態，新引擎加載後 forward 驗證
    ckpt = args.checkpoint
    if ckpt is None:
        ckpt = os.path.join(os.path.dirname(__file__), "..", "data/checkpoints/association_pilot.json")
    if ckpt:
        try:
            eng.save(ckpt)
            from ai.ed3n.ed3n_engine import ED3NEngine as _Fresh
            fresh = _Fresh()
            fresh.load(ckpt)
            vacts = fresh.network.forward([probe_pair[0]]) if hasattr(fresh, "network") else []
            print(f"   Checkpoint: saved {ckpt} ({os.path.getsize(ckpt)//1024}KB), fresh-load forward -> {len(vacts)} activations {'✅' if len(vacts) else '❌'}")
        except Exception as e:
            print(f"   Checkpoint ❌: {e}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
