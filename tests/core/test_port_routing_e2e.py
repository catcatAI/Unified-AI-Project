"""End-to-end test for port routing with StateMatrixAdapter"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

from core.autonomous.state_matrix_adapter import StateMatrixAdapter


def make_vector(val: float = 0.5, nonzero: int = 8) -> list:
    vec = [0.0] * 32
    for i in range(nonzero):
        vec[i] = val
    return vec


def test_port_routing_integration():
    sm = StateMatrixAdapter()

    p1 = sm.register_port(
        name="llm_output",
        direction="io",
        semantic_vector=make_vector(0.9, nonzero=10),
        priority=0.7,
        tags=["llm", "text"],
    )
    assert p1.name == "llm_output"
    assert p1.axis is not None

    p2 = sm.register_port(
        name="cli_input",
        direction="out",
        semantic_vector=make_vector(0.5, nonzero=5),
        priority=0.6,
        tags=["cli", "command"],
    )
    assert p2.name == "cli_input"

    ports = sm.list_ports()
    assert len(ports) == 2

    bound_axis = p1.axis
    outputs = sm.cascade_output(bound_axis, {"focus": 0.8})
    assert outputs["status"] == "completed"

    sm.output_to_port("cli_input", {"command": "status"})
    data = sm.input_from_port("cli_input")
    assert data is not None
    assert "command" in data

    sm.unregister_port("llm_output")
    sm.unregister_port("cli_input")
    assert len(sm.list_ports()) == 0


def test_port_routing_full_report():
    sm = StateMatrixAdapter()

    sm.register_port(name="port_a", direction="io", semantic_vector=make_vector(), priority=0.6)
    sm.register_port(name="port_b", direction="out", semantic_vector=make_vector(0.8, nonzero=6), priority=0.7)

    report = sm.full_report()
    assert "port_routing" in report
    pr = report["port_routing"]
    assert pr["total_ports"] == 2
    assert pr["bound_ports"] == 2

    sm.unregister_port("port_a")
    sm.unregister_port("port_b")


def test_auto_allocate_ports():
    sm = StateMatrixAdapter()

    sm.register_port(name="new_port_1", direction="io", semantic_vector=make_vector(0.9, nonzero=12), auto_bind=False)
    sm.register_port(name="new_port_2", direction="in", semantic_vector=make_vector(0.7, nonzero=8), auto_bind=False)

    unbound_before = [p for p in sm.list_ports() if not p.get("bound", False)]
    count = sm.auto_allocate_ports()
    assert count >= 0

    sm.unregister_port("new_port_1")
    sm.unregister_port("new_port_2")


if __name__ == "__main__":
    test_port_routing_integration()
    test_port_routing_full_report()
    test_auto_allocate_ports()
    print("All port routing integration tests passed!")