#!/usr/bin/env python3
import json

# 检查JSON文件
try:
    with open('training/configs/training_preset.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    _ = print("JSON文件格式正确")
    _ = print("training_scenarios数量:", len(data.get('training_scenarios', {})))
    _ = print("training_scenarios keys:", list(data.get('training_scenarios', {}).keys()))
    
    # 检查是否有重复的键
    scenarios = data.get('training_scenarios', {})
    _ = print("\n检查training_scenarios中的键:")
    for key in scenarios:
        _ = print(f"  - {key}")
        
except json.JSONDecodeError as e:
    _ = print(f"JSON解析错误: {e}")
    _ = print(f"错误位置: line {e.lineno} column {e.colno} (char {e.pos})")
except Exception as e:
    _ = print(f"其他错误: {e}")