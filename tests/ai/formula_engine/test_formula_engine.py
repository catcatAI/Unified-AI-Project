import pytest
import json
import tempfile
from pathlib import Path
from ai.formula_engine import FormulaEngine


def test_formula_engine_imports():
    from ai.formula_engine import FormulaEngine
    assert FormulaEngine is not None


def test_formula_engine_init_nonexistent():
    engine = FormulaEngine(formulas_filepath="nonexistent_file.json")
    assert engine.formulas == []


def test_formula_engine_empty_match():
    engine = FormulaEngine(formulas_filepath="nonexistent_file.json")
    result = engine.match_input("")
    assert result is None


def test_formula_engine_no_match():
    engine = FormulaEngine(formulas_filepath="nonexistent_file.json")
    result = engine.match_input("anything")
    assert result is None


def test_formula_engine_execute_minimal():
    engine = FormulaEngine(formulas_filepath="nonexistent_file.json")
    formula = {"name": "test", "action": "respond_greeting"}
    result = engine.execute_formula(formula)
    assert result == {"action_name": "respond_greeting", "action_params": {}}


def test_formula_engine_execute_with_params():
    engine = FormulaEngine(formulas_filepath="nonexistent_file.json")
    formula = {"name": "test", "action": "calculate", "parameters": {"query": "2+2"}}
    result = engine.execute_formula(formula)
    assert result == {"action_name": "calculate", "action_params": {"query": "2+2"}}


def test_formula_engine_load_valid_json():
    formulas = [
        {"name": "greeting", "conditions": ["hello"], "action": "greet", "enabled": True, "priority": 1}
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(formulas, f)
        tmp_path = f.name
    try:
        engine = FormulaEngine(formulas_filepath=tmp_path)
        assert len(engine.formulas) == 1
        assert engine.formulas[0]["name"] == "greeting"
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_formula_engine_match_with_loaded_formula():
    formulas = [
        {"name": "greeting", "conditions": ["hello"], "action": "greet", "enabled": True, "priority": 1}
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(formulas, f)
        tmp_path = f.name
    try:
        engine = FormulaEngine(formulas_filepath=tmp_path)
        result = engine.match_input("hello world")
        assert result is not None
        assert result["name"] == "greeting"
    finally:
        Path(tmp_path).unlink(missing_ok=True)
