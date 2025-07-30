#!/usr/bin/env python3
"""
文档链接验证脚本
检查所有 Markdown 文件中的内部链接是否有效
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Dict

def find_markdown_files(root_dir: str) -> List[Path]:
    """查找所有 Markdown 文件"""
    root_path = Path(root_dir)
    return list(root_path.rglob("*.md"))

def extract_links(file_path: Path) -> List[Tuple[str, str]]:
    """从 Markdown 文件中提取链接"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 匹配 [text](link) 格式的链接
        pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        matches = re.findall(pattern, content)
        return matches
    except Exception as e:
        print(f"❌ 读取文件失败: {file_path} - {e}")
        return []

def validate_link(base_path: Path, link: str) -> bool:
    """验证链接是否有效"""
    # 跳过外部链接
    if link.startswith(('http://', 'https://', 'mailto:', '#')):
        return True
    
    # 处理相对路径
    if link.startswith('./'):
        link = link[2:]
    elif link.startswith('../'):
        # 处理上级目录
        target_path = base_path.parent / link
    else:
        target_path = base_path.parent / link
    
    # 解析路径
    target_path = target_path.resolve()
    
    # 检查文件是否存在
    return target_path.exists()

def main():
    """主函数"""
    print("🔍 开始验证文档链接...")
    
    root_dir = "."
    markdown_files = find_markdown_files(root_dir)
    
    broken_links = []
    total_links = 0
    
    for md_file in markdown_files:
        print(f"\n📄 检查文件: {md_file}")
        links = extract_links(md_file)
        
        for text, link in links:
            total_links += 1
            if not validate_link(md_file, link):
                broken_links.append((md_file, text, link))
                print(f"  ❌ 无效链接: [{text}]({link})")
            else:
                print(f"  ✅ 有效链接: [{text}]({link})")
    
    print(f"\n📊 验证结果:")
    print(f"总链接数: {total_links}")
    print(f"无效链接数: {len(broken_links)}")
    
    if broken_links:
        print(f"\n❌ 发现 {len(broken_links)} 个无效链接:")
        for file_path, text, link in broken_links:
            print(f"  {file_path}: [{text}]({link})")
        return 1
    else:
        print("✅ 所有链接都有效!")
        return 0

if __name__ == "__main__":
    exit(main())