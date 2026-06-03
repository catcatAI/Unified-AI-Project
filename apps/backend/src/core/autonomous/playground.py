"""
Angela AI v7.5.0-dev — StateMatrix 能力展示場 / Capability Playground
===============================================================

Standalone development script (not imported by production code).

展示 StateMatrixAdapter 所有能力。

運行方式:
    python apps/backend/src/core/autonomous/playground.py

Author: Angela AI v7.5.0-dev
"""


from core.engine.state_matrix_adapter import StateMatrixAdapter
from core.ripple.node import MathOp


def make_vector(val: float = 0.5, nonzero: int = 8) -> list:
    """Execute the make vector operation."""
    vec = [0.0] * 32
    for i in range(nonzero):
        vec[i] = val
    return vec


def banner(text: str, width: int = 70) -> None:
    """Execute the banner operation."""
    print(f"\n{'=' * width}")
    print(f"  {text}")
    print(f"{'=' * width}")


def section(text: str) -> None:
    """Execute the section operation."""
    print(f"\n## {text}")


# =============================================================================
# 初始化
# =============================================================================


def main() -> None:
    """Main entry point."""
    banner("Angela AI v7.5.0-dev — StateMatrix Capability Playground")

    print("\n初始化 StateMatrixAdapter...")
    sm = StateMatrixAdapter()
    print(f"  → OK (temporal={sm._temporal.size()} snapshots)")

    # =============================================================================
    # 1. 6D 狀態矩陣
    # =============================================================================

    banner("1. 6D State Matrix (αβγδεθ)")

    section("Update each axis")
    sm.update_alpha(energy=0.8, comfort=0.7, arousal=0.6)
    sm.update_beta(focus=0.85, curiosity=0.9, clarity=0.7)
    sm.update_gamma(happiness=0.75, calm=0.6, trust=0.8)
    sm.update_delta(bond=0.7, attention=0.8, presence=0.6)
    sm.update_epsilon(logic=0.7, precision=0.6, certainty=0.65)
    sm.update_theta(novelty=0.5, complexity=0.4, creation_urge=0.1)

    averages = sm._sm.get_dimension_averages()
    print(f"  Axis averages: α={averages['alpha']:.3f}, β={averages['beta']:.3f}, "
          f"γ={averages['gamma']:.3f}, δ={averages['delta']:.3f}, "
          f"ε={averages['epsilon']:.3f}, θ={averages['theta']:.3f}")

    analysis = sm._sm.get_analysis()
    print(f"  Overall: {analysis['overall']:.3f}, Wellbeing: {analysis['wellbeing']:.3f}")
    print(f"  Arousal: {analysis['arousal']:.3f}, Valence: {analysis['valence']:.3f}")
    print(f"  Dominant dimension: {analysis['dominant_dimension']}")
    print(f"  Update count: {sm._sm.update_count}")


    # =============================================================================
    # 2. θ 元認知軸
    # =============================================================================

    banner("2. Theta Meta-Cognition (θ)")

    section("Trigger negativity")
    sm.trigger_theta_negativity(0.3)
    print(f"  θ negativity: {sm._sm.theta.values.get('theta_negativity', 0):.3f}")
    print(f"  correction_urge: {sm._sm.theta.values.get('correction_urge', 0):.3f}")

    section("Detect misallocation")
    points = sm.detect_misallocated_points()
    print(f"  Misallocated points: {len(points)}")

    section("Negativity report")
    report = sm.get_negativity_report()
    for k, v in report.items():
        if not isinstance(v, list):
            print(f"  {k}: {v}")


    # =============================================================================
    # 3. 時間查詢
    # =============================================================================

    banner("3. Temporal State Queries")

    for _ in range(20):
        sm.update_alpha(energy=0.5 + (_ % 5) * 0.04)

    trend = sm.temporal_trend("alpha", "energy", window=20)
    print(f"  Trend: {trend}")
    anomalies = sm.temporal_anomalies("alpha", "energy", threshold=0.3)
    print(f"  Anomalies: {len(anomalies)} found")
    corr = sm.temporal_correlation("alpha", "energy", "beta", "focus")
    print(f"  Correlation (alpha.energy, beta.focus): r={corr.correlation:.4f} ({corr.strength})")


    # =============================================================================
    # 4. 影響計算
    # =============================================================================

    banner("4. Influence Computation")

    inf = sm.influence_compute("alpha", "beta")
    print(f"  alpha → beta: {inf:.4f}")
    inf2 = sm.influence_compute("gamma", "alpha")
    print(f"  gamma → alpha: {inf2:.4f}")
    inf3 = sm.influence_compute("epsilon", "gamma")
    print(f"  epsilon → gamma: {inf3:.4f}")


    # =============================================================================
    # 5. 分配決策
    # =============================================================================

    banner("5. Allocation Decision")

    test_cases = [
        ("happiness emotion", [0.5] * 32),
        ("logical reasoning math", make_vector(0.8, nonzero=10)),
        ("social bond connection", make_vector(0.6, nonzero=6)),
    ]

    for label, vec in test_cases:
        decision = sm.allocation_decide(vec, label)
        print(f"  '{label}': {decision.action.value} (conf={decision.confidence:.2f})")


    # =============================================================================
    # 6. 漣漪級聯
    # =============================================================================

    banner("7. Ripple Cascade")

    nodes = sm.apply_ripple(MathOp.MUL, 1.1, cascade_targets=["alpha", "beta", "gamma"])
    print(f"  Cascade: {len(nodes)} nodes produced")
    summary = sm.ripple_summary()
    print(f"  Accumulator: {summary['count']} ripples, last_epsilon={summary.get('last_epsilon', 'N/A')}")


    # =============================================================================
    # 7. GradientField 導航
    # =============================================================================

    banner("7. Attractor Field Navigation")

    g = sm.compute_gradient()
    print(f"  Gradient strength: {g['gradient_strength']:.2f}")
    print("  Nearest attractors:")
    for a in g["nearest_attractors"][:3]:
        print(f"    - {a['description']} (tone={a['tone']}, dist={a['distance']:.3f})")
    print(f"  Blended tone: {g['blended_tone']}")

    n = sm.navigate_to_attractor(max_steps=3)
    print(f"  Navigate: {n['navigation_steps']} steps, new_state={n['new_state'][:3]}...")
    print(f"  Triggered attractor: {n['nearest_attractors'][0]['description'] if n['nearest_attractors'] else 'none'}")


    # =============================================================================
    # 8. 軸端口路由
    # =============================================================================

    banner("8. Axis Port Routing")

    sm.register_port(name="demo_llm", direction="io", semantic_vector=make_vector(0.9, nonzero=10),
                     tags=["llm", "demo"])
    sm.register_port(name="demo_cli", direction="out", semantic_vector=make_vector(0.5, nonzero=5),
                     tags=["cli"])

    ports = sm.list_ports()
    print(f"  Registered ports: {len(ports)}")
    for p in ports:
        print(f"    - {p['name']} ({p['direction']}) → axis={p['axis']}")

    cascade = sm.cascade_output(ports[0]["axis"], {"focus": 0.9})
    print(f"  Cascade output: {cascade['dispatched']}/{len(ports)} dispatched")

    sm.unregister_port("demo_llm")
    sm.unregister_port("demo_cli")


    # =============================================================================
    # 9. 持久化
    # =============================================================================

    banner("9. State Persistence")

    sm.update_beta(focus=0.95)
    state = sm.save_state()
    print(f"  Saved: {len(state['dimensions'])} dimensions, update_count={state['update_count']}")

    sm2 = StateMatrixAdapter()
    sm2.load_state(state)
    print(f"  Loaded: beta.focus = {sm2._sm.beta.values.get('focus', 0):.2f}")


    # =============================================================================
    # 10. CodeInspector 集成
    # =============================================================================

    banner("10. Code Inspector Integration")

    result = sm.integrate_code_inspect({
        "report": None,
        "total_issues": 5,
        "critical": 1,
        "high": 2,
        "medium": 2,
    })
    print(f"  Integrate result: {result.get('status', 'unknown')}")

    ci_report = sm.code_inspect_report()
    for k, v in ci_report.items():
        print(f"  {k}: {v:.3f}" if isinstance(v, float) else f"  {k}: {v}")


    # =============================================================================
    # 11. 吸引子管理
    # =============================================================================

    banner("11. Attractor Management")

    before = len(sm.gradient_field.attractors)
    sm.add_attractor(
        coord=(0.7, 0.8, 0.6, 0.5, 0.4),
        behavior="Creative exploration attractor",
        tone="curious",
        mass=1.5,
        tags=["creative", "exploration"],
    )
    after = len(sm.gradient_field.attractors)
    print(f"  Attractors: {before} → {after} (added 1)")

    sm.remove_attractor_by_tags(["creative"])
    final = len(sm.gradient_field.attractors)
    print(f"  After remove: {after} → {final}")


    # =============================================================================
    # 12. 完整報告
    # =============================================================================

    banner("12. Full Report")

    report = sm.full_report()
    print(f"  Sections: {list(report.keys())}")
    for section_name in ["state_matrix", "temporal", "influence", "allocation", "negativity", "port_routing"]:
        if section_name in report:
            data = report[section_name]
            if isinstance(data, dict):
                keys = list(data.keys())[:5]
                print(f"  {section_name}: {keys}...")


    # =============================================================================
    # 13. HTTP API 端點預覽
    # =============================================================================

    banner("13. FastAPI Endpoints Preview")

    from services.api.state_matrix_api import state_matrix_router
    routes = state_matrix_router.routes
    print(f"  Total endpoints: {len(routes)}")
    for r in routes:
        methods = list(r.methods) if hasattr(r.methods, '__iter__') else [str(r.methods)]
        print(f"  {methods[0]:4} {r.path}")


    # =============================================================================
    # 完成
    # =============================================================================

    banner("Playground Complete")
    print("\n所有能力展示完成。")
    print("\n下一步：")
    print("  1. 啟動服務: python -m uvicorn src.services.main_api_server:app --port 8000")
    print("  2. 查看 API:  GET /api/v1/state/summary")
    print("  3. 測試路由: POST /api/v1/state/navigate  {\"max_steps\": 3}")
    print("  4. 學習系統: 多次 allocation_decide() 後 AnchorLearningEngine 會自優化")


if __name__ == "__main__":
    main()
