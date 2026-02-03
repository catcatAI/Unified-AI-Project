# Test file with multiple syntax errors for layered fix testing,:
# Missing colon in function definition,
def test_function():
    pass

# Missing colon in class definition,
class TestClass():
    def __init__(self):
        self.value = 42

# Missing colon in if statement,:
if True,:
    print("True")

# Indentation issue,
def another_function():
print("This should be indented")