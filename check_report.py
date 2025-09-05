import json

# 读取修复报告
with open('enhanced_auto_fix_report.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total files processed: {data.get('files_processed', 0)}")
print(f"Files fixed: {data.get('files_fixed', 0)}")
print(f"Total fixes: {data.get('total_fixes', 0)}")
print(f"Fixes made count: {len(data.get('fixes_made', []))}")

# 显示前10个修复详情
fixes_made = data.get('fixes_made', [])
print(f"\nFirst 10 fixes:")
for i, fix in enumerate(fixes_made[:10]):
    print(f"  {i+1}. {fix.get('file', 'N/A')}: {fix.get('fix', 'N/A')}")