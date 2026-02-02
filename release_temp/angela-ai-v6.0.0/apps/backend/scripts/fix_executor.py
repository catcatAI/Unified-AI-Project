#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立的修复执行模块
负责根据错误分析结果执行各种类型的修复操作
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# 添加项目根目录到Python路径
try:
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))
    from apps.backend.scripts.error_analyzer import ErrorType
except (ImportError, IndexError):
    # Fallback for standalone execution or different structure
    # This allows the script to be run directly for debugging, assuming it's in the right place.
    from error_analyzer import ErrorType

import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FixExecutor:
    def __init__(self, error_report_file: str = "error_report.json") -> None:
        self.error_report_file = error_report_file
        # Assume the script is run from apps/backend, so project root is two levels up
        self.project_root = Path.cwd().parent.parent 
        self.fix_log: List[Dict[str, Any]] = []

    def _normalize_file_path(self, file_path: Optional[str]) -> Optional[Path]:
        """规范化文件路径"""
        if not file_path:
            return None
        
        # If the path is absolute, try to make it relative to the project root
        if Path(file_path).is_absolute():
            try:
                # This might fail if the path is on a different drive on Windows
                relative_path = Path(file_path).relative_to(self.project_root)
                full_path = self.project_root / relative_path
                if full_path.exists():
                    return full_path
            except ValueError:
                # Path is not within the project root, we can't handle it.
                logger.warning(f"Path {file_path} is not within project root {self.project_root}")
                return None
        
        # If it's already a relative path, resolve it from project root
        full_path = self.project_root / file_path
        if full_path.exists():
            return full_path
        
        logger.warning(f"Could not find file at path: {file_path}")
        return None

    def load_error_report(self) -> Dict[str, Any]:
        """加载错误分析报告"""
        try:
            with open(self.error_report_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"[ERROR] 错误报告文件 {self.error_report_file} 未找到")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"[ERROR] 错误报告文件格式错误: {e}")
            return {}

    def execute_fixes(self) -> bool:
        """执行所有修复操作"""
        logger.info("[FIX] 开始执行自动修复")
        print("=" * 50)
        
        error_report = self.load_error_report()
        if not error_report or error_report.get("total_errors", 0) == 0:
            logger.info("[FIX] 没有发现需要修复的错误")
            return True
        
        success_count = 0
        fail_count = 0
        
        for error in error_report.get("error_details", []):
            error_type_str = error.get("type", "")
            try:
                error_type = ErrorType(error_type_str)
            except ValueError:
                logger.warning(f"[FIX] 未知错误类型 '{error_type_str}', 跳过修复")
                continue

            file_path = error.get("file_path")
            line_number = error.get("line_number")
            message = error.get("message", "")
            details = error.get("details", {})
            
            logger.info(f"[FIX] 正在处理错误: {error_type.value}")
            if file_path:
                logger.info(f"      文件: {file_path}")
                if line_number:
                    logger.info(f"      行号: {line_number}")
            
            success = False
            try:
                # Simple dispatcher based on error type
                fix_method_name = f"_fix_{error_type.name.lower()}"
                fix_method = getattr(self, fix_method_name, self._fix_unknown)
                success = fix_method(file_path, line_number, message, details)
                
                if success:
                    success_count += 1
                    logger.info("[FIX] ✓ 修复成功")
                else:
                    fail_count += 1
                    logger.info("[FIX] ✗ 修复失败或无需修复")
                    
            except Exception as e:
                fail_count += 1
                logger.error(f"[FIX] ✗ 修复过程中发生错误: {e}", exc_info=True)
            
            print("-" * 30)
        
        print("=" * 50)
        logger.info(f"[FIX] 修复完成, 成功 {success_count}, 失败 {fail_count}")
        
        self._save_fix_log()
        
        return fail_count == 0

    def _save_fix_log(self):
        """保存修复日志"""
        log_file = self.project_root / "fix_log.json"
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(self.fix_log, f, ensure_ascii=False, indent=2)
            logger.info(f"[FIX] 修复日志已保存到 {log_file}")
        except Exception as e:
            logger.error(f"[FIX] 保存修复日志时出错: {e}")

    def _log_fix(self, success: bool, file_path: Optional[str], fix_type: str, description: str):
        self.fix_log.append({
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "file_path": file_path,
            "fix_type": fix_type,
            "description": description,
        })

    # --- Fixer Methods (Placeholders) ---

    def _fix_unknown(self, file_path: Optional[str], line: Optional[int], msg: str, details: dict) -> bool:
        logger.warning(f"No fix method implemented for this error type.")
        return False

    def _fix_async_warning(self, file_path: Optional[str], line: Optional[int], msg: str, details: dict) -> bool:
        logger.info("[FIX] 修复异步测试协程警告 (目前仅记录)")
        self._log_fix(False, file_path, "ASYNC_WARNING", "需要人工检查: coroutine was never awaited.")
        return False

    def _fix_init_error(self, file_path: Optional[str], line: Optional[int], msg: str, details: dict) -> bool:
        logger.info("[FIX] 修复对象初始化错误 (目前仅记录)")
        self._log_fix(False, file_path, "INIT_ERROR", "需要人工检查: __init__ missing arguments. Likely requires mocking.")
        return False

    def _fix_attribute_error(self, file_path: Optional[str], line: Optional[int], msg: str, details: dict) -> bool:
        logger.info("[FIX] 修复属性错误 (目前仅记录)")
        self._log_fix(False, file_path, "ATTRIBUTE_ERROR", "需要人工检查: AttributeError. Check for typos or incorrect method calls.")
        return False

    def _fix_assertion_error(self, file_path: Optional[str], line: Optional[int], msg: str, details: dict) -> bool:
        logger.info("[FIX] 修复断言失败 (目前仅记录)")
        self._log_fix(False, file_path, "ASSERTION_ERROR", "需要人工检查: AssertionError. Test expectation does not match result.")
        return False

    def _fix_timeout_error(self, file_path: Optional[str], line: Optional[int], msg: str, details: dict) -> bool:
        logger.info("[FIX] 修复超时错误 (目前仅记录)")
        self._log_fix(False, file_path, "TIMEOUT_ERROR", "需要人工检查: Test timed out. May require code optimization or increased timeout.")
        return False

    def _fix_import_error(self, file_path: Optional[str], line: Optional[int], msg: str, details: dict) -> bool:
        logger.info("[FIX] 修复导入路径错误 (目前仅记录)")
        self._log_fix(False, file_path, "IMPORT_ERROR", "需要人工检查: ImportError. Check for incorrect import paths or circular dependencies.")
        return False
        
    def _fix_syntax_error(self, file_path: Optional[str], line: Optional[int], msg: str, details: dict) -> bool:
        logger.info("[FIX] 修复语法错误 (目前仅记录)")
        self._log_fix(False, file_path, "SYNTAX_ERROR", "需要人工检查: SyntaxError.")
        return False

    def _fix_connection_error(self, file_path: Optional[str], line: Optional[int], msg: str, details: dict) -> bool:
        logger.info("[FIX] 修复连接错误 (目前仅记录)")
        self._log_fix(False, file_path, "CONNECTION_ERROR", "需要人工检查: ConnectionError. Check network or add retry logic.")
        return False

    def _fix_validation_error(self, file_path: Optional[str], line: Optional[int], msg: str, details: dict) -> bool:
        logger.info("[FIX] 修复数据验证错误 (目前仅记录)")
        self._log_fix(False, file_path, "VALIDATION_ERROR", "需要人工检查: ValidationError. Check data formats.")
        return False


if __name__ == "__main__":
    executor = FixExecutor()
    success = executor.execute_fixes()
    sys.exit(0 if success else 1)
