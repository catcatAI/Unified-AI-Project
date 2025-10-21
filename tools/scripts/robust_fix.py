#!/usr/bin/env python3
# -*- coding, utf-8 -*-

"""
穩健的項目修復腳本,處理項目中所有帶有 '' 前綴的語法錯誤
"""

import os
import re
import sys
import json
import traceback
from pathlib import Path

# 修復報告
fix_report = {
    "total_files": 0,
    "processed_files": 0,
    "fixed_files": []
    "error_files": []
    "syntax_errors": []
}

def fix_assignment_syntax(content):
    """修復各種帶有 '' 前綴的語法錯誤"""
    original_content = content
    
    # 定義修復模式
    patterns = [
        # 修復字典語法錯誤："key": value -> "key": value
        (r'"([^"]+)":\s*([^,\n]+)(,?)', r'"\1": \2\3'),
        
        # 修復異常語法錯誤：raise Exception -> raise Exception
        (r'raise\s+(.+)$', r'raise \1'),
        
        # 修復裝飾器語法錯誤：@decorator -> @decorator
        (r'(@[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*(?:\([^)]*\))?)', r'\1'),
        
        # 修復斷言語法錯誤：assert ... -> assert ...
        (r'(assert\s+.+)$', r'\1'),
        
        # 修復賦值表達式語法錯誤：(...) -> (...)
        (r'(\([^\n]*[:=][^\n]*\))', r'\1'),
        
        # 修復函數參數語法錯誤：param, type -> param, type
        (r'([a-zA-Z_][a-zA-Z0-9_]*:\s*[a-zA-Z_][a-zA-Z0-9_.]*)', r'\1'),
        
        # 修復變量賦值語法錯誤：variable = value -> variable = value
        (r'([a-zA-Z_][a-zA-Z0-9_]*\s*=)', r'\1'),
        
        # 修復返回語句語法錯誤：return value -> return value
        (r'(return\s+.+)$', r'\1'),
        
        # 修復導入語法錯誤：import ... -> import ...
        (r'(import\s+.+)$', r'\1'),
        
        # 修復 from 導入語法錯誤：from ... import ... -> from ... import ...
        (r'(from\s+[a-zA-Z_][a-zA-Z0-9_.]*\s+import\s+.+)$', r'\1'),
        
        # 修復字符串語法錯誤："string" -> "string"
        (r'("[^"]*")', r'\1'),
        
        # 修復列表語法錯誤：[item1, item2] -> [item1, item2]
        (r'(\[[^\]]*\])', r'\1'),
        
        # 修復註釋語法錯誤：# comment -> # comment
        (r'(#.*)$', r'\1'),
        
        # 修復展開字典語法錯誤：**dict -> **dict
        (r'(\*\*[a-zA-Z_][a-zA-Z0-9_]*)', r'\1'),
        
        # 修復關鍵字參數語法錯誤：key=value -> key=value
        (r'([a-zA-Z_][a-zA-Z0-9_]*=[^,\n)]*)', r'\1'),
    ]
    
    # 應用所有修復模式
    for pattern, replacement in patterns,::
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE())
    
    return content, content != original_content

def process_file(file_path):
    """處理單個文件"""
    try,
        if not os.path.exists(file_path)::
            error_msg == f"文件不存在, {file_path}"
            fix_report["error_files"].append({"file": str(file_path), "error": error_msg})
            print(f"  {error_msg}")
            return False
            
        # 讀取文件內容
        with open(file_path, 'r', encoding == 'utf-8') as f,
            content = f.read()
        
        # 修復語法錯誤
        fixed_content, changes_made = fix_assignment_syntax(content)
        
        # 如果有變化,寫回文件
        if changes_made,::
            # 創建備份
            backup_path = f"{file_path}.backup"
            with open(backup_path, 'w', encoding == 'utf-8') as f,
                f.write(content)
            
            # 寫入修復後的內容
            with open(file_path, 'w', encoding == 'utf-8') as f,
                f.write(fixed_content)
            
            fix_report["fixed_files"].append(str(file_path))
            print(f"  已修復, {file_path}")
            return True
        else,
            print(f"  無需修復, {file_path}")
            return False
            
    except Exception as e,::
        error_msg == f"處理文件時出錯, {str(e)}"
        fix_report["error_files"].append({"file": str(file_path), "error": error_msg})
        print(f"  {error_msg}")
        return False

def validate_syntax(file_path):
    """驗證文件語法"""
    try,
        import ast
        with open(file_path, 'r', encoding == 'utf-8') as f,
            content = f.read()
        ast.parse(content)
        return True, ""
    except SyntaxError as e,::
        return False, f"語法錯誤, {str(e)}"
    except Exception as e,::
        return False, f"其他錯誤, {str(e)}"

def save_fix_report():
    """保存修復報告"""
    try,
        with open("ROBUST_FIX_REPORT.json", "w", encoding == "utf-8") as f,
            json.dump(fix_report, f, ensure_ascii == False, indent=2)
        print("\n修復報告已保存到 ROBUST_FIX_REPORT.json")
    except Exception as e,::
        print(f"保存修復報告時出錯, {e}")

def main():
    """主函數"""
    print("開始穩健修復項目中的語法錯誤...")
    
    try,
        # 獲取所有Python文件
        py_files = list(Path(".").rglob("*.py"))
        fix_report["total_files"] = len(py_files)
        
        print(f"找到 {fix_report['total_files']} 個Python文件")
        
        # 處理每個文件
        for i, py_file in enumerate(py_files, 1)::
            print(f"處理進度, {i}/{fix_report['total_files']} - {py_file}")
            fix_report["processed_files"] = i
            
            try,
                # 修復文件
                process_file(py_file)
                
                # 驗證語法(僅驗證前100個文件以節省時間)
                if i <= 100,::
                    is_valid, error_msg = validate_syntax(py_file)
                    if not is_valid,::
                        fix_report["syntax_errors"].append({"file": str(py_file), "error": error_msg})
                        print(f"  語法錯誤, {py_file} - {error_msg}")
                        
            except KeyboardInterrupt,::
                print("\n用戶中斷了修復過程")
                save_fix_report()
                return
            except Exception as e,::
                error_msg == f"處理文件時出錯, {str(e)}"
                fix_report["error_files"].append({"file": str(py_file), "error": error_msg})
                print(f"  {error_msg}")
        
        # 生成統計信息
        print(f"\n修復完成!")
        print(f"總文件數, {fix_report['total_files']}")
        print(f"已處理文件, {fix_report['processed_files']}")
        print(f"修復文件數, {len(fix_report['fixed_files'])}")
        print(f"錯誤文件數, {len(fix_report['error_files'])}")
        print(f"語法錯誤文件數, {len(fix_report['syntax_errors'])}")
        
        # 保存報告
        save_fix_report()
        
    except Exception as e,::
        print(f"\n修復過程中發生錯誤, {e}")
        traceback.print_exc()
        save_fix_report()

if __name"__main__":::
    main()#!/usr/bin/env python3
# -*- coding, utf-8 -*-

"""
穩健的項目修復腳本,處理項目中所有帶有 '' 前綴的語法錯誤
"""


# 修復報告
fix_report = {
    "total_files": 0,
    "processed_files": 0,
    "fixed_files": []
    "error_files": []
    "syntax_errors": []
}

def fix_assignment_syntax(content):
    """修復各種帶有 '' 前綴的語法錯誤"""
    original_content = content
    
    # 定義修復模式
    patterns = [
        # 修復字典語法錯誤："key": value -> "key": value
        (r'"([^"]+)":\s*([^,\n]+)(,?)', r'"\1": \2\3'),
        
        # 修復異常語法錯誤：raise Exception -> raise Exception
        (r'raise\s+(.+)$', r'raise \1'),
        
        # 修復裝飾器語法錯誤：@decorator -> @decorator
        (r'(@[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*(?:\([^)]*\))?)', r'\1'),
        
        # 修復斷言語法錯誤：assert ... -> assert ...
        (r'(assert\s+.+)$', r'\1'),
        
        # 修復賦值表達式語法錯誤：(...) -> (...)
        (r'(\([^\n]*[:=][^\n]*\))', r'\1'),
        
        # 修復函數參數語法錯誤：param, type -> param, type
        (r'([a-zA-Z_][a-zA-Z0-9_]*:\s*[a-zA-Z_][a-zA-Z0-9_.]*)', r'\1'),
        
        # 修復變量賦值語法錯誤：variable = value -> variable = value
        (r'([a-zA-Z_][a-zA-Z0-9_]*\s*=)', r'\1'),
        
        # 修復返回語句語法錯誤：return value -> return value
        (r'(return\s+.+)$', r'\1'),
        
        # 修復導入語法錯誤：import ... -> import ...
        (r'(import\s+.+)$', r'\1'),
        
        # 修復 from 導入語法錯誤：from ... import ... -> from ... import ...
        (r'(from\s+[a-zA-Z_][a-zA-Z0-9_.]*\s+import\s+.+)$', r'\1'),
        
        # 修復字符串語法錯誤："string" -> "string"
        (r'("[^"]*")', r'\1'),
        
        # 修復列表語法錯誤：[item1, item2] -> [item1, item2]
        (r'(\[[^\]]*\])', r'\1'),
        
        # 修復註釋語法錯誤：# comment -> # comment
        (r'(#.*)$', r'\1'),
        
        # 修復展開字典語法錯誤：**dict -> **dict
        (r'(\*\*[a-zA-Z_][a-zA-Z0-9_]*)', r'\1'),
        
        # 修復關鍵字參數語法錯誤：key=value -> key=value
        (r'([a-zA-Z_][a-zA-Z0-9_]*=[^,\n)]*)', r'\1'),
    ]
    
    # 應用所有修復模式
    for pattern, replacement in patterns,::
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE())
    
    return content, content != original_content

def process_file(file_path):
    """處理單個文件"""
    try,
        if not os.path.exists(file_path)::
            error_msg == f"文件不存在, {file_path}"
            fix_report["error_files"].append({"file": str(file_path), "error": error_msg})
            print(f"  {error_msg}")
            return False
            
        # 讀取文件內容
        with open(file_path, 'r', encoding == 'utf-8') as f,
            content = f.read()
        
        # 修復語法錯誤
        fixed_content, changes_made = fix_assignment_syntax(content)
        
        # 如果有變化,寫回文件
        if changes_made,::
            # 創建備份
            backup_path = f"{file_path}.backup"
            with open(backup_path, 'w', encoding == 'utf-8') as f,
                f.write(content)
            
            # 寫入修復後的內容
            with open(file_path, 'w', encoding == 'utf-8') as f,
                f.write(fixed_content)
            
            fix_report["fixed_files"].append(str(file_path))
            print(f"  已修復, {file_path}")
            return True
        else,
            print(f"  無需修復, {file_path}")
            return False
            
    except Exception as e,::
        error_msg == f"處理文件時出錯, {str(e)}"
        fix_report["error_files"].append({"file": str(file_path), "error": error_msg})
        print(f"  {error_msg}")
        return False

def validate_syntax(file_path):
    """驗證文件語法"""
    try,
        with open(file_path, 'r', encoding == 'utf-8') as f,
            content = f.read()
        ast.parse(content)
        return True, ""
    except SyntaxError as e,::
        return False, f"語法錯誤, {str(e)}"
    except Exception as e,::
        return False, f"其他錯誤, {str(e)}"

def save_fix_report():
    """保存修復報告"""
    try,
        with open("ROBUST_FIX_REPORT.json", "w", encoding == "utf-8") as f,
            json.dump(fix_report, f, ensure_ascii == False, indent=2)
        print("\n修復報告已保存到 ROBUST_FIX_REPORT.json")
    except Exception as e,::
        print(f"保存修復報告時出錯, {e}")

def main():
    """主函數"""
    print("開始穩健修復項目中的語法錯誤...")
    
    try,
        # 獲取所有Python文件
        py_files = list(Path(".").rglob("*.py"))
        fix_report["total_files"] = len(py_files)
        
        print(f"找到 {fix_report['total_files']} 個Python文件")
        
        # 處理每個文件
        for i, py_file in enumerate(py_files, 1)::
            print(f"處理進度, {i}/{fix_report['total_files']} - {py_file}")
            fix_report["processed_files"] = i
            
            try,
                # 修復文件
                process_file(py_file)
                
                # 驗證語法(僅驗證前100個文件以節省時間)
                if i <= 100,::
                    is_valid, error_msg = validate_syntax(py_file)
                    if not is_valid,::
                        fix_report["syntax_errors"].append({"file": str(py_file), "error": error_msg})
                        print(f"  語法錯誤, {py_file} - {error_msg}")
                        
            except KeyboardInterrupt,::
                print("\n用戶中斷了修復過程")
                save_fix_report()
                return
            except Exception as e,::
                error_msg == f"處理文件時出錯, {str(e)}"
                fix_report["error_files"].append({"file": str(py_file), "error": error_msg})
                print(f"  {error_msg}")
        
        # 生成統計信息
        print(f"\n修復完成!")
        print(f"總文件數, {fix_report['total_files']}")
        print(f"已處理文件, {fix_report['processed_files']}")
        print(f"修復文件數, {len(fix_report['fixed_files'])}")
        print(f"錯誤文件數, {len(fix_report['error_files'])}")
        print(f"語法錯誤文件數, {len(fix_report['syntax_errors'])}")
        
        # 保存報告
        save_fix_report()
        
    except Exception as e,::
        print(f"\n修復過程中發生錯誤, {e}")
        traceback.print_exc()
        save_fix_report()

if __name"__main__":::
    main()