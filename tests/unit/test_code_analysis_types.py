"""Tests for ai.code_understanding.code_analysis_types"""
from datetime import datetime
import pytest

class TestCodeAnalysisResult:
    def test_import(self):
        from ai.code_understanding.code_analysis_types import CodeAnalysisResult
        assert CodeAnalysisResult is not None
        assert callable(CodeAnalysisResult)

    def test_instantiation(self):
        from ai.code_understanding.code_analysis_types import CodeAnalysisResult
        instance = CodeAnalysisResult(filepath="test.py", analysis_timestamp=datetime.now())
        assert instance.filepath == "test.py"
        assert instance.complexity_score == 0.0
        assert instance.classes == []
        assert instance.functions == []
        assert instance.dependencies == []
        assert instance.dna_chain_id is None

    def test_instantiation_with_all_fields(self):
        from ai.code_understanding.code_analysis_types import CodeAnalysisResult
        ts = datetime(2026, 1, 1, 12, 0, 0)
        instance = CodeAnalysisResult(
            filepath="/src/main.py",
            analysis_timestamp=ts,
            classes=[{"name": "Foo"}],
            functions=[{"name": "bar"}],
            dependencies=["os", "sys"],
            complexity_score=3.5,
            dna_chain_id="chain-001",
        )
        assert instance.filepath == "/src/main.py"
        assert instance.analysis_timestamp == ts
        assert len(instance.classes) == 1
        assert len(instance.functions) == 1
        assert "os" in instance.dependencies
        assert instance.complexity_score == 3.5
        assert instance.dna_chain_id == "chain-001"

    def test_default_complexity_is_zero(self):
        from ai.code_understanding.code_analysis_types import CodeAnalysisResult
        instance = CodeAnalysisResult(filepath="a.py", analysis_timestamp=datetime.now())
        assert instance.complexity_score == 0.0
        assert isinstance(instance.complexity_score, float)

    def test_dna_chain_id_optional(self):
        from ai.code_understanding.code_analysis_types import CodeAnalysisResult
        r1 = CodeAnalysisResult(filepath="a.py", analysis_timestamp=datetime.now(), dna_chain_id="abc")
        r2 = CodeAnalysisResult(filepath="b.py", analysis_timestamp=datetime.now())
        assert r1.dna_chain_id == "abc"
        assert r2.dna_chain_id is None
