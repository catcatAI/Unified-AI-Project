"""
测试模块 - test_all_fixed_modules

 自动生成的测试模块,用于验证系统功能。



"""

# 测试所有已修复的模块
import sys
import traceback
import logging

logger = logging.getLogger(__name__)

modules_to_test = [
    "apps.backend.src.tools.logic_model.logic_parser_eval",
    "apps.backend.src.tools.logic_tool",
    "apps.backend.src.tools.math_model.lightweight_math_model",
    "apps.backend.src.tools.math_tool",
    "apps.backend.test_agi_integration",
    "apps.backend.src.core.managers.dependency_manager",
    "apps.backend.src.core.shared.types.common_types",
    "apps.backend.src.tools.math_model.model",
]

failed_modules = []
successful_modules = []

for module_name in modules_to_test:
    try:
        __import__(module_name)
        successful_modules.append(module_name)
        print(f"✓ {module_name} imported successfully")
    except Exception as e:
        logger.error(f"Error in test_all_fixed_modules.py: {e}", exc_info=True)
        failed_modules.append((module_name, str(e)))

        print(f"✗ {module_name} failed to import: {e}")

print(f"\nSummary:")
print(f"Successful: {len(successful_modules)}")
print(f"Failed: {len(failed_modules)}")

if failed_modules:
    print("\nFailed modules:")
    for module_name, error in failed_modules:
        print(f"  {module_name}: {error}")
else:
    print("\n🎉 All modules imported successfully!")
