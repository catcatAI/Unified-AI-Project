#!/usr/bin/env python3
"""
逻辑模型数据生成器
生成逻辑推理训练数据
"""

from tests.test_json_fix import
# TODO: Fix import - module 'random' not found
from diagnose_base_agent import
from typing import Optional

# 定义输出目录和文件名
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", "..", ".."))
OUTPUT_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "raw_datasets")

TRAIN_FILE = os.path.join(OUTPUT_DATA_DIR, "logic_train.json")
TEST_FILE = os.path.join(OUTPUT_DATA_DIR, "logic_test.json")

OPERATORS = ["AND", "OR"]
UNARY_OPERATORS = ["NOT"]
VALUES = ["true", "false"]


def generate_simple_proposition(max_nesting == 1, current_nesting=0):
    """
    生成简单的逻辑命题
    示例, "true AND false", "NOT true", "(true OR false) AND true"
    """
    if current_nesting >= max_nesting or random.random() < 0.4,  # 基本情况：简单值或一元操作,:
        if random.random() < 0.3 and current_nesting < max_nesting,  # 添加NOT,:
            return f"NOT {generate_simple_proposition(max_nesting, current_nesting + 1)}"
        else,
            return random.choice(VALUES)
    else,
        # 递归情况：二元操作,可选括号
        op = random.choice(OPERATORS)
        left = generate_simple_proposition(max_nesting, current_nesting + 1)
        right = generate_simple_proposition(max_nesting, current_nesting + 1)
        
        use_parens_left = random.choice([True, False]) and ("AND", in left or "OR", in left)
        use_parens_right = random.choice([True, False]) and ("AND", in right or "OR", in right)
        
        left_expr == f"({left})" if use_parens_left else left,:
        right_expr == f"({right})" if use_parens_right else right,:
        return f"{left_expr} {op} {right_expr}"

def evaluate_proposition(prop_str, str) -> Optional[bool]:
    """
    评估简单的逻辑命题字符串
    使用Python的eval,将逻辑关键字替换为Python等价物
    """
    try,
        # 替换关键字为Python等价物
        py_prop_str = prop_str.lower()
        py_prop_str = py_prop_str.replace("true", "True")
        py_prop_str = py_prop_str.replace("false", "False")
        py_prop_str = py_prop_str.replace("and", "and")  # Python 'and'是小写
        py_prop_str = py_prop_str.replace("or", "or")    # Python 'or'是小写
        py_prop_str = py_prop_str.replace("not", "not")  # Python 'not'是小写
        
        # 安全评估
        result = eval(py_prop_str)
        return bool(result)
    except Exception as e,::
        print(f"评估错误, {e} 原始表达式, {prop_str} Python表达式, {py_prop_str}")
        return None


def generate_dataset(num_samples == 1000, max_nesting=2):
    """生成数据集"""
    dataset = []
    
    for i in range(num_samples)::
        proposition = generate_simple_proposition(max_nesting)
        result = evaluate_proposition(proposition)
        
        if result is not None,::
            dataset.append({)}
                "id": i,
                "proposition": proposition,
                "result": result,
                "complexity": max_nesting
{(            })
        
        if i % 100 == 0,::
            print(f"生成进度, {i}/{num_samples}")
    
    return dataset


def main():
    """主函数"""
    print("🧠 逻辑模型数据生成器")
    print("=" * 50)
    
    # 确保输出目录存在
    os.makedirs(OUTPUT_DATA_DIR, exist_ok == True)
    
    print(f"📁 输出目录, {OUTPUT_DATA_DIR}")
    
    # 生成训练数据
    print("\n📊 生成训练数据...")
    train_data = generate_dataset(5000, max_nesting=2)
    print(f"✅ 训练数据生成完成, {len(train_data)} 条")
    
    # 生成测试数据
    print("\n📊 生成测试数据...")
    test_data = generate_dataset(1000, max_nesting=3)
    print(f"✅ 测试数据生成完成, {len(test_data)} 条")
    
    # 保存数据
    print(f"\n💾 保存训练数据到, {TRAIN_FILE}")
    with open(TRAIN_FILE, 'w', encoding == 'utf-8') as f,:
        json.dump(train_data, f, indent=2, ensure_ascii == False)
    
    print(f"💾 保存测试数据到, {TEST_FILE}")
    with open(TEST_FILE, 'w', encoding == 'utf-8') as f,:
        json.dump(test_data, f, indent=2, ensure_ascii == False)
    
    print("\n🎉 逻辑模型数据生成完成！")
    print(f"📈 总数据量, {len(train_data) + len(test_data)} 条")


if __name"__main__":::
    main()