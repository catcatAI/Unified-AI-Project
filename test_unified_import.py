#!/usr/bin/env python3
"""
快速测试统一自动修复系统导入
"""

try:
    from unified_auto_repair_system import UnifiedAutoRepairSystem
    print("✅ 统一自动修复系统导入成功")
    
    # 基础功能测试
    system = UnifiedAutoRepairSystem()
    print("✅ 系统实例创建成功")
    
except Exception as e:
    print(f"❌ 导入或创建失败: {e}")
    import traceback
    print(f"错误详情: {traceback.format_exc()}")