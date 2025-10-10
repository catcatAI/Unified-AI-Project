import ast
import sys

def check_file_syntax(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
        print(f"✅ {filepath} - Syntax OK")
        return True
    except SyntaxError as e:
        print(f"❌ {filepath} - Syntax error: {e}")
        return False
    except Exception as e:
        print(f"❌ {filepath} - Error: {e}")
        return False

# Check key files
files_to_check = [
    'apps/backend/src/tools/tool_dispatcher.py',
    'apps/backend/src/ai/dialogue/dialogue_manager.py',
    'apps/backend/src/core/services/multi_llm_service.py',
    'apps/backend/src/ai/reasoning/causal_reasoning_engine.py'
]

all_good = True
for file in files_to_check:
    if not check_file_syntax(file):
        all_good = False

if all_good:
    print("\n🎉 All files have valid syntax!")
else:
    print("\n⚠️  Some files have syntax errors that need to be fixed.")