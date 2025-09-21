#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查兼容性包脚本
用于验证项目依赖库的兼容性
"""

def check_compat_packages():
    """检查兼容性包"""
    print("正在检查兼容性包...")
    
    # 检查tf-keras
    try:
        import tf_keras
        print("✓ tf-keras 导入成功")
        print(f"  版本: {tf_keras.__version__}")
    except ImportError as e:
        print(f"✗ tf-keras 导入失败: {e}")
    
    # 检查tensorflow
    try:
        import tensorflow
        print("✓ tensorflow 导入成功")
        print(f"  版本: {tensorflow.__version__}")
    except ImportError as e:
        print(f"✗ tensorflow 导入失败: {e}")
    
    # 检查transformers
    try:
        import transformers
        print("✓ transformers 导入成功")
        print(f"  版本: {transformers.__version__}")
    except ImportError as e:
        print(f"✗ transformers 导入失败: {e}")
    
    # 检查sentence_transformers
    try:
        import sentence_transformers
        print("✓ sentence_transformers 导入成功")
        print(f"  版本: {sentence_transformers.__version__}")
    except ImportError as e:
        print(f"✗ sentence_transformers 导入失败: {e}")

if __name__ == "__main__":
    check_compat_packages()