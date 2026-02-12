import sys
import importlib
import os
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

# 设置路径
sys.path.insert(0, 'apps/backend/src')

# 查找所有Python文件
src_dir = Path('apps/backend/src')
py_files = list(src_dir.rglob('*.py'))

errors = []

for py_file in py_files:
    # 转换为模块路径
    rel_path = py_file.relative_to(src_dir)
    module_path = str(rel_path.with_suffix('')).replace(os.sep, '.')

    # 跳过__pycache__
    if '__pycache__' in str(rel_path) or rel_path.name.startswith('_'):
        continue

    try:
        importlib.import_module(module_path)
    except ImportError as e:
        errors.append((str(rel_path), str(e)))
    except Exception as e:
        logger.error(f'Error in {__name__}: {e}', exc_info=True)
        errors.append((str(rel_path), f"Non-ImportError: {type(e).__name__}: {e}"))


if errors:
    print(f"❌ 发现 {len(errors)} 个文件有导入错误:")
    for path, err in errors[:20]:
        print(f"  - {path}: {err}")
    if len(errors) > 20:
        print(f"  ... 还有 {len(errors) - 20} 个文件")
else:
    print("✅ 所有Python文件导入成功!")