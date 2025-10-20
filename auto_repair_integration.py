#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自動修復系統整合腳本
將新開發的修復腳本功能整合到現有的自動修復系統中

使用方法:
    python auto_repair_integration.py [--check] [--fix] [--backup] [--verbose]
"""

import os
import sys
import time
import json
import shutil
import logging
import argparse
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from enum import Enum, auto
from datetime import datetime

# 確保腳本可以在任何目錄執行
if not os.path.exists('repair_scripts'):
    os.makedirs('repair_scripts', exist_ok=True)

if not os.path.exists('auto_fix_workspace'):
    os.makedirs('auto_fix_workspace', exist_ok=True)
    
if not os.path.exists('auto_fix_workspace/scripts'):
    os.makedirs('auto_fix_workspace/scripts', exist_ok=True)

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('auto_repair_integration')

# 項目根目錄
PROJECT_ROOT = Path(__file__).resolve().parent

# 修復腳本目錄
REPAIR_SCRIPTS_DIR = PROJECT_ROOT / 'repair_scripts'
if not REPAIR_SCRIPTS_DIR.exists():
    REPAIR_SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"創建修復腳本目錄: {REPAIR_SCRIPTS_DIR}")

# 自動修復系統目錄
AUTO_REPAIR_DIR = PROJECT_ROOT / 'auto_fix_workspace' / 'scripts'
if not AUTO_REPAIR_DIR.exists():
    AUTO_REPAIR_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"創建自動修復系統目錄: {AUTO_REPAIR_DIR}")

# 修復類型枚舉
class RepairType(Enum):
    SYNTAX = auto()
    STRUCTURE = auto()
    PATH = auto()
    DUPLICATE = auto()
    IMPLEMENTATION = auto()
    CONFIG = auto()
    VALIDATION = auto()

# 修復腳本映射
REPAIR_SCRIPTS = {
    RepairType.SYNTAX: 'syntax_repair.py',
    RepairType.STRUCTURE: 'structure_repair.py',
    RepairType.PATH: 'path_repair.py',
    RepairType.DUPLICATE: 'duplicate_fix.py',
    RepairType.IMPLEMENTATION: 'implementation_fix.py',
    RepairType.CONFIG: 'config_repair.py',
    RepairType.VALIDATION: 'quick_validate.py'
}

# 自動修復系統腳本
AUTO_REPAIR_SCRIPTS = {
    'unified_auto_fix.py': '統一自動修復腳本',
    'interactive_auto_fix_system.py': '交互式自動修復系統',
    'auto_repair_integration_manager.py': '自動修復集成管理器'
}

def parse_args():
    """解析命令行參數"""
    parser = argparse.ArgumentParser(description='自動修復系統整合工具')
    parser.add_argument('--check', action='store_true', help='只檢查問題，不修復')
    parser.add_argument('--fix', action='store_true', help='修復發現的問題')
    parser.add_argument('--backup', action='store_true', help='修復前備份文件')
    parser.add_argument('--verbose', action='store_true', help='顯示詳細日誌')
    
    args = parser.parse_args()
    
    # 如果沒有指定--check或--fix，默認為--check
    if not (args.check or args.fix):
        args.check = True
    
    return args

def setup_logging(verbose):
    """設置日誌級別"""
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

def backup_file(file_path):
    """備份文件"""
    if not os.path.exists(file_path):
        return False
    
    backup_dir = PROJECT_ROOT / 'backups' / datetime.now().strftime('%Y%m%d_%H%M%S')
    os.makedirs(backup_dir, exist_ok=True)
    
    rel_path = os.path.relpath(file_path, PROJECT_ROOT)
    backup_path = backup_dir / rel_path
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    
    shutil.copy2(file_path, backup_path)
    logger.debug(f"已備份文件: {file_path} -> {backup_path}")
    return True

def check_repair_scripts():
    """檢查修復腳本是否存在"""
    missing_scripts = []
    
    for repair_type, script_name in REPAIR_SCRIPTS.items():
        script_path = REPAIR_SCRIPTS_DIR / script_name
        if not os.path.exists(script_path):
            missing_scripts.append((repair_type, script_name))
    
    return missing_scripts

def check_auto_repair_system():
    """檢查自動修復系統是否存在"""
    missing_scripts = []
    
    for script_name in AUTO_REPAIR_SCRIPTS:
        script_path = AUTO_REPAIR_DIR / script_name
        if not os.path.exists(script_path):
            missing_scripts.append(script_name)
    
    return missing_scripts

def create_integration_module():
    """創建整合模塊"""
    integration_dir = AUTO_REPAIR_DIR / 'integrated_fixes'
    os.makedirs(integration_dir, exist_ok=True)
    
    # 創建 __init__.py
    init_path = integration_dir / '__init__.py'
    if not os.path.exists(init_path):
        with open(init_path, 'w', encoding='utf-8') as f:
            f.write('"""整合修復模塊"""')
    
    # 為每種修復類型創建整合模塊
    for repair_type, script_name in REPAIR_SCRIPTS.items():
        source_path = REPAIR_SCRIPTS_DIR / script_name
        if not os.path.exists(source_path):
            logger.warning(f"修復腳本不存在: {script_name}")
            continue
        
        # 創建整合模塊
        module_name = f"{repair_type.name.lower()}_fix.py"
        target_path = integration_dir / module_name
        
        with open(source_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修改導入路徑
        content = content.replace('PROJECT_ROOT = Path(__file__).resolve().parent.parent', 
                                 'PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent')
        
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"已創建整合模塊: {module_name}")
    
    return integration_dir

def update_unified_auto_fix(integration_dir, backup=False):
    """更新統一自動修復腳本"""
    unified_fix_path = AUTO_REPAIR_DIR / 'unified_auto_fix.py'
    
    if not os.path.exists(unified_fix_path):
        logger.error(f"統一自動修復腳本不存在: {unified_fix_path}")
        return False
    
    if backup:
        backup_file(unified_fix_path)
    
    # 讀取原始文件
    with open(unified_fix_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 添加新的修復類型
    if 'class FixType(Enum):' in content:
        new_fix_types = """class FixType(Enum):
    SYNTAX = auto()
    IMPORT = auto()
    PATH = auto()
    STRUCTURE = auto()
    DUPLICATE = auto()
    IMPLEMENTATION = auto()
    CONFIG = auto()
    VALIDATION = auto()
"""
        content = content.replace('class FixType(Enum):', new_fix_types)
    
    # 添加新的修復引擎導入
    import_section = """# 導入整合修復模塊
from integrated_fixes.syntax_fix import SyntaxRepair
from integrated_fixes.path_fix import PathRepair
from integrated_fixes.structure_fix import StructureRepair
from integrated_fixes.duplicate_fix import DuplicateFix
from integrated_fixes.implementation_fix import ImplementationFix
from integrated_fixes.config_fix import ConfigRepair
"""
    
    if 'import time' in content and import_section not in content:
        content = content.replace('import time', 'import time\n' + import_section)
    
    # 添加新的修復引擎初始化
    if 'self.fix_engine = FixEngine(' in content:
        engine_init = """        self.fix_engine = FixEngine(
            fixes={
                FixType.SYNTAX: SyntaxRepair(),
                FixType.IMPORT: ImportFixer(),
                FixType.PATH: PathRepair(),
                FixType.STRUCTURE: StructureRepair(),
                FixType.DUPLICATE: DuplicateFix(),
                FixType.IMPLEMENTATION: ImplementationFix(),
                FixType.CONFIG: ConfigRepair(),
            },
            operation_mode=self.operation_mode
        )
"""
        content = content.replace('self.fix_engine = FixEngine(', engine_init)
    
    # 寫入更新後的文件
    with open(unified_fix_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"已更新統一自動修復腳本: {unified_fix_path}")
    return True

def update_auto_repair_manager(backup=False):
    """更新自動修復集成管理器"""
    manager_path = AUTO_REPAIR_DIR / 'auto_repair_integration_manager.py'
    
    if not os.path.exists(manager_path):
        logger.error(f"自動修復集成管理器不存在: {manager_path}")
        return False
    
    if backup:
        backup_file(manager_path)
    
    # 讀取原始文件
    with open(manager_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 添加新的修復系統類型
    if 'class RepairSystemType(Enum):' in content:
        new_system_types = """class RepairSystemType(Enum):
    UNIFIED = "unified"
    COMPLETE = "complete"
    ENHANCED = "enhanced"
    INTEGRATED = "integrated"
"""
        content = content.replace('class RepairSystemType(Enum):', new_system_types)
    
    # 添加新的修復系統導入
    import_section = """# 導入整合修復系統
from integrated_fixes.syntax_fix import SyntaxRepair
from integrated_fixes.path_fix import PathRepair
from integrated_fixes.structure_fix import StructureRepair
from integrated_fixes.duplicate_fix import DuplicateFix
from integrated_fixes.implementation_fix import ImplementationFix
from integrated_fixes.config_fix import ConfigRepair
"""
    
    if 'import time' in content and import_section not in content:
        content = content.replace('import time', 'import time\n' + import_section)
    
    # 添加新的修復系統配置
    if 'self.systems = {' in content:
        systems_config = """        self.systems = {
            RepairSystemType.UNIFIED: {
                'class': UnifiedAutoRepairSystem,
                'config': self.config.unified_config,
                'status': 'active'
            },
            RepairSystemType.COMPLETE: {
                'class': CompleteAutoRepairSystem,
                'config': self.config.complete_config,
                'status': 'active'
            },
            RepairSystemType.ENHANCED: {
                'class': EnhancedAutoRepairSystem,
                'config': self.config.enhanced_config,
                'status': 'active'
            },
            RepairSystemType.INTEGRATED: {
                'class': IntegratedAutoRepairSystem,
                'config': self.config.integrated_config,
                'status': 'active'
            }
        }
"""
        content = content.replace('self.systems = {', systems_config)
    
    # 添加新的修復系統類
    integrated_system_class = """
class IntegratedAutoRepairSystem:
    """整合自動修復系統"""
    
    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.syntax_repair = SyntaxRepair()
        self.path_repair = PathRepair()
        self.structure_repair = StructureRepair()
        self.duplicate_fix = DuplicateFix()
        self.implementation_fix = ImplementationFix()
        self.config_repair = ConfigRepair()
    
    def run_unified_auto_repair(self, target_path: str = '.') -> Dict[str, Any]:
        """運行整合自動修復"""
        logger.info("🔧 啟動整合自動修復系統...")
        start_time = time.time()
        
        results = {
            'status': 'success',
            'start_time': start_time,
            'end_time': None,
            'duration': None,
            'repairs': []
        }
        
        try:
            # 1. 語法錯誤修復
            logger.info("1️⃣ 執行語法錯誤修復...")
            syntax_result = self.syntax_repair.run_repair(target_path)
            results['repairs'].append({
                'type': 'syntax',
                'status': 'success' if syntax_result else 'failed',
                'details': syntax_result
            })
            
            # 2. 路徑計算問題修復
            logger.info("2️⃣ 執行路徑計算問題修復...")
            path_result = self.path_repair.run_repair(target_path)
            results['repairs'].append({
                'type': 'path',
                'status': 'success' if path_result else 'failed',
                'details': path_result
            })
            
            # 3. 文件結構修復
            logger.info("3️⃣ 執行文件結構修復...")
            structure_result = self.structure_repair.run_repair(target_path)
            results['repairs'].append({
                'type': 'structure',
                'status': 'success' if structure_result else 'failed',
                'details': structure_result
            })
            
            # 4. 重複開發問題修復
            logger.info("4️⃣ 執行重複開發問題修復...")
            duplicate_result = self.duplicate_fix.run_repair(target_path)
            results['repairs'].append({
                'type': 'duplicate',
                'status': 'success' if duplicate_result else 'failed',
                'details': duplicate_result
            })
            
            # 5. 未實作功能修復
            logger.info("5️⃣ 執行未實作功能修復...")
            implementation_result = self.implementation_fix.run_repair(target_path)
            results['repairs'].append({
                'type': 'implementation',
                'status': 'success' if implementation_result else 'failed',
                'details': implementation_result
            })
            
            # 6. 配置文件修復
            logger.info("6️⃣ 執行配置文件修復...")
            config_result = self.config_repair.run_repair(target_path)
            results['repairs'].append({
                'type': 'config',
                'status': 'success' if config_result else 'failed',
                'details': config_result
            })
            
            # 計算總修復時間
            end_time = time.time()
            results['end_time'] = end_time
            results['duration'] = end_time - start_time
            
            logger.info(f"✅ 整合自動修復完成，耗時 {results['duration']:.2f} 秒")
            return results
            
        except Exception as e:
            logger.error(f"❌ 整合自動修復失敗: {e}")
            results['status'] = 'error'
            results['error'] = str(e)
            
            # 計算總修復時間
            end_time = time.time()
            results['end_time'] = end_time
            results['duration'] = end_time - start_time
            
            return results
"""
    
    if integrated_system_class not in content:
        content += integrated_system_class
    
    # 寫入更新後的文件
    with open(manager_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"已更新自動修復集成管理器: {manager_path}")
    return True

def create_run_integrated_repair_script():
    """創建運行整合修復腳本"""
    script_path = PROJECT_ROOT / 'run_integrated_repair.bat'
    
    content = """@echo off
echo 開始執行整合修復...
cd /d "%~dp0"
python auto_repair_integration.py --fix --backup --verbose
echo 修復完成！
pause
"""
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"已創建運行整合修復腳本: {script_path}")
    return True

def main():
    """主函數"""
    args = parse_args()
    setup_logging(args.verbose)
    
    logger.info("開始整合自動修復系統...")
    
    # 檢查修復腳本
    missing_repair_scripts = check_repair_scripts()
    if missing_repair_scripts:
        logger.warning(f"缺少 {len(missing_repair_scripts)} 個修復腳本:")
        for repair_type, script_name in missing_repair_scripts:
            logger.warning(f"  - {repair_type.name}: {script_name}")
    else:
        logger.info("所有修復腳本都已存在")
    
    # 檢查自動修復系統
    missing_auto_repair_scripts = check_auto_repair_system()
    if missing_auto_repair_scripts:
        logger.warning(f"缺少 {len(missing_auto_repair_scripts)} 個自動修復系統腳本:")
        for script_name in missing_auto_repair_scripts:
            logger.warning(f"  - {script_name}")
    else:
        logger.info("所有自動修復系統腳本都已存在")
    
    if args.fix:
        # 創建整合模塊
        integration_dir = create_integration_module()
        
        # 更新統一自動修復腳本
        update_unified_auto_fix(integration_dir, backup=args.backup)
        
        # 更新自動修復集成管理器
        update_auto_repair_manager(backup=args.backup)
        
        # 創建運行整合修復腳本
        create_run_integrated_repair_script()
        
        logger.info("整合自動修復系統完成")
    else:
        logger.info("僅執行了檢查模式，沒有進行任何修改")
        logger.info("使用 --fix 參數來執行整合")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())