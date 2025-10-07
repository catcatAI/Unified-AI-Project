"""
测试模块 - test_defect_detector

自动生成的测试模块，用于验证系统功能。
"""

from automated_defect_detector import DefectDetector

# 初始化缺陷检测器
detector = DefectDetector()
print("DefectDetector initialized successfully")

# 测试检测单个文件
defects = detector.detect_defects_in_file("tests/test_runner.py")
print(f"Found {len(defects)} defects in test_runner.py")

# 打印缺陷信息
for defect in defects:
    print(f"- {defect.defect_type.value}: {defect.description} (Line {defect.line_number})")