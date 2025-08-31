#!/usr/bin/env python3
import json

# 检查JSON文件
print("开始检查JSON文件...")
try:
    with open('training/configs/training_preset.json', 'r', encoding='utf-8') as f:
        content = f.read()
        print(f"文件大小: {len(content)} 字符")
        
        # 尝试解析JSON
        data = json.loads(content)
        print("JSON文件格式正确")
        print("training_scenarios数量:", len(data.get('training_scenarios', {})))
        
except json.JSONDecodeError as e:
    print(f"JSON解析错误: {e}")
    print(f"错误位置: line {e.lineno} column {e.colno} (char {e.pos})")
    
    # 显示错误位置附近的文本
    lines = content.split('\n')
    start_line = max(0, e.lineno - 5)
    end_line = min(len(lines), e.lineno + 5)
    
    print(f"\n错误位置附近的文本 (行 {start_line+1} 到 {end_line}):")
    for i in range(start_line, end_line):
        marker = ">>> " if i == e.lineno - 1 else "    "
        print(f"{marker}{i+1:3d}: {lines[i]}")
        
except Exception as e:
    print(f"其他错误: {e}")