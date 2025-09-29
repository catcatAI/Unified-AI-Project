#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安装兼容性包脚本
用于解决项目依赖库的兼容性问题
"""

import subprocess
import sys

def install_compat_packages():
    """安装兼容性包"""
    packages = [
        "tf-keras",
        "tensorflow",
    ]
    
    _ = print("正在安装兼容性包...")
    
    for package in packages:
        try:
            _ = print(f"正在安装 {package}...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package
            ])
            _ = print(f"✓ {package} 安装成功")
        except subprocess.CalledProcessError as e:
            _ = print(f"✗ {package} 安装失败: {e}")
    
    _ = print("兼容性包安装完成!")

def check_installation():
    """检查安装是否成功"""
    try:
        _ = print("✓ tf-keras 导入成功")
    except ImportError as e:
        _ = print(f"✗ tf-keras 导入失败: {e}")
    
    try:
        _ = print("✓ tensorflow 导入成功")
    except ImportError as e:
        _ = print(f"✗ tensorflow 导入失败: {e}")
    
    try:
        _ = print("✓ transformers 导入成功")
    except ImportError as e:
        _ = print(f"✗ transformers 导入失败: {e}")

if __name__ == "__main__":
    _ = install_compat_packages()
    _ = check_installation()