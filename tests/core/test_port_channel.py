"""Tests for port_channel.py"""


from core.engine.port_channel import AxisOutputManager, PortChannel


def test_port_channel_push_pull():
    channel = PortChannel("test_channel", max_buffer=10)
    assert channel.is_empty()

    channel.push({"data": 0.5})
    channel.push({"data": 0.7})
    assert channel.size() == 2

    data = channel.pull()
    assert data["data"] == 0.5
    assert channel.size() == 1


def test_port_channel_overflow():
    channel = PortChannel("test", max_buffer=3)
    for i in range(5):
        channel.push({"i": i})
    assert channel.size() == 3
    assert channel.pull()["i"] == 2


def test_port_channel_peek():
    channel = PortChannel("test")
    channel.push({"a": 1})
    channel.push({"b": 2})

    assert channel.peek()["a"] == 1
    assert channel.size() == 2

    all_data = channel.peek_all()
    assert len(all_data) == 2


def test_port_channel_clear():
    channel = PortChannel("test")
    channel.push({"x": 1})
    channel.push({"y": 2})
    assert channel.size() == 2

    count = channel.clear()
    assert count == 2
    assert channel.size() == 0
    assert channel.is_empty()


def test_port_channel_is_full():
    channel = PortChannel("test", max_buffer=2)
    assert not channel.is_full()
    channel.push(1)
    channel.push(2)
    assert channel.is_full()


def test_port_channel_summary():
    channel = PortChannel("summary_test", max_buffer=50)
    channel.push({"val": 0.8})
    channel.push({"val": 0.6})

    summary = channel.summary()
    assert summary["port_name"] == "summary_test"
    assert summary["buffer_size"] == 2
    assert summary["fill_ratio"] > 0
    assert summary["push_count"] == 2
    assert summary["pull_count"] == 0


def test_axis_output_manager_init():
    manager = AxisOutputManager(state_adapter=None, port_registry=None)
    assert manager._channels == {}


def test_axis_output_manager_push_to_port_no_registry():
    manager = AxisOutputManager(state_adapter=None, port_registry=None)
    result = manager.push_to_port("port1", {"data": 1.0})
    assert result is False


def test_axis_output_manager_output_no_registry():
    manager = AxisOutputManager(state_adapter=None, port_registry=None)
    result = manager.output("alpha", {"focus": 0.8})
    assert result["status"] == "no_registry"


def test_axis_output_manager_input_no_registry():
    manager = AxisOutputManager(state_adapter=None, port_registry=None)
    result = manager.input("alpha")
    assert result["status"] == "no_registry"


def test_axis_output_manager_batch_output():
    manager = AxisOutputManager(state_adapter=None, port_registry=None)
    result = manager.batch_output({"alpha": {"focus": 0.8}, "beta": {"curiosity": 0.5}})
    assert result["status"] == "batch_completed"
    assert result["axes"] == 2


def test_axis_output_manager_get_port_summary_no_channel():
    manager = AxisOutputManager(state_adapter=None, port_registry=None)
    summary = manager.get_port_summary("nonexistent")
    assert summary["status"] == "no_channel"


if __name__ == "__main__":
    test_port_channel_push_pull()
    test_port_channel_overflow()
    test_port_channel_peek()
    test_port_channel_clear()
    test_port_channel_is_full()
    test_port_channel_summary()
    test_axis_output_manager_init()
    test_axis_output_manager_push_to_port_no_registry()
    test_axis_output_manager_output_no_registry()
    test_axis_output_manager_input_no_registry()
    test_axis_output_manager_batch_output()
    test_axis_output_manager_get_port_summary_no_channel()
    print("All port_channel tests passed!")