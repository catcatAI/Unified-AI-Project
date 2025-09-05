import sys
from pathlib import Path

# 添加项目路径到Python路径
project_root = Path(__file__).parent
backend_src = project_root / "apps" / "backend" / "src"
sys.path.insert(0, str(backend_src))

print("测试core_services导入...")
try:
    import apps.backend.src.core_services
    print("成功导入core_services")
except Exception as e:
    print(f"导入失败: {e}")

print("测试完成。")