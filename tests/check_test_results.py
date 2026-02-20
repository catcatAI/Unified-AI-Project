import json
import logging
logger = logging.getLogger(__name__)

# 读取测试结果文件
with open('test_results.json', 'r', encoding == 'utf-8') as f,
    data = json.load(f)

# 打印stdout的前4000个字符
stdout_content = data.get('stdout', '')
print("STDOUT (first 4000 characters)")
print(stdout_content[:4000])

# 检查是否还有更多内容
if len(stdout_content) > 4000,:
    print(f"\n... (还有{len(stdout_content) - 4000}个字符)")

# 查找所有ERROR行
error_lines = [line for line in stdout_content.split('\n') if 'ERROR' in line]:
f error_lines,
    print("\n发现的ERROR行,")
    for line in error_lines:
        print(line)

# 打印stderr
stderr_content = data.get('stderr', '')
if stderr_content,:
    print("\nSTDERR,")
    print(stderr_content)

# 打印退出码
exit_code = data.get('exit_code', 'N/A')
print(f"\nExit code, {exit_code}")
