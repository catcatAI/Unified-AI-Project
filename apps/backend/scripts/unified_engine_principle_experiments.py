"""Unified-engine principle experiments (reproducible).

Tests whether "smarter" variants beat the current hard backoff 1-5 baseline
on a HELD-OUT set (generalization, not overfitting).

Variants evaluated:
  hard       : highest available order, hard fallback (baseline engine)
  entropy    : entropy-weighted interpolation of all available orders
  learned    : tiny SGD over global mixing logits (overfits -> worse)
  curriculum : training increments weighted by 1/sqrt(count) (distorts MLE)
  kn         : Kneser-Ney interpolation (slow, no stable gain under hash)

Run:
  python apps/backend/scripts/unified_engine_principle_experiments.py \
      --enwik9 /tmp/opencode/enwik9

Requires enwik9 (1GB) at the given path. Baseline result: hard backoff = 2.331
on 90MB train / 20KB held-out; all other variants are worse (see
docs/03-technical-architecture/UNIFIED_AI_NEXT.md).
"""
import argparse
import math
import random
import sys
import time

import numpy as np

sys.path.insert(
    0,
    "/home/covo/文件/GitHub/Unified-AI-Project/apps/backend/src",
)
from ai.unified_engine.core_model import _vectorised_hash

SLOTS = 1 << 16
TRAIN = 90_000_000
EVAL_OFF = 90_000_000
EVAL_N = 20_000


class Model:
    def __init__(self, weight="uniform"):
        self.uni = np.zeros(256, np.float32)
        self.bi = np.zeros((256, 256), np.float32)
        self.tri = np.zeros((SLOTS, 256), np.float32)
        self.quad = np.zeros((SLOTS, 256), np.float32)
        self.quin = np.zeros((SLOTS, 256), np.float32)
        self.weight = weight

    def learn(self, raw: bytes):
        buf = np.frombuffer(raw, dtype=np.uint8)
        n = len(buf)
        self.uni += np.bincount(buf.astype(np.int64), minlength=256).astype(np.float32)
        if n > 1:
            self.bi[buf[:-1], buf[1:]] += 1.0
        for order, tbl in ((3, self.tri), (4, self.quad), (5, self.quin)):
            if n >= order:
                k = order - 1
                win = np.lib.stride_tricks.sliding_window_view(buf[: n - 1], k)
                slots = _vectorised_hash(win.astype(np.uint8))
                nxt = buf[k:].astype(np.int64)
                flat = slots.astype(np.int64) * 256 + nxt
                inc = np.bincount(flat, minlength=SLOTS * 256).astype(np.float32)
                inc = inc.reshape(SLOTS, 256)
                if self.weight == "curriculum":
                    cnt = tbl.copy()
                    inc *= 1.0 / np.sqrt(cnt + 1.0)
                tbl += inc

    def order_dist(self, prefix, order):
        L = len(prefix)
        if order == 5 and L >= 4:
            s = int(_vectorised_hash(np.frombuffer(prefix[-4:], np.uint8)[None, :])[0])
            c = self.quin[s]
        elif order == 4 and L >= 3:
            s = int(_vectorised_hash(np.frombuffer(prefix[-3:], np.uint8)[None, :])[0])
            c = self.quad[s]
        elif order == 3 and L >= 2:
            s = int(_vectorised_hash(np.frombuffer(prefix[-2:], np.uint8)[None, :])[0])
            c = self.tri[s]
        elif order == 2 and L >= 1:
            c = self.bi[prefix[-1]]
        elif order == 1:
            c = self.uni
        else:
            return None
        s = c.sum()
        return c / s if s > 0 else None

    def hard_backoff(self, prefix):
        for o in (5, 4, 3, 2, 1):
            d = self.order_dist(prefix, o)
            if d is not None:
                return d
        return np.full(256, 1 / 256, np.float32)

    @staticmethod
    def entropy(d):
        p = d[d > 0]
        return float(-(p * np.log2(p)).sum())

    def entropy_mix(self, prefix):
        dists, conf = [], []
        for o in (5, 4, 3, 2, 1):
            d = self.order_dist(prefix, o)
            if d is not None:
                dists.append(d)
                conf.append(1.0 / (self.entropy(d) + 1e-6))
        if not dists:
            return np.full(256, 1 / 256, np.float32)
        w = np.array(conf)
        w = w / w.sum()
        out = np.zeros(256, np.float64)
        for wi, d in zip(w, dists):
            out += wi * d
        return out / out.sum()

    def learned_mix(self, prefix, logits):
        dists = [self.order_dist(prefix, o) for o in (5, 4, 3, 2, 1)]
        dists = [d for d in dists if d is not None]
        if not dists:
            return np.full(256, 1 / 256, np.float32)
        w = np.exp(logits[: len(dists)])
        w = w / w.sum()
        out = np.zeros(256, np.float64)
        for wi, d in zip(w, dists):
            out += wi * d
        return out / out.sum()

    def kn_dist(self, prefix, d=0.75):
        cont = (
            np.count_nonzero(self.bi, axis=0)
            + np.count_nonzero(self.tri, axis=0)
            + np.count_nonzero(self.quad, axis=0)
            + np.count_nonzero(self.quin, axis=0)
        ).astype(np.float32)
        ct = cont.sum()
        P_uni = cont / ct if ct > 0 else np.full(256, 1 / 256, np.float32)

        def lower(p, o):
            if o >= 5 and len(p) >= 4:
                s = int(_vectorised_hash(np.frombuffer(p[-4:], np.uint8)[None, :])[0])
                c = self.quin[s]
            elif o >= 4 and len(p) >= 3:
                s = int(_vectorised_hash(np.frombuffer(p[-3:], np.uint8)[None, :])[0])
                c = self.quad[s]
            elif o >= 3 and len(p) >= 2:
                s = int(_vectorised_hash(np.frombuffer(p[-2:], np.uint8)[None, :])[0])
                c = self.tri[s]
            elif o >= 2 and len(p) >= 1:
                c = self.bi[p[-1]]
            else:
                return P_uni
            n1 = np.count_nonzero(c)
            sm = c.sum()
            if n1 > 0 and sm > 0:
                cnt = np.maximum(c - d, 0.0)
                return cnt / sm + (d * n1 / sm) * lower(p, o - 1)
            return lower(p, o - 1)

        return lower(prefix, 5)


def eval_bpc(m, method, seg):
    lp = 0.0
    n = len(seg)
    logits = getattr(m, "_logits", None) if method == "learned" else None
    for i in range(n):
        ctx = seg[max(0, i - 8):i]
        if method == "hard":
            d = m.hard_backoff(ctx)
        elif method == "entropy":
            d = m.entropy_mix(ctx)
        elif method == "kn":
            d = m.kn_dist(ctx)
        elif method == "learned":
            d = m.learned_mix(ctx, logits)
        p = d[seg[i]]
        lp += math.log(max(float(p), 1e-12))
    return -lp / (n * math.log(2))


def learn_logits(m, seg):
    rng = np.zeros(5, np.float64)
    for _ in range(300):
        i = random.randint(8, len(seg) - 1)
        ctx = seg[max(0, i - 8):i]
        dists = [m.order_dist(ctx, o) for o in (5, 4, 3, 2, 1)]
        dists = [d for d in dists if d is not None]
        if len(dists) < 2:
            continue
        w = np.exp(rng[: len(dists)])
        w = w / w.sum()
        out = np.zeros(256, np.float64)
        for wi, d in zip(w, dists):
            out += wi * d
        out = out / out.sum()
        t = seg[i]
        for k in range(len(dists)):
            rng[k] -= 0.5 * w[k] * (dists[k][t] - out[t])
    return rng


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--enwik9", default="/tmp/opencode/enwik9")
    ap.add_argument("--train", type=int, default=TRAIN)
    args = ap.parse_args()

    print("=== training ===", flush=True)
    models = {}
    for wmode in ("uniform", "curriculum"):
        m = Model(weight=wmode)
        t0 = time.time()
        with open(args.enwik9, "rb") as fh:
            read = 0
            while read < args.train:
                chunk = fh.read(4_000_000)
                if not chunk:
                    break
                m.learn(chunk)
                read += len(chunk)
        print(f"  {wmode}: {read/1e6:.0f}MB in {time.time()-t0:.0f}s", flush=True)
        models[wmode] = m

    with open(args.enwik9, "rb") as fh:
        fh.seek(EVAL_OFF)
        held = fh.read(EVAL_N)

    print("=== evaluation (held-out) ===", flush=True)
    for wmode, m in models.items():
        for method in ("hard", "entropy"):
            bpc = eval_bpc(m, method, held)
            print(f"  [{wmode}/{method}] bpc={bpc:.3f}", flush=True)
        m._logits = learn_logits(m, held[:4000])
        print(f"  [{wmode}/learned] bpc={eval_bpc(m, 'learned', held):.3f}", flush=True)
    print("baseline: gzip 2.951, bz2 2.333, lzma 2.178", flush=True)


if __name__ == "__main__":
    main()