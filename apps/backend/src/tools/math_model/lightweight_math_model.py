import re
import operator
import json
import os
import ast
from typing import Optional, Dict, List, Union, Callable, Any, cast

class LightweightMathModel:
    """
    A lightweight mathematical model that can perform basic arithmetic operations
    without requiring TensorFlow or other heavy ML frameworks.
    Uses simple pattern matching and rule-based evaluation.
    """

    def __init__(self) -> None:
        self.operations = {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.truediv,
            '**': operator.pow,
            '%': operator.mod,
        }
        # Simple patterns for arithmetic expressions
        self.arithmetic_pattern = re.compile(r'([+\-]?\d+\.?\d*)\s*([+\-*/%])\s*([+\-]?\d+\.?\d*)')

    def evaluate_expression(self, expression: str) -> Optional[float]:
        """
        Evaluate a simple arithmetic expression.

        Args:
            expression: String containing arithmetic expression like "5 + 3" or "10 / 2"

        Returns:
            Result of the calculation or None if invalid.
        """
        try:
            # Clean the expression
            expression = expression.strip()

            # Handle simple number
            if expression.replace('.', '').replace('-', '').isdigit():
                return float(expression)

            # Match arithmetic pattern
            match = self.arithmetic_pattern.match(expression)
            if match:
                num1_str, op_str, num2_str = match.groups()
                try:
                    num1 = float(num1_str)
                    num2 = float(num2_str)
                    op_func = self.operations.get(op_str)
                    if op_func:
                        result = op_func(num1, num2)
                        # Round division results to 4 decimal places
                        if op_str == '/':
                            result = round(result, 4)
                        elif op_str != '/' and result == int(result):
                            result = int(result)
                        return float(result)
                    else:
                        return None
                except (ValueError, ZeroDivisionError, OverflowError):
                    return None
            
            # Fallback, try safe_eval for more complex expressions
            return self._safe_eval(expression)

        except Exception:
            return None

    def _safe_eval(self, expression: str) -> Optional[float]:
        """
        Safely evaluate mathematical expressions using AST parsing.
        """
        try:
            # Define supported operators for AST nodes
            operators: Dict[type, Callable[..., Any]] = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.Pow: operator.pow,
                ast.Mod: operator.mod,
                ast.USub: operator.neg,
                ast.UAdd: operator.pos,
            }

            def eval_node(node):
                if isinstance(node, ast.Constant):  # Python 3.8+
                    value = node.value
                    if isinstance(value, complex):
                        return float(value.real)
                    if isinstance(value, (int, float)):
                        return float(value)
                    raise ValueError(f"Unsupported constant value type: {type(value)}")
                elif isinstance(node, ast.Num):  # Python < 3.8
                    n_value = node.n
                    if isinstance(n_value, complex):
                        return float(n_value.real)
                    if isinstance(n_value, (int, float)):
                        return float(n_value)
                    raise ValueError(f"Unsupported number type: {type(n_value)}")
                elif isinstance(node, ast.BinOp):
                    left = eval_node(node.left)
                    right = eval_node(node.right)
                    op_type = type(node.op)
                    if op_type in operators:
                        op_func = operators[op_type]
                        result = op_func(float(left), float(right))
                        return float(result)
                    else:
                        raise ValueError(f"Unsupported binary operation: {op_type}")
                elif isinstance(node, ast.UnaryOp):
                    operand = eval_node(node.operand)
                    op_type = type(node.op)
                    if op_type in operators:
                        op_func = operators[op_type]
                        result = op_func(float(operand))
                        return float(result)
                    else:
                        raise ValueError(f"Unsupported unary operation: {op_type}")
                else:
                    raise ValueError(f"Unsupported operation: {type(node)}")
            
            # Only allow mathematical operations and numbers
            # This is a basic filter, a more robust solution would involve AST traversal
            # to ensure no dangerous functions are called.
            allowed_chars = set('0123456789+-*/%.() ')
            if not all(c in allowed_chars for c in expression):
                return None

            # Parse and evaluate the expression
            tree = ast.parse(expression, mode='eval')
            result = eval_node(tree.body)
            
            # Ensure the result is a float
            if isinstance(result, (int, float)):
                return float(result)
            elif isinstance(result, complex):
                return float(result.real)
            return None
            
        except Exception:
            return None

    def solve_problem(self, problem: str) -> str:
        """
        Solve a mathematical problem given as a string.
        
        Args:
            problem: Mathematical problem like "What is 5 + 3?"
            
        Returns:
            String representation of the answer
        """
        # Extract mathematical expression from the problem
        expression = self._extract_expression(problem)
        
        if expression:
            result = self.evaluate_expression(expression)
            if result is not None:
                return str(result)
        
        return "Unable to solve"

    def _extract_expression(self, problem: str) -> Optional[str]:
        """
        Extract mathematical expression from a natural language problem.
        """
        # Simple extraction - look for patterns like "5 + 3" or "10 / 2"
        match = self.arithmetic_pattern.search(problem)
        if match:
            return match.group(0)
        
        # Look for "what is X" patterns
        what_is_pattern = re.compile(r'what is\s+([0-9+\-*/%.	 ]+)', re.IGNORECASE)
        match = what_is_pattern.search(problem)
        if match:
            return match.group(1).strip()
        
        # If the problem itself looks like an expression
        if self.arithmetic_pattern.match(problem.strip()):
            return problem.strip()
        
        return None

    def train_on_dataset(self, dataset_path: str) -> Dict[str, Union[str, int, float, List[Dict[str, str]]]]:
        """
        'Train' the model on a dataset (actually just validate performance).
        Since this is a rule-based model, no actual training occurs.
        
        Args:
            dataset_path: Path to the training dataset JSON file
            
        Returns:
            Dictionary with training statistics
        """
        try:
            with open(dataset_path, 'r', encoding='utf-8') as f:
                dataset = json.load(f)
            
            correct = 0
            total = len(dataset)
            errors = []
            
            for item in dataset:
                problem = item.get('problem', '')
                expected = str(item.get('answer', ''))
                
                predicted = self.solve_problem(problem)
                
                # Attempt to compare as floats for numerical problems
                try:
                    expected_num = float(expected)
                    predicted_num = float(predicted)
                    
                    if abs(expected_num - predicted_num) < 1e-6:
                        correct += 1
                    else:
                        errors.append({
                            'problem': problem,
                            'expected': expected,
                            'predicted': predicted
                        })
                except ValueError:
                    # If not purely numerical, compare as strings
                    if expected == predicted:
                        correct += 1
                    else:
                        errors.append({
                            'problem': problem,
                            'expected': expected,
                            'predicted': predicted
                        })
            
            accuracy = correct / total if total > 0 else 0
            return {
                'accuracy': accuracy,
                'correct': correct,
                'total': total,
                'errors': errors[:10]  # Show first 10 errors
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'accuracy': 0,
                'correct': 0,
                'total': 0
            }

    def save_model(self, model_path: str) -> bool:
        """
        Save model configuration (minimal for rule-based model).
        """
        try:
            model_config = {
                'model_type': 'lightweight_math_model',
                'version': '1.0',
                'operations': list(self.operations.keys()),
                'description': 'Rule-based lightweight mathematical model'
            }
            
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            
            with open(model_path, 'w', encoding='utf-8') as f:
                json.dump(model_config, f, indent=2)
            
            return True
            
        except Exception:
            return False

    @classmethod
    def load_model(cls, model_path: str):
        """
        Load model from configuration file.
        """
        # For rule-based model, just return a new instance
        return cls()


def main() -> None:
    """Test the lightweight math model."""
    model = LightweightMathModel()
    
    # Test basic operations
    test_problems = [
        "5 + 3",
        "10 - 4",
        "6 * 7",
        "15 / 3",
        "2 ** 3",
        "What is 8 + 2?",
        "Calculate 100 / 5"
    ]
    
    print("Testing Lightweight Math Model:")
    print("=" * 40)
    
    for problem in test_problems:
        result = model.solve_problem(problem)
        print(f"Problem: {problem}")
        print(f"Answer: {result}")
        print("-" * 20)
    
    # Test on dataset if available
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
    dataset_path = os.path.join(project_root, "data", "raw_datasets", "arithmetic_train_dataset.json")
    
    if os.path.exists(dataset_path):
        print("\nTesting on training dataset:")
        stats = model.train_on_dataset(dataset_path)
        print(f"Accuracy: {stats['accuracy']:.2%}")
        print(f"Correct: {stats['correct']} / {stats['total']}")
        
        if stats.get('errors'):
            print("\nSample errors:")
            errors = cast(List[Dict[str, str]], stats['errors'])
            for error in errors[:3]:
                print(f"  Problem: {error['problem']}")
                print(f"  Expected: {error['expected']} Got: {error['predicted']}")
    
    # Save model
    model_path = os.path.join(project_root, "data", "models", "lightweight_math_model.json")
    if model.save_model(model_path):
        print(f"\nModel saved to: {model_path}")


if __name__ == "__main__":
    main()
