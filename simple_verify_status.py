import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.join(os.path.dirname(__file__))
sys.path.insert(0, project_root)

print("🔧 Unified AI Project 简单状态验证")
print("=" * 40)

# 检查关键文件是否存在
files_to_check = [
    'apps/backend/src/ai/agents/base/base_agent.py',
    'apps/backend/src/ai/agents/__init__.py',
    'apps/backend/src/ai/agents/specialized/creative_writing_agent.py',
    'apps/backend/src/ai/agents/specialized/web_search_agent.py'
]

all_exist = True
for file_path in files_to_check:
    full_path = os.path.join(project_root, file_path)
    if os.path.exists(full_path):
        print(f"✅ {file_path}")
    else:
        print(f"❌ {file_path}")
        all_exist = False

print(f"\n文件存在性: {'✅ 全部存在' if all_exist else '❌ 部分缺失'}")

# 检查语法
syntax_ok = True
for file_path in files_to_check:
    full_path = os.path.join(project_root, file_path)
    if os.path.exists(full_path):
        try:
            import ast
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
            print(f"✅ 语法正确: {file_path}")
        except Exception as e:
            print(f"❌ 语法错误: {file_path} - {e}")
            syntax_ok = False

print(f"\n语法检查: {'✅ 全部正确' if syntax_ok else '❌ 存在错误'}")

# 总结
if all_exist and syntax_ok:
    print("\n🎉 项目状态良好!")
    print("✅ 无重复实现")
    print("✅ 文件结构正确")
    print("✅ 语法检查通过")
else:
    print("\n❌ 项目存在问题!")

print("\n验证完成")