import json

# 读取修复报告
with open('enhanced_auto_fix_report.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

fix_details = data.get('fix_details', [])
import_fixes = [d for d in fix_details if d.get('fix_type') == 'import_path' and '成功修复' in d.get('message', '')]

print(f"Import fixes: {len(import_fixes)}")

# 显示前5个导入路径修复
for i, detail in enumerate(import_fixes[:5]):
    print(f"  {i+1}. {detail.get('file_path', 'N/A')}: {detail.get('message', 'N/A')}")
    # 显示更改详情
    changes = detail.get('changes_made', [])
    for change in changes:
        print(f"    - {change}")