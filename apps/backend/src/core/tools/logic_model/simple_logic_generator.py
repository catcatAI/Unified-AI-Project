"""
简单逻辑生成器
"""

import random
from typing import List, Dict, Any
import logging
logger = logging.getLogger(__name__)


def generate_simple_logic_dataset(num_samples: int = 1000) -> List[Dict[str, Any]]:
    """生成简单逻辑数据集"""
    dataset = []
    operators = ["AND", "OR"]
    values = ["true", "false"]

    for i in range(num_samples):
        # 生成不同类型的命题
        prop_type = random.choice(["simple", "binary", "unary", "complex"])

        if prop_type == "simple":
            # 简单值
            prop = random.choice(values)
            answer = prop == "true"
        elif prop_type == "binary":
            # 二元操作 A op B
            left = random.choice(values)
            right = random.choice(values)
            op = random.choice(operators)
            prop = f"{left} {op} {right}"

            if op == "AND":
                answer = (left == "true") and (right == "true")
            else:  # OR
                answer = (left == "true") or (right == "true")
        elif prop_type == "unary":
            # 一元操作 NOT A
            val = random.choice(values)
            prop = f"NOT {val}"
            answer = val == "false"
        else:  # complex
            # 复杂表达式
            left = random.choice(values)
            right = random.choice(values)
            middle = random.choice(values)
            op1 = random.choice(operators)
            op2 = random.choice(operators)
            prop = f"({left} {op1} {middle}) {op2} {right}"

            # 简化评估
            left_val = left == "true"
            middle_val = middle == "true"
            right_val = right == "true"

            if op1 == "AND":
                first_part = left_val and middle_val
            else:
                first_part = left_val or middle_val

            if op2 == "AND":
                answer = first_part and right_val
            else:
                answer = first_part or right_val

        dataset.append({
            "proposition": prop,
            "answer": answer,
            "type": prop_type
        })

    return dataset


def save_dataset(dataset: List[Dict[str, Any]], output_file: str):
    """保存数据集"""
    import json
    import os

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    logger.info(f"保存 {len(dataset)} 个样本到 {output_file}")


def main():
    """主函数"""
    logger.info("生成简单逻辑数据集...")
    dataset = generate_simple_logic_dataset(1000)
    save_dataset(dataset, "data/raw_datasets/simple_logic.json")
    logger.info("完成!")


if __name__ == "__main__":
    main()