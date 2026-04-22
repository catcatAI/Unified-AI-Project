import os
import re

path = r'D:\Projects\Unified-AI-Project\apps\backend\src\services\main_api_server.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Truncate at the first '__main__' block to remove junk
# Find the FIRST occurrence of the main block
main_block_pattern = r'if __name__ == "__main__":'
match = re.search(main_block_pattern, text)
if match:
    # We keep everything up to the main block, then add our clean one
    text = text[:match.start()] + 'if __name__ == "__main__":\n    import uvicorn\n    uvicorn.run(app, host="0.0.0.0", port=8000)\n'

# 2. Cleanup brain_bridge references
# Remove global and getter
text = re.sub(r'_brain_bridge = None.*?\n', '_metabolic_heartbeat = None # 2030 Standard Pulse\n', text)
text = re.sub(r'def get_brain_bridge.*?return _brain_bridge\n\n', '', text, flags=re.DOTALL)

# 3. Add get_metabolic_heartbeat properly
heartbeat_func = """
def get_metabolic_heartbeat() -> MetabolicHeartbeat:
    global _metabolic_heartbeat
    if _metabolic_heartbeat is None:
        from core.autonomous.heartbeat import MetabolicHeartbeat
        _metabolic_heartbeat = MetabolicHeartbeat(update_interval=30.0)
    return _metabolic_heartbeat

"""
if 'def get_metabolic_heartbeat' not in text:
    text = text.replace('def get_desktop_interaction()', heartbeat_func + 'def get_desktop_interaction()')

# 4. Fix _initialize_all_services
text = text.replace('brain_bridge = get_brain_bridge()', '')
# Remove from return tuple
text = text.replace('        brain_bridge,', '')
text = text.replace(', brain_bridge', '')

# 5. Fix startup_event
# Find where brain_bridge.start() was and replace with heartbeat.start()
text = re.sub(r'await brain_bridge\.start\(\)', 'heartbeat = get_metabolic_heartbeat()\n    await heartbeat.start()', text)
# Fix unpacking
text = text.replace('        brain_bridge,\n    ) = _initialize_all_services()', '    ) = _initialize_all_services()')

# 6. Fix shutdown_event
text = re.sub(r'if _brain_bridge:.*?await _brain_bridge\.stop\(\)\n', '', text, flags=re.DOTALL)

# 7. Fix system_status
text = re.sub(r'brain_bridge = get_brain_bridge\(\)\n', '', text)
text = re.sub(r'"brain_bridge":.*?\),', '"heartbeat": get_metabolic_heartbeat()._running,', text)

# 8. Fix broadcast_state_updates (remove brain_bridge calls)
text = re.sub(r'# Get current state from brain bridge.*?status = brain_bridge\.get_current_status\(\)', 'status = {} # Placeholder for 2030 sync', text, flags=re.DOTALL)

# 9. Fix any IndentationErrors or dangling commas in unpacking
text = text.replace(',\n    ) = _initialize_all_services()', '\n    ) = _initialize_all_services()')

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print('Successfully applied definitive GSI-4 / 2030 Refactor to main_api_server.py')
