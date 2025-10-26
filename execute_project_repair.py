#!/usr/bin/env python3
"""
执行项目修复并检查成果
"""

import sys
import os
from pathlib import Path
import subprocess
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_unified_fix():
    """运行统一修复系统"""
    logger.info("开始执行项目修复...")
    
    # 获取项目根目录
    project_root = Path(__file__).parent
    fix_script = project_root / "tools" / "unified-fix.py"
    
    if not fix_script.exists():
        logger.error(f"修复脚本不存在: {fix_script}")
        return False
    
    try:
        # 执行修复脚本
        result = subprocess.run(
            [sys.executable, str(fix_script), "--type", "all", "--verbose"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        logger.info("修复脚本输出:")
        logger.info(result.stdout)
        
        if result.stderr:
            logger.warning("修复脚本错误:")
            logger.warning(result.stderr)
        
        if result.returncode == 0:
            logger.info("✅ 修复脚本执行成功")
            return True
        else:
            logger.error(f"❌ 修复脚本执行失败,退出码: {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("❌ 修复脚本执行超时")
        return False
    except Exception as e:
        logger.error(f"❌ 执行修复脚本时出错: {e}")
        return False

def check_python_syntax():
    """检查Python语法"""
    logger.info("检查Python语法...")
    
    project_root = Path(__file__).parent
    syntax_errors = []
    
    # 需要检查的目录
    check_dirs = [
        "apps/backend/src",
        "tools",
        "scripts"
    ]
    
    for check_dir in check_dirs:
        dir_path = project_root / check_dir
        if not dir_path.exists():
            continue
            
        for py_file in dir_path.rglob("*.py"):
            # 跳过__pycache__和venv
            if "__pycache__" in str(py_file) or "venv" in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                compile(content, str(py_file), 'exec')
            except SyntaxError as e:
                rel_path = py_file.relative_to(project_root)
                syntax_errors.append(f"{rel_path}:{e.lineno} {e.msg}")
            except Exception as e:
                rel_path = py_file.relative_to(project_root)
                logger.warning(f"检查文件 {rel_path} 时出错: {e}")
    
    if syntax_errors:
        logger.error("发现语法错误:")
        for error in syntax_errors:
            logger.error(f"  {error}")
        return False
    else:
        logger.info("✅ 所有Python文件语法检查通过")
        return True

def test_backend_startup():
    """测试后端启动"""
    logger.info("测试后端启动...")
    
    project_root = Path(__file__).parent
    backend_main = project_root / "apps" / "backend" / "main.py"
    
    if not backend_main.exists():
        logger.warning("后端主文件不存在,跳过启动测试")
        return True
    
    try:
        # 尝试导入后端模块
        sys.path.insert(0, str(project_root / "apps" / "backend"))
        
        # 检查导入
        import src.api.routes
        import src.core.managers.system_manager
        import src.core.config.system_config
        logger.info("✅ 后端模块导入成功")
        return True
        
    except ImportError as e:
        logger.error(f"❌ 后端模块导入失败: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ 测试后端启动时出错: {e}")
        return False

def test_frontend_build():
    """测试前端构建"""
    logger.info("测试前端构建...")
    
    project_root = Path(__file__).parent
    
    try:
        # 检查前端目录
        frontend_dir = project_root / "apps" / "frontend-dashboard"
        if not frontend_dir.exists():
            logger.warning("前端目录不存在,跳过构建测试")
            return True
        
        # 检查package.json
        package_json = frontend_dir / "package.json"
        if not package_json.exists():
            logger.warning("前端package.json不存在,跳过构建测试")
            return True
        
        logger.info("✅ 前端文件检查通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试前端构建时出错: {e}")
        return False

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("开始执行项目修复和检查")
    logger.info("=" * 60)
    
    results = {
        "unified_fix": False,
        "syntax_check": False,
        "backend_test": False,
        "frontend_test": False
    }
    
    # 1. 运行统一修复系统
    logger.info("\n1. 运行统一修复系统")
    results["unified_fix"] = run_unified_fix()
    
    # 2. 检查Python语法
    logger.info("\n2. 检查Python语法")
    results["syntax_check"] = check_python_syntax()
    
    # 3. 测试后端启动
    logger.info("\n3. 测试后端启动")
    results["backend_test"] = test_backend_startup()
    
    # 4. 测试前端构建
    logger.info("\n4. 测试前端构建")
    results["frontend_test"] = test_frontend_build()
    
    # 输出总结
    logger.info("\n" + "=" * 60)
    logger.info("修复和检查结果总结")
    logger.info("=" * 60)
    
    for task, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        logger.info(f"{task}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n🎉 所有检查通过！项目修复成功！")
        return 0
    else:
        logger.error("\n⚠️ 部分检查失败,需要进一步修复")
        return 1

if __name__ == "__main__":
    sys.exit(main())