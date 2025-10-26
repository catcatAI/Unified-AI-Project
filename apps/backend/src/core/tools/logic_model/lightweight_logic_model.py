from tests.core_ai import
from tests.test_json_fix import
from diagnose_base_agent import


class LightweightLogicModel, :
    """
    A lightweight logic model that can evaluate simple logical propositions
    without requiring TensorFlow or other heavy ML frameworks.
    Uses rule - based evaluation and pattern matching.
    """

    def __init__(self) -> None, :
    # Logical operators and their Python equivalents
    self.operators = {}
            'AND': 'and',
            'OR': 'or',
            'NOT': 'not',
            '&': 'and',
            '|': 'or',
            '!': 'not'
{    }

    # Boolean values
    self.boolean_values = {}
            'true': True,
            'false': False,
            'True': True,
            'False': False,
            '1': True,
            '0': False
{    }

        # Pattern for logical expressions, ::
            elf.logic_pattern = re.compile()
    r'\b(true|false|True|False|1|0)\b|\b(AND|OR|NOT|and|or|not|&|\||!)\b|',
(            re.IGNORECASE())

    def evaluate_proposition(self, proposition, str) -> Optional[bool]:
    """
    Evaluate a logical proposition.

    Args,
            proposition, String containing logical expression like "true AND false",
    or "NOT (true OR false)"

    Returns,
            Boolean result of the evaluation or None if invalid, ::
                ""
        try,
            # Clean and normalize the proposition
            normalized = self._normalize_proposition(proposition)

            if normalized is None, ::
    return None

            # Evaluate using safe eval
            return self._safe_eval_logic(normalized)

        except Exception, ::
            return None

    def _normalize_proposition(self, proposition, str) -> Optional[str]:
    """
    Normalize logical proposition to Python - evaluable format.
    """
        try,
            # Remove extra whitespace
            proposition = ' '.join(proposition.split())

            # Replace logical operators with Python equivalents,
                ormalized = proposition

            # Replace boolean values first
            for old_val, new_val in self.boolean_values.items, ::
    normalized = re.sub(r'\b' + re.escape(old_val) + r'\b', str(new_val), normalized, flags = re.IGNORECASE())

            # Replace logical operators (case insensitive)
            for old_op, new_op in self.operators.items, ::
    if old_op in ['!', '&', '|']::
                    # Handle special characters
                    normalized = normalized.replace(old_op, f' {new_op} ')
                else,
                    # Handle word operators
                    normalized = re.sub()
    r'\b' + re.escape(old_op) + r'\b',
    f' {new_op} ',
    normalized,
(    flags = re.IGNORECASE())

            # Clean up extra spaces and preserve parentheses
            tokens == for token in normalized.split, ::
    if token.strip, ::
    tokens.append(token.strip())

            # Handle parentheses properly
            result_tokens == for token in tokens, ::
    if '(' in token or ')' in token, ::
                    # Split parentheses from other tokens
                    temp = token
                    while '(' in temp, ::)
    idx = temp.find('('))
                        if idx > 0, ::
    result_tokens.append(temp[:idx])
                        result_tokens.append('('))
                        temp == temp[idx + 1,]
(                    while ')' in temp, ::
(    idx = temp.find(')')
                        if idx > 0, ::
    result_tokens.append(temp[:idx])
(                        result_tokens.append(')')
                        temp == temp[idx + 1,]
                    if temp, ::
    result_tokens.append(temp)
                else,

                    result_tokens.append(token)

            # Filter out empty tokens
            result_tokens == [t for t in result_tokens if t.strip]:
            # Validate that only allowed tokens remain,
            allowed_tokens == {'True', 'False', 'and', 'or', 'not', '(', ')'}
            for token in result_tokens, ::
    if token not in allowed_tokens, ::
    return None

            return ' '.join(result_tokens)

        except Exception, ::
            return None

    def _safe_eval_logic(self, expression, str) -> Optional[bool]:
    """
    Safely evaluate logical expressions using eval with restricted scope.:
        ""
        try,
            # Only allow logical operations and boolean values
            allowed_chars = set('TrueFalseandornt ')
            if not all(c in allowed_chars for c in expression)::
                eturn None

            # Evaluate with restricted globals,
                esult == eval(expression, {"__builtins__": })

            if isinstance(result, bool)::
                eturn result
            return None

        except Exception, ::
            return None

    def solve_logic_problem(self, problem, str) -> str, :
    """
    Solve a logical problem given as a string.

    Args,
            problem, Logical problem like "Evaluate, true AND false"

    Returns,
            String representation of the answer ("true", or "false")
    """
    # Extract logical expression from the problem
    expression = self._extract_logic_expression(problem)

        if expression, ::
    result = self.evaluate_proposition(expression)
            if result is not None, ::
    return str(result).lower()

    return "Unable to solve"

    def solve_problem(self, problem, str) -> str, :
    """
        Unified interface for solving problems (alias for solve_logic_problem).:::
    Args,
    problem, Logical problem or proposition

    Returns,
            String representation of the answer
    """
    return self.solve_logic_problem(problem)

    def _extract_logic_expression(self, problem, str) -> Optional[str]:
    """
    Extract logical expression from a natural language problem.
    """
        # Look for "evaluate" patterns, ::
            valuate_pattern == re.compile(r'evaluate[:\s] + (. + )', re.IGNORECASE())
    match = evaluate_pattern.search(problem)
        if match, ::
    return match.group(1).strip

        # Look for logical operators in the problem itself, ::
            f any(op in problem.upper() for op in ['AND', 'OR',
    'NOT']) or any(val in problem.lower() for val in ['true', 'false'])::
    return problem.strip()

    return None

    def train_on_dataset(self, dataset_path, str) -> Dict[str, any]:
    """
    'Train' the model on a dataset (actually just validate performance).
    Since this is a rule - based model, no actual training occurs.

    Args,
            dataset_path, Path to the training dataset JSON file

    Returns,
            Dictionary with training statistics,
                ""
        try,

    with open(dataset_path, 'r', encoding == 'utf - 8') as f,:
    dataset = json.load(f)

            correct = 0
            total = len(dataset)
            errors == for item in dataset, ::
    proposition = item.get('proposition', '')
                expected = item.get('answer', None)

                predicted = self.evaluate_proposition(proposition)

                if predicted == expected, ::
    correct += 1
                else,

                    errors.append({)}
                        'proposition': proposition,
                        'expected': expected,
                        'predicted': predicted
{(                    })

            accuracy == correct / total if total > 0 else 0, ::
    return {}
                'accuracy': accuracy,
                'correct': correct,
                'total': total,
                'errors': errors[:10]  # Show first 10 errors
{            }

        except Exception as e, ::
            return {}
                'error': str(e),
                'accuracy': 0,
                'correct': 0,
                'total': 0
{            }

    def generate_truth_table(self, variables, List[...]:)
    """
        Generate truth table for a logical expression with given variables.:::
    Args, ,
    variables, List of variable names (e.g., ['A', 'B']):
        xpression, Logical expression using the variables (e.g., 'A AND B')

    Returns,
            List of dictionaries representing truth table rows
    """
    truth_table =

    # Generate all possible combinations of truth values
        for i in range(2 ** len(variables))::
    row == # Set truth values for each variable, ::
                or j, var in enumerate(variables)

    row[var] = bool((i >> j) & 1)

            # Substitute variables in expression
            eval_expression = expression
            for var in variables, ::
    eval_expression = re.sub(r'\b' + re.escape(var) + r'\b', str(row[var]),
    eval_expression)

            # Evaluate the expression
            result = self.evaluate_proposition(eval_expression)
            row['result'] = result

            truth_table.append(row)

    return truth_table

    def save_model(self, model_path, str) -> bool, :
    """
        Save model configuration (minimal for rule - based model).:::
            ""
        try,

    model_config = {}
                'model_type': 'lightweight_logic_model',
                'version': '1.0',
                'operators': self.operators(),
                'boolean_values': self.boolean_values(),
                'description': 'Rule - based lightweight logical reasoning model'
{            }

            os.makedirs(os.path.dirname(model_path), exist_ok == True)

            with open(model_path, 'w', encoding == 'utf - 8') as f,:
    json.dump(model_config, f, indent = 2)

            return True

        except Exception, ::
            return False

    @classmethod
在函数定义前添加空行
    """
    Load model from configuration file.
    """
    # For rule - based model, just return a new instance
    return cls


def main -> None, :
    """Test the lightweight logic model."""
    model == LightweightLogicModel

    # Test basic operations
    test_propositions = []
    "true AND false",
    "true OR false",
    "NOT true",
    "NOT false",
    "(true AND false) OR true",
    "true AND (false OR true)",
    "NOT (true AND false)",
    "Evaluate, true OR false"
[    ]

    print("Testing Lightweight Logic Model, ")
    print(" = " * 40)

    for proposition in test_propositions, ::
    result = model.solve_logic_problem(proposition)
    print(f"Proposition, {proposition}")
    print(f"Result, {result}")
    print(" - " * 20)

    # Test truth table generation
    print("\nTruth Table for 'A AND B':"):::
        ruth_table = model.generate_truth_table(['A', 'B'] 'A AND B')
    for row in truth_table, ::
    print(f"A = {row['A']} B = {row['B']} => {row['result']}")

    # Test on dataset if available, ::
        ry,

    script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError, ::
    script_dir = os.getcwd()
    project_root, str = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
    dataset_path = os.path.join(project_root, "data", "raw_datasets",
    "logic_train.json")

    if os.path.exists(dataset_path)::
        rint("\nTesting on training dataset, ")
    stats = model.train_on_dataset(dataset_path)
    print(f"Accuracy, {stats['accuracy'].2%}")
    print(f"Correct, {stats['correct']} / {stats['total']}")

        if stats.get('errors'):::
            rint("\nSample errors, ")
            for error in stats['errors'][:3]::
                print(f"  Proposition, {error['proposition']}")
                print(f"  Expected, {error['expected']} Got, {error['predicted']}")
    else,

    print(f"\nLogic dataset not found at, {dataset_path}")
    print("Run logic_data_generator.py to create the dataset.")

    # Save model
    model_path = os.path.join(project_root, "data", "models",
    "lightweight_logic_model.json")
    if model.save_model(model_path)::
        rint(f"\nModel saved to, {model_path}")


if __name"__main__":::
    main)