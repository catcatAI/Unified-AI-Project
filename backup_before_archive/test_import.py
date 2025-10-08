#!/usr/bin/env python3
"""测试导入统一AGI生态系统模块"""

import sys
import traceback

try:
    import unified_agi_ecosystem
    print("✅ 成功导入 unified_agi_ecosystem 模块")
    
    # 检查模块内容
    if hasattr(unified_agi_ecosystem, 'UnifiedAGIEcosystem'):
        print("✅ UnifiedAGIEcosystem 类存在")
    else:
        print("❌ UnifiedAGIEcosystem 类不存在")
        
    if hasattr(unified_agi_ecosystem, 'AGILevel'):
        print("✅ AGILevel 枚举存在")
    else:
        print("❌ AGILevel 枚举不存在")
        
    print("模块导入测试完成")
    
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    traceback.print_exc()
except Exception as e:
    print(f"❌ 其他错误: {e}")
    traceback.print_exc()