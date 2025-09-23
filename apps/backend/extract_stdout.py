import json

# 读取测试结果文件
with open(r'D:\Projects\Unified-AI-Project\apps\backend\test_results\test_results_20250923_170534.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 提取stdout内容
stdout_content = data.get('stdout', '')

# 打印前5000个字符
print(stdout_content[:5000])

# 查找失败的测试
if "FAILED" in stdout_content:
    print("\n=== 失败的测试 ===")
    lines = stdout_content.split('\n')
    for line in lines:
        if "FAILED" in line:
            print(line)
else:
    print("\n=== 没有找到明确标记为FAILED的测试 ===")

# 查找包含"timeout"的行
if "timeout" in stdout_content.lower():
    print("\n=== 超时相关的行 ===")
    lines = stdout_content.split('\n')
    for line in lines:
        if "timeout" in line.lower():
            print(line)