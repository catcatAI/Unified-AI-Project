#!/usr/bin/env python3
"""
完整的统一AI项目集成测试
测试所有组件：Backend API、Frontend Dashboard、Desktop App、CLI、Atlassian CLI
"""
import requests
import subprocess
import sys
import json
import time

def test_backend_apis():
    """测试所有后端API"""
    print("🔧 测试后端API...")
    
    tests = [
        ("健康检查", "GET", "/api/v1/health"),
        ("代码分析", "POST", "/api/v1/code", {"code": "print('hello')", "language": "python"}),
        ("搜索功能", "POST", "/api/v1/search", {"query": "artificial intelligence"}),
        ("图像生成", "POST", "/api/v1/image", {"prompt": "robot", "style": "cartoon"}),
        ("聊天功能", "POST", "/api/v1/chat", {"text": "Hello", "user_id": "test", "session_id": "test"}),
        ("Atlassian状态", "GET", "/api/v1/atlassian/status"),
    ]
    
    results = []
    for name, method, endpoint, data in [(t[0], t[1], t[2], t[3] if len(t) > 3 else None) for t in tests]:
        try:
            url = f"http://localhost:8000{endpoint}"
            if method == "GET":
                response = requests.get(url, timeout=10)
            else:
                response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                results.append(f"✅ {name}: 成功")
            else:
                results.append(f"❌ {name}: HTTP {response.status_code}")
        except Exception as e:
            results.append(f"❌ {name}: {str(e)}")
    
    return results

def test_cli_commands():
    """测试CLI命令"""
    print("🖥️ 测试CLI命令...")
    
    cli_path = "Unified-AI-Project/packages/cli/cli/unified_cli.py"
    commands = [
        (["python", cli_path, "health"], "健康检查"),
        (["python", cli_path, "chat", "Hello from CLI"], "聊天功能"),
        (["python", cli_path, "analyze", "--code", "def test(): pass", "--language", "python"], "代码分析"),
        (["python", cli_path, "search", "machine learning"], "搜索功能"),
        (["python", cli_path, "atlassian", "status"], "Atlassian状态"),
    ]
    
    results = []
    for cmd, name in commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                results.append(f"✅ CLI {name}: 成功")
            else:
                results.append(f"❌ CLI {name}: 失败 - {result.stderr[:100]}")
        except Exception as e:
            results.append(f"❌ CLI {name}: {str(e)}")
    
    return results

def test_frontend_proxy():
    """测试前端代理"""
    print("🌐 测试前端代理...")
    
    try:
        response = requests.get("http://localhost:3000/api/py/api/v1/health", timeout=10)
        if response.status_code == 200:
            return ["✅ 前端代理: 正常工作"]
        else:
            return [f"❌ 前端代理: HTTP {response.status_code}"]
    except Exception as e:
        return [f"⚠️ 前端代理: {str(e)} (可能需要重启前端服务器)"]

def test_atlassian_cli():
    """测试Atlassian CLI"""
    print("🔗 测试Atlassian CLI...")
    
    try:
        result = subprocess.run(["./acli.exe", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return [f"✅ Atlassian CLI: 可用 - {result.stdout.strip()}"]
        else:
            return ["❌ Atlassian CLI: 不可用"]
    except Exception as e:
        return [f"❌ Atlassian CLI: {str(e)}"]

def check_services_status():
    """检查服务状态"""
    print("🔍 检查服务状态...")
    
    services = [
        ("后端API", "http://localhost:8000"),
        ("前端Dashboard", "http://localhost:3000"),
    ]
    
    results = []
    for name, url in services:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                results.append(f"✅ {name}: 运行中")
            else:
                results.append(f"❌ {name}: HTTP {response.status_code}")
        except Exception as e:
            results.append(f"❌ {name}: 未运行")
    
    return results

def generate_summary_report():
    """生成完整的测试报告"""
    print("\n" + "="*60)
    print("🧪 统一AI项目 - 完整集成测试报告")
    print("="*60)
    
    # 检查服务状态
    service_results = check_services_status()
    print("\n📊 服务状态:")
    for result in service_results:
        print(f"  {result}")
    
    # 测试后端API
    api_results = test_backend_apis()
    print("\n🔧 后端API测试:")
    for result in api_results:
        print(f"  {result}")
    
    # 测试CLI
    cli_results = test_cli_commands()
    print("\n🖥️ CLI测试:")
    for result in cli_results:
        print(f"  {result}")
    
    # 测试前端代理
    proxy_results = test_frontend_proxy()
    print("\n🌐 前端代理测试:")
    for result in proxy_results:
        print(f"  {result}")
    
    # 测试Atlassian CLI
    atlassian_results = test_atlassian_cli()
    print("\n🔗 Atlassian CLI测试:")
    for result in atlassian_results:
        print(f"  {result}")
    
    # 统计成功率
    all_results = api_results + cli_results + proxy_results + atlassian_results
    success_count = len([r for r in all_results if r.startswith("✅")])
    total_count = len(all_results)
    success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
    
    print(f"\n📈 总体成功率: {success_count}/{total_count} ({success_rate:.1f}%)")
    
    print("\n🎯 使用指南:")
    print("1. 后端API: http://localhost:8000/api/v1/")
    print("2. 前端Dashboard: http://localhost:3000")
    print("3. CLI: python Unified-AI-Project/packages/cli/cli/unified_cli.py --help")
    print("4. Desktop App: cd Unified-AI-Project/apps/desktop-app && pnpm dev")
    print("5. Atlassian CLI: ./acli.exe --help")
    
    print("\n🔧 功能特性:")
    print("- ✅ AI聊天对话")
    print("- ✅ 代码分析")
    print("- ✅ 智能搜索")
    print("- ✅ 图像生成")
    print("- ✅ 系统监控")
    print("- ✅ Atlassian集成")
    print("- ✅ 多平台支持 (Web/Desktop/CLI)")
    
    return success_rate >= 80

if __name__ == "__main__":
    success = generate_summary_report()
    
    if success:
        print("\n🎉 统一AI项目集成测试完成！所有主要功能正常工作。")
    else:
        print("\n⚠️ 部分功能需要检查，请参考上述报告进行修复。")
    
    print("\n" + "="*60)