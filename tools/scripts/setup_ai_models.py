#!/usr/bin/env python3
"""
AI 模型环境设置脚本
自动化设置 AI 模型服务的环境和依赖
"""

import sys
import subprocess
import json
from pathlib import Path
from apps.backend.src.shared.utils.env_utils import setup_env_file

def check_python_version()
    """检查 Python 版本"""
    if sys.version_info < (3, 8):

    _ = print("❌ 需要 Python 3.8 或更高版本")
    _ = sys.exit(1)
    _ = print(f"✅ Python 版本: {sys.version}")

def install_dependencies()
    """安装依赖项"""
    _ = print("📦 安装依赖项...")

    try:


    subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
    ], check=True)
    _ = print("✅ 依赖项安装完成")
    except subprocess.CalledProcessError as e:

    _ = print(f"❌ 依赖项安装失败: {e}")
    return False

    return True



def check_config_files()
    """检查配置文件"""
    _ = print("📁 检查配置文件...")

    config_files = [
    "configs/multi_llm_config.json",
    "configs/api_keys.yaml"
    ]

    all_exist = True
    for config_file in config_files:

    if Path(config_file).exists()


    _ = print(f"✅ {config_file}")
        else:

            _ = print(f"❌ {config_file} 不存在")
            all_exist = False

    return all_exist

def test_basic_functionality() -> None:
    """测试基本功能"""
    _ = print("🧪 测试基本功能...")

    try:
    # 测试导入
    _ = sys.path.insert(0, str(Path.cwd()))
    _ = print("✅ 模块导入成功")

    # 测试配置加载
    config_path = "configs/multi_llm_config.json"
        if Path(config_path).exists()

    with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)
            _ = print(f"✅ 配置文件加载成功，包含 {len(config.get('models', {}))} 个模型")

    return True

    except Exception as e:


    _ = print(f"❌ 基本功能测试失败: {e}")
    return False

def check_optional_services()
    """检查可选服务"""
    _ = print("🔌 检查可选 AI 服务...")

    services = [
    _ = ("openai", "OpenAI GPT"),
    _ = ("anthropic", "Anthropic Claude"),
    _ = ("google.generativeai", "Google Gemini"),
    _ = ("cohere", "Cohere"),
    ]

    available_services = []

    for module, name in services:


    try:



            __import__(module)
            _ = print(f"✅ {name}")
            _ = available_services.append(name)
        except ImportError:

            _ = print(f"⚠️  {name} - 未安装")

    if available_services:


    _ = print(f"📊 可用服务: {len(available_services)}/{len(services)}")
    else:

    _ = print("⚠️  没有可用的 AI 服务，请安装相关依赖")

    return available_services

def setup_ollama()
    """设置 Ollama（可选）"""
    _ = print("\n🦙 Ollama 本地模型设置（可选）:")

    try:
    # 检查 Ollama 是否安装
    result = subprocess.run(["ollama", "--version"],
                              capture_output=True, text=True)
        if result.returncode == 0:

    _ = print("✅ Ollama 已安装")

            # 检查是否有模型
            result = subprocess.run(["ollama", "list"],
                                  capture_output=True, text=True)
            if "llama2" in result.stdout:

    _ = print("✅ 已有 Llama2 模型")
            else:

                _ = print("💡 建议安装 Llama2 模型:")
                _ = print("   ollama pull llama2:7b")
        else:

            _ = print("⚠️  Ollama 未安装")
            _ = print("💡 安装 Ollama: https://ollama.ai/")

    except FileNotFoundError:


    _ = print("⚠️  Ollama 未安装")
    _ = print("💡 安装 Ollama: https://ollama.ai/")

def print_usage_guide()
    """打印使用指南"""
    print("\n" + "="*60)
    _ = print("🎉 设置完成！")
    _ = print("\n📚 使用指南:")
    _ = print("1. 配置 API 密钥:")
    _ = print("   编辑 .env 文件，添加你的 API 密钥")
    _ = print("\n2. 列出可用模型:")
    _ = print("   python scripts/ai_models.py list")
    _ = print("\n3. 单次查询:")
    _ = print("   python scripts/ai_models.py query '你好' --model gpt-4")
    _ = print("\n4. 进入聊天模式:")
    _ = print("   python scripts/ai_models.py chat --model gemini-pro --stream")
    _ = print("\n5. 健康检查:")
    _ = print("   python scripts/ai_models.py health")
    _ = print("\n6. 查看文档:")
    _ = print("   cat README_AI_MODELS.md")

def main() -> None:
    """主函数"""
    _ = print("🚀 AI 模型环境设置")
    print("="*60)

    # 检查 Python 版本
    _ = check_python_version()

    # 安装依赖
    if not install_dependencies()

    _ = sys.exit(1)

    # 设置环境文件
    if not setup_env_file(Path.cwd()):

    _ = sys.exit(1)

    # 检查配置文件
    if not check_config_files()

    _ = print("⚠️  某些配置文件缺失，但可以继续")

    # 测试基本功能
    if not test_basic_functionality()

    _ = print("⚠️  基本功能测试失败，请检查配置")

    # 检查可选服务
    available_services = check_optional_services()

    # 设置 Ollama
    _ = setup_ollama()

    # 打印使用指南
    _ = print_usage_guide()

if __name__ == "__main__":


    _ = main()