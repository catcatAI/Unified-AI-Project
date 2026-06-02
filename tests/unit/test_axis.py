"""Tests for core.state.axis"""
import pytest


class TestAxis:
    """Tests for Axis dataclass"""

    def test_import(self):
        """Verify Axis is importable and has expected methods"""
        from core.state.axis import Axis
        assert hasattr(Axis, 'get')
        assert hasattr(Axis, 'set')
        assert hasattr(Axis, 'modify')
        assert hasattr(Axis, 'update')
        assert hasattr(Axis, 'average')
        assert hasattr(Axis, 'dominant')
        assert hasattr(Axis, 'snapshot')

    def test_instantiation(self):
        """Verify basic instantiation with defaults"""
        from core.state.axis import Axis
        instance = Axis(name="test", label="Test")
        assert instance.name == "test"
        assert instance.label == "Test"
        assert instance.coordinate == (0.0, 0.0, 0.0)
        assert instance.weight == 1.0

    def test_from_config(self):
        """Verify from_config factory method"""
        from core.state.axis import Axis
        axis = Axis.from_config(
            name="alpha", label="生理",
            coordinate=(1.0, 2.0, 3.0),
            weight=0.5, description="test",
            initial_values={"energy": 0.8},
        )
        assert axis.name == "alpha"
        assert axis.coordinate == (1.0, 2.0, 3.0)
        assert axis.weight == 0.5
        assert axis.get_str("energy") == 0.8

    def test_set_get_field(self):
        """Verify set/get for field values"""
        from core.state.axis import Axis
        from core.state.axis_field import AxisField
        axis = Axis(name="test", label="Test")
        field = AxisField(axis="test", name="custom", label="Custom", min_val=0.0, max_val=1.0, default=0.5)
        result = axis.set(field, 0.9)
        assert result == 0.9
        assert axis.get(field) == 0.9

    def test_set_clamping(self):
        """Verify set clamps value to field range"""
        from core.state.axis import Axis
        from core.state.axis_field import AxisField
        axis = Axis(name="test", label="Test")
        field = AxisField(axis="test", name="custom", label="Custom", min_val=0.0, max_val=1.0, default=0.5)
        axis.set(field, 2.0)
        assert axis.get(field) == 1.0
        axis.set(field, -1.0)
        assert axis.get(field) == 0.0

    def test_modify_field(self):
        """Verify modify applies delta correctly"""
        from core.state.axis import Axis
        from core.state.axis_field import AxisField
        axis = Axis(name="test", label="Test")
        field = AxisField(axis="test", name="custom", label="Custom", min_val=0.0, max_val=1.0, default=0.5)
        val = axis.modify(field, 0.3)
        assert val == 0.8
        val = axis.modify(field, -0.4)
        assert val == 0.4

    def test_set_str(self):
        """Verify set_str/get_str string-based access"""
        from core.state.axis import Axis
        axis = Axis(name="test", label="Test")
        axis.set_str("custom_field", 0.75)
        assert axis.get_str("custom_field") == 0.75
        assert axis.get_str("nonexistent", 0.5) == 0.5

    def test_update_batch(self):
        """Verify update sets multiple fields at once"""
        from core.state.axis import Axis
        axis = Axis(name="test", label="Test")
        axis.set_str("a", 0.1)
        axis.set_str("b", 0.2)
        axis.update(a=0.5, b=0.6)
        assert axis.get_str("a") == 0.5
        assert axis.get_str("b") == 0.6

    def test_average(self):
        """Verify average calculation"""
        from core.state.axis import Axis
        axis = Axis(name="test", label="Test")
        axis.set_str("a", 0.2)
        axis.set_str("b", 0.4)
        axis.set_str("c", 0.6)
        assert abs(axis.average() - 0.4) < 0.01

    def test_average_empty(self):
        """Verify average returns 0 for empty axis"""
        from core.state.axis import Axis
        axis = Axis(name="empty", label="Empty", _values={})
        assert axis.average() == 0.0

    def test_dominant(self):
        """Verify dominant returns max field"""
        from core.state.axis import Axis
        axis = Axis(name="test", label="Test")
        axis.set_str("a", 0.2)
        axis.set_str("b", 0.9)
        axis.set_str("c", 0.5)
        name, val = axis.dominant()
        assert name == "b"
        assert val == 0.9

    def test_dominant_empty(self):
        """Verify dominant returns empty for no fields"""
        from core.state.axis import Axis
        axis = Axis(name="empty", label="Empty", _values={})
        assert axis.dominant() == ("", 0.0)

    def test_variance(self):
        """Verify variance calculation"""
        from core.state.axis import Axis
        axis = Axis(name="test", label="Test")
        axis.set_str("a", 0.0)
        axis.set_str("b", 0.5)
        axis.set_str("c", 1.0)
        var = axis.variance()
        assert var > 0.0

    def test_variance_insufficient(self):
        """Verify variance returns 0 for fewer than 2 values"""
        from core.state.axis import Axis
        axis = Axis(name="test", label="Test")
        axis.set_str("a", 0.5)
        assert axis.variance() == 0.0

    def test_shift_coordinate(self):
        """Verify shift moves coordinate"""
        from core.state.axis import Axis
        axis = Axis(name="test", label="Test", coordinate=(1.0, 2.0, 3.0))
        axis.shift(dx=0.5, dy=-1.0, dz=2.0)
        assert axis.coordinate == (1.5, 1.0, 5.0)

    def test_distance_to(self):
        """Verify Euclidean distance calculation"""
        from core.state.axis import Axis
        a = Axis(name="a", label="A", coordinate=(0.0, 0.0, 0.0))
        b = Axis(name="b", label="B", coordinate=(3.0, 4.0, 0.0))
        assert abs(a.distance_to(b) - 5.0) < 0.001

    def test_influence_factor_to(self):
        """Verify influence factor uses inverse square law"""
        from core.state.axis import Axis
        a = Axis(name="a", label="A", coordinate=(0.0, 0.0, 0.0))
        b = Axis(name="b", label="B", coordinate=(0.0, 0.0, 0.0))
        influence = a.influence_factor_to(b)
        assert 0.5 <= influence <= 2.0

    def test_snapshot_roundtrip(self):
        """Verify snapshot and load_snapshot round-trip"""
        from core.state.axis import Axis
        axis = Axis(name="test", label="Test")
        axis.set_str("a", 0.3)
        axis.set_str("b", 0.7)
        snap = axis.snapshot()
        assert snap == {"a": 0.3, "b": 0.7}
        axis2 = Axis(name="test2", label="Test2")
        axis2.load_snapshot(snap)
        assert axis2.get_str("a") == 0.3
        assert axis2.get_str("b") == 0.7

    def test_field_count(self):
        """Verify field_count returns correct count"""
        from core.state.axis import Axis
        axis = Axis(name="test", label="Test")
        axis.set_str("a", 0.1)
        axis.set_str("b", 0.2)
        assert axis.field_count() == 2

    def test_factory_create_alpha(self):
        """Verify create_alpha factory method"""
        from core.state.axis import Axis
        alpha = Axis.create_alpha(weight=0.8)
        assert alpha.name == "alpha"
        assert alpha.label == "生理"
        assert alpha.weight == 0.8
        assert alpha.coordinate == (0.0, -5.0, 0.0)

    def test_factory_create_beta(self):
        """Verify create_beta factory method"""
        from core.state.axis import Axis
        beta = Axis.create_beta()
        assert beta.name == "beta"
        assert beta.coordinate == (0.0, 10.0, 0.0)

    def test_factory_create_all(self):
        """Verify all factory methods produce valid axes"""
        from core.state.axis import Axis
        for factory, name in [
            (Axis.create_alpha, "alpha"),
            (Axis.create_beta, "beta"),
            (Axis.create_gamma, "gamma"),
            (Axis.create_delta, "delta"),
            (Axis.create_epsilon, "epsilon"),
            (Axis.create_theta, "theta"),
        ]:
            axis = factory()
            assert axis.name == name
            assert axis.average() >= 0.0

    def test_repr(self):
        """Verify __repr__ output"""
        from core.state.axis import Axis
        axis = Axis(name="test", label="Test")
        axis.set_str("a", 0.9)
        rep = repr(axis)
        assert "Axis(" in rep
        assert "test" in rep
        assert "0.90" in rep
