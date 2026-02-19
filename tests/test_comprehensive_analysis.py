#!/usr/bin/env python3
"""Comprehensive analysis of Angela AI system issues"""

import sys
import os
import asyncio
import time
import json
import logging
logger = logging.getLogger(__name__)

# Add apps/backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'apps/backend')
sys.path.insert(0, backend_path)

from src.services.angela_llm_service import AngelaLLMService, get_llm_service

class IssueAnalyzer:
    def __init__(self):
        self.issues = []

    def add_issue(self, category, severity, description, analysis, fix):
        self.issues.append({
            "category": category,
            "severity": severity,
            "description": description,
            "analysis": analysis,
            "fix": fix
        })

    def print_report(self):
        print("=" * 80)
        print("ANGELA AI 系统问题分析报告")
        print("=" * 80)
        print(f"日期: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"发现的问题数: {len(self.issues)}")
        print()

        # Group by severity
        critical = [i for i in self.issues if i['severity'] == 'CRITICAL']
        high = [i for i in self.issues if i['severity'] == 'HIGH']
        medium = [i for i in self.issues if i['severity'] == 'MEDIUM']
        low = [i for i in self.issues if i['severity'] == 'LOW']

        for severity, issues in [('CRITICAL', critical), ('HIGH', high),
                                   ('MEDIUM', medium), ('LOW', low)]:
            if issues:
                print(f"\n{'=' * 80}")
                print(f"{severity} 优先级问题 ({len(issues)} 个)")
                print(f"{'=' * 80}")
                for i, issue in enumerate(issues, 1):
                    print(f"\n问题 {i}: {issue['category']}")
                    print(f"描述: {issue['description']}")
                    print(f"分析: {issue['analysis']}")
                    print(f"修复: {issue['fix']}")
                    print()

async def analyze_llm_timeout(analyzer):
    """分析 LLM 超时问题"""
    print("\n[1] 分析 LLM 超时问题...")
    service = await get_llm_service()

    # 检查配置
    config = service.config
    print(f"配置: {json.dumps(config, indent=2, ensure_ascii=False)}")

    # 检查超时设置
    for backend_name, backend in service.backends.items():
        print(f"\n后端: {backend_name}")
        print(f"  超时设置: {getattr(backend, 'timeout', 'N/A')}")

    # 测试响应时间
    print("\n测试响应时间...")
    test_cases = [
        "你好",
        "今天天气怎么样？",
        "我很开心",
        "我很难过"
    ]

    response_times = []
    for msg in test_cases:
        start = time.time()
        result = await service.generate_response(msg)
        elapsed = (time.time() - start) * 1000
        response_times.append(elapsed)
        print(f"  '{msg}': {elapsed:.2f}ms (backend: {result.backend})")

    avg_time = sum(response_times) / len(response_times)
    print(f"\n平均响应时间: {avg_time:.2f}ms")

    # 分析
    if avg_time < 10:
        analyzer.add_issue(
            "LLM 服务",
            "HIGH",
            "LLM 响应时间异常快速 (<10ms)，可能是 fallback 机制",
            f"平均响应时间 {avg_time:.2f}ms，远低于正常的 LLM 响应时间",
            "1. 检查 Ollama 服务是否正常运行\n2. 增加超时时间到 60 秒\n3. 添加重试机制"
        )
    elif avg_time > 30000:
        analyzer.add_issue(
            "LLM 服务",
            "HIGH",
            "LLM 响应时间过长 (>30秒)",
            f"平均响应时间 {avg_time:.2f}ms，超过 30 秒超时限制",
            "1. 增加超时时间到 60 秒\n2. 优化提示词减少 token 使用\n3. 使用更快的模型"
        )
    else:
        print("✅ LLM 响应时间正常")

async def analyze_emotion_recognition(analyzer):
    """分析情感识别系统"""
    print("\n[2] 分析情感识别系统...")
    service = await get_llm_service()

    # 测试用例
    test_cases = [
        ("我很开心", "happy"),
        ("我很难过", "sad"),
        ("我有点害怕", "fear"),
        ("我很好奇", "curious"),
        ("我很生气", "angry"),
        ("我很惊讶", "surprise"),
        ("我很平静", "calm"),
        ("不开心", "sad"),  # 否定词
        ("不难过", "calm"),  # 双重否定
        ("好开心", "happy"),  # 程度词
        ("太开心了", "happy"),  # 程度词
        ("真的很好奇", "curious"),  # 程度词
    ]

    passed = 0
    failed = []

    for text, expected in test_cases:
        result = service.analyze_emotion(text)
        detected = result['emotion']

        if detected == expected:
            passed += 1
        else:
            failed.append({
                "text": text,
                "expected": expected,
                "detected": detected,
                "confidence": result['confidence']
            })

    success_rate = (passed / len(test_cases)) * 100
    print(f"成功率: {passed}/{len(test_cases)} = {success_rate:.1f}%")

    if failed:
        print(f"\n失败的测试 ({len(failed)} 个):")
        for fail in failed:
            print(f"  '{fail['text']}'")
            print(f"    期望: {fail['expected']}, 实际: {fail['detected']}, 置信度: {fail['confidence']:.2f}")

    # 分析
    if success_rate < 95:
        analyzer.add_issue(
            "情感识别系统",
            "HIGH",
            f"情感识别成功率 {success_rate:.1f}%，低于目标 95%",
            f"{len(failed)} 个测试失败，主要集中在否定词和程度词处理",
            "1. 改进否定词检测逻辑\n2. 增强程度词权重计算\n3. 添加更多测试用例"
        )
    else:
        print("✅ 情感识别系统达到目标")

async def analyze_system_nodes(analyzer):
    """分析系统节点状态"""
    print("\n[3] 分析系统节点状态...")

    try:
        from src.system.cluster_manager import ClusterManager
        cluster = ClusterManager()

        # 获取节点状态
        nodes = cluster.get_all_nodes()
        offline_nodes = [n for n in nodes if n.get('status') == 'offline']

        print(f"总节点数: {len(nodes)}")
        print(f"离线节点数: {len(offline_nodes)}")

        for node in nodes:
            print(f"  {node['name']}: {node['status']}")

        if offline_nodes:
            for node in offline_nodes:
                analyzer.add_issue(
                    "系统节点",
                    "MEDIUM",
                    f"节点 {node['name']} 离线",
                    f"节点状态为 offline，可能影响系统性能",
                    "1. 检查节点服务是否启动\n2. 检查网络连接\n3. 检查资源分配"
                )
        else:
            print("✅ 所有节点正常")
    except Exception as e:
        print(f"⚠️  无法获取节点状态: {e}")

async def analyze_dialogue_container(analyzer):
    """分析前端对话容器"""
    print("\n[4] 分析前端对话容器...")

    # 检查 HTML 文件
    html_path = os.path.join(os.path.dirname(__file__), 'apps/desktop-app/electron_app/index.html')

    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        if 'dialogue-container' in html_content:
            print("✅ 对话容器存在于 HTML 中")
        else:
            # 检查是否动态创建
            js_files = [
                'apps/desktop-app/electron_app/js/dialogue-ui.js',
            ]

            for js_file in js_files:
                js_path = os.path.join(os.path.dirname(__file__), js_file)
                if os.path.exists(js_path):
                    with open(js_path, 'r', encoding='utf-8') as f:
                        js_content = f.read()

                    if "dialogue-container" in js_content and "createElement" in js_content:
                        print(f"✅ 对话容器在 {js_file} 中动态创建")
                        return

            analyzer.add_issue(
                "前端对话容器",
                "LOW",
                "对话容器未找到",
                "HTML 中缺少 id='dialogue-container' 元素，也未在 JS 中动态创建",
                "1. 在 HTML 中添加对话容器\n2. 或在 JS 中动态创建"
            )
    except Exception as e:
        print(f"⚠️  无法检查对话容器: {e}")

async def analyze_live2d_touch(analyzer):
    """分析 Live2D 触摸响应"""
    print("\n[5] 分析 Live2D 触摸响应...")

    # 检查相关文件
    files_to_check = [
        'apps/desktop-app/electron_app/js/live2d-manager.js',
        'apps/desktop-app/electron_app/js/character-touch-detector.js',
        'apps/desktop-app/electron_app/js/unified-display-matrix.js',
    ]

    touch_implementation = False

    for file_path in files_to_check:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if 'detectTouch' in content or 'handleTouch' in content:
                touch_implementation = True
                print(f"✅ {file_path} 包含触摸响应实现")
            else:
                print(f"⚠️  {file_path} 缺少触摸响应实现")

    if not touch_implementation:
        analyzer.add_issue(
            "Live2D 触摸响应",
            "MEDIUM",
            "Live2D 身体部位触摸响应功能缺失",
            "相关文件中未找到触摸响应实现",
            "1. 实现 detectTouch 方法\n2. 实现 handleTouch 方法\n3. 集成到 Live2D 管理器"
        )

async def main():
    analyzer = IssueAnalyzer()

    print("开始 Angela AI 系统深度分析...")
    print("=" * 80)

    await analyze_llm_timeout(analyzer)
    await analyze_emotion_recognition(analyzer)
    await analyze_system_nodes(analyzer)
    await analyze_dialogue_container(analyzer)
    await analyze_live2d_touch(analyzer)

    # 打印报告
    analyzer.print_report()

    # 保存报告
    report_file = os.path.join(os.path.dirname(__file__), 'ANGELA_AI_DEEP_ANALYSIS_REPORT.md')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Angela AI 系统深度分析报告\n\n")
        f.write(f"**日期**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## 发现的问题总数: {len(analyzer.issues)}\n\n")

        # 按严重性分组
        critical = [i for i in analyzer.issues if i['severity'] == 'CRITICAL']
        high = [i for i in analyzer.issues if i['severity'] == 'HIGH']
        medium = [i for i in analyzer.issues if i['severity'] == 'MEDIUM']
        low = [i for i in analyzer.issues if i['severity'] == 'LOW']

        for severity, issues in [('CRITICAL', critical), ('HIGH', high),
                                   ('MEDIUM', medium), ('LOW', low)]:
            if issues:
                f.write(f"## {severity} 优先级问题 ({len(issues)} 个)\n\n")
                for i, issue in enumerate(issues, 1):
                    f.write(f"### 问题 {i}: {issue['category']}\n\n")
                    f.write(f"**描述**: {issue['description']}\n\n")
                    f.write(f"**分析**: {issue['analysis']}\n\n")
                    f.write(f"**修复**: {issue['fix']}\n\n")
                    f.write("---\n\n")

    print(f"\n报告已保存到: {report_file}")

if __name__ == "__main__":
    asyncio.run(main())
