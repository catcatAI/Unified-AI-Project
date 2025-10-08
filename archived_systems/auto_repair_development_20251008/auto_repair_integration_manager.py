#!/usr/bin/env python3
"""
自动修复系统集成管理器
提供统一的接口来管理所有自动修复系统，协调各子系统工作
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import time
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RepairSystemType(Enum):
    """修复系统类型"""
    UNIFIED = "unified"           # 统一自动修复系统（最新最完整）
    COMPLETE = "complete"         # 增强版完整修复系统
    INTELLIGENT = "intelligent"   # 增强版智能修复系统
    SMART_VALIDATOR = "validator" # 智能验证器
    LEGACY = "legacy"             # 遗留系统（归档）

@dataclass
class RepairSystemConfig:
    """修复系统配置"""
    default_system: RepairSystemType = RepairSystemType.UNIFIED
    enable_fallback: bool = True
    max_execution_time: int = 600  # 10分钟
    enable_backup: bool = True
    repair_scope: Dict[str, bool] = None
    
    def __post_init__(self):
        if self.repair_scope is None:
            self.repair_scope = {
                'syntax': True,
                'semantic': True,
                'style': True,
                'performance': False,
                'security': False
            }

class AutoRepairIntegrationManager:
    """自动修复系统集成管理器"""
    
    def __init__(self, config: Optional[RepairSystemConfig] = None):
        self.config = config or RepairSystemConfig()
        self.systems = {}
        self._initialize_systems()
        logger.info("🚀 自动修复系统集成管理器初始化完成")
    
    def _initialize_systems(self):
        """初始化所有可用的修复系统"""
        logger.info("🔧 初始化修复系统...")
        
        # 1. 统一自动修复系统（最新最完整）
        try:
            from unified_auto_repair_system import UnifiedAutoRepairSystem, RepairConfig as UnifiedConfig
            
            unified_config = UnifiedConfig(
                max_workers=4,
                enable_backup=self.config.enable_backup,
                enable_validation=True,
                repair_scope=self.config.repair_scope
            )
            
            self.systems[RepairSystemType.UNIFIED] = {
                'class': UnifiedAutoRepairSystem,
                'config': unified_config,
                'status': 'active',
                'description': '统一自动修复系统 - 最完整版本'
            }
            logger.info("✅ 统一自动修复系统初始化成功")
            
        except ImportError as e:
            logger.warning(f"⚠️ 统一自动修复系统不可用: {e}")
            self.systems[RepairSystemType.UNIFIED] = {
                'status': 'unavailable',
                'error': str(e),
                'description': '统一自动修复系统 - 不可用'
            }
        
        # 2. 增强版完整修复系统
        try:
            from enhanced_complete_repair_system import EnhancedCompleteRepairSystem
            
            self.systems[RepairSystemType.COMPLETE] = {
                'class': EnhancedCompleteRepairSystem,
                'config': {'max_workers': 4},
                'status': 'active',
                'description': '增强版完整修复系统'
            }
            logger.info("✅ 增强版完整修复系统初始化成功")
            
        except ImportError as e:
            logger.warning(f"⚠️ 增强版完整修复系统不可用: {e}")
            self.systems[RepairSystemType.COMPLETE] = {
                'status': 'unavailable',
                'error': str(e),
                'description': '增强版完整修复系统 - 不可用'
            }
        
        # 3. 增强版智能修复系统
        try:
            from enhanced_intelligent_repair_system import EnhancedIntelligentRepairSystem
            
            self.systems[RepairSystemType.INTELLIGENT] = {
                'class': EnhancedIntelligentRepairSystem,
                'config': {},
                'status': 'active',
                'description': '增强版智能修复系统 - AGI Level 3'
            }
            logger.info("✅ 增强版智能修复系统初始化成功")
            
        except ImportError as e:
            logger.warning(f"⚠️ 增强版智能修复系统不可用: {e}")
            self.systems[RepairSystemType.INTELLIGENT] = {
                'status': 'unavailable',
                'error': str(e),
                'description': '增强版智能修复系统 - 不可用'
            }
        
        # 4. 智能验证器
        try:
            from enhanced_smart_repair_validator import EnhancedSmartRepairValidator
            
            self.systems[RepairSystemType.SMART_VALIDATOR] = {
                'class': EnhancedSmartRepairValidator,
                'config': {},
                'status': 'active',
                'description': '智能验证器 - 多层级验证'
            }
            logger.info("✅ 智能验证器初始化成功")
            
        except ImportError as e:
            logger.warning(f"⚠️ 智能验证器不可用: {e}")
            self.systems[RepairSystemType.SMART_VALIDATOR] = {
                'status': 'unavailable',
                'error': str(e),
                'description': '智能验证器 - 不可用'
            }
        
        logger.info("✅ 所有可用修复系统初始化完成")
    
    def run_auto_repair(self, target_path: str = '.', system_type: Optional[RepairSystemType] = None) -> Dict[str, Any]:
        """运行自动修复（统一接口）"""
        logger.info("🔧 启动自动修复集成系统...")
        start_time = time.time()
        
        try:
            # 确定要使用的系统
            selected_system = system_type or self.config.default_system
            
            if selected_system not in self.systems or self.systems[selected_system]['status'] != 'active':
                if self.config.enable_fallback:
                    logger.warning(f"所选系统 {selected_system} 不可用，尝试备用系统")
                    selected_system = self._select_fallback_system()
                else:
                    raise RuntimeError(f"所选系统 {selected_system} 不可用且备用系统已禁用")
            
            logger.info(f"使用修复系统: {selected_system.value}")
            
            # 运行选定的修复系统
            system_info = self.systems[selected_system]
            system_class = system_info['class']
            system_config = system_info['config']
            
            # 实例化并运行
            if selected_system == RepairSystemType.UNIFIED:
                repair_system = system_class(system_config)
                results = repair_system.run_unified_auto_repair(target_path)
            elif selected_system == RepairSystemType.COMPLETE:
                repair_system = system_class(**system_config)
                results = repair_system.run_complete_repair(target_path)
            elif selected_system == RepairSystemType.INTELLIGENT:
                repair_system = system_class()
                results = repair_system.run_enhanced_intelligent_repair(target_path)
            elif selected_system == RepairSystemType.SMART_VALIDATOR:
                # 智能验证器需要特殊处理
                validator = system_class()
                results = self._run_validator_system(validator, target_path)
            else:
                raise ValueError(f"不支持的系统类型: {selected_system}")
            
            # 增强结果信息
            execution_time = time.time() - start_time
            enhanced_results = {
                **results,
                'system_used': selected_system.value,
                'system_description': system_info['description'],
                'integration_manager_version': '2.0',
                'execution_time': execution_time,
                'config_used': {
                    'default_system': self.config.default_system.value,
                    'enable_fallback': self.config.enable_fallback,
                    'enable_backup': self.config.enable_backup,
                    'repair_scope': self.config.repair_scope
                }
            }
            
            logger.info(f"✅ 自动修复完成，使用系统: {selected_system.value}")
            return enhanced_results
            
        except Exception as e:
            logger.error(f"自动修复集成系统执行失败: {e}")
            import traceback
            logger.error(f"详细错误堆栈: {traceback.format_exc()}")
            
            return {
                'status': 'error',
                'error': str(e),
                'error_type': type(e).__name__,
                'system_used': selected_system.value if 'selected_system' in locals() else 'unknown',
                'execution_time': time.time() - start_time,
                'fallback_mode': True,
                'recommendation': '建议检查系统配置和文件权限'
            }
    
    def _select_fallback_system(self) -> RepairSystemType:
        """选择备用系统"""
        # 按优先级选择备用系统
        fallback_order = [
            RepairSystemType.UNIFIED,
            RepairSystemType.COMPLETE,
            RepairSystemType.INTELLIGENT,
            RepairSystemType.SMART_VALIDATOR
        ]
        
        for system_type in fallback_order:
            if (system_type in self.systems and 
                self.systems[system_type]['status'] == 'active'):
                logger.info(f"选择备用系统: {system_type.value}")
                return system_type
        
        raise RuntimeError("没有可用的备用系统")
    
    def _run_validator_system(self, validator, target_path: str) -> Dict[str, Any]:
        """运行验证器系统"""
        logger.info("🔍 运行智能验证器系统...")
        
        # 智能验证器需要特殊处理 - 只进行验证而不修复
        import subprocess
        from pathlib import Path
        
        validation_results = []
        python_files = list(Path(target_path).rglob('*.py'))
        
        for py_file in python_files[:20]:  # 限制文件数量
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                lines = content.split('\n')
                
                # 使用验证器验证
                validation_result = validator.validate_repair_intelligent(
                    original_lines=[],
                    repaired_lines=lines,
                    issue_type='general_validation',
                    confidence=0.5
                )
                
                validation_results.append({
                    'file': str(py_file),
                    'validation_result': validation_result,
                    'overall_success': validation_result.get('overall_success', False)
                })
                
            except Exception as e:
                logger.debug(f"验证文件失败 {py_file}: {e}")
        
        # 生成验证报告
        total_validated = len(validation_results)
        valid_files = sum(1 for r in validation_results if r.get('overall_success'))
        
        return {
            'status': 'completed',
            'validation_results': validation_results,
            'total_validated': total_validated,
            'valid_files': valid_files,
            'invalid_files': total_validated - valid_files,
            'validation_success_rate': (valid_files / max(total_validated, 1)) * 100,
            'report': self._generate_validation_report(validation_results)
        }
    
    def _generate_validation_report(self, validation_results: List[Dict]) -> str:
        """生成验证报告"""
        total = len(validation_results)
        valid = sum(1 for r in validation_results if r.get('overall_success'))
        
        return f"""# 🔍 智能验证器报告

**验证时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**验证文件数**: {total}  
**有效文件**: {valid}  
**无效文件**: {total - valid}  
**验证成功率**: {(valid / max(total, 1)) * 100:.1f}%

**系统**: 智能验证器 - 多层级验证  
**模式**: 只验证不修复  
"""
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        active_systems = []
        unavailable_systems = []
        
        for system_type, info in self.systems.items():
            if info['status'] == 'active':
                active_systems.append({
                    'type': system_type.value,
                    'description': info['description']
                })
            else:
                unavailable_systems.append({
                    'type': system_type.value,
                    'description': info['description'],
                    'error': info.get('error', '未知错误')
                })
        
        return {
            'integration_manager_status': 'active',
            'config': {
                'default_system': self.config.default_system.value,
                'enable_fallback': self.config.enable_fallback,
                'enable_backup': self.config.enable_backup
            },
            'active_systems': active_systems,
            'unavailable_systems': unavailable_systems,
            'total_systems': len(self.systems),
            'available_count': len(active_systems)
        }
    
    def get_repair_system_info(self, system_type: RepairSystemType) -> Dict[str, Any]:
        """获取特定修复系统的信息"""
        if system_type in self.systems:
            info = self.systems[system_type]
            return {
                'type': system_type.value,
                'status': info['status'],
                'description': info['description'],
                'error': info.get('error'),
                'config': info.get('config', {})
            }
        else:
            return {
                'type': system_type.value,
                'status': 'not_found',
                'description': '系统未找到'
            }
    
    def update_system_config(self, new_config: RepairSystemConfig):
        """更新系统配置"""
        old_config = self.config
        self.config = new_config
        
        logger.info(f"系统配置已更新")
        logger.info(f"默认系统: {old_config.default_system.value} -> {new_config.default_system.value}")
        logger.info(f"备用系统: {'启用' if new_config.enable_fallback else '禁用'}")
        
        # 重新初始化系统（如果需要）
        if old_config.repair_scope != new_config.repair_scope:
            logger.info("修复范围配置已变更，重新初始化相关系统")
            self._initialize_systems()

# 全局实例
_auto_repair_manager = None

def get_auto_repair_manager() -> AutoRepairIntegrationManager:
    """获取全局自动修复集成管理器实例"""
    global _auto_repair_manager
    if _auto_repair_manager is None:
        _auto_repair_manager = AutoRepairIntegrationManager()
    return _auto_repair_manager

def run_unified_auto_repair(target_path: str = '.', system_type: Optional[str] = None) -> Dict[str, Any]:
    """运行统一自动修复（全局函数）"""
    manager = get_auto_repair_manager()
    
    if system_type:
        try:
            system_enum = RepairSystemType(system_type)
        except ValueError:
            logger.error(f"未知的系统类型: {system_type}")
            return {
                'status': 'error',
                'error': f'未知的系统类型: {system_type}'
            }
        return manager.run_auto_repair(target_path, system_enum)
    else:
        return manager.run_auto_repair(target_path)

def get_repair_system_status() -> Dict[str, Any]:
    """获取修复系统状态（全局函数）"""
    manager = get_auto_repair_manager()
    return manager.get_system_status()

if __name__ == "__main__":
    print("🚀 测试自动修复系统集成管理器...")
    print("=" * 60)
    
    # 获取管理器实例
    manager = get_auto_repair_manager()
    
    # 获取系统状态
    status = manager.get_system_status()
    
    print(f"系统集成管理器状态: {status['integration_manager_status']}")
    print(f"可用系统数量: {status['available_count']}/{status['total_systems']}")
    print(f"默认系统: {status['config']['default_system']}")
    
    print("\n📊 可用修复系统:")
    for system in status['active_systems']:
        print(f"   ✅ {system['type']}: {system['description']}")
    
    if status['unavailable_systems']:
        print("\n⚠️ 不可用系统:")
        for system in status['unavailable_systems']:
            print(f"   ❌ {system['type']}: {system['description']}")
    
    print("\n🎉 自动修复系统集成管理器测试完成！")
