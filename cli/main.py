#!/usr/bin/env python3
"""
Unified AI Project CLI 主入口点
统一命令行界面，整合所有项目管理功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import click
    from cli.commands import dev, test, git, deps, system, editor, rovo, security
    from cli.utils import logger
except ImportError as e:
    print(f"缺少必要的依赖包: {e}")
    print("请运行: pip install click")
    sys.exit(1)


@click.group()
@click.version_option(version='1.0.0')
@click.option('--verbose', '-v', is_flag=True, help='启用详细输出')
def cli(verbose):
    """Unified AI Project 命令行工具
    
    用于管理Unified AI项目的开发、测试、构建和部署等操作的统一工具。
    
    使用示例:
      unified-ai-cli dev start     # 启动开发环境
      unified-ai-cli test run      # 运行测试
      unified-ai-cli git status    # 查看Git状态
    """
    # 设置日志级别
    if verbose:
        logger.set_level('DEBUG')


# 注册各功能模块命令
cli.add_command(dev)
cli.add_command(test)
cli.add_command(git)
cli.add_command(deps.deps)
cli.add_command(system.system)
cli.add_command(editor)
cli.add_command(rovo)
cli.add_command(security)


@cli.command()
def help():
    """显示帮助信息"""
    ctx = click.get_current_context()
    click.echo(cli.get_help(ctx))


if __name__ == '__main__':
    try:
        cli()
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
        if logger.get_level() == 'DEBUG':
            import traceback
            traceback.print_exc()
        sys.exit(1)