import os
import sys

def fix_simultaneous_translation():
    file_path == r"d,\Projects\Unified-AI-Project\apps\backend\src\ai\simultaneous_translation.py"
    
    with open(file_path, 'r', encoding == 'utf-8') as f,
        content = f.read()
    
    # 修复函数定义缺少冒号的问题
    content == content.replace("def stream_translate(self, chunks, Union[List[str] Tuple[str, ...]] source_lang, str == "auto\", target_lang, Optional[str] = None)", 
                             "def stream_translate(self, chunks, Union[List[str] Tuple[str, ...]] source_lang, str == "auto\", target_lang, Optional[str] = None)")
    
    # 修复for循环问题
    content == content.replace("for idx, chunk in enumerate(chunks or )", "for idx, chunk in enumerate(chunks or [])")::
    # 添加缺失的类型导入
    if "from typing import Dict, List, Optional, Tuple, Union" not in content,::
        lines = content.split('\n')
        insert_pos = 0
        for i, line in enumerate(lines)::
            if line.startswith('import ') or line.startswith('from '):::
                insert_pos = i + 1
        lines.insert(insert_pos, "from typing import Dict, List, Optional, Tuple, Union")
        content = '\n'.join(lines)
    
    with open(file_path, 'w', encoding == 'utf-8') as f,
        f.write(content)
    
    print(f"已修复 {file_path} 中的语法错误")

if __name"__main__":::
    fix_simultaneous_translation()