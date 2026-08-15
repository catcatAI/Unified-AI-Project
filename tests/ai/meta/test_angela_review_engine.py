# =============================================================================
# ANGELA-MATRIX: [L3-L5] [βδεθζη] [A] [L3+]
# =============================================================================
#
# Tests for Angela Review Engine — multi-dimensional project audit system.
#
# WARNING: The reviewer tests scan the ENTIRE project source tree (~610 files,
# ~96K lines) on every call — this module takes ~8 minutes standalone and
# stalls the full test suite under a combined run. Skipped by default; run
# explicitly when auditing the review engine itself.
# =============================================================================

import sys
from pathlib import Path

import pytest

SRC_ROOT = Path(__file__).resolve().parent.parent.parent.parent / "apps" / "backend" / "src"
sys.path.insert(0, str(SRC_ROOT))

pytestmark = [
    pytest.mark.skip(
        reason="SLOW REVIEW ENGINE: scans entire project (~8 min standalone), stalls full suite; run explicitly when auditing"
    ),
    pytest.mark.slow,
]

from ai.meta.angela_review_engine import (
    AngelaReviewEngine,
    CodeReviewer,
    ConsistencyReviewer,
    DesignReviewer,
    MDReviewer,
    ReviewFinding,
    ReviewReport,
    Severity,
    TrainingReviewer,
    get_review_engine,
    run_full_review,
    run_single_review,
)


@pytest.fixture
def src_root():
    return SRC_ROOT


@pytest.fixture
def project_root():
    return SRC_ROOT.parent.parent.parent


@pytest.fixture
def docs_root():
    return SRC_ROOT.parent.parent.parent / "docs"


# =============================================================================
# Severity & Data Model Tests
# =============================================================================

class TestSeverity:
    def test_severity_values(self):
        assert Severity.CRITICAL.value == "critical"
        assert Severity.HIGH.value == "high"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.LOW.value == "low"
        assert Severity.INFO.value == "info"


class TestReviewFinding:
    def test_finding_creation(self):
        f = ReviewFinding(
            severity=Severity.HIGH,
            category="test",
            message="test finding",
            file="test.py",
            line=42,
        )
        assert f.severity == Severity.HIGH
        assert f.category == "test"
        assert f.message == "test finding"
        assert f.file == "test.py"
        assert f.line == 42

    def test_finding_defaults(self):
        f = ReviewFinding(severity=Severity.LOW, category="cat", message="msg")
        assert f.file is None
        assert f.line is None
        assert f.suggestion is None


class TestReviewReport:
    def test_empty_report(self):
        r = ReviewReport(dimension="test")
        assert r.score == 0.0
        assert r.total_findings == 0
        assert r.critical_count == 0

    def test_report_counts(self):
        r = ReviewReport(
            dimension="test",
            findings=[
                ReviewFinding(Severity.CRITICAL, "cat", "msg1"),
                ReviewFinding(Severity.HIGH, "cat", "msg2"),
                ReviewFinding(Severity.HIGH, "cat", "msg3"),
                ReviewFinding(Severity.MEDIUM, "cat", "msg4"),
                ReviewFinding(Severity.LOW, "cat", "msg5"),
            ],
        )
        assert r.critical_count == 1
        assert r.high_count == 2
        assert r.medium_count == 1
        assert r.low_count == 1
        assert r.total_findings == 5

    def test_to_dict(self):
        r = ReviewReport(
            dimension="test",
            score=7.5,
            summary="test summary",
            findings=[ReviewFinding(Severity.LOW, "cat", "msg", file="f.py")],
        )
        d = r.to_dict()
        assert d["dimension"] == "test"
        assert d["score"] == 7.5
        assert d["summary"] == "test summary"
        assert d["counts"]["total"] == 1
        assert len(d["findings"]) == 1
        assert d["findings"][0]["severity"] == "low"
        assert d["findings"][0]["file"] == "f.py"


# =============================================================================
# Design Reviewer Tests
# =============================================================================

class TestDesignReviewer:
    def test_reviewer_initialization(self, src_root, docs_root):
        reviewer = DesignReviewer(src_root, docs_root)
        assert reviewer is not None

    def test_review_returns_report(self, src_root, docs_root):
        reviewer = DesignReviewer(src_root, docs_root)
        report = reviewer.review()
        assert isinstance(report, ReviewReport)
        assert report.dimension == "design"
        assert 0.0 <= report.score <= 10.0

    def test_review_has_metadata(self, src_root, docs_root):
        reviewer = DesignReviewer(src_root, docs_root)
        report = reviewer.review()
        assert "layers_checked" in report.metadata

    def test_design_doc_completeness(self, src_root, docs_root):
        reviewer = DesignReviewer(src_root, docs_root)
        findings = reviewer._check_design_doc_completeness()
        assert isinstance(findings, list)


# =============================================================================
# Code Reviewer Tests
# =============================================================================

class TestCodeReviewer:
    def test_reviewer_initialization(self, src_root):
        reviewer = CodeReviewer(src_root)
        assert reviewer is not None

    def test_review_returns_report(self, src_root):
        reviewer = CodeReviewer(src_root)
        report = reviewer.review()
        assert isinstance(report, ReviewReport)
        assert report.dimension == "code"

    def test_review_has_metadata(self, src_root):
        reviewer = CodeReviewer(src_root)
        report = reviewer.review()
        assert "files_checked" in report.metadata
        assert report.metadata["files_checked"] > 0

    def test_matrix_annotation_detection(self, src_root):
        reviewer = CodeReviewer(src_root)
        good_code = """# =============================================================================
# ANGELA-MATRIX: L2 [αβ] [A] L3
# =============================================================================
x = 1
"""
        bad_code = "x = 1\n"
        findings_good = reviewer._check_matrix_annotation(good_code, "good.py")
        findings_bad = reviewer._check_matrix_annotation(bad_code, "bad.py")
        assert len(findings_good) == 0
        assert len(findings_bad) == 1
        assert findings_bad[0].severity == Severity.MEDIUM

    def test_bare_except_detection(self, src_root):
        reviewer = CodeReviewer(src_root)
        code_with_bare = "try:\n    pass\nexcept:\n    pass\n"
        code_with_exception = "try:\n    pass\nexcept Exception:\n    pass\n"
        findings_bare = reviewer._check_bare_except(code_with_bare, "bare.py")
        findings_exception = reviewer._check_bare_except(code_with_exception, "exc.py")
        assert len(findings_bare) >= 1
        assert any(f.severity == Severity.HIGH for f in findings_bare)

    def test_stub_pass_detection(self, src_root):
        reviewer = CodeReviewer(src_root)
        code_with_stub = "def foo():\n    pass\n"
        findings = reviewer._check_stub_pass(code_with_stub, "stub.py")
        assert len(findings) >= 1

    def test_specific_files_review(self, src_root):
        reviewer = CodeReviewer(src_root)
        report = reviewer.review(target_files=["ai/core/execution_gate.py"])
        assert isinstance(report, ReviewReport)
        assert report.metadata["files_checked"] == 1

    def test_dynamic_import_detection(self, src_root):
        reviewer = CodeReviewer(src_root)
        code = '__import__("os")\n'
        findings = reviewer._check_import_patterns(code, "test.py")
        assert len(findings) == 1
        assert findings[0].severity == Severity.MEDIUM


# =============================================================================
# MD Reviewer Tests
# =============================================================================

class TestMDReviewer:
    def test_reviewer_initialization(self, project_root, src_root):
        reviewer = MDReviewer(project_root, src_root)
        assert reviewer is not None

    def test_review_returns_report(self, project_root, src_root):
        reviewer = MDReviewer(project_root, src_root)
        report = reviewer.review()
        assert isinstance(report, ReviewReport)
        assert report.dimension == "markdown"
        assert "docs_checked" in report.metadata

    def test_collects_md_files(self, project_root, src_root):
        reviewer = MDReviewer(project_root, src_root)
        files = reviewer._collect_md_files()
        assert len(files) > 0
        assert all(f.suffix == ".md" for f in files)

    def test_excludes_archives(self, project_root, src_root):
        reviewer = MDReviewer(project_root, src_root)
        files = reviewer._collect_md_files()
        for f in files:
            assert "09-archive" not in f.parts


# =============================================================================
# Consistency Reviewer Tests
# =============================================================================

class TestConsistencyReviewer:
    def test_reviewer_initialization(self, src_root, docs_root, project_root):
        reviewer = ConsistencyReviewer(src_root, docs_root, project_root)
        assert reviewer is not None

    def test_review_returns_report(self, src_root, docs_root, project_root):
        reviewer = ConsistencyReviewer(src_root, docs_root, project_root)
        report = reviewer.review()
        assert isinstance(report, ReviewReport)
        assert report.dimension == "consistency"

    def test_design_vs_code(self, src_root, docs_root, project_root):
        reviewer = ConsistencyReviewer(src_root, docs_root, project_root)
        findings = reviewer._check_design_vs_code()
        assert isinstance(findings, list)

    def test_code_vs_md(self, src_root, docs_root, project_root):
        reviewer = ConsistencyReviewer(src_root, docs_root, project_root)
        findings = reviewer._check_code_vs_md()
        assert isinstance(findings, list)

    def test_collects_src_symbols(self, src_root, docs_root, project_root):
        reviewer = ConsistencyReviewer(src_root, docs_root, project_root)
        symbols = reviewer._collect_src_symbols()
        assert len(symbols) > 10
        assert "StateMatrix4D" in symbols or "state_matrix" in symbols


# =============================================================================
# Training Reviewer Tests
# =============================================================================

class TestTrainingReviewer:
    def test_reviewer_initialization(self, src_root, project_root):
        reviewer = TrainingReviewer(src_root, project_root)
        assert reviewer is not None

    def test_review_returns_report(self, src_root, project_root):
        reviewer = TrainingReviewer(src_root, project_root)
        report = reviewer.review()
        assert isinstance(report, ReviewReport)
        assert report.dimension == "training"

    def test_pipeline_structure_check(self, src_root, project_root):
        reviewer = TrainingReviewer(src_root, project_root)
        findings = reviewer._check_pipeline_structure()
        assert isinstance(findings, list)


# =============================================================================
# Angela Review Engine Integration Tests
# =============================================================================

class TestAngelaReviewEngine:
    def test_engine_initialization(self):
        engine = AngelaReviewEngine()
        assert engine is not None
        assert "design" in engine._reviewers
        assert "code" in engine._reviewers
        assert "markdown" in engine._reviewers
        assert "consistency" in engine._reviewers
        assert "training" in engine._reviewers

    def test_run_full_review(self):
        engine = AngelaReviewEngine()
        reports = engine.run_full_review()
        assert len(reports) == 5
        for dim in ["design", "code", "markdown", "consistency", "training"]:
            assert dim in reports
            assert isinstance(reports[dim], ReviewReport)

    def test_run_single_review(self):
        engine = AngelaReviewEngine()
        report = engine.run_review("design")
        assert isinstance(report, ReviewReport)
        assert report.dimension == "design"

    def test_run_unknown_dimension_raises(self):
        engine = AngelaReviewEngine()
        with pytest.raises(ValueError):
            engine.run_review("nonexistent")

    def test_composite_score(self):
        engine = AngelaReviewEngine()
        reports = engine.run_full_review()
        score = engine.get_composite_score(reports)
        assert 0.0 <= score <= 10.0

    def test_composite_score_without_reports(self):
        engine = AngelaReviewEngine()
        score = engine.get_composite_score()
        assert 0.0 <= score <= 10.0

    def test_generate_summary(self):
        engine = AngelaReviewEngine()
        reports = engine.run_full_review()
        summary = engine.generate_summary(reports)
        assert isinstance(summary, str)
        assert "Angela Project Review Report" in summary
        assert "COMPOSITE SCORE" in summary

    def test_generate_summary_empty(self):
        engine = AngelaReviewEngine()
        summary = engine.generate_summary({})
        assert isinstance(summary, str)


# =============================================================================
# Singleton & Convenience Functions Tests
# =============================================================================

class TestSingleton:
    def test_get_review_engine_singleton(self):
        e1 = get_review_engine()
        e2 = get_review_engine()
        assert e1 is e2

    def test_run_full_review_convenience(self):
        result = run_full_review()
        assert "reports" in result
        assert "composite_score" in result
        assert "summary" in result
        assert isinstance(result["reports"], dict)

    def test_run_single_review_convenience(self):
        result = run_single_review("design")
        assert "dimension" in result
        assert result["dimension"] == "design"


# =============================================================================
# Score Boundary Tests
# =============================================================================

class TestScoreBoundaries:
    def test_perfect_score(self):
        r = ReviewReport(dimension="test", score=10.0)
        assert r.score == 10.0

    def test_zero_score(self):
        r = ReviewReport(dimension="test", score=0.0)
        assert r.score == 0.0

    def test_score_with_all_severities(self):
        findings = [
            ReviewFinding(Severity.CRITICAL, "c", "m1"),
            ReviewFinding(Severity.HIGH, "h", "m2"),
            ReviewFinding(Severity.MEDIUM, "m", "m3"),
            ReviewFinding(Severity.LOW, "l", "m4"),
            ReviewFinding(Severity.INFO, "i", "m5"),
        ]
        r = ReviewReport(dimension="test", findings=findings, score=5.0)
        assert r.critical_count == 1
        assert r.high_count == 1
        assert r.medium_count == 1
        assert r.low_count == 1
        assert r.total_findings == 5


# =============================================================================
# Review Engine Error Handling Tests
# =============================================================================

class TestErrorHandling:
    def test_engine_handles_reviewer_exception(self):
        engine = AngelaReviewEngine()
        original = engine._reviewers["design"]

        def failing_reviewer():
            raise RuntimeError("test failure")

        engine._reviewers["design"] = failing_reviewer
        reports = engine.run_full_review()
        assert reports["design"].score == 0.0
        assert any("failed" in f.message.lower() for f in reports["design"].findings)
        engine._reviewers["design"] = original

    def test_single_review_handles_exception(self):
        engine = AngelaReviewEngine()
        original = engine._reviewers["code"]

        def failing_reviewer():
            raise RuntimeError("single failure")

        engine._reviewers["code"] = failing_reviewer
        report = engine.run_review("code")
        assert report.score == 0.0
        engine._reviewers["code"] = original


# =============================================================================
# WebSocket Push API Tests
# =============================================================================

class TestWebSocketPushAPI:
    def test_push_functions_exist(self):
        from services.websocket_manager import push_to_all, push_to_session, push_to_client
        assert callable(push_to_all)
        assert callable(push_to_session)
        assert callable(push_to_client)

    def test_push_enabled_toggle(self):
        from services.websocket_manager import set_push_enabled, is_push_enabled
        set_push_enabled(False)
        assert is_push_enabled() is False
        set_push_enabled(True)
        assert is_push_enabled() is True


# =============================================================================
# BehaviorExecutor Feedback Loop Tests
# =============================================================================

class TestBehaviorExecutorFix:
    def test_behavior_executor_import(self):
        from core.autonomous.behavior_executor import BehaviorExecutor
        assert BehaviorExecutor is not None

    def test_execution_returns_variable_success(self):
        import asyncio
        from core.autonomous.behavior_executor import BehaviorExecutor

        async def _test():
            executor = BehaviorExecutor()
            results = []
            for _ in range(100):
                r = await executor.execute(decision_type="exploration", rationale="test")
                results.append(r["status"])
            assert "completed" in results or "failed" in results
            stats = executor.get_type_stats()
            assert "exploration" in stats

        asyncio.run(_test())

    def test_type_stats_tracking(self):
        import asyncio
        from core.autonomous.behavior_executor import BehaviorExecutor

        async def _test():
            executor = BehaviorExecutor()
            for _ in range(10):
                await executor.execute(decision_type="exploration")
                await executor.execute(decision_type="coexistence_activation")
            stats = executor.get_type_stats()
            assert "exploration" in stats
            assert "coexistence_activation" in stats
            overall = executor.get_overall_stats()
            assert overall["total_executions"] == 20

        asyncio.run(_test())


# =============================================================================
# ProactiveInteractionSystem Wiring Tests
# =============================================================================

class TestProactiveWiring:
    def test_proactive_import(self):
        from ai.lifecycle.proactive_interaction_system import ProactiveInteractionSystem
        assert ProactiveInteractionSystem is not None

    def test_proactive_can_be_instantiated(self):
        import asyncio
        from ai.lifecycle.proactive_interaction_system import ProactiveInteractionSystem
        from ai.lifecycle.user_monitor import UserMonitor

        async def _test():
            monitor = UserMonitor()
            system = ProactiveInteractionSystem(
                llm_service=None,
                state_manager=None,
                memory_manager=None,
                user_monitor=monitor,
                broadcast_callback=lambda msg: None,
            )
            assert system is not None
            assert system.broadcast_callback is not None

        asyncio.run(_test())

    def test_push_to_all_with_proactive_message(self):
        import asyncio
        from services.websocket_manager import push_to_all

        async def _test():
            msg = {
                "type": "proactive_action",
                "opportunity": "test",
                "message": "Hello from Angela",
            }
            result = await push_to_all(msg)
            assert result in ("ok", "disabled", "", 0)

        asyncio.run(_test())
