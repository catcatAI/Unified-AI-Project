"""core.state.axis_field 軸域註冊表測試"""

from apps.backend.src.core.state.axis_field import (
    AxisField,
    AxisFieldEnum,
    AxisFieldRegistry,
)


class TestAxisFieldRegistry:
    def test_get_known_field(self):
        field = AxisFieldRegistry().get("alpha", "energy")
        assert field is not None
        assert field.name == "energy"

    def test_get_missing_field(self):
        assert AxisFieldRegistry().get("alpha", "nonexistent") is None

    def test_get_by_key(self):
        field = AxisFieldRegistry().get_by_key("alpha.energy")
        assert field is not None
        assert field.axis == "alpha"

    def test_fields_for(self):
        fields = AxisFieldRegistry().fields_for("alpha")
        assert len(fields) > 0
        assert all(f.axis == "alpha" for f in fields)


class TestAxisField:
    def test_in_range(self):
        field = AxisFieldRegistry().get("alpha", "energy")
        assert field is not None
        assert field.in_range(field.default)
        assert field.in_range(2.0) in (True, False)


class TestAxisFieldEnum:
    def test_get_known_field(self):
        field = AxisFieldEnum.get("alpha", "energy")
        assert field is not None
        assert field.name == "energy"

    def test_get_missing_field(self):
        assert AxisFieldEnum.get("alpha", "nonexistent") is None
