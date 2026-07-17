"""Interactive terminal dialogue against the TRAINED ED3N + GARDEN checkpoints.

Loads the trained weights (ed3n_full.json / garden_checkpoint) WITHOUT resetting
to presets, so this exercises exactly what train_pipeline.py produced.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))

from ai.ed3n.ed3n_engine import ED3NEngine
from ai.garden.garden_engine import GARDENEngine
from ai.knowledge_base import route_knowledge

CKPT = os.path.join(os.path.dirname(__file__), "..", "data", "checkpoints")
ED3N_CK = os.path.join(CKPT, "ed3n_full.json")
GARDEN_CK = os.path.join(CKPT, "garden_checkpoint")


def build_engine():
    e = ED3NEngine()
    if os.path.isfile(ED3N_CK):
        e.load(ED3N_CK)
        print(f"[ED3N] loaded TRAINED checkpoint: dict={len(e.dictionary.entries)} "
              f"reflex={len(e.reflex.patterns)} conns={e.network._conn_count}")
    else:
        e.load_presets()
        print("[ED3N] WARNING: trained checkpoint missing, loaded PRESETS only")
    return e


def build_garden():
    g = GARDENEngine(compatibility_mode=True)
    if os.path.isdir(GARDEN_CK):
        g.load(GARDEN_CK)
        print(f"[GARDEN] loaded TRAINED checkpoint: dict={len(g.dictionary.entries)} "
              f"snn_vocab={g.snn.vocab_size}")
    else:
        g.load_presets()
        print("[GARDEN] WARNING: trained checkpoint missing, loaded PRESETS only")
    return g


def main() -> None:
    ed3n = build_engine()
    garden = build_garden()
    print("=" * 70)
    print("TRAINED MODEL TERMINAL DIALOGUE  (type 'quit' to exit)")
    print("=" * 70)

    while True:
        try:
            u = input("\nYOU> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye")
            break
        if not u:
            continue
        if u.lower() in ("quit", "exit", "q"):
            break

        # 1) ED3N neural/reflex/knowledge/relational path
        try:
            ed3n_out = ed3n.process(u, depth="auto")
        except Exception as ex:
            ed3n_out = f"<ed3n error: {ex}>"

        # 2) GARDEN knowledge/query path
        try:
            g_out = garden.process(u)
        except Exception as ex:
            g_out = f"<garden error: {ex}>"

        # 3) deterministic KB path
        try:
            kb_out = route_knowledge(u)
        except Exception as ex:
            kb_out = f"<kb error: {ex}>"

        print(f"ED3N>  {ed3n_out!r}")
        print(f"GARDEN> {g_out!r}")
        print(f"KB>     {kb_out!r}")


if __name__ == "__main__":
    main()
