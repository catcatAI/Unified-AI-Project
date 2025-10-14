#!/usr/bin/env python3
"""
项目完整性检查脚本
验证所有组件的导入、依赖关系和实现完整性
"""

import os
import sys
import logging
import importlib
import traceback
from pathlib import Path
from typing import Dict, List, Any, Tuple

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "apps" / "backend"))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProjectIntegrityChecker:
    """项目完整性检查器"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.success_count = 0
        self.total_checks = 0
        
    def check_import(self, module_name: str, description: str = "") -> bool:
        """检查模块导入"""
        self.total_checks += 1
        try:
            importlib.import_module(module_name)
            logger.info(f"✅ {module_name} - {description}")
            self.success_count += 1
            return True
        except ImportError as e:
            error_msg = f"❌ {module_name} - {description}: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False
        except Exception as e:
            error_msg = f"⚠️ {module_name} - {description}: {e}"
            logger.warning(error_msg)
            self.warnings.append(error_msg)
            return False
    
    def check_file_exists(self, file_path: str, description: str = "") -> bool:
        """检查文件是否存在"""
        self.total_checks += 1
        full_path = project_root / file_path
        if full_path.exists():
            logger.info(f"✅ {file_path} - {description}")
            self.success_count += 1
            return True
        else:
            error_msg = f"❌ {file_path} - {description}: 文件不存在"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False
    
    def check_directory_structure(self):
        """检查目录结构"""
        logger.info("=== 检查目录结构 ===")
        
        directories = [
            ("apps", "应用目录"),
            ("apps/backend", "后端应用"),
            ("apps/frontend-dashboard", "前端仪表板"),
            ("apps/desktop-app", "桌面应用"),
            ("packages", "共享包"),
            ("docs", "文档目录"),
            ("tests", "测试目录"),
            ("tools", "工具目录"),
            ("scripts", "脚本目录"),
            ("training", "训练系统"),
        ]
        
        for directory, description in directories:
            self.check_file_exists(directory, description)
    
    def check_core_modules(self):
        """检查核心模块"""
        logger.info("=== 检查核心模块 ===")
        
        modules = [
            ("apps.backend.main", "后端主入口"),
            ("apps.backend.src.api.routes", "API路由"),
            ("apps.backend.src.core.config.system_config", "系统配置"),
            ("apps.backend.src.ai.ops.ai_ops_engine", "AI运维引擎"),
            ("apps.backend.src.ai.ops.predictive_maintenance", "预测性维护"),
            ("apps.backend.src.ai.ops.performance_optimizer", "性能优化器"),
            ("apps.backend.src.ai.ops.capacity_planner", "容量规划器"),
            ("apps.backend.src.ai.ops.intelligent_ops_manager", "智能运维管理器"),
        ]
        
        for module, description in modules:
            self.check_import(module, description)
    
    def check_agent_modules(self):
        """检查AI代理模块"""
        logger.info("=== 检查AI代理模块 ===")
        
        agents = [
            ("apps.backend.src.ai.agents.base_agent", "基础代理"),
            ("apps.backend.src.ai.agents.creative_writing_agent", "创意写作代理"),
            ("apps.backend.src.ai.agents.web_search_agent", "网络搜索代理"),
            ("apps.backend.src.ai.agents.code_understanding_agent", "代码理解代理"),
            ("apps.backend.src.ai.agents.data_analysis_agent", "数据分析代理"),
        ]
        
        for agent, description in agents:
            self.check_import(agent, description)
    
    def check_memory_system(self):
        """检查记忆系统"""
        logger.info("=== 检查记忆系统 ===")
        
        memory_modules = [
            ("apps.backend.src.ai.memory.ham_memory_manager", "HAM记忆管理器"),
            ("apps.backend.src.ai.memory.deep_mapper", "深度映射器"),
        ]
        
        for module, description in memory_modules:
            self.check_import(module, description)
    
    def check_hsp_protocol(self):
        """检查HSP协议"""
        logger.info("=== 检查HSP协议 ===")
        
        hsp_modules = [
            ("apps.backend.src.core.hsp.bridge.message_bridge", "消息桥接"),
        ]
        
        for module, description in hsp_modules:
            self.check_import(module, description)
    
    def check_training_system(self):
        """检查训练系统"""
        logger.info("=== 检查训练系统 ===")
        
        training_files = [
            ("training/train_model.py", "主训练脚本"),
            ("training/auto_training_manager.py", "自动训练管理器"),
            ("training/collaborative_training_manager.py", "协作训练管理器"),
            ("training/incremental_learning_manager.py", "增量学习管理器"),
        ]
        
        for file_path, description in training_files:
            self.check_file_exists(file_path, description)
    
    def check_configuration_files(self):
        """检查配置文件"""
        logger.info("=== 检查配置文件 ===")
        
        config_files = [
            ("apps/backend/requirements.txt", "Python依赖"),
            ("apps/backend/requirements-dev.txt", "开发依赖"),
            ("package.json", "Node.js配置"),
            ("pnpm-workspace.yaml", "工作区配置"),
            (".gitignore", "Git忽略文件"),
        ]
        
        for file_path, description in config_files:
            self.check_file_exists(file_path, description)
    
    def check_documentation(self):
        """检查文档"""
        logger.info("=== 检查文档 ===")
        
        doc_files = [
            ("README.md", "项目主文档"),
            ("LOCAL_EXECUTION_GUIDE.md", "本地执行指南"),
            ("FINAL_DELIVERY_REPORT.md", "最终交付报告"),
            ("DATA_SOURCE_ANALYSIS.md", "数据源分析"),
        ]
        
        for file_path, description in doc_files:
            self.check_file_exists(file_path, description)
    
    def check_test_coverage(self):
        """检查测试覆盖"""
        logger.info("=== 检查测试覆盖 ===")
        
        test_files = [
            ("tests/unit/test_ai_ops_complete.py", "AI运维系统测试"),
        ]
        
        for file_path, description in test_files:
            self.check_file_exists(file_path, description)
    
    def simulate_code_execution(self):
        """模拟代码执行"""
        logger.info("=== 模拟代码执行 ===")
        
        try:
            # 尝试导入并实例化核心组件
            from apps.backend.src.core.config.system_config import get_system_config
            config = get_system_config()
            logger.info("✅ 系统配置加载成功")
            self.success_count += 1
            
            # 检查AI运维引擎初始化
            from apps.backend.src.ai.ops.ai_ops_engine import AIOpsEngine
            ai_ops = AIOpsEngine(config.get('ai_ops', {}))
            logger.info("✅ AI运维引擎实例化成功")
            self.success_count += 1
            
            # 检查基础代理
            from apps.backend.src.ai.agents.base_agent import BaseAgent
            logger.info("✅ 基础代理类导入成功")
            self.success_count += 1
            
        except Exception as e:
            error_msg = f"❌ 模拟执行失败: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            traceback.print_exc()
        
        self.total_checks += 3
    
    def run_all_checks(self) -> Dict[str, Any]:
        """运行所有检查"""
        logger.info("开始项目完整性检查...")
        
        self.check_directory_structure()
        self.check_core_modules()
        self.check_agent_modules()
        self.check_memory_system()
        self.check_hsp_protocol()
        self.check_training_system()
        self.check_configuration_files()
        self.check_documentation()
        self.check_test_coverage()
        self.simulate_code_execution()
        
        # 计算结果
        success_rate = (self.success_count / self.total_checks) * 100 if self.total_checks > 0 else 0
        
        result = {
            "total_checks": self.total_checks,
            "success_count": self.success_count,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "success_rate": success_rate,
            "errors": self.errors,
            "warnings": self.warnings
        }
        
        return result
    
    def print_summary(self, result: Dict[str, Any]):
        """打印检查摘要"""
        logger.info("=== 检查摘要 ===")
        logger.info(f"总检查项: {result['total_checks']}")
        logger.info(f"成功: {result['success_count']}")
        logger.info(f"错误: {result['error_count']}")
        logger.info(f"警告: {result['warning_count']}")
        logger.info(f"成功率: {result['success_rate']:.2f}%")
        
        if result['errors']:
            logger.error("\n错误详情:")
            for error in result['errors']:
                logger.error(f"  - {error}")
        
        if result['warnings']:
            logger.warning("\n警告详情:")
            for warning in result['warnings']:
                logger.warning(f"  - {warning}")
        
        # 评估项目状态
        if result['success_rate'] >= 95:
            logger.info("🎉 项目状态: 优秀 - 可以安全运行")
        elif result['success_rate'] >= 85:
            logger.info("✅ 项目状态: 良好 - 基本可以运行")
        elif result['success_rate'] >= 70:
            logger.warning("⚠️ 项目状态: 一般 - 需要修复一些问题")
        else:
            logger.error("❌ 项目状态: 较差 - 需要重大修复")

def main():
    """主函数"""
    checker = ProjectIntegrityChecker()
    result = checker.run_all_checks()
    checker.print_summary(result)
    
    # 返回适当的退出码
    if result['success_rate'] >= 85:
        sys.exit(0)  # 成功
    else:
        sys.exit(1)  # 失败

if __name__ == "__main__":
    main()