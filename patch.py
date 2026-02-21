import os

js_dir = 'd:/Projects/Unified-AI-Project/apps/web-live2d-viewer/js'
files_to_patch = ['live2d-manager.js', 'live2d-manager-improved.js', 'live2d-cubism-wrapper.js']

for f in files_to_patch:
    path = os.path.join(js_dir, f)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Replace local:// interpolations with a check
        content = content.replace("`local://${", "`${window.electronAPI?.platform === 'web' ? '' : 'local://'}${")
        content = content.replace("'local://'", "(window.electronAPI?.platform === 'web' ? '' : 'local://')")
        content = content.replace("'local:///'", "(window.electronAPI?.platform === 'web' ? '' : 'local:///')")
        
        with open(path, 'w', encoding='utf-8') as file:
            file.write(content)

audio_path = os.path.join(js_dir, 'audio-handler.js')
if os.path.exists(audio_path):
    with open(audio_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Patch audio handler to avoid loading native modules in web
    content = content.replace(
        "return await import('../../native_modules/", 
        "if (window.electronAPI?.platform === 'web') throw new Error('Web platform'); return await import('../../native_modules/"
    )
    
    with open(audio_path, 'w', encoding='utf-8') as file:
        file.write(content)

print("Patching complete.")
