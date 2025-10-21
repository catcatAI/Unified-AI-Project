"""
命令行接口
提供命令行方式的自动修复功能
"""

import argparse
import sys
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import asdict

from ..core.unified_fix_engine import UnifiedFixEngine, FixContext
from ..core.fix_types import FixType, FixScope, FixPriority
from ..core.fix_result import FixReport


class CLIFixInterface:
    """命令行修复接口"""
    
    def __init__(self):
        self.parser = self._create_argument_parser()
        self.engine: Optional[UnifiedFixEngine] = None
    
    def _create_argument_parser(self) -> argparse.ArgumentParser:
        """创建参数解析器"""
        parser = argparse.ArgumentParser(
            description="统一自动修复系统 - 命令行接口",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
使用示例:
  # 分析整个项目
  unified-fix analyze
  
  # 修复语法错误
  unified-fix fix --types syntax_fix
  
  # 修复特定目录
  unified-fix fix --target src/ai --scope directory
  
  # 干运行模式(不实际修复)
  unified-fix fix --dry-run
  
  # 生成详细报告
  unified-fix analyze --output report.json
  # 修复多种类型问题
  unified-fix fix --types syntax_fix import_fix dependency_fix
  
  # 指定优先级
  unified-fix fix --types security_fix --priority critical
            """
        )
        
         # 全局选项

        parser.add_argument(
            "--project-root", "-p",
            type=str,
            default=".",
            help="项目根目录路径 (默认: 当前目录)"
        )
        
        parser.add_argument(
            "--config", "-c",
            type=str,
            help="配置文件路径"
        )
        
        parser.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="详细输出"
        )
        
        parser.add_argument(
            "--quiet", "-q",
            action="store_true",
            help="安静模式,只显示错误"
        )
        
        # 子命令
        subparsers = parser.add_subparsers(dest="command", help="可用命令")
        
        # 分析命令
        analyze_parser = subparsers.add_parser(
            "analyze",
            help="分析项目问题"
        )
        
        analyze_parser.add_argument(
            "--scope", "-s",
            choices=["project", "backend", "frontend", "desktop", "file", "directory"],
            default="project",
            help="分析范围 (默认: project)"
        )
        
        analyze_parser.add_argument(
            "--target", "-t",
            type=str,
            help="特定目标文件或目录"
        )
        
        analyze_parser.add_argument(
            "--output", "-o",
            type=str,
            help="输出分析结果到文件 (JSON格式)"
        )
        
        analyze_parser.add_argument(
            "--format",
            choices=["json", "text", "summary"],
            default="text",
            help="输出格式 (默认: text)"
        )
        
         # 修复命令
        fix_parser = subparsers.add_parser(
            "fix",
            help="修复项目问题"
        )
        
        fix_parser.add_argument(
            "--types",
            nargs="+",
            choices=[ft.value for ft in FixType],
            help="要修复的问题类型"
        )
        
        fix_parser.add_argument(
            "--scope", "-s",
            choices=["project", "backend", "frontend", "desktop", "file", "directory"],
            default="project",
            help="修复范围 (默认: project)"
        )
        
        fix_parser.add_argument(
            "--target", "-t",
            type=str,
            help="特定目标文件或目录"
        )
        
        fix_parser.add_argument(
            "--priority",
            choices=["critical", "high", "normal", "low"],
            default="normal",
            help="修复优先级 (默认: normal)"
        )
        
        fix_parser.add_argument(
            "--dry-run",
            action="store_true",
            help="干运行模式,不实际执行修复"
        )
        
        fix_parser.add_argument(
            "--no-backup",
            action="store_true",
            help="不创建备份"
        )
        
        fix_parser.add_argument(
            "--ai-assisted",
            action="store_true",
            help="启用AI辅助修复"
        )
        
        fix_parser.add_argument(
            "--output", "-o",
            type=str,
            help="输出修复报告到文件 (JSON格式)"
        )
        
         # 状态命令

        status_parser = subparsers.add_parser(
            "status",
            help="显示系统状态"
        )
        
        status_parser.add_argument(
            "--detailed",
            action="store_true",
            help="显示详细信息"
        )
        
         # 配置命令

        config_parser = subparsers.add_parser(
            "config",
            help="管理配置"
        )
        
        config_parser.add_argument(
            "--list",
            action="store_true",
            help="列出当前配置"

        )
        
        config_parser.add_argument(
            "--set",
            nargs=2,
            metavar=("KEY", "VALUE"),
            action="append",
            help="设置配置项"
        )
        
        config_parser.add_argument(
            "--reset",
            action="store_true",
            help="重置为默认配置"
        )
        
        return parser
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """运行CLI接口"""
        parsed_args = None
        try:
            parsed_args = self.parser.parse_args(args)
            
            # 设置日志级别
            if parsed_args.verbose:
                log_level = "DEBUG"
            elif parsed_args.quiet:
                log_level = "ERROR"
            else:
                log_level = "INFO"
            
            self._setup_logging(log_level)
            
             # 初始化引擎
            project_root = Path(parsed_args.project_root).resolve()
            config_path = Path(parsed_args.config) if parsed_args.config else None
            self.engine = UnifiedFixEngine(project_root, config_path)
            
            # 执行命令
            if parsed_args.command == "analyze":
                return self._handle_analyze_command(parsed_args)
            elif parsed_args.command == "fix":
                return self._handle_fix_command(parsed_args)
            elif parsed_args.command == "status":
                return self._handle_status_command(parsed_args)
            elif parsed_args.command == "config":
                return self._handle_config_command(parsed_args)
            else:
                self.parser.print_help()
                return 1
        
        except KeyboardInterrupt:
            print("\n操作被用户中断")
            return 130
        except Exception as e:
            # 现在parsed_args已经初始化，可以安全使用
            if parsed_args and hasattr(parsed_args, 'verbose') and parsed_args.verbose:
                import traceback
                traceback.print_exc()
            else:
                print(f"错误: {e}")
            
            return 1
    
    def _setup_logging(self, level: str):
        """设置日志"""
        import logging
        
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
    
    def _handle_analyze_command(self, args) -> int:
        """处理分析命令"""
        print("正在分析项目问题...")
        
        # 添加类型检查以避免警告
        if self.engine is None:
            print("错误: 引擎未初始化")
            return 1
            
        # 创建上下文
        context = self._create_context(args)
        
        # 执行分析
        result = self.engine.analyze_project(context)
        
        # 输出结果
        if args.format == "json":
            self._output_json(result, args.output)
        elif args.format == "summary":
            self._output_analysis_summary(result)
        else:
            self._output_analysis_text(result)
        
        return 0
    
    def _handle_fix_command(self, args) -> int:
        """处理修复命令"""
        print("正在执行修复...")
        
        # 添加类型检查以避免警告
        if self.engine is None:
            print("错误: 引擎未初始化")
            return 1

         # 创建上下文
        context = self._create_context(args)
        
        # 解析修复类型
        fix_types = None
        if args.types:
            fix_types = args.types
         # 执行修复
        report = self.engine.fix_issues(context, fix_types)

        
        # 输出结果
        self._output_fix_report(report, args.output)
        
        # 返回适当的退出码
        if report.get_success_rate() == 1.0:
            return 0
        elif report.get_success_rate() > 0.5:
            return 1  # 部分成功
        else:
            return 2  # 大部分失败
    
    def _handle_status_command(self, args) -> int:
        """处理状态命令"""
        print("统一自动修复系统状态")
        print("=" * 40)
        
        # 添加类型检查以避免警告
        if self.engine is None:
            print("错误: 引擎未初始化")
            return 1
            
        # 获取引擎状态
        module_status = self.engine.get_module_status()
        
        print(f"项目根目录: {self.engine.project_root}")
        print(f"配置文件: {self.engine.config_path}")
        print(f"已启用模块: {len([m for m in module_status.values() if m == 'enabled'])}")
        print(f"总修复数: {self.engine.stats['total_fixes']}")
        print(f"成功修复: {self.engine.stats['successful_fixes']}")
        print(f"失败修复: {self.engine.stats['failed_fixes']}")
        
        if args.detailed:
            print("\n模块状态:")
            for module, status in module_status.items():
                print(f"  {module} {status}")
        
        return 0
    
    def _handle_config_command(self, args) -> int:
        """处理配置命令"""
        # 添加类型检查以避免警告
        if self.engine is None:
            print("错误: 引擎未初始化")
            return 1
            
        if args.list:
            print("当前配置:")
            print(json.dumps(self.engine.config, indent=2))
        
        elif args.set:
            for key, value in args.set:
                # 尝试解析值(支持JSON格式)
                try:
                    parsed_value = json.loads(value)
                except json.JSONDecodeError:
                    parsed_value = value
                
                # 设置配置
                keys = key.split('.')
                config = self.engine.config
                for k in keys[:-1]:
                    if k not in config:
                        config[k] = {}
                    config = config[k]
                config[keys[-1]] = parsed_value
            
            self.engine.save_config()
            print("配置已更新")
        
        elif args.reset:
            # 重置为默认配置
            self.engine.config = self.engine._load_config()
            self.engine.save_config()
            print("配置已重置为默认值")
        
        else:
            print("请指定配置操作, --list, --set, 或 --reset")
            return 1

        return 0
    
    def _create_context(self, args) -> FixContext:
        """创建修复上下文"""
        # 添加类型检查以避免警告
        if self.engine is None:
            raise RuntimeError("引擎未初始化")
            
        # 解析目标路径
        target_path = None
        if hasattr(args, 'target') and args.target:
            target_path = Path(args.target)
            if not target_path.is_absolute():
                target_path = self.engine.project_root / target_path
        
        # 解析范围
        scope_map = {
            "project": FixScope.PROJECT,
            "backend": FixScope.BACKEND,
            "frontend": FixScope.FRONTEND,
            "desktop": FixScope.DESKTOP,
            "file": FixScope.SPECIFIC_FILE,
            "directory": FixScope.SPECIFIC_DIRECTORY
        }
        
        scope = scope_map.get(args.scope, FixScope.PROJECT)
        
        # 解析优先级
        priority_map = {
            "critical": FixPriority.CRITICAL,
            "high": FixPriority.HIGH,
            "normal": FixPriority.NORMAL,
            "low": FixPriority.LOW
        }
        
        priority = priority_map.get(args.priority, FixPriority.NORMAL)
        
        # 创建上下文
        context = FixContext(
            project_root=self.engine.project_root,
            target_path=target_path,
            scope=scope,
            priority=priority,
            backup_enabled=not getattr(args, 'no_backup', False),
            dry_run=getattr(args, 'dry_run', False),
            ai_assisted=getattr(args, 'ai_assisted', False)
        )
        
        return context
    
    def _output_analysis_text(self, result: Dict[str, Any]):
        """输出分析结果(文本格式)"""
        print("\n项目分析结果,")
        print("=" * 50)
        
        issues = result.get("issues", {})
        statistics = result.get("statistics", {})
        recommendations = result.get("recommendations", [])
        
        if not issues:
            print("✅ 未发现问题！")
            return
        
        print(f"发现 {sum(statistics.values())} 个问题,")
        
        for fix_type, issue_list in issues.items():
            if issue_list:
                count = len(issue_list)
                print(f"\n🔍 {fix_type} {count} 个问题")
                
                # 显示前5个问题的详细信息
                for i, issue in enumerate(issue_list[:5]):
                    print(f"  {i+1}. {str(issue)}")
                
                if count > 5:
                    print(f"  ... 还有 {count - 5} 个问题")
        
        if recommendations:
            print("\n💡 建议,")
            for rec in recommendations[:3]:
                print(f"  - {rec}")
    
    def _output_analysis_summary(self, result: Dict[str, Any]):
        """输出分析结果(摘要格式)"""
        issues = result.get("issues", {})
        statistics = result.get("statistics", {})

        
        total_issues = sum(statistics.values())
        
        print(f"\n分析摘要,")
        print(f"总问题数: {total_issues}")
        
        for fix_type, count in statistics.items():
            if count > 0:
                print(f"  {fix_type} {count}")
    
    def _output_fix_report(self, report: FixReport, output_file: Optional[str] = None):
        """输出修复报告"""
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                # 修复这里：使用to_dict方法而不是asdict
                self._output_json(report.to_dict(), output_file)
        else:
            print("\n修复报告:")
            print("=" * 50)
            print(report.get_summary())
            
            successful_fixes = report.get_successful_fixes()
            failed_fixes = report.get_failed_fixes()
            
            if successful_fixes:
                print(f"\n成功修复 {len(successful_fixes)} 个模块:")
                for fix in successful_fixes:
                    print(f"  - {fix.fix_type.value}: {fix.summary()}")
            
            if failed_fixes:
                print(f"\n失败修复 {len(failed_fixes)} 个模块:")
                for fix in failed_fixes:
                    print(f"  - {fix.fix_type.value}: {fix.summary()}")
            
            if report.errors:
                print(f"\n错误信息:")
                for error in report.errors:
                    print(f"  - {error}")
            
            if report.warnings:
                print(f"\n警告信息:")
                for warning in report.warnings:
                    print(f"  - {warning}")

    def _output_json(self, data, output_file: Optional[str] = None):
        """输出JSON格式数据"""
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        else:
            print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


def main():
    """主函数"""
    cli = CLIFixInterface()
    return cli.run()


if __name__ == "__main__":
    cli = CLIFixInterface()
    sys.exit(cli.run())