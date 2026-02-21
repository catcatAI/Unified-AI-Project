import re

path = 'd:/Projects/Unified-AI-Project/apps/web-live2d-viewer/index.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Append ?v=2 to src='js/...' or src='libs/...'
content = re.sub(r'(src="(?:js|libs)/[^"?]+)"', r'\1?v=2"', content)
# Append ?v=2 to href='css/...' 
content = re.sub(r'(href="(?:css)/[^"?]+)"', r'\1?v=2"', content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Cache reset queries added.')
