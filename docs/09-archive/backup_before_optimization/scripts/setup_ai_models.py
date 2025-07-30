#!/usr/bin/env python3
"""
AI 模型环境设置脚本
自动化设置 AI 模型服务的环境和依赖
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_python_version():
    """检查 Python 版本"""
    if sys.version_info < (3, 8):
        print("❌ 需要 Python 3.8 或更高版本")
        sys.exit(1)
    print(f"✅ Python 版本: {sys.version}")

def install_dependencies():
    """安装依赖项"""
    print("📦 安装依赖项...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        print("✅ 依赖项安装完成")
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖项安装失败: {e}")
        return False
    
    return True

def setup_env_file():
    """设置环境变量文件"""
    print("🔧 设置环境变量...")
    
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if not env_example.exists():
        print("❌ .env.example 文件不存在")
        return False
    
    if not env_file.exists():
        # 复制示例文件
        with open(env_example, 'r', encoding='utf-8') as f:
            content = f.read()
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 已创建 .env 文件")
        print("⚠️  请编辑 .env 文件，添加你的 API 密钥")
    else:
        print("✅ .env 文件已存在")
    
    return True

def check_config_files():
    """检查配置文件"""
    print("📁 检查配置文件...")
    
    config_files = [
        "configs/multi_llm_config.json",
        "configs/api_keys.yaml"
    ]
    
    all_exist = True
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"✅ {config_file}")
        else:
            print(f"❌ {config_file} 不存在")
            all_exist = False
    
    return all_exist

def test_basic_functionality():
    """测试基本功能"""
    print("🧪 测试基本功能...")
    
    try:
        # 测试导入
        sys.path.insert(0, str(Path.cwd()))
        from src.services.multi_llm_service import MultiLLMService
        print("✅ 模块导入成功")
        
        # 测试配置加载
        config_path = "configs/multi_llm_config.json"
        if Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✅ 配置文件加载成功，包含 {len(config.get('models', {}))} 个模型")
        
        return True
        
    except Exception as e:
        print(f"❌ 基本功能测试失败: {e}")
        return False

def check_optional_services():
    """检查可选服务"""
    print("🔌 检查可选 AI 服务...")
    
    services = [
        ("openai", "OpenAI GPT"),
        ("anthropic", "Anthropic Claude"),
        ("google.generativeai", "Google Gemini"),
        ("cohere", "Cohere"),
    ]
    
    available_services = []
    
    for module, name in services:
        try:
            __import__(module)
            print(f"✅ {name}")
            available_services.append(name)
        except ImportError:
            print(f"⚠️  {name} - 未安装")
    
    if available_services:
        print(f"📊 可用服务: {len(available_services)}/{len(services)}")
    else:
        print("⚠️  没有可用的 AI 服务，请安装相关依赖")
    
    return available_services

def setup_ollama():
    """设置 Ollama（可选）"""
    print("\n🦙 Ollama 本地模型设置（可选）:")
    
    try:
        # 检查 Ollama 是否安装
        result = subprocess.run(["ollama", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ollama 已安装")
            
            # 检查是否有模型
            result = subprocess.run(["ollama", "list"], 
                                  capture_output=True, text=True)
            if "llama2" in result.stdout:
                print("✅ 已有 Llama2 模型")
            else:
                print("💡 建议安装 Llama2 模型:")
                print("   ollama pull llama2:7b")
        else:
            print("⚠️  Ollama 未安装")
            print("💡 安装 Ollama: https://ollama.ai/")
    
    except FileNotFoundError:
        print("⚠️  Ollama 未安装")
        print("💡 安装 Ollama: https://ollama.ai/")

def print_usage_guide():
    """打印使用指南"""
    print("\n" + "="*60)
    print("🎉 设置完成！")
    print("\n📚 使用指南:")
    print("1. 配置 API 密钥:")
    print("   编辑 .env 文件，添加你的 API 密钥")
    print("\n2. 列出可用模型:")
    print("   python scripts/ai_models.py list")
    print("\n3. 单次查询:")
    print("   python scripts/ai_models.py query '你好' --model gpt-4")
    print("\n4. 进入聊天模式:")
    print("   python scripts/ai_models.py chat --model gemini-pro --stream")
    print("\n5. 健康检查:")
    print("   python scripts/ai_models.py health")
    print("\n6. 查看文档:")
    print("   cat README_AI_MODELS.md")

def main():
    """主函数"""
    print("🚀 AI 模型环境设置")
    print("="*60)
    
    # 检查 Python 版本
    check_python_version()
    
    # 安装依赖
    if not install_dependencies():
        sys.exit(1)
    
    # 设置环境文件
    if not setup_env_file():
        sys.exit(1)
    
    # 检查配置文件
    if not check_config_files():
        print("⚠️  某些配置文件缺失，但可以继续")
    
    # 测试基本功能
    if not test_basic_functionality():
        print("⚠️  基本功能测试失败，请检查配置")
    
    # 检查可选服务
    available_services = check_optional_services()
    
    # 设置 Ollama
    setup_ollama()
    
    # 打印使用指南
    print_usage_guide()

if __name__ == "__main__":
    main()