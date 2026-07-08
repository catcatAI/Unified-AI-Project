"""Smoke tests for core/version.py"""
from core.version import ReleasePhase, VersionInfo


class TestVersionInfo:
    """Basic smoke tests for VersionInfo"""

    def test_import(self):
        assert VersionInfo is not None

    def test_instantiation(self):
        instance = VersionInfo()
        assert instance is not None
        assert instance.major == 7
        assert instance.minor == 5

    def test_increment_patch(self):
        v1 = VersionInfo(major=1, minor=2, patch=3)
        v2 = v1.increment_patch()
        assert v2.major == 1
        assert v2.minor == 2
        assert v2.patch == 4

    def test_increment_minor(self):
        v1 = VersionInfo(major=1, minor=2, patch=3)
        v2 = v1.increment_minor()
        assert v2.major == 1
        assert v2.minor == 3
        assert v2.patch == 0

    def test_increment_major(self):
        v1 = VersionInfo(major=1, minor=2, patch=3)
        v2 = v1.increment_major()
        assert v2.major == 2
        assert v2.minor == 0
        assert v2.patch == 0

    def test_str_representation(self):
        v = VersionInfo(major=7, minor=5, patch=0, phase=ReleasePhase.STABLE)
        assert str(v) == "7.5.0"
