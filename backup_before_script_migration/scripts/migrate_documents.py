#!/usr/bin/env python3
"""
文档文件迁移脚本
此脚本用于将根目录下的文档文件迁移到docs目录的相应子目录
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict

class DocumentMigrator:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.docs_dir = self.project_root / "docs"
        
        # 定义文档分类规则
        self.category_rules = {
            "architecture": ["architecture", "design", "structure", "framework"],
            "development": ["development", "develop", "coding", "programming", "implement"],
            "api": ["api", "interface", "endpoint"],
            "testing": ["test", "testing", "fix", "bug", "error", "debug"],
            "deployment": ["deploy", "install", "setup", "config", "configuration", "run", "startup"],
            "reports": ["report", "summary", "analysis", "plan", "execution", "result"]
        }
    
    def find_md_files(self) -> List[Path]:
        """查找根目录下的所有MD文件"""
        md_files = []
        for file_path in self.project_root.glob("*.md"):
            # 排除一些不需要迁移的文件
            if file_path.name not in ["README.md", "CHANGELOG.md"]:
                md_files.append(file_path)
        return md_files
    
    def categorize_document(self, file_path: Path) -> str:
        """根据文件名和内容对文档进行分类"""
        filename = file_path.name.lower()
        
        # 首先根据文件名分类
        for category, keywords in self.category_rules.items():
            for keyword in keywords:
                if keyword in filename:
                    return category
        
        # 如果文件名无法分类，尝试读取文件内容
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
                
                # 根据内容关键词分类
                for category, keywords in self.category_rules.items():
                    for keyword in keywords:
                        if keyword in content:
                            return category
        except Exception as e:
            print(f"读取文件 {file_path} 时出错: {e}")
        
        # 默认分类到reports
        return "reports"
    
    def migrate_documents(self):
        """迁移文档文件"""
        print("开始迁移文档文件...")
        
        # 查找所有MD文件
        md_files = self.find_md_files()
        print(f"找到 {len(md_files)} 个文档文件需要迁移")
        
        # 统计分类结果
        category_stats = {}
        migration_plan = []
        
        # 为每个文件确定目标目录
        for file_path in md_files:
            category = self.categorize_document(file_path)
            target_dir = self.docs_dir / category
            
            # 更新统计
            if category not in category_stats:
                category_stats[category] = 0
            category_stats[category] += 1
            
            # 添加到迁移计划
            migration_plan.append({
                "source": file_path,
                "target": target_dir / file_path.name,
                "category": category
            })
        
        # 显示分类统计
        print("\n文档分类统计:")
        for category, count in category_stats.items():
            print(f"  {category}: {count} 个文件")
        
        # 确认迁移
        print(f"\n准备迁移 {len(migration_plan)} 个文件到以下目录:")
        for category in category_stats.keys():
            print(f"  - docs/{category}/")
        
        # 执行迁移
        migrated_count = 0
        error_count = 0
        
        for plan in migration_plan:
            try:
                source = plan["source"]
                target = plan["target"]
                target_dir = target.parent
                
                # 确保目标目录存在
                target_dir.mkdir(parents=True, exist_ok=True)
                
                # 移动文件
                shutil.move(str(source), str(target))
                print(f"已迁移: {source.name} -> docs/{plan['category']}/{source.name}")
                migrated_count += 1
                
            except Exception as e:
                print(f"迁移文件 {plan['source']} 时出错: {e}")
                error_count += 1
        
        # 生成迁移报告
        self.generate_migration_report(migration_plan, migrated_count, error_count)
        
        print(f"\n迁移完成!")
        print(f"  成功迁移: {migrated_count} 个文件")
        print(f"  错误: {error_count} 个文件")
    
    def generate_migration_report(self, migration_plan: List[Dict], migrated_count: int, error_count: int):
        """生成迁移报告"""
        report_file = self.project_root / "DOCUMENT_MIGRATION_REPORT.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 文档文件迁移报告\n\n")
            f.write("## 1. 迁移概述\n")
            f.write(f"- 总文件数: {len(migration_plan)}\n")
            f.write(f"- 成功迁移: {migrated_count}\n")
            f.write(f"- 迁移失败: {error_count}\n")
            f.write(f"- 迁移成功率: {migrated_count/len(migration_plan)*100:.1f}%\n\n")
            
            f.write("## 2. 迁移详情\n")
            for plan in migration_plan:
                status = "✅ 成功" if plan["target"].exists() else "❌ 失败"
                f.write(f"- {status} `{plan['source'].name}` -> `docs/{plan['category']}/{plan['source'].name}`\n")
            f.write("\n")
            
            f.write("## 3. 分类统计\n")
            categories = {}
            for plan in migration_plan:
                if plan['category'] not in categories:
                    categories[plan['category']] = 0
                categories[plan['category']] += 1
            
            for category, count in categories.items():
                f.write(f"- `{category}`: {count} 个文件\n")
            f.write("\n")
            
            f.write("## 4. 后续建议\n")
            f.write("1. 检查迁移失败的文件，手动处理\n")
            f.write("2. 更新项目中对这些文档的引用路径\n")
            f.write("3. 建立文档维护规范，避免未来再次出现根目录文档混乱问题\n")
            f.write("4. 定期清理不再需要的文档\n")
        
        print(f"迁移报告已生成: {report_file}")

def main():
    """主函数"""
    # 获取项目根目录
    project_root = os.getcwd()
    
    # 创建并运行迁移器
    migrator = DocumentMigrator(project_root)
    migrator.migrate_documents()

if __name__ == "__main__":
    main()