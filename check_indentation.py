# Check indentation around line 654
with open('apps/backend/src/core/ethics/ethics_manager.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i in range(649, 660):
    if i < len(lines):
        line = lines[i].rstrip()
        print(f'{i+1:3d}: {repr(line)}')