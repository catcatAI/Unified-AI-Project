import os
import re

# 定义测试目录
test_dir = r"D:\Projects\Unified-AI-Project\tests"

# 定义需要修复的导入路径映射
import_mappings = {
    # 修复code_understanding模块的导入路径
    r"from code_understanding\.lightweight_code_model import LightweightCodeModel": 
    "from apps.backend.src.ai.code_understanding.lightweight_code_model import LightweightCodeModel",
    
    # 修复HSP模块的导入路径
    r"from \.{3}src\.hsp\.connector import HSPConnector": 
    "from apps.backend.src.core.hsp.connector import HSPConnector",
    
    r"from \.{3}src\.hsp\.types import HSPFactPayload": 
    "from apps.backend.src.core.hsp.types import HSPFactPayload",
    
    # 修复其他可能的导入路径问题
    r"from \.{2}src\.hsp\.connector import HSPConnector": 
    "from apps.backend.src.core.hsp.connector import HSPConnector",
    
    r"from \.{2}src\.hsp\.types import HSPFactPayload": 
    "from apps.backend.src.core.hsp.types import HSPFactPayload",
    
    r"from \.src\.hsp\.connector import HSPConnector": 
    "from apps.backend.src.core.hsp.connector import HSPConnector",
    
    r"from \.src\.hsp\.types import HSPFactPayload": 
    "from apps.backend.src.core.hsp.types import HSPFactPayload",
}

def read_file_with_encoding(file_path):
    """尝试不同的编码方式读取文件"""
    encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read(), encoding
        except UnicodeDecodeError:
            continue
    # 如果所有编码都失败，使用latin1并忽略错误
    with open(file_path, 'r', encoding='latin1', errors='ignore') as f:
        return f.read(), 'latin1'

# 递归遍历所有Python文件
for root, dirs, files in os.walk(test_dir):
    for file in files:
        if file.endswith('.py'):
            file_path = os.path.join(root, file)
            
            # 读取文件内容
            try:
                content, encoding = read_file_with_encoding(file_path)
            except Exception as e:
                print(f"无法读取文件 {file_path}: {e}")
                continue
            
            # 检查是否需要修复导入路径
            original_content = content
            for old_import, new_import in import_mappings.items():
                content = re.sub(old_import, new_import, content)
            
            # 如果内容有变化，写回文件
            if content != original_content:
                try:
                    with open(file_path, 'w', encoding=encoding) as f:
                        f.write(content)
                    print(f"修复导入路径: {file_path}")
                except Exception as e:
                    print(f"无法写入文件 {file_path}: {e}")

print("导入路径修复完成。")