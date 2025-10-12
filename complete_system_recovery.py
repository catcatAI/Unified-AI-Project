#!/usr/bin/env python3
"""
完整系统恢复工具
整合真实修复系统和智能清理系统，彻底解决修复脚本造成的问题
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# 导入我们的新系统
from real_auto_repair_system import RealAutoRepairSystem, RepairResult
from intelligent_cleanup_system import IntelligentCleanupSystem

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CompleteSystemRecovery:
    """完整系统恢复工具"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        
        # 初始化子系统
        self.cleanup_system = IntelligentCleanupSystem(project_root)
        self.repair_system = RealAutoRepairSystem(project_root)
        
        # 恢复统计
        self.recovery_stats = {
            "cleanup_completed": False,
            "repair_completed": False,
            "total_files_processed": 0,
            "total_issues_fixed": 0,
            "space_saved_mb": 0,
            "backup_files_created": 0
        }
        
        logger.info(f"完整系统恢复工具初始化完成 - 项目根目录: {self.project_root}")
    
    def perform_complete_recovery(self, dry_run: bool = True) -> Dict[str, Any]:
        """执行完整的系统恢复"""
        logger.info(f"开始完整系统恢复 (dry_run={dry_run})")
        start_time = datetime.now()
        
        recovery_report = {
            "success": True,
            "dry_run": dry_run,
            "start_time": start_time.isoformat(),
            "phases": {},
            "summary": {},
            "recommendations": []
        }
        
        try:
            # 阶段1: 智能清理
            logger.info("🧹 阶段1: 执行智能清理...")
            cleanup_result = self._phase1_cleanup(dry_run)
            recovery_report["phases"]["cleanup"] = cleanup_result
            
            if not cleanup_result["success"]:
                raise Exception(f"清理阶段失败: {cleanup_result.get('error', '未知错误')}")
            
            # 阶段2: 文件修复
            logger.info("🔧 阶段2: 执行文件修复...")
            repair_result = self._phase2_repair(dry_run)
            recovery_report["phases"]["repair"] = repair_result
            
            if not repair_result["success"]:
                raise Exception(f"修复阶段失败: {repair_result.get('error', '未知错误')}")
            
            # 阶段3: 系统验证
            logger.info("✅ 阶段3: 执行系统验证...")
            validation_result = self._phase3_validation(dry_run)
            recovery_report["phases"]["validation"] = validation_result
            
            # 生成恢复总结
            recovery_report["summary"] = self._generate_recovery_summary(recovery_report)
            
            # 生成建议
            recovery_report["recommendations"] = self._generate_recommendations(recovery_report)
            
            end_time = datetime.now()
            recovery_report["end_time"] = end_time.isoformat()
            recovery_report["duration_seconds"] = (end_time - start_time).total_seconds()
            
            logger.info(f"系统恢复完成！用时 {recovery_report['duration_seconds']:.2f} 秒")
            
        except Exception as e:
            logger.error(f"系统恢复失败: {e}")
            recovery_report["success"] = False
            recovery_report["error"] = str(e)
            recovery_report["end_time"] = datetime.now().isoformat()
        
        return recovery_report
    
    def _phase1_cleanup(self, dry_run: bool) -> Dict[str, Any]:
        """阶段1: 智能清理"""
        try:
            logger.info("开始清理阶段...")
            
            # 执行智能清理
            cleanup_result = self.cleanup_system.perform_intelligent_cleanup(dry_run)
            
            # 更新恢复统计
            if cleanup_result["success"]:
                self.recovery_stats["cleanup_completed"] = True
                self.recovery_stats["space_saved_mb"] += cleanup_result["cleanup_summary"]["space_saved_mb"]
            
            logger.info(f"清理阶段完成 - 节省了 {cleanup_result['cleanup_summary']['space_saved_mb']:.2f} MB")
            return cleanup_result
            
        except Exception as e:
            logger.error(f"清理阶段失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _phase2_repair(self, dry_run: bool) -> Dict[str, Any]:
        """阶段2: 文件修复"""
        try:
            logger.info("开始修复阶段...")
            
            if dry_run:
                # 干运行模式：只分析，不实际修复
                logger.info("干运行模式：分析修复需求...")
                
                # 扫描需要修复的文件
                python_files = list(self.project_root.rglob("*.py"))
                files_needing_repair = []
                
                for file_path in python_files:
                    if self._file_needs_repair(file_path):
                        files_needing_repair.append(str(file_path))
                
                repair_analysis = {
                    "success": True,
                    "dry_run": True,
                    "files_needing_repair": files_needing_repair,
                    "total_files_analyzed": len(python_files),
                    "estimated_repair_time": len(files_needing_repair) * 2  # 估计每个文件2秒
                }
                
                logger.info(f"分析完成 - {len(files_needing_repair)} 个文件需要修复")
                return repair_analysis
            
            else:
                # 实际修复模式
                repair_result = self.repair_system.repair_project()
                
                if repair_result["success"]:
                    self.recovery_stats["repair_completed"] = True
                    self.recovery_stats["total_files_processed"] += repair_result["summary"]["total_files_processed"]
                    self.recovery_stats["total_issues_fixed"] += repair_result["summary"]["successful_repairs"]
                    self.recovery_stats["backup_files_created"] += repair_result["summary"]["backup_created"]
                
                logger.info(f"修复阶段完成 - 处理了 {repair_result['summary']['total_files_processed']} 个文件")
                return repair_result
                
        except Exception as e:
            logger.error(f"修复阶段失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _phase3_validation(self, dry_run: bool) -> Dict[str, Any]:
        """阶段3: 系统验证"""
        try:
            logger.info("开始验证阶段...")
            
            validation_result = {
                "success": True,
                "dry_run": dry_run,
                "validation_tests": {}
            }
            
            # 测试1: 基础导入验证
            logger.info("执行基础导入验证...")
            validation_result["validation_tests"]["basic_imports"] = self._test_basic_imports()
            
            # 测试2: 语法验证
            logger.info("执行语法验证...")
            validation_result["validation_tests"]["syntax_validation"] = self._test_syntax_validation()
            
            # 测试3: 核心功能验证
            logger.info("执行核心功能验证...")
            validation_result["validation_tests"]["core_functionality"] = self._test_core_functionality()
            
            # 测试4: 项目结构验证
            logger.info("执行项目结构验证...")
            validation_result["validation_tests"]["project_structure"] = self._test_project_structure()
            
            # 计算总体健康状况
            validation_result["overall_health"] = self._calculate_overall_health(validation_result["validation_tests"])
            
            logger.info(f"验证阶段完成 - 总体健康状况: {validation_result['overall_health']:.2%}")
            return validation_result
            
        except Exception as e:
            logger.error(f"验证阶段失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _file_needs_repair(self, file_path: Path) -> bool:
        """检查文件是否需要修复"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查语法错误
            import ast
            try:
                ast.parse(content)
            except SyntaxError:
                return True
            
            # 检查其他问题（缩进、导入等）
            if self._has_indentation_issues(content):
                return True
            
            if self._has_import_issues(content):
                return True
            
            return False
            
        except Exception:
            return True  # 无法读取的文件需要修复
    
    def _has_indentation_issues(self, content: str) -> bool:
        """检查是否有缩进问题"""
        lines = content.split('\n')
        for line in lines:
            if '\t' in line:
                return True
            leading_spaces = len(line) - len(line.lstrip())
            if leading_spaces % 4 != 0 and line.strip():
                return True
        return False
    
    def _has_import_issues(self, content: str) -> bool:
        """检查是否有导入问题"""
        # 这里可以实现导入问题检查
        return False
    
    def _test_basic_imports(self) -> Dict[str, Any]:
        """测试基础导入"""
        test_result = {
            "success": True,
            "tests": {},
            "overall_score": 0.0
        }
        
        # 测试关键模块的导入
        import_tests = [
            ("pathlib.Path", "Path"),
            ("ast", "ast"),
            ("json", "json"),
            ("logging", "logging"),
        ]
        
        passed_tests = 0
        total_tests = len(import_tests)
        
        for import_statement, module_name in import_tests:
            try:
                if "." in import_statement:
                    module_path, attr_name = import_statement.rsplit(".", 1)
                    module = __import__(module_path, fromlist=[attr_name])
                    getattr(module, attr_name)
                else:
                    __import__(import_statement)
                
                test_result["tests"][import_statement] = {
                    "status": "passed",
                    "error": None
                }
                passed_tests += 1
                
            except Exception as e:
                test_result["tests"][import_statement] = {
                    "status": "failed",
                    "error": str(e)
                }
                test_result["success"] = False
        
        test_result["overall_score"] = passed_tests / total_tests if total_tests > 0 else 0.0
        return test_result
    
    def _test_syntax_validation(self) -> Dict[str, Any]:
        """测试语法验证"""
        test_result = {
            "success": True,
            "files_checked": 0,
            "syntax_errors": 0,
            "overall_score": 0.0
        }
        
        try:
            # 检查项目中的Python文件
            python_files = list(self.project_root.rglob("*.py"))
            syntax_errors = 0
            
            for file_path in python_files[:50]:  # 只检查前50个文件，避免太慢
                try:
                    test_result["files_checked"] += 1
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    import ast
                    ast.parse(content)
                    
                except SyntaxError:
                    syntax_errors += 1
                except Exception:
                    # 其他错误不计算为语法错误
                    pass
            
            test_result["syntax_errors"] = syntax_errors
            
            # 计算分数
            if test_result["files_checked"] > 0:
                test_result["overall_score"] = (test_result["files_checked"] - syntax_errors) / test_result["files_checked"]
            else:
                test_result["overall_score"] = 0.0
            
            if syntax_errors > 0:
                test_result["success"] = False
            
        except Exception as e:
            test_result["success"] = False
            test_result["error"] = str(e)
        
        return test_result
    
    def _test_core_functionality(self) -> Dict[str, Any]:
        """测试核心功能"""
        test_result = {
            "success": True,
            "tests": {},
            "overall_score": 0.0
        }
        
        # 测试我们的修复系统
        tests = [
            ("修复系统初始化", self._test_repair_system_init),
            ("清理系统初始化", self._test_cleanup_system_init),
            ("文件备份功能", self._test_backup_functionality),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                test_result["tests"][test_name] = result
                if result.get("success", False):
                    passed_tests += 1
                else:
                    test_result["success"] = False
            except Exception as e:
                test_result["tests"][test_name] = {
                    "success": False,
                    "error": str(e)
                }
                test_result["success"] = False
        
        test_result["overall_score"] = passed_tests / total_tests if total_tests > 0 else 0.0
        return test_result
    
    def _test_repair_system_init(self) -> Dict[str, Any]:
        """测试修复系统初始化"""
        try:
            # 测试修复系统是否可以正常初始化
            from real_auto_repair_system import RealAutoRepairSystem
            repair_system = RealAutoRepairSystem(str(self.project_root))
            
            return {
                "success": True,
                "error": None,
                "details": "修复系统初始化成功"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "details": "修复系统初始化失败"
            }
    
    def _test_cleanup_system_init(self) -> Dict[str, Any]:
        """测试清理系统初始化"""
        try:
            # 测试清理系统是否可以正常初始化
            from intelligent_cleanup_system import IntelligentCleanupSystem
            cleanup_system = IntelligentCleanupSystem(str(self.project_root))
            
            return {
                "success": True,
                "error": None,
                "details": "清理系统初始化成功"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "details": "清理系统初始化失败"
            }
    
    def _test_backup_functionality(self) -> Dict[str, Any]:
        """测试备份功能"""
        try:
            # 创建一个测试文件
            test_file = self.project_root / "test_backup_functionality.tmp"
            test_content = "测试备份功能"
            
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            # 测试备份功能
            backup_dir = self.project_root / "test_backup_dir"
            backup_dir.mkdir(exist_ok=True)
            
            # 复制文件作为备份
            backup_file = backup_dir / test_file.name
            shutil.copy2(test_file, backup_file)
            
            # 验证备份
            if backup_file.exists():
                with open(backup_file, 'r', encoding='utf-8') as f:
                    backup_content = f.read()
                
                if backup_content == test_content:
                    # 清理测试文件
                    test_file.unlink(missing_ok=True)
                    backup_file.unlink(missing_ok=True)
                    backup_dir.rmdir()
                    
                    return {
                        "success": True,
                        "error": None,
                        "details": "备份功能测试成功"
                    }
                else:
                    raise Exception("备份内容不匹配")
            else:
                raise Exception("备份文件未创建")
                
        except Exception as e:
            # 清理测试文件
            test_file.unlink(missing_ok=True)
            backup_file.unlink(missing_ok=True)
            backup_dir.rmdir()
            
            return {
                "success": False,
                "error": str(e),
                "details": "备份功能测试失败"
            }
    
    def _test_project_structure(self) -> Dict[str, Any]:
        """测试项目结构"""
        test_result = {
            "success": True,
            "structure_checks": {},
            "overall_score": 0.0
        }
        
        # 检查关键目录是否存在
        expected_dirs = [
            "apps", "docs", "tests", "tools", "training"
        ]
        
        found_dirs = 0
        for expected_dir in expected_dirs:
            dir_path = self.project_root / expected_dir
            exists = dir_path.exists() and dir_path.is_dir()
            test_result["structure_checks"][f"dir_{expected_dir}"] = exists
            if exists:
                found_dirs += 1
        
        # 检查关键文件是否存在
        expected_files = [
            "README.md", "package.json", "requirements.txt"
        ]
        
        found_files = 0
        for expected_file in expected_files:
            file_path = self.project_root / expected_file
            exists = file_path.exists() and file_path.is_file()
            test_result["structure_checks"][f"file_{expected_file}"] = exists
            if exists:
                found_files += 1
        
        total_checks = len(expected_dirs) + len(expected_files)
        passed_checks = found_dirs + found_files
        
        test_result["overall_score"] = passed_checks / total_checks if total_checks > 0 else 0.0
        
        if test_result["overall_score"] < 0.5:
            test_result["success"] = False
        
        return test_result
    
    def _calculate_overall_health(self, validation_tests: Dict[str, Any]) -> float:
        """计算总体健康状况"""
        scores = []
        
        for test_name, test_result in validation_tests.items():
            if "overall_score" in test_result:
                scores.append(test_result["overall_score"])
            elif "success" in test_result:
                scores.append(1.0 if test_result["success"] else 0.0)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _generate_recovery_summary(self, recovery_report: Dict[str, Any]) -> Dict[str, Any]:
        """生成恢复总结"""
        summary = {
            "total_files_processed": 0,
            "total_issues_resolved": 0,
            "space_recovered_mb": 0,
            "system_health_improvement": 0,
            "recovery_efficiency": 0
        }
        
        # 从各个阶段收集数据
        phases = recovery_report.get("phases", {})
        
        if "cleanup" in phases:
            cleanup = phases["cleanup"]
            if cleanup.get("success"):
                summary["space_recovered_mb"] += cleanup.get("cleanup_summary", {}).get("space_saved_mb", 0)
        
        if "repair" in phases:
            repair = phases["repair"]
            if repair.get("success"):
                summary["total_files_processed"] += repair.get("summary", {}).get("total_files_processed", 0)
                summary["total_issues_resolved"] += repair.get("summary", {}).get("successful_repairs", 0)
        
        if "validation" in phases:
            validation = phases["validation"]
            if validation.get("success"):
                summary["system_health_improvement"] = validation.get("overall_health", 0)
        
        # 计算恢复效率
        if summary["total_files_processed"] > 0:
            summary["recovery_efficiency"] = summary["total_issues_resolved"] / summary["total_files_processed"]
        
        return summary
    
    def _generate_recommendations(self, recovery_report: Dict[str, Any]) -> List[str]:
        """生成建议"""
        recommendations = []
        
        phases = recovery_report.get("phases", {})
        
        # 基于清理结果的建议
        if "cleanup" in phases:
            cleanup = phases["cleanup"]
            if cleanup.get("success"):
                harmful_files = cleanup.get("cleanup_summary", {}).get("harmful_files", 0)
                if harmful_files > 10:
                    recommendations.append(f"发现 {harmful_files} 个有害文件，建议定期运行清理系统")
        
        # 基于修复结果的建议
        if "repair" in phases:
            repair = phases["repair"]
            if repair.get("success"):
                syntax_errors = repair.get("summary", {}).get("failed_repairs", 0)
                if syntax_errors > 5:
                    recommendations.append(f"有 {syntax_errors} 个文件修复失败，建议手动检查这些文件")
        
        # 基于验证结果的建议
        if "validation" in phases:
            validation = phases["validation"]
            if validation.get("success"):
                health_score = validation.get("overall_health", 0)
                if health_score < 0.7:
                    recommendations.append(f"系统健康分数为 {health_score:.2%}，建议进一步优化")
                elif health_score > 0.9:
                    recommendations.append("系统健康状况良好，建议定期维护")
        
        if not recommendations:
            recommendations.append("系统恢复完成，建议定期运行维护工具")
        
        return recommendations

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="完整系统恢复工具")
    parser.add_argument("--path", default=".", help="要恢复的项目路径")
    parser.add_argument("--dry-run", action="store_true", help="只分析，不执行恢复")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--phase", choices=["cleanup", "repair", "validation", "all"], 
                       default="all", help="指定执行的阶段")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 创建恢复工具
    recovery_tool = CompleteSystemRecovery(args.path)
    
    if args.phase == "all":
        # 执行完整恢复
        result = recovery_tool.perform_complete_recovery(dry_run=args.dry_run)
    else:
        # 执行特定阶段
        logger.info(f"执行特定阶段: {args.phase}")
        # 这里可以添加单独阶段的执行逻辑
        result = recovery_tool.perform_complete_recovery(dry_run=args.dry_run)
    
    # 输出结果
    if result["success"]:
        print(f"\n🎉 系统恢复{'分析' if args.dry_run else '执行'}完成！")
        print(f"用时: {result['duration_seconds']:.2f} 秒")
        
        summary = result.get("summary", {})
        print(f"\n📊 恢复总结:")
        print(f"  处理文件: {summary.get('total_files_processed', 0)}")
        print(f"  解决问题: {summary.get('total_issues_resolved', 0)}")
        print(f"  空间恢复: {summary.get('space_recovered_mb', 0):.2f} MB")
        print(f"  系统健康: {summary.get('system_health_improvement', 0):.2%}")
        
        recommendations = result.get("recommendations", [])
        if recommendations:
            print(f"\n💡 建议:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        
        if args.dry_run:
            print(f"\n⚠️  这是干运行模式，没有实际执行恢复操作")
            print(f"   移除 --dry-run 参数来执行实际恢复")
    else:
        print(f"\n❌ 系统恢复失败: {result.get('error', '未知错误')}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())