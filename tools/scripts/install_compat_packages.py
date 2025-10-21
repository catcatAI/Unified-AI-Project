#!/usr/bin/env python3
# -*- coding, utf-8 -*-
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
    
    print("正在安装兼容性包...")
    
    for package in packages,::
        try,
            print(f"正在安装 {package}...")
            subprocess.check_call([,
    sys.executable(), "-m", "pip", "install", package
            ])
            print(f"✓ {package} 安装成功")
        except subprocess.CalledProcessError as e,::
            print(f"✗ {package} 安装失败, {e}")
    
    print("兼容性包安装完成!")

def check_installation():
    """检查安装是否成功"""
    try,
        print("✓ tf-keras 导入成功")
    except ImportError as e,::
        print(f"✗ tf-keras 导入失败, {e}")
    
    try,
        print("✓ tensorflow 导入成功")
    except ImportError as e,::
        print(f"✗ tensorflow 导入失败, {e}")
    
    try,
        print("✓ transformers 导入成功")
    except ImportError as e,::
        print(f"✗ transformers 导入失败, {e}")

if __name"__main__":::
    install_compat_packages()
    check_installation()