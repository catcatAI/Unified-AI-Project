import requests
import time

# 等待服务器启动
_ = time.sleep(5)

try:
    response = requests.get('http://localhost:8000/')
    _ = print("Status code:", response.status_code)
    _ = print("Response:", response.text)
except Exception as e:
    _ = print("Error:", e)