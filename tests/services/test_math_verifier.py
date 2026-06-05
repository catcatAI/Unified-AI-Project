import json
import pytest
try:
    from apps.backend.src.services.math_verifier import (
        MathExtractor,
        SpatialEngine,
        MathVerifier,
        ExtractionResult,
        VerificationResult,
    )
except ImportError:
    pytest.skip("MathVerifier not available (stub module)", allow_module_level=True)


class TestExtractionResult:
    def test_defaults(self):
        r = ExtractionResult()
        assert r.expression is None
        assert r.understanding is None
        assert r.assumptions == []
        assert r.confidence == 0.0
        assert r.llm_answer is None
        assert r.is_valid is False

    def test_fields(self):
        r = ExtractionResult(
            expression="1+1",
            understanding="add",
            assumptions=["a"],
            confidence=0.9,
            llm_answer=2.0,
            is_valid=True,
        )
        assert r.expression == "1+1"
        assert r.understanding == "add"
        assert r.confidence == 0.9


class TestVerificationResult:
    def test_defaults(self):
        r = VerificationResult(expression="")
        assert r.llm_answer is None
        assert r.engine_answer is None
        assert r.matches is False
        assert r.discrepancy == 0.0

    def test_mixed_fields(self):
        r = VerificationResult(
            expression="2*3",
            llm_answer=6.0,
            engine_answer=6.0,
            matches=True,
        )
        assert r.final_answer is None
        assert r.needs_clarification is False


class TestMathExtractor:
    def test_contains_likely_math_empty(self):
        m = MathExtractor()
        assert m._contains_likely_math("hello world") is False

    def test_contains_likely_math_operators(self):
        m = MathExtractor()
        assert m._contains_likely_math("1+1") is True

    def test_contains_likely_math_keywords(self):
        m = MathExtractor()
        assert m._contains_likely_math("多少錢") is True
        assert m._contains_likely_math("計算一下") is True

    def test_contains_likely_math_units(self):
        m = MathExtractor()
        assert m._contains_likely_math("100元") is True

    def test_contains_likely_math_subtract(self):
        m = MathExtractor()
        assert m._contains_likely_math("花了") is True

    def test_safe_float_none(self):
        m = MathExtractor()
        assert m._safe_float(None) is None

    def test_safe_float_invalid(self):
        m = MathExtractor()
        assert m._safe_float("abc") is None

    def test_safe_float_valid(self):
        m = MathExtractor()
        assert m._safe_float("3.14") == 3.14
        assert m._safe_float(42) == 42.0

    def test_fallback_extract_expression_simple(self):
        m = MathExtractor()
        r = m._fallback_extract_expression("計算 3*299")
        assert r == "3*299"

    def test_fallback_extract_expression_with_cjk_multiply(self):
        m = MathExtractor()
        r = m._fallback_extract_expression("3×4")
        assert r == "3*4"

    def test_fallback_extract_expression_with_cjk_divide(self):
        m = MathExtractor()
        r = m._fallback_extract_expression("10÷2")
        assert r == "10/2"

    def test_fallback_extract_expression_parenthesized(self):
        m = MathExtractor()
        r = m._fallback_extract_expression("計算 (-3.5)")
        assert r == "(-3.5)"

    def test_fallback_extract_expression_no_math(self):
        m = MathExtractor()
        r = m._fallback_extract_expression("你好世界")
        assert r is None

    def test_parse_chinese_word_problem_subtract(self):
        m = MathExtractor()
        r = m._parse_chinese_word_problem("小明吃了3個蘋果，還剩5個")
        assert r == "3-5"

    def test_parse_chinese_word_problem_pow(self):
        m = MathExtractor()
        r = m._parse_chinese_word_problem("2的3次方")
        assert r == "2**3"

    def test_parse_chinese_word_problem_add(self):
        m = MathExtractor()
        r = m._parse_chinese_word_problem("又買了3個，加上5個")
        assert r == "3+5"

    def test_parse_chinese_word_problem_multiply(self):
        m = MathExtractor()
        r = m._parse_chinese_word_problem("3倍5")
        assert r == "3*5"

    def test_parse_chinese_word_problem_few_numbers(self):
        m = MathExtractor()
        r = m._parse_chinese_word_problem("只有一個數字3")
        assert r is None

    def test_fallback_extract_no_math(self):
        m = MathExtractor()
        r = m._fallback_extract("hello")
        assert json.loads(r) == {"is_math": False}

    def test_fallback_extract_with_expression(self):
        m = MathExtractor()
        r = json.loads(m._fallback_extract("1+1"))
        assert r["expression"] == "1+1"
        assert r["confidence"] == 0.3

    async def test_extract_fallback_path_non_math(self):
        m = MathExtractor()
        r = await m.extract("hello world")
        assert r.is_valid is False
        assert r.expression is None

    async def test_extract_fallback_path_valid_expression(self):
        m = MathExtractor()
        r = await m.extract("計算 3*299")
        assert r.is_valid is True
        assert r.expression == "3*299"
        assert r.confidence == 0.3

    async def test_extract_fallback_path_chinese_word_problem(self):
        m = MathExtractor()
        r = await m.extract("剩下3個蘋果，吃了5個")
        assert r.is_valid is True
        assert r.expression == "3-5"
        assert r.confidence == 0.3

    async def test_extract_fallback_path_json_malformed(self):
        m = MathExtractor()
        r = await m.extract("abc {broken json} def")
        assert r.is_valid is False


class TestSpatialEngine:
    def test_evaluate_empty(self):
        e = SpatialEngine()
        r, ok = e.evaluate("")
        assert ok is False
        assert r == 0.0

    def test_whitespace_only(self):
        e = SpatialEngine()
        r, ok = e.evaluate("   ")
        assert ok is False

    def test_eval_simple_addition(self):
        e = SpatialEngine()
        r, ok = e.evaluate("1+2")
        assert ok is True
        assert r == 3.0

    def test_eval_simple_complex(self):
        e = SpatialEngine()
        r, ok = e.evaluate("(3+5)*2")
        assert ok is True
        assert r == 16.0

    def test_eval_simple_division(self):
        e = SpatialEngine()
        r, ok = e.evaluate("10/4")
        assert ok is True
        assert r == 2.5

    def test_eval_simple_invalid_chars(self):
        e = SpatialEngine()
        r, ok = e.evaluate("1+abc")
        assert ok is False
        assert r == 0.0

    def test_eval_simple_all_invalid(self):
        e = SpatialEngine()
        r, ok = e.evaluate("abc")
        assert ok is True
        assert r == 0.0

    def test_caching(self):
        e = SpatialEngine()
        r1, ok1 = e.evaluate("2+2")
        r2, ok2 = e.evaluate("2+2")
        assert ok1 is True
        assert ok2 is True
        assert r1 == 4.0
        assert r2 == 4.0
        assert len(e._local_cache) == 1

    def test_no_side_effects(self):
        e = SpatialEngine()
        r, ok = e.evaluate("__import__('os')")
        assert ok is False
        assert r == 0.0

    def test_evaluate_sql_injection_attempt(self):
        e = SpatialEngine()
        r, ok = e.evaluate("1; DROP TABLE")
        assert ok is True
        assert r == 1.0


class TestMathVerifier:
    def test_is_math_message(self):
        v = MathVerifier()
        assert v.is_math_message("多少錢") is True
        assert v.is_math_message("hello") is False

    def test_build_clarification_no_assumptions(self):
        v = MathVerifier()
        r = v._build_clarification("計算總價", [], "小明")
        assert "小明" in r
        assert "計算總價" in r

    def test_build_clarification_one_assumption(self):
        v = MathVerifier()
        r = v._build_clarification("計算總價", ["單價100"], "小明")
        assert "單價100" in r

    def test_build_clarification_two_assumptions(self):
        v = MathVerifier()
        r = v._build_clarification("計算總價", ["單價100", "數量5"], "小明")
        assert "單價100" in r
        assert "還是" in r
        assert "數量5" in r

    def test_build_clarification_many_assumptions(self):
        v = MathVerifier()
        r = v._build_clarification(
            "計算總價",
            ["a", "b", "c"],
            "小明",
        )
        assert "複雜" in r or "是這個意思" in r

    def test_build_response_clarification_needed(self):
        v = MathVerifier()
        result = VerificationResult(expression="1+1", needs_clarification=True)
        result.clarification_question = "確認問題"
        ext = ExtractionResult()
        r = v._build_response(result, ext, "小明")
        assert r == "確認問題"

    def test_build_response_no_answer(self):
        v = MathVerifier()
        result = VerificationResult(expression="1+1")
        ext = ExtractionResult()
        r = v._build_response(result, ext, "小明")
        assert r == ""

    def test_build_response_matches_high_conf(self):
        v = MathVerifier()
        result = VerificationResult(expression="1+1", final_answer=2.0, matches=True)
        ext = ExtractionResult(confidence=0.9)
        r = v._build_response(result, ext, "小明")
        assert "2.0" in r

    def test_build_response_matches_low_conf(self):
        v = MathVerifier()
        result = VerificationResult(expression="1+1", final_answer=2.0, matches=True)
        ext = ExtractionResult(confidence=0.5)
        r = v._build_response(result, ext, "小明")
        assert "算了一下" in r

    def test_build_response_mismatch(self):
        v = MathVerifier()
        result = VerificationResult(
            expression="1+1", final_answer=3.0, matches=False
        )
        ext = ExtractionResult(confidence=0.9)
        r = v._build_response(result, ext, "小明")
        assert "不對" in r
        assert "3.0" in r

    async def test_verify_non_math_message(self):
        v = MathVerifier()
        r = await v.verify("hello world")
        assert r.expression == ""
        assert r.extraction is not None
        assert r.extraction.is_valid is False

    async def test_verify_fallback_valid(self):
        v = MathVerifier()
        r = await v.verify("計算 3*299")
        assert r.expression == "3*299"
        assert r.extraction.is_valid is True
        assert r.extraction.confidence == 0.3

    async def test_verify_engine_computes(self):
        v = MathVerifier()
        r = await v.verify("計算 2+3")
        assert r.engine_answer == 5.0
        assert r.final_answer == 5.0

    async def test_verify_no_clarification_for_fallback(self):
        v = MathVerifier()
        r = await v.verify("計算 1+1")
        assert r.needs_clarification is False
