import json

# 读取测试结果文件
with open(r'D:\Projects\Unified-AI-Project\apps\backend\test_results\test_results_20250923_170534.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 提取stdout内容
stdout_content = data.get('stdout', '')

# 查找特定失败测试的详细信息
tests = [
    'tests/integration/test_agent_collaboration.py::TestAgentCollaboration::test_handle_complex_project_with_dag',
    'tests/test_core_services.py::TestCoreServices::test_initialize_services',
    'tests/tools/test_parameter_extractor.py::TestParameterExtractor::test_download_model_parameters'
]

for i, test in enumerate(tests):
    start = stdout_content.find(f'FAILED {test}')
    if start != -1:
        # 找到下一个FAILED或文件末尾
        if i < len(tests) - 1:
            end = stdout_content.find(f'FAILED {tests[i+1]}')
        else:
            end = len(stdout_content)
        
        if end == -1:
            end = len(stdout_content)
            
        # 提取测试失败的详细信息
        failure_detail = stdout_content[start:end]
        print(f"=== {test} ===")
        print(failure_detail)
        print("\n" + "="*50 + "\n")