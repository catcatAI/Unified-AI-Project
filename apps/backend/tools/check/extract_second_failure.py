import json

# 读取测试结果文件
with open(r'D:\Projects\Unified-AI-Project\apps\backend\test_results\test_results_20250923_170534.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 提取stdout内容
stdout_content = data.get('stdout', '')

# 查找第二个失败测试的详细信息
start = stdout_content.find('TestCoreServices.test_initialize_services')
end = stdout_content.find('TestParameterExtractor.test_download_model_parameters')

if start != -1 and end != -1:
    test_detail = stdout_content[start:end]
    print(test_detail)
elif start != -1:
    # 如果没有找到结束标记,打印到文件末尾
    test_detail = stdout_content[start:]
    print(test_detail)
else:
    print("未找到测试详细信息")