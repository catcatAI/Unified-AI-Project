from tools.scripts.core.fix_engine import FixEngine, FixType
from pathlib import Path

# 创建修复引擎实例
engine = FixEngine(Path('.'))

# 运行语法修复
result = engine.run_fix(FixType.SYNTAX_FIX)

# 输出结果
print(f"修复结果: {result.status.value}")
print(f"消息: {result.message}")

# 如果有详细信息，也输出
if hasattr(result, 'details') and result.details:
    print(f"详细信息: {result.details}")

# 获取修复摘要
summary = engine.get_fix_summary()
print("\n修复摘要:")
print(f"总修复数: {summary['total_fixes']}")
print(f"完成: {summary['completed']}")
print(f"失败: {summary['failed']}")
print(f"跳过: {summary['skipped']}")

# 保存结果
engine.save_results(Path("syntax_fix_results.json"))