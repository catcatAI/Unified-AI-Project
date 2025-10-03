#!/usr/bin/env python3
"""
修复项目中的语法问题
"""

import os
import re
from pathlib import Path

def fix_ham_memory_manager():
    """修复HAMMemoryManager文件中的重复类定义问题"""
    file_path = Path("apps/backend/src/ai/memory/ham_memory_manager.py")
    
    if not file_path.exists():
        print(f"文件不存在: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否存在重复的类定义
    # 查找文件末尾是否有重复的HAMMemoryManager类定义
    lines = content.split('\n')
    
    # 查找最后一个HAMMemoryManager类定义的开始位置
    last_class_index = -1
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == "class HAMMemoryManager:":
            last_class_index = i
            break
    
    # 如果找到了类定义，并且不是在文件的合理位置（比如前1000行）
    # 则认为是重复定义，需要删除
    if last_class_index > 1000:  # 假设正常类定义应该在前1000行内
        # 删除从最后一个类定义开始到文件末尾的所有内容
        lines = lines[:last_class_index]
        # 重新添加文件末尾应该存在的内容
        lines.append("")
        lines.append("# 从备份实现合并的函数")
        lines.append("")
        lines.append("def _mock_embed_texts(input: List[str]) -> List[List[float]]:")
        lines.append('    """A simple mock embedding function for testing purposes."""')
        lines.append("    logger.debug(f\"_mock_embed_texts called with input: {input}\")")
        lines.append("    # Returns a dummy embedding (e.g., a list of zeros or ones)")
        lines.append("    # The size (384) should match the expected model output for 'all-MiniLM-L6-v2'")
        lines.append("    return [[0.1] * 384 for _ in input]")
        lines.append("")
        lines.append("class MockEmbeddingFunction:")
        lines.append('    """A mock embedding function class for ChromaDB."""')
        lines.append("")
        lines.append("    def __call__(self, input: List[str]) -> List[List[float]]:")
        lines.append("        return _mock_embed_texts(input)")
        lines.append("")
        lines.append("    def name(self) -> str:")
        lines.append("        return \"MockEmbeddingFunction\"")
        lines.append("")
        lines.append("# Placeholder for actual stopword list and NLP tools if not available")
        lines.append("# 使用小写命名方式替代全大写常量命名方式，避免重新定义问题")
        lines.append("try:")
        lines.append("    # A very basic list, consider a more comprehensive one for real use")
        lines.append("    stopwords = set([\"a\", \"an\", \"the\", \"is\", \"are\", \"was\", \"were\", \"be\", \"been\", \"being\",")
        lines.append("                     \"have\", \"has\", \"had\", \"do\", \"does\", \"did\", \"will\", \"would\", \"should\",")
        lines.append("                     \"can\", \"could\", \"may\", \"might\", \"must\", \"of\", \"to\", \"in\", \"on\", \"at\",")
        lines.append("                     \"for\", \"with\", \"about\", \"against\", \"between\", \"into\", \"through\",")
        lines.append("                     \"during\", \"before\", \"after\", \"above\", \"below\", \"from\", \"up\", \"down\",")
        lines.append("                     \"out\", \"off\", \"over\", \"under\", \"again\", \"further\", \"then\", \"once\",")
        lines.append("                     \"here\", \"there\", \"when\", \"where\", \"why\", \"how\", \"all\", \"any\", \"both\",")
        lines.append("                     \"each\", \"few\", \"more\", \"most\", \"other\", \"some\", \"such\", \"no\", \"nor\",")
        lines.append("                     \"not\", \"only\", \"own\", \"same\", \"so\", \"than\", \"too\", \"very\", \"s\", \"t\",")
        lines.append("                     \"just\", \"don\", \"should've\", \"now\", \"i\", \"me\", \"my\", \"myself\", \"we\",")
        lines.append("                     \"our\", \"ours\", \"ourselves\", \"you\", \"your\", \"yours\", \"yourself\",")
        lines.append("                     \"yourselves\", \"he\", \"him\", \"his\", \"himself\", \"she\", \"her\", \"hers\",")
        lines.append("                     \"herself\", \"it\", \"its\", \"itself\", \"they\", \"them\", \"their\", \"theirs\",")
        lines.append("                     \"themselves\", \"what\", \"which\", \"who\", \"whom\", \"this\", \"that\", \"these\",")
        lines.append("                     \"those\", \"am\"])  # type: set[str]")
        lines.append("except ImportError:")
        lines.append("    stopwords = set()  # type: set[str]")
        lines.append("")
        lines.append("class HAMMemoryManager:")
        lines.append("    \"\"\"")
        lines.append("    分層抽象记忆管理器")
        lines.append("    实现分层抽象记忆管理功能，包括存储、检索、抽象和压缩")
        lines.append("    \"\"\"")
        lines.append("    # 添加缺失的常量定义")
        lines.append("    BASE_SAVE_DELAY_SECONDS = 0.1  # 基础保存延迟时间（秒）")
        lines.append("    # 使用文件级别的stopwords定义，避免重复定义")
        
        # 写入修复后的内容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"已修复HAMMemoryManager文件中的重复类定义问题: {file_path}")
        return True
    
    print(f"HAMMemoryManager文件中未发现重复类定义问题: {file_path}")
    return False

def fix_hsp_connector():
    """修复HSP连接器文件中的语法问题"""
    file_path = Path("apps/backend/src/core/hsp/connector.py")
    
    if not file_path.exists():
        print(f"文件不存在: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复属性定义缺少冒号的问题
    fixes = [
        (r"(\s*@property\s*\n\s*)def default_qos\(self\)\s*$", "\\1def default_qos(self):"),
        (r"(\s*@property\s*\n\s*)def mqtt_client\(self\)\s*$", "\\1def mqtt_client(self):"),
        (r"(\s*@property\s*\n\s*)def subscribed_topics\(self\)\s*$", "\\1def subscribed_topics(self):"),
        (r"(\s*@property\s*\n\s*)def on_message\(self\)\s*$", "\\1def on_message(self):"),
    ]
    
    fixed = False
    for pattern, replacement in fixes:
        if re.search(pattern, content, re.MULTILINE):
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            fixed = True
    
    if fixed:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"已修复HSP连接器文件中的语法问题: {file_path}")
        return True
    
    print(f"HSP连接器文件中未发现需要修复的语法问题: {file_path}")
    return False

def main():
    """主函数"""
    print("开始修复项目中的语法问题...")
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    
    # 修复各个文件
    fixes = [
        fix_ham_memory_manager,
        fix_hsp_connector,
    ]
    
    fixed_count = 0
    for fix_func in fixes:
        try:
            if fix_func():
                fixed_count += 1
        except Exception as e:
            print(f"修复过程中出现错误: {e}")
    
    print(f"修复完成，共修复了 {fixed_count} 个问题。")

if __name__ == "__main__":
    main()