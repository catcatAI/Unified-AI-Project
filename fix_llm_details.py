import os
import re

path = r'D:\Projects\Unified-AI-Project\apps\backend\src\services\angela_llm_service.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add missing attribute to __init__
init_patch = '''
        self.enable_memory_enhancement = self.config.get("enable_memory_enhancement", True)
        self.is_available = False
'''
text = text.replace('        self.is_available = False', init_patch)

# 2. Fix Relative Imports to Absolute Imports
text = re.sub(r'from \.\.ai', 'from ai', text)
text = re.sub(r'from \.\.core', 'from core', text)
text = re.sub(r'from \.\.integrations', 'from integrations', text)

# 3. Specifically fix the _load_memory_modules relative import fallback
text = re.sub(r'except ImportError as e:.*?TaskGenerator = _TG', '', text, flags=re.DOTALL)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print('Successfully applied Absolute Imports and Attribute fixes to angela_llm_service.py')
