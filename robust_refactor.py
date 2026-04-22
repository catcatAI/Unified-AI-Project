import os
import sys

file_path = r'D:\Projects\Unified-AI-Project\apps\backend\src\services\main_api_server.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip_mode = False

for line in lines:
    # Skip the function get_brain_bridge
    if "def get_brain_bridge()" in line:
        skip_mode = True
        continue
    
    if skip_mode:
        if line.startswith("def ") or line.startswith("# "):
            skip_mode = False
        else:
            continue

    # Skip lines with _brain_bridge
    if "_brain_bridge" in line and "None" not in line:
        continue
    
    # Update _brain_bridge = None to _metabolic_heartbeat = None
    if "_brain_bridge = None" in line:
        new_lines.append("_metabolic_heartbeat = None # 2030 Standard Pulse\n")
        continue

    # Fix _initialize_all_services
    if "brain_bridge = get_brain_bridge()" in line:
        continue
    
    # Fix return tuple in _initialize_all_services and unpacking in startup_event
    if "brain_bridge," in line:
        line = line.replace("brain_bridge,", "")
    elif ", brain_bridge" in line:
        line = line.replace(", brain_bridge", "")

    # Fix shutdown_event
    if "await _brain_bridge.stop()" in line:
        continue

    # Fix system_status
    if '"brain_bridge":' in line:
        # We'll handle this line specifically if we can match it
        continue

    new_lines.append(line)

# Final cleanup of any missed mentions
final_lines = [l for l in new_lines if "brain_bridge" not in l]

# Ensure MetabolicHeartbeat function is present
if "def get_metabolic_heartbeat()" not in "".join(final_lines):
    idx = 0
    for i, l in enumerate(final_lines):
        if "def get_desktop_interaction()" in l:
            idx = i
            break
    
    heartbeat_code = [
        "def get_metabolic_heartbeat() -> MetabolicHeartbeat:\n",
        "    global _metabolic_heartbeat\n",
        "    if _metabolic_heartbeat is None:\n",
        "        from core.autonomous.heartbeat import MetabolicHeartbeat\n",
        "        _metabolic_heartbeat = MetabolicHeartbeat(update_interval=30.0)\n",
        "    return _metabolic_heartbeat\n",
        "\n"
    ]
    final_lines[idx:idx] = heartbeat_code

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(final_lines)

print("Successfully performed robust refactor of main_api_server.py")
