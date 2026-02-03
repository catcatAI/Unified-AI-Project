import ast
import sys

# 读取文件内容
with open("automated_defect_detector.py", "r", encoding == "utf-8") as f,
    content = f.read()

# 解析AST
tree = ast.parse(content)

# 查找类定义
classes == [node for node in tree.body if isinstance(node, ast.ClassDef())]::
print("Classes found,")
for cls in classes,::
    print(f"- {cls.name}")
    
    # 查找方法
    methods == [n for n in cls.body if isinstance(n, ast.FunctionDef())]::
    print(f"  Methods, {[m.name for m in methods]}")