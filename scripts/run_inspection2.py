import sys
sys.path.insert(0, 'apps/backend/src')
from ai.code_inspection import create_inspector
import json

inspector = create_inspector('apps/backend/src')
result = inspector.inspect()

# Critical issues
critical = [i for i in result['report'].issues if i.severity.value == 'critical']
print('=== CRITICAL ISSUES ===')
for i in critical:
    print(f'{i.id} | {i.file}:{i.line}')
    print(f'  {i.description}')
    print(f'  Suggestion: {i.suggestion}')
    print(f'  Confidence: {i.confidence:.0%}')
    print()

# By category
by_cat = {}
for i in result['report'].issues:
    cat = i.category.value
    by_cat[cat] = by_cat.get(cat, 0) + 1

print('=== ISSUES BY CATEGORY ===')
for cat, count in sorted(by_cat.items(), key=lambda x: -x[1]):
    print(f'  {cat:15} {count:4}')

print()
print('=== AUTO-FIXABLE ===')
fixable = [i for i in result['report'].issues if i.auto_fixable]
print(f'  Count: {len(fixable)}')
for i in fixable[:10]:
    print(f'    {i.id} | {i.file}:{i.line} | {i.fix_template}')

# Show security issues
sec = [i for i in result['report'].issues if i.category.value == 'security']
print()
print('=== SECURITY ISSUES ===')
for i in sec[:10]:
    print(f'  [{i.severity.value.upper():8}] {i.file.split("src\\\\")[-1] if "src\\\\" in i.file else i.file.split("/")[-1]}:{i.line}')
    print(f'    {i.description}')
    if i.suggestion:
        print(f'    Fix: {i.suggestion}')