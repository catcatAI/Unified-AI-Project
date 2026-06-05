"""
 * =============================================================================
 * ANGELA-MATRIX: [L4-Test] [α-Test] [A-Validation] [L0-L3]
 * =============================================================================
"""

import pytest
try:
    from apps.backend.src.core.security.secure_eval import (
        EvalResult,
        SafeEvaluator,
        safe_eval,
        safe_eval_arithmetic,
        get_safe_evaluator,
    )
except ImportError:
    import pytest; pytest.skip("SecureEval is a stub", allow_module_level=True)


class TestEvalResult:
    def test_defaults(self):
        r = EvalResult(success=True)
        assert r.success is True
        assert r.result is None
        assert r.error is None
        assert r.expression is None

    def test_full(self):
        r = EvalResult(success=True, result=42, error=None, expression="40+2")
        assert r.result == 42
        assert r.expression == "40+2"


class TestSafeEvaluator:
    def setup_method(self):
        self.e = SafeEvaluator()

    # --- Basic arithmetic ---

    def test_addition(self):
        r = self.e.evaluate("1+2")
        assert r.success is True
        assert r.result == 3

    def test_subtraction(self):
        r = self.e.evaluate("10-3")
        assert r.success is True
        assert r.result == 7

    def test_multiplication(self):
        r = self.e.evaluate("3*4")
        assert r.success is True
        assert r.result == 12

    def test_division(self):
        r = self.e.evaluate("10/4")
        assert r.success is True
        assert r.result == 2.5

    def test_floor_division(self):
        r = self.e.evaluate("10//3")
        assert r.success is True
        assert r.result == 3

    def test_modulo(self):
        r = self.e.evaluate("10%3")
        assert r.success is True
        assert r.result == 1

    def test_power(self):
        r = self.e.evaluate("2**8")
        assert r.success is True
        assert r.result == 256

    def test_complex_expression(self):
        r = self.e.evaluate("2*3+4")
        assert r.success is True
        assert r.result == 10

    # --- Comparison operators ---

    def test_eq(self):
        assert self.e.evaluate("1==1").result is True
        assert self.e.evaluate("1==2").result is False

    def test_ne(self):
        assert self.e.evaluate("1!=2").result is True

    def test_lt(self):
        assert self.e.evaluate("1<2").result is True

    def test_lte(self):
        assert self.e.evaluate("2<=2").result is True

    def test_gt(self):
        assert self.e.evaluate("3>2").result is True

    def test_gte(self):
        assert self.e.evaluate("3>=3").result is True

    # --- Boolean operators ---

    def test_and(self):
        assert self.e.evaluate("True and False").result is False

    def test_or(self):
        assert self.e.evaluate("True or False").result is True

    def test_not(self):
        assert self.e.evaluate("not True").result is False

    def test_chained_comparison(self):
        r = self.e.evaluate("1 < 2 and 3 > 4")
        assert r.result is False

    # --- Identity operators ---

    def test_is(self):
        assert self.e.evaluate("None is None").result is True

    def test_is_not(self):
        assert self.e.evaluate("True is not False").result is True

    # --- Membership operators ---

    def test_in(self):
        assert self.e.evaluate("2 in [1,2,3]").result is True

    def test_not_in(self):
        assert self.e.evaluate("4 not in [1,2,3]").result is True

    # --- Constants ---

    def test_true(self):
        assert self.e.evaluate("True").result is True

    def test_false(self):
        assert self.e.evaluate("False").result is False

    def test_none(self):
        assert self.e.evaluate("None").result is None

    # --- Context variables ---

    def test_context_variable(self):
        r = self.e.evaluate("x + 1", {"x": 5})
        assert r.success is True
        assert r.result == 6

    def test_context_multiple(self):
        r = self.e.evaluate("a * b", {"a": 3, "b": 7})
        assert r.result == 21

    def test_context_overrides_constant(self):
        r = self.e.evaluate("True", {"True": False})
        assert r.result is True

    def test_context_missing_variable(self):
        r = self.e.evaluate("unknown_var")
        assert r.success is False

    # --- Allowed functions ---

    @pytest.mark.parametrize("expr,expected", [
        ("abs(-5)", 5),
        ("min(3,7)", 3),
        ("max(3,7)", 7),
        ("round(3.14159,2)", 3.14),
        ("pow(2,3)", 8),
        ("len([1,2,3])", 3),
        ("sum([1,2,3])", 6),
        ("sorted([3,1,2])", [1, 2, 3]),
        ("any([False, True])", True),
        ("all([True, True])", True),
        ("int(3.7)", 3),
        ("float(3)", 3.0),
        ("str(42)", "42"),
        ("bool(1)", True),
        ("list((1,2))", [1, 2]),
        ("tuple([1,2])", (1, 2)),
        ("set([1,2,2])", {1, 2}),
    ])
    def test_allowed_functions(self, expr, expected):
        r = self.e.evaluate(expr)
        assert r.success is True, f"Failed: {expr}, error: {r.error}"
        assert r.result == expected, f"For {expr}: got {r.result}, expected {expected}"

    # --- Literal types ---

    def test_list_literal(self):
        r = self.e.evaluate("[1,2,3]")
        assert r.result == [1, 2, 3]

    def test_tuple_literal(self):
        r = self.e.evaluate("(1,2,3)")
        assert r.result == (1, 2, 3)

    def test_dict_literal(self):
        r = self.e.evaluate("{'a':1,'b':2}")
        assert r.result == {"a": 1, "b": 2}

    # --- Subscript / slice ---

    def test_subscript_index(self):
        r = self.e.evaluate("[1,2,3][1]")
        assert r.result == 2

    def test_subscript_slice(self):
        r = self.e.evaluate("[1,2,3,4][1:3]")
        assert r.result == [2, 3]

    def test_dict_key_access(self):
        r = self.e.evaluate("{'a':42}['a']")
        assert r.result == 42

    # --- Security: dangerous expressions ---

    @pytest.mark.parametrize("expr", [
        "__import__('os')",
        "open('test.txt')",
        "exec('print(1)')",
        "eval('1+1')",
        "().__class__",
    ])
    def test_rejected_dangerous(self, expr):
        r = self.e.evaluate(expr)
        assert r.success is False, f"Should have rejected: {expr}"

    # --- Edge cases ---

    def test_empty_string(self):
        r = self.e.evaluate("")
        assert r.success is False

    def test_nonexistent_variable_rejected(self):
        r = self.e.evaluate("foo")
        assert r.success is False

    def test_syntax_error(self):
        r = self.e.evaluate("1++")
        assert r.success is False

    def test_length_limit(self):
        e = SafeEvaluator(max_length=5)
        r = e.evaluate("1+2")
        assert r.success is True
        r2 = e.evaluate("1+2+3+4")
        assert r2.success is False

    def test_complexity_limit(self):
        e = SafeEvaluator(max_complexity=2)
        r = e.evaluate("1")
        assert r.success is True
        r2 = e.evaluate("1+2")
        assert r2.success is False

    def test_non_string_input(self):
        r = self.e.evaluate(123)
        assert r.success is False

    # --- evaluate_arithmetic ---

    def test_arithmetic_valid(self):
        r = self.e.evaluate_arithmetic("1.5+2.5")
        assert r.success is True
        assert abs(r.result - 4.0) < 0.001

    def test_arithmetic_string_result_rejected(self):
        r = self.e.evaluate_arithmetic("'hello'")
        assert r.success is False

    def test_arithmetic_context_limited(self):
        r = self.e.evaluate_arithmetic("1+2*3")
        assert r.success is True
        assert r.result == 7

    # --- Module-level convenience functions ---

    def test_safe_eval_function(self):
        r = safe_eval("2+2")
        assert r.success is True
        assert r.result == 4

    def test_safe_eval_arithmetic_function(self):
        r = safe_eval_arithmetic("3*3")
        assert r.success is True
        assert r.result == 9

    def test_get_safe_evaluator_singleton(self):
        e1 = get_safe_evaluator()
        e2 = get_safe_evaluator()
        assert e1 is e2
