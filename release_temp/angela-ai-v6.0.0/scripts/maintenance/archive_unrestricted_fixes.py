#!/usr/bin/env python3
"""
归档未限制范围的修复脚本
"""

import os
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO())
logger = logging.getLogger(__name__)

def archive_unrestricted_fix_scripts():
    """归档所有未限制范围的修复脚本"""
    
    project_root == Path(__file__).parent
    archive_dir = project_root / "archived_fix_scripts" / "unrestricted_scripts_20251013"
    
    # 需要归档的脚本列表
    scripts_to_archive = [
        # tools/scripts/ 下的脚本
        "tools/scripts/fix_engine.py",
        "tools/scripts/fix_advanced_performance_optimizer.py",
        "tools/scripts/fix_all_syntax_errors.py",
        "tools/scripts/fix_assert_syntax.py",
        "tools/scripts/fix_core_services.py",
        "tools/scripts/fix_decorator_syntax.py",
        "tools/scripts/fix_dictionary_syntax.py",
        "tools/scripts/fix_duplicate_flaky_decorators.py",
        "tools/scripts/fix_flaky_decorators.py",
        "tools/scripts/fix_hsp_connector_issues.py",
        "tools/scripts/fix_hsp_connector.py",
        "tools/scripts/fix_hsp_function_blocks.py",
        "tools/scripts/fix_hsp_indentation.py",
        "tools/scripts/fix_import_paths.py",
        "tools/scripts/fix_line110.py",
        "tools/scripts/fix_line312.py",
        "tools/scripts/fix_nlp_agent_comprehensive.py",
        "tools/scripts/fix_nlp_agent_indentation.py",
        "tools/scripts/fix_nlp_agent.py",
        "tools/scripts/fix_project_syntax.py",
        "tools/scripts/fix_raise_syntax.py",
        "tools/scripts/fix_remaining_syntax_errors.py",
        "tools/scripts/fix_specific_file.py",
        "tools/scripts/fix_symbolic_space.py",
        "tools/scripts/fix_syntax_error.py",
        "tools/scripts/fix_syntax_issues.py",
        "tools/scripts/fix_type_issues.py",
        "tools/scripts/fix_unused_call_results_final.py",
        "tools/scripts/fix_unused_call_results.py",
        "tools/scripts/fix_unused_imports.py",
        
        # tools/ 下的脚本
        "tools/fix_import_paths.py",
        
        # apps/backend/scripts/ 下的脚本
        "apps/backend/scripts/fix_executor.py",
        "apps/backend/scripts/fix_import_paths.py",
        
        # apps/backend/tools/fix/ 下的脚本
        "apps/backend/tools/fix/fix_hsp_integration.py",
        "apps/backend/tools/fix/fix_import_path.py",
    ]
    
    archived_count = 0
    
    for script_path in scripts_to_archive,::
        source_path = project_root / script_path
        
        if source_path.exists():::
            # 创建目标路径
            target_path = archive_dir / Path(script_path).name
            
            # 确保目标目录存在
            target_path.parent.mkdir(parents == True, exist_ok == True)
            
            try,
                # 移动文件
                shutil.move(str(source_path), str(target_path))
                logger.info(f"已归档, {script_path}")
                archived_count += 1
            except Exception as e,::
                logger.error(f"归档失败 {script_path} {e}")
        else,
            logger.warning(f"文件不存在, {script_path}")
    
    logger.info(f"\n归档完成！共归档 {archived_count} 个脚本")
    
    # 创建禁用脚本占位符
    placeholder_content = '''#!/usr/bin/env python3
"""
此脚本已被归档,因为它没有范围限制。

原因：该脚本可能会修改下载的内容(如依赖、模型、数据集等),不符合项目本体的修复原则。

请使用具有范围限制的 unified-fix.py 工具进行修复。
"""

print("此脚本已被禁用并归档。")
print("请使用具有范围限制的 unified-fix.py 工具进行修复。")
print("位置：tools/unified-fix.py")
'''
    
    for script_path in scripts_to_archive,::
        source_path = project_root / script_path
        if source_path.exists():::
            # 跳过已移动的文件
            continue
            
        # 创建禁用占位符
        try,
            with open(source_path, 'w', encoding == 'utf-8') as f,
                f.write(placeholder_content)
            logger.info(f"已创建禁用占位符, {script_path}")
        except Exception as e,::
            logger.error(f"创建占位符失败 {script_path} {e}")

if __name"__main__":::
    archive_unrestricted_fix_scripts()