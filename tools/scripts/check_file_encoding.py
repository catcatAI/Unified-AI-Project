# 检查文件编码和开头字节的脚本
import os

file_path = r'D:\Projects\Unified-AI-Project\apps\backend\src\hsp\connector.py'

# 检查文件大小
file_size = os.path.getsize(file_path)
print(f"文件大小: {file_size} 字节")

# 读取前100个字节并显示十六进制值
with open(file_path, 'rb') as f:
    data = f.read(100)
    print("前100个字节的十六进制表示:")
    print([hex(b) for b in data])

# 尝试以文本模式读取前几行:
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()[:5]
        print("\n文件前5行内容:")
        for i, line in enumerate(lines, 1):
            print(f"{i}: {repr(line)}")
except Exception as e:
    print(f"\n以UTF-8编码读取文件时出错: {e}")
    
    # 尝试其他编码
    try:
        with open(file_path, 'r', encoding='gbk') as f:
            lines = f.readlines()[:5]
            print("\n使用GBK编码读取的前5行内容:")
            for i, line in enumerate(lines, 1):
                print(f"{i}: {repr(line)}")
    except Exception as e:
        print(f"使用GBK编码读取文件时也出错: {e}")