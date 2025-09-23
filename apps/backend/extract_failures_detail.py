import json

# 读取测试结果文件
with open(r'D:\Projects\Unified-AI-Project\apps\backend\test_results\test_results_20250923_170534.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 提取stdout内容
stdout_content = data.get('stdout', '')

# 查找失败测试的详细错误信息
# 查找"FAILURES"部分
failures_start = stdout_content.find('FAILURES')
if failures_start != -1:
    # 查找最后的汇总信息
    summary_start = stdout_content.find('===== ', failures_start)
    if summary_start != -1:
        failures_content = stdout_content[failures_start:summary_start]
        print("=== 测试失败详细信息 ===")
        print(failures_content)
    else:
        # 如果没有找到汇总信息，打印到文件末尾
        failures_content = stdout_content[failures_start:]
        print("=== 测试失败详细信息 ===")
        print(failures_content)
else:
    print("未找到FAILURES部分")