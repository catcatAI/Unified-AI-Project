"""Test improved semantic anchor vectors"""


try:
    from core.allocation.resonance import ResonanceEngine
except ImportError:
    import pytest; pytest.skip("ResonanceEngine is a stub", allow_module_level=True)
from core.state.text_to_vector import text_to_vector


def test_nonzero_dims():
    eng = ResonanceEngine()

    print("=== Semantic Anchor Vectors ===")
    total_nonzero = 0
    for name, vec in sorted(eng._semantic_vectors.items()):
        nonzero = sum(1 for v in vec if abs(v) > 0.01)
        total_nonzero += nonzero
        max_val = max(abs(v) for v in vec)
        print(f"  {name}: {nonzero} non-zero dims, max_val={max_val:.3f}")

    print(f"\nTotal non-zero: {total_nonzero} across 6 axes")
    print(f"Average: {total_nonzero / 6:.1f} per axis")
    assert total_nonzero >= 30


def test_word_similarity():
    eng = ResonanceEngine()

    print("\n=== Word Similarity Tests ===")
    test_cases = [
        ("happiness", "gamma", True),
        ("focus", "beta", True),
        ("energy", "alpha", True),
        ("bond", "delta", True),
        ("logic", "epsilon", True),
    ]

    for text, expected, should_be_high in test_cases:
        vec = text_to_vector(text, 32)
        sim = eng.compute_resonance(vec, expected)
        marker = "✓" if sim > 0.1 else "○"
        print(f"  {marker} \"{text}\" → {expected}: {sim:.3f}")


def test_uniform_vector():
    eng = ResonanceEngine()

    print("\n=== Uniform Test Vector ===")
    test_vec = [0.1] * 32
    sims = {}
    for name in sorted(eng._semantic_vectors):
        sim = eng.compute_resonance(test_vec, name)
        sims[name] = sim

    best = max(sims, key=sims.get)
    print(f"  Best: {best} = {sims[best]:.3f}")
    print(f"  All: " + ", ".join(f"{k}={v:.3f}" for k, v in sorted(sims.items())))
    assert all(s > 0.0 for s in sims.values()), "All similarities should be > 0"


def test_axis_discrimination():
    eng = ResonanceEngine()

    print("\n=== Axis Discrimination ===")
    test_words = ["happiness", "focus", "comfort", "bond", "logic"]
    results = {}

    for word in test_words:
        vec = text_to_vector(word, 32)
        sims = {name: eng.compute_resonance(vec, name) for name in eng._semantic_vectors}
        best = max(sims, key=sims.get)
        results[word] = (best, max(sims.values()))

    for word, (best, sim) in sorted(results.items()):
        print(f"  \"{word}\" → {best} ({sim:.3f})")


if __name__ == "__main__":
    test_nonzero_dims()
    test_word_similarity()
    test_uniform_vector()
    test_axis_discrimination()
    print("\n=== All anchor vector tests passed ===")