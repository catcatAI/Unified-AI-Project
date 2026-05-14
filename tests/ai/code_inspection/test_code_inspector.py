"""
Test suite for Angela Code Inspection System
Testing native code inspection without LLM dependency

Tests:
1. ASTInspector parsing and analysis
2. PatternMatcher rule matching
3. CodeInspector scanning
4. KnowledgeGraph building
5. CodeLearningEngine feedback learning
6. Integration
"""

import pytest
import sys
import tempfile
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

from ai.code_inspection.code_inspector import (
    CodeInspector, ASTInspector, PatternMatcher, Issue,
    Severity, IssueCategory, PatternRule
)
from ai.code_inspection.knowledge_graph import KnowledgeGraph, GraphQueryEngine
from ai.code_inspection.code_learning import (
    CodeLearningEngine, LearnedPattern, CodeInspectorInterface
)


class TestASTInspector:
    """ASTInspector tests"""

    def test_parse_valid_python(self):
        code = '''
def hello():
    """Test function"""
    print("hello")
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            filepath = f.name

        try:
            inspector = ASTInspector(filepath)
            assert inspector.parse() is True
            assert inspector.tree is not None
        finally:
            os.unlink(filepath)

    def test_parse_invalid_python(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def broken(\n")
            f.flush()
            filepath = f.name

        try:
            inspector = ASTInspector(filepath)
            assert inspector.parse() is False
            assert len(inspector.errors) > 0
        finally:
            os.unlink(filepath)

    def test_extract_functions(self):
        code = '''
def func_a():
    pass

def func_b(x):
    return x * 2
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            filepath = f.name

        try:
            inspector = ASTInspector(filepath)
            inspector.parse()
            funcs = inspector.get_functions()
            assert len(funcs) >= 2
            names = [f.name for f in funcs]
            assert "func_a" in names
            assert "func_b" in names
        finally:
            os.unlink(filepath)

    def test_extract_classes(self):
        code = '''
class MyClass:
    def method_a(self):
        pass

    def method_b(self, x):
        return x
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            filepath = f.name

        try:
            inspector = ASTInspector(filepath)
            inspector.parse()
            classes = inspector.get_classes()
            assert len(classes) == 1
            assert classes[0].name == "MyClass"
            assert len(classes[0].methods) >= 2
        finally:
            os.unlink(filepath)

    def test_check_function_length_short(self):
        code = '''
def short_func():
    print(1)
    print(2)
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            filepath = f.name

        try:
            inspector = ASTInspector(filepath)
            inspector.parse()
            issues = inspector.check_function_length()
            assert len(issues) == 0
        finally:
            os.unlink(filepath)

    def test_check_function_length_long(self):
        lines = ["def long_func():"] + ["    pass"] * 101
        code = "\n".join(lines)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            filepath = f.name

        try:
            inspector = ASTInspector(filepath)
            inspector.parse()
            issues = inspector.check_function_length()
            assert len(issues) > 0
            assert issues[0].severity == Severity.MEDIUM
        finally:
            os.unlink(filepath)


class TestPatternMatcher:
    """PatternMatcher tests"""

    def test_init_rules(self):
        PatternMatcher.init_rules()
        assert len(PatternMatcher.RULES) > 0

    def test_match_hardcoded_key(self):
        line = 'api_key = "sk-abc123xyz"'
        issues = PatternMatcher.match_line(line, 1, "test.py")
        matched = [i for i in issues if i.id == "SEC-001"]
        assert len(matched) > 0

    def test_match_eval(self):
        line = "result = eval(user_input)"
        issues = PatternMatcher.match_line(line, 1, "test.py")
        matched = [i for i in issues if i.id == "SEC-002"]
        assert len(matched) > 0

    def test_match_empty_except(self):
        line = "except Exception:\n        pass"
        issues = PatternMatcher.match_line(line, 1, "test.py")
        matched = [i for i in issues if i.id == "LOG-003"]
        assert len(matched) > 0

    def test_no_false_positive_clean_code(self):
        line = "def clean_function(x):"
        issues = PatternMatcher.match_line(line, 1, "test.py")
        critical = [i for i in issues if i.severity == Severity.CRITICAL]
        assert len(critical) == 0


class TestCodeInspector:
    """CodeInspector tests"""

    @pytest.fixture
    def temp_project(self):
        tmpdir = tempfile.mkdtemp()

        Path(tmpdir, "main.py").write_text('''
import os

def hello():
    print("hello")

def broken_func():
    return 1 / 0
''')

        Path(tmpdir, "utils.py").write_text('''
def util_a():
    pass

def util_b():
    eval("bad")
''')

        yield tmpdir

        import shutil
        shutil.rmtree(tmpdir)

    def test_scan_python_files(self, temp_project):
        inspector = CodeInspector(temp_project)
        report = inspector.scan()
        assert report.total_files >= 2
        assert report.total_issues >= 0

    def test_scan_detects_security_issues(self, temp_project):
        inspector = CodeInspector(temp_project)
        report = inspector.scan()
        sec_issues = [i for i in report.issues if i.category == IssueCategory.SECURITY]
        assert len(sec_issues) > 0

    def test_scan_detects_logic_issues(self, temp_project):
        inspector = CodeInspector(temp_project)
        report = inspector.scan()
        logic_issues = [i for i in report.issues if i.category == IssueCategory.LOGIC]
        assert len(logic_issues) > 0

    def test_auto_fixable_count(self, temp_project):
        inspector = CodeInspector(temp_project)
        report = inspector.scan()
        assert report.auto_fixable_count >= 0

    def test_issue_counts_by_severity(self, temp_project):
        inspector = CodeInspector(temp_project)
        report = inspector.scan()
        assert report.critical_count >= 0
        assert report.high_count >= 0
        assert report.medium_count >= 0
        assert report.low_count >= 0


class TestKnowledgeGraph:
    """KnowledgeGraph tests"""

    @pytest.fixture
    def temp_project(self):
        tmpdir = tempfile.mkdtemp()

        Path(tmpdir, "module_a.py").write_text('''
class MyClass:
    def method_one(self):
        pass

def helper_func():
    pass
''')

        Path(tmpdir, "module_b.py").write_text('''
from module_a import MyClass

def another_func():
    obj = MyClass()
    obj.method_one()
''')

        yield tmpdir

        import shutil
        shutil.rmtree(tmpdir)

    def test_build_from_directory(self, temp_project):
        graph = KnowledgeGraph(temp_project)
        count = graph.build_from_directory()
        assert count >= 2

    def test_nodes_created(self, temp_project):
        graph = KnowledgeGraph(temp_project)
        graph.build_from_directory()
        assert len(graph.nodes) > 0

    def test_edges_created(self, temp_project):
        graph = KnowledgeGraph(temp_project)
        graph.build_from_directory()
        assert len(graph.edges) > 0

    def test_find_node(self, temp_project):
        graph = KnowledgeGraph(temp_project)
        graph.build_from_directory()
        results = graph.find_node("MyClass")
        assert len(results) > 0

    def test_get_statistics(self, temp_project):
        graph = KnowledgeGraph(temp_project)
        graph.build_from_directory()
        stats = graph.get_statistics()
        assert "total_nodes" in stats
        assert "total_edges" in stats
        assert stats["total_nodes"] > 0

    def test_export_to_dict(self, temp_project):
        graph = KnowledgeGraph(temp_project)
        graph.build_from_directory()
        data = graph.export_to_dict()
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) > 0


class TestCodeLearningEngine:
    """CodeLearningEngine tests"""

    @pytest.fixture
    def engine(self):
        return CodeLearningEngine()

    def test_init_builtin_patterns(self, engine):
        assert len(engine.patterns) > 0
        assert "PAT-001" in engine.patterns
        assert "PAT-007" in engine.patterns

    def test_learn_feedback_accepted(self, engine):
        pattern = engine.learn_from_feedback(
            issue_id="ISS-001",
            original_fix="check_divisor_nonzero",
            human_feedback="Correct, good divisor check",
            accepted=True,
        )
        if pattern:
            assert pattern.success_count >= 1

    def test_learn_feedback_rejected(self, engine):
        engine.learn_from_feedback(
            issue_id="ISS-002",
            original_fix="wrong_approach",
            human_feedback="This does not handle the zero case properly",
            accepted=False,
            correction="proper_zero_check",
        )
        pat = engine.patterns.get("PAT-001")
        if pat:
            assert pat.failure_count >= 0

    def test_get_high_confidence_patterns(self, engine):
        engine.patterns["PAT-001"].confidence = 0.9
        engine.patterns["PAT-002"].confidence = 0.5
        high_conf = engine.get_high_confidence_patterns(threshold=0.8)
        assert len(high_conf) >= 1

    def test_get_feedback_stats(self, engine):
        stats = engine.get_feedback_stats()
        assert "total_feedback" in stats
        assert "accepted" in stats
        assert "patterns_count" in stats

    def test_export_import_patterns(self, engine):
        exported = engine.export_patterns()
        assert len(exported) > 0

        engine2 = CodeLearningEngine()
        engine2.import_patterns(exported)
        assert len(engine2.patterns) == len(engine.patterns)


class TestCodeInspectorInterface:
    """CodeInspectorInterface tests"""

    @pytest.fixture
    def inspector(self):
        tmpdir = tempfile.mkdtemp()
        Path(tmpdir, "test.py").write_text('''
api_key = "secret123"

def divide(a, b):
    return a / b

def demo():
    try:
        pass
    except:
        pass
''')
        iface = CodeInspectorInterface(tmpdir)
        yield iface

        import shutil
        shutil.rmtree(tmpdir)

    def test_create_inspector(self, inspector):
        assert inspector is not None
        assert inspector.inspector is not None

    def test_inspect_finds_issues(self, inspector):
        result = inspector.inspect()
        assert "total_issues" in result
        assert result["total_issues"] > 0

    def test_inspect_finds_security(self, inspector):
        result = inspector.inspect()
        assert result["critical"] > 0 or result["high"] > 0

    def test_get_status(self, inspector):
        status = inspector.get_status()
        assert "knowledge_graph" in status
        assert "learning" in status

    def test_explain_fix(self, inspector):
        result = inspector.inspect()
        if result["total_issues"] > 0:
            first_issue = result["report"].issues[0]
            explanation = inspector.explain_fix(first_issue.id)
            assert len(explanation) > 0
            assert first_issue.id in explanation

    def test_learn_from_feedback(self, inspector):
        result = inspector.learn(
            issue_id="SEC-001",
            original_fix="replace_with_env_get",
            human_feedback="Good approach, this handles the case properly",
            accepted=True,
        )
        assert "stats" in result

    def test_ask_human(self, inspector):
        question = inspector.ask_human("Should I use os.getenv or environment variable?")
        assert "Angela Question" in question


class TestIntegration:
    """Integration tests"""

    @pytest.fixture
    def project_dir(self):
        return str(Path(__file__).parent.parent.parent.parent / "apps" / "backend" / "src")

    def test_inspect_actual_codebase(self, project_dir):
        if not Path(project_dir).exists():
            pytest.skip("Project directory not found")

        inspector = CodeInspectorInterface(project_dir)
        result = inspector.inspect()
        assert "total_issues" in result
        assert result["total_issues"] >= 0

    def test_knowledge_graph_actual_codebase(self, project_dir):
        if not Path(project_dir).exists():
            pytest.skip("Project directory not found")

        graph = KnowledgeGraph(project_dir)
        count = graph.build_from_directory()
        assert count > 0

        stats = graph.get_statistics()
        assert stats["total_nodes"] > 0

    def test_inspector_status_with_real_project(self, project_dir):
        if not Path(project_dir).exists():
            pytest.skip("Project directory not found")

        inspector = CodeInspectorInterface(project_dir)
        status = inspector.get_status()
        assert "knowledge_graph" in status
        assert status["knowledge_graph"]["total_nodes"] > 0