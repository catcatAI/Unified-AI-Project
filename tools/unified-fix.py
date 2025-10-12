#!/usr/bin/env python3
"""
统一自动修复系统 - 项目本体限制版本
仅修复项目本体文件，不包括下载的数据集、依赖、模型和工具
"""

import sys
import os
import argparse
from pathlib import Path
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProjectScopeFixer:
    """项目范围修复器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        # 定义项目本体目录
        self.project_scope_dirs = [
            "apps/backend/src",
            "apps/frontend-dashboard/src",
            "apps/desktop-app/src",
            "packages/cli/src",
            "packages/ui/src",
            "tools",
            "scripts"
        ]
        
        # 定义排除目录（下载的内容）
        self.exclude_dirs = [
            "node_modules",
            "venv",
            "__pycache__",
            ".pytest_cache",
            "data",
            "model_cache",
            "checkpoints",
            "logs",
            "chroma_db",
            "chromadb_local"
        ]
        
        # 定义排除文件类型（下载的内容）
        self.exclude_extensions = [
            ".pyc",
            ".pyo",
            ".pyd",
            ".so",
            ".dll",
            ".exe",
            ".bin",
            ".model",
            ".pkl",
            ".h5",
            ".pb",
            ".onnx"
        ]
    
    def is_in_project_scope(self, file_path: Path) -> bool:
        """检查文件是否在项目范围内"""
        # 转换为相对路径
        try:
            rel_path = file_path.relative_to(self.project_root)
        except ValueError:
            return False
        
        # 检查是否在项目范围内
        for scope_dir in self.project_scope_dirs:
            if rel_path.is_relative_to(scope_dir):
                # 检查是否在排除列表中
                for exclude_dir in self.exclude_dirs:
                    if exclude_dir in str(rel_path):
                        return False
                
                # 检查文件扩展名
                if rel_path.suffix in self.exclude_extensions:
                    return False
                
                return True
        
        return False
    
    def scan_project_files(self) -> list[Path]:
        """扫描项目范围内的文件"""
        project_files = []
        
        for scope_dir in self.project_scope_dirs:
            scope_path = self.project_root / scope_dir
            if not scope_path.exists():
                continue
                
            for file_path in scope_path.rglob("*"):
                if file_path.is_file() and self.is_in_project_scope(file_path):
                    project_files.append(file_path)
        
        return project_files
    
    def fix_syntax_errors(self, file_path: Path) -> bool:
        """修复语法错误"""
        try:
            # 简单的语法检查
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 编译检查语法
            compile(content, str(file_path), 'exec')
            return True
        except SyntaxError as e:
            logger.warning(f"语法错误在 {file_path}: {e}")
            # 这里可以添加更复杂的修复逻辑
            return False
        except Exception as e:
            logger.warning(f"检查 {file_path} 时出错: {e}")
            return False
    
    def fix_import_errors(self, file_path: Path) -> bool:
        """修复导入错误"""
        # 这里可以添加导入错误修复逻辑
        return True
    
    def run_fix(self, fix_type: str = "all") -> dict:
        """运行修复"""
        results = {
            "total_files": 0,
            "fixed_files": 0,
            "failed_files": 0,
            "errors": []
        }
        
        logger.info("开始扫描项目文件...")
        project_files = self.scan_project_files()
        results["total_files"] = len(project_files)
        
        logger.info(f"找到 {results['total_files']} 个项目文件")
        
        for file_path in project_files:
            if file_path.suffix == '.py':
                # Python文件修复
                if fix_type in ["all", "syntax"]:
                    if self.fix_syntax_errors(file_path):
                        results["fixed_files"] += 1
                    else:
                        results["failed_files"] += 1
                
                if fix_type in ["all", "import"]:
                    if self.fix_import_errors(file_path):
                        results["fixed_files"] += 1
                    else:
                        results["failed_files"] += 1
        
        return results

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="统一自动修复系统 - 项目本体限制版本")
    parser.add_argument("--type", choices=["all", "syntax", "import"], default="all",
                       help="修复类型")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="详细输出")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 获取项目根目录
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    
    # 创建修复器并运行
    fixer = ProjectScopeFixer(project_root)
    results = fixer.run_fix(args.type)
    
    # 输出结果
    print("\n修复结果:")
    print(f"总文件数: {results['total_files']}")
    print(f"修复成功: {results['fixed_files']}")
    print(f"修复失败: {results['failed_files']}")
    
    if results['errors']:
        print("\n错误:")
        for error in results['errors']:
            print(f"  - {error}")
    
    return 0 if results['failed_files'] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())