"""Tests for core.state.axis_field"""
import pytest


class TestAxisField:
    """Tests for AxisField dataclass"""

    def test_import(self):
        """Verify AxisField and AxisFieldRegistry are importable"""
        from core.state.axis_field import AxisField, AxisFieldRegistry
        assert hasattr(AxisField, 'in_range')
        assert hasattr(AxisField, 'clamp')
        assert hasattr(AxisField, 'normalize')
        assert hasattr(AxisFieldRegistry, 'fields_for')
        assert hasattr(AxisFieldRegistry, 'all_axes')

    def test_axis_field_creation(self):
        """Verify AxisField creation stores all attributes"""
        from core.state.axis_field import AxisField
        field = AxisField(axis="alpha", name="energy", label="能量", min_val=0.0, max_val=1.0, default=0.5)
        assert field.axis == "alpha"
        assert field.name == "energy"
        assert field.label == "能量"
        assert field.min_val == 0.0
        assert field.max_val == 1.0
        assert field.default == 0.5

    def test_in_range(self):
        """Verify in_range validation"""
        from core.state.axis_field import AxisField
        field = AxisField(axis="test", name="f", label="F", min_val=0.0, max_val=1.0)
        assert field.in_range(0.5) is True
        assert field.in_range(0.0) is True
        assert field.in_range(1.0) is True
        assert field.in_range(-0.1) is False
        assert field.in_range(1.1) is False

    def test_clamp(self):
        """Verify clamp limits value to range"""
        from core.state.axis_field import AxisField
        field = AxisField(axis="test", name="f", label="F", min_val=0.0, max_val=1.0)
        assert field.clamp(0.5) == 0.5
        assert field.clamp(-0.5) == 0.0
        assert field.clamp(1.5) == 1.0

    def test_normalize(self):
        """Verify normalize maps value to [0, 1]"""
        from core.state.axis_field import AxisField
        field = AxisField(axis="test", name="f", label="F", min_val=0.0, max_val=10.0)
        assert field.normalize(0.0) == 0.0
        assert field.normalize(5.0) == 0.5
        assert field.normalize(10.0) == 1.0
        assert field.normalize(2.5) == 0.25

    def test_normalize_at_bounds(self):
        """Verify normalize returns 0 at min, 1 at max"""
        from core.state.axis_field import AxisField
        field = AxisField(axis="test", name="f", label="F", min_val=10.0, max_val=20.0)
        assert field.normalize(10.0) == 0.0
        assert field.normalize(20.0) == 1.0
        assert field.normalize(15.0) == 0.5

    def test_invalid_field_min_gte_max(self):
        """Verify AxisField creation with min >= max raises ValueError"""
        from core.state.axis_field import AxisField
        with pytest.raises(ValueError, match="min_val"):
            AxisField(axis="test", name="bad", label="Bad", min_val=1.0, max_val=0.5)

    def test_field_hash_equality(self):
        """Verify AxisField hashing and equality"""
        from core.state.axis_field import AxisField
        f1 = AxisField(axis="alpha", name="energy", label="能量")
        f2 = AxisField(axis="alpha", name="energy", label="不同")
        f3 = AxisField(axis="beta", name="energy", label="Beta能量")
        assert f1 == f2
        assert f1 != f3
        assert hash(f1) == hash(f2)
        assert hash(f1) != hash(f3)


class TestAxisFieldRegistry:
    """Tests for AxisFieldRegistry"""

    def test_registry_singleton(self):
        """Verify AxisFieldRegistry can be instantiated and has fields"""
        from core.state.axis_field import AxisFieldRegistry
        registry = AxisFieldRegistry()
        assert registry.count() > 0

    def test_fields_for_alpha(self):
        """Verify fields_for returns correct fields for alpha axis"""
        from core.state.axis_field import AxisFieldRegistry
        registry = AxisFieldRegistry()
        fields = registry.fields_for("alpha")
        names = [f.name for f in fields]
        assert "energy" in names
        assert "comfort" in names
        assert "arousal" in names
        assert "vitality" in names

    def test_fields_for_beta(self):
        """Verify fields_for returns correct fields for beta axis"""
        from core.state.axis_field import AxisFieldRegistry
        registry = AxisFieldRegistry()
        fields = registry.fields_for("beta")
        names = [f.name for f in fields]
        assert "curiosity" in names
        assert "focus" in names
        assert "learning" in names
        assert "clarity" in names

    def test_fields_for_unknown_axis(self):
        """Verify fields_for returns empty list for unknown axis"""
        from core.state.axis_field import AxisFieldRegistry
        registry = AxisFieldRegistry()
        assert registry.fields_for("unknown_axis") == []

    def test_all_axes(self):
        """Verify all_axes returns all registered axis names"""
        from core.state.axis_field import AxisFieldRegistry
        registry = AxisFieldRegistry()
        axes = registry.all_axes()
        for expected in ("alpha", "beta", "gamma", "delta", "epsilon", "theta"):
            assert expected in axes

    def test_get_field(self):
        """Verify get returns specific field by axis and name"""
        from core.state.axis_field import AxisFieldRegistry
        registry = AxisFieldRegistry()
        field = registry.get("alpha", "energy")
        assert field is not None
        assert field.name == "energy"
        assert field.axis == "alpha"
        assert registry.get("alpha", "nonexistent") is None

    def test_get_by_key(self):
        """Verify get_by_key resolves 'axis.name' format"""
        from core.state.axis_field import AxisFieldRegistry
        registry = AxisFieldRegistry()
        field = registry.get_by_key("alpha.energy")
        assert field is not None
        assert field.name == "energy"
        assert registry.get_by_key("invalid.key") is None

    def test_validate_axis_values_valid(self):
        """Verify validate_axis_values for valid values"""
        from core.state.axis_field import AxisFieldRegistry
        registry = AxisFieldRegistry()
        results = registry.validate_axis_values("alpha", {"energy": 0.5, "comfort": 0.8})
        assert results["energy"] == (True, None)
        assert results["comfort"] == (True, None)

    def test_validate_axis_values_invalid(self):
        """Verify validate_axis_values for out-of-range values"""
        from core.state.axis_field import AxisFieldRegistry
        registry = AxisFieldRegistry()
        results = registry.validate_axis_values("alpha", {"energy": -0.1, "comfort": 2.0})
        assert results["energy"][0] is False
        assert results["comfort"][0] is False

    def test_validate_axis_values_unknown_field(self):
        """Verify validate_axis_values passes through unknown fields"""
        from core.state.axis_field import AxisFieldRegistry
        registry = AxisFieldRegistry()
        results = registry.validate_axis_values("alpha", {"unknown_field": 999})
        assert results["unknown_field"] == (True, None)

    def test_schema_for(self):
        """Verify schema_for returns structured field definitions"""
        from core.state.axis_field import AxisFieldRegistry
        registry = AxisFieldRegistry()
        schema = registry.schema_for("alpha")
        assert "energy" in schema
        assert schema["energy"]["label"] == "能量"
        assert schema["energy"]["min"] == 0.0
        assert schema["energy"]["max"] == 1.0
        assert schema["energy"]["default"] == 0.5

    def test_repr(self):
        """Verify AxisField __repr__ output"""
        from core.state.axis_field import AxisField
        field = AxisField(axis="alpha", name="energy", label="能量")
        rep = repr(field)
        assert "AxisField" in rep
        assert "alpha.energy" in rep
        assert "0.5" in rep
