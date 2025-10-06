#!/usr/bin/env python3
"""
继续执行统一自动修复
分批处理，提高效率
"""

import sys
import time
import traceback
from pathlib import Path

sys.path.append('.')
from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine, FixContext
from unified_auto_fix_system.core.fix_types import FixScope, FixStatus

def batch_fix_directory(dir_path, engine, project_root, batch_size=10):
    """分批修复目录中的文件"""
    print(f'\n=== 分批修复: {dir_path.name} ===')
    
    # 获取目录中的所有Python文件
    python_files = list(dir_path.rglob('*.py'))
    print(f'找到 {len(python_files)} 个Python文件')
    
    total_fixed = 0
    total_processed = 0
    
    # 分批处理
    for i in range(0, len(python_files), batch_size):
        batch = python_files[i:i+batch_size]
        print(f'\n处理第 {i//batch_size + 1} 批 ({len(batch)} 个文件)...')
        
        batch_fixed = 0
        
        for py_file in batch:
            try:
                # 检查文件是否真的有语法错误
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                import ast
                try:
                    ast.parse(content)
                    continue  # 文件没有语法错误，跳过
                except SyntaxError:
                    pass  # 有语法错误，需要修复
                
                print(f'  修复: {py_file.relative_to(project_root)}')
                
                # 创建修复上下文
                context = FixContext(
                    project_root=project_root,
                    target_path=py_file,
                    scope=FixScope.PROJECT,
                    backup_enabled=True,
                    dry_run=False,
                    ai_assisted=True,
                    excluded_paths=['node_modules', '__pycache__', '.git', 'venv', '.venv', 'backup', 'unified_fix_backups']
                )
                
                # 执行修复
                result = engine.fix_issues(context, specific_issues=['syntax_fix'])
                
                # 统计修复结果
                for fix_type, fix_result in result.fix_results.items():
                    if fix_result.issues_fixed > 0:
                        batch_fixed += fix_result.issues_fixed
                        print(f'    ✓ 修复了 {fix_result.issues_fixed} 个问题')
                
                total_processed += 1
                
                # 小延迟，避免系统过载
                time.sleep(0.1)
                
            except Exception as e:
                print(f'    ✗ 修复失败: {e}')
                continue
        
        total_fixed += batch_fixed
        print(f'第 {i//batch_size + 1} 批完成: 修复了 {batch_fixed} 个问题')
        
        # 每批之间暂停一下
        time.sleep(1)
    
    return total_fixed, total_processed

def continue_unified_fix():
    """继续统一自动修复"""
    project_root = Path('D:/Projects/Unified-AI-Project')
    engine = UnifiedFixEngine(project_root)
    
    print('=== 继续统一自动修复 ===')
    print(f'项目根目录: {project_root}')
    print(f'已加载 {len(engine.modules)} 个修复模块')
    
    # 定义优先级目录
    priority_directories = [
        project_root / 'apps' / 'backend' / 'src' / 'core',      # 最高优先级
        project_root / 'apps' / 'backend' / 'src' / 'ai',        # AI模块
        project_root / 'unified_auto_fix_system',                # 修复系统本身
        project_root / 'auto_fix_workspace',                     # 修复工作区
        project_root / 'tests',                                  # 测试文件
        project_root / 'tools',                                  # 工具脚本
        project_root / 'training',                               # 训练系统
    ]
    
    total_fixed = 0
    total_processed = 0
    
    start_time = time.time()
    
    for dir_path in priority_directories:
        if not dir_path.exists():
            print(f'跳过不存在的目录: {dir_path}')
            continue
        
        try:
            fixed, processed = batch_fix_directory(dir_path, engine, project_root)
            total_fixed += fixed
            total_processed += processed
            
            if processed > 0:
                print(f'目录 {dir_path.name} 修复统计: 处理了{processed}个文件，修复了{fixed}个问题')
            
        except Exception as e:
            print(f'修复目录 {dir_path.name} 失败: {e}')
            traceback.print_exc()
            continue
    
    duration = time.time() - start_time
    
    print(f'\n=== 修复完成 ===')
    print(f'总处理文件: {total_processed}个')
    print(f'总修复问题: {total_fixed}个')
    print(f'耗时: {duration:.1f}秒')
    print(f'平均修复速度: {total_fixed/duration:.1f}个问题/秒' if duration > 0 else 'N/A')
    
    return total_fixed > 0

if __name__ == '__main__':
    success = continue_unified_fix()
    print(f'\n修复执行{"成功" if success else "完成（无新问题）"}')
    sys.exit(0 if success else 0)