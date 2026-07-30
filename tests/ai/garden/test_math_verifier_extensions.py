# =============================================================================
# ANGELA-MATRIX: [L2] [γ] [C] [L4]
# =============================================================================
"""Tests for deterministic engine extensions (trig, constants, logic, KB)."""

import math
import pytest

from services.math_verifier import (
    evaluate_math,
    evaluate_logic,
    MathExtractor,
    _SAFE_FUNCTIONS,
    _MATH_CONSTANTS,
    _is_prime,
    _gcd,
)
from ai.knowledge_base import route_knowledge, _UNIT_CONVERSIONS, _CHEMICAL_FORMULAS


class TestSafeFunctions:
    def test_sin_zero(self):
        assert _SAFE_FUNCTIONS["sin"](0) == 0.0

    def test_cos_pi(self):
        assert abs(_SAFE_FUNCTIONS["cos"](math.pi) - (-1.0)) < 1e-10

    def test_sqrt_144(self):
        assert _SAFE_FUNCTIONS["sqrt"](144) == 12.0

    def test_log(self):
        assert _SAFE_FUNCTIONS["log"](1) == 0.0

    def test_factorial_5(self):
        assert _SAFE_FUNCTIONS["factorial"](5) == 120

    def test_abs_neg(self):
        assert _SAFE_FUNCTIONS["abs"](-5) == 5

    def test_all_functions_present(self):
        expected = {"sin", "cos", "tan", "sqrt", "log", "factorial", "abs", "floor", "ceil", "exp"}
        assert expected.issubset(_SAFE_FUNCTIONS.keys())


class TestMathConstants:
    def test_pi(self):
        assert _MATH_CONSTANTS["pi"][1] == math.pi

    def test_e(self):
        assert _MATH_CONSTANTS["e"][1] == math.e


class TestNumberTheory:
    def test_is_prime_17(self):
        assert _is_prime(17) is True

    def test_is_prime_1(self):
        assert _is_prime(1) is False

    def test_is_prime_0(self):
        assert _is_prime(0) is False

    def test_is_prime_negative(self):
        assert _is_prime(-7) is False

    def test_is_prime_composite(self):
        assert _is_prime(15) is False

    def test_gcd(self):
        assert _gcd(12, 18) == 6

    def test_gcd_coprime(self):
        assert _gcd(7, 13) == 1


class TestMathExtractorFunctionCalls:
    def test_extract_sin(self):
        result = MathExtractor().extract("sin(0)")
        assert result is not None
        expr, val = result
        assert val == 0.0

    def test_extract_sqrt(self):
        result = MathExtractor().extract("sqrt(144)")
        assert result is not None
        expr, val = result
        assert val == 12.0

    def test_extract_composite(self):
        result = MathExtractor().extract("sin(0) + cos(0)")
        assert result is not None
        expr, val = result
        assert abs(val - 1.0) < 1e-10


class TestEvaluateMathConstants:
    def test_what_is_pi(self):
        result = evaluate_math("what is pi")
        assert result is not None
        assert abs(float(result.split("=")[1].strip()) - math.pi) < 1e-10

    def test_value_of_e(self):
        result = evaluate_math("value of e")
        assert result is not None
        assert abs(float(result.split("=")[1].strip()) - math.e) < 1e-10

    def test_pi_symbol(self):
        result = evaluate_math("π")
        assert result is not None
        assert abs(float(result.split("=")[1].strip()) - math.pi) < 1e-10


class TestEvaluateMathNumberTheory:
    def test_is_17_prime(self):
        result = evaluate_math("is 17 prime")
        assert result is not None
        assert "true" in result.lower()

    def test_is_15_prime(self):
        result = evaluate_math("is 15 prime")
        assert result is not None
        assert "false" in result.lower()

    def test_gcd(self):
        result = evaluate_math("gcd 12 18")
        assert result is not None
        assert result == "gcd(12, 18) = 6"

    def test_lcm(self):
        result = evaluate_math("lcm 6 8")
        assert result is not None
        assert result == "lcm(6, 8) = 24"


class TestEvaluateMathTrig:
    def test_sin_zero(self):
        result = evaluate_math("sin(0)")
        assert result is not None
        val = float(result.split("=")[1].strip())
        assert abs(val) < 1e-10

    def test_cos_zero(self):
        result = evaluate_math("cos(0)")
        assert result is not None
        val = float(result.split("=")[1].strip())
        assert abs(val - 1.0) < 1e-10

    def test_sqrt_144(self):
        result = evaluate_math("sqrt(144)")
        assert result is not None
        val = float(result.split("=")[1].strip())
        assert abs(val - 12.0) < 1e-10

    def test_factorial_5(self):
        result = evaluate_math("factorial(5)")
        assert result is not None
        val = float(result.split("=")[1].strip())
        assert abs(val - 120.0) < 1e-10


class TestEvaluateLogicEnglish:
    def test_true_and_false(self):
        assert evaluate_logic("true and false") == "false"

    def test_true_or_false(self):
        assert evaluate_logic("true or false") == "true"

    def test_not_true(self):
        assert evaluate_logic("not true") == "false"

    def test_nor_true_false(self):
        assert evaluate_logic("nor True False") == "false"

    def test_nand_true_true(self):
        assert evaluate_logic("nand True True") == "false"

    def test_xor_true_false(self):
        assert evaluate_logic("xor True False") == "true"

    def test_xor_true_true(self):
        assert evaluate_logic("xor True True") == "false"

    def test_complex(self):
        result = evaluate_logic("(true and false) or true")
        assert result == "true"


class TestEvaluateLogicChinese:
    def test_zhen_huo_jia(self):
        result = evaluate_logic("真或假")
        assert result == "true"

    def test_zhen_qie_jia(self):
        result = evaluate_logic("真且假")
        assert result == "false"

    def test_not_zhen(self):
        result = evaluate_logic("既不是真")
        assert result == "false"

    def test_bu_cheng_li(self):
        result = evaluate_logic("不成立")
        assert result == "false"

    def test_mao_dun(self):
        result = evaluate_logic("矛盾")
        assert result == "false"

    def test_non_boolean_returns_none(self):
        assert evaluate_logic("hello world") is None


class TestKnowledgeBaseExtensions:
    def test_unit_conversion_km_to_m(self):
        result = route_knowledge("how many m in a km")
        assert result is not None
        assert "0.001" in result

    def test_unit_conversion_convert_5km(self):
        result = route_knowledge("convert 5 km to m")
        assert result is not None
        assert "5000" in result

    def test_chemical_water(self):
        result = route_knowledge("formula of water")
        assert result is not None
        assert "H2O" in result

    def test_chemical_salt(self):
        result = route_knowledge("formula of salt")
        assert result is not None
        assert "NaCl" in result

    def test_chemical_carbon_dioxide(self):
        result = route_knowledge("formula of carbon dioxide")
        assert result is not None
        assert "CO2" in result

    def test_chemical_none(self):
        assert route_knowledge("formula of nonexistent_element") is None
