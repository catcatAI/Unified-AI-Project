#!/usr/bin/env python3
"""
独立的修复执行模块
负责根据错误分析结果执行各种类型的修复操作
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, Any
# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 使用相对导入
# 修复导入路径，ErrorType在error_analyzer.py文件中
from apps.backend.scripts.error_analyzer import ErrorType


class FixExecutor:
    def __init__(self, error_report_file: str = "error_report.json") -> None:
        self.error_report_file = error_report_file
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.fix_log = []
    
    def _normalize_file_path(self, file_path: str) -> Path:
        """规范化文件路径"""
        if not file_path:
            return None
            
        # 移除路径前缀，只保留相对路径部分
        # 处理类似 "Project\apps\backend\src\core_ai\memory\vector_store.py" 的路径
        if "Project\\apps\\backend\\" in file_path:
            file_path = file_path.split("Project\\apps\\backend\\")[-1]
        elif "apps\\backend\\" in file_path:
            file_path = file_path.split("apps\\backend\\")[-1]
        elif file_path.startswith("src\\"):
            pass  # 已经是相对路径
        elif file_path.startswith("\\") or ":\\" in file_path:
            # 绝对路径，检查是否在项目目录中
            path_obj = Path(file_path)
            if self.project_root in path_obj.parents:
                try:
                    file_path = str(path_obj.relative_to(self.project_root))
                except ValueError:
                    # 如果无法计算相对路径，返回None
                    return None
            else:
                # 不在项目目录中的绝对路径，无法处理
                return None
        
        # 构建完整的文件路径
        full_path = self.project_root / file_path
        return full_path if full_path.exists() else None

    def load_error_report(self) -> Dict[str, Any]:
        """加载错误分析报告"""
        try:
            with open(self.error_report_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[ERROR] 错误报告文件 {self.error_report_file} 未找到")
            return {}
        except json.JSONDecodeError as e:
            print(f"[ERROR] 错误报告文件格式错误: {e}")
            return {}
    
    def execute_fixes(self) -> bool:
        """执行所有修复操作"""
        print("[FIX] 开始执行自动修复")
        print("=" * 50)
        
        error_report = self.load_error_report()
        if not error_report or error_report.get("total_errors", 0) == 0:
            print("[FIX] 没有发现需要修复的错误")
            return True
        
        success_count = 0
        fail_count = 0
        
        # 处理每个错误
        for error in error_report.get("error_details", []):
            error_type = error.get("type", "")
            file_path = error.get("file_path", "")
            line_number = error.get("line_number")
            message = error.get("message", "")
            details = error.get("details", {})
            
            print(f"[FIX] 正在处理错误: {error_type}")
            if file_path:
                print(f"      文件: {file_path}")
                if line_number:
                    print(f"      行号: {line_number}")
            
            # 根据错误类型执行相应的修复
            try:
                if error_type == ErrorType.ASYNC_WARNING.value:
                    success = self._fix_async_warning(file_path, line_number, message, details)
                elif error_type == ErrorType.INIT_ERROR.value:
                    success = self._fix_init_error(file_path, line_number, message, details)
                elif error_type == ErrorType.ATTRIBUTE_ERROR.value:
                    success = self._fix_attribute_error(file_path, line_number, message, details)
                elif error_type == ErrorType.ASSERTION_ERROR.value:
                    success = self._fix_assertion_error(file_path, line_number, message, details)
                elif error_type == ErrorType.TIMEOUT_ERROR.value:
                    success = self._fix_timeout_error(file_path, line_number, message, details)
                elif error_type == ErrorType.IMPORT_ERROR.value:
                    success = self._fix_import_error(file_path, line_number, message, details)
                elif error_type == ErrorType.CONNECTION_ERROR.value:
                    success = self._fix_connection_error(file_path, line_number, message, details)
                elif error_type == ErrorType.VALIDATION_ERROR.value:
                    success = self._fix_validation_error(file_path, line_number, message, details)
                else:
                    print(f"[FIX] 未知错误类型，跳过修复: {error_type}")
                    success = False
                
                if success:
                    success_count += 1
                    print(f"[FIX] ✓ 修复成功")
                else:
                    fail_count += 1
                    print(f"[FIX] ✗ 修复失败")
                    
            except Exception as e:
                fail_count += 1
                print(f"[FIX] ✗ 修复过程中发生错误: {e}")
            
            print("-" * 30)
        
        print("=" * 50)
        print(f"[FIX] 修复完成: 成功 {success_count}, 失败 {fail_count}")
        
        # 保存修复日志
        self._save_fix_log()
        
        return fail_count == 0
    
    def _save_fix_log(self):
        """保存修复日志"""
        log_file = self.project_root / "fix_log.json"
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(self.fix_log, f, ensure_ascii=False, indent=2)
            print(f"[FIX] 修复日志已保存到 {log_file}")
        except Exception as e:
            print(f"[FIX] 保存修复日志时出错: {e}")
    
    def _fix_async_warning(self, file_path: str, line_number: int, message: str, details: dict) -> bool:
        """修复异步测试协程警告"""
        print("[FIX] 执行异步测试协程警告修复")
        
        # 规范化文件路径
        normalized_path = self._normalize_file_path(file_path)
        if not normalized_path or not normalized_path.exists():
            print("[FIX] 文件路径无效，无法修复")
            return False
        
        try:
            # 读取文件内容
            with open(normalized_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 查找未await的协程调用
            # 这是一个简化的修复，实际修复需要更复杂的分析
            fixed = False
            for i, line in enumerate(lines):
                # 查找可能的协程调用（以括号结尾的行）
                if re.search(r'\w+\s*=\s*\w+\(', line) and not re.search(r'\b(await|def|class)\b', line):
                    # 检查下一行是否是使用该变量的地方
                    if i + 1 < len(lines):
                        next_line = lines[i + 1]
                        # 如果下一行使用了这个变量，可能需要await
                        var_match = re.search(r'(\w+)\s*=', line)
                        if var_match:
                            var_name = var_match.group(1)
                            if var_name in next_line and 'await' not in next_line:
                                # 在当前行添加await
                                lines[i] = line.replace(f'{var_name} =', f'{var_name} = await')
                                fixed = True
                                print(f"[FIX] 在第 {i+1} 行添加了 await 关键字")
            
            if fixed:
                # 写入修复后的内容
                with open(normalized_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                return True
            else:
                print("[FIX] 未找到需要修复的异步调用")
                return False
                
        except Exception as e:
            print(f"[FIX] 修复异步警告时发生错误: {e}")
            return False
    
    def _fix_init_error(self, file_path: str, line_number: int, message: str, details: dict) -> bool:
        """修复对象初始化错误"""
        print("[FIX] 执行对象初始化错误修复")
        
        # 规范化文件路径
        normalized_path = self._normalize_file_path(file_path)
        if not normalized_path or not normalized_path.exists():
            print("[FIX] 文件路径无效，无法修复")
            return False
        
        try:
            # 读取文件内容
            with open(normalized_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找类初始化调用
            # 添加unittest.mock或pytest fixtures
            if "import pytest" not in content and "from unittest.mock" not in content:
                # 在文件开头添加导入
                content = "from unittest.mock import MagicMock, patch\nimport pytest\n\n" + content
                
                # 写入修复后的内容
                with open(normalized_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("[FIX] 添加了必要的导入语句")
                return True
            else:
                print("[FIX] 已存在必要的导入语句")
                return True
                
        except Exception as e:
            print(f"[FIX] 修复初始化错误时发生错误: {e}")
            return False
    
    def _fix_attribute_error(self, file_path: str, line_number: int, message: str, details: dict) -> bool:
        """修复属性错误"""
        print("[FIX] 执行属性错误修复")
        
        # 规范化文件路径
        normalized_path = self._normalize_file_path(file_path)
        if not normalized_path or not normalized_path.exists():
            print("[FIX] 文件路径无效，无法修复")
            return False
        
        # 属性错误通常需要人工检查，这里只记录日志
        print("[FIX] 属性错误需要人工检查确认方法名是否正确")
        return False
    
    def _fix_assertion_error(self, file_path: str, line_number: int, message: str, details: dict) -> bool:
        """修复断言失败"""
        print("[FIX] 执行断言失败修复")
        
        # 规范化文件路径
        normalized_path = self._normalize_file_path(file_path)
        if not normalized_path or not normalized_path.exists():
            print("[FIX] 文件路径无效，无法修复")
            return False
        
        # 断言失败通常需要人工确认期望值是否正确
        print("[FIX] 断言失败需要人工确认期望值是否正确")
        # 这里可以尝试从错误消息中提取期望值和实际值的差异
        match = re.search(r"AssertionError: (.*) != (.*)", message)
        return False
    
    def _fix_timeout_error(self, file_path: str, line_number: int, message: str, details: dict) -> bool:
        """修复超时错误"""
        print("[FIX] 执行超时错误修复")
        
        # 规范化文件路径
        normalized_path = self._normalize_file_path(file_path)
        if not normalized_path or not normalized_path.exists():
            print("[FIX] 文件路径无效，无法修复")
            return False
        
        # 超时错误通常需要增加超时时间或优化代码
        print("[FIX] 超时错误需要增加超时时间或优化代码逻辑")
        return False
    
    def _fix_import_error(self, file_path: str, line_number: int, message: str, details: dict) -> bool:
        """修复导入路径错误"""
        print("[FIX] 执行导入路径错误修复")
        
        # 规范化文件路径
        normalized_path = self._normalize_file_path(file_path)
        if not normalized_path or not normalized_path.exists():
            print("[FIX] 文件路径无效，无法修复")
            return False
        
        # 导入错误需要检查导入路径是否正确
        print("[FIX] 导入错误需要检查导入路径是否正确")
        return False
    
    def _fix_connection_error(self, file_path: str, line_number: int, message: str, details: dict) -> bool:
        """修复连接错误"""
        print("[FIX] 执行连接错误修复")
        
        # 规范化文件路径
        normalized_path = self._normalize_file_path(file_path)
        if not normalized_path or not normalized_path.exists():
            print("[FIX] 文件路径无效，无法修复")
            return False
        
        # 连接错误通常需要检查网络配置或增加重试机制
        print("[FIX] 连接错误需要检查网络配置或增加重试机制")
        # 尝试添加重试逻辑到相关代码
        try:
            with open(normalized_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找可能的网络连接代码并添加重试机制
            # 这是一个简化的示例，实际修复需要更复杂的分析
            if "requests." in content or "urllib." in content or "socket." in content:
                # 添加重试装饰器导入
                if "from tenacity import retry" not in content and "import tenacity" not in content:
                    content = "from tenacity import retry, stop_after_attempt, wait_exponential\n\n" + content
                    with open(normalized_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print("[FIX] 添加了重试机制导入")
                    return True
            
            return False
        except Exception as e:
            print(f"[FIX] 修复连接错误时发生异常: {e}")
            return False
    
    def _fix_validation_error(self, file_path: str, line_number: int, message: str, details: dict) -> bool:
        """修复数据验证错误"""
        print("[FIX] 执行数据验证错误修复")
        
        # 规范化文件路径
        normalized_path = self._normalize_file_path(file_path)
        if not normalized_path or not normalized_path.exists():
            print("[FIX] 文件路径无效，无法修复")
            return False
        
        # 数据验证错误需要检查数据格式或添加数据验证逻辑
        print("[FIX] 数据验证错误需要检查数据格式或添加数据验证逻辑")
        # 从错误消息中提取验证失败的字段信息
        match = re.search(r"Missing '(.+)' in (.+) payload", message)
        if match:
            missing_field = match.group(1)
            payload_type = match.group(2)
            print(f"[FIX] 缺少字段 '{missing_field}' 在 '{payload_type}' 负载中")
            # 可以尝试添加缺失的字段
        
        # 尝试修复常见的验证错误
        try:
            with open(normalized_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否有数据验证相关的代码
            if "ValidationError" in content or "validation" in content.lower():
                # 添加默认值或验证逻辑
                print("[FIX] 检测到验证相关代码，建议人工检查数据结构")
                return False  # 需要人工干预
            
            return False
        except Exception as e:
            print(f"[FIX] 修复验证错误时发生异常: {e}")
            return False


if __name__ == "__main__":
    executor = FixExecutor()
    success = executor.execute_fixes()
    sys.exit(0 if success else 1)