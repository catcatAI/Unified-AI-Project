#!/usr/bin/env python3
import json

# 检查JSON文件
try:
    with open('training/configs/training_preset.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    print("JSON文件格式正确")
    print("training_scenarios数量:", len(data.get('training_scenarios', {})))
    print("training_scenarios keys:", list(data.get('training_scenarios', {}).keys()))
    
    # 检查是否有重复的键
    scenarios = data.get('training_scenarios', {})
    print("\n检查training_scenarios中的键:")
    for key in scenarios:
        print(f"  - {key}")
        
except json.JSONDecodeError as e:
    print(f"JSON解析错误: {e}")
    print(f"错误位置: line {e.lineno} column {e.colno} (char {e.pos})")
except Exception as e:
    print(f"其他错误: {e}")