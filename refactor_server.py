import os

file_path = r'D:\Projects\Unified-AI-Project\apps\backend\src\services\main_api_server.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip_until = None

for i, line in enumerate(lines):
    # 1. Remove _brain_bridge global
    if "global _brain_bridge" in line:
        continue
    if "_brain_bridge =" in line and "None" in line:
        new_lines.append("_metabolic_heartbeat = None # 2030 Standard Pulse\n")
        continue
    
    # 2. Skip get_brain_bridge function
    if "def get_brain_bridge()" in line:
        skip_until = "def get_desktop_interaction()"
        continue
    
    if skip_until and skip_until in line:
        skip_until = None
    
    if skip_until:
        continue

    # 3. Fix _initialize_all_services return unpacking
    if "brain_bridge = get_brain_bridge()" in line:
        continue
    
    if "brain_bridge," in line:
        line = line.replace("brain_bridge,", "")
    
    # 4. Fix shutdown_event
    if "if _brain_bridge:" in line:
        # Skip next two lines (the stop call)
        # Assuming the next line is the await stop call
        continue
    if "_brain_bridge.stop()" in line:
        continue

    # 5. Fix system_status
    if '"brain_bridge":' in line:
        new_lines.append('            "heartbeat": get_metabolic_heartbeat()._running,\n')
        continue
    if "brain_bridge = get_brain_bridge()" in line:
        continue

    new_lines.append(line)

# Add get_metabolic_heartbeat if missing
if "def get_metabolic_heartbeat()" not in "".join(new_lines):
    insertion_point = 0
    for i, line in enumerate(new_lines):
        if "def get_desktop_interaction()" in line:
            insertion_point = i
            break
    
    heartbeat_func = [
        "def get_metabolic_heartbeat() -> MetabolicHeartbeat:\n",
        "    global _metabolic_heartbeat\n",
        "    if _metabolic_heartbeat is None:\n",
        "        from core.autonomous.heartbeat import MetabolicHeartbeat\n",
        "        _metabolic_heartbeat = MetabolicHeartbeat(update_interval=30.0)\n",
        "    return _metabolic_heartbeat\n",
        "\n"
    ]
    new_lines[insertion_point:insertion_point] = heartbeat_func

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Successfully refactored main_api_server.py")
