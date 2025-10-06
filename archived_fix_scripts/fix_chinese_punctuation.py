#!/usr/bin/env python3
"""
修復中文標點符號腳本
"""

def fix_chinese_punctuation(filename):
    """修復文件中的中文標點符號"""
    try:
        # 讀取文件
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 定義替換映射
        replacements = {
            '（': '(',  # 全形左括號 -> 半形左括號
            '）': ')',  # 全形右括號 -> 半形右括號
            '，': ',',  # 全形逗號 -> 半形逗號
            '。': '.',  # 全形句號 -> 半形句號
            '：': ':',  # 全形冒號 -> 半形冒號
            '；': ';',  # 全形分號 -> 半形分號
            '？': '?',  # 全形問號 -> 半形問號
            '！': '!',  # 全形驚嘆號 -> 半形驚嘆號
        }
        
        # 應用替換
        original_content = content
        for chinese, english in replacements.items():
            content = content.replace(chinese, english)
        
        # 如果有變化，寫回文件
        if content != original_content:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 已修復 {filename} 中的中文標點符號")
            return True
        else:
            print(f"ℹ️  {filename} 中沒有發現中文標點符號")
            return False
            
    except Exception as e:
        print(f"❌ 修復 {filename} 時出錯: {e}")
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("用法: python fix_chinese_punctuation.py <文件名>")
        sys.exit(1)
    
    filename = sys.argv[1]
    fix_chinese_punctuation(filename)