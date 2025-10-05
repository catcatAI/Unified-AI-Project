#!/usr/bin/env python3
"""
修复HSP连接器中的所有剩余问题
"""

import re
from pathlib import Path

def fix_hsp_connector():
    """修复HSP连接器文件"""
    file_path = Path("apps/backend/src/core/hsp/connector.py")
    
    if not file_path.exists():
        print(f"文件不存在: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复disconnect方法的缩进问题
    pattern = r'(async def disconnect\(self\))\n(\s*)(if self\.mock_mode:)'
    content = re.sub(pattern, r'\1\n\2\3', content)
    
    # 修复connect方法中的语法问题
    pattern = r'(_ = await self\.external_connector\.connect\(\))\n(\s*)(self\.is_connected = self\.external_connector\.is_connected)'
    content = re.sub(pattern, r'\1\n\2\3', content)
    
    # 修复close方法的缩进问题
    pattern = r'(async def close\(self\):)\n(\s*)(self\.logger\.info\("HSPConnector: Disconnecting external connector\.\.\."\))'
    content = re.sub(pattern, r'\1\n\2\3', content)
    
    # 写入修复后的内容
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"已修复HSP连接器文件: {file_path}")
    return True

def main():
    """主函数"""
    print("开始修复HSP连接器中的所有剩余问题...")
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent.parent
    import os
    os.chdir(project_root)
    
    # 修复文件
    if fix_hsp_connector():
        print("HSP连接器修复完成。")
    else:
        print("HSP连接器修复失败。")

if __name__ == "__main__":
    main()