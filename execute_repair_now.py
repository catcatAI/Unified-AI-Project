#!/usr/bin/env python3
"""
立即执行项目修复
"""

import sys
import os
import re
from pathlib import Path
import logging

# 设置日志
logging.basicConfig(level=logging.INFO(), format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleProjectFixer:
    """简化的项目修复器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.project_scope_dirs = [
            "apps/backend/src",
            "tools",
            "scripts"
        ]
        self.exclude_dirs = [
            "node_modules",
            "venv",
            "__pycache__",
            ".pytest_cache"
        ]
        
    def is_in_scope(self, file_path):
        """检查文件是否在范围内"""
        try:
            rel_path = file_path.relative_to(self.project_root)
            rel_str = str(rel_path)
            
            # 检查是否在排除目录中
            for exclude_dir in self.exclude_dirs:
                if exclude_dir in rel_str:
                    return False
            
            # 检查是否在项目目录中
            for scope_dir in self.project_scope_dirs:
                if rel_str.startswith(scope_dir):
                    return True
            
            return False
        except ValueError:
            return False
    
    def scan_files(self):
        """扫描项目文件"""
        files = []
        for scope_dir in self.project_scope_dirs:
            scope_path = self.project_root / scope_dir
            if scope_path.exists():
                for file_path in scope_path.rglob("*.py"):
                    if self.is_in_scope(file_path):
                        files.append(file_path)
        return files
    
    def fix_file(self, file_path):
        """修复单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original = content
            changes = False
            
            # 修复字典语法
            pattern = r'"([^"]+)":\s*([^,\n}]+)(,?)'
            replacement = r'"\1": \2\3'
            content = re.sub(pattern, replacement, content)
            if content != original:
                changes = True
                logger.info(f"修复字典语法: {file_path}")
            
            # 修复raise语法
            content = re.sub(r'raise\s+', 'raise ', content)
            if content != original and not changes:
                changes = True
                logger.info(f"修复raise语法: {file_path}")
            
            # 修复装饰器语法
            content = re.sub(r'(@\w+)', r'\1', content)
            if content != original and not changes:
                changes = True
                logger.info(f"修复装饰器语法: {file_path}")
            
            # 修复assert语法
            content = re.sub(r'assert\s+', 'assert ', content)
            if content != original and not changes:
                changes = True
                logger.info(f"修复assert语法: {file_path}")
            
            # 修复kwargs语法
            content = re.sub(r'\*\*(\w+)', r'**\1', content)
            if content != original and not changes:
                changes = True
                logger.info(f"修复kwargs语法: {file_path}")
            
            # 修复智能引号
            content = content.replace('“', '"')
            content = content.replace('”', '"')
            content = content.replace('‘', "'")
            content = content.replace('’', "'")
            if content != original and not changes:
                changes = True
                logger.info(f"修复智能引号: {file_path}")
            
            # 写回文件
            if changes:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # 验证语法
            try:
                compile(content, str(file_path), 'exec')
                return True
            except SyntaxError as e:
                logger.error(f"语法错误仍然存在: {file_path} {e}")
                return False
                
        except Exception as e:
            logger.error(f"处理文件 {file_path} 时出错: {e}")
            return False
    
    def run_repair(self):
        """执行修复"""
        logger.info("开始扫描项目文件...")
        files = self.scan_files()
        logger.info(f"找到 {len(files)} 个Python文件")
        
        fixed = 0
        failed = 0
        
        for file_path in files:
            if self.fix_file(file_path):
                fixed += 1
            else:
                failed += 1
        
        logger.info(f"\n修复完成:")
        logger.info(f"修复成功: {fixed}")
        logger.info(f"修复失敗: {failed}")
        
        return failed == 0

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("开始执行项目修复")
    logger.info("=" * 60)
    
    fixer = SimpleProjectFixer()
    success = fixer.run_repair()
    
    if success:
        logger.info("\n✅ 所有文件修复成功！")
        return 0
    else:
        logger.error("\n❌ 部分文件修复失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())