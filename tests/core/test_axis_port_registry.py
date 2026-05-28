"""Tests for axis_port_registry.py"""


from core.autonomous.axis_port_registry import PortRegistry, PortDirection, Port


def make_vector(val: float = 0.5, nonzero: int = 8) -> list:
    vec = [0.0] * 32
    for i in range(nonzero):
        vec[i] = val
    return vec


def test_port_creation():
    port = Port(
        name="test_port",
        direction=PortDirection.IN,
        semantic_vector=make_vector(),
        priority=0.7,
        tags=["test"],
    )
    assert port.name == "test_port"
    assert port.direction == PortDirection.IN
    assert port.axis is None
    assert not port.is_bound()
    assert len(port.semantic_vector) == 32


def test_port_compute_similarity():
    port = Port(name="test", direction=PortDirection.IO, semantic_vector=make_vector(0.8))
    target = make_vector(0.8)
    sim = port.compute_similarity(target)
    assert 0.0 < sim <= 1.0


def test_port_registry_register():
    registry = PortRegistry(state_adapter=None)
    port = registry.register(
        name="llm_out",
        direction=PortDirection.IN,
        semantic_vector=make_vector(),
        auto_bind=False,
    )
    assert port.name == "llm_out"
    assert registry.size() == 1
    assert registry.unbound_count() == 1


def test_port_registry_unregister():
    registry = PortRegistry(state_adapter=None)
    registry.register(name="port1", direction=PortDirection.IO, semantic_vector=make_vector())
    assert registry.size() == 1
    registry.unregister("port1")
    assert registry.size() == 0


def test_port_registry_list():
    registry = PortRegistry(state_adapter=None)
    registry.register(name="in1", direction=PortDirection.IN, semantic_vector=make_vector())
    registry.register(name="out1", direction=PortDirection.OUT, semantic_vector=make_vector())
    registry.register(name="io1", direction=PortDirection.IO, semantic_vector=make_vector())

    all_ports = registry.list_ports()
    assert len(all_ports) == 3

    in_only = registry.list_ports(direction=PortDirection.IN)
    assert len(in_only) == 1
    assert in_only[0].name == "in1"


def test_port_registry_bind_unbind():
    registry = PortRegistry(state_adapter=None)
    registry.register(name="port1", direction=PortDirection.OUT, semantic_vector=make_vector())

    registry.bind_port_to_axis("port1", "alpha")
    port = registry.get_port("port1")
    assert port.axis == "alpha"
    assert registry.bound_count() == 1

    outputs = registry.get_outputs_for_axis("alpha")
    assert len(outputs) == 1
    assert outputs[0].name == "port1"

    registry.unbind_port("port1")
    assert registry.get_port("port1").axis is None
    assert registry.unbound_count() == 1


def test_port_registry_find_best_axis():
    registry = PortRegistry(state_adapter=None)
    port = registry.register(
        name="logic_port",
        direction=PortDirection.IO,
        semantic_vector=make_vector(0.9, nonzero=10),
    )
    best = registry.find_best_axis_for_port(port)
    assert best is None


def test_port_registry_find_best_axis_with_adapter():
    from core.engine.state_matrix_adapter import StateMatrixAdapter
    adapter = StateMatrixAdapter()
    registry = PortRegistry(state_adapter=adapter)
    port = registry.register(
        name="logic_port",
        direction=PortDirection.IO,
        semantic_vector=make_vector(0.9, nonzero=10),
        auto_bind=False,
    )
    best = registry.find_best_axis_for_port(port)
    assert best is not None
    assert best in ("alpha", "beta", "gamma", "delta", "epsilon", "theta")


def test_port_registry_auto_bind_idle():
    from core.engine.state_matrix_adapter import StateMatrixAdapter
    adapter = StateMatrixAdapter()
    registry = PortRegistry(state_adapter=adapter)
    registry.register(name="p1", direction=PortDirection.IO, semantic_vector=make_vector(), auto_bind=False)
    registry.register(name="p2", direction=PortDirection.IN, semantic_vector=make_vector(), auto_bind=False)

    for name in ["p1", "p2"]:
        registry.unbind_port(name)

    assert registry.unbound_count() == 2
    count = registry.auto_bind_idle_ports()
    assert count == 2


def test_port_registry_report():
    from core.engine.state_matrix_adapter import StateMatrixAdapter
    adapter = StateMatrixAdapter()
    registry = PortRegistry(state_adapter=adapter)
    registry.register(name="p1", direction=PortDirection.OUT, semantic_vector=make_vector(), auto_bind=False)
    registry.register(name="p2", direction=PortDirection.IN, semantic_vector=make_vector(), auto_bind=False)

    report = registry.get_report()
    assert report["total_ports"] == 2
    assert report["bound_ports"] == 0
    assert len(report["ports"]) == 2


if __name__ == "__main__":
    test_port_creation()
    test_port_compute_similarity()
    test_port_registry_register()
    test_port_registry_unregister()
    test_port_registry_list()
    test_port_registry_bind_unbind()
    test_port_registry_find_best_axis()
    test_port_registry_find_best_axis_with_adapter()
    test_port_registry_auto_bind_idle()
    test_port_registry_report()
    print("All axis_port_registry tests passed!")