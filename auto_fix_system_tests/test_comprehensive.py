
class TestClass:
    def method_with_issues(self, a=None, b=None):
        # 可变默认参数 - 已修复
        if a is None:
            a = []
        if b is None:
            b = {}
        return a, b

def function_with_issues():
    # 缺少冒号 - 已修复
    if True:
        pass
    
    # 未定义变量 - 已修复
    undefined_var = "test_value"  # 定义变量
    result = undefined_var
    return result

@undefined_decorator
def decorated_function():
    pass
