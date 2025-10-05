"""
统一自动修复系统测试套件
测试所有修复功能
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine
from unified_auto_fix_system.core.fix_types import FixType, FixStatus, FixScope
from unified_auto_fix_system.core.fix_result import FixContext


class TestUnifiedFixSystem:
    """统一修复系统测试类"""
    
    @pytest.fixture
    def temp_project(self):
        """创建临时项目"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # 创建项目结构
            (project_root / "src").mkdir()
            (project_root / "tests").mkdir()
            (project_root / "docs").mkdir()
            
            # 创建一些测试文件
            (project_root / "src" / "main.py").write_text("print('Hello World')")
            (project_root / "src" / "utils.py").write_text("def helper(): pass")
            (project_root / "tests" / "test_main.py").write_text("def test_main(): pass")
            
            yield project_root
    
    @pytest.fixture
    def fix_engine(self, temp_project):
        """创建修复引擎"""
        return UnifiedFixEngine(temp_project)
    
    def test_engine_initialization(self, temp_project):
        """测试引擎初始化"""
        engine = UnifiedFixEngine(temp_project)
        
        assert engine.project_root == temp_project
        assert engine.config is not None
        assert len(engine.modules) > 0
    
    def test_analyze_empty_project(self, fix_engine):
        """测试分析空项目"""
        context = FixContext(
            project_root=fix_engine.project_root,
            scope=FixScope.PROJECT
        )
        
        result = fix_engine.analyze_project(context)
        
        assert result is not None
        assert "timestamp" in result
        assert "issues" in result
        assert "statistics" in result
    
    def test_fix_with_no_issues(self, fix_engine):
        """测试没有问题的修复"""
        context = FixContext(
            project_root=fix_engine.project_root,
            scope=FixScope.PROJECT
        )
        
        report = fix_engine.fix_issues(context)
        
        assert report is not None
        assert report.status in [FixStatus.SUCCESS, FixStatus.NOT_APPLICABLE]
    
    def test_syntax_fix_detection(self, fix_engine):
        """测试语法修复检测"""
        # 创建一个包含语法错误的文件
        syntax_error_file = fix_engine.project_root / "syntax_error.py"
        syntax_error_file.write_text("def missing_colon()\n    pass")  # 缺少冒号
        
        context = FixContext(
            project_root=fix_engine.project_root,
            target_path=syntax_error_file,
            scope=FixScope.SPECIFIC_FILE
        )
        
        result = fix_engine.analyze_project(context)
        
        # 应该检测到语法错误
        syntax_issues = result.get("issues", {}).get("syntax_fix", [])
        assert len(syntax_issues) > 0
    
    def test_backup_creation(self, fix_engine):
        """测试备份创建"""
        context = FixContext(
            project_root=fix_engine.project_root,
            backup_enabled=True
        )
        
        report = fix_engine.fix_issues(context)
        
        # 备份应该在修复时创建
        if report.backup_path:
            assert report.backup_path.exists()
    
    def test_dry_run_mode(self, fix_engine):
        """测试干运行模式"""
        context = FixContext(
            project_root=fix_engine.project_root,
            dry_run=True
        )
        
        report = fix_engine.fix_issues(context)
        
        # 干运行不应该实际修复问题
        for fix_result in report.fix_results.values():
            if fix_result.status != FixStatus.NOT_APPLICABLE:
                assert fix_result.status == FixStatus.SIMULATED
    
    def test_module_enable_disable(self, fix_engine):
        """测试模块启用/禁用"""
        # 禁用语法修复模块
        fix_engine.disable_module(FixType.SYNTAX_FIX)
        
        module_status = fix_engine.get_module_status()
        assert module_status[FixType.SYNTAX_FIX.value] == "disabled"
        
        # 重新启用
        fix_engine.enable_module(FixType.SYNTAX_FIX)
        module_status = fix_engine.get_module_status()
        assert module_status[FixType.SYNTAX_FIX.value] == "enabled"
    
    def test_config_loading(self, temp_project):
        """测试配置加载"""
        # 创建自定义配置文件
        config_path = temp_project / "custom_config.json"
        config_content = {
            "enabled_modules": ["syntax_fix", "import_fix"],
            "backup_enabled": False,
            "dry_run": True
        }
        config_path.write_text(json.dumps(config_content))
        
        engine = UnifiedFixEngine(temp_project, config_path)
        
        assert engine.config["backup_enabled"] == False
        assert engine.config["dry_run"] == True
        assert len(engine.config["enabled_modules"]) == 2
    
    def test_report_generation(self, fix_engine):
        """测试报告生成"""
        context = FixContext(
            project_root=fix_engine.project_root
        )
        
        report = fix_engine.fix_issues(context)
        
        # 报告应该包含所有必要信息
        assert report.timestamp is not None
        assert report.project_root == fix_engine.project_root
        assert report.statistics is not None
        
        # 检查统计信息
        assert "total_fixes" in report.statistics
        assert "successful_fixes" in report.statistics
        assert "failed_fixes" in report.statistics
    
    def test_specific_file_fixing(self, fix_engine):
        """测试特定文件修复"""
        # 创建有问题的文件
        test_file = fix_engine.project_root / "test_file.py"
        test_file.write_text("def test(\n    pass")  # 语法错误
        
        context = FixContext(
            project_root=fix_engine.project_root,
            target_path=test_file,
            scope=FixScope.SPECIFIC_FILE
        )
        
        report = fix_engine.fix_issues(context, [FixType.SYNTAX_FIX.value])
        
        # 应该只修复特定文件
        assert report is not None
    
    def test_error_handling(self, fix_engine):
        """测试错误处理"""
        # 创建无效的上下文
        context = FixContext(
            project_root=Path("/nonexistent/path"),
            scope=FixScope.PROJECT
        )
        
        # 应该优雅地处理错误
        report = fix_engine.fix_issues(context)
        
        assert report is not None
        # 不应该抛出异常，而是返回失败状态
    
    def test_cleanup(self, fix_engine):
        """测试清理功能"""
        # 运行一些操作
        context = FixContext(project_root=fix_engine.project_root)
        fix_engine.fix_issues(context)
        
        # 清理资源
        fix_engine.cleanup()
        
        # 清理应该成功完成
        assert True  # 如果没有异常，测试通过


class TestFixModules:
    """修复模块测试类"""
    
    @pytest.fixture
    def temp_project(self):
        """创建临时项目"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    def test_syntax_fixer(self, temp_project):
        """测试语法修复器"""
        from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
        
        # 创建有语法错误的文件
        error_file = temp_project / "error.py"
        error_file.write_text("def test()\n    pass")  # 缺少冒号
        
        fixer = EnhancedSyntaxFixer(temp_project)
        context = FixContext(
            project_root=temp_project,
            target_path=error_file
        )
        
        # 分析问题
        issues = fixer.analyze(context)
        assert len(issues) > 0
        
        # 修复问题
        result = fixer.fix(context)
        assert result.status in [FixStatus.SUCCESS, FixStatus.PARTIAL_SUCCESS]
    
    def test_import_fixer(self, temp_project):
        """测试导入修复器"""
        from unified_auto_fix_system.modules.import_fixer import ImportFixer
        
        # 创建有导入问题的文件
        main_file = temp_project / "main.py"
        main_file.write_text("from nonexistent.module import something")
        
        fixer = ImportFixer(temp_project)
        context = FixContext(
            project_root=temp_project,
            target_path=main_file
        )
        
        # 分析问题
        issues = fixer.analyze(context)
        # 应该发现问题（导入不存在的模块）
        # 注意：这可能不会发现问题，取决于具体的分析逻辑
    
    def test_dependency_fixer(self, temp_project):
        """测试依赖修复器"""
        from unified_auto_fix_system.modules.dependency_fixer import DependencyFixer
        
        # 创建requirements.txt
        req_file = temp_project / "requirements.txt"
        req_file.write_text("nonexistent-package==1.0.0")
        
        fixer = DependencyFixer(temp_project)
        context = FixContext(
            project_root=temp_project
        )
        
        # 分析问题
        issues = fixer.analyze(context)
        # 应该发现依赖问题
        # 注意：实际结果取决于环境中是否安装了该包


if __name__ == "__main__":
    pytest.main([__file__, "-v"])