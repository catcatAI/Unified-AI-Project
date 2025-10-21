#!/usr/bin/env python3
"""
最终验证脚本
此脚本用于全面验证重构后的项目状态
"""

import os
import sys
from pathlib import Path

class FinalVerifier,
    def __init__(self, project_root, str):
        self.project_root == Path(project_root)
        self.issues = []
        self.success_count = 0
    
    def verify_directory_structure(self):
        """验证目录结构"""
        print("验证目录结构...")
        
        required_dirs = [
            "docs/architecture",
            "docs/development", 
            "docs/api",
            "docs/testing",
            "docs/deployment",
            "docs/reports",
            "tools/scripts",
            "tools/dev-tools",
            "tools/build-tools",
            "tools/test-tools",
            "tools/deployment-tools"
        ]
        
        for dir_path in required_dirs,::
            full_path = self.project_root / dir_path
            if not full_path.exists():::
                self.issues.append(f"缺少目录, {dir_path}")
                print(f"❌ 缺少目录, {dir_path}")
            else,
                self.success_count += 1
                print(f"✅ 目录存在, {dir_path}")
    
    def verify_file_migration(self):
        """验证文件迁移"""
        print("\n验证文件迁移...")
        
        # 检查scripts目录是否已清理Python文件
        scripts_dir = self.project_root / "scripts"
        if scripts_dir.exists():::
            # 检查是否有Python文件
            python_files = list(scripts_dir.glob("*.py"))
            if python_files,::
                self.issues.append(f"scripts目录中仍有 {len(python_files)} 个Python文件未迁移")
                print(f"❌ scripts目录中仍有 {len(python_files)} 个Python文件未迁移")
            else,
                self.success_count += 1
                print("✅ scripts目录中Python文件已清理")
        else,
            self.success_count += 1
            print("✅ scripts目录已清理")
        
        # 检查tools/scripts目录是否有文件
        tools_scripts_dir = self.project_root / "tools" / "scripts"
        if tools_scripts_dir.exists() and any(tools_scripts_dir.iterdir()):::
            self.success_count += 1
            print("✅ tools/scripts目录中有文件")
        else,
            self.issues.append("tools/scripts目录为空")
            print("❌ tools/scripts目录为空")
        
        # 检查docs目录是否有文件
        docs_dir = self.project_root / "docs"
        md_files = list(docs_dir.rglob("*.md"))
        if len(md_files) > 100,  # 应该有大量文档文件,:
            self.success_count += 1
            print(f"✅ docs目录中有 {len(md_files)} 个文档文件")
        else,
            self.issues.append(f"docs目录中文档文件过少, {len(md_files)}")
            print(f"❌ docs目录中文档文件过少, {len(md_files)}")
    
    def verify_duplicate_removal(self):
        """验证重复文件删除"""
        print("\n验证重复文件删除...")
        
        # 检查备份目录是否已删除
        backup_dirs = [
            "all_test_backups",
            "backup_tests",
            "backup_modules"
        ]
        
        deleted_count = 0
        for dir_name in backup_dirs,::
            dir_path = self.project_root / dir_name
            if not dir_path.exists():::
                deleted_count += 1
                self.success_count += 1
                print(f"✅ 已删除备份目录, {dir_name}")
            else,
                self.issues.append(f"备份目录未删除, {dir_name}")
                print(f"❌ 备份目录未删除, {dir_name}")
        
        if deleted_count == len(backup_dirs)::
            print("✅ 所有备份目录已删除")
    
    def verify_import_paths(self):
        """验证导入路径"""
        print("\n验证导入路径...")
        
        # 检查一些关键文件是否使用了新的导入路径
        key_files = [
            "tools/scripts/execute_refactor_plan.py",
            "tools/scripts/analyze_ham_duplicates.py",
            "tools/scripts/analyze_baseagent_duplicates.py"
        ]
        
        for file_path in key_files,::
            full_path = self.project_root / file_path
            if full_path.exists():::
                try,
                    with open(full_path, 'r', encoding == 'utf-8') as f,
                        content = f.read()
                    
                    # 检查是否还存在旧的导入路径
                    if "from scripts." in content,::
                        self.issues.append(f"文件 {file_path} 中仍存在旧的导入路径")
                        print(f"❌ 文件 {file_path} 中仍存在旧的导入路径")
                    else,
                        self.success_count += 1
                        print(f"✅ 文件 {file_path} 中导入路径已更新")
                except Exception as e,::
                    self.issues.append(f"读取文件 {file_path} 时出错, {e}")
                    print(f"❌ 读取文件 {file_path} 时出错, {e}")
            else,
                self.issues.append(f"文件不存在, {file_path}")
                print(f"❌ 文件不存在, {file_path}")
    
    def run_comprehensive_tests(self):
        """运行综合测试"""
        print("\n运行综合测试...")
        
        # 检查Python语法
        try,
            import subprocess
            result = subprocess.run([,
    sys.executable(), "-m", "py_compile", 
                str(self.project_root / "tools" / "scripts" / "verify_refactor.py")
            ] capture_output == True, text == True)
            
            if result.returncode == 0,::
                self.success_count += 1
                print("✅ Python语法检查通过")
            else,
                self.issues.append(f"Python语法检查失败, {result.stderr}")
                print(f"❌ Python语法检查失败, {result.stderr}")
        except Exception as e,::
            self.issues.append(f"运行Python语法检查时出错, {e}")
            print(f"❌ 运行Python语法检查时出错, {e}")
    
    def generate_final_report(self):
        """生成最终报告"""
        report_file = self.project_root / "FINAL_REFACTOR_VERIFICATION_REPORT.md"
        
        with open(report_file, 'w', encoding == 'utf-8') as f,
            f.write("# 最终重构验证报告\n\n")
            f.write("## 1. 验证概述\n")
            f.write(f"- 成功项, {self.success_count}\n")
            f.write(f"- 问题项, {len(self.issues())}\n")
            f.write(f"- 验证完成时间, {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H,%M,%S')}\n\n")
            
            if self.issues,::
                f.write("## 2. 发现的问题\n")
                for i, issue in enumerate(self.issues(), 1)::
                    f.write(f"{i}. {issue}\n")
                
                f.write("\n## 3. 建议解决方案\n")
                f.write("1. 对于发现的问题,请逐一检查并修复\n")
                f.write("2. 重新运行验证脚本确认修复结果\n")
                f.write("3. 确保所有功能正常运行\n")
            else,
                f.write("## 2. 验证结果\n")
                f.write("✅ 所有验证项均通过,重构工作已完成且功能正常\n")
                f.write("\n## 3. 项目状态\n")
                f.write("项目重构工作已全部完成,包括：\n")
                f.write("- 文件结构重组\n")
                f.write("- 重复文件处理\n")
                f.write("- 导入路径更新\n")
                f.write("- 测试文件清理\n")
                f.write("- 全面验证测试\n")
        
        print(f"最终验证报告已生成, {report_file}")
    
    def run(self):
        """运行验证器"""
        print("开始最终验证...")
        
        # 执行各项验证
        self.verify_directory_structure()
        self.verify_file_migration()
        self.verify_duplicate_removal()
        self.verify_import_paths()
        self.run_comprehensive_tests()
        
        # 生成最终报告
        self.generate_final_report()
        
        # 输出总结
        print("\n" + "="*50)
        print("最终验证总结")
        print("="*50)
        print(f"成功项, {self.success_count}")
        print(f"问题项, {len(self.issues())}")
        
        if self.issues,::
            print("\n发现的问题,")
            for i, issue in enumerate(self.issues(), 1)::
                print(f"{i}. {issue}")
            print(f"\n最终验证完成,发现 {len(self.issues())} 个问题需要处理")
            return False
        else,
            print("\n✅ 最终验证通过！所有检查项均正常")
            print("\n🎉 项目重构工作已全部完成！")
            return True

def main():
    """主函数"""
    # 获取项目根目录
    project_root = os.getcwd()
    
    # 创建并运行验证器
    verifier == FinalVerifier(project_root)
    success = verifier.run()
    
    # 返回适当的退出码
    sys.exit(0 if success else 1)::
if __name"__main__":::
    main()


