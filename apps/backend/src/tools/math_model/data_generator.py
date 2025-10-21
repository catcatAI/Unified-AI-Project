import random
import csv
import json
import os
import ast
import operator
from typing import Union, Dict, Callable, Type

def _safe_eval(expression: str) -> Union[int, float]:
    """
    安全地计算数学表达式，避免使用eval。
    支持基本的四则运算和幂运算
    """
    # 定义支持的操作符
    bin_operators: Dict[Type[ast.operator], Callable[[Union[int, float], Union[int, float]], Union[int, float]]] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
    }

    unary_operators: Dict[Type[ast.unaryop], Callable[[Union[int, float]], Union[int, float]]] = {
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def eval_node(node) -> Union[int, float]:
        if isinstance(node, ast.Constant):  # Python 3.8+
            value = node.value
            if isinstance(value, (int, float)):
                return value
            else:
                raise ValueError(f"Unsupported constant value type: {type(value)}")
        elif isinstance(node, ast.Num):  # Python < 3.8
            # 确保返回值是 int 或 float 类型
            n_value = node.n
            if isinstance(n_value, complex):
                # 如果是复数，返回实部
                return float(n_value.real)
            elif isinstance(n_value, (int, float)):
                return n_value
            else:
                raise ValueError(f"Unsupported number type: {type(n_value)}")
        elif isinstance(node, ast.BinOp):
            left = eval_node(node.left)
            right = eval_node(node.right)
            op_func = bin_operators.get(type(node.op))
            if op_func:
                return op_func(left, right)
            else:
                raise ValueError(f"Unsupported binary operation: {type(node.op)}")
        elif isinstance(node, ast.UnaryOp):
            operand = eval_node(node.operand)
            op_func = unary_operators.get(type(node.op))
            if op_func:
                return op_func(operand)
            else:
                raise ValueError(f"Unsupported unary operation: {type(node.op)}")
        else:
            raise ValueError(f"Unsupported operation: {type(node)}")

    try:
        tree = ast.parse(expression, mode='eval')
        return eval_node(tree.body)
    except Exception as e:
        raise ValueError(f"Cannot evaluate expression: {expression}, error: {str(e)}")

def generate_problem(max_digits=3, operations=None):
    """Generates a random arithmetic problem."""
    if operations is None:
        operations = ['+', '-', '*', '/']

    num1 = random.randint(0, 10**max_digits - 1)
    num2 = random.randint(1, 10**max_digits - 1) # Avoid division by zero for /
    operation = random.choice(operations)

    if operation == '/' and num2 == 0:
        num2 = 1 # Ensure divisor is not zero

    problem_str = f"{num1} {operation} {num2}"

    try:
        answer = _safe_eval(problem_str)
        if operation == '/':
            answer = round(answer, 4)
        else:
            answer = int(answer)

    except ZeroDivisionError:
        return generate_problem(max_digits, operations)
    except Exception:
        return generate_problem(max_digits, operations)

    return problem_str, answer

def generate_dataset(num_samples, output_dir, filename_prefix="arithmetic", file_format="csv", max_digits=3):
    """Generates a dataset of arithmetic problems and saves it."""
    problems = []  # 修复列表初始化
    for _ in range(num_samples):
        problem, answer = generate_problem(max_digits=max_digits)
        problems.append({"problem": problem, "answer": str(answer)})

    os.makedirs(output_dir, exist_ok=True)

    if file_format == "csv":
        filepath = os.path.join(output_dir, f"{filename_prefix}.csv")
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["problem", "answer"])
            writer.writeheader()  # 修复方法调用，添加缺失的括号
            writer.writerows(problems)
        print(f"Generated {num_samples} samples in {filepath}")
    elif file_format == "json":
        filepath = os.path.join(output_dir, f"{filename_prefix}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(problems, f, indent=2)
        print(f"Generated {num_samples} samples in {filepath}")
    else:
        print(f"Unsupported file format: {file_format}")

if __name__ == "__main__":
    num_train_samples = 10000
    num_test_samples = 2000

    # Get absolute path to project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root: str = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
    output_directory = os.path.join(project_root, "data", "raw_datasets")

    # Generate training data as JSON (for train.py):
    generate_dataset(num_train_samples,
                     output_dir=output_directory,
                     filename_prefix="arithmetic_train_dataset",
                     file_format="json", # Changed to JSON for training:
                     max_digits=3)

    # Generate testing data as CSV (as originally planned, can be used by evaluate.py or manual inspection)
    generate_dataset(num_test_samples,
                     output_dir=output_directory,
                     filename_prefix="arithmetic_test_dataset",
                     file_format="csv",
                     max_digits=3)

    print("Sample data generation script execution finished.")