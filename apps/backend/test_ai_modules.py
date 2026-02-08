#!/usr/bin/env python3
"""深度检查脚本"""
import sys
sys.path.insert(0, '/home/cat/桌面/Unified-AI-Project/apps/backend')

print('=' * 60)
print('深度检查: AI 模块导入测试')
print('=' * 60)

# 测试AI模块
ai_modules = [
    ('src.ai.level5_asi_system', 'Level5 ASI System'),
    ('src.ai.genesis', 'Genesis'),
    ('src.ai.memory.vector_store', 'Vector Store'),
    ('src.ai.memory.ham_memory', 'HAM Memory'),
    ('src.ai.deep_mapper', 'Deep Mapper'),
]

all_ok = True
for module_name, desc in ai_modules:
    try:
        __import__(module_name)
        print(f'✅ {desc}')
    except Exception as e:
        print(f'❌ {desc}: {str(e)[:60]}')
        all_ok = False

print('=' * 60)
if all_ok:
    print('✅ 所有AI模块导入成功!')
else:
    print('⚠️ 存在导入错误')
print('=' * 60)