import re
import os

# 1. Cache Busting index.html
path = 'd:/Projects/Unified-AI-Project/apps/web-live2d-viewer/index.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# Replace any ?v=2 with ?v=3
html = html.replace('?v=2', '?v=3')

# add ?v=3 to all src="js/..." or src="libs/..." that don't have it
def add_cache_bust(match):
    src = match.group(1)
    if '?v=' not in src:
        return f'src="{src}?v=3"'
    return match.group(0)

html = re.sub(r'src="(js/[^"]+|libs/[^"]+)"', add_cache_bust, html)

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)

# 2. Purge mangled local:// replaces from live2d-cubism-wrapper.js
wrapper_path = 'd:/Projects/Unified-AI-Project/apps/web-live2d-viewer/js/live2d-cubism-wrapper.js'
with open(wrapper_path, 'r', encoding='utf-8') as f:
    code = f.read()

bad_str1 = "${window.electronAPI?.platform === 'web' ? '' : (window.electronAPI?.platform === 'web' ? '' : 'local://')}"
bad_str2 = "(window.electronAPI?.platform === 'web' ? '' : 'local://')"
bad_str3 = "(window.electronAPI?.platform === 'web' ? '' : 'local:///')"

code = code.replace(bad_str1, "")
code = code.replace(bad_str2, "''")
code = code.replace(bad_str3, "''")

with open(wrapper_path, 'w', encoding='utf-8') as f:
    f.write(code)

# 3. Purge mangled local:// from live2d-manager.js
manager_path = 'd:/Projects/Unified-AI-Project/apps/web-live2d-viewer/js/live2d-manager.js'
with open(manager_path, 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(bad_str1, "")
code = code.replace(bad_str2, "''")
code = code.replace(bad_str3, "''")

with open(manager_path, 'w', encoding='utf-8') as f:
    f.write(code)

print('Cleaned up paths and applied cache busting.')
