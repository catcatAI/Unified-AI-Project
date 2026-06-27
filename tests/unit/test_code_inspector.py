"""Tests for apps.backend.src.ai.code_inspection.code_inspector"""
import pytest


class TestCodeInspector:
    def test_import(self):
        from ai.code_inspection.code_inspector import CodeInspector
        assert CodeInspector is not None

    def test_instantiation(self):
        from ai.code_inspection.code_inspector import CodeInspector
        instance = CodeInspector(root_path=".")
        assert instance is not None
        assert hasattr(instance, "scan")
        assert hasattr(instance, "root_path")

    def test_pattern_matcher_rules(self):
        from ai.code_inspection.code_inspector import IssueCategory, PatternMatcher, Severity
        PatternMatcher.init_rules()
        assert len(PatternMatcher.RULES) > 0
        rule = PatternMatcher.RULES[0]
        assert hasattr(rule, "pattern")
        assert hasattr(rule, "severity")
        assert hasattr(rule, "category")
        assert hasattr(rule, "confidence")

    def test_issue_category_enum(self):
        from ai.code_inspection.code_inspector import IssueCategory
        assert IssueCategory.TYPE is not None
        assert IssueCategory.SECURITY is not None
        assert IssueCategory.LOGIC is not None
        assert IssueCategory.STYLE is not None
        assert IssueCategory.CONSISTENCY is not None
        assert IssueCategory.DEPRECATION is not None

    def test_severity_enum(self):
        from ai.code_inspection.code_inspector import Severity
        assert Severity.CRITICAL is not None
        assert Severity.HIGH is not None
        assert Severity.MEDIUM is not None
        assert Severity.LOW is not None

    def test_ast_inspector(self):
        from ai.code_inspection.code_inspector import ASTInspector
        inspector = ASTInspector(__file__)
        assert inspector.parse() is True
        assert inspector.tree is not None
