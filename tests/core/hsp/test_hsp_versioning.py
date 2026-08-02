"""core.hsp.versioning HSP 版本管理測試"""

import asyncio

import pytest

from apps.backend.src.core.hsp.versioning import (
    HSPCompatibilityChecker,
    HSPVersionCompatibility,
    HSPVersionConverter,
    HSPVersionInfo,
    HSPVersionManager,
    HSPVersionNegotiator,
    HSPVersionedMessageHandler,
)


class TestHSPVersionInfo:
    def test_requires_metadata(self):
        info = HSPVersionInfo(
            version="0.1.0",
            release_date="2023-01-01",
            description="Initial release",
            compatible_versions=[],
            breaking_changes=[],
            deprecated_features=[],
        )
        assert info.version == "0.1.0"


class TestHSPVersionManager:
    def test_default_current_version(self):
        mgr = HSPVersionManager()
        assert mgr.current_version == "0.1.0"
        assert "0.1.0" in mgr.supported_versions

    def test_register_version(self):
        mgr = HSPVersionManager()
        mgr.register_version(
            HSPVersionInfo(
                version="0.2.0",
                release_date="2023-06-01",
                description="Second release",
                compatible_versions=["0.1.0"],
                breaking_changes=[],
                deprecated_features=[],
            )
        )
        assert mgr.is_version_supported("0.2.0")
        assert mgr.get_version_info("0.2.0").description == "Second release"

    def test_check_compatibility_same_version(self):
        mgr = HSPVersionManager()
        assert mgr.check_compatibility("0.1.0", "0.1.0") is True

    def test_is_upgrade_needed(self):
        mgr = HSPVersionManager()
        assert mgr.is_upgrade_needed("0.1.0", "0.2.0") is True
        assert mgr.is_upgrade_needed("0.2.0", "0.1.0") is False


class TestHSPVersionNegotiator:
    def test_negotiate_common_highest(self):
        mgr = HSPVersionManager()
        negotiator = HSPVersionNegotiator(mgr)
        result = negotiator.negotiate_with_capabilities(["0.1.0", "0.2.0"], ["0.1.0"])
        assert result == "0.1.0"

    def test_negotiate_no_common(self):
        mgr = HSPVersionManager()
        negotiator = HSPVersionNegotiator(mgr)
        assert negotiator.negotiate_with_capabilities(["0.3.0"], ["0.1.0"]) is None

    def test_get_upgrade_recommendation(self):
        mgr = HSPVersionManager()
        negotiator = HSPVersionNegotiator(mgr)
        assert negotiator.get_upgrade_recommendation("0.1.0") is None


class TestHSPVersionConverter:
    def test_convert_same_version_noop(self):
        mgr = HSPVersionManager()
        conv = HSPVersionConverter(mgr)
        msg = {"message_id": "m1", "protocol_version": "0.1.0", "payload": {}}
        assert conv.convert_message_with_version_check(msg) is msg

    def test_convert_upgrade(self):
        mgr = HSPVersionManager()
        conv = HSPVersionConverter(mgr)
        msg = {
            "message_id": "m1",
            "protocol_version": "0.1.0",
            "hsp_envelope_version": "0.1.0",
            "payload": {"metadata": None},
            "timestamp_sent": 1700000000,
        }
        converted = conv.convert_message_with_version_check(msg)
        assert converted["protocol_version"] == "0.1.0"


class TestHSPVersionedMessageHandler:
    def test_handle_versioned_message_returns_message(self):
        mgr = HSPVersionManager()
        conv = HSPVersionConverter(mgr)
        handler = HSPVersionedMessageHandler(mgr, conv)
        msg = {"message_id": "m1", "protocol_version": "0.1.0", "payload": {}}
        result = asyncio.run(handler.handle_versioned_message(msg))
        assert result["message_id"] == "m1"

    def test_rejects_unsupported_version(self):
        mgr = HSPVersionManager()
        conv = HSPVersionConverter(mgr)
        handler = HSPVersionedMessageHandler(mgr, conv)
        msg = {"message_id": "m1", "protocol_version": "9.9.9"}
        with pytest.raises(ValueError):
            asyncio.run(handler.handle_versioned_message(msg))


class TestHSPCompatibilityChecker:
    def test_check_message_compatibility(self):
        mgr = HSPVersionManager()
        checker = HSPCompatibilityChecker(mgr)
        result = checker.check_message_compatibility(
            {"protocol_version": "0.1.0"}, "0.1.0"
        )
        assert result["is_compatible"] is True

    def test_generate_compatibility_report(self):
        mgr = HSPVersionManager()
        checker = HSPCompatibilityChecker(mgr)
        report = checker.generate_compatibility_report(["0.1.0"])
        assert report["summary"]["compatibility_rate"] == 1.0
