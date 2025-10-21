#!/usr/bin/env python3
import json
import re

# 读取文件内容
with open('training/configs/training_preset.json', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找所有的"training_scenarios"键
matches = list(re.finditer(r'"training_scenarios"\s*:', content))
print(f"找到 {len(matches)} 个 'training_scenarios' 键")

if len(matches) > 1:
    print("发现重复的 'training_scenarios' 键:")
    for i, match in enumerate(matches):
        pos = match.start()
        line_num = content[:pos].count('\n') + 1
        print(f"  {i+1}. 位置: 行 {line_num}, 字符位置 {pos}")
else:
    print("没有发现重复的 'training_scenarios' 键")

# 尝试解析JSON
try:
    data = json.loads(content)
    print("JSON解析成功")
except json.JSONDecodeError as e:
    print(f"JSON解析失败: {e}")