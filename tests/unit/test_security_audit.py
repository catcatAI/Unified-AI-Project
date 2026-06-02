"""Tests for core/security/security_audit.py"""
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
import pytest
import tempfile


class TestSecurityAudit:
    """Tests for SecurityAudit"""

    def test_import(self):
        from core.security.security_audit import SecurityAudit
        assert SecurityAudit is not None

    def test_instantiation_defaults(self):
        from core.security.security_audit import SecurityAudit
        instance = SecurityAudit()
        assert instance.project_root is not None
        assert "security_rules" in instance.__dict__

    def test_security_rules_defined(self):
        from core.security.security_audit import SecurityAudit
        instance = SecurityAudit()
        assert "hardcoded_secrets" in instance.security_rules
        assert "sql_injection" in instance.security_rules
        assert "command_injection" in instance.security_rules
        assert "weak_cryptography" in instance.security_rules

    def test_scan_file_detects_password(self):
        from core.security.security_audit import SecurityAudit
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write('password = "supersecret"\n')
            tmp = f.name
        try:
            instance = SecurityAudit()
            result = instance.scan_file(tmp)
            assert "vulnerabilities" in result
            vuln_types = [v["type"] for v in result["vulnerabilities"]]
            assert "hardcoded_secrets" in vuln_types
        finally:
            import os
            os.unlink(tmp)

    def test_scan_file_clean(self):
        from core.security.security_audit import SecurityAudit
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write('x = 1\n')
            tmp = f.name
        try:
            instance = SecurityAudit()
            result = instance.scan_file(tmp)
            assert len(result["vulnerabilities"]) == 0
        finally:
            import os
            os.unlink(tmp)

    def test_scan_file_not_found(self):
        from core.security.security_audit import SecurityAudit
        instance = SecurityAudit()
        result = instance.scan_file("nonexistent.py")
        assert "error" in result

    def test_calculate_security_score(self):
        from core.security.security_audit import SecurityAudit
        instance = SecurityAudit()
        vulns = {"critical": [{"type": "test"}], "high": [{"type": "test"}, {"type": "test"}], "medium": [], "low": []}
        score = instance._calculate_security_score(vulns)
        assert score == 100 - 20 - 20

    def test_generate_recommendations_critical(self):
        from core.security.security_audit import SecurityAudit
        instance = SecurityAudit()
        vulns = {"critical": [{"type": "hardcoded_secrets", "file": "x.py", "line": 1, "code": "pw"}]}
        recs = instance._generate_recommendations(vulns)
        assert len(recs) >= 2
