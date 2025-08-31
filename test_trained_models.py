#!/usr/bin/env python3
"""
测试训练好的模型
"""

import sys
import os
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent
BACKEND_PATH = PROJECT_ROOT / "apps" / "backend"
sys.path.insert(0, str(BACKEND_PATH))
sys.path.insert(0, str(BACKEND_PATH / "src"))

def test_math_model_loading():
    """测试数学模型加载"""
    print("\n=== 测试数学模型加载 ===")
    
    try:
        # 检查模型文件是否存在
        model_path = BACKEND_PATH / "data" / "models" / "arithmetic_model.keras"
        char_map_path = BACKEND_PATH / "data" / "models" / "arithmetic_char_maps.json"
        
        if not model_path.exists():
            print(f"❌ 数学模型文件不存在: {model_path}")
            return False
            
        if not char_map_path.exists():
            print(f"❌ 数学模型字符映射文件不存在: {char_map_path}")
            return False
            
        print("✅ 数学模型文件存在")
        
        # 尝试加载模型
        from src.tools.math_model.model import ArithmeticSeq2Seq
        import json
        
        # 加载字符映射
        with open(char_map_path, 'r', encoding='utf-8') as f:
            char_maps = json.load(f)
        
        print("✅ 字符映射加载成功")
        print(f"  - 唯一标记数: {char_maps.get('n_token', '未知')}")
        print(f"  - 最大编码器序列长度: {char_maps.get('max_encoder_seq_length', '未知')}")
        print(f"  - 最大解码器序列长度: {char_maps.get('max_decoder_seq_length', '未知')}")
        
        # 创建模型实例
        math_model = ArithmeticSeq2Seq.load_for_inference(
            str(model_path),
            str(char_map_path)
        )
        
        if math_model is None:
            print("❌ 数学模型加载失败")
            return False
            
        print("✅ 数学模型加载成功")
        return True
        
    except ImportError as e:
        print(f"❌ 无法导入数学模型模块: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试数学模型加载时发生错误: {e}")
        return False

def test_logic_model_loading():
    """测试逻辑模型加载"""
    print("\n=== 测试逻辑模型加载 ===")
    
    try:
        # 检查模型文件是否存在
        model_path = BACKEND_PATH / "data" / "models" / "logic_model_nn.keras"
        char_map_path = BACKEND_PATH / "data" / "models" / "logic_model_char_maps.json"
        
        if not model_path.exists():
            print(f"❌ 逻辑模型文件不存在: {model_path}")
            return False
            
        if not char_map_path.exists():
            print(f"❌ 逻辑模型字符映射文件不存在: {char_map_path}")
            return False
            
        print("✅ 逻辑模型文件存在")
        
        # 尝试加载模型
        from src.tools.logic_model.logic_model_nn import LogicNNModel
        import json
        
        # 加载字符映射
        with open(char_map_path, 'r', encoding='utf-8') as f:
            char_maps = json.load(f)
        
        print("✅ 字符映射加载成功")
        print(f"  - 词汇表大小: {char_maps.get('vocab_size', '未知')}")
        print(f"  - 最大序列长度: {char_maps.get('max_seq_len', '未知')}")
        
        # 创建模型实例
        logic_model = LogicNNModel.load_model(
            str(model_path),
            str(char_map_path)
        )
        
        if logic_model is None:
            print("❌ 逻辑模型加载失败")
            return False
            
        print("✅ 逻辑模型加载成功")
        return True
        
    except ImportError as e:
        print(f"❌ 无法导入逻辑模型模块: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试逻辑模型加载时发生错误: {e}")
        return False

def test_math_model_prediction():
    """测试数学模型预测"""
    print("\n=== 测试数学模型预测 ===")
    
    try:
        from src.tools.math_model.model import ArithmeticSeq2Seq
        import json
        
        # 加载模型
        model_path = BACKEND_PATH / "data" / "models" / "arithmetic_model.keras"
        char_map_path = BACKEND_PATH / "data" / "models" / "arithmetic_char_maps.json"
        
        if not model_path.exists() or not char_map_path.exists():
            print("❌ 模型文件不存在，无法进行预测测试")
            return False
        
        math_model = ArithmeticSeq2Seq.load_for_inference(
            str(model_path),
            str(char_map_path)
        )
        
        if math_model is None:
            print("❌ 数学模型加载失败，无法进行预测测试")
            return False
        
        # 测试一些简单的数学计算
        test_cases = [
            "10 + 5",
            "20 - 8",
            "6 * 7",
            "45 / 9"
        ]
        
        print("测试数学计算:")
        for case in test_cases:
            try:
                result = math_model.predict_sequence(case)
                print(f"  {case} = {result}")
            except Exception as e:
                print(f"  {case} -> 错误: {e}")
                
        return True
        
    except Exception as e:
        print(f"❌ 测试数学模型预测时发生错误: {e}")
        return False

def test_logic_model_prediction():
    """测试逻辑模型预测"""
    print("\n=== 测试逻辑模型预测 ===")
    
    try:
        from src.tools.logic_model.logic_model_nn import LogicNNModel
        import json
        
        # 加载模型
        model_path = BACKEND_PATH / "data" / "models" / "logic_model_nn.keras"
        char_map_path = BACKEND_PATH / "data" / "models" / "logic_model_char_maps.json"
        
        if not model_path.exists() or not char_map_path.exists():
            print("❌ 模型文件不存在，无法进行预测测试")
            return False
        
        logic_model = LogicNNModel.load_model(
            str(model_path),
            str(char_map_path)
        )
        
        if logic_model is None:
            print("❌ 逻辑模型加载失败，无法进行预测测试")
            return False
        
        # 加载字符映射以用于预测
        with open(char_map_path, 'r', encoding='utf-8') as f:
            char_maps_data = json.load(f)
            char_to_token = char_maps_data['char_to_token']
        
        # 测试一些简单的逻辑表达式
        test_cases = [
            "true AND false",
            "true OR false",
            "NOT true",
            "NOT false"
        ]
        
        print("测试逻辑表达式:")
        for case in test_cases:
            try:
                result = logic_model.predict(case, char_to_token)
                print(f"  {case} = {result}")
            except Exception as e:
                print(f"  {case} -> 错误: {e}")
                
        return True
        
    except Exception as e:
        print(f"❌ 测试逻辑模型预测时发生错误: {e}")
        return False

def main():
    print("=== Unified AI Project - 训练模型测试 ===")
    
    # 测试数学模型加载
    math_load_success = test_math_model_loading()
    
    # 测试逻辑模型加载
    logic_load_success = test_logic_model_loading()
    
    # 如果模型加载成功，测试预测功能
    if math_load_success:
        test_math_model_prediction()
    
    if logic_load_success:
        test_logic_model_prediction()
    
    print("\n=== 测试完成 ===")
    print(f"数学模型加载: {'✅ 成功' if math_load_success else '❌ 失败'}")
    print(f"逻辑模型加载: {'✅ 成功' if logic_load_success else '❌ 失败'}")
    
    if math_load_success and logic_load_success:
        print("🎉 所有模型测试通过！")
        return True
    else:
        print("⚠️ 部分模型测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)