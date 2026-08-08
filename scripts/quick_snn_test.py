"""Quick SNN-ONLY test after retraining with fixed encode."""
import time
import sys
import numpy as np

sys.path.insert(0, "D:\\Projects\\Unified-AI-Project\\apps\\backend\\src")

from ai.garden.garden_engine import GARDENEngine


def main():
    t0 = time.time()
    g = GARDENEngine(compatibility_mode=True)
    g.load("D:\\Projects\\Unified-AI-Project\\data\\checkpoints\\garden_checkpoint")
    snn = g.snn
    stats = snn.get_stats()
    print(f"GARDEN loaded in {time.time()-t0:.1f}s")
    print(f"Dict: {len(g.dictionary.entries)} entries")
    print(f"SNN: V={snn.vocab_size}, density={stats.get('density', 0)*100:.2f}%, "
          f"total_steps={stats.get('total_steps', 0)}, hebbian_updates={stats.get('total_hebbian_updates', 0)}")

    test_cases = [
        "2+3=5",
        "10-3=7",
        "4*5=20",
        "true OR false",
        "NOT false",
        "hello",
        "你好",
    ]

    for query in test_cases:
        t1 = time.time()
        keys = g.dictionary.encode(query)
        idx = [g.dictionary.key_to_index[k] for k in keys if k in g.dictionary.key_to_index]
        if idx:
            out = snn.forward(np.array(idx))
            active_idx = np.where(out > 0.3)[0]
            snn_keys = [g.dictionary.index_to_key.get(i, "?") for i in active_idx]
            words = []
            for k in snn_keys[:10]:
                if k in g.dictionary.entries:
                    for form in g.dictionary.entries[k].surface_forms.values():
                        if form:
                            words.append(form.split()[0])
                            break
            print(f"[{query:20s}] encode={str(keys[:6]):50s} snn_active={len(active_idx):4d} snn_out={' '.join(words[:8])}")
        else:
            print(f"[{query:20s}] encode={keys} -> no indices")
        print(f"  ({time.time()-t1:.3f}s)")

    # HYBRID test
    print("\n--- HYBRID (dict->deterministic->snn) ---")
    for query in ["2+3=5", "true OR false", "hello"]:
        result = g.query(query)
        print(f"[{query:20s}] -> {result}")


if __name__ == "__main__":
    main()
