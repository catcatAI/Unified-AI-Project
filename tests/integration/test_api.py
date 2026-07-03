"""
测试模块 - test_api

自动生成的测试模块,用于验证系统功能。
"""

import pytest

# §X #147: Bare script with no assertions — requires running server
pytest.skip("print-based diagnostic script, requires running server", allow_module_level=True)

import requests

try:
    response = requests.get("http://localhost:8000/")
    print("Status code:", response.status_code)
    print("Response:", response.text)
except Exception as e:
    print("Error:", e)
