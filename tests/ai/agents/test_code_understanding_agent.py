# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""CodeUnderstandingAgent 行為測試（此前僅 smoke import，無行為覆蓋）。"""

from ai.agents.specialized.code_understanding_agent import CodeUnderstandingAgent


def _agent():
    return CodeUnderstandingAgent()


def test_analyze_code_counts_lines_and_parses():
    result = _agent().analyze_code("x = 1\ny = 2\n", "python")
    assert result["line_count"] == 2
    assert result["language"] == "python"
    assert result["has_syntax_errors"] is False


def test_analyze_code_empty_is_error():
    result = _agent().analyze_code("", "python")
    assert result["status"] == "error"
    assert result["line_count"] == 0


def test_analyze_code_flags_syntax_error():
    result = _agent().analyze_code("def broken(:\n", "python")
    assert result["has_syntax_errors"] is True


def test_code_review_empty_is_error():
    result = _agent().code_review("", "python")
    assert result["status"] == "error"
    assert result["issues"] == []


def test_explain_code_empty_is_error():
    result = _agent().explain_code("")
    assert result["status"] == "error"
    assert result["purpose"] == ""
