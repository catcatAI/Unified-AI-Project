import json

# 读取修复报告
with open('enhanced_auto_fix_report.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total files: {data.get('total_files', 0)}")
print(f"Successful fixes: {data.get('successful_fixes', 0)}")
print(f"Failed fixes: {data.get('failed_fixes', 0)}")
print(f"Fix details count: {len(data.get('fix_details', []))}")

# 显示前5个修复详情
fix_details = data.get('fix_details', [])
print(f"\nFirst 5 fix details:")
for i, detail in enumerate(fix_details[:5]):
    print(f"  {i+1}. {detail.get('file_path', 'N/A')}: {detail.get('fix_type', 'N/A')} - {detail.get('message', 'N/A')}")