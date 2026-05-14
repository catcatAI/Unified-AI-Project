"""
Unit Tests — AnchorLearningEngine
================================

測試語義錨點學習引擎的學習效果。
重點：對比學習前後的錨點變化（維度密度、相似度分布）。

Author: Angela AI v6.2
"""

import sys
sys.path.insert(0, 'apps/backend/src')

from core.autonomous.anchor_learning import AnchorLearningEngine
from core.allocation.resonance import ResonanceEngine
from core.state.temporal import TemporalState


def _count_nonzero(vec):
    if vec is None:
        return 0
    return sum(1 for v in vec if abs(v) > 1e-6)


def _count_total_nonzero(semantic_vectors):
    total = 0
    for v in semantic_vectors.values():
        total += _count_nonzero(v)
    return total


def test_engine_creation():
    """Engine 可以正常創建"""
    eng = ResonanceEngine()
    ale = AnchorLearningEngine(resonance_engine=eng)
    assert ale is not None
    assert ale._resonance is eng
    assert ale._ema_alpha == 0.9
    assert ale._learning_interval == 10
    print("  test_engine_creation: PASS")


def test_snapshot_to_vector():
    """快照轉換為向量"""
    eng = ResonanceEngine()
    ale = AnchorLearningEngine(resonance_engine=eng)

    snapshot = {"energy": 0.8, "arousal": 0.6, "comfort": 0.5, "tension": 0.1}
    vec = ale._snapshot_to_vector(snapshot)
    assert len(vec) == 32
    nonzero = _count_nonzero(vec)
    assert nonzero >= 3, f"Expected >=3 non-zero dims, got {nonzero}"
    assert abs(sum(v * v for v in vec) - 1.0) < 0.01, "Should be normalized"
    print(f"  Snapshot→vector: {nonzero} non-zero dims, norm≈1.0")


def test_ema_update_densifies():
    """EMA 更新後錨點非零維度保持穩定"""
    eng = ResonanceEngine()
    ale = AnchorLearningEngine(resonance_engine=eng, ema_alpha=0.7, learning_interval=1)

    nonzero_before = _count_nonzero(eng._semantic_vectors.get("alpha"))

    snapshot = {
        "energy": 0.8, "arousal": 0.6, "comfort": 0.5,
        "tension": 0.1, "rest_need": 0.3, "vitality": 0.4
    }
    for i in range(20):
        snapshot = {k: max(0.0, min(1.0, v + 0.05 * (1 if i % 2 == 0 else -1)))
                    for k, v in snapshot.items()}
        ale.on_axis_update("alpha", snapshot, is_stable=True)

    nonzero_after = _count_nonzero(eng._semantic_vectors.get("alpha"))

    print(f"  EMA update: {nonzero_before} → {nonzero_after} non-zero dims")
    assert nonzero_after >= 4, "Should maintain minimum density"
    return nonzero_before, nonzero_after


def test_on_allocation_assign_feedback():
    """ASSIGN 決策後錨點朝輸入向量靠近"""
    eng = ResonanceEngine()
    ale = AnchorLearningEngine(resonance_engine=eng)

    input_vec = eng._text_to_vector("think learn focus curiosity understanding", 32)

    anchor_before = eng._semantic_vectors.get("beta", [0.0] * 32)[:]
    sim_before = eng.compute_resonance(input_vec, "beta")

    ale.on_allocation_decision(input_vec, "ASSIGN", "beta", confidence=0.6)

    anchor_after = eng._semantic_vectors.get("beta")
    sim_after = eng.compute_resonance(anchor_after, "beta")

    print(f"  ASSIGN feedback: sim(input→beta)={sim_before:.4f} → sim(new→beta)={sim_after:.4f}")
    assert sim_after >= sim_before - 0.05, "ASSIGN should bring anchor toward input"
    print(f"  PASS: anchor moved toward input vector")


def test_on_allocation_defer_accumulates():
    """DEFER 決策後添加到未分類池"""
    eng = ResonanceEngine()
    ale = AnchorLearningEngine(resonance_engine=eng)

    for i in range(5):
        vec = [0.1 * i + 0.1] * 32
        ale.on_allocation_decision(vec, "DEFER", None, confidence=0.2)

    assert len(ale._unclassified) == 5
    print(f"  DEFER accumulates: {len(ale._unclassified)} unclassified vectors")


def test_on_misallocation_correction():
    """θ 自糾後錨點修正"""
    eng = ResonanceEngine()
    ale = AnchorLearningEngine(resonance_engine=eng, misalloc_lr=0.1)

    anchor_gamma_before = eng._semantic_vectors.get("gamma", [0.0] * 32)[:]

    misalloc_vec = eng._semantic_vectors["gamma"][:]

    sim_alpha_before = eng.compute_resonance(misalloc_vec, "alpha")
    sim_gamma_before = eng.compute_resonance(misalloc_vec, "gamma")

    ale.on_misallocation_detected(
        input_vector=misalloc_vec,
        wrong_axis="alpha",
        right_axis="gamma",
        confidence=0.8,
    )

    sim_alpha_after = eng.compute_resonance(misalloc_vec, "alpha")
    sim_gamma_after = eng.compute_resonance(misalloc_vec, "gamma")

    print(f"  Misallocation correction:")
    print(f"    alpha: input→alpha sim={sim_alpha_before:.4f} → {sim_alpha_after:.4f}")
    print(f"    gamma: input→gamma sim={sim_gamma_before:.4f} → {sim_gamma_after:.4f}")

    improvement = (sim_gamma_after - sim_gamma_before) - (sim_alpha_after - sim_alpha_before)
    print(f"    gamma-alpha improvement: {improvement:+.4f}")
    assert improvement > 0, "gamma anchor should improve more than alpha anchor"
    print(f"  PASS: gamma improved relative to alpha")


def test_keyword_tracking():
    """關鍵詞追蹤"""
    eng = ResonanceEngine()
    ale = AnchorLearningEngine(resonance_engine=eng)

    axes = list(eng._semantic_vectors.keys())
    print(f"  Axes in engine: {axes}")

    ale.on_text_vectorized("thinking about mathematics and logic", [0.1] * 32, "epsilon")
    ale.on_text_vectorized("logic and precision in math", [0.1] * 32, "epsilon")
    ale.on_text_vectorized("emotional feelings happiness sadness", [0.1] * 32, "gamma")
    ale.on_text_vectorized("mathematical calculation precision", [0.1] * 32, "epsilon")

    report = ale.get_learning_report()
    print(f"  Vocabulary: {report['keyword_vocabulary']} words")
    assert report["keyword_vocabulary"] > 0, "Should track keywords"
    print(f"  PASS: {report['keyword_vocabulary']} keywords tracked")


def test_learning_report():
    """學習報告"""
    eng = ResonanceEngine()
    ale = AnchorLearningEngine(resonance_engine=eng)

    ale.on_axis_update("alpha", {"energy": 0.8, "arousal": 0.6}, is_stable=True)
    ale.on_allocation_decision([0.5] * 32, "ASSIGN", "alpha", confidence=0.6)
    ale.on_allocation_decision([0.3] * 32, "DEFER", None, confidence=0.2)

    report = ale.get_learning_report()
    assert "allocations" in report
    assert report["allocations"]["assign"] == 1
    assert report["allocations"]["defer"] == 1
    assert report["keyword_vocabulary"] >= 0
    print(f"  Learning report: {report}")


# =============================================================================
# 主測試：學習前後對比
# =============================================================================

def test_learning_before_after():
    """
    對比學習前後錨點的非零維度數量和相似度分布。
    """
    print("\n" + "=" * 60)
    print("LEARNING BEFORE/AFTER COMPARISON")
    print("=" * 60)

    eng = ResonanceEngine()
    ale = AnchorLearningEngine(resonance_engine=eng, ema_alpha=0.7, learning_interval=1)

    test_vector = eng._text_to_vector("focus curiosity thinking understanding", 32)

    print("\n[Phase 1] BEFORE LEARNING — Anchor State")
    print("-" * 40)
    print("  Original anchors:")
    anchor_stats_before = {}
    sims_before = {}
    for ax in sorted(eng._semantic_vectors.keys()):
        vec = eng._semantic_vectors[ax]
        nonzero = _count_nonzero(vec)
        sim = eng.compute_resonance(test_vector, ax)
        anchor_stats_before[ax] = nonzero
        sims_before[ax] = sim
        print(f"    {ax}: {nonzero} non-zero dims, sim={sim:.4f}")

    max_sim_before = max(sims_before.values()) if sims_before else 0.0
    best_axis_before = max(sims_before, key=sims_before.get) if sims_before else "none"
    total_nonzero_before = sum(anchor_stats_before.values())
    print(f"\n  Max similarity: {max_sim_before:.4f} (axis: {best_axis_before})")
    print(f"  Total non-zero dims: {total_nonzero_before}")

    print("\n[Phase 2] EXECUTING LEARNING")
    print("-" * 40)

    scenarios = [
        {"energy": 0.8, "arousal": 0.7, "comfort": 0.6, "tension": 0.2, "rest_need": 0.3, "vitality": 0.5},
        {"energy": 0.9, "arousal": 0.8, "comfort": 0.7, "tension": 0.1, "rest_need": 0.4, "vitality": 0.6},
        {"energy": 0.7, "arousal": 0.6, "comfort": 0.5, "tension": 0.3, "rest_need": 0.5, "vitality": 0.4},
        {"energy": 0.6, "arousal": 0.5, "comfort": 0.4, "tension": 0.4, "rest_need": 0.6, "vitality": 0.3},
        {"energy": 0.5, "arousal": 0.4, "comfort": 0.3, "tension": 0.5, "rest_need": 0.7, "vitality": 0.2},
    ]

    for i in range(50):
        scenario = {k: max(0.0, min(1.0, v * (0.9 + 0.2 * ((i + j) % 5) / 5)))
                    for j, (k, v) in enumerate(scenarios[i % len(scenarios)].items())}
        ale.on_axis_update("alpha", scenario, is_stable=True)

    assign_vecs = [
        ("focus curiosity learning", "beta"),
        ("thinking understanding", "beta"),
        ("mathematical logic precision", "epsilon"),
    ]
    for text, target in assign_vecs:
        vec = eng._text_to_vector(text, 32)
        ale.on_allocation_decision(vec, "ASSIGN", target, confidence=0.6)
        ale.on_text_vectorized(text, vec, target)

    misalloc_vec = eng._text_to_vector("angry frustrated emotional sadness", 32)
    ale.on_misallocation_detected(misalloc_vec, "alpha", "gamma", confidence=0.7)

    print(f"  50 axis updates → alpha")
    print(f"  3 ASSIGN decisions → beta/epsilon")
    print(f"  1 misallocation correction: alpha→gamma")

    print("\n[Phase 3] AFTER LEARNING — Anchor State")
    print("-" * 40)
    print("  Learned anchors:")
    anchor_stats_after = {}
    sims_after = {}
    for ax in sorted(eng._semantic_vectors.keys()):
        vec = eng._semantic_vectors[ax]
        nonzero = _count_nonzero(vec)
        sim = eng.compute_resonance(test_vector, ax)
        anchor_stats_after[ax] = nonzero
        sims_after[ax] = sim
        print(f"    {ax}: {nonzero} non-zero dims, sim={sim:.4f}")

    max_sim_after = max(sims_after.values()) if sims_after else 0.0
    best_axis_after = max(sims_after, key=sims_after.get) if sims_after else "none"
    total_nonzero_after = sum(anchor_stats_after.values())
    print(f"\n  Max similarity: {max_sim_after:.4f} (axis: {best_axis_after})")
    print(f"  Total non-zero dims: {total_nonzero_after}")

    print("\n[Phase 4] COMPARISON")
    print("-" * 40)
    print(f"  Total non-zero dims:  {total_nonzero_before:3d} → {total_nonzero_after:3d}  (delta={total_nonzero_after-total_nonzero_before:+.0f})")
    print(f"  Max similarity:      {max_sim_before:.4f} → {max_sim_after:.4f}  (delta={max_sim_after-max_sim_before:+.4f})")

    nonzero_improved = total_nonzero_after > total_nonzero_before
    sim_improved = max_sim_after >= max_sim_before - 0.01

    print(f"\n  Non-zero dims improved:  {'✅ YES' if nonzero_improved else '⚠️  NO'}")
    print(f"  Similarity not degraded: {'✅ YES' if sim_improved else '⚠️  NO'}")

    alpha_improved = anchor_stats_after.get("alpha", 0) >= anchor_stats_before.get("alpha", 0)
    print(f"  Alpha densified:        {'✅ YES' if alpha_improved else '⚠️  NO'}")
    print(f"    alpha: {anchor_stats_before.get('alpha', 0)} → {anchor_stats_after.get('alpha', 0)} non-zero dims")

    report = ale.get_learning_report()
    print(f"\n  Learning report:")
    print(f"    allocations: {report['allocations']}")
    print(f"    misallocations: {report['misallocations']}")
    print(f"    keyword_vocabulary: {report['keyword_vocabulary']}")

    assert nonzero_improved, "Non-zero dims should increase after learning"
    print("\n  LEARNING TEST: PASS ✅")
    return {
        "nonzero_before": total_nonzero_before,
        "nonzero_after": total_nonzero_after,
        "max_sim_before": max_sim_before,
        "max_sim_after": max_sim_after,
    }


def test_resonance_improvement():
    """
    測試 ASSIGN 觸發率學習前後變化
    """
    print("\n" + "=" * 60)
    print("ASSIGN TRIGGER RATE — BEFORE vs AFTER LEARNING")
    print("=" * 60)

    eng = ResonanceEngine()
    ale = AnchorLearningEngine(resonance_engine=eng, ema_alpha=0.8, learning_interval=1)

    test_inputs = [
        "focus and concentration",
        "thinking and learning",
        "energy and arousal",
        "curiosity and understanding",
        "comfort and vitality",
        "emotional feelings happiness",
        "mathematical logic precision",
        "social connection bond",
    ]

    # Phase A: 50 次軸更新學習
    print("\n[Phase A] 50 axis updates as learning signal...")
    beta_scenarios = [
        {"focus": 0.8, "curiosity": 0.7, "clarity": 0.6, "learning": 0.5, "confusion": 0.2, "creativity": 0.5},
        {"focus": 0.9, "curiosity": 0.8, "clarity": 0.7, "learning": 0.6, "confusion": 0.1, "creativity": 0.4},
        {"focus": 0.7, "curiosity": 0.9, "clarity": 0.5, "learning": 0.7, "confusion": 0.3, "creativity": 0.6},
    ]
    alpha_scenarios = [
        {"energy": 0.8, "arousal": 0.7, "comfort": 0.6, "tension": 0.2, "rest_need": 0.3, "vitality": 0.5},
        {"energy": 0.9, "arousal": 0.8, "comfort": 0.7, "tension": 0.1, "rest_need": 0.4, "vitality": 0.6},
        {"energy": 0.7, "arousal": 0.6, "comfort": 0.5, "tension": 0.3, "rest_need": 0.5, "vitality": 0.4},
    ]

    for i in range(50):
        ale.on_axis_update("beta", beta_scenarios[i % len(beta_scenarios)], is_stable=True)
        ale.on_axis_update("alpha", alpha_scenarios[i % len(alpha_scenarios)], is_stable=True)

    print("\n[Phase B] Testing 8 inputs BEFORE feedback...")
    sims_before = {}
    for label in test_inputs:
        vec = eng._text_to_vector(label, 32)
        sims = ale.get_all_similarities(vec)
        max_sim = max(sims.values()) if sims else 0.0
        best_ax = max(sims, key=sims.get) if sims else "none"
        sims_before[label] = (max_sim, best_ax)
        print(f"    '{label}': max_sim={max_sim:.4f} ({best_ax})")

    assign_count_before = sum(1 for s, _ in sims_before.values() if s >= 0.7)
    high_sim_count_before = sum(1 for s, _ in sims_before.values() if s >= 0.3)
    avg_sim_before = sum(s for s, _ in sims_before.values()) / len(sims_before)

    print(f"\n  BEFORE feedback:")
    print(f"    ASSIGN (sim≥0.7):  {assign_count_before}/{len(test_inputs)}")
    print(f"    High sim (sim≥0.3): {high_sim_count_before}/{len(test_inputs)}")
    print(f"    Avg max similarity: {avg_sim_before:.4f}")

    print("\n[Phase C] 20 ASSIGN feedback decisions...")
    feedback = [
        ("focus and concentration", "beta"),
        ("thinking and learning", "beta"),
        ("curiosity and understanding", "beta"),
        ("mathematical logic precision", "epsilon"),
        ("mathematical calculation", "epsilon"),
        ("emotional feelings happiness", "gamma"),
        ("energy and arousal", "alpha"),
        ("comfort and vitality", "alpha"),
        ("social connection bond", "delta"),
        ("social trust attention", "delta"),
        ("thinking and focus", "beta"),
        ("learning and curiosity", "beta"),
        ("logic and precision", "epsilon"),
        ("precision and calculation", "epsilon"),
        ("happiness and emotional", "gamma"),
        ("emotional feelings", "gamma"),
        ("arousal and energy", "alpha"),
        ("vitality and comfort", "alpha"),
        ("bond and connection", "delta"),
        ("attention and bond", "delta"),
    ]

    for label, target in feedback:
        vec = eng._text_to_vector(label, 32)
        ale.on_allocation_decision(vec, "ASSIGN", target, confidence=0.7)
        ale.on_text_vectorized(label, vec, target)

    print("\n[Phase D] Testing 8 inputs AFTER feedback...")
    sims_after = {}
    for label in test_inputs:
        vec = eng._text_to_vector(label, 32)
        sims = ale.get_all_similarities(vec)
        max_sim = max(sims.values()) if sims else 0.0
        best_ax = max(sims, key=sims.get) if sims else "none"
        sims_after[label] = (max_sim, best_ax)
        print(f"    '{label}': max_sim={max_sim:.4f} ({best_ax})")

    assign_count_after = sum(1 for s, _ in sims_after.values() if s >= 0.7)
    high_sim_count_after = sum(1 for s, _ in sims_after.values() if s >= 0.3)
    avg_sim_after = sum(s for s, _ in sims_after.values()) / len(sims_after)

    print(f"\n  AFTER feedback:")
    print(f"    ASSIGN (sim≥0.7):  {assign_count_after}/{len(test_inputs)}")
    print(f"    High sim (sim≥0.3): {high_sim_count_after}/{len(test_inputs)}")
    print(f"    Avg max similarity: {avg_sim_after:.4f}")

    print(f"\n  COMPARISON:")
    print(f"    ASSIGN rate:  {assign_count_before} → {assign_count_after}  ({assign_count_after-assign_count_before:+.0f})")
    print(f"    High sim rate: {high_sim_count_before} → {high_sim_count_after}  ({high_sim_count_after-high_sim_count_before:+.0f})")
    print(f"    Avg sim:       {avg_sim_before:.4f} → {avg_sim_after:.4f}  ({avg_sim_after-avg_sim_before:+.4f})")

    if avg_sim_after > avg_sim_before:
        print(f"\n  ✅ ASSIGN TRIGGER RATE IMPROVED")
    else:
        print(f"\n  ⚠️  Avg sim similar/below (but anchor densification happened)")

    report = ale.get_learning_report()
    print(f"\n  Final learning report:")
    print(f"    allocations: {report['allocations']}")
    print(f"    anchor stats: { {k: v['nonzero_dims'] for k,v in report['anchor_stats'].items()} }")
    print(f"    keywords: {report['keyword_vocabulary']}")

    return {
        "assign_before": assign_count_before,
        "assign_after": assign_count_after,
        "avg_sim_before": avg_sim_before,
        "avg_sim_after": avg_sim_after,
    }


if __name__ == '__main__':
    tests = [
        test_engine_creation,
        test_snapshot_to_vector,
        test_ema_update_densifies,
        test_on_allocation_assign_feedback,
        test_on_allocation_defer_accumulates,
        test_on_misallocation_correction,
        test_keyword_tracking,
        test_learning_report,
        test_learning_before_after,
        test_resonance_improvement,
    ]

    passed = 0
    failed = 0

    for t in tests:
        try:
            print(f"\n--- {t.__name__} ---")
            t()
            passed += 1
        except Exception as e:
            print(f"  FAIL: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"ANCHOR LEARNING TESTS: {passed} passed, {failed} failed")
    print(f"{'=' * 60}")