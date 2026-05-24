import pytest
from ai.meta_formulas.meta_formula import MetaFormula


def test_meta_formula_init():
    mf = MetaFormula("test_name", "test_description")
    assert mf.name == "test_name"
    assert mf.description == "test_description"


def test_meta_formula_execute_raises():
    mf = MetaFormula("test", "desc")
    with pytest.raises(NotImplementedError, match="not been implemented"):
        mf.execute()


def test_meta_formula_execute_with_args_raises():
    mf = MetaFormula("test", "desc")
    with pytest.raises(NotImplementedError):
        mf.execute("arg1", kwarg="value")


def test_meta_formula_empty_name():
    mf = MetaFormula("", "")
    assert mf.name == ""
    assert mf.description == ""