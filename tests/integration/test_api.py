"""
测试模块 - test_api

自动生成的测试模块，用于验证系统功能。
"""

import requests

try:
    response = requests.get('http://localhost:8000/')
    _ = print("Status code:", response.status_code)
    _ = print("Response:", response.text)
except Exception as e:
    _ = print("Error:", e)