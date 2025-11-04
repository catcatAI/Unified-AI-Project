with open('unified_auto_fix_system/modules/class_fixer.py', 'r') as f:
    lines = f.readlines()
    
print("类修复器中的方法定义:")
print("="*50)

for i, line in enumerate(lines, 1):
    if 'def ' in line and line.strip().startswith('def '):
        print(f'{i:3d}: {line.strip()}')