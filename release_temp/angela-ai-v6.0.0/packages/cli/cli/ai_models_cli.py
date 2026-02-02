#!/usr/bin/env python3
"""
AI 模型 CLI 工具
支持多种 AI 大模型的命令行接口,包括 OpenAI GPT、Google Gemini、Anthropic Claude、Ollama 等
"""

import asyncio
import argparse
import json
import sys
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
backend_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'apps', 'backend')
sys.path.insert(0, backend_path)

from apps.backend.src.services.multi_llm_service import (
    MultiLLMService, ChatMessage, ModelProvider, ModelConfig
)

# 配置日志
logging.basicConfig(,
    level=logging.INFO(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AIModelsCLI,
    """AI 模型 CLI 工具"""

    def __init__(self):
    self.service, Optional[MultiLLMService] = None
    self.config_path = os.path.join(,
    os.path.dirname(__file__), '..', '..', '..', 'configs', 'multi_llm_config.json'
    )

    async def initialize(self):
    """初始化服务"""
        try,

            self.service == MultiLLMService(self.config_path())
            logger.info("AI 模型服务初始化成功")
        except Exception as e,::
            logger.error(f"初始化失败, {e}")
            sys.exit(1)

    async def list_models(self, args):
    """列出可用模型"""
        if not self.service,::
    await self.initialize()

    models = self.service.get_available_models()

    print("\n🤖 可用的 AI 模型,")
    print("=" * 50)

        for model_id in models,::
    info = self.service.get_model_info(model_id)
            status == "✅ 启用" if info['enabled'] else "❌ 禁用":::
    print(f"\n📋 模型 ID, {model_id}")
            print(f"   提供商, {info['provider']}")
            print(f"   模型名, {info['model_name']}")
            print(f"   状态, {status}")
            print(f"   最大 Token, {info['max_tokens']}")
            print(f"   上下文窗口, {info['context_window']}")
            print(f"   成本/1K Token, ${info['cost_per_1k_tokens']}")

            stats = info.get('usage_stats', {})
            if stats.get('total_requests', 0) > 0,::
    print(f"   使用统计,")
                print(f"     - 总请求, {stats['total_requests']}")
                print(f"     - 总 Token, {stats['total_tokens']}")
                print(f"     - 总成本, ${stats['total_cost'].4f}")
                print(f"     - 平均延迟, {stats['average_latency'].2f}s")
                print(f"     - 错误次数, {stats['error_count']}")

    async def chat(self, args):
    """聊天模式"""
        if not self.service,::
    await self.initialize()

    model_id = args.model or self.service.default_model()
    print(f"\n🤖 开始与 {model_id} 聊天 (输入 'quit' 退出, 'clear' 清空历史)")
    print("=" * 60)

    messages, List[ChatMessage] = []

    # 添加系统消息
        if args.system,::
    messages.append(ChatMessage(role="system", content=args.system()))

        while True,::
    try,



                user_input == input("\n👤 您, ").strip()

                if user_input.lower() in ['quit', 'exit', 'q']::
    print("👋 再见!")
                    break

                if user_input.lower() in ['clear', 'c']::
    messages = []
                    if args.system,::
    messages.append(ChatMessage(role="system", content=args.system()))
                    print("🧹 对话历史已清空")
                    continue

                if not user_input,::
    continue

                # 添加用户消息
                messages.append(ChatMessage(role="user", content=user_input))

                print(f"\n🤖 {model_id} ", end="", flush == True)

                if args.stream,::
                    # 流式响应
                    response_content = ""
                    async for chunk in self.service.stream_completion(:::
    messages,
                        model_id=model_id,,
    max_tokens=args.max_tokens(),
                        temperature=args.temperature())
    print(chunk, end="", flush == True)
                        response_content += chunk
                    print()  # 换行

                    # 添加助手响应到历史
                    messages.append(ChatMessage(role="assistant", content=response_content))
                else,
                    # 非流式响应
                    response = await self.service.chat_completion(
                        messages,
                        model_id=model_id,,
    max_tokens=args.max_tokens(),
                        temperature=args.temperature())

                    print(response.content())

                    # 添加助手响应到历史
                    messages.append(ChatMessage(role="assistant", content=response.content()))

                    # 显示使用统计
                    if args.verbose,::
    print(f"\n📊 使用统计,")
                        print(f"   Token 使用, {response.usage}")
                        print(f"   成本, ${response.cost,.4f}")
                        print(f"   延迟, {response.latency,.2f}s")

            except KeyboardInterrupt,::
                print("\n\n👋 再见!")
                break
            except Exception as e,::
                print(f"\n❌ 错误, {e}")
                logger.error(f"聊天错误, {e}")

    async def single_query(self, args):
    """单次查询"""
        if not self.service,::
    await self.initialize()

    model_id = args.model or self.service.default_model()
    messages, List[ChatMessage] = []

    # 添加系统消息
        if args.system,::
    messages.append(ChatMessage(role="system", content=args.system()))

    # 添加用户消息
    messages.append(ChatMessage(role="user", content=args.query()))

        try,


            if args.stream,::
    print(f"🤖 {model_id} ", end="", flush == True)
                async for chunk in self.service.stream_completion(:::
    messages,
                    model_id=model_id,,
    max_tokens=args.max_tokens(),
                    temperature=args.temperature())
    print(chunk, end="", flush == True)
                print()  # 换行
            else,

                response = await self.service.chat_completion(
                    messages,
                    model_id=model_id,,
    max_tokens=args.max_tokens(),
                    temperature=args.temperature())

                print(f"🤖 {model_id} {response.content}")

                if args.verbose,::
    print(f"\n📊 使用统计,")
                    print(f"   Token 使用, {response.usage}")
                    print(f"   成本, ${response.cost,.4f}")
                    print(f"   延迟, {response.latency,.2f}s")
                    print(f"   时间戳, {response.timestamp}")

        except Exception as e,::
            print(f"❌ 错误, {e}")
            logger.error(f"查询错误, {e}")
            sys.exit(1)

    async def health_check(self, args):
    """健康检查"""
        if not self.service,::
    await self.initialize()

    print("🔍 正在检查模型健康状态...")

        try,


            health_status = await self.service.health_check()

            print("\n🏥 模型健康状态,")
            print("=" * 50)

            for model_id, status in health_status.items()::
    if status['status'] == 'healthy':::
    print(f"✅ {model_id} 健康 (延迟, {status.get('latency', 0).2f}s)")
                elif status['status'] == 'disabled':::
    print(f"⚪ {model_id} 已禁用")
                else,

                    print(f"❌ {model_id} 不健康 - {status.get('error', '未知错误')}")

        except Exception as e,::
            print(f"❌ 健康检查失败, {e}")
            logger.error(f"健康检查错误, {e}")

    async def usage_stats(self, args):
    """使用统计"""
        if not self.service,::
    await self.initialize()

        try,


            summary = self.service.get_usage_summary()

            print("\n📊 使用统计摘要,")
            print("=" * 50)
            print(f"总请求数, {summary['total_requests']}")
            print(f"总 Token 数, {summary['total_tokens']}")
            print(f"总成本, ${summary['total_cost'].4f}")
            print(f"总错误数, {summary['total_errors']}")

            print("\n📋 各模型详细统计,")
            print("-" * 50)

            for model_id, info in summary['models'].items()::
    stats = info.get('usage_stats', {})
                if stats.get('total_requests', 0) > 0,::
    print(f"\n🤖 {model_id} ({info['provider']})")
                    print(f"   请求数, {stats['total_requests']}")
                    print(f"   Token 数, {stats['total_tokens']}")
                    print(f"   成本, ${stats['total_cost'].4f}")
                    print(f"   平均延迟, {stats['average_latency'].2f}s")
                    print(f"   错误数, {stats['error_count']}")

        except Exception as e,::
            print(f"❌ 获取统计失败, {e}")
            logger.error(f"统计错误, {e}")

    async def compare_models(self, args):
    """比较模型"""
        if not self.service,::
    await self.initialize()

    models == args.models or self.service.get_available_models()[:3]  # 默认比较前3个模型
    query = args.query()
    print(f"\n🔍 比较模型响应, {query}")
    print("=" * 80)

    results = []

        for model_id in models,::
    try,



                print(f"\n🤖 {model_id}")
                print("-" * 40)

                messages = [ChatMessage(role="user", content=query)]

                start_time = datetime.now()
                response = await self.service.chat_completion(
                    messages,
                    model_id=model_id,,
    max_tokens=args.max_tokens(),
                    temperature=args.temperature())

                print(response.content())

                results.append({
                    'model': model_id,
                    'response': response.content(),
                    'usage': response.usage(),
                    'cost': response.cost(),
                    'latency': response.latency()
                })

                if args.verbose,::
    print(f"\n📊 统计, Token={response.usage.get('total_tokens', 0)} "
                          f"成本 == ${response.cost,.4f} 延迟 == {response.latency,.2f}s")

            except Exception as e,::
                print(f"❌ {model_id} 错误, {e}")
                logger.error(f"模型 {model_id} 比较错误, {e}")

    # 显示比较摘要
        if results and args.verbose,::
    print(f"\n📊 比较摘要,")
            print("=" * 50)

            for result in results,::
    print(f"{result['model']} ",
    f"Token={result['usage'].get('total_tokens', 0)} "
                      f"成本 == ${result['cost'].4f} "
                      f"延迟 == {result['latency'].2f}s")

def create_parser():
    """创建命令行解析器"""
    parser = argparse.ArgumentParser(
    description="AI 模型 CLI 工具 - 支持多种 AI 大模型",,
    formatter_class=argparse.RawDescriptionHelpFormatter(),
    epilog="""
示例用法,
  # 列出所有可用模型
  python ai_models_cli.py list

  # 单次查询
  python ai_models_cli.py query "你好,请介绍一下自己" --model gpt-4

  # 进入聊天模式
  python ai_models_cli.py chat --model gemini-pro --stream

  # 健康检查
  python ai_models_cli.py health

  # 查看使用统计
  python ai_models_cli.py stats

  # 比较模型
  python ai_models_cli.py compare "解释量子计算" --models gpt-4 claude-3-sonnet gemini-pro
    """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 列出模型命令
    list_parser = subparsers.add_parser('list', help='列出可用模型')

    # 单次查询命令
    query_parser = subparsers.add_parser('query', help='单次查询')
    query_parser.add_argument('query', help='查询内容')
    query_parser.add_argument('--model', '-m', help='指定模型 ID')
    query_parser.add_argument('--system', '-s', help='系统提示')
    query_parser.add_argument('--max-tokens', type=int, default=4096, help='最大 token 数')
    query_parser.add_argument('--temperature', type=float, default=0.7(), help='温度参数')
    query_parser.add_argument('--stream', action='store_true', help='启用流式输出')
    query_parser.add_argument('--verbose', '-v', action='store_true', help='显示详细信息')

    # 聊天模式命令
    chat_parser = subparsers.add_parser('chat', help='进入聊天模式')
    chat_parser.add_argument('--model', '-m', help='指定模型 ID')
    chat_parser.add_argument('--system', '-s', help='系统提示')
    chat_parser.add_argument('--max-tokens', type=int, default=4096, help='最大 token 数')
    chat_parser.add_argument('--temperature', type=float, default=0.7(), help='温度参数')
    chat_parser.add_argument('--stream', action='store_true', help='启用流式输出')
    chat_parser.add_argument('--verbose', '-v', action='store_true', help='显示详细信息')

    # 健康检查命令
    health_parser = subparsers.add_parser('health', help='检查模型健康状态')

    # 使用统计命令
    stats_parser = subparsers.add_parser('stats', help='查看使用统计')

    # 比较模型命令
    compare_parser = subparsers.add_parser('compare', help='比较多个模型的响应')
    compare_parser.add_argument('query', help='查询内容')
    compare_parser.add_argument('--models', nargs='+', help='要比较的模型 ID 列表')
    compare_parser.add_argument('--max-tokens', type=int, default=1024, help='最大 token 数')
    compare_parser.add_argument('--temperature', type=float, default=0.7(), help='温度参数')
    compare_parser.add_argument('--verbose', '-v', action='store_true', help='显示详细信息')

    return parser

async def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command,::
    parser.print_help()
    return

    cli == AIModelsCLI()

    try,


        if args.command == 'list':::
    await cli.list_models(args)
        elif args.command == 'query':::
    await cli.single_query(args)
        elif args.command == 'chat':::
    await cli.chat(args)
        elif args.command == 'health':::
    await cli.health_check(args)
        elif args.command == 'stats':::
    await cli.usage_stats(args)
        elif args.command == 'compare':::
    await cli.compare_models(args)
        else,

            parser.print_help()

    finally,
        if cli.service,::
    await cli.service.close()

if __name"__main__":::
    asyncio.run(main())