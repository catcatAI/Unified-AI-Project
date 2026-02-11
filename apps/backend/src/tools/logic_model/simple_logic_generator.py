"""简单逻辑生成器"""

from typing import List, Dict
import random


def generate_simple_logic_dataset(num_samples: int = 1000) -> List[Dict]:
    """生成简单逻辑数据集"""
    dataset = []
    operators = ["AND", "OR"]
    values = ["true", "false"]

    for i in range(num_samples):
        prop_type = random.choice(["simple", "binary", "unary", "complex"])

        if prop_type == "simple":
            prop = random.choice(values)
            answer = prop == "true"

        elif prop_type == "binary":
            left = random.choice(values)
            right = random.choice(values)
            op = random.choice(operators)
            prop = f"{left} {op} {right}"

            if op == "AND":
                answer = (left == "true") and (right == "true")
            else:  # OR
                answer = (left == "true") or (right == "true")

        elif prop_type == "unary":
            value = random.choice(values)
            prop = f"NOT {value}"
            answer = value == "false"

        else:  # complex
            left = random.choice(values)
            right = random.choice(values)
            op1 = random.choice(operators)
            prop = f"NOT ({left} {op1} {right})"

            if op1 == "AND":
                temp = (left == "true") and (right == "true")
            else:  # OR
                temp = (left == "true") or (right == "true")
            answer = not temp

        dataset.append({
            "proposition": prop,
            "answer": answer,
            "type": prop_type
        })

    return dataset


if __name__ == "__main__":
    dataset = generate_simple_logic_dataset(10)
    for item in dataset:
        print(f"{item['proposition']} => {item['answer']}")