#!/usr/bin/env python3
"""
智能修复执行器
执行完整的智能修复流程，包括问题检测、修复、验证和报告生成
"""

import sys
import subprocess
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Literal, Optional

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SmartFixExecutor:
    """智能修复执行器"""
    
    def __init__(self, project_root: Optional[Path] = None) -> None:
        self.project_root = project_root or PROJECT_ROOT
        self.reports_dir = self.project_root / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        
    def run_smart_auto_fix(self) -> bool:
        """运行智能自动修复"""
        logger.info("开始运行智能自动修复...")
        try:
            # 导入并运行智能自动修复工具
            smart_fix_script = self.project_root / "scripts" / "enhanced_auto_fix.py"
            if not smart_fix_script.exists():
                logger.error(f"智能自动修复脚本不存在: {smart_fix_script}")
                return False
                
            result = subprocess.run([
                "python", str(smart_fix_script), "--all"
            ], cwd=self.project_root, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                logger.info("✓ 智能自动修复执行完成")
                return True
            else:
                logger.error(f"✗ 智能自动修复执行失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("✗ 智能自动修复执行超时")
            return False
        except Exception as e:
            logger.error(f"✗ 运行智能自动修复时出错: {e}")
            return False
    
    def run_integration_fixer(self) -> bool:
        """运行集成问题修复器"""
        logger.info("开始运行集成问题修复器...")
        try:
            # 导入并运行集成问题修复工具
            integration_fix_script = self.project_root / "apps" / "backend" / "scripts" / "integration_fixer.py"
            if not integration_fix_script.exists():
                logger.error(f"集成问题修复脚本不存在: {integration_fix_script}")
                return False
                
            result = subprocess.run([
                "python", str(integration_fix_script)
            ], cwd=self.project_root, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                logger.info("✓ 集成问题修复执行完成")
                return True
            else:
                logger.error(f"✗ 集成问题修复执行失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("✗ 集成问题修复执行超时")
            return False
        except Exception as e:
            logger.error(f"✗ 运行集成问题修复时出错: {e}")
            return False
    
    def run_tests(self) -> Dict[str, Any]:
        """运行测试并返回结果"""
        logger.info("开始运行测试...")
        test_results: Dict[str, Any] = {
            "success": False,
            "passed": 0,
            "failed": 0,
            "errors": [],  # type: List[str]
            "output": ""
        }
        
        # 明确指定 errors 列表的类型
        errors_list: List[str] = test_results["errors"]
        
        try:
            # 运行后端测试
            result = subprocess.run([
                "python", "-m", "pytest", 
                "--tb=short", "-v", "--maxfail=5"
            ], cwd=self.project_root / "apps" / "backend", 
            capture_output=True, text=True, timeout=1200)
            
            test_results["output"] = result.stdout
            if result.returncode == 0:
                logger.info("✓ 测试执行完成")
                test_results["success"] = True
                
                # 解析测试结果
                lines = result.stdout.split('\n')
                for line in lines:
                    if "passed" in line and "failed" in line:
                        # 提取通过和失败的测试数量
                        import re
                        passed_match = re.search(r"(\d+) passed", line)
                        failed_match = re.search(r"(\d+) failed", line)
                        if passed_match:
                            test_results["passed"] = int(passed_match.group(1))
                        if failed_match:
                            test_results["failed"] = int(failed_match.group(1))
                        break
            else:
                logger.error("✗ 测试执行失败")
                errors_list.append(result.stderr[-1000:])  # 只保留最后1000个字符
                test_results["errors"] = errors_list
                
        except subprocess.TimeoutExpired:
            logger.error("✗ 测试执行超时")
            errors_list.append("测试执行超时")
            test_results["errors"] = errors_list
        except Exception as e:
            logger.error(f"✗ 运行测试时出错: {e}")
            errors_list.append(str(e))
            test_results["errors"] = errors_list
            
        return test_results
    
    def generate_execution_report(self, test_results: Dict[str, Any]) -> str:
        """生成执行报告"""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "test_results": test_results,
            "summary": {
                "total_tests": test_results["passed"] + test_results["failed"],
                "passed_tests": test_results["passed"],
                "failed_tests": test_results["failed"],
                "success_rate": 0 if (test_results["passed"] + test_results["failed"]) == 0 else 
                               test_results["passed"] / (test_results["passed"] + test_results["failed"]) * 100
            }
        }
        
        # 保存报告
        report_file = self.reports_dir / f"smart_fix_execution_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"执行报告已保存到: {report_file}")
        return str(report_file)
    
    def execute_complete_fix_process(self) -> bool:
        """执行完整的修复流程"""
        logger.info("=== 开始执行完整的智能修复流程 ===")
        
        # 1. 运行智能自动修复
        print("\n1. 运行智能自动修复...")
        if not self.run_smart_auto_fix():
            logger.error("智能自动修复执行失败")
            return False
            
        # 2. 运行集成问题修复
        print("\n2. 运行集成问题修复...")
        if not self.run_integration_fixer():
            logger.error("集成问题修复执行失败")
            return False
            
        # 3. 运行测试验证
        print("\n3. 运行测试验证...")
        test_results = self.run_tests()
        
        # 4. 生成执行报告
        print("\n4. 生成执行报告...")
        report_file = self.generate_execution_report(test_results)
        
        # 5. 显示结果摘要
        print("\n=== 执行结果摘要 ===")
        print(f"测试总数: {test_results['passed'] + test_results['failed']}")
        print(f"通过测试: {test_results['passed']}")
        print(f"失败测试: {test_results['failed']}")
        if test_results['passed'] + test_results['failed'] > 0:
            success_rate = test_results['passed'] / (test_results['passed'] + test_results['failed']) * 100
            print(f"成功率: {success_rate:.2f}%")
        print(f"执行报告: {report_file}")
        
        if test_results["success"]:
            print("✓ 所有测试通过，修复成功完成")
            return True
        else:
            print("✗ 部分测试失败，请检查错误信息")
            return False

def main() -> Literal[0, 1]:
    """主函数"""
    print("=== 智能修复执行器 ===")
    
    # 创建执行器
    executor = SmartFixExecutor()
    
    # 执行完整修复流程
    success = executor.execute_complete_fix_process()
    
    if success:
        print("\n🎉 智能修复流程执行成功完成!")
        return 0
    else:
        print("\n❌ 智能修复流程执行失败，请查看详细日志")
        return 1

if __name__ == "__main__":
    sys.exit(main())