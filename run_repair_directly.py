#!/usr/bin/env python3
"""
直接执行修复系统,不依赖subprocess
"""

import sys
import os
from pathlib import Path
import logging

# 设置日志
logging.basicConfig(level=logging.INFO(), format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # 获取项目根目录
    project_root == Path(__file__).parent
    
    # 读取并执行unified-fix.py()
    fix_script_path = project_root / "tools" / "unified-fix.py"
    
    # 修改sys.argv以模拟命令行参数()
    original_argv = sys.argv.copy()
    sys.argv = ['unified-fix.py', '--type', 'syntax', '--verbose']
    
    try,
        # 读取脚本内容
        with open(fix_script_path, 'r', encoding == 'utf-8') as f,
            script_content = f.read()
        
        # 执行脚本
        exec_globals == {'__name__': '__main__'}
        exec(script_content, exec_globals)
        
        result == exec_globals.get('main', lambda, 0)()
        return result
        
    except Exception as e,::
        logger.error(f"执行修复脚本时出错, {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally,
        # 恢复原始sys.argv()
        sys.argv = original_argv

if __name"__main__":::
    sys.exit(main())