import json

# 读取修复报告
with open('enhanced_auto_fix_report.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Files processed: {data.get('files_processed', 0)}")
print(f"Files fixed: {data.get('files_fixed', 0)}")
print(f"Total fixes: {data.get('total_fixes', 0)}")

# 显示错误信息
errors = data.get('errors', [])
if errors:
    print(f"\nErrors ({len(errors)}):")
    for error in errors[:5]:  # 只显示前5个错误
        print(f"  - {error}")
else:
    print("\nNo errors found.")