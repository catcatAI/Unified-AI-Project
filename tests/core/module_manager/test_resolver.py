import pytest

from apps.backend.src.core.system.module_manager.resolver import (
    CycleError,
    DependencyResolver,
)
from apps.backend.src.core.system.module_manager.models import (
    DependencySpec,
    ModuleDescriptor,
)


def create_descriptor(name, required=None, optional=None):
    return ModuleDescriptor(
        name=name,
        version="1.0.0",
        depends_on=DependencySpec(
            required=required or [],
            optional=optional or [],
        ),
    )


class TestResolve:
    def test_resolve_single(self):
        desc = create_descriptor("A")
        result = DependencyResolver().resolve([desc])
        assert result == [desc]

    def test_resolve_linear(self):
        a = create_descriptor("A")
        b = create_descriptor("B", required=["A"])
        c = create_descriptor("C", required=["B"])
        result = DependencyResolver().resolve([a, b, c])
        assert result == [a, b, c]

    def test_resolve_diamond(self):
        a = create_descriptor("A")
        b = create_descriptor("B", required=["A"])
        c = create_descriptor("C", required=["A"])
        d = create_descriptor("D", required=["B", "C"])
        result = DependencyResolver().resolve([a, b, c, d])
        names = [x.name for x in result]
        assert names[0] == "A"
        assert names[-1] == "D"
        assert set(names[1:-1]) == {"B", "C"}

    def test_resolve_cycle_detected(self):
        a = create_descriptor("A", required=["B"])
        b = create_descriptor("B", required=["C"])
        c = create_descriptor("C", required=["A"])
        with pytest.raises(CycleError) as exc_info:
            DependencyResolver().resolve([a, b, c])
        for name in ("A", "B", "C"):
            assert name in exc_info.value.cycle

    def test_resolve_self_cycle(self):
        a = create_descriptor("A", required=["A"])
        with pytest.raises(CycleError):
            DependencyResolver().resolve([a])

    def test_resolve_disjoint(self):
        a = create_descriptor("A")
        b = create_descriptor("B")
        result = DependencyResolver().resolve([a, b])
        names = [x.name for x in result]
        assert len(names) == 2
        assert set(names) == {"A", "B"}

    def test_resolve_ignores_optional_in_cycle(self):
        a = create_descriptor("A", optional=["B"])
        b = create_descriptor("B", optional=["A"])
        result = DependencyResolver().resolve([a, b])
        names = [x.name for x in result]
        assert len(names) == 2
        assert set(names) == {"A", "B"}


class TestCheckDeps:
    def test_check_deps_all_present(self):
        a = create_descriptor("A", required=["B"])
        b = create_descriptor("B")
        missing = DependencyResolver().check_deps(a, [b])
        assert missing == []

    def test_check_deps_missing(self):
        a = create_descriptor("A", required=["missing_dep"])
        missing = DependencyResolver().check_deps(a, [])
        assert missing == ["missing_dep"]


class TestMissingOptional:
    def test_missing_optional_none_missing(self):
        a = create_descriptor("A", optional=["B"])
        b = create_descriptor("B")
        missing = DependencyResolver().missing_optional(a, [b])
        assert missing == []

    def test_missing_optional_some_missing(self):
        a = create_descriptor("A", optional=["B", "C"])
        b = create_descriptor("B")
        missing = DependencyResolver().missing_optional(a, [b])
        assert missing == ["C"]


class TestVersionConstraint:
    def test_check_constraint_empty(self):
        assert DependencyResolver._check_constraint("1.0.0", "") is True

    def test_check_constraint_exact(self):
        assert DependencyResolver._check_constraint("1.0.0", "1.0.0") is True
        assert DependencyResolver._check_constraint("1.0.0", "==1.0.0") is True
        assert DependencyResolver._check_constraint("1.0.0", "==2.0.0") is False

    def test_check_constraint_greater_equal(self):
        assert DependencyResolver._check_constraint("1.0.0", ">=1.0.0") is True
        assert DependencyResolver._check_constraint("2.0.0", ">=1.0.0") is True
        assert DependencyResolver._check_constraint("0.9.0", ">=1.0.0") is False

    def test_check_constraint_less_equal(self):
        assert DependencyResolver._check_constraint("1.0.0", "<=1.0.0") is True
        assert DependencyResolver._check_constraint("0.9.0", "<=1.0.0") is True
        assert DependencyResolver._check_constraint("1.1.0", "<=1.0.0") is False

    def test_check_constraint_greater_than(self):
        assert DependencyResolver._check_constraint("1.0.1", ">1.0.0") is True
        assert DependencyResolver._check_constraint("1.0.0", ">1.0.0") is False

    def test_check_constraint_less_than(self):
        assert DependencyResolver._check_constraint("0.9.9", "<1.0.0") is True
        assert DependencyResolver._check_constraint("1.0.0", "<1.0.0") is False

    def test_check_constraint_multi_part(self):
        assert DependencyResolver._check_constraint("1.2.3", ">=1.2.3") is True
        assert DependencyResolver._check_constraint("1.2.4", ">=1.2.3") is True
        assert DependencyResolver._check_constraint("1.2.2", ">=1.2.3") is False

    def test_check_constraint_different_part_count(self):
        assert DependencyResolver._check_constraint("2.0", ">=1.0.0") is True
        assert DependencyResolver._check_constraint("2.0.0.1", ">=2.0.0") is True

    def test_check_deps_version_mismatch(self):
        resolver = DependencyResolver()
        a = create_descriptor("A", required=["B"])
        a.constraints["B"] = ">=2.0.0"
        b = ModuleDescriptor(
            name="B",
            version="1.0.0",
            depends_on=DependencySpec(),
        )
        missing = resolver.check_deps(a, [b])
        assert len(missing) == 1
        assert ">=2.0.0" in missing[0] and "1.0.0" in missing[0]

    def test_check_deps_version_match(self):
        resolver = DependencyResolver()
        a = create_descriptor("A", required=["B"])
        a.constraints["B"] = ">=1.0.0"
        b = ModuleDescriptor(
            name="B",
            version="2.0.0",
            depends_on=DependencySpec(),
        )
        missing = resolver.check_deps(a, [b])
        assert missing == []
