import asyncio
import logging
import math  # Import math module for functions like sqrt, pow
from typing import Any
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# Define the path to the configuration file
CONFIG_FILE_PATH = Path(__file__).parent / "config" / "formula_engine_config.json"
# Define the path to the managed formulas file
MANAGED_FORMULAS_FILE_PATH = Path(__file__).parent / "config" / "managed_formulas.json"


class FormulaEngine:
    """A specialized engine to parse, execute, and manage mathematical or logical formulas.
    This enhanced version supports parentheses, basic mathematical functions, and logical operations.
    """

    def __init__(self):
        logger.info("FormulaEngine initialized.")
        # Define allowed functions and constants for safe evaluation
        self.allowed_globals = {
            "__builtins__": {},  # No built-ins
            "math": math,  # Allow math module functions
            "sqrt": math.sqrt,
            "pow": math.pow,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "log10": math.log10,
            "e": math.e,
            "pi": math.pi,
            # Python's native True/False are allowed
            "True": True,
            "False": False,
        }
        self.managed_formulas: dict[str, str] = {}
        self._load_config()
        self._load_managed_formulas()

    def register_function(self, name: str, func: callable):
        """Registers a custom function to be available within formula evaluations.
        The function must be safe and not introduce any security vulnerabilities.
        """
        if not isinstance(name, str) or not name.isidentifier():
            raise ValueError(
                f"Function name '{name}' must be a valid Python identifier.",
            )
        if not callable(func):
            raise TypeError(f"Registered item '{name}' must be a callable function.")

        # Basic safety check: prevent overwriting critical built-ins or math module
        if name in self.allowed_globals and self.allowed_globals[name] != func:
            logger.warning(f"Overwriting existing global function/constant: {name}")

        self.allowed_globals[name] = func
        logger.info(f"Function '{name}' registered with FormulaEngine.")

    def _load_managed_formulas(self):
        """Loads managed formulas from the JSON file."""
        try:
            with MANAGED_FORMULAS_FILE_PATH.open(encoding="utf-8") as f:
                self.managed_formulas = json.load(f)
            logger.info(f"Managed formulas loaded from {MANAGED_FORMULAS_FILE_PATH}")
        except FileNotFoundError:
            logger.warning(
                f"Managed formulas file not found at {MANAGED_FORMULAS_FILE_PATH}. Starting with empty collection.",
            )
            self.managed_formulas = {}
        except json.JSONDecodeError as e:
            logger.error(
                f"Error decoding managed formulas JSON from {MANAGED_FORMULAS_FILE_PATH}: {e}. Starting with empty collection.",
            )
            self.managed_formulas = {}
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while loading managed formulas: {e}. Starting with empty collection.",
            )
            self.managed_formulas = {}

    def _save_managed_formulas(self):
        """Saves managed formulas to the JSON file."""
        try:
            with MANAGED_FORMULAS_FILE_PATH.open("w", encoding="utf-8") as f:
                json.dump(self.managed_formulas, f, indent=4)
            logger.info(f"Managed formulas saved to {MANAGED_FORMULAS_FILE_PATH}")
        except Exception as e:
            logger.error(
                f"Error saving managed formulas to {MANAGED_FORMULAS_FILE_PATH}: {e}",
            )

    def add_formula(self, name: str, formula_string: str):
        """Adds a formula to the managed collection."""
        if not name or not formula_string:
            raise ValueError("Formula name and string cannot be empty.")
        if name in self.managed_formulas:
            logger.warning(f"Overwriting existing formula: {name}")

        self.managed_formulas[name] = formula_string
        self._save_managed_formulas()
        logger.info(f"Formula '{name}' added to managed collection.")

    def get_formula(self, name: str) -> str:
        """Retrieves a formula from the managed collection by name."""
        if name not in self.managed_formulas:
            raise ValueError(f"Formula '{name}' not found in managed collection.")
        return self.managed_formulas[name]

    def _load_config(self):
        """Loads configuration from the JSON file."""
        try:
            with CONFIG_FILE_PATH.open(encoding="utf-8") as f:
                config = json.load(f)
            self.allowed_operators = config.get(
                "allowed_operators",
                ["+", "-", "*", "/", "**", "%", "//", "==", "!=", "<", ">", "<=", ">="],
            )
            logger.info(f"FormulaEngine configuration loaded from {CONFIG_FILE_PATH}")
        except FileNotFoundError:
            logger.error(
                f"FormulaEngine configuration file not found at {CONFIG_FILE_PATH}. Using default values.",
            )
            self.allowed_operators = [
                "+",
                "-",
                "*",
                "/",
                "**",
                "%",
                "//",
                "==",
                "!=",
                "<",
                ">",
                "<=",
                ">=",
            ]
        except json.JSONDecodeError as e:
            logger.error(
                f"Error decoding FormulaEngine configuration JSON from {CONFIG_FILE_PATH}: {e}. Using default values.",
            )
            self.allowed_operators = [
                "+",
                "-",
                "*",
                "/",
                "**",
                "%",
                "//",
                "==",
                "!=",
                "<",
                ">",
                "<=",
                ">=",
            ]
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while loading FormulaEngine configuration: {e}. Using default values.",
            )
            self.allowed_operators = [
                "+",
                "-",
                "*",
                "/",
                "**",
                "%",
                "//",
                "==",
                "!=",
                "<",
                ">",
                "<=",
                ">=",
            ]

    def _safe_evaluate_expression(
        self,
        expression: str,
        local_vars: dict[str, Any] = None,
    ) -> Any:
        """Safely evaluates a mathematical or logical expression using `eval`.
        Only allows predefined functions, operators, and variables.
        """
        if local_vars is None:
            local_vars = {}

        # Basic sanitization: ensure no dangerous keywords are present
        dangerous_keywords = [
            "import",
            "os",
            "sys",
            "subprocess",
            "eval",
            "exec",
            "lambda",
        ]
        for keyword in dangerous_keywords:
            if keyword in expression:
                raise ValueError(
                    f"Dangerous keyword '{keyword}' detected in expression.",
                )

        # Use a restricted environment for eval
        # Combine allowed_globals with local_vars for the eval's scope
        eval_globals = self.allowed_globals.copy()
        # Allow boolean variables in addition to numeric ones
        eval_locals = {
            k: v for k, v in local_vars.items() if isinstance(v, (int, float, bool))
        }

        try:
            # Compile the expression first to catch syntax errors early and prevent some injection
            code = compile(expression, "<string>", "eval")

            # Check for disallowed nodes in the AST (Abstract Syntax Tree)
            import ast

            tree = ast.parse(expression, mode="eval")
            for node in ast.walk(tree):
                if isinstance(
                    node,
                    (
                        ast.Call,
                        ast.Attribute,
                        ast.Subscript,
                        ast.List,
                        ast.Dict,
                        ast.Set,
                        ast.GeneratorExp,
                        ast.ListComp,
                        ast.SetComp,
                        ast.DictComp,
                    ),
                ):
                    # Allow calls to explicitly defined logical functions (AND, OR, NOT)
                    if (
                        isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Name)
                        and node.func.id in self.allowed_globals
                    ):
                        continue  # Allowed function call
                    if isinstance(node, ast.Name) and node.id in eval_locals:
                        continue  # Allowed variable
                    if isinstance(node, (ast.Constant, ast.Num)):
                        continue  # Allowed constants/numbers/booleans
                    # Allow logical operators (And, Or, Not) and comparison operators
                    if (
                        (
                            isinstance(node, ast.BoolOp)
                            and isinstance(
                                node.op,
                                (ast.And, ast.Or),
                            )
                        )
                        or (
                            isinstance(node, ast.UnaryOp)
                            and isinstance(node.op, ast.Not)
                        )
                        or isinstance(node, ast.Compare)
                    ):
                        continue
                    if isinstance(node, ast.BinOp) and isinstance(
                        node.op,
                        (
                            ast.Pow,
                            ast.Mult,
                            ast.Div,
                            ast.FloorDiv,
                            ast.Mod,
                            ast.Add,
                            ast.Sub,
                        ),
                    ):
                        continue  # Allowed binary operations
                    if isinstance(node, ast.UnaryOp) and isinstance(
                        node.op,
                        (ast.UAdd, ast.USub),
                    ):
                        continue  # Allowed unary operations
                    raise ValueError(
                        f"Disallowed operation or function call in expression: {expression}",
                    )
                if (
                    isinstance(node, ast.Name)
                    and node.id not in eval_locals
                    and node.id not in self.allowed_globals
                ):
                    raise ValueError(
                        f"Undefined variable or function '{node.id}' in expression: {expression}",
                    )

            # Evaluate the expression
            result = eval(code, eval_globals, eval_locals)
            return result
        except (SyntaxError, NameError, TypeError, ValueError, ZeroDivisionError) as e:
            raise ValueError(f"Invalid expression or operation: {e}")
        except Exception as e:
            raise ValueError(f"An unexpected error occurred during evaluation: {e}")

    async def evaluate_formula(
        self,
        formula: str,
        variables: dict[str, Any] = None,
    ) -> dict[str, Any]:
        """Evaluates a given formula with provided variables using a safe expression evaluator."""
        logger.info(
            f"FormulaEngine: Evaluating formula: '{formula}' with variables: {variables}",
        )
        await asyncio.sleep(0.05)  # Reduced sleep for faster simulation

        try:
            result = self._safe_evaluate_expression(formula, variables)
            return {"status": "success", "result": result, "evaluated_formula": formula}
        except ValueError as e:
            logger.error(f"Error evaluating formula: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error evaluating formula: {e}",
                "evaluated_formula": formula,
            }
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"An unexpected error occurred: {e}",
                "evaluated_formula": formula,
            }


if __name__ == "__main__":

    async def main():
        # Set PYTHONPATH to include the project root for module resolution
        import os
        import sys

        sys.path.insert(
            0,
            str(Path(__file__).resolve().parent.parent.parent.parent.parent),
        )

        engine = FormulaEngine()

        # Test mathematical formula evaluation
        print("\n--- Mathematical Formula Tests ---")
        formula1 = "2 + 3 * 4"
        result1 = await engine.evaluate_formula(formula1)
        print(f"Result 1 (2 + 3 * 4): {result1}")

        formula2 = "(x * y) + z"  # Test parentheses
        variables2 = {"x": 5, "y": 2, "z": 10}
        result2 = await engine.evaluate_formula(formula2, variables2)
        print(f"Result 2 ((5 * 2) + 10): {result2}")

        formula3 = "sqrt(16)"  # Test math function
        result3 = await engine.evaluate_formula(formula3)
        print(f"Result 3 (sqrt(16)): {result3}")

        formula4 = "pow(2, 3) + pi"  # Test pow and pi constant
        result4 = await engine.evaluate_formula(formula4)
        print(f"Result 4 (pow(2, 3) + pi): {result4}")

        formula9 = "2 ** 3"  # Test power operator
        result9 = await engine.evaluate_formula(formula9)
        print(f"Result 9 (2 ** 3): {result9}")

        # Test logical formula evaluation
        print("\n--- Logical Formula Tests ---")
        formula_l1 = "True and False"  # Changed from AND to and
        result_l1 = await engine.evaluate_formula(formula_l1)
        print(f"Result L1 (True and False): {result_l1}")
        assert result_l1["result"] == False

        formula_l2 = "x > 5 or y < 10"  # Changed from OR to or
        variables_l2 = {"x": 7, "y": 3}
        result_l2 = await engine.evaluate_formula(formula_l2, variables_l2)
        print(f"Result L2 (x > 5 or y < 10): {result_l2}")
        assert result_l2["result"] == True

        formula_l3 = "not (a == b)"  # Changed from NOT to not
        variables_l3 = {"a": 10, "b": 10}
        result_l3 = await engine.evaluate_formula(formula_l3, variables_l3)
        print(f"Result L3 (not (a == b)): {result_l3}")
        assert result_l3["result"] == False

        formula_l4 = "(temp > 25 and humidity < 60) or is_raining"  # Changed from AND/OR to and/or
        variables_l4 = {"temp": 28, "humidity": 55, "is_raining": False}
        result_l4 = await engine.evaluate_formula(formula_l4, variables_l4)
        print(f"Result L4 ((temp > 25 and humidity < 60) or is_raining): {result_l4}")
        assert result_l4["result"] == True

        # Test error handling for logical expressions
        print("\n--- Error Handling Tests (Logical) ---")
        formula_e1 = "True and unknown_var"
        result_e1 = await engine.evaluate_formula(formula_e1)
        print(f"Result E1 (True and unknown_var): {result_e1}")
        assert result_e1["status"] == "error"

        # Test existing error cases again to ensure no regressions
        print("\n--- Regression Tests for Error Handling ---")
        formula5 = "10 / 0"  # Test division by zero
        result5 = await engine.evaluate_formula(formula5)
        print(f"Result 5 (10 / 0): {result5}")

        formula6 = "2 + import os"  # Test dangerous keyword
        result6 = await engine.evaluate_formula(formula6)
        print(f"Result 6 (2 + import os): {result6}")

        formula7 = "unknown_func(5)"  # Test unknown function
        result7 = await engine.evaluate_formula(formula7)
        print(f"Result 7 (unknown_func(5)): {result7}")

        formula8 = "x + 5"  # Test undefined variable
        result8 = await engine.evaluate_formula(formula8)
        print(f"Result 8 (x + 5): {result8}")

    asyncio.run(main())
