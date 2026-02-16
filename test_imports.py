#!/usr/bin/env python3
"""Test script to verify AI service module imports"""

import sys
import traceback

modules_to_test = [
    "apps.backend.src.services.angela_llm_service",
    "apps.backend.src.services.audio_service",
    "apps.backend.src.services.vision_service",
    "apps.backend.src.services.api_models",
    "apps.backend.src.services.hot_reload_service",
    "apps.backend.src.tools.tool_dispatcher",
]

print("Testing AI service module imports...\n")

failed = []
passed = []

for module_name in modules_to_test:
    try:
        __import__(module_name)
        print(f"✓ {module_name}")
        passed.append(module_name)
    except Exception as e:
        print(f"✗ {module_name}")
        print(f"  Error: {e}")
        traceback.print_exc()
        failed.append(module_name)
        print()

print(f"\n{'='*60}")
print(f"Results: {len(passed)} passed, {len(failed)} failed")
print(f"{'='*60}")

if failed:
    print("\nFailed modules:")
    for module in failed:
        print(f"  - {module}")
    sys.exit(1)
else:
    print("\n✓ All AI service modules imported successfully!")
    sys.exit(0)
