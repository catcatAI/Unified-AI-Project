#!/usr/bin/env python3
"""
智能自动修复系统 (Smart Auto-Fix System)
新一代智能自动修复工具，支持多种类型问题的检测、分析和修复
"""

import os
import sys
import re
import json
import argparse
import traceback
import subprocess
import ast
from pathlib import Path
from typing import List, Tuple, Dict, Set, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.error_analyzer import ErrorAnalyzer, ErrorType, ErrorInfo

# 配置日志
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FixType(Enum):
    """修复类型枚举"""
    IMPORT_PATH = "import_path"
    SYNTAX_ERROR = "syntax_error"
    ASYNC_WARNING = "async_warning"
    TIMEOUT_ERROR = "timeout_error"
    ASSERTION_ERROR = "assertion_error"
    CONFIG_ERROR = "config_error"
    UNKNOWN = "unknown"

@dataclass
class FixStrategy:
    """修复策略"""
    fix_type: FixType
    description: str
    pattern: str
    replacement: str
    priority: int  # 优先级，数值越小优先级越高

@dataclass
class SmartFixReport:
    """智能修复报告"""
    timestamp: str
    files_scanned: int
    issues_detected: int
    issues_fixed: int
    fixes_applied: int
    errors: List[str]
    warnings: List[str]
    fixed_files: List[str]
    skipped_files: List[str]
    fix_details: List[Dict[str, Any]]

class SmartAutoFixer:
    """智能自动修复器"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or PROJECT_ROOT
        self.backup_dir = self.project_root / "backup" / f"smart_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.fix_report = SmartFixReport(
            timestamp=datetime.now().isoformat(),
            files_scanned=0,
            issues_detected=0,
            issues_fixed=0,
            fixes_applied=0,
            errors=[],
            warnings=[],
            fixed_files=[],
            skipped_files=[],
            fix_details=[]
        )
        
        # 创建备份目录
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 定义修复策略
        self.fix_strategies = self._initialize_fix_strategies()
        
        logger.info("智能自动修复系统初始化完成")
    
    def _initialize_fix_strategies(self) -> List[FixStrategy]:
        """初始化修复策略"""
        strategies = [
            # 导入路径修复策略
            FixStrategy(
                fix_type=FixType.IMPORT_PATH,
                description="修复core_ai相对导入问题",
                pattern=r"from\s+\.\.core_ai\.",
                replacement="from apps.backend.src.core_ai.",
                priority=1
            ),
            FixStrategy(
                fix_type=FixType.IMPORT_PATH,
                description="修复core相对导入问题",
                pattern=r"from\s+\.\.core\.",
                replacement="from apps.backend.src.core.",
                priority=1
            ),
            FixStrategy(
                fix_type=FixType.IMPORT_PATH,
                description="修复services相对导入问题",
                pattern=r"from\s+\.\.services\.",
                replacement="from apps.backend.src.services.",
                priority=1
            ),
            FixStrategy(
                fix_type=FixType.IMPORT_PATH,
                description="修复hsp相对导入问题",
                pattern=r"from\s+\.\.hsp\.",
                replacement="from apps.backend.src.hsp.",
                priority=1
            ),
            
            # 协程未await修复策略
            FixStrategy(
                fix_type=FixType.ASYNC_WARNING,
                description="修复协程未await问题",
                pattern=r"(\w+\([^)]*\))",
                replacement=r"await \1",
                priority=2
            ),
            
            # 配置错误修复策略
            FixStrategy(
                fix_type=FixType.CONFIG_ERROR,
                description="修复配置文件路径问题",
                pattern=r"configs/([^/]+)$",
                replacement=r"apps/backend/configs/\1",
                priority=3
            )
        ]
        return strategies
    
    def backup_file(self, file_path: Path) -> Path:
        """备份文件"""
        try:
            # 创建相对于项目根的路径
            relative_path = file_path.relative_to(self.project_root)
            backup_file_path = self.backup_dir / relative_path
            backup_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            import shutil
            shutil.copy2(file_path, backup_file_path)
            return backup_file_path
        except Exception as e:
            error_msg = f"备份文件 {file_path} 失败: {e}"
            self.fix_report.errors.append(error_msg)
            logger.error(error_msg)
            return None
    
    def find_python_files(self) -> List[Path]:
        """查找所有Python文件"""
        python_files = []
        
        # 遍历所有Python文件
        for py_file in self.project_root.rglob("*.py"):
            # 跳过不需要处理的目录
            skip_dirs = ["backup", "node_modules", "__pycache__", "venv", ".git", ".pytest_cache"]
            if any(part in str(py_file) for part in skip_dirs):
                continue
                
            python_files.append(py_file)
            
        self.fix_report.files_scanned = len(python_files)
        logger.info(f"找到 {len(python_files)} 个Python文件")
        return python_files
    
    def detect_issues(self) -> List[Tuple[Path, ErrorInfo]]:
        """检测问题"""
        issues = []
        
        # 使用错误分析器检测问题
        error_analyzer = ErrorAnalyzer("test_results.json")
        errors = error_analyzer.analyze_errors()
        
        # 将错误信息转换为问题列表
        for error in errors:
            # 为每个错误创建一个虚拟的文件路径（实际应用中需要更精确的定位）
            dummy_path = Path("unknown_file.py")
            issues.append((dummy_path, error))
            
        self.fix_report.issues_detected = len(issues)
        logger.info(f"检测到 {len(issues)} 个问题")
        return issues
    
    def apply_fix_strategy(self, file_path: Path, strategy: FixStrategy) -> bool:
        """应用修复策略"""
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 备份文件
            self.backup_file(file_path)
            
            # 应用修复
            original_content = content
            if strategy.fix_type == FixType.IMPORT_PATH:
                content = re.sub(strategy.pattern, strategy.replacement, content)
            elif strategy.fix_type == FixType.ASYNC_WARNING:
                # 这里需要更复杂的逻辑来处理协程问题
                content = self._fix_async_warnings(content)
            elif strategy.fix_type == FixType.CONFIG_ERROR:
                content = re.sub(strategy.pattern, strategy.replacement, content)
            
            # 如果内容有变化，写入文件
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # 记录修复详情
                fix_detail = {
                    "file": str(file_path),
                    "fix_type": strategy.fix_type.value,
                    "description": strategy.description,
                    "timestamp": datetime.now().isoformat()
                }
                self.fix_report.fix_details.append(fix_detail)
                self.fix_report.fixes_applied += 1
                logger.info(f"✓ 修复了文件 {file_path}: {strategy.description}")
                return True
            else:
                return False
                
        except Exception as e:
            error_msg = f"修复文件 {file_path} 时出错: {e}"
            self.fix_report.errors.append(error_msg)
            logger.error(error_msg)
            return False
    
    def _fix_async_warnings(self, content: str) -> str:
        """修复协程警告"""
        # 这里需要实现更复杂的协程修复逻辑
        # 暂时只做一个简单的示例
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # 检查是否包含协程调用但没有await
            if re.search(r'\w+\([^)]*\)', line) and 'await' not in line:
                # 简单地在可能的协程调用前添加await
                # 注意：这只是一个示例，实际应用中需要更精确的检测
                line = re.sub(r'(\w+\([^)]*\))', r'await \1', line)
            fixed_lines.append(line)
            
        return '\n'.join(fixed_lines)
    
    def fix_file(self, file_path: Path) -> bool:
        """修复单个文件"""
        try:
            fixes_applied = 0
            
            # 按优先级排序修复策略
            sorted_strategies = sorted(self.fix_strategies, key=lambda s: s.priority)
            
            # 应用每个修复策略
            for strategy in sorted_strategies:
                if self.apply_fix_strategy(file_path, strategy):
                    fixes_applied += 1
            
            if fixes_applied > 0:
                self.fix_report.fixed_files.append(str(file_path))
                self.fix_report.issues_fixed += 1
                return True
            else:
                return False
                
        except Exception as e:
            error_msg = f"修复文件 {file_path} 时出错: {e}"
            self.fix_report.errors.append(error_msg)
            logger.error(error_msg)
            return False
    
    def fix_all_files(self) -> SmartFixReport:
        """修复所有文件"""
        logger.info("开始智能自动修复...")
        
        # 查找所有Python文件
        python_files = self.find_python_files()
        
        # 检测问题
        issues = self.detect_issues()
        
        # 修复每个文件
        for file_path in python_files:
            try:
                self.fix_file(file_path)
            except Exception as e:
                error_msg = f"处理文件 {file_path} 时出错: {e}"
                self.fix_report.errors.append(error_msg)
                logger.error(error_msg)
        
        logger.info("智能自动修复完成")
        return self.fix_report
    
    def validate_fixes(self) -> bool:
        """验证修复效果"""
        logger.info("开始验证修复效果...")
        
        try:
            # 运行测试来验证修复
            result = subprocess.run([
                "python", "-m", "pytest", "--tb=short", "-v"
            ], cwd=self.project_root, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info("✓ 修复验证通过")
                return True
            else:
                logger.warning("✗ 修复验证失败")
                self.fix_report.errors.append("修复验证失败")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("✗ 修复验证超时")
            self.fix_report.errors.append("修复验证超时")
            return False
        except Exception as e:
            logger.error(f"✗ 修复验证时出错: {e}")
            self.fix_report.errors.append(f"修复验证时出错: {e}")
            return False
    
    def generate_report(self, report_file: str = None) -> str:
        """生成修复报告"""
        if report_file is None:
            report_file = self.project_root / f"SMART_FIX_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # 转换为可序列化的格式
        report_data = {
            "timestamp": self.fix_report.timestamp,
            "files_scanned": self.fix_report.files_scanned,
            "issues_detected": self.fix_report.issues_detected,
            "issues_fixed": self.fix_report.issues_fixed,
            "fixes_applied": self.fix_report.fixes_applied,
            "errors": self.fix_report.errors,
            "warnings": self.fix_report.warnings,
            "fixed_files": self.fix_report.fixed_files,
            "skipped_files": self.fix_report.skipped_files,
            "fix_details": self.fix_report.fix_details
        }
        
        # 保存报告
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"修复报告已保存到: {report_file}")
        return str(report_file)

def main():
    parser = argparse.ArgumentParser(description="智能自动修复系统")
    parser.add_argument("--fix", action="store_true", help="执行自动修复")
    parser.add_argument("--validate", action="store_true", help="验证修复效果")
    parser.add_argument("--report", action="store_true", help="生成修复报告")
    parser.add_argument("--all", action="store_true", help="执行所有操作")
    
    args = parser.parse_args()
    
    # 创建智能修复器
    fixer = SmartAutoFixer()
    
    # 执行操作
    if args.fix or args.all:
        report = fixer.fix_all_files()
        print(f"修复完成:")
        print(f"  扫描文件数: {report.files_scanned}")
        print(f"  检测问题数: {report.issues_detected}")
        print(f"  修复问题数: {report.issues_fixed}")
        print(f"  应用修复数: {report.fixes_applied}")
        
        if report.errors:
            print(f"  错误数: {len(report.errors)}")
            for error in report.errors:
                print(f"    - {error}")
    
    if args.validate or args.all:
        if fixer.validate_fixes():
            print("✓ 修复验证通过")
        else:
            print("✗ 修复验证失败")
    
    if args.report or args.all:
        report_file = fixer.generate_report()
        print(f"✓ 修复报告已生成: {report_file}")
    
    print("智能自动修复系统执行完成")

if __name__ == "__main__":
    main()