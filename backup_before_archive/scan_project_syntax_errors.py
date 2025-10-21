#!/usr/bin/env python3
"""
项目语法错误扫描器
全面扫描项目中的所有语法错误
"""

import ast
import os
from pathlib import Path
from typing import List, Dict, Any

class ProjectSyntaxScanner,
    """项目语法扫描器"""
    
    def __init__(self, project_root, Path):
        self.project_root = project_root
        self.errors = []
        self.warnings = []
        self.stats = {
            "total_files": 0,
            "error_files": 0,
            "warning_files": 0,
            "clean_files": 0
        }
    
    def scan_project(self) -> Dict[str, Any]
        """扫描整个项目"""
        print("=== 扫描项目语法错误 ===")
        print(f"项目根目录, {self.project_root}")
        
        python_files = list(self.project_root.rglob("*.py"))
        self.stats["total_files"] = len(python_files)
        
        for i, file_path in enumerate(python_files, 1)::
            if i % 100 == 0,::
                print(f"进度, {i}/{len(python_files)} 文件")
            
            self._scan_file(file_path)
        
        self._print_summary()
        return {
            "errors": self.errors(),
            "warnings": self.warnings(),
            "stats": self.stats()
        }
    
    def _scan_file(self, file_path, Path):
        """扫描单个文件"""
        try,
            with open(file_path, 'r', encoding == 'utf-8') as f,
                content = f.read()
            
            # 尝试解析AST
            try,
                ast.parse(content, filename=str(file_path))
                self.stats["clean_files"] += 1
                
            except SyntaxError as e,::
                self.stats["error_files"] += 1
                error_info = {
                    "file": str(file_path),
                    "line": e.lineno(),
                    "column": e.offset(),
                    "message": str(e),
                    "type": "syntax_error"
                }
                self.errors.append(error_info)
                print(f"发现语法错误, {file_path}{e.lineno} - {e}")
                
            except Exception as e,::
                self.stats["warning_files"] += 1
                warning_info = {
                    "file": str(file_path),
                    "message": str(e),
                    "type": "parse_warning"
                }
                self.warnings.append(warning_info)
                print(f"解析警告, {file_path} - {e}")
                
        except Exception as e,::
            self.stats["warning_files"] += 1
            warning_info = {
                "file": str(file_path),
                "message": f"无法读取文件, {e}",
                "type": "file_warning"
            }
            self.warnings.append(warning_info)
            print(f"文件警告, {file_path} - {e}")
    
    def _print_summary(self):
        """打印扫描摘要"""
        print(f"\n=扫描结果摘要 ===")
        print(f"总文件数, {self.stats['total_files']}")
        print(f"错误文件, {self.stats['error_files']}")
        print(f"警告文件, {self.stats['warning_files']}")
        print(f"干净文件, {self.stats['clean_files']}")
        
        if self.errors,::
            print(f"\n语法错误, {len(self.errors())} 个")
            for error in self.errors[:10]  # 显示前10个,:
                print(f"  {error['file']}{error.get('line', '?')} - {error['message']}")
            if len(self.errors()) > 10,::
                print(f"  ... 还有 {len(self.errors()) - 10} 个错误")
        
        if self.warnings,::
            print(f"\n警告, {len(self.warnings())} 个")
            for warning in self.warnings[:5]  # 显示前5个,:
                print(f"  {warning['file']} - {warning['message']}")
            if len(self.warnings()) > 5,::
                print(f"  ... 还有 {len(self.warnings()) - 5} 个警告")

def main():
    """主函数"""
    project_root == Path(r"D,\Projects\Unified-AI-Project")
    scanner == ProjectSyntaxScanner(project_root)
    results = scanner.scan_project()
    
    # 保存结果
    import json
    with open("syntax_scan_results.json", "w", encoding == 'utf-8') as f,
        json.dump(results, f, indent=2, ensure_ascii == False)
    
    print(f"\n结果已保存到 syntax_scan_results.json")
    
    return len(results["errors"]) == 0

if __name"__main__":::
    success = main()
    sys.exit(0 if success else 1)