"""
测试模块 - test_json_fix

自动生成的测试模块,用于验证系统功能。
"""

import json

# Test the JSON serialization that was fixed in the tests
mock_decomposed_plan = [
    {"capability_needed": "analyze_csv_data", "task_parameters": {"source": "data.csv"}, "dependencies": []},
    {"capability_needed": "generate_marketing_copy", "task_parameters": {"product_description": "Our new product, which is based on the analysis: <output_of_task_0>"}, "dependencies": [0]}
]

# Test serialization
serialized = json.dumps(mock_decomposed_plan)
print("Serialized plan:")
print(serialized)

# Test deserialization
deserialized = json.loads(serialized)
print("\nDeserialized plan:")
print(deserialized)

# Verify it's a list of dictionaries
print(f"\nIs list: {isinstance(deserialized, list)}")
print(f"Length: {len(deserialized)}")
if len(deserialized) > 0:
    print(f"First item is dict: {isinstance(deserialized[0], dict)}")
    print(f"First item capability: {deserialized[0].get('capability_needed')}")