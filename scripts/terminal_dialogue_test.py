"""Terminal dialogue smoke test for the ED3N/GARDEN reasoning pipeline.

Runs real conversational turns through ED3NEngine.process() (the same path the
chat service uses for neural/reflex/knowledge/relational-chain stages) plus the
deterministic knowledge engine. Verifies end-to-end behavior from the terminal.
"""
import asyncio
import sys

sys.path.insert(0, "apps/backend/src")

from ai.ed3n.ed3n_engine import ED3NEngine
from ai.knowledge_base import route_knowledge


async def main() -> None:
    engine = ED3NEngine.get_shared()
    engine.load_presets()
    print("=" * 70)
    print("ED3N TERMINAL DIALOGUE TEST")
    print("=" * 70)

    turns = [
        "what color is the sky",                       # knowledge: sky->blue
        "what is the red planet",                      # knowledge: mars
        "who is taller, a or c",                        # relational chain A>B>C
        "if a is taller than b and b is taller than c, who is tallest",  # paraphrase
        "hello",                                        # reflex
        "2 + 2",                                        # math engine
        "what is the meaning of life",                  # open-domain -> fallback
    ]

    for t in turns:
        out = engine.process(t, depth="auto")
        print(f"\nUSER> {t}")
        print(f"ED3N> {out!r}")

    print("\n" + "=" * 70)
    print("DETERMINISTIC KNOWLEDGE ENGINE (direct)")
    print("=" * 70)
    for q in ["what sound does a cat make", "what day comes after monday", "what is the opposite of hot", "month after march", "next tuesday"]:
        r = route_knowledge(q)
        print(f"\nQ> {q}")
        print(f"KB> {r!r}")


if __name__ == "__main__":
    asyncio.run(main())
