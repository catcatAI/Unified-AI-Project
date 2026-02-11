#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数学模型评估脚本
用于评估训练好的算术计算模型
"""

import os
import json
import csv
from typing import Tuple, Optional, List, Dict, Any

# Add src directory to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.sys.path:
    sys.sys.path.insert(0, SRC_DIR)

# 修复相对导入
sys.sys.path.append(os.path.join(SCRIPT_DIR))

try:
    # 使用完整模块路径
    from src.tools.math_model.model import ArithmeticSeq2Seq
except ImportError as e:
    print(f"Error importing from model: {e}")
    sys.sys.exit(1)

# Configuration
TEST_DATASET_PATH = os.path.join(PROJECT_ROOT, "data", "raw_datasets", "arithmetic_test_dataset.csv")
MODEL_LOAD_PATH = os.path.join(PROJECT_ROOT, "data", "models", "arithmetic_model.keras")
CHAR_MAP_LOAD_PATH = os.path.join(PROJECT_ROOT, "data", "models", "arithmetic_char_maps.json")


def load_char_maps(file_path: str) -> Optional[Tuple[Dict[str, int], Dict[int, str], int, int, int]]:
    """从JSON文件加载字符令牌映射"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            char_map_data = json.load(f)
        return (
            char_map_data['char_to_token'],
            char_map_data['token_to_char'],
            char_map_data['n_token'],
            char_map_data['max_encoder_seq_length'],
            char_map_data['max_decoder_seq_length']
        )
    except FileNotFoundError:
        print(f"Error: 字符映射文件未找到于 {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: 无法从 {file_path} 解码JSON")
        return None


def load_test_dataset_csv(file_path: str) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """从CSV文件加载测试数据集"""
    problems: List[Dict[str, str]] = []
    answers: List[Dict[str, str]] = []
    
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                problems.append({'problem': row['problem']})
                answers.append({'answer': row['answer']})
    except FileNotFoundError:
        print(f"Error: 测试数据集文件未找到于 {file_path}")
        print("请先使用data_generator.py生成数据集")
    except Exception as e:
        print(f"Error loading CSV: {e}")
    
    return problems, answers  # 总是返回列表


def main() -> None:
    """主评估函数"""
    print("开始评估过程...")

    # 1. 加载字符映射
    print(f"从 {CHAR_MAP_LOAD_PATH} 加载字符映射...")
    maps_data = load_char_maps(CHAR_MAP_LOAD_PATH)
    if maps_data is None:
        return
    char_to_token, token_to_char, n_token, max_encoder_seq_length, max_decoder_seq_length = maps_data

    # 2. 加载训练好的模型
    print(f"从 {MODEL_LOAD_PATH} 加载训练好的模型...")
    try:
        # 首先重建模型架构
        # 注意：latent_dim和embedding_dim最好与char_maps一起保存或在模型配置中保存
        # 现在使用train.py中的相同值；考虑重构这一点。
        latent_dim = 256
        embedding_dim = 128

        math_model_shell = ArithmeticSeq2Seq(
            char_to_token, token_to_char,
            max_encoder_seq_length, max_decoder_seq_length,
            n_token, latent_dim, embedding_dim
        )
        # 修复模型构建方式
        math_model_shell._build_inference_models()
        # 修复模型加载方式
        if math_model_shell.model is not None:
            math_model_shell.model.load_weights(MODEL_LOAD_PATH)  # 将权重加载到训练模型结构中

        # math_model_shell内部的推理模型（encoder_model、decoder_model）
        # 现在应该具有训练好的权重，因为它们与math_model_shell.model共享层
        print("模型加载成功。")
    except Exception as e:
        print(f"Error loading model: {e}")
        print(f"确保模型在训练后正确保存于 {MODEL_LOAD_PATH}。")
        return

    # 3. 加载测试数据
    print(f"从 {TEST_DATASET_PATH} 加载测试数据集...")
    test_problems, test_answers = load_test_dataset_csv(TEST_DATASET_PATH)
    # 移除None检查，因为我们现在总是返回列表
    print(f"已加载 {len(test_problems)} 个测试样本。")

    # 4. 评估模型
    correct_predictions = 0
    num_samples_to_show = 5

    print(f"\n--- 评估 {len(test_problems)} 个样本 ---")
    for i in range(len(test_problems)):
        input_problem_str = test_problems[i]['problem']
        expected_answer_str = test_answers[i]['answer']

        predicted_answer_str = math_model_shell.predict_sequence(input_problem_str)

        if i < num_samples_to_show:
            print(f"Problem: \"{input_problem_str}\"")
            print(f"Expected: \"{expected_answer_str}\", Got: \"{predicted_answer_str}\"")

        # 标准化答案以便比较（例如 "2.0" vs "2"）
        try:
            if float(predicted_answer_str) == float(expected_answer_str):
                correct_predictions += 1
                if i < num_samples_to_show:
                    print("Result: CORRECT")
            else:
                if i < num_samples_to_show:
                    print("Result: INCORRECT")
        except ValueError:
            # 如果转换为float失败（例如空或格式错误的预测）
            if predicted_answer_str == expected_answer_str:
                # 处理空字符串等情况（如果这是有效的）
                correct_predictions += 1
                if i < num_samples_to_show:
                    print("Result: CORRECT (非数值匹配)")
            else:
                if i < num_samples_to_show:
                    print("Result: INCORRECT (预测不是数字)")
        
        if i < num_samples_to_show:
            print("---")

    accuracy = (correct_predictions / len(test_problems)) * 100
    print(f"\n评估完成。")
    print(f"总测试样本: {len(test_problems)}")
    print(f"正确预测: {correct_predictions}")
    print(f"准确率: {accuracy:.2f}%")


if __name__ == "__main__":
    # 修复文件检查方式
    if not os.path.exists(MODEL_LOAD_PATH) or not os.path.exists(CHAR_MAP_LOAD_PATH):
        print("模型文件或字符映射文件未找到。")
        print(f"确保 '{MODEL_LOAD_PATH}' 和 '{CHAR_MAP_LOAD_PATH}' 存在。")
        print("请先使用train.py训练模型。")
    elif not os.path.exists(TEST_DATASET_PATH):
        print(f"测试数据集未找到于 {TEST_DATASET_PATH}。")
        print("请运行 `python src/tools/math_model/data_generator.py` 生成测试数据集（CSV格式）。")
    else:
        main()
