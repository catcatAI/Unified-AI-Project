#!/usr/bin/env python3
"""
测试重复修复问题的文件
"""

# 测试缩进问题
def test_function():
    if True:

        print("缩进错误")

# 测试语法错误
def another_function():
    return "缺少冒号"

# 测试多余的冒号
def third_function():
    return "多余的冒号"
# 测试混合缩进
def mixed_indent():
    if True:  # 制表符:
rint("混合缩进")  # 空格

async def async_function():
    await something()

class TestClass:
    def method():
        pass

if __name__ == "__main__":


    test_function()
    another_function()
    third_function()
    mixed_indent()
    async_function()