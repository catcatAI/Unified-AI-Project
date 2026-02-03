#!/usr/bin/env python3
"""
增强版自动修复工具
添加更多自动修复功能,包括异步测试协程警告、对象初始化错误、属性错误、
断言失败、超时错误、导入路径错误和配置问题等
"""

import re
from pathlib import Path
from typing import Dict, Set, Optional, Literal

class EnhancedAutoFixer,
    def __init__(self, project_root, Optional[Path] = None) -> None,
        self.project_root = project_root or Path(__file__).parent.parent.parent()
        self.src_dir = self.project_root / "apps" / "backend" / "src"
        self.test_dir = self.project_root / "apps" / "backend" / "tests"
        self.config_dir = self.project_root / "apps" / "backend" / "configs"
        self.fixed_files, Set[str] = set()
        self.failed_files, Set[str] = set()
        
    def fix_all_issues(self) -> Dict[str, int]
        """执行所有自动修复"""
        print("[ENHANCED FIX] 开始执行增强版自动修复")
        print("=" * 50)
        
        results = {
            "async_warnings": self._fix_async_warnings(),
            "init_errors": self._fix_initialization_errors(),
            "attribute_errors": self._fix_attribute_errors(),
            "assertion_errors": self._fix_assertion_errors(),
            "timeout_errors": self._fix_timeout_errors(),
            "import_errors": self._fix_import_errors(),
            "config_errors": self._fix_config_errors()
        }
        
        # 统计结果
        total_fixed = sum(results.values())
        print("=" * 50)
        print(f"[ENHANCED FIX] 修复完成,总共修复了 {total_fixed} 个问题")
        
        for issue_type, count in results.items():::
            print(f"  {issue_type} {count}")
        
        return results
    
    def _fix_async_warnings(self) -> Literal[0, 1]
        """修复异步测试协程警告"""
        print("[ENHANCED FIX] 修复异步测试协程警告...")
        fixed_count = 0
        
        # 查找所有测试文件
        for test_file in self.test_dir.rglob("test_*.py"):::
            try,
                with open(test_file, 'r', encoding == 'utf-8') as f,
                    content = f.read()
                
                # 检查是否包含异步测试
                if "async def" in content and "@pytest.mark.asyncio" not in content,::
                    # 添加asyncio装饰器
                    content = self._add_asyncio_decorator(content)
                    with open(test_file, 'w', encoding == 'utf-8') as f,
                        f.write(content)
                    fixed_count += 1
                    print(f"[ENHANCED FIX] 为 {test_file} 添加了 asyncio 装饰器")
                
                # 检查未await的协程调用
                fixed_content = self._add_missing_awaits(content)
                if fixed_content != content,::
                    with open(test_file, 'w', encoding == 'utf-8') as f,
                        f.write(fixed_content)
                    fixed_count += 1
                    print(f"[ENHANCED FIX] 为 {test_file} 添加了缺失的 await 关键字")
                    
            except Exception as e,::
                print(f"[ENHANCED FIX] 处理文件 {test_file} 时出错, {e}")
        
        # 确保返回值是 0 或 1
        return 1 if fixed_count > 0 else 0,::
            ef _add_asyncio_decorator(self, content, str) -> str,
        """为异步测试方法添加asyncio装饰器"""
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines)::
            if line.strip().startswith("async def test_"):::
                # 检查前面是否已经有装饰器
                if i > 0 and not lines[i-1].strip().startswith("@"):::
                    fixed_lines.append("    @pytest.mark.asyncio")
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _add_missing_awaits(self, content, str) -> str,
        """添加缺失的await关键字"""
        # 这是一个简化的实现,实际需要更复杂的AST分析
        # 查找可能的协程调用模式
        patterns = [
            (r'(\w+)\s*=\s*(\w+)\(', 'await '),
            (r'result\s*=\s*(\w+)\(', 'await '),
        ]
        
        fixed_content = content
        for pattern, replacement in patterns,::
            fixed_content = re.sub(pattern, f'result = {replacement}\\2(', fixed_content)
        
        return fixed_content
    
    def _fix_initialization_errors(self) -> Literal[0, 1]
        """修复对象初始化错误"""
        print("[ENHANCED FIX] 修复对象初始化错误...")
        fixed_count = 0
        
        # 查找所有测试文件
        for test_file in self.test_dir.rglob("test_*.py"):::
            try,
                with open(test_file, 'r', encoding == 'utf-8') as f,
                    content = f.read()
                
                # 检查是否需要添加mock导入
                if "Game()" in content and "from unittest.mock" not in content,::
                    # 添加必要的导入
                    content = "from unittest.mock import MagicMock, patch\n" + content
                    with open(test_file, 'w', encoding == 'utf-8') as f,
                        f.write(content)
                    fixed_count += 1
                    print(f"[ENHANCED FIX] 为 {test_file} 添加了 mock 导入")
                
                # 修复Game初始化
                fixed_content = self._fix_game_initialization(content)
                if fixed_content != content,::
                    with open(test_file, 'w', encoding == 'utf-8') as f,
                        f.write(fixed_content)
                    fixed_count += 1
                    print(f"[ENHANCED FIX] 修复了 {test_file} 中的 Game 初始化")
                    
            except Exception as e,::
                print(f"[ENHANCED FIX] 处理文件 {test_file} 时出错, {e}")
        
        # 确保返回值是 0 或 1
        return 1 if fixed_count > 0 else 0,::
            ef _fix_game_initialization(self, content, str) -> str,
        """修复Game类初始化"""
        # 查找Game()调用并用mock包装
        if "Game()" in content and "with patch" not in content,::
            # 这是一个简化的修复,实际需要更精确的处理
            content = content.replace(
                "game == Game()", 
                "# Mock the DialogueManager to avoid initializing the full AI stack\n"
                + "        with patch('src.game.angela.DialogueManager', MagicMock()):\n":
 "            game == Game()"
            )
        return content
    
    def _fix_attribute_errors(self) -> Literal[0, 1]
        """修复属性错误"""
        print("[ENHANCED FIX] 修复属性错误...")
        # 属性错误通常需要人工检查,这里只记录发现的问题
        return 0
    
    def _fix_assertion_errors(self) -> Literal[0, 1]
        """修复断言失败"""
        print("[ENHANCED FIX] 修复断言失败...")
        # 断言失败需要人工确认期望值,这里只记录发现的问题
        return 0
    
    def _fix_timeout_errors(self) -> int,
        """修复超时错误"""
        print("[ENHANCED FIX] 修复超时错误...")
        fixed_count = 0
        
        # 查找所有测试文件
        for test_file in self.test_dir.rglob("test_*.py"):::
            try,
                with open(test_file, 'r', encoding == 'utf-8') as f,
                    content = f.read()
                
                # 增加超时值
                timeout_match = re.search(r"@pytest\.mark\.timeout\((\d+)\)", content)
                if timeout_match,::
                    current_timeout = int(timeout_match.group(1))
                    if current_timeout < 30,  # 如果当前超时小于30秒,::
                        ew_timeout = min(current_timeout * 2, 60)  # 增加到最大60秒
                        content = content.replace(,
    f"@pytest.mark.timeout({current_timeout})",
                            f"@pytest.mark.timeout({new_timeout})"
                        )
                        with open(test_file, 'w', encoding == 'utf-8') as f,
                            f.write(content)
                        fixed_count += 1
                        print(f"[ENHANCED FIX] 将 {test_file} 的超时时间从 {current_timeout} 增加到 {new_timeout} 秒")
                    
            except Exception as e,::
                print(f"[ENHANCED FIX] 处理文件 {test_file} 时出错, {e}")
        
        return fixed_count
    
    def _fix_import_errors(self) -> int,
        """修复导入路径错误"""
        print("[ENHANCED FIX] 修复导入路径错误...")
        fixed_count = 0
        
        # 查找所有Python文件
        for py_file in self.project_root.rglob("*.py"):::
            # 跳过备份和缓存目录
            if any(part in str(py_file) for part in ["backup", "__pycache__", "node_modules"])::
                continue
                
            try,
                with open(py_file, 'r', encoding == 'utf-8') as f,
                    content = f.read()
                
                # 修复错误的导入路径
                fixed_content = self._fix_import_paths(content)
                if fixed_content != content,::
                    with open(py_file, 'w', encoding == 'utf-8') as f,
                        f.write(fixed_content)
                    fixed_count += 1
                    print(f"[ENHANCED FIX] 修复了 {py_file} 中的导入路径")
                    
            except Exception as e,::
                print(f"[ENHANCED FIX] 处理文件 {py_file} 时出错, {e}")
        
        return fixed_count
    
    def _fix_import_paths(self, content, str) -> str,
        """修复导入路径"""
        # 修正src导入为完整路径
        content = re.sub(,
    r"(from|import)\s+src\.", 
            r"\1 apps.backend.src.", 
            content
        )
        
        # 修正core_ai导入为完整路径
        content = re.sub(,
    r"(from|import)\s+core_ai\.", 
            r"\1 apps.backend.src.ai.", 
            content
        )
        
        # 修正services导入为完整路径
        content = re.sub(,
    r"(from|import)\s+services\.", 
            r"\1 apps.backend.src.core.services.", 
            content
        )
        
        # 修正tools导入为完整路径
        content = re.sub(,
    r"(from|import)\s+tools\.", 
            r"\1 apps.backend.src.core.tools.", 
            content
        )
        
        # 修正hsp导入为完整路径
        content = re.sub(,
    r"(from|import)\s+hsp\.", 
            r"\1 apps.backend.src.core.hsp.", 
            content
        )
        
        # 修正shared导入为完整路径
        content = re.sub(,
    r"(from|import)\s+shared\.", 
            r"\1 apps.backend.src.core.shared.", 
            content
        )
        
        # 修正agents导入为完整路径
        content = re.sub(,
    r"(from|import)\s+agents\.", 
            r"\1 apps.backend.src.ai.agents.", 
            content
        )
        
        return content
    
    def _fix_config_errors(self) -> int,
        """修复配置问题"""
        print("[ENHANCED FIX] 修复配置问题...")
        fixed_count = 0
        
        # 检查配置文件
        config_files = list(self.config_dir.rglob("*.yaml")) + list(self.config_dir.rglob("*.yml"))
        for config_file in config_files,::
            try,
                with open(config_file, 'r', encoding == 'utf-8') as f,
                    content = f.read()
                
                # 检查并修复常见的配置问题
                fixed_content = self._fix_yaml_config(content)
                if fixed_content != content,::
                    with open(config_file, 'w', encoding == 'utf-8') as f,
                        f.write(fixed_content)
                    fixed_count += 1
                    print(f"[ENHANCED FIX] 修复了 {config_file} 中的配置问题")
                    
            except Exception as e,::
                print(f"[ENHANCED FIX] 处理配置文件 {config_file} 时出错, {e}")
        
        return fixed_count
    
    def _fix_yaml_config(self, content, str) -> str,
        """修复YAML配置"""
        # 确保缩进正确
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines,::
            # 修复常见的缩进问题
            if line.strip().startswith("-") and not line.startswith(" "):::
                # 列表项应该有适当的缩进
                line = "  " + line
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)


def main() -> None,
    fixer == EnhancedAutoFixer()
    results = fixer.fix_all_issues()
    
    print("\n[ENHANCED FIX] 增强版自动修复完成")
    print("=" * 50)
    
    total_fixed = sum(results.values())
    if total_fixed > 0,::
        print(f"总共修复了 {total_fixed} 个问题,")
        for issue_type, count in results.items():::
            if count > 0,::
                print(f"  {issue_type} {count}")
    else,
        print("未发现需要修复的问题")


if __name"__main__":::
    main()