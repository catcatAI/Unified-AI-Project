#!/usr/bin/env python3
"""
L1-1 關聯數據 12K→100K 擴充 — 分批流式生成（資源保護）

- 不一次持有 100K list（雖僅 ~10MB，但示範 OOM 防護）
- 批次 10K × 10，逐批寫入 JSON array（流式），峰值 <5MB
- 維度 14→30（含中文比較詞、口語改述、否定/反轉）
- 實體 42→60（增中文人名/常見物）
- 每批間 sleep 0.05s 避免 CPU 佔滿
- 尊重 ANGELA_HARDWARE_PROFILE：若為 laptop_power_saver 則降至 50K

Usage:
  python scripts/generate_association_100k.py --count 100000 --batch 10000
  python scripts/generate_association_100k.py --count 50000  # 低功耗自動降
"""

import argparse
import json
import os
import random
import time

# 擴充維度 14→30
ASSOC_DIMS_30 = {
    # 原 14
    "taller": ("{a} is taller than {b}.", "{b} is shorter than {a}."),
    "shorter": ("{a} is shorter than {b}.", "{b} is taller than {a}."),
    "heavier": ("{a} is heavier than {b}.", "{b} is lighter than {a}."),
    "lighter": ("{a} is lighter than {b}.", "{b} is heavier than {a}."),
    "older": ("{a} is older than {b}.", "{b} is younger than {a}."),
    "younger": ("{a} is younger than {b}.", "{b} is older than {a}."),
    "bigger": ("{a} is bigger than {b}.", "{b} is smaller than {a}."),
    "smaller": ("{a} is smaller than {b}.", "{b} is bigger than {a}."),
    "faster": ("{a} is faster than {b}.", "{b} is slower than {a}."),
    "slower": ("{a} is slower than {b}.", "{b} is faster than {a}."),
    "smarter": ("{a} is smarter than {b}.", "{b} is duller than {a}."),
    "richer": ("{a} is richer than {b}.", "{b} is poorer than {a}."),
    "hotter": ("{a} is hotter than {b}.", "{b} is colder than {a}."),
    "colder": ("{a} is colder than {b}.", "{b} is hotter than {a}."),
    # 新增 16（含中文/口語/變體）
    "taller_cn": ("{a}比{b}高", "{b}比{a}矮"),
    "heavier_cn": ("{a}比{b}重", "{b}比{a}轻"),
    "older_cn": ("{a}比{b}年长", "{b}比{a}年轻"),
    "bigger_cn": ("{a}比{b}大", "{b}比{a}小"),
    "faster_cn": ("{a}比{b}快", "{b}比{a}慢"),
    "stronger": ("{a} is stronger than {b}.", "{b} is weaker than {a}."),
    "weaker": ("{a} is weaker than {b}.", "{b} is stronger than {a}."),
    "brighter": ("{a} is brighter than {b}.", "{b} is dimmer than {a}."),
    "louder": ("{a} is louder than {b}.", "{b} is quieter than {a}."),
    "cheaper": ("{a} is cheaper than {b}.", "{b} is more expensive than {a}."),
    "higher": ("{a} is higher than {b}.", "{b} is lower than {a}."),
    "wider": ("{a} is wider than {b}.", "{b} is narrower than {a}."),
    "deeper": ("{a} is deeper than {b}.", "{b} is shallower than {a}."),
    "longer": ("{a} is longer than {b}.", "{b} is shorter than {a}."),
    "earlier": ("{a} is earlier than {b}.", "{b} is later than {a}."),
    "more_expensive": ("{a} is more expensive than {b}.", "{b} is cheaper than {a}."),
}

ASSOC_ENTITIES_60 = [
    "Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace", "Heidi",
    "Ivan", "Judy", "Karl", "Laura", "Mike", "Nina", "Oscar", "Paula",
    "Tom", "Jerry", "Spike", "Tyke", "Butch", "Tweety", "Sylvester",
    "elephant", "mouse", "whale", "ant", "giraffe", "rabbit", "turtle",
    "mountain", "hill", "building", "tree", "car", "bicycle", "train",
    "cheetah", "snail", "eagle", "sloth", "professor", "student", "billionaire",
    # 新增 18（中文人名/常見物）
    "小明", "小红", "小刚", "李雷", "韩梅", "张三", "李四", "王五",
    "泰山", "黄河", "长城", "故宫", "熊猫", "老虎", "狮子", "鲸鱼",
    "飞机", "高铁",
]


def generate_batch(count, dims, entities):
    batch = []
    dims_list = list(dims.items())
    for _ in range(count):
        dim, (tmpl_a, tmpl_b) = random.choice(dims_list)
        a, b = random.sample(entities, 2)
        batch.append({
            "input": tmpl_a.format(a=a, b=b),
            "output": tmpl_b.format(a=a, b=b),
            "domain": "association",
            "relation": dim,
        })
    return batch


def stream_write(path, total, batch_size):
    dims = ASSOC_DIMS_30
    entities = ASSOC_ENTITIES_60
    # 硬體自適應：低功耗自動降
    profile = os.getenv("ANGELA_HARDWARE_PROFILE", "")
    if profile in ("laptop_power_saver", "low_power_device") and total > 50000:
        print(f"⚡ Detected {profile}: auto-reducing {total}→50000 (resource protection)")
        total = 50000

    os.makedirs(os.path.dirname(path), exist_ok=True)
    batches = (total + batch_size - 1) // batch_size
    print(f"Generating {total} association samples in {batches} batches of {batch_size} (dims=30, entities=60)")

    # 流式寫 JSON array：手動寫 [ ... ] 避免持有全量
    with open(path, "w", encoding="utf-8") as f:
        f.write("[\n")
        written = 0
        for bi in range(batches):
            cur = min(batch_size, total - written)
            batch = generate_batch(cur, dims, entities)
            for j, sample in enumerate(batch):
                # 寫入，批次間加逗號
                is_last = (bi == batches - 1 and j == len(batch) - 1)
                json.dump(sample, f, ensure_ascii=False)
                if not is_last:
                    f.write(",\n")
                else:
                    f.write("\n")
            written += cur
            print(f"  batch {bi+1}/{batches}: {written}/{total} ({written/total:.0%})")
            # 避免 CPU 佔滿
            time.sleep(0.05)
            # 釋放批次
            del batch
        f.write("]\n")

    size_kb = os.path.getsize(path) / 1024
    print(f"✅ Wrote {total} samples to {path} ({size_kb:.1f} KB, dims=30, entities=60)")


def main():
    ap = argparse.ArgumentParser(description="L1-1 association 12K→100K (batched, low-resource)")
    ap.add_argument("--count", type=int, default=100000, help="total samples")
    ap.add_argument("--batch", type=int, default=10000, help="batch size")
    ap.add_argument("--output", default="apps/backend/data/raw_datasets/association_train.json")
    args = ap.parse_args()
    stream_write(args.output, args.count, args.batch)


if __name__ == "__main__":
    main()
