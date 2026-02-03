
class TestClass,
    def method_with_issues(self, a = [] b = {}):
        # 可变默认参数
        return a, b

def function_with_issues():
    # 缺少冒号
    if True,:
        pass
    
    # 未定义变量
    result = undefined_var
    return result

@undefined_decorator
decorated_function():
    pass
