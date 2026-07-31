# =============================================================================
# ANGELA-MATRIX: L3 δ A L5
# ED3N 確定性路由整合測試 — 驗證 math/logic/knowledge 擴充
# 透過 ED3NEngine.process() 實際走完整 stage 管線抵達確定性引擎，
# 鎖定「確擴充不會被 network stage 攔截或格式破壞」。
# =============================================================================

import pytest

from ai.ed3n.ed3n_engine import ED3NEngine


@pytest.fixture(scope="module")
def ed3n_engine() -> ED3NEngine:
    e = ED3NEngine()
    e.load_presets()
    return e


class TestED3NMathRouting:
    def test_math_expression(self, ed3n_engine: ED3NEngine):
        assert ed3n_engine.process("What is 6 * 7?") == "6 * 7 = 42"

    def test_math_number_theory(self, ed3n_engine: ED3NEngine):
        result = ed3n_engine.process("is 17 prime")
        assert "17" in result
        assert "prime" in result.lower()

    def test_math_function(self, ed3n_engine: ED3NEngine):
        result = ed3n_engine.process("sqrt(144)")
        assert "144" in result
        assert "12" in result


class TestED3NLogicRouting:
    @pytest.mark.parametrize(
        "query,expected",
        [
            ("true and false", "false"),
            ("true or false", "true"),
            ("not true", "false"),
            ("xor True True", "false"),
        ],
    )
    def test_logic_boolean(self, ed3n_engine: ED3NEngine, query: str, expected: str):
        assert ed3n_engine.process(query) == expected

    @pytest.mark.parametrize(
        "query,expected",
        [
            ("真或假", "true"),
            ("真且假", "false"),
            ("既不是真", "false"),
        ],
    )
    def test_logic_chinese(self, ed3n_engine: ED3NEngine, query: str, expected: str):
        assert ed3n_engine.process(query) == expected


class TestED3NKnowledgeRouting:
    def test_factual_knowledge(self, ed3n_engine: ED3NEngine):
        assert ed3n_engine.process("What color is the sky?") == "blue"

    def test_unit_conversion(self, ed3n_engine: ED3NEngine):
        result = ed3n_engine.process("how many m in a km")
        assert "1 m" in result
        assert "km" in result
