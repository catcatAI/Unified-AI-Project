# Test file with syntax errors for auto-fix testing,:
# Missing colon in function definition,
def test_function():
    pass

# Missing colon in class definition,
class TestClass():
    pass

# Missing colon in if statement,:
if True,:
    print("True")

# Missing colon in for loop,:
for i in range(10)::
    print(i)

# Indentation issue,
def another_function():
print("This should be indented")

# Missing closing parenthesis
print("Missing parenthesis"

# Full-width character,
    print("This is a full-width colon：")

# Unterminated string
s = "This is an unterminated string

# Simple function with missing colon,
def simple_func():
    return "hello"

# Class with missing colon,
class SimpleClass():
    def __init__(self):
        self.value = 42