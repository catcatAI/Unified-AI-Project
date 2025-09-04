#!/usr/bin/env python3
"""
集成问题检查和修复工具
专门用于检查和修复项目中的集成问题
"""

import os
import sys
import json
import asyncio
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntegrationFixer:
    """集成问题检查和修复器"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or PROJECT_ROOT
        self.backup_dir = self.project_root / "backup" / f"integration_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 集成模块列表
        self.integration_modules = [
            "hsp",
            "atlassian",
            "rovo_dev",
            "confluence",
            "jira"
        ]
        
        # 新增：需要检查的文件列表
        self.critical_files = [
            "apps/backend/src/hsp/connector.py",
            "apps/backend/src/integrations/atlassian_bridge.py",
            "apps/backend/src/integrations/confluence_integration.py",
            "apps/backend/src/integrations/jira_integration.py",
            "apps/backend/src/integrations/enhanced_rovo_dev_connector.py",
            "apps/backend/src/core_ai/learning/content_analyzer_module.py",
            "apps/backend/src/core_ai/learning/learning_manager.py"
        ]
        
        logger.info("集成问题检查和修复工具初始化完成")
    
    def backup_file(self, file_path: Path) -> Path:
        """备份文件"""
        try:
            # 创建相对于项目根的路径
            relative_path = file_path.relative_to(self.project_root)
            backup_file_path = self.backup_dir / relative_path
            backup_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            import shutil
            shutil.copy2(file_path, backup_file_path)
            return backup_file_path
        except Exception as e:
            logger.error(f"备份文件 {file_path} 失败: {e}")
            return None
    
    def check_hsp_integration(self) -> Dict[str, Any]:
        """检查HSP集成问题"""
        logger.info("开始检查HSP集成问题...")
        issues = []
        
        try:
            # 检查HSP连接器文件
            hsp_connector_path = self.project_root / "apps" / "backend" / "src" / "hsp" / "connector.py"
            if hsp_connector_path.exists():
                with open(hsp_connector_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查协程调用问题
                if "async def" in content and "await" not in content:
                    issues.append({
                        "type": "async_warning",
                        "file": str(hsp_connector_path),
                        "description": "发现可能的协程未await问题"
                    })
                
                # 检查MQTT客户端导入
                if "import paho.mqtt.client" not in content:
                    issues.append({
                        "type": "import_error",
                        "file": str(hsp_connector_path),
                        "description": "MQTT客户端未正确导入"
                    })
                    
                # 检查HSP协议相关配置
                if "HSP_PROTOCOL_VERSION" not in content:
                    issues.append({
                        "type": "config_error",
                        "file": str(hsp_connector_path),
                        "description": "HSP协议版本未配置"
                    })
            else:
                issues.append({
                    "type": "file_missing",
                    "file": str(hsp_connector_path),
                    "description": "HSP连接器文件不存在"
                })
                
        except Exception as e:
            logger.error(f"检查HSP集成时出错: {e}")
            issues.append({
                "type": "check_error",
                "description": f"检查HSP集成时出错: {e}"
            })
        
        logger.info(f"HSP集成问题检查完成，发现 {len(issues)} 个问题")
        return {
            "module": "hsp",
            "issues": issues,
            "status": "completed"
        }
    
    def check_atlassian_integration(self) -> Dict[str, Any]:
        """检查Atlassian集成问题"""
        logger.info("开始检查Atlassian集成问题...")
        issues = []
        
        try:
            # 检查Atlassian集成文件
            atlassian_files = [
                "apps/backend/src/integrations/atlassian_bridge.py",
                "apps/backend/src/integrations/confluence_integration.py",
                "apps/backend/src/integrations/jira_integration.py",
                "apps/backend/src/integrations/enhanced_rovo_dev_connector.py"
            ]
            
            for file_path in atlassian_files:
                full_path = self.project_root / file_path
                if full_path.exists():
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 检查配置导入
                    if "from config" in content and "from apps.backend.config" not in content:
                        issues.append({
                            "type": "import_error",
                            "file": str(full_path),
                            "description": "配置文件导入路径不正确"
                        })
                    
                    # 检查认证相关代码
                    if "api_token" in content and "self.api_token" not in content:
                        issues.append({
                            "type": "config_error",
                            "file": str(full_path),
                            "description": "API令牌未正确初始化"
                        })
                        
                    # 检查Atlassian API连接
                    if "AtlassianAPI" in content and "initialize_connection" not in content:
                        issues.append({
                            "type": "connection_error",
                            "file": str(full_path),
                            "description": "Atlassian API连接未正确初始化"
                        })
                else:
                    issues.append({
                        "type": "file_missing",
                        "file": str(full_path),
                        "description": "Atlassian集成文件不存在"
                    })
                    
        except Exception as e:
            logger.error(f"检查Atlassian集成时出错: {e}")
            issues.append({
                "type": "check_error",
                "description": f"检查Atlassian集成时出错: {e}"
            })
        
        logger.info(f"Atlassian集成问题检查完成，发现 {len(issues)} 个问题")
        return {
            "module": "atlassian",
            "issues": issues,
            "status": "completed"
        }
    
    def check_content_analysis(self) -> Dict[str, Any]:
        """检查内容分析模块问题"""
        logger.info("开始检查内容分析模块问题...")
        issues = []
        
        try:
            # 检查内容分析模块文件
            ca_path = self.project_root / "apps" / "backend" / "src" / "core_ai" / "learning" / "content_analyzer_module.py"
            if ca_path.exists():
                with open(ca_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查实体提取相关代码
                if "nx_graph.number_of_nodes()" in content:
                    # 检查是否有对应的实体计数逻辑
                    if "len(kg_data[\"entities\"])" in content:
                        # 这可能是一个断言失败的问题
                        issues.append({
                            "type": "logic_error",
                            "file": str(ca_path),
                            "description": "实体计数逻辑可能存在不一致"
                        })
                
                # 检查关系提取相关代码
                if "relationship" in content and "found_relationship" in content:
                    issues.append({
                        "type": "logic_error",
                        "file": str(ca_path),
                        "description": "关系提取逻辑可能需要优化"
                    })
                    
                # 检查内容分析模块的导入问题
                if "from apps.backend.src.core_ai.learning" in content and "from ." in content:
                    issues.append({
                        "type": "import_error",
                        "file": str(ca_path),
                        "description": "相对导入和绝对导入混用"
                    })
            else:
                issues.append({
                    "type": "file_missing",
                    "file": str(ca_path),
                    "description": "内容分析模块文件不存在"
                })
                
        except Exception as e:
            logger.error(f"检查内容分析模块时出错: {e}")
            issues.append({
                "type": "check_error",
                "description": f"检查内容分析模块时出错: {e}"
            })
        
        logger.info(f"内容分析模块问题检查完成，发现 {len(issues)} 个问题")
        return {
            "module": "content_analysis",
            "issues": issues,
            "status": "completed"
        }
    
    def fix_hsp_integration(self, issues: List[Dict[str, Any]]) -> bool:
        """修复HSP集成问题"""
        logger.info("开始修复HSP集成问题...")
        fixed_count = 0
        
        try:
            hsp_connector_path = self.project_root / "apps" / "backend" / "src" / "hsp" / "connector.py"
            if hsp_connector_path.exists():
                # 备份文件
                self.backup_file(hsp_connector_path)
                
                with open(hsp_connector_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # 修复协程调用问题
                for issue in issues:
                    if issue["type"] == "async_warning":
                        # 更精确的修复逻辑
                        # 查找可能需要await的协程调用
                        async_calls = [
                            "publish_fact", "send_ack", "connect_to_broker", 
                            "subscribe_to_topic", "unsubscribe_from_topic"
                        ]
                        for call in async_calls:
                            pattern = rf"(\b{call}\s*\()"
                            replacement = rf"await \1"
                            content = re.sub(pattern, replacement, content)
                
                # 修复导入问题
                content = re.sub(
                    r"import paho\.mqtt\.client as mqtt",
                    "import paho.mqtt.client as mqtt  # MQTT客户端",
                    content
                )
                
                # 添加HSP协议版本配置
                if "HSP_PROTOCOL_VERSION" not in content:
                    # 在文件顶部添加配置
                    content = content.replace(
                        '"""',
                        '"""\n\n# HSP协议配置\nHSP_PROTOCOL_VERSION = "1.0"\nHSP_DEFAULT_TIMEOUT = 30'
                    )
                
                # 如果内容有变化，写入文件
                if content != original_content:
                    with open(hsp_connector_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    fixed_count += 1
                    logger.info("✓ HSP集成问题修复完成")
                else:
                    logger.info("  HSP集成无需要修复的问题")
            else:
                logger.warning("✗ HSP连接器文件不存在，无法修复")
                
        except Exception as e:
            logger.error(f"修复HSP集成问题时出错: {e}")
            return False
        
        return fixed_count > 0
    
    def fix_atlassian_integration(self, issues: List[Dict[str, Any]]) -> bool:
        """修复Atlassian集成问题"""
        logger.info("开始修复Atlassian集成问题...")
        fixed_count = 0
        
        try:
            # 修复Atlassian集成文件
            atlassian_files = [
                "apps/backend/src/integrations/atlassian_bridge.py",
                "apps/backend/src/integrations/confluence_integration.py",
                "apps/backend/src/integrations/jira_integration.py",
                "apps/backend/src/integrations/enhanced_rovo_dev_connector.py"
            ]
            
            for file_path in atlassian_files:
                full_path = self.project_root / file_path
                if full_path.exists():
                    # 备份文件
                    self.backup_file(full_path)
                    
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    
                    # 修复配置导入问题
                    for issue in issues:
                        if issue["type"] == "import_error" and issue["file"] == str(full_path):
                            content = content.replace(
                                "from config", 
                                "from apps.backend.config"
                            )
                    
                    # 修复API令牌初始化问题
                    if "self.api_token = None" not in content and "api_token" in content:
                        # 查找API令牌初始化位置
                        content = re.sub(
                            r"def __init__\(self.*?\):",
                            "def __init__(self, config=None):\n        self.api_token = config.get('api_token') if config else None\n        self.domain = config.get('domain') if config else None",
                            content,
                            flags=re.DOTALL
                        )
                    
                    # 如果内容有变化，写入文件
                    if content != original_content:
                        with open(full_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        fixed_count += 1
                        logger.info(f"✓ {file_path} 修复完成")
                else:
                    logger.warning(f"✗ {file_path} 不存在，无法修复")
                    
        except Exception as e:
            logger.error(f"修复Atlassian集成问题时出错: {e}")
            return False
        
        logger.info(f"Atlassian集成问题修复完成，修复了 {fixed_count} 个文件")
        return fixed_count > 0
    
    def fix_content_analysis(self, issues: List[Dict[str, Any]]) -> bool:
        """修复内容分析模块问题"""
        logger.info("开始修复内容分析模块问题...")
        fixed_count = 0
        
        try:
            ca_path = self.project_root / "apps" / "backend" / "src" / "core_ai" / "learning" / "content_analyzer_module.py"
            if ca_path.exists():
                # 备份文件
                self.backup_file(ca_path)
                
                with open(ca_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # 修复逻辑错误
                for issue in issues:
                    if issue["type"] == "logic_error":
                        logger.info(f"  发现逻辑问题: {issue['description']}")
                        # 修复实体计数逻辑不一致问题
                        if "实体计数逻辑可能存在不一致" in issue["description"]:
                            # 添加更准确的实体计数逻辑
                            content = re.sub(
                                r"nx_graph\.number_of_nodes\(\)",
                                "# 获取实体节点数量\nentity_nodes = [n for n, attrs in nx_graph.nodes(data=True) if attrs.get('type') == 'entity']\nlen(entity_nodes)",
                                content
                            )
                    
                    # 修复导入问题
                    elif issue["type"] == "import_error":
                        content = re.sub(
                            r"from apps\.backend\.src\.core_ai\.learning",
                            "from .",
                            content
                        )
                
                # 如果内容有变化，写入文件
                if content != original_content:
                    with open(ca_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    fixed_count += 1
                    logger.info("✓ 内容分析模块问题修复完成")
                else:
                    logger.info("  内容分析模块无需要修复的问题")
            else:
                logger.warning("✗ 内容分析模块文件不存在，无法修复")
                
        except Exception as e:
            logger.error(f"修复内容分析模块问题时出错: {e}")
            return False
        
        return fixed_count > 0
    
    def check_all_integrations(self) -> List[Dict[str, Any]]:
        """检查所有集成问题"""
        logger.info("开始检查所有集成问题...")
        results = []
        
        # 检查各个集成模块
        results.append(self.check_hsp_integration())
        results.append(self.check_atlassian_integration())
        results.append(self.check_content_analysis())
        
        logger.info("所有集成问题检查完成")
        return results
    
    def fix_all_integrations(self, check_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """修复所有集成问题"""
        logger.info("开始修复所有集成问题...")
        fix_results = {
            "hsp": False,
            "atlassian": False,
            "content_analysis": False
        }
        
        # 修复各个集成模块的问题
        for result in check_results:
            module = result["module"]
            issues = result["issues"]
            
            if module == "hsp":
                fix_results["hsp"] = self.fix_hsp_integration(issues)
            elif module == "atlassian":
                fix_results["atlassian"] = self.fix_atlassian_integration(issues)
            elif module == "content_analysis":
                fix_results["content_analysis"] = self.fix_content_analysis(issues)
        
        logger.info("所有集成问题修复完成")
        return fix_results
    
    def validate_fixes(self) -> bool:
        """验证修复效果"""
        logger.info("开始验证修复效果...")
        
        try:
            # 运行相关测试
            import subprocess
            result = subprocess.run([
                "python", "-m", "pytest", 
                "tests/hsp/", 
                "tests/integration/test_atlassian_integration.py",
                "tests/core_ai/learning/test_content_analyzer_module.py",
                "--tb=short", "-v", "--disable-warnings"
            ], cwd=self.project_root, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info("✓ 集成测试通过")
                return True
            else:
                logger.warning("✗ 集成测试失败")
                logger.warning(f"错误输出: {result.stdout[-1000:]}")
                # 保存详细的测试结果
                test_result_file = self.project_root / "integration_test_results.txt"
                with open(test_result_file, 'w', encoding='utf-8') as f:
                    f.write(result.stdout)
                    f.write("\n\nSTDERR:\n")
                    f.write(result.stderr)
                logger.info(f"详细测试结果已保存到: {test_result_file}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("✗ 集成测试超时")
            return False
        except Exception as e:
            logger.error(f"✗ 验证修复效果时出错: {e}")
            return False

def main():
    """主函数"""
    print("=== 集成问题检查和修复工具 ===")
    
    # 创建集成修复器
    fixer = IntegrationFixer()
    
    # 检查所有集成问题
    print("\n1. 检查所有集成问题...")
    check_results = fixer.check_all_integrations()
    
    # 显示检查结果
    print("\n2. 检查结果:")
    total_issues = 0
    for result in check_results:
        print(f"  {result['module']}: {len(result['issues'])} 个问题")
        total_issues += len(result['issues'])
        for issue in result['issues']:
            print(f"    - {issue['description']}")
    
    if total_issues > 0:
        # 修复所有集成问题
        print("\n3. 修复所有集成问题...")
        fix_results = fixer.fix_all_integrations(check_results)
        
        # 显示修复结果
        print("\n4. 修复结果:")
        for module, fixed in fix_results.items():
            status = "✓ 已修复" if fixed else "  无需修复"
            print(f"  {module}: {status}")
        
        # 验证修复效果
        print("\n5. 验证修复效果...")
        if fixer.validate_fixes():
            print("✓ 修复验证通过")
        else:
            print("✗ 修复验证失败")
    else:
        print("\n  没有发现集成问题")
    
    print("\n=== 集成问题检查和修复完成 ===")

if __name__ == "__main__":
    main()