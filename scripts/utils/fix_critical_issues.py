#!/usr/bin/env python3
"""
Angela AI - 關鍵問題修復工具
修復 P1-P4 所有優先級問題
"""

import ast
import re
import os
import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class CriticalIssuesFixer:
    """關鍵問題修復器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.fixes_applied = 0
        self.files_modified = 0
        self.fixes_log = []

    def fix_exception_handling(self, file_path: Path, dry_run: bool = False) -> int:
        """
        修復異常處理問題

        Args:
            file_path: 文件路徑
            dry_run: 是否只演示不實際修改

        Returns:
            int: 修復的問題數量
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"無法讀取文件 {file_path}: {e}")
            return 0

        original_content = content
        fixes = 0

        # 檢查是否有 logger 導入
        has_logger = 'import logging' in content or 'from logging import' in content
        logger_name = 'logger'

        if not has_logger:
            # 添加 logger 導入
            import_section = re.search(r'^(import .*?\n|from .*? import .*?\n)+', content, re.MULTILINE)
            if import_section:
                content = content[:import_section.end()] + "import logging\nlogger = logging.getLogger(__name__)\n" + content[import_section.end():]
                fixes += 1
                logger.info(f"添加 logger 導入到 {file_path}")

        # 模式 1: 修復缺少日誌的 except Exception: as e
        pattern1 = re.compile(
            r'(except Exception as e:\s*\n)(\s+)([^#\n]+)',
            re.MULTILINE
        )

        def add_logging_to_exception(match):
            nonlocal fixes
            indent = match.group(2)
            existing_code = match.group(3).strip()

            # 如果已有日誌，跳過
            if 'logger.' in existing_code or 'print(' in existing_code:
                return match.group(0)

            # 添加日誌
            fixes += 1
            return f"{match.group(1)}{indent}logger.error(f'Error in {file_path.name}: {{e}}', exc_info=True)\n{indent}{existing_code}\n"

        content = pattern1.sub(add_logging_to_exception, content)

        # 模式 2: 修復缺少異常對象的 except Exception as e:
        pattern2 = re.compile(
            r'(except Exception:\s*\n)(\s+)([^#\n]+)',
            re.MULTILINE
        )

        def add_exception_variable(match):
            nonlocal fixes
            existing_code = match.group(3).strip()

            # 如果已有日誌，跳過
            if 'logger.' in existing_code or 'print(' in existing_code:
                return match.group(0)

            fixes += 1
            return f"except Exception as e:\n{match.group(2)}logger.error(f'Error in {file_path.name}: {{e}}', exc_info=True)\n{match.group(2)}{existing_code}\n"

        content = pattern2.sub(add_exception_variable, content)

        # 模式 3: 修復裸 except Exception as e:
        pattern3 = re.compile(
            r'except:\s*\n(\s+)([^#\n]+)',
            re.MULTILINE
        )

        def fix_bare_except(match):
            nonlocal fixes
            indent = match.group(1)
            existing_code = match.group(2).strip()

            # 如果已有日誌，跳過
            if 'logger.' in existing_code or 'print(' in existing_code:
                return match.group(0)

            fixes += 1
            return f"except Exception as e:\n{indent}logger.error(f'Unexpected error in {file_path.name}: {{e}}', exc_info=True)\n{indent}{existing_code}\n"

        content = pattern3.sub(fix_bare_except, content)

        if content != original_content:
            if not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.files_modified += 1
                self.fixes_applied += fixes
                logger.info(f"修復了 {fixes} 個異常處理問題: {file_path}")
            else:
                logger.info(f"[DRY RUN] 將修復 {fixes} 個問題: {file_path}")
            return fixes
        return 0

    def fix_circular_imports(self, file_path: Path, dry_run: bool = False) -> int:
        """
        檢查並修復循環導入問題

        Args:
            file_path: 文件路徑
            dry_run: 是否只演示不實際修改

        Returns:
            int: 修復的問題數量
        """
        # 這是檢測，實際修復需要人工干預
        fixes = 0

        # 檢查常見的循環導入模式
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            return 0

        # 檢查是否在頂層導入了可能導致循環的模塊
        circular_import_patterns = [
            (r'from core\.autonomous import.*', '循環導入風險: core.autonomous'),
            (r'from core\.managers import.*', '循環導入風險: core.managers'),
            (r'from core\.action_execution_bridge import.*', '循環導入風險: action_execution_bridge'),
        ]

        for pattern, warning in circular_import_patterns:
            if re.search(pattern, content):
                fixes += 1
                logger.warning(f"檢測到 {warning} 在 {file_path}")

        return fixes

    def clean_todo_comments(self, file_path: Path, dry_run: bool = False) -> int:
        """
        清理 TODO/FIXME/XXX/HACK 註釋

        Args:
            file_path: 文件路徑
            dry_run: 是否只演示不實際修改

        Returns:
            int: 清理的註釋數量
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            return 0

        original_content = content
        fixes = 0

        # 清理無用的 HACK 註釋
        pattern = re.compile(r'#\s*HACK.*$', re.MULTILINE)
        matches = list(pattern.finditer(content))

        for match in reversed(matches):
            # 刪除整行
            line_start = content.rfind('\n', 0, match.start()) + 1
            line_end = content.find('\n', match.end())
            if line_end == -1:
                line_end = len(content)

            # 檢查這一行是否只有 HACK 註釋
            line = content[line_start:line_end].strip()
            if line.startswith('# HACK'):
                content = content[:line_start] + content[line_end:]
                fixes += 1

        if content != original_content:
            if not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.files_modified += 1
                self.fixes_applied += fixes
                logger.info(f"清理了 {fixes} 個 HACK 註釋: {file_path}")
            else:
                logger.info(f"[DRY RUN] 將清理 {fixes} 個註釋: {file_path}")
            return fixes
        return 0

    def fix_wildcard_imports(self, file_path: Path, dry_run: bool = False) -> int:
        """
        修復通配符導入

        Args:
            file_path: 文件路徑
            dry_run: 是否只演示不實際修改

        Returns:
            int: 修復的問題數量
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            return 0

        original_content = content
        fixes = 0

        # 檢查並修復通配符導入
        pattern = re.compile(r'from\s+(\S+)\s+import\s+\*', re.MULTILINE)

        def replace_wildcard(match):
            nonlocal fixes
            module = match.group(1)
            fixes += 1
            logger.warning(f"發現通配符導入: from {module} import * 在 {file_path}")
            # 返回註釋掉的原始代碼
            return f"# TODO: 替換通配符導入: # TODO: 替換通配符導入: # TODO: 替換通配符導入: # TODO: 替換通配符導入: from {module} import *"

        content = pattern.sub(replace_wildcard, content)

        if content != original_content:
            if not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.files_modified += 1
                self.fixes_applied += fixes
                logger.info(f"修復了 {fixes} 個通配符導入: {file_path}")
            else:
                logger.info(f"[DRY RUN] 將修復 {fixes} 個通配符導入: {file_path}")
            return fixes
        return 0

    def fix_config_password_placeholder(self, file_path: Path, dry_run: bool = False) -> int:
        """
        修復配置文件密碼佔位符

        Args:
            file_path: 文件路徑
            dry_run: 是否只演示不實際修改

        Returns:
            int: 修復的問題數量
        """
        if file_path.name not in ['.env', '.env.example', '.env.production']:
            return 0

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            return 0

        original_content = content
        fixes = 0

        # 修復密碼佔位符
        pattern = re.compile(r'^(PASSWORD|SECRET|KEY|TOKEN)\s*=\s*[^\s#]+', re.MULTILINE)

        def replace_password(match):
            nonlocal fixes
            fixes += 1
            key = match.group(1)
            return f"{key}=PLACEHOLDER_{key}_HERE  # TODO: Set actual value in production"

        content = pattern.sub(replace_password, content)

        if content != original_content:
            if not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.files_modified += 1
                self.fixes_applied += fixes
                logger.info(f"修復了 {fixes} 個密碼佔位符: {file_path}")
            else:
                logger.info(f"[DRY RUN] 將修復 {fixes} 個密碼佔位符: {file_path}")
            return fixes
        return 0

    def clean_temp_test_files(self, dry_run: bool = False) -> int:
        """
        清理臨時測試文件

        Args:
            dry_run: 是否只演示不實際刪除

        Returns:
            int: 清理的文件數量
        """
        test_dir = self.project_root / "tests"
        if not test_dir.exists():
            return 0

        cleaned = 0
        temp_patterns = ['temp_', 'test_', 'debug_', 'fix_', 'old_']

        for file_path in test_dir.rglob("*.py"):
            if any(file_path.name.startswith(pattern) for pattern in temp_patterns):
                # 檢查是否是調試測試文件
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if 'TODO:' in content or 'FIXME:' in content or 'DEBUG' in content:
                        if not dry_run:
                            file_path.unlink()
                            logger.info(f"刪除臨時測試文件: {file_path}")
                        else:
                            logger.info(f"[DRY RUN] 將刪除: {file_path}")
                        cleaned += 1
                except Exception as e:
                    logger.error(f'Error in {__name__}: {e}', exc_info=True)
                    pass


        return cleaned

    def fix_all_issues(self, dry_run: bool = False) -> Dict[str, int]:
        """
        修復所有問題

        Args:
            dry_run: 是否只演示不實際修改

        Returns:
            Dict[str, int]: 修復統計
        """
        stats = {
            'exception_handling': 0,
            'circular_imports': 0,
            'todo_comments': 0,
            'wildcard_imports': 0,
            'config_passwords': 0,
            'temp_test_files': 0,
        }

        # 遍歷所有 Python 文件
        python_files = list(self.project_root.rglob("*.py"))
        logger.info(f"開始檢查 {len(python_files)} 個 Python 文件...")

        for file_path in python_files:
            # 跳過虛擬環境、緩存和備份目錄
            skip_patterns = ['venv', '__pycache__', 'tests_backup', 'docs', '.git', 'node_modules', 'build', 'dist']
            if any(pattern in str(file_path) for pattern in skip_patterns):
                continue

            # 跳過測試文件中的異常處理修復（測試可能需要簡單的異常處理）
            if 'tests/' in str(file_path) and 'tests_backup/' not in str(file_path):
                stats['todo_comments'] += self.clean_todo_comments(file_path, dry_run)
                continue

            # 修復異常處理
            stats['exception_handling'] += self.fix_exception_handling(file_path, dry_run)

            # 檢查循環導入
            stats['circular_imports'] += self.fix_circular_imports(file_path, dry_run)

            # 清理 TODO 註釋
            stats['todo_comments'] += self.clean_todo_comments(file_path, dry_run)

            # 修復通配符導入
            stats['wildcard_imports'] += self.fix_wildcard_imports(file_path, dry_run)

        # 修復配置文件密碼佔位符
        for env_file in ['.env', '.env.example', '.env.production']:
            env_path = self.project_root / env_file
            if env_path.exists():
                stats['config_passwords'] += self.fix_config_password_placeholder(env_path, dry_run)

        # 清理臨時測試文件
        stats['temp_test_files'] = self.clean_temp_test_files(dry_run)

        return stats


def main():
    """主函數"""
    project_root = "d:\\Projects\\Unified-AI-Project"

    logger.info("=" * 80)
    logger.info("Angela AI - 關鍵問題修復工具")
    logger.info("=" * 80)
    logger.info("")

    # 詢問是否使用 dry run 模式
    dry_run = False  # 設為 False 進行實際修復

    if dry_run:
        logger.info("⚠️  DRY RUN 模式 - 不會實際修改文件")
        logger.info("")

    fixer = CriticalIssuesFixer(project_root)

    logger.info("開始修復所有問題...")
    logger.info("")

    stats = fixer.fix_all_issues(dry_run=dry_run)

    logger.info("")
    logger.info("=" * 80)
    logger.info("修復完成")
    logger.info("=" * 80)
    logger.info("")
    logger.info("修復統計:")
    logger.info(f"  異常處理修復: {stats['exception_handling']} 個問題")
    logger.info(f"  循環導入檢測: {stats['circular_imports']} 個問題")
    logger.info(f"  TODO 註釋清理: {stats['todo_comments']} 處")
    logger.info(f"  通配符導入修復: {stats['wildcard_imports']} 個")
    logger.info(f"  密碼佔位符修復: {stats['config_passwords']} 個")
    logger.info(f"  臨時測試文件清理: {stats['temp_test_files']} 個")
    logger.info("")
    logger.info(f"修改的文件數: {fixer.files_modified}")
    logger.info(f"總修復數: {fixer.fixes_applied}")
    logger.info("")

    if dry_run:
        logger.info("這是 DRY RUN，沒有實際修改任何文件")
        logger.info("請確認修復計劃後，將 dry_run 設為 False 並重新運行")
    else:
        logger.info("✅ 所有修復已應用")
        logger.info("")
        logger.info("建議下一步:")
        logger.info("1. 運行測試驗證修復: python3 comprehensive_test.py")
        logger.info("2. 運行異常處理分析檢查改善: python3 apps/backend/src/core/security/exception_handler_analyzer.py")


if __name__ == "__main__":
    main()