import pytest
from apps.backend.src.core.state.axis import Axis
from apps.backend.src.core.state.axis_field import AxisField, AxisFieldRegistry


class TestAxis:
    def test_create_alpha(self):
        axis = Axis.create_alpha(weight=1.0)
        assert axis.name == "alpha"
        assert axis.label == "生理"
        assert axis.coordinate == (0.0, -5.0, 0.0)

    def test_create_beta(self):
        axis = Axis.create_beta()
        assert axis.name == "beta"

    def test_create_gamma(self):
        axis = Axis.create_gamma()
        assert axis.name == "gamma"

    def test_create_delta(self):
        axis = Axis.create_delta()
        assert axis.name == "delta"

    def test_create_epsilon(self):
        axis = Axis.create_epsilon()
        assert axis.name == "epsilon"

    def test_create_theta(self):
        axis = Axis.create_theta()
        assert axis.name == "theta"

    def test_get_returns_default_from_registry(self):
        axis = Axis.create_alpha()
        energy_field = AxisField(axis="alpha", name="energy", label="能量", default=0.5)
        val = axis.get(energy_field)
        assert val == pytest.approx(0.5)

    def test_set_and_get(self):
        axis = Axis.create_alpha()
        energy_field = AxisField(axis="alpha", name="energy", label="能量", default=0.5, min_val=0.0, max_val=1.0)
        axis.set(energy_field, 0.8)
        assert axis.get(energy_field) == pytest.approx(0.8)

    def test_set_clamps_value(self):
        axis = Axis.create_alpha()
        energy_field = AxisField(axis="alpha", name="energy", label="能量", default=0.5, min_val=0.0, max_val=1.0)
        axis.set(energy_field, 5.0)
        assert axis.get(energy_field) == pytest.approx(1.0)

    def test_set_no_clamp(self):
        axis = Axis.create_alpha()
        energy_field = AxisField(axis="alpha", name="energy", label="能量", default=0.5)
        axis.set(energy_field, 5.0, clamp=False)
        assert axis.get(energy_field) == pytest.approx(5.0)

    def test_modify_adds_delta(self):
        axis = Axis.create_alpha()
        energy_field = AxisField(axis="alpha", name="energy", label="能量", default=0.5, min_val=0.0, max_val=1.0)
        axis.set(energy_field, 0.5)
        axis.modify(energy_field, 0.3)
        assert axis.get(energy_field) == pytest.approx(0.8)

    def test_modify_clamps(self):
        axis = Axis.create_alpha()
        energy_field = AxisField(axis="alpha", name="energy", label="能量", default=0.5, min_val=0.0, max_val=1.0)
        axis.set(energy_field, 0.5)
        axis.modify(energy_field, 10.0)
        assert axis.get(energy_field) == pytest.approx(1.0)

    def test_get_str_backward_compat(self):
        axis = Axis.create_alpha()
        axis.set_str("energy", 0.75)
        assert axis.get_str("energy") == pytest.approx(0.75)

    def test_get_str_default(self):
        axis = Axis.create_alpha()
        assert axis.get_str("nonexistent", default=0.5) == pytest.approx(0.5)

    def test_update_batch(self):
        axis = Axis.create_alpha()
        axis.update(energy=0.9, comfort=0.3)
        assert axis.get_str("energy") == pytest.approx(0.9)
        assert axis.get_str("comfort") == pytest.approx(0.3)

    def test_average(self):
        axis = Axis.create_alpha()
        axis.update(energy=1.0, comfort=0.0)
        avg = axis.average()
        assert 0.3 < avg < 0.5

    def test_average_empty(self):
        axis = Axis.from_config(name="empty", label="Empty")
        assert axis.average() == 0.0

    def test_dominant(self):
        axis = Axis.create_alpha()
        axis.update(energy=1.0, comfort=0.0)
        name, val = axis.dominant()
        assert name == "energy"
        assert val == pytest.approx(1.0)

    def test_dominant_empty(self):
        axis = Axis.from_config(name="empty", label="Empty")
        name, val = axis.dominant()
        assert name == ""
        assert val == 0.0

    def test_variance(self):
        axis = Axis.create_alpha()
        axis.update(energy=1.0, comfort=0.0)
        var = axis.variance()
        assert var > 0.0

    def test_variance_single_value(self):
        axis = Axis.from_config(name="single", label="Single")
        axis.update(field_a=0.5)
        assert axis.variance() == 0.0

    def test_field_count(self):
        axis = Axis.create_alpha()
        assert axis.field_count() >= 5

    def test_shift_coordinate(self):
        axis = Axis.from_config("test", "Test", coordinate=(0.0, 0.0, 0.0))
        axis.shift(dx=1.0, dy=-2.0, dz=3.0)
        assert axis.coordinate == (1.0, -2.0, 3.0)

    def test_distance_to(self):
        a = Axis.from_config("a", "A", coordinate=(0.0, 0.0, 0.0))
        b = Axis.from_config("b", "B", coordinate=(1.0, 0.0, 0.0))
        assert a.distance_to(b) == pytest.approx(1.0)

    def test_influence_factor_to(self):
        a = Axis.from_config("a", "A", coordinate=(0.0, 0.0, 0.0))
        b = Axis.from_config("b", "B", coordinate=(1.0, 0.0, 0.0))
        factor = a.influence_factor_to(b)
        assert 0.5 <= factor <= 2.0

    def test_snapshot_and_load(self):
        axis = Axis.create_alpha()
        axis.update(energy=0.9, comfort=0.2)
        snap = axis.snapshot()
        assert snap["energy"] == pytest.approx(0.9)
        axis2 = Axis.create_alpha()
        axis2.load_snapshot(snap)
        assert axis2.get_str("energy") == pytest.approx(0.9)

    def test_from_config_with_initial_values(self):
        axis = Axis.from_config(
            "custom", "Custom", initial_values={"energy": 0.7, "comfort": 0.3},
        )
        assert axis.get_str("energy") == pytest.approx(0.7)

    def test_field_names(self):
        axis = Axis.create_alpha()
        names = axis.field_names()
        assert len(names) > 0
        assert "energy" in names
