#!/usr/bin/env python3
"""
Angela AI - Configuration Initialization Script
配置初始化脚本

帮助用户设置 .env 文件并生成安全密钥。
"""

import os
import sys
import shutil
from pathlib import Path
from cryptography.fernet import Fernet
import logging
logger = logging.getLogger(__name__)


def print_header(text: str) -> None:
    """打印标题"""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def print_success(text: str) -> None:
    """打印成功消息"""
    print(f"✓ {text}")


def print_error(text: str) -> None:
    """打印错误消息"""
    print(f"✗ {text}", file=sys.stderr)


def print_info(text: str) -> None:
    """打印信息"""
    print(f"ℹ️  {text}")


def generate_secure_key() -> str:
    """生成安全的密钥"""
    return Fernet.generate_key().decode()


def copy_env_example() -> bool:
    """复制 .env.example 到 .env"""
    env_example = Path.cwd() / ".env.example"
    env_file = Path.cwd() / ".env"
    
    if env_file.exists():
        response = input(f"{env_file} 已存在，是否覆盖？:")
        if response.lower() != 'y':
            print_info("跳过 .env 文件创建")
            return False
    
    if not env_example.exists():
        print_error(f"找不到 .env.example 文件: {env_example}")
        return False
    
    shutil.copy(env_example, env_file)
    print_success(f"已创建 .env 文件: {env_file}")
    return True


def update_env_file_with_keys() -> bool:
    """更新 .env 文件中的密钥"""
    env_file = Path.cwd() / ".env"
    
    if not env_file.exists():
        print_error(f".env 文件不存在: {env_file}")
        return False
    
    # 生成密钥
    key_a = generate_secure_key()
    key_b = generate_secure_key()
    key_c = generate_secure_key()
    
    # 读取文件内容
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换密钥占位符
    content = content.replace("your_key_a_minimum_32_chars", key_a)
    content = content.replace("your_key_b_minimum_32_chars", key_b)
    content = content.replace("your_key_c_minimum_32_chars", key_c)
    
    # 写回文件
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print_success("已生成安全密钥并更新 .env 文件")
    print_info("密钥已生成:")
    print(f"  - ANGELA_KEY_A: {key_a[:16]}...")
    print(f"  - ANGELA_KEY_B: {key_b[:16]}...")
    print(f"  - ANGELA_KEY_C: {key_c[:16]}...")
    return True


def create_directories() -> bool:
    """创建必要的目录"""
    directories = [
        "logs",
        "data",
        "data/vector_db",
        "model_cache",
        "test_data",
    ]
    
    success = True
    for dir_name in directories:
        dir_path = Path.cwd() / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print_success(f"已创建目录: {dir_name}")
        else:
            print_info(f"目录已存在: {dir_name}")
    
    return success


def validate_config() -> bool:
    """验证配置"""
    try:
        from apps.backend.src.core.config_validator import ConfigValidator
        from apps.backend.src.core.config_loader import Config
        
        print_info("正在验证配置...")
        
        # 运行配置验证器
        validator = ConfigValidator()
        result = validator.validate()
        
        if not result.valid:
            print_error("配置验证失败")
            for error in result.errors:
                print_error(f"  - {error}")
            return False
        
        # 尝试加载配置
        config = Config.load()
        valid, errors = config.validate()
        
        if not valid:
            print_error("配置加载失败")
            for error in errors:
                print_error(f"  - {error}")
            return False
        
        print_success("配置验证通过")
        return True
        
    except ImportError as e:
        print_error(f"无法导入配置模块: {e}")
        return False
    except Exception as e:
        logger.error(f'Error in {__name__}: {e}', exc_info=True)
        print_error(f"配置验证出错: {e}")

        return False


def main():
    """主函数"""
    print_header("Angela AI - 配置初始化")
    
    # 检查当前目录
    if not (Path.cwd() / ".env.example").exists():
        print_error("请在项目根目录运行此脚本")
        print_info("当前目录:", Path.cwd())
        sys.exit(1)
    
    steps = [
        ("创建 .env 文件", copy_env_example),
        ("生成安全密钥", update_env_file_with_keys),
        ("创建必要目录", create_directories),
        ("验证配置", validate_config),
    ]
    
    all_success = True
    for step_name, step_func in steps:
        print_info(f"\n步骤: {step_name}")
        try:
            if not step_func():
                all_success = False
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            print_error(f"{step_name} 失败: {e}")

            all_success = False
    
    print_header("初始化完成")
    
    if all_success:
        print_success("所有步骤完成！")
        print_info("\n下一步:")
        print_info("  1. 根据需要编辑 .env 文件")
        print_info("  2. 运行: python -m apps.backend.src.core.config_validator")
        print_info("  3. 启动 Angela: python run_angela.py")
        sys.exit(0)
    else:
        print_error("部分步骤失败，请检查错误信息")
        print_info("\n提示:")
        print_info("  - 检查 .env 文件是否存在")
        print_info("  - 确保已安装所有依赖: pip install -r requirements.txt")
        sys.exit(1)


if __name__ == "__main__":
    main()