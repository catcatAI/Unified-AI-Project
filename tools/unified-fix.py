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
            # 使用pathlib.Path兼容的方式检查路径关系
            try:
                if rel_path.parts[:len(scope_dir.split('/'))] == tuple(scope_dir.split('/')):
                    # 检查是否在排除列表中
                    for exclude_dir in self.exclude_dirs:
                        if exclude_dir in str(rel_path):
                            return False
                    
                    # 检查文件扩展名
                    if rel_path.suffix in self.exclude_extensions:
                        return False
                    
                    return True
            except (ValueError, IndexError):
                continue
        
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
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            changes_made = False
            
            # 修复常见的语法错误
            
            # 1. 修复字典语法错误 ("key": value)
            import re
            pattern = r'_ = "([^"]+)":\s*([^,\n}]+)(,?)'
            replacement = r'"\1": \2\3'
            content = re.sub(pattern, replacement, content)
            if content != original_content:
                changes_made = True
                logger.debug(f"修复字典语法: {file_path}")
            
            # 2. 修复 raise Exception 语法错误
            content = re.sub(r'_ = raise\s+', 'raise ', content)
            if content != original_content:
                changes_made = True
                logger.debug(f"修复raise语法: {file_path}")
            
            # 3. 修复 @decorator 语法错误
            content = re.sub(r'_ = (@\w+)', r'\1', content)
            if content != original_content:
                changes_made = True
                logger.debug(f"修复装饰器语法: {file_path}")
            
            # 4. 修复 assert 语法错误
            content = re.sub(r'_ = assert\s+', 'assert ', content)
            if content != original_content:
                changes_made = True
                logger.debug(f"修复assert语法: {file_path}")
            
            # 5. 修复 **kwargs 语法错误
            content = re.sub(r'_ = \*\*(\w+)', r'**\1', content)
            if content != original_content:
                changes_made = True
                logger.debug(f"修复kwargs语法: {file_path}")
            
            # 6. 修复智能引号问题
            content = content.replace('"""', '"""')
            content = content.replace('"""', '"""')
            content = content.replace('"', '"')
            content = content.replace('"', '"')
            content = content.replace(''''''', "'")
            if content != original_content:
                changes_made = True
                logger.debug(f"修复智能引号: {file_path}")
            
            # 如果有更改，写回文件
            if changes_made:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"修复语法错误: {file_path}")
            
            # 验证修复后的语法
            try:
                compile(content, str(file_path), 'exec')
                return True
            except SyntaxError as e:
                logger.warning(f"修复后仍有语法错误在 {file_path}: {e}")
                return False
                
        except Exception as e:
            logger.warning(f"检查 {file_path} 时出错: {e}")
            return False
    
    def fix_import_errors(self, file_path: Path) -> bool:
        """修复导入错误"""
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            changes_made = False
            
            # 修复常见的导入错误
            
            # 1. 修复不完整的导入语句
            pattern = r'from\s+[\w\.]+\s+import\s*\n'
            replacement = ''
            content = re.sub(pattern, replacement, content)
            if content != original_content:
                changes_made = True
                logger.debug(f"修复不完整导入: {file_path}")
            
            # 2. 修复重复的导入语句
            lines = content.split('\n')
            imports = {}
            new_lines = []
            
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('import ') or stripped.startswith('from '):
                    if stripped not in imports:
                        imports[stripped] = True
                        new_lines.append(line)
                    else:
                        changes_made = True
                        logger.debug(f"移除重复导入: {stripped}")
                else:
                    new_lines.append(line)
            
            if changes_made:
                content = '\n'.join(new_lines)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"修复导入错误: {file_path}")
            
            return True
            
        except Exception as e:
            logger.warning(f"修复导入错误时出错 {file_path}: {e}")
            return False
    
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