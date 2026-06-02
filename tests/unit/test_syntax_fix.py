"""Tests for syntax correctness and basic Python patterns."""
from unittest.mock import patch
import pytest


def test_basic_assertion():
    assert 1 + 1 == 2
    assert isinstance("hello", str)


def test_function_syntax():
    def function_with_correct_syntax():
        if True:
            return "Correct"
        return "Incorrect"

    assert function_with_correct_syntax() == "Correct"


def test_another_function_syntax():
    def another_function_with_correct_syntax():
        return "Correct"

    assert another_function_with_correct_syntax() == "Correct"


def test_third_function_syntax():
    def third_function_with_correct_syntax():
        return "Correct"

    assert third_function_with_correct_syntax() == "Correct"


def test_mixed_indent_syntax():
    def mixed_indent_function():
        if True:
            return "Mixed Indent"
        return "Incorrect"

    assert mixed_indent_function() == "Mixed Indent"


@patch("builtins.print")
def test_async_function_call(mock_print):
    async def async_function_mock():
        return "done"

    assert callable(async_function_mock)


def test_class_method_syntax():
    class TestClassCorrect:
        def method(self):
            return "Class Method"

    instance = TestClassCorrect()
    assert instance.method() == "Class Method"


def test_lambda_syntax():
    double = lambda x: x * 2
    assert double(5) == 10
    assert double(0) == 0


def test_list_comprehension():
    squares = [x ** 2 for x in range(5)]
    assert squares == [0, 1, 4, 9, 16]


def test_exception_handling():
    def divide(a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

    with pytest.raises(ValueError):
        divide(1, 0)
    assert divide(10, 2) == 5
