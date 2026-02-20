"""Check syntax errors in core apps/backend/src files"""
import ast
from pathlib import Path

src_path = Path('apps/backend/src')
files = list(src_path.rglob('*.py'))
errors = []

for f in files:
    try:
        content = f.read_text(encoding='utf-8')
        ast.parse(content)
    except SyntaxError as e:
        errors.append((f, e))
    except Exception as e:
        errors.append((f, e))

print(f'Core src files checked: {len(files)}')
print(f'Files with syntax errors: {len(errors)}')
print(f'\nErrors in core src files:')
for f, e in errors[:30]:
    print(f'  {f}: {e}')

if len(errors) == 0:
    print('\n✓ All core src files are syntactically correct!')
else:
    print(f'\nNote: {len(errors)} files still have syntax errors')
