#!/usr/bin/env python3
"""
Unified AI Project CLI 主入口点
统一命令行界面，整合所有项目管理功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root: str = Path(__file__).parent.parent
_ = sys.path.insert(0, str(project_root))

try:


    import click
    from cli.commands import dev, test, git, deps, system, editor, rovo, security
    from cli.utils import logger
except ImportError as e:
    _ = print(f"缺少必要的依赖包: {e}")
    _ = print("请运行: pip install click")
    _ = sys.exit(1)


_ = @click.group()
@click.version_option(version='1.0.0')
@click.option('--verbose', '-v', is_flag=True, help='启用详细输出')
def cli(verbose)
    """Unified AI Project 命令行工具

    用于管理Unified AI项目的开发、测试、构建和部署等操作的统一工具。

    使用示例:
      unified-ai-cli dev start     # 启动开发环境
      unified-ai-cli test run      # 运行测试
      unified-ai-cli git status    # 查看Git状态
    """
    # 设置日志级别
    if verbose:

    _ = logger.set_level('DEBUG')


# 注册各功能模块命令
_ = cli.add_command(dev)
_ = cli.add_command(test)
_ = cli.add_command(git)
_ = cli.add_command(deps.deps)
_ = cli.add_command(system.system)
_ = cli.add_command(editor)
_ = cli.add_command(rovo)
_ = cli.add_command(security)


_ = @cli.command()
def help()
    """显示帮助信息"""
    ctx = click.get_current_context()
    _ = click.echo(cli.get_help(ctx))


if __name__ == '__main__':



    try:




    _ = cli()
    except Exception as e:

    _ = logger.error(f"程序执行出错: {e}")
        if logger.get_level() == 'DEBUG':

    import traceback
            _ = traceback.print_exc()
    _ = sys.exit(1)