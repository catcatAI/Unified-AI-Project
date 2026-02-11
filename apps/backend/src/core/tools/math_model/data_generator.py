"""
数学模型数据生成器
"""

import json
import csv
import os
import random
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


def _atomic_write_text(path: Path, content: str) -> None:
    """原子写入文本文件"""
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    os.replace(tmp, path)


def generate_problem(max_digits: int = 3, operations: list = None) -> tuple:
    """生成随机算术问题"""
    if operations is None:
        operations = ['+', '-', '*', '/']

    num1 = random.randint(0, 10 ** max_digits - 1)
    num2 = random.randint(1, 10 ** max_digits - 1)
    operation = random.choice(operations)

    if operation == '/' and num2 == 0:
        num2 = 1

    problem_str = f"{num1} {operation} {num2}"

    try:
        answer = eval(problem_str)
        if operation == '/':
            answer = round(answer, 4)
        else:
            answer = int(answer)
    except ZeroDivisionError:
        return generate_problem(max_digits, operations)
    except Exception:
        return generate_problem(max_digits, operations)

    return problem_str, answer


def _sha256_of_file(path: Path) -> str:
    """计算文件的SHA256哈希"""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def generate_dataset(
    output_dir: str,
    filename_prefix: str,
    num_samples: int,
    max_digits: int = 3,
    file_format: str = "csv"
) -> Optional[Dict[str, Any]]:
    """生成算术问题数据集并保存"""
    problems = []

    for _ in range(num_samples):
        problem, answer = generate_problem(max_digits=max_digits)
        problems.append({"problem": problem, "answer": str(answer)})

    os.makedirs(output_dir, exist_ok=True)

    metadata = {
        "problems": problems,
        "num_samples": num_samples,
        "filename_prefix": filename_prefix,
        "file_format": file_format,
        "max_digits": max_digits,
    }

    if file_format == "csv":
        filepath = Path(output_dir) / f"{filename_prefix}.csv"
        tmp = filepath.with_suffix(filepath.suffix + ".tmp")
        with open(tmp, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["problem", "answer"])
            writer.writeheader()
            writer.writerows(problems)
        os.replace(tmp, filepath)
        print(f"生成 {num_samples} 个样本到 {filepath}")
    elif file_format == "json":
        filepath = Path(output_dir) / f"{filename_prefix}.json"
        json_text = json.dumps(problems, indent=2)
        _atomic_write_text(filepath, json_text)
        print(f"生成 {num_samples} 个样本到 {filepath}")
    else:
        print(f"不支持的文件格式: {file_format}")
        return None

    # 丰富元数据
    metadata.update({
        "output_path": str(filepath),
        "file_size_bytes": filepath.stat().st_size,
        "sha256": _sha256_of_file(filepath),
        "created_at": datetime.utcnow().isoformat() + "Z",
    })

    return metadata


def main():
    """主函数"""
    print("生成数学模型数据集...")

    metadata = generate_dataset(
        output_dir="data/raw_datasets",
        filename_prefix="math_train",
        num_samples=1000,
        max_digits=3,
        file_format="csv"
    )

    if metadata:
        print(f"数据集生成完成: {metadata['output_path']}")

    return metadata


if __name__ == "__main__":
    main()