#!/usr/bin/env python3
"""
自动修复Python导入路径问题的工具
能够自动扫描项目中的导入路径问题，自动修正错误的导入路径，并自动继续测试或执行
"""

import os
import sys
import ast
import subprocess
from pathlib import Path
import argparse

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class ImportFixer:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.src_dir = project_root / "apps" / "backend" / "src"
        self.fixed_files: Set[str] = set()
        self.failed_files: Set[str] = set()
        self.module_cache: Dict[str, List[Path]] = {}
        
    def scan_project_for_imports(self) -> List[Tuple[Path, str, int]]:
        """扫描项目中所有Python文件的导入语句"""
        import_issues = []
        
        # 遍历所有Python文件
        for py_file in self.project_root.rglob("*.py"):
            # 跳过备份目录和node_modules
            if any(part in str(py_file) for part in ["backup", "node_modules", "__pycache__"]):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 解析AST以查找导入语句
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module and (node.module.startswith('core_ai') or node.module.startswith('services') or node.module.startswith('tools') or node.module.startswith('hsp') or node.module.startswith('shared') or node.module.startswith('agents')):
                            # 检查是否需要修复
                            if not self._is_valid_import(node.module):
                                import_issues.append((py_file, node.module, node.lineno))
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name.startswith('core_ai') or alias.name.startswith('services') or alias.name.startswith('tools') or alias.name.startswith('hsp') or alias.name.startswith('shared') or alias.name.startswith('agents'):
                                if not self._is_valid_import(alias.name):
                                    import_issues.append((py_file, alias.name, node.lineno))
            except Exception as e:
                print(f"警告: 无法解析文件 {py_file}: {e}")
                
        return import_issues
    
    def _is_valid_import(self, module_name: str) -> bool:
        """检查导入是否有效"""
        try:
            # 尝试直接导入
            __import__(module_name)
            return True
        except ImportError:
            # 如果直接导入失败，检查是否可以通过完整路径导入
            # 检查新的目录结构
            if module_name.startswith('core_ai'):
                # 新的AI模块路径
                new_module_name = module_name.replace('core_ai', 'apps.backend.src.ai')
            elif module_name.startswith('services'):
                # 新的服务模块路径
                new_module_name = module_name.replace('services', 'apps.backend.src.core.services')
            elif module_name.startswith('tools'):
                # 新的工具模块路径
                new_module_name = module_name.replace('tools', 'apps.backend.src.core.tools')
            elif module_name.startswith('hsp'):
                # 新的HSP模块路径
                new_module_name = module_name.replace('hsp', 'apps.backend.src.core.hsp')
            elif module_name.startswith('shared'):
                # 新的共享模块路径
                new_module_name = module_name.replace('shared', 'apps.backend.src.core.shared')
            elif module_name.startswith('agents'):
                # 新的代理模块路径
                new_module_name = module_name.replace('agents', 'apps.backend.src.ai.agents')
            else:
                # 其他模块保持原样
                new_module_name = f"apps.backend.src.{module_name}"
            
            try:
                __import__(new_module_name)
                return False  # 需要修复
            except ImportError:
                return False  # 确实不存在
    
    def _find_module_paths(self, module_name: str) -> List[Path]:
        """查找模块的实际路径"""
        if module_name in self.module_cache:
            return self.module_cache[module_name]
            
        module_paths = []
        # 将模块名转换为实际路径
        relative_path = module_name.replace('.', os.sep)
        
        # 在src目录中搜索
        for src_file in self.src_dir.rglob("*.py"):
            # 检查文件路径是否匹配模块名
            if relative_path in str(src_file):
                # 检查是否是模块的__init__.py或模块文件本身
                module_path = str(src_file.relative_to(self.src_dir))
                module_path = module_path.replace(os.sep, '.').replace('.py', '')
                if module_path.endswith('__init__'):
                    module_path = module_path[:-9]  # 移除.__init__
                    
                if module_path == module_name or module_path.startswith(module_name):
                    module_paths.append(src_file)
                    
        self.module_cache[module_name] = module_paths
        return module_paths
    
    def fix_import_in_file(self, file_path: Path, module_name: str) -> bool:
        """修复文件中的导入语句"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            fixed = False
            new_lines = []
            
            for line in lines:
                # 检查是否包含需要修复的导入
                if f"from {module_name}" in line or f"import {module_name}" in line:
                    # 根据模块名确定新的导入路径
                    if module_name.startswith('core_ai'):
                        # 新的AI模块路径
                        new_module_name = module_name.replace('core_ai', 'apps.backend.src.ai')
                    elif module_name.startswith('services'):
                        # 新的服务模块路径
                        new_module_name = module_name.replace('services', 'apps.backend.src.core.services')
                    elif module_name.startswith('tools'):
                        # 新的工具模块路径
                        new_module_name = module_name.replace('tools', 'apps.backend.src.core.tools')
                    elif module_name.startswith('hsp'):
                        # 新的HSP模块路径
                        new_module_name = module_name.replace('hsp', 'apps.backend.src.core.hsp')
                    elif module_name.startswith('shared'):
                        # 新的共享模块路径
                        new_module_name = module_name.replace('shared', 'apps.backend.src.core.shared')
                    elif module_name.startswith('agents'):
                        # 新的代理模块路径
                        new_module_name = module_name.replace('agents', 'apps.backend.src.ai.agents')
                    else:
                        # 其他模块保持原样
                        new_module_name = f"apps.backend.src.{module_name}"
                    
                    # 构造新的导入语句
                    fixed_line = line.replace(
                        f"from {module_name}", 
                        f"from {new_module_name}"
                    )
                    fixed_line = fixed_line.replace(
                        f"import {module_name}", 
                        f"import {new_module_name}"
                    )
                    
                    if fixed_line != line:
                        new_lines.append(fixed_line)
                        fixed = True
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
                    
            if fixed:
                # 写入修复后的内容
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                    
                print(f"✓ 修复了文件 {file_path} 中的导入: {module_name} -> {new_module_name}")
                self.fixed_files.add(str(file_path))
                return True
            else:
                return False
                
        except Exception as e:
            print(f"✗ 修复文件 {file_path} 时出错: {e}")
            self.failed_files.add(str(file_path))
            return False
    
    def fix_all_imports(self) -> Dict[str, int]:
        """修复所有导入问题"""
        print("开始扫描项目中的导入问题...")
        import_issues = self.scan_project_for_imports()
        
        if not import_issues:
            print("未发现导入问题。")
            return {"fixed": 0, "failed": 0, "skipped": 0}
            
        print(f"发现 {len(import_issues)} 个导入问题。")
        
        fixed_count = 0
        failed_count = 0
        skipped_count = 0
        
        for file_path, module_name, line_no in import_issues:
            print(f"处理文件: {file_path} 中的模块: {module_name}")
            
            # 查找模块路径
            module_paths = self._find_module_paths(module_name)
            
            if len(module_paths) == 0:
                print(f"  跳过: 未找到模块 {module_name}")
                skipped_count += 1
                continue
            elif len(module_paths) > 1:
                print(f"  跳过: 找到多个同名模块 {module_name}")
                skipped_count += 1
                continue
            else:
                # 修复导入
                if self.fix_import_in_file(file_path, module_name):
                    fixed_count += 1
                else:
                    failed_count += 1
                    
        return {
            "fixed": fixed_count,
            "failed": failed_count,
            "skipped": skipped_count
        }
    
    def run_tests(self) -> bool:
        """运行测试"""
        print("运行测试...")
        try:
            # 激活虚拟环境并运行测试
            venv_python = self.project_root / "venv" / "Scripts" / "python.exe"
            if not venv_python.exists():
                venv_python = "python"
                
            result = subprocess.run(
                [str(venv_python), "-m", "pytest", "--tb=short", "-v"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                print("✓ 测试通过")
                return True
            else:
                print("✗ 测试失败")
                print(result.stdout)
                print(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("✗ 测试超时")
            return False
        except Exception as e:
            print(f"✗ 运行测试时出错: {e}")
            return False
    
    def run_dev_server(self) -> bool:
        """运行开发服务器"""
        print("启动开发服务器...")
        try:
            # 激活虚拟环境并运行开发服务器
            venv_python = self.project_root / "venv" / "Scripts" / "python.exe"
            if not venv_python.exists():
                venv_python = "python"
                
            # 启动ChromaDB服务器
            chroma_process = subprocess.Popen(
                _ = [str(venv_python), "start_chroma_server.py"],
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # 等待几秒钟让ChromaDB启动
            import time
            time.sleep(5)
            
            # 启动FastAPI服务器
            fastapi_process = subprocess.Popen(
                _ = [str(venv_python), "-m", "uvicorn", "apps.backend.src.core.services.main_api_server:app", 
                 "--reload", "--host", "0.0.0.0", "--port", "8000"],
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            print("✓ 开发服务器已启动")
            print("  ChromaDB: http://localhost:8001")
            print("  API服务器: http://localhost:8000")
            
            # 等待用户按键停止
            input("按回车键停止服务器...")
            
            # 停止进程
            chroma_process.terminate()
            fastapi_process.terminate()
            
            return True
            
        except Exception as e:
            print(f"✗ 启动开发服务器时出错: {e}")
            return False

def main() -> None:
    parser = argparse.ArgumentParser(description="自动修复Python导入路径问题")
    parser.add_argument("--fix", action="store_true", help="修复导入路径问题")
    parser.add_argument("--test", action="store_true", help="修复后运行测试")
    parser.add_argument("--dev", action="store_true", help="修复后运行开发服务器")
    parser.add_argument("--all", action="store_true", help="执行所有操作: 修复 -> 测试 -> 开发服务器")
    
    args = parser.parse_args()
    
    # 确定项目根目录
    project_root: str = Path(__file__).parent.parent.parent
    print(f"项目根目录: {project_root}")
    
    # 创建导入修复器
    fixer = ImportFixer(project_root)
    
    # 执行操作
    if args.fix or args.all:
        result = fixer.fix_all_imports()
        print(f"\n修复完成:")
        print(f"  修复: {result['fixed']} 个文件")
        print(f"  失败: {result['failed']} 个文件")
        print(f"  跳过: {result['skipped']} 个文件")
        
        if result['failed'] > 0:
            print("警告: 部分文件修复失败，请手动检查。")
    
    if args.test or args.all:
        if not fixer.run_tests():
            print("测试失败，退出。")
            return 1
    
    if args.dev or args.all:
        if not fixer.run_dev_server():
            print("启动开发服务器失败。")
            return 1
    
    print("所有操作完成。")
    return 0

if __name__ == "__main__":
    sys.exit(main())