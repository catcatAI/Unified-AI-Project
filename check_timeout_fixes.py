import json

# 读取修复报告
with open('enhanced_auto_fix_report.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

fix_details = data.get('fix_details', [])
timeout_fixes = [d for d in fix_details if d.get('fix_type') == 'timeout_error' and '成功修复' in d.get('message', '')]

print(f"Timeout fixes: {len(timeout_fixes)}")

# 显示前5个超时错误修复
for i, detail in enumerate(timeout_fixes[:5]):
    print(f"  {i+1}. {detail.get('file_path', 'N/A')}: {detail.get('message', 'N/A')}")
    # 显示更改详情
    changes = detail.get('changes_made', [])
    for change in changes:
        print(f"    - {change}")